# Arch Linux 软件包

[English](README.md) | 中文

`PKGBUILD` 会把发布版 AppImage 安装到 `/opt/deepseek-harness`，并添加启动器、图标和 `.desktop` 文件。

```sh
cd packaging/arch
updpkgsums        # only needed for manual changes
makepkg -si
```

正常发布由 `.github/workflows/refresh-arch-hashes.yml` 自动刷新：x64 和 arm64 发布完成后，它会更新 `_version`、`pkgver` 和两个 AppImage 的校验和。正常发布不需要手动操作。

手动更新步骤：

1. 设置 `pkgver`（Arch 版本号，不带连字符，例如 `0.2.2alpha3`）和 `_version`（发布版本号，例如 `0.2.2-alpha.3`）。`_tag` 会自动派生。
2. 只有在没有发布的情况下修改了源文件时，才需要运行 `updpkgsums`。
3. 使用 `makepkg -si` 构建。

本软件包不会由 CI 发布到 AUR。Arch 特有问题请提交到仓库 issue。
