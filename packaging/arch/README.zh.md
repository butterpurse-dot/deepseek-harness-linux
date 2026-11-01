# Arch Linux 软件包

[English](README.md) | 中文

`PKGBUILD` 会把发布版 AppImage 安装到 `/opt/deepseek-harness`，并添加启动器、图标和 `.desktop` 文件。

```sh
cd packaging/arch
updpkgsums        # replace the pinned hashes after a version bump
makepkg -si
```

新版本的更新步骤：

1. 设置 `pkgver`（Arch 版本号，不带连字符，例如 `0.2.2alpha3`）和 `_version`（发布版本号，例如 `0.2.2-alpha.3`）。`_tag` 会自动派生。
2. 运行 `updpkgsums` 替换固定的校验和。
3. 使用 `makepkg -si` 构建。

本软件包不会由 CI 发布到 AUR。Arch 特有问题请提交到仓库 issue。
