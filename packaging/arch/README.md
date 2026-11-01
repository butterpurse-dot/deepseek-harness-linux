# Arch Linux package

English | [中文](README.zh.md)

`PKGBUILD` installs the release AppImage into `/opt/deepseek-harness` and adds a
launcher, icon, and `.desktop` entry.

```sh
cd packaging/arch
updpkgsums        # only needed for manual changes
makepkg -si
```

Normal releases are refreshed automatically by
`.github/workflows/refresh-arch-hashes.yml`: it updates `_version`, `pkgver`,
and both AppImage hashes after the x64 and arm64 releases complete. No manual
step is needed.

Manual update steps:

1. Set `pkgver` (Arch version: no hyphen, e.g. `0.2.2alpha3`) and
   `_version` (release version, e.g. `0.2.2-alpha.3`). `_tag` is derived.
2. Run `updpkgsums` only if you changed a source without a release.
3. Build with `makepkg -si`.

The package is intentionally not published to the AUR from CI. Report Arch-specific
problems in the repository issue tracker.
