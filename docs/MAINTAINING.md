# Maintaining this fork

This repository is a downstream Linux packaging fork of
[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness).
It is a standalone repository, not a GitHub fork, so it can appear in search.

## Upstream sync

`.github/workflows/sync-upstream.yml` runs daily at 06:00 UTC and can be started
manually. It:

1. fetches the newest `dsh-v*` release tag from upstream,
2. compares it with `apps/desktop/package.json`,
3. rebases every commit after the first Linux commit (`butterpurse@gmail.com`)
   onto that tag,
4. runs `pnpm run typecheck` and `pnpm run test:linux`,
5. force-pushes `master`, moves `v<version>` to the new head, and dispatches
   `linux-desktop.yml` with the tag as the ref.

If the rebase or verification fails, the workflow opens or updates an
`upstream-sync` issue and leaves the last release untouched. Fix the conflict
locally, push the corrected commit, then re-run the sync.

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

`linux-desktop-arm64.yml` is manual. It builds on an arm64 runner and creates a
separate `v<version>-arm64` release. arm64 builds have no update feed, so users
update by downloading the next arm64 release.

## Installer

`scripts/install-linux.sh` selects the x64 or arm64 release by architecture,
verifies `SHA256SUMS.txt`, installs the AppImage to `$PREFIX/bin`, writes the
version and installed checksum, and installs `dsh-update`.

`dsh-update --check`, `dsh-update`, and `dsh-update --force` re-run the
installer in update mode. The script is published as a release asset; the
installed updater fetches `releases/latest/download/install-linux.sh`, not a
cached raw branch.

## Rollback

Re-publish an older tag by dispatching `linux-desktop.yml` with that tag. If the
tag no longer exists, restore it from the commit recorded in the release notes,
push it, and dispatch. The updater only moves forward, so users must reinstall
an older release manually.

## Known limitations

- Builds are unsigned. Every release publishes checksums.
- arm64 has no auto-update feed.
- The in-app download/install path has not been exercised against a newer
  release in CI; the feed check and the terminal fetch/verify/install path are
  tested.
