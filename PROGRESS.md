# PROGRESS — 安然诗歌档案工程

> 本文件持续记录进度。**每次阶段性推送后必须更新并再次提交。**
> 长期成果以 **GitHub 远程仓库**为准；Workspace 仅作临时执行环境。

## 任务开始时间

- 2026-11-12（UTC）

## 当前工作分支

- `research/poetry-discovery`（任务 B：旧博客诗歌普查）— 进行中
- `migration/hugo-poetry-foundation`（任务 A：Hugo 框架）— 待开始
- `audit/pre-hugo-migration-2026-11-12`（前序只读审计，PR #1）— **保留不动**

## 已完成的阶段

| 阶段 | 内容 | 分支 | 提交 SHA |
| --- | --- | --- | --- |
| 0 | 前序只读审计报告（PR #1，勿动） | audit/pre-hugo-migration-2026-11-12 | eaac3a4 |
| B1 | 博客系统识别 + 全量抓取（305 篇） | research/poetry-discovery | （见下方推送记录） |
| B2 | 文章清单 CSV + 候选 CSV + 对照 CSV + 普查报告 | research/poetry-discovery | （见下方推送记录） |
| A1 | Hugo 框架 | migration/hugo-poetry-foundation | 待办 |

## 已推送的重要文件

- `docs/poetry-discovery/blog-post-inventory.csv`（305 篇）
- `docs/poetry-discovery/poetry-candidates.csv`（137 候选）
- `docs/poetry-discovery/existing-site-comparison.csv`（3 篇对照）
- `docs/poetry-discovery/2026-11-12-poetry-discovery-report.md`
- `tools/poetry-discovery/*.py`（可复现脚本）
- `PROGRESS.md`（本文件）

## 尚未完成的工作

- 任务 A：Hugo Extended 框架（首页/列表/单篇/RSS/sitemap/robots/canonical/404/导航/响应式）。
- 任务 A：`docs/migration/url-compatibility.md`。
- 任务 A：本地 Hugo 构建验证。
- 创建 PR A（Hugo）与 PR B（普查）。

## 尚未解决的问题

- 29 篇 B 类候选待人工复核。
- 多首诗文章（4 篇已知）待拆分。
- 《那拉提（未赴）》《诗人小传》未见于博客，来源待确认。
- 《青春的物语》博客版 vs 站点版差异待作者裁定。
- Hugo 二进制尚未安装（需下载 Hugo Extended v0.168.0 或兼容版本）。

## 下一步计划

1. 推送 research 分支（先保存）。
2. 搭建 Hugo 框架并本地构建验证。
3. 推送 migration 分支，创建 PR A、PR B。

## 需要人工审核的事项

- **是**：所有 137 候选的分类与归属；特别是 29 篇 B 类。
- **是**：Hugo 框架的视觉与结构是否符合作者预期。
- **是**：是否授权后续诗歌正文迁移。

## 推送记录（最近一次成功推送的提交 SHA）

- （待填写）
