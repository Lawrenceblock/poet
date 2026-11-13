# P1-E · 备份与可恢复性报告（N3）

- 日期：2026-11-12
- 目标文件：`tools/review/backup_review_data.py`
- 结论：**已建立跨文件系统独立备份；还原演练通过（逐字节一致）**

## 1. 风险背景（【已验证】）

- 审阅记录（作者意见）位于 `/workspace/...`。同一容器内 `/workspace` 与备份目录若**同设备**，则一次工作区回收会同时带走源与备份。
- 实测设备号：
  - `/workspace` → `66309`
  - `/home/openhands` → `1048590`（与 `/` 同一 overlay；容器整体回收仍会丢失，但可抵御单工作区回收）

## 2. 加固（【已验证】）

- 备份默认目标移出 `/workspace`：`/home/openhands/poet-review-backups/author-review/`。
- 新增**文件系统分离守卫**：目标与源同设备时**拒绝执行**，除非显式传 `--allow-same-fs`。把“同设备伪备份”从静默成功改为硬失败。

## 3. 备份结果（【已验证】）

- 备份目录：`/home/openhands/poet-review-backups/author-review/20261113-103728`
- 校验：`journal.jsonl` 23 行 / 19 条唯一候选，SHA-256 与源一致。
- **还原演练**：在空环境还原后**逐字节一致**（23 行 / 19 条唯一）。

## 4. 权限与令牌（【已验证】）

- 审阅访问令牌存放于：
  - `/home/openhands/poet-review-backups/access/review-token.txt`（`chmod 600`）
  - `docs/author-review/private/review-token.txt`（**已 git-ignore**，经 `git check-ignore` 确认）
- 令牌**未**写入任何公开文件或提交。

## 5. 局限（【已知未解决】）

- `/home` 与 `/` 同 overlay：**容器整体回收仍会同时丢失源与备份**。
- 令牌权限不足以创建新仓库（`Resource not accessible by integration`），也无法 push-to-create。
- 现有私有仓库 `Lawrenceblock/anran-literary-archive` 属**另一项目**，未触碰。
- 因此“异地/云端”持久备份**尚未建立**，属**非阻塞**事项，待项目负责人提供可写目标后再落地。

## 6. 边界声明

- 未改动任何审阅记录内容；未触碰其他项目仓库。**【已验证】**
