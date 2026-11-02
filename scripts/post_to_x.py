#!/usr/bin/env python3
"""Post to X (Twitter) API v2 using environment or ~/.config/dsh-x/env credentials."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_CONFIG = Path.home() / ".config" / "dsh-x" / "env"
CREDENTIAL_KEYS = (
    "X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET",
    "X_BEARER_TOKEN", "TWITTER_CONSUMER_KEY", "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET", "TWITTER_BEARER_TOKEN",
)


def load_credentials(path: Path) -> dict[str, str]:
    values = {key: os.environ[key] for key in CREDENTIAL_KEYS if os.environ.get(key)}
    if not path.exists():
        return values
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def oauth1_header(method: str, url: str, params: dict[str, str], consumer_secret: str, token_secret: str) -> str:
    encoded = "&".join(f"{quote(key)}={quote(value)}" for key, value in sorted(params.items()))
    base = "&".join([method.upper(), quote(url), quote(encoded)])
    key = f"{quote(consumer_secret)}&{quote(token_secret)}"
    signature = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    params["oauth_signature"] = signature
    return "OAuth " + ", ".join(f'{quote(key)}="{quote(value)}"' for key, value in sorted(params.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a tweet using the X API v2.")
    parser.add_argument("text", nargs="*", help="tweet text; omit to read stdin")
    parser.add_argument("--file", help="read tweet text from a file")
    parser.add_argument("--config", default=os.environ.get("X_CONFIG", str(DEFAULT_CONFIG)))
    parser.add_argument("--base", default=os.environ.get("X_API_BASE", "https://api.x.com"))
    parser.add_argument("--dry-run", action="store_true", help="validate and print without posting")
    parser.add_argument("--check", action="store_true", help="report the configured auth method")
    parser.add_argument("--allow-long", action="store_true", help="allow text longer than 280 characters")
    args = parser.parse_args()

    env = load_credentials(Path(args.config).expanduser())
    bearer = env.get("X_BEARER_TOKEN") or env.get("TWITTER_BEARER_TOKEN")
    consumer_key = env.get("X_API_KEY") or env.get("TWITTER_CONSUMER_KEY")
    consumer_secret = env.get("X_API_SECRET") or env.get("TWITTER_CONSUMER_SECRET")
    access_token = env.get("X_ACCESS_TOKEN") or env.get("TWITTER_ACCESS_TOKEN")
    access_secret = env.get("X_ACCESS_TOKEN_SECRET") or env.get("TWITTER_ACCESS_TOKEN_SECRET")

    if args.check:
        if bearer:
            print("auth: OAuth 2.0 bearer token")
        elif all([consumer_key, consumer_secret, access_token, access_secret]):
            print("auth: OAuth 1.0a user context")
        else:
            print(f"auth: missing credentials in {args.config} and the environment")
            raise SystemExit(1)
        return

    if args.file:
        text = Path(args.file).expanduser().read_text().strip()
    elif args.text:
        text = " ".join(args.text).strip()
    else:
        text = sys.stdin.read().strip()
    if not text:
        raise SystemExit("post_to_x: no text provided")
    if len(text) > 280 and not args.allow_long:
        raise SystemExit(f"post_to_x: {len(text)} characters; pass --allow-long for premium limits")

    url = f"{args.base.rstrip('/')}/2/tweets"
    if bearer:
        headers = {"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"}
    elif all([consumer_key, consumer_secret, access_token, access_secret]):
        params = {
            "oauth_consumer_key": consumer_key,
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": access_token,
            "oauth_version": "1.0",
        }
        headers = {
            "Authorization": oauth1_header("POST", url, params, consumer_secret, access_secret),
            "Content-Type": "application/json",
        }
    else:
        raise SystemExit("post_to_x: missing X credentials")

    if args.dry_run:
        print(f"dry-run: would POST {url} ({len(text)} chars)")
        print(text)
        return

    request = urllib.request.Request(url, data=json.dumps({"text": text}).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(response.read().decode())
    except urllib.error.HTTPError as error:
        print(error.read().decode(errors="replace"), file=sys.stderr)
        raise SystemExit(error.code) from error


if __name__ == "__main__":
    main()
