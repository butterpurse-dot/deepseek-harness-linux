# 维护这个分支

[English](MAINTAINING.md) | 中文

本仓库是 [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) 的下游 Linux 打包分支。它是独立仓库，不是 GitHub fork，因此可以被搜索到。

## 上游同步

`.github/workflows/sync-upstream.yml` 每小时第 7 分钟运行，也可以手动启动。它会：

1. 获取上游最新的 `dsh-v*` 发布 tag；
2. 与 `apps/desktop/package.json` 比较；
3. 把首个 Linux 提交（`butterpurse@gmail.com`）之后的每个提交 rebase 到该 tag；
4. 运行 `pnpm run typecheck` 和 `pnpm run test:linux`；
5. 强制推送 `master`，把 `v<version>` 移动到新 HEAD，并派发 `linux-desktop.yml` 和 `linux-desktop-arm64.yml`。

当上游没有新版本，但 `master` 自当前 tag 以来有与发布相关的改动时，它会移动 tag 并派发两个发布工作流。Arch 打包改动被排除，因此发布后刷新 `PKGBUILD` 校验和不会再次触发发布。

如果 rebase 或验证失败，工作流会打开或更新 `upstream-sync` issue，并保留上一个发布。请在本地修复冲突，推送修正后的提交，然后重新运行同步。项目没有常驻维护者，因此被阻塞的同步需要社区贡献者。

工作流还会大约每月写入 `.github/keepalive`。该提交可防止 GitHub 在仓库 60 天无活动后禁用定时工作流。

除非 rebase 无法修复，否则不要手动把上游 `master` 合并到此分支；工作流假定 Linux 提交线性地叠加在上游发布 tag 之上。

## 发布

`linux-desktop.yml` 在推送 `v*` tag 或用 tag ref 手动派发时构建 x64 并发布。它会：

- 删除该版本已有的 release（GitHub 会保留同名资产）；
- 使用本地客户端配置构建官方应用（未签名）；
- 运行 `pnpm run test:linux`，并在 Xvfb 下启动构建出的 AppImage；
- 写入 `SHA256SUMS.txt` 并发布 release。

`linux-desktop-arm64.yml` 由同步工作流派发，也可以手动运行。它在 arm64 runner 上构建，并创建单独的 `v<version>-arm64` release。其 AppImage 通过 `latest-linux-arm64.yml` 更新；元数据刷新工作流会把该文件复制到 x64 release，arm64 release 仍可用于手动下载。

`refresh-arch-hashes.yml` 会在 x64 或 arm64 发布成功后运行，更新 `packaging/arch/PKGBUILD` 中的 `_version`、`pkgver` 和两个 AppImage 的校验和。因此正常发布不需要手动运行 `updpkgsums`。

## 外部 Pull Request

本地 `dsh-pr-agent` systemd timer 每两分钟运行一次。它仅在队列变化时更新 **External PR review queue** issue，然后对每条新的、非平凡的 reviewer 评论调用 `dsh --profile headless`。Agent 在临时 clone 中工作；wrapper 在推送到 PR fork 并发布回复之前运行 `git diff --check`，对于代码改动还会运行仓库测试脚本。平凡评论（LGTM、感谢、纯 emoji）会被跳过，每条评论最多尝试三次。可以让 agent 检查队列 issue 获取摘要；timer 无需邮件即可处理评论。队列会排除同一账号拥有的仓库。

开放的 awesome-list pull request 是免费的精选列表提交，不是付费推广。如果不想要，可以关闭它们；这些 fork 仅用于这些 PR。

## 安装器

`scripts/install-linux.sh` 按架构选择 x64 或 arm64 release，校验 `SHA256SUMS.txt`，把 AppImage 安装到 `$PREFIX/bin`，写入版本和已安装校验和，并安装 `dsh-update`。

`dsh-update --check`、`dsh-update` 和 `dsh-update --force` 会以更新模式重新运行安装器。该脚本作为 release 资产发布；已安装的更新器会获取 `releases/latest/download/install-linux.sh`，而不是缓存的 raw 分支。

## X 公告

当仓库 secrets 中配置了 `X_API_KEY`、`X_API_SECRET`、`X_ACCESS_TOKEN` 和 `X_ACCESS_TOKEN_SECRET`（或 `X_BEARER_TOKEN`）时，x64 发布工作流会自动发布一条 release 公告。没有配置时会跳过该步骤。发布脚本是 `scripts/post_to_x.py`；可用 `--dry-run` 检查文本，用 `--check` 检查认证方式。

## 社交预览

落地页使用 `docs/assets/social-preview.png`（1280x640）作为 `og:image` 和 `twitter:image`。GitHub 的仓库社交预览没有 API；该设置是可选的，不属于自动发布流程。

## 回滚

通过使用旧 tag 派发 `linux-desktop.yml` 来重新发布。如果 tag 已不存在，请从 release notes 中记录的提交恢复它，推送，然后派发。更新器只向前更新，因此用户必须手动重新安装旧版本。

## Linux 软件包检查

AppImage 是主要产物。`.deb` 会在 Ubuntu 24.04 容器中安装并启动；`.rpm` 会在 Fedora 容器中安装并启动；`packaging/arch/PKGBUILD` 会在 Arch 容器中使用 `APPIMAGE_EXTRACT_AND_RUN=1` 构建并启动（容器通常没有 `/dev/fuse`）。软件包依赖列表包含 `libasound2`（或 `libasound2t64`）和 `alsa-lib`；没有它们，Electron 在最小安装上会失败，即使桌面系统通常已经提供。

## 已知限制

- 构建未签名。每个 release 都会发布校验和。
- 应用内下载/安装路径已在本地使用通用 feed 和 stub AppImage 验证：应用检查 feed、下载文件、校验 SHA-512、替换 `APPIMAGE` 目标并启动它。CI 仍未发布更新的真实版本以测试完整的新版本启动。
