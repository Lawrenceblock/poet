# Phase A · 只读核实（2026-11-13）

> 本次独立会话的第一阶段：只核实事实，不写迁移审计报告。
> 所有结论均来自 GitHub API、`git` 与真实构建，不依赖旧会话的自我报告。

## 1. 仓库事实

| 项目 | 事实 |
|------|------|
| `main` HEAD | `ee94501`（"Update index.html"） |
| `main` 文件数 | **13** —— 仅 Jekyll 旧站（`index.html`、`_layouts/`、`_posts/`、`style.css` 等） |
| `main` 是否含 Hugo 网站 | **否** |
| 是否浅克隆 | 是（`git rev-parse --is-shallow-repository` = true） |

**关键结论**：`main` 里没有 Hugo 文件，**不代表项目没有这些文件**。
完整 Hugo 网站在候选分支上（见下）。这与任务书的提醒一致。

## 2. PR 状态（全部仍为 OPEN，无一合并）

| PR | 状态 | 分支 | 内容 |
|----|------|------|------|
| #13 | open | `design/phase1-visual-refinement-2026-11-13` | 第一轮 方案 C（白/墨黑/暗红） |
| #14 | open | `design/phase2-black-white-composition-2026-11-13` | 第二轮 黑色骨架 |
| #15 | open | `design/phase3-ammons-editorial-2026-11-13` | 第三轮 Ammons/Tubik 编辑设计 |
| #16 | open | `audit/verify-pre-hugo-migration-2026-11-13` | 审计复核（**不是视觉设计**） |
| #1  | open | `audit/pre-hugo-migration-2026-11-12` | 迁移前技术审计 |

## 3. 完整 Hugo 网站位于哪个分支

自底向上的分支链（每一层都包含完整 Hugo 网站与作者审阅系统）：

```
main (Jekyll only, 13 files)
 └─ site/poetry-site-v1-2026-11-12        阶段C：Hugo v1 + /review/ + 旧站存档
     └─ feat/author-review-system          作者审阅系统（保存/回读/导出）
         └─ impl/phase1-candidate-2026-11-12   Phase1 候选站
             └─ design/phase1-visual-refinement-2026-11-13  视觉一轮（方案C）
                 └─ design/phase2-black-white-composition-2026-11-13  视觉二轮（黑骨架）
                     └─ design/phase3-ammons-editorial-2026-11-13  视觉三轮（Ammons/Tubik）★
```

**结论**：完整 Hugo 网站（含 `/review/` 137 篇、旧站存档、搜索、RSS、sitemap）
位于 **`design/phase3-ammons-editorial-2026-11-13`** 及其祖先分支。

- 第三轮分支 HEAD：`1037d1b`
- 第三轮基线：`6c9bd55`（第二轮）

## 4. 第三轮设计文件是否完整

`docs/phase3-ammons/` 下 5 个文件全部存在：

- `research.md`、`design-system.md`、`page-design.md`、`implementation-note.md`、`test-report.md` ✅

`screenshots/phase3/` 下 16 张截图全部存在（桌面 9 + 移动 5 + 审阅 2）✅

## 5. 第三轮是否仍可重新构建

**可以。** 实测（本会话）：

- Hugo Extended `v0.168.0`（与本项目 `hugo/vercel.json` 声明的 `HUGO_VERSION` 一致）。
- `hugo --gc --minify` 成功，18 页 + 旧站存档，0 错误 0 警告。
- 预览构建脚本 `tools/preview/build_preview.py`、审阅 API `tools/review/serve_review.py` 均在。

## 6. 已完成 vs 未获作者验收

| 工作 | 状态 |
|------|------|
| Hugo 网站框架（首页/卷目/年份/搜索/RSS/sitemap/404） | 已完成（分支上） |
| 作者审阅系统（137 篇，保存/回读/导出，令牌门禁） | 已完成（分支上） |
| 视觉一轮 / 二轮 / 三轮 | 已完成（分支上，均为候选） |
| **作者对任一视觉方案的验收** | **尚未发生**（PR #13/#14/#15 全部 open，无合并） |

## 7. 当前实际页面构建方式

- 生产构建：`cd hugo && hugo --gc --minify`（Vercel `vercel.json` 同）。
- 预览构建：`python3 tools/preview/build_preview.py`（Hugo + 把 `docs/author-review/site/` 拷进 `/review/`）。
- 预览服务：`tools/preview/serve_preview.py`（静态）或 `tools/review/serve_review.py`（静态 + `/api/`）。
- URL 方案：`/posts` → `/:year/:month/:slug/`；旧诗站 3 篇用显式 `url:` 扁平路径。

## 8. 本阶段不做什么

- 不重写迁移审计报告。
- 不改 `main`、不合并 PR、不删除分支。
- 不把旧会话的自述当作完成证明。
