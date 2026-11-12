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
| `review/poetry-classification-phase2` | Phase 2：分类规则复核（PR #4） | ✅ 已推送 |
| `review/hugo-deployment-readiness-phase2` | Phase 2：Hugo/Vercel + 排版保护（PR #5） | ✅ 已推送 |

## 已完成的阶段

| 阶段 | 内容 | 分支 | 提交 SHA |
| --- | --- | --- | --- |
| 0 | 前序只读审计报告（PR #1） | audit/pre-hugo-migration-2026-11-12 | `eaac3a4` |
| B1–B2 | 博客全量抓取（305 篇）+ 清单/候选/对照 CSV + 普查报告 + 脚本 | research/poetry-discovery | `e414aa9` → `e25f6f3` |
| A1 | Hugo Extended 框架 + 模板 + URL 兼容方案 + 构建验证 | migration/hugo-poetry-foundation | `a9644ac` |
| P2-1 | 署名规则复核 + 可复现性工具（Task 1/3） | review/poetry-classification-phase2 | `0d2a8fd` |
| P2-2 | 候选 vs 独立作品数据模型（Task 2） | review/poetry-classification-phase2 | `5149f35` |
| P2-3 | Hugo/Vercel 部署审计 + 排版保护测试（Task 4/5） | review/hugo-deployment-readiness-phase2 | `9796cea` |

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

### review/poetry-classification-phase2（Phase 2 · PR #4）

- `docs/poetry-discovery/2026-11-12-phase2-authorship-rule-review.md`（署名规则复核）
- `docs/poetry-discovery/2026-11-12-phase2-candidate-vs-work-model.md`（候选 vs 独立作品模型）
- `docs/poetry-discovery/{blog-post-inventory,poetry-candidates}.v2.csv`、`classification-diff-v1-v2.csv`
- `tools/poetry-discovery/fetch_feed.py`（公开 Feed 抓取 + 校验）、`README.md`、`.gitignore`
- `tools/poetry-discovery/{build_inventory_v2,analyze_authorship,scan_risks,scan_anran_contexts,scan_substring_fp,phase2_risk_samples}.py`
- `tools/poetry-discovery/build_inventory.py`（改进：自动发现 feed 分页，输出不变）
- `.gitignore`（忽略 `work/`、`__pycache__/`）

### review/hugo-deployment-readiness-phase2（Phase 2 · PR #5）

- `docs/migration/2026-11-12-phase2-hugo-vercel-readiness.md`（Hugo 子目录 + Vercel 审计）
- `docs/migration/2026-11-12-phase2-poem-typography-protection.md`（排版保护测试）

## 尚未完成的工作

- 真实诗歌正文迁移（**需作者授权**，本阶段不做）。
- 29 篇 B 类候选人工复核。
- 多首诗文章拆分。
- Phase 2 建议的 Hugo 修正（关闭 typographer、统一短代码、锁定 HUGO_VERSION）**尚未应用**（仅建议）。

## 尚未解决的问题

- 29 篇 B 类候选待人工复核；E 类可能被低估。
- 多首诗文章（7 篇标题标记 + 若干无标记）待拆分。
- 《那拉提（未赴）》《诗人小传》未见于博客，来源待确认。
- 《青春的物语》博客版 vs 站点版差异待作者裁定。
- Vercel 上 `HUGO_VERSION=0.168.0` 的实际构建待验证（**未部署**）。
- **【Phase 2 新】Goldmark typographer 默认开启，会改写引号/省略号/破折号**（违反逐字保护），修正未应用。
- **【Phase 2 新】** `hardWraps` 正文会把 `*x*`/`_x_` 渲染为斜体；需统一用 `poem` 短代码。
- **【Phase 2 新】** `hugo.toml` 不被 Vercel 官方预设识别；`HUGO_VERSION` 未锁定。

## 下一步计划

1. ~~创建 PR A、PR B~~ ✅ 已完成（PR #1/#2/#3）。
2. Phase 2 复核已完成（PR #4/#5），等待审阅。
3. 等待作者/ChatGPT 审阅；获授权后再考虑应用 Phase 2 修正与正文迁移。

## 需要人工审核的事项

- **是**：所有 137 候选的分类与归属；特别是 29 篇 B 类。
- **是**：`放牧的星星/安然` 是否确为安然原创（正文无署名）。
- **是**：Hugo 框架的视觉与结构是否符合作者预期。
- **是**：是否授权后续诗歌正文迁移与应用 Phase 2 修正。

## 推送记录（最近一次成功推送的提交 SHA）

| 分支 | 最近成功推送 SHA |
| --- | --- |
| research/poetry-discovery | `e25f6f3`（PR #2） |
| migration/hugo-poetry-foundation | `a9644ac`（PR #3） |
| audit/pre-hugo-migration-2026-11-12 | `eaac3a4`（PR #1） |
| review/poetry-classification-phase2 | `5149f35`（PR #4） |
| review/hugo-deployment-readiness-phase2 | `9796cea`（PR #5） |

## 已创建的 PR（**均未合并**）

| PR | 分支 | 内容 |
| --- | --- | --- |
| #1 | audit/pre-hugo-migration-2026-11-12 | 前序只读审计报告 |
| #2 | research/poetry-discovery | 任务 B：诗歌普查 |
| #3 | migration/hugo-poetry-foundation | 任务 A：Hugo 框架 |
| #4 | review/poetry-classification-phase2 | Phase 2：分类规则复核 |
| #5 | review/hugo-deployment-readiness-phase2 | Phase 2：Hugo/Vercel + 排版保护 |
