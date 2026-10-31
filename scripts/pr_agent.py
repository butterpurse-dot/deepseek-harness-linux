#!/usr/bin/env python3
"""Answer review comments on external pull requests with a local DSH agent.

The agent is invoked only for comments written by other people. It edits a
throwaway clone of the pull request head branch, the script pushes the result
back to the fork, and posts the agent's reply to the pull request.

Run it from a systemd timer. It is deliberately deterministic: one comment at a
time, persisted state, bounded retries, and a lock.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
ACCOUNT = os.environ.get("DSH_PR_AGENT_ACCOUNT", "butterpurse-dot")
STATE_ROOT = Path(os.environ.get("DSH_PR_AGENT_STATE", Path.home() / ".local/state/dsh-pr-agent"))
STATE_FILE = STATE_ROOT / "state.json"
LOG_FILE = STATE_ROOT / "agent.log"
LOCK_FILE = STATE_ROOT / "lock"
DSH_BIN = os.environ.get("DSH_BIN", "dsh")
REPO_ALLOWLIST = [item.strip() for item in os.environ.get("DSH_PR_AGENT_REPOS", "").split(",") if item.strip()]
AGENT_TIMEOUT = int(os.environ.get("DSH_PR_AGENT_TIMEOUT", "900"))
MAX_PER_RUN = int(os.environ.get("DSH_PR_AGENT_MAX", "3"))
MAX_ATTEMPTS = 3
BOT_LOGINS = {ACCOUNT, "github-actions[bot]", "dependabot[bot]", "renovate[bot]"}
PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "pr-comment-agent.md"
TRIVIAL_COMMENTS = {
    "lgtm", "looks good", "looks good to me", "thanks", "thank you", "thanks!",
    "approved", "+1", "ship it", "nice", "great", "ok", "okay",
}
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".c", ".h", ".cpp", ".sh", ".rb", ".php"}


def log(message: str) -> None:
    line = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} {message}"
    print(line, flush=True)
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def request(path: str, method: str = "GET", body: dict | None = None):
    if not TOKEN:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required")
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "dsh-pr-comment-agent",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read()
            return json.loads(payload) if payload else None
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        detail = error.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"GitHub API {method} {path} failed: {error.code} {detail}") from error


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"seen": {}}


def save_state(state: dict) -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    temporary.replace(STATE_FILE)


def search_open_prs() -> list[dict]:
    query = urllib.parse.quote(f"is:pr is:open author:{ACCOUNT}")
    result = request(f"/search/issues?q={query}&per_page=100") or {}
    return result.get("items", [])


def external_comments(repo: str, number: int) -> list[dict]:
    comments: list[dict] = []
    for item in request(f"/repos/{repo}/issues/{number}/comments?per_page=100") or []:
        comments.append({
            "key": f"{repo}#{number}:issue:{item['id']}",
            "kind": "issue comment",
            "author": item["user"]["login"],
            "created": item["created_at"],
            "body": item.get("body") or "",
            "url": item["html_url"],
        })
    for item in request(f"/repos/{repo}/pulls/{number}/reviews?per_page=100") or []:
        if not item.get("submitted_at"):
            continue
        body = item.get("body") or ""
        if not body and item.get("state") == "APPROVED":
            continue
        comments.append({
            "key": f"{repo}#{number}:review:{item['id']}",
            "kind": f"review ({item.get('state', '').lower()})",
            "author": item["user"]["login"],
            "created": item["submitted_at"],
            "body": body,
            "url": item["html_url"],
        })
    for item in request(f"/repos/{repo}/pulls/{number}/comments?per_page=100") or []:
        comments.append({
            "key": f"{repo}#{number}:review-comment:{item['id']}",
            "kind": f"review comment on {item.get('path') or 'the diff'}",
            "author": item["user"]["login"],
            "created": item["created_at"],
            "body": item.get("body") or "",
            "url": item["html_url"],
        })
    return [
        comment for comment in comments
        if comment["author"] not in BOT_LOGINS and comment["body"].strip()
    ]


def render_prompt(template: str, values: dict[str, str]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace("{" + key + "}", value)
    return result


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def git(command: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 120) -> str:
    result = run(["git", *command], cwd, env, timeout)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(command)} failed: {result.stderr.strip()[:400]}")
    return result.stdout.strip()


def push_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GH_TOKEN"] = TOKEN or ""
    return env


def is_actionable(comment: dict) -> bool:
    text = " ".join(comment["body"].lower().split()).strip(" .!?:;")
    if not text:
        return False
    if text in TRIVIAL_COMMENTS:
        return False
    if not any(character.isalnum() for character in text):
        return False
    return True


def verify_changes(workspace: Path, files: list[str], before: str, committed: bool) -> str:
    checks = [["git", "diff", "--check", "HEAD"]]
    if committed:
        checks.append(["git", "diff", "--check", f"{before}..HEAD"])
    for check in checks:
        result = run(check, workspace)
        if result.returncode != 0:
            raise RuntimeError(f"diff check failed: {result.stdout.strip()[:300] or result.stderr.strip()[:300]}")
    if not any(Path(name).suffix in CODE_SUFFIXES for name in files):
        return "diff check passed"
    manifest = workspace / "package.json"
    if not manifest.exists():
        return "diff check passed"
    try:
        scripts = json.loads(manifest.read_text()).get("scripts", {})
    except json.JSONDecodeError:
        return "diff check passed"
    if "test" not in scripts:
        return "diff check passed"
    manager = "pnpm" if (workspace / "pnpm-lock.yaml").exists() else "yarn" if (workspace / "yarn.lock").exists() else "npm"
    log(f"verifying with {manager} test")
    tested = run([manager, "test"], workspace, os.environ.copy(), 300)
    if tested.returncode != 0:
        raise RuntimeError(f"{manager} test failed: {tested.stdout.strip()[-400:] or tested.stderr.strip()[-400:]}")
    return f"diff check passed; `{manager} test` passed"


def address_comment(pr: dict, comment: dict, dry_run: bool) -> None:
    base_repo = pr["base"]["repo"]["full_name"]
    number = pr["number"]
    head = pr["head"]
    head_repo = (head.get("repo") or {}).get("full_name")
    head_ref = head.get("ref")
    if not head_repo or not head_ref:
        raise RuntimeError("pull request head repository is unavailable")
    if head_repo.split("/", 1)[0] != ACCOUNT:
        raise RuntimeError(f"head repository {head_repo} is not owned by {ACCOUNT}; cannot push")
    template = PROMPT_FILE.read_text()
    prompt = render_prompt(template, {
        "account": ACCOUNT,
        "repo": base_repo,
        "number": str(number),
        "pr_url": pr["html_url"],
        "title": pr.get("title") or "",
        "body": (pr.get("body") or "").strip() or "(empty)",
        "branch": head_ref,
        "head_repo": head_repo,
        "comment_author": comment["author"],
        "comment_kind": comment["kind"],
        "comment_url": comment["url"],
        "comment_body": comment["body"].strip(),
    })
    if dry_run:
        log(f"dry run: would address {comment['key']}")
        print(prompt)
        return

    workspace = Path(tempfile.mkdtemp(prefix="dsh-pr-agent-"))
    try:
        clone_url = f"https://github.com/{head_repo}.git"
        log(f"cloning {clone_url} ({head_ref}) for {comment['key']}")
        git(["clone", "--quiet", "--depth", "1", "--branch", head_ref, clone_url, str(workspace)], workspace.parent)
        git(["config", "user.name", "Infinite Foundation"], workspace)
        git(["config", "user.email", "butterpurse@gmail.com"], workspace)
        before = git(["rev-parse", "HEAD"], workspace)

        agent_env = os.environ.copy()
        agent_env.pop("GH_TOKEN", None)
        agent_env.pop("GITHUB_TOKEN", None)
        log(f"invoking {DSH_BIN} for {comment['key']}")
        result = run([DSH_BIN, "--profile", "headless", prompt], workspace, agent_env, AGENT_TIMEOUT)
        if result.returncode != 0:
            raise RuntimeError(f"agent exited {result.returncode}: {result.stderr.strip()[:400] or result.stdout.strip()[-400:]}")

        reply_file = workspace / "REPLY.md"
        reply = reply_file.read_text().strip() if reply_file.exists() else ""
        if reply_file.exists():
            reply_file.unlink()

        status = git(["status", "--porcelain"], workspace)
        after = git(["rev-parse", "HEAD"], workspace)
        committed = after != before
        files: list[str] = []
        if status:
            git(["add", "-A"], workspace)
            staged = git(["diff", "--cached", "--name-only"], workspace)
            if staged:
                files = staged.splitlines()
        elif committed:
            files = git(["diff", "--name-only", f"{before}..HEAD"], workspace).splitlines()

        verification = "no changes"
        if files:
            verification = verify_changes(workspace, files, before, committed)
            log(f"verified {comment['key']}: {verification}")
            if status:
                git(["commit", "--quiet", "-m", f"Address review: {comment['kind']}"], workspace)

        if files:
            log(f"pushing {len(files)} changed file(s) to {head_repo}:{head_ref}")
            git(["-c", "credential.helper=!gh auth git-credential", "push", "--quiet", "origin", f"HEAD:{head_ref}"],
                workspace, push_env(), 180)

        if not reply:
            reply = "Thanks for the review. I checked this and did not find a code change to make." if not files \
                else f"Thanks for the review. Updated {', '.join(files[:5])}."
        body = reply.strip()
        if files:
            body += "\n\n---\nChanged: " + ", ".join(f"`{name}`" for name in files[:10])
        body += f"\n\n_Automated response to [this comment]({comment['url']}). Verification: {verification}._"
        request(f"/repos/{base_repo}/issues/{number}/comments", "POST", {"body": body})
        log(f"posted reply for {comment['key']}")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print the prompt without invoking the agent")
    parser.add_argument("--pr", help="only process this pull request URL")
    args = parser.parse_args()

    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("another run is active; exiting")
            return

        state = load_state()
        seen = state.setdefault("seen", {})
        processed = 0
        for item in search_open_prs():
            repo = item["repository_url"].split("/repos/", 1)[1]
            if repo == f"{ACCOUNT}/deepseek-harness-linux" or repo.split("/", 1)[0] == ACCOUNT:
                continue
            if REPO_ALLOWLIST and repo not in REPO_ALLOWLIST:
                continue
            pr = request(f"/repos/{repo}/pulls/{item['number']}")
            if pr is None or pr.get("state") != "open":
                continue
            if args.pr and args.pr.rstrip("/") != pr["html_url"].rstrip("/"):
                continue
            for comment in sorted(external_comments(repo, pr["number"]), key=lambda value: value["created"]):
                record = seen.get(comment["key"], {})
                if record.get("status") == "done":
                    continue
                if record.get("status") == "skipped":
                    continue
                if record.get("attempts", 0) >= MAX_ATTEMPTS:
                    continue
                if processed >= MAX_PER_RUN:
                    break
                if not is_actionable(comment):
                    seen[comment["key"]] = {
                        "status": "skipped",
                        "at": datetime.now(timezone.utc).isoformat(),
                        "url": comment["url"],
                    }
                    save_state(state)
                    continue
                processed += 1
                try:
                    address_comment(pr, comment, args.dry_run)
                    if not args.dry_run:
                        seen[comment["key"]] = {
                            "status": "done",
                            "at": datetime.now(timezone.utc).isoformat(),
                            "url": comment["url"],
                        }
                        save_state(state)
                except Exception as error:  # noqa: BLE001 - persist the failure and continue
                    log(f"failed {comment['key']}: {error}")
                    seen[comment["key"]] = {
                        "status": "failed",
                        "attempts": record.get("attempts", 0) + 1,
                        "at": datetime.now(timezone.utc).isoformat(),
                        "error": str(error)[:500],
                        "url": comment["url"],
                    }
                    save_state(state)
        save_state(state)
        log(f"run complete: {processed} comment(s) handled")


if __name__ == "__main__":
    main()
