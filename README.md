# DeepSeek Harness for Linux

Community Linux packaging for the official [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) desktop app. This is a downstream fork, not an official DeepSeek project.

The upstream desktop app is packaged for macOS and Windows only. This fork adds a Linux release target and publishes **AppImage**, **`.deb`**, and **`.tar.gz`** builds, with AppImage auto-update through `electron-updater` and GitHub Releases.

## Install

One command (installs to `~/.local`):

```sh
curl -fsSL https://raw.githubusercontent.com/butterpurse-dot/deepseek-harness-linux/master/scripts/install-linux.sh | bash
```

Then run `deepseek-harness` or open **DeepSeek Harness** from your application menu.

Manual options, from [Releases](https://github.com/butterpurse-dot/deepseek-harness-linux/releases):

| Format | Install |
|---|---|
| AppImage | `chmod +x deepseek-harness-*.AppImage && ./deepseek-harness-*.AppImage` |
| Debian / Ubuntu | `sudo apt install ./deepseek-harness-*.deb` |
| Portable | `tar -xzf deepseek-harness-*.tar.gz && ./deepseek-harness-*/deepseek-harness` |

Every release ships `SHA256SUMS.txt`. Verify with `sha256sum -c SHA256SUMS.txt`.

AppImage needs FUSE 2 on some distributions:

```sh
sudo apt install libfuse2        # Debian / Ubuntu
sudo dnf install fuse2           # Fedora / RHEL
```

## Updates

Installed AppImages check GitHub Releases through `electron-updater`. The app asks before downloading; installation happens on the next restart. `.deb` and `.tar.gz` users update by installing the newer release.

## What is included

- The official Electron desktop application (`apps/desktop`), unmodified except for the Linux target wiring and desktop icon.
- The bundled Node, pnpm, and Python runtime, so no system Node installation is required.
- The official agent, plugin, workspace, and `dsh://` protocol behaviour.

## Status

- **x64** builds are published.
- Builds are **unsigned**; there is no Linux code-signing story upstream yet. Checksums are published for every artifact.
- `arm64` is wired into the build target but is not published yet.
- Office document conversion uses the WASM engine on Linux, matching upstream's fallback.

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

This fork tracks `deepseek-ai/deepseek-harness`. The Linux changes are limited to the desktop target resolver, the packaging target table, the electron-builder Linux configuration, and the desktop icon/desktop-name wiring. Everything else is upstream code.

## License

MIT, matching upstream. DeepSeek Harness is a DeepSeek AI project; this repository is an independent community build.
