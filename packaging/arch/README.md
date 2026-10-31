# Arch Linux package

`PKGBUILD` installs the release AppImage into `/opt/deepseek-harness` and adds a
launcher, icon, and `.desktop` entry.

```sh
cd packaging/arch
updpkgsums        # replace the SKIP entries with the release hashes
makepkg -si
```

Update steps for a new release:

1. Set `pkgver` (Arch version: no hyphen, e.g. `0.2.2alpha3`) and `_tag`.
2. Run `updpkgsums`.
3. Build with `makepkg -si`.

The package is intentionally not published to the AUR from CI. Report Arch-specific
problems in the repository issue tracker.
