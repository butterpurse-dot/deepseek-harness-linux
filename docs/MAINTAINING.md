# Maintaining this fork

English | [中文](MAINTAINING.zh.md)

This repository is a downstream Linux packaging fork of
[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness).
It is a standalone repository, not a GitHub fork, so it can appear in search.

## Upstream sync

`.github/workflows/sync-upstream.yml` runs hourly at minute 7 and can be started
manually. It:

1. fetches the newest `dsh-v*` release tag from upstream,
2. compares it with `apps/desktop/package.json`,
3. rebases every commit after the first Linux commit (`butterpurse@gmail.com`)
   onto that tag,
4. runs `pnpm run typecheck` and `pnpm run test:linux`,
5. force-pushes `master`, moves `v<version>` to the new head, and dispatches
   `linux-desktop.yml` and `linux-desktop-arm64.yml`.

When upstream has no newer release but `master` has release-relevant changes
since the current tag, it moves the tag and dispatches both release workflows.
Arch packaging changes are excluded so refreshing the `PKGBUILD` hashes after a
release does not trigger another release.

If the rebase or verification fails, the workflow opens or updates an
`upstream-sync` issue and leaves the last release untouched. Fix the conflict
locally, push the corrected commit, then re-run the sync. The project has no
active maintainer, so a blocked sync needs a community contributor.

The workflow also writes `.github/keepalive` about once a month. That commit
keeps GitHub from disabling scheduled workflows after 60 days without
repository activity.

Do not merge upstream `master` into this branch by hand unless the rebase cannot
be repaired; the workflow assumes a linear series of Linux commits on top of an
upstream release tag.

## Release

`linux-desktop.yml` builds x64 and publishes when a `v*` tag is pushed or the
workflow is dispatched with a tag ref. It:

- removes an existing release for that version (GitHub keeps same-named assets),
- builds the official app with the local client profile (unsigned),
- runs `pnpm run test:linux` and boots the built AppImage under Xvfb,
- writes `SHA256SUMS.txt` and publishes the release.

`linux-desktop-arm64.yml` is dispatched by the sync workflow and can also be run
manually. It builds on an arm64 runner and creates a separate
`v<version>-arm64` release. arm64 builds have no update feed, so users
update by downloading the next arm64 release.

## External pull requests

The local `dsh-pr-agent` systemd timer runs every two minutes. It updates the
**External PR review queue** issue only when the queue changes, then invokes
`dsh --profile headless` for each new, non-trivial reviewer comment. The agent
works in a throwaway clone; the wrapper runs `git diff --check` and, for code
changes, the repository's test script before pushing to the PR fork and posting
the reply. Trivial comments (LGTM, thanks, emoji-only) are skipped, and each
comment gets at most three attempts. Ask the agent to check the queue issue for a
summary; the timer handles comments without email. The queue excludes
repositories owned by the same account.

The open awesome-list pull requests are free curated-list submissions, not paid
promotion. Close them if they are unwanted; the forks exist only for those PRs.

## Installer

`scripts/install-linux.sh` selects the x64 or arm64 release by architecture,
verifies `SHA256SUMS.txt`, installs the AppImage to `$PREFIX/bin`, writes the
version and installed checksum, and installs `dsh-update`.

`dsh-update --check`, `dsh-update`, and `dsh-update --force` re-run the
installer in update mode. The script is published as a release asset; the
installed updater fetches `releases/latest/download/install-linux.sh`, not a
cached raw branch.

## Social preview

Upload `docs/assets/social-preview.png` (1280x640) in the repository's
**Settings → Social preview**. GitHub has no API for this setting, so it stays a
one-time manual step. The landing page already uses the same image for
`og:image` and `twitter:image`.

## Rollback

Re-publish an older tag by dispatching `linux-desktop.yml` with that tag. If the
tag no longer exists, restore it from the commit recorded in the release notes,
push it, and dispatch. The updater only moves forward, so users must reinstall
an older release manually.

## Linux package checks

The AppImage is the primary artifact. The `.deb` is installed and booted in an
Ubuntu 24.04 container; the `.rpm` is installed and booted in a Fedora
container; and `packaging/arch/PKGBUILD` is built and booted in an Arch
container with `APPIMAGE_EXTRACT_AND_RUN=1` (containers usually lack
`/dev/fuse`). The package dependency lists include `libasound2` (or
`libasound2t64`) and `alsa-lib`; without them Electron fails on a minimal
install even though desktop systems already provide them.

## Known limitations

- Builds are unsigned. Every release publishes checksums.
- arm64 has no auto-update feed.
- The in-app download/install path was exercised locally against a generic feed
  with a stub AppImage: the app checked the feed, downloaded the file, verified
  its SHA-512, replaced the `APPIMAGE` target, and spawned it. CI still does not
  publish a newer real release to test a full new-version boot.
