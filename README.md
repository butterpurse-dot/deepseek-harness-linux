<p align="center">
  <img src="docs/assets/dolphin-banner.gif" alt="A playful blue dolphin swimming with a beach ball" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <a href="https://github.com/butterpurse-dot/deepseek-harness-linux/releases"><img alt="Latest release" src="https://img.shields.io/github/v/release/butterpurse-dot/deepseek-harness-linux?include_prereleases&label=release"></a>
  <a href="https://github.com/butterpurse-dot/deepseek-harness-linux/actions/workflows/sync-upstream.yml"><img alt="Upstream sync" src="https://github.com/butterpurse-dot/deepseek-harness-linux/actions/workflows/sync-upstream.yml/badge.svg"></a>
  <a href="#platform-support"><img alt="Platform: Linux x64 + arm64" src="https://img.shields.io/badge/platform-linux%20x64%20%2B%20arm64-lightgrey.svg"></a>
  <a href="https://butterpurse-dot.github.io/deepseek-harness-linux/"><img alt="Website" src="https://img.shields.io/badge/website-live-1b6fd6.svg"></a>
</p>

<p align="center">
  <img src="docs/assets/app-screenshot.png" alt="DeepSeek Harness desktop running on Linux" width="90%">
</p>

# DeepSeek Harness for Linux

English | [中文](README.zh.md)

Community Linux packaging for the official [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) desktop app. This is a downstream fork, not an official DeepSeek project.

The upstream desktop app is packaged for macOS and Windows only. This fork adds a Linux release target and publishes **AppImage**, **`.deb`**, **`.rpm`**, and **`.tar.gz`** builds for x64 and arm64, with AppImage auto-update through `electron-updater` and GitHub Releases.

## Why this repo

- **RPM as well as AppImage, deb, and tar.gz**, for Fedora/RHEL users.
- **x64 and arm64** artifacts, with a separate arm64 release.
- **AppImage auto-update** and a `dsh-update` terminal updater with checksum verification.
- **One-command installer** and a published `SHA256SUMS.txt` for every release.
- **Hourly upstream sync** that rebases, tests, and releases automatically.

## Install

One command (installs to `~/.local`):

```sh
curl -fsSL https://github.com/butterpurse-dot/deepseek-harness-linux/releases/latest/download/install-linux.sh | bash
```

Then run `deepseek-harness` or open **DeepSeek Harness** from your application menu.

Manual options, from [Releases](https://github.com/butterpurse-dot/deepseek-harness-linux/releases):

| Format | Install |
|---|---|
| AppImage | `chmod +x deepseek-harness-*.AppImage && ./deepseek-harness-*.AppImage` |
| Debian / Ubuntu | `sudo apt install ./deepseek-harness-*.deb` |
| Fedora / RHEL | `sudo dnf install ./deepseek-harness-*.rpm` |
| Portable | `tar -xzf deepseek-harness-*.tar.gz && ./deepseek-harness-*/deepseek-harness` |

Every release ships `SHA256SUMS.txt`. Verify with `sha256sum -c SHA256SUMS.txt`.

AppImage needs FUSE 2 on some distributions:

```sh
sudo apt install libfuse2        # Debian / Ubuntu
sudo dnf install fuse2           # Fedora / RHEL
```

## Updates

The app checks GitHub Releases on startup and every six hours. When a newer release exists, a badge appears in the sidebar and the settings page offers the update dialog: it asks before downloading, then installs after **Install and Restart**.

From a terminal, the installed `dsh-update` command does the same fetch/verify/install flow:

```sh
dsh-update --check   # report whether a newer release exists
dsh-update           # download, verify SHA256SUMS and replace the installed AppImage
dsh-update --force   # reinstall the current release
```

`dsh-update` compares the installed AppImage against the published checksum, so a corrupted or manually modified copy is reinstalled. `.deb` and `.tar.gz` users update by installing the newer release.

arm64 builds are published as a separate `v<version>-arm64` release and update manually; they do not ship an update feed.

## What is included

- The official Electron desktop application (`apps/desktop`), unmodified except for the Linux target wiring and desktop icon.
- The bundled Node, pnpm, and Python runtime, so no system Node installation is required.
- The official agent, plugin, workspace, and `dsh://` protocol behaviour.

## Platform support

| Platform | Artifacts | Auto-update |
|---|---|---|
| Linux x64 | AppImage, `.deb`, `.rpm`, `.tar.gz` | AppImage only |
| Linux arm64 | AppImage, `.deb`, `.rpm`, `.tar.gz` (separate release) | manual |

**Requirements:** x64 or arm64 Linux with glibc 2.28+ and about 450 MB of disk. The AppImage needs FUSE 2 (`libfuse2` on Debian/Ubuntu, `fuse2` on Fedora); without FUSE, run it with `--appimage-extract-and-run`.

**Known limitations**

- Builds are unsigned, so the desktop may warn on first launch. Every release ships `SHA256SUMS.txt`; verify before running.
- Office conversion uses the WASM engine because upstream publishes no native Linux LibreOfficeKit package.
- The updater only moves forward. To go back to an older release, download that tag and reinstall it.

## Build from source

Requirements: Linux x64, Node 24.9+, pnpm 11, git.

```sh
git clone https://github.com/butterpurse-dot/deepseek-harness-linux
cd deepseek-harness-linux
corepack enable
corepack prepare pnpm@11.28.5 --activate
pnpm install --frozen-lockfile
pnpm run build
pnpm --filter @deepseek-ai/dsh-desktop run package:linux:x64 -- --unsigned
```

Artifacts land in `apps/desktop/.desktop-build/targets/linux-x64/unsigned-artifacts/`.

## Syncing with upstream

This fork tracks `deepseek-ai/deepseek-harness` automatically. A scheduled workflow fetches the newest upstream release tag, rebases the Linux commits onto it, runs `pnpm run typecheck`, pushes `master`, and starts the release build. If the rebase or typecheck fails it opens an `upstream-sync` issue and keeps the last good release.

The Linux changes are limited to the desktop target resolver, the packaging target table, the electron-builder Linux configuration, and the desktop icon/desktop-name wiring. Everything else is upstream code.

## Maintenance

This is a best-effort community build with no SLA and no active maintainer. A scheduled workflow checks upstream hourly, rebases the Linux changes onto new releases, and publishes automatically. Issues and pull requests are handled by the community when someone has time.

If the sync workflow is blocked, it opens an `upstream-sync` issue with the failing run; anyone is welcome to fix it.

## Contributing

Packaging fixes, installer improvements, and distribution reports are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

If this saves you a build, a star helps other Linux users find it.

## License

MIT, matching upstream. DeepSeek Harness is a DeepSeek AI project; this repository is an independent community build.
