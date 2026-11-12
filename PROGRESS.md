# PROGRESS — 安然诗歌档案工程

> 本文件持续记录进度。**每次阶段性推送后必须更新并再次提交。**
> 长期成果以 **GitHub 远程仓库**为准；Workspace 仅作临时执行环境。

## 任务开始时间

- 2026-11-12（UTC）

## 当前工作分支

| 分支 | 用途 | 状态 |
| --- | --- | --- |
| `research/poetry-discovery` | 任务 B：旧博客诗歌普查 | ✅ 已推送 |
| `migration/hugo-poetry-foundation` | 任务 A：Hugo 框架 | ✅ 已推送 |
| `audit/pre-hugo-migration-2026-11-12` | 前序只读审计（PR #1） | ✅ **保留不动** |

## 已完成的阶段

| 阶段 | 内容 | 分支 | 提交 SHA |
| --- | --- | --- | --- |
| 0 | 前序只读审计报告（PR #1） | audit/pre-hugo-migration-2026-11-12 | `eaac3a4` |
| B1–B2 | 博客全量抓取（305 篇）+ 清单/候选/对照 CSV + 普查报告 + 脚本 | research/poetry-discovery | `e414aa9` |
| A1 | Hugo Extended 框架 + 模板 + URL 兼容方案 + 构建验证 | migration/hugo-poetry-foundation | `a9644ac` |

## 已推送的重要文件

### research/poetry-discovery

- `docs/poetry-discovery/blog-post-inventory.csv`（305 篇）
- `docs/poetry-discovery/poetry-candidates.csv`（137 候选）
- `docs/poetry-discovery/existing-site-comparison.csv`（3 篇对照）
- `docs/poetry-discovery/2026-11-12-poetry-discovery-report.md`
- `tools/poetry-discovery/{build_inventory,build_comparison,verify_clues}.py`
- `PROGRESS.md`（本文件）

### migration/hugo-poetry-foundation

- `hugo/hugo.toml`、`hugo/README-HUGO.md`、`hugo/vercel.json`
- `hugo/content/{archive.md,preface.md,posts/2026-11-12-demo-framework-check.md}`
- `hugo/layouts/{index.html,404.html,robots.txt}`、`hugo/layouts/_default/*`、`hugo/layouts/shortcodes/poem.html`
- `hugo/assets/css/style.css`、`hugo/static/assets/img/cover.png`
- `hugo/archetypes/posts.md`
- `docs/migration/url-compatibility.md`
- `docs/migration/hugo-build-verification.md`

## 尚未完成的工作

- PR A（Hugo）与 PR B（普查）的创建（见下）。
- 真实诗歌正文迁移（**需作者授权**，本阶段不做）。
- 29 篇 B 类候选人工复核。
- 多首诗文章拆分。

## 尚未解决的问题

- 29 篇 B 类候选待人工复核；E 类可能被低估。
- 多首诗文章（4 篇已知）待拆分。
- 《那拉提（未赴）》《诗人小传》未见于博客，来源待确认。
- 《青春的物语》博客版 vs 站点版差异待作者裁定。
- Vercel 上 `HUGO_VERSION=0.168.0` 的实际构建待验证。

## 下一步计划

1. 创建 PR A、PR B（指向 `main`，**不合并**）。
2. 更新本文件并推送。
3. 等待作者/ChatGPT 审阅。

## 需要人工审核的事项

- **是**：所有 137 候选的分类与归属；特别是 29 篇 B 类。
- **是**：Hugo 框架的视觉与结构是否符合作者预期。
- **是**：是否授权后续诗歌正文迁移。

## 推送记录（最近一次成功推送的提交 SHA）

| 分支 | 最近成功推送 SHA |
| --- | --- |
| research/poetry-discovery | `e414aa9`（+ 本次 PROGRESS 更新） |
| migration/hugo-poetry-foundation | `a9644ac` |
| audit/pre-hugo-migration-2026-11-12 | `eaac3a4`（PR #1） |
