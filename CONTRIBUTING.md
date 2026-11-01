# Contributing

English | [中文](CONTRIBUTING.zh.md)

This repository packages the official [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) desktop app for Linux. Contributions to the packaging, installer, CI, and documentation are welcome.

The upstream project does not accept external pull requests. Agent, runtime, plugin, and web UI issues belong in the [upstream discussions](https://github.com/deepseek-ai/deepseek-harness/discussions); this repository only owns the Linux packaging layer.

## Maintenance model

This is a best-effort community build with no SLA and no active maintainer. Upstream releases are synced automatically; issues and pull requests are handled by the community when someone has time. If the sync workflow is blocked, it opens an `upstream-sync` issue and anyone may fix it.

## Ways to help

- Test on your distribution and report what works or breaks.
- Improve the existing RPM, Arch PKGBUILD, installer, updater, or checksum verification.
- Add packaging formats: Nix, Flatpak, or another installer.
- Translate the docs or the landing page.
- Share the project where Linux and DeepSeek users gather.
- If you want to take over maintenance, open a discussion. The MIT license lets anyone fork and continue.

There is no expectation that the original author will review or merge anything.

## Report a problem

Open an issue with:

- distribution and version (`cat /etc/os-release`),
- how the app was installed (installer, AppImage, `.deb`, `.tar.gz`),
- the output of `dsh-update --check`,
- the relevant lines from the app log or terminal.

## Change the packaging

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

Open a pull request against `master`. Keep changes small: the scheduled sync rebases the Linux commit series onto each upstream release, so edits should stay inside the Linux packaging surface (target resolver, `package-target.ts`, electron-builder configuration, desktop icon/desktop name, installer, workflows, docs).

## Rebuild the banner

```sh
python3 scripts/generate-dolphin-banner.py
```

Writes `docs/assets/dolphin-banner.gif` and `.png`.

## License

By contributing you agree that your changes are licensed under the MIT License in [LICENSE](LICENSE).
