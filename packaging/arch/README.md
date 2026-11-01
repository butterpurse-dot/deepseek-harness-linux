# Arch Linux package

English | [中文](README.zh.md)

`PKGBUILD` installs the release AppImage into `/opt/deepseek-harness` and adds a
launcher, icon, and `.desktop` entry.

```sh
cd packaging/arch
updpkgsums        # replace the pinned hashes after a version bump
makepkg -si
```

Update steps for a new release:

1. Set `pkgver` (Arch version: no hyphen, e.g. `0.2.2alpha3`) and
   `_version` (release version, e.g. `0.2.2-alpha.3`). `_tag` is derived.
2. Run `updpkgsums` to replace the pinned hashes.
3. Build with `makepkg -si`.

The package is intentionally not published to the AUR from CI. Report Arch-specific
problems in the repository issue tracker.
