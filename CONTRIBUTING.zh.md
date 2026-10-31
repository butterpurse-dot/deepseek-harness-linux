# 贡献指南

本仓库为官方 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) 桌面端提供 Linux 打包。欢迎提交打包、安装器、CI 和文档相关的改动。

上游项目目前不接受外部 pull request。Agent、运行时、插件和 Web UI 的问题请前往[上游讨论区](https://github.com/deepseek-ai/deepseek-harness/discussions)；本仓库只负责 Linux 打包层。

## 报告问题

请在 issue 中附上：

- 发行版与版本（`cat /etc/os-release`）；
- 安装方式（安装脚本、AppImage、`.deb`、`.tar.gz`）；
- `dsh-update --check` 的输出；
- 应用日志或终端中的相关行。

## 修改打包

```sh
git clone https://github.com/butterpurse-dot/deepseek-harness-linux
cd deepseek-harness-linux
corepack enable
corepack prepare pnpm@11.28.5 --activate
pnpm install --frozen-lockfile
pnpm run build
pnpm --filter @deepseek-ai/dsh-desktop run package:linux:x64 -- --unsigned
```

产物位于 `apps/desktop/.desktop-build/targets/linux-x64/unsigned-artifacts/`。

请向 `master` 提交 pull request。改动尽量小：定时同步会把 Linux 提交系列 rebase 到每个上游 release 上，因此修改应限制在 Linux 打包范围内（target resolver、`package-target.ts`、electron-builder 配置、桌面图标/desktop name、安装器、workflow、文档）。

## 重新生成横幅

```sh
python3 scripts/generate-dolphin-banner.py
```

生成 `docs/assets/dolphin-banner.gif` 和 `.png`。

## 许可证

提交即表示你同意以 [LICENSE](LICENSE) 中的 MIT 许可证授权你的改动。
