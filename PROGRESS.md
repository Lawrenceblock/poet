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
| `review/poetry-classification-phase2` | Phase 2/3：分类规则复核（PR #4） | ✅ 已推送 |
| `review/hugo-deployment-readiness-phase2` | Phase 2/3：Hugo/Vercel + 排版保护（PR #5） | ✅ 已推送 |
| `review/author-review-materials` | 阶段A：作者审阅材料（PR #6） | ✅ 已推送 |
| `site/hugo-poetry-site-foundation` | 阶段B：Hugo 完整网站框架（PR #7） | ✅ 已推送 |
| `site/poetry-site-v1-2026-11-12` | 阶段C：整合 + 作者审阅全文站 + 旧站存档（PR #9） | ✅ 已推送 |
| `feat/author-review-system` | 作者审阅系统（PR #10） | ✅ 已推送 |
| `plan/final-implementation-2026-11-12` | 最终建设总策划（PR #11） | ✅ 已推送 |
| `impl/phase1-candidate-2026-11-12` | **第一阶段实施：候选站 + 作者审阅交付（PR #12）** | ✅ 已推送 |

---

## 第一阶段实施（POET-PHASE1-IMPLEMENTATION-01）· 2026-11-12

**分支**：`impl/phase1-candidate-2026-11-12`（基线 `feat/author-review-system@5b423d8`，PR #12，draft）
**目标**：建成完整、稳定、可独立链接访问的候选站，供作者浏览/审阅/提交意见。**非正式发布。**

### 已完成（P1-A … P1-H）

- **P1-A 构建环境**：Hugo Extended `0.168.0`；全量构建成功（预览 176 页 / 正式 22 页）。
- **P1-B 内容保真**：`verify_verbatim` **137/137 逐字一致**；公开清单 `candidate-list.md` + `to-confirm.md`。
- **P1-C 界面评估**：逐页实测（桌面/移动）；发现 1 处标题实体转义瑕疵（C0013，正文未受影响）。
- **P1-D 安全加固**：令牌门禁覆盖 GET/HEAD/OPTIONS；日志脱敏；`?token=` 一次性后重定向剥离；授权范围收敛到 `/review/` + `/api/`。
- **P1-E 备份可恢复**：跨文件系统独立备份 + 还原演练**通过**（逐字节一致）。
- **P1-F 稳定性**：并发重建 204 次请求 **0 瞬时 404**；新增生产产物守门（Hugo `--cleanDestinationDir` 在本版本为 no-op）。
- **P1-G URL 兼容**：8 个扁平旧页全部保持；305 篇博客映射 **305/305，0 遗漏、0 冲突**；站内链接预览 795 / 正式 209，**0 断链**。
- **P1-H 交付**：候选站外网可达；审阅系统可用；CSV/JSON 导出。

### 报告

`docs/phase1/`（索引 `README.md` + 8 份任务报告）。

### 待办（需授权）

- 作者逐篇确认 137 候选；标题实体转义瑕疵修正；异地/云端持久备份；旧博客 301（须旧主机下发）。

---

## 阶段 C（整合与交付）· 2026-11-12

**分支**：`site/poetry-site-v1-2026-11-12`（以 `main` `ee94501c` 为基线，整合 B/A/审阅分支）

### 已完成

- **C1 分支整合**：将 `review/author-review-materials`、`site/hugo-poetry-site-foundation`、
  `audit/*` 合并进本分支（`PROGRESS.md` 冲突已解决）。
- **C2 作者审阅全文站**：137 篇候选，逐字保留原文（含标点/诗行/段落/图片），
  仅移除脚本类不安全代码；共 11 个分批页 + 137 个阅读页。
  校验工具 `verify_verbatim.py`：**137/137 逐字一致**，内部链接全部可达。
- **C3 旧站只读存档**：`hugo/static/legacy/`（首页/卷目/题记/小传/两首诗），
  仅重写路径，未改动任何文字。
- **C4 URL 方案**：博客 305 篇 → `/:year/:month/:slug/`（= 旧 URL 去掉 `.html`）；
  映射表 `docs/migration/legacy-url-redirect-map.csv`，**0 冲突**。
- **C5 旧路径兼容**：`/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/style.css` 在新站不再 404
  （正文是否搬入正式页面待作者确认，当前为指向存档的说明页）。
- **C6 预览站**：`tools/preview/build_preview.py` 生成可点击预览；
  **正式构建不含 `/review/`**（未经确认的作品不进入正式站）。
- **C7 版本差异发现**：《青春的物语》在旧诗站与旧博客各有一版（正文一致，
  旧诗站残留 `**`/`---` 字面量）；已建 `review/oldsite/` 供作者裁定。
- **C8 线上核对**：旧站 8 条 URL 与新站逐条比对，全部 200 一致。

### 待办（需授权）

- 作者逐篇确认 137 候选（全部 `human_review=pending`）后方可迁移正文。
- DNS `poet.ismaelan.com` → Vercel 切换、Jekyll Pages 退役（**需显式授权 + 回滚方案**）。
- 旧域名 `www.ismaelan.com` 的 301 需**由旧站自身**实施（跨域，不能由新站代劳）。

## 已完成的阶段

| 阶段 | 内容 | 分支 | 提交 SHA |
| --- | --- | --- | --- |
| 0 | 前序只读审计报告（PR #1） | audit/pre-hugo-migration-2026-11-12 | `eaac3a4` |
| B1–B2 | 博客全量抓取（305 篇）+ 清单/候选/对照 CSV + 普查报告 + 脚本 | research/poetry-discovery | `e414aa9` → `e25f6f3` |
| A1 | Hugo Extended 框架 + 模板 + URL 兼容方案 + 构建验证 | migration/hugo-poetry-foundation | `a9644ac` |
| P2-1 | 署名规则复核 + 可复现性工具（Task 1/3） | review/poetry-classification-phase2 | `0d2a8fd` |
| P2-2 | 候选 vs 独立作品数据模型（Task 2） | review/poetry-classification-phase2 | `5149f35` |
| P2-3 | Hugo/Vercel 部署审计 + 排版保护测试（Task 4/5） | review/hugo-deployment-readiness-phase2 | `9796cea` |
| P3-1 | 分类规则修正（A 类须署名）+ 字段语义 + README + 复现验证 | review/poetry-classification-phase2 | `4ec62f7` |
| P3-2 | 关闭 typographer + 短代码矩阵 + Jekyll 隔离 + Vercel 预览修正 | review/hugo-deployment-readiness-phase2 | `22e3907` |
| P3-3 | Phase 3.1 文档收尾：作品数量表述修正 + 阶段标识统一 | review/poetry-classification-phase2 | `c5f7f55` |
| A2 | 阶段A：作者审阅材料（CSV + 分批 + 指南 + 边界说明 + 生成脚本） | review/author-review-materials | `044341b` |
| B | 阶段B：Hugo 完整网站框架（首页/卷目/年份/题记/小传/说明/搜索/RSS/robots/预览隔离/Vercel 配置） | site/hugo-poetry-site-foundation | `f4f28c1` |

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
- 31 篇 B 类候选人工复核。
- 多首诗文章拆分。
- Phase 3 已**应用** typographer 关闭；其余建议（Jekyll `exclude`、`HUGO_VERSION` 锁定、`/style.css` 兼容、favicon）**尚未应用**（仅建议）。
- 当前 v2 分类：**A=104, B=31, C=1, D=1**（合计 137）。

## 尚未解决的问题

- 31 篇 B 类候选待人工复核（含 Phase 3 降级的 2 条）；E 类可能被低估。
- 多首诗文章（7 篇标题标记 + 若干无标记）待拆分。
- 《那拉提（未赴）》《诗人小传》未见于博客，来源待确认。
- 《青春的物语》博客版 vs 站点版差异待作者裁定。
- Vercel 上 `HUGO_VERSION=0.168.0` 的实际构建待验证（**未部署**）。
- **【Phase 3 已解决】** ~~Goldmark typographer 默认开启~~ → **已在 `hugo/hugo.toml` 关闭**（`typographer = false`）。
- **【Phase 3 已解决】** ~~`hugo.toml` 不被 Vercel 官方预设识别~~ → **建议显式 `"framework": "hugo"` + 锁定 `HUGO_VERSION`**（文档已写明，配置未应用）。
- **【Phase 3 新】** Jekyll 会构建 `hugo/`、`docs/`（`hugo/` 不以 `_` 开头）；`main` 无这些目录故线上暂不受影响，合并前需加 `exclude`。
- **【Phase 3 新】** 短代码为**纯文本**（转义 HTML）；含内联 HTML 的诗需专门处理。
- **【Phase 3 新】** 旧站 `/style.css` 在新 Hugo 站为指纹路径 `/css/style.min.<hash>.css`，旧链接会 404。
- **【Phase 3 新】** `baseof.html` 引用 `/favicon.ico` 但无该文件。

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
| review/poetry-classification-phase2 | `c5f7f55`（PR #4） |
| review/hugo-deployment-readiness-phase2 | `92d4686`（PR #5） |
| review/author-review-materials | `044341b`（PR #6） |
| site/hugo-poetry-site-foundation | `f4f28c1`（PR #7） |
| site/poetry-site-v1-2026-11-12 | `07e23b2`（PR #9） |
| feat/author-review-system | `5b423d8`（PR #10） |
| plan/final-implementation-2026-11-12 | `c9272d0`（PR #11） |
| impl/phase1-candidate-2026-11-12 | `87a1f1a`（PR #12） |
| design/phase1-visual-refinement-2026-11-13 | `06e2fa4`（PR #13） |

> 上表 SHA 以 `git ls-remote` / GitHub 远程为准（2026-11-12 核验）。

## 已创建的 PR（**均未合并**）

| PR | 分支 | 内容 |
| --- | --- | --- |
| #1 | audit/pre-hugo-migration-2026-11-12 | 前序只读审计报告 |
| #2 | research/poetry-discovery | 任务 B：诗歌普查 |
| #3 | migration/hugo-poetry-foundation | 任务 A：Hugo 框架 |
| #4 | review/poetry-classification-phase2 | Phase 2：分类规则复核 |
| #5 | review/hugo-deployment-readiness-phase2 | Phase 2：Hugo/Vercel + 排版保护 |
| #6 | review/author-review-materials | 阶段A：作者审阅材料 |
| #7 | site/hugo-poetry-site-foundation | 阶段B：Hugo 完整网站框架 |
| #8 | audit/phase-c-production-readiness-2026-11-12 | Phase C 审计（只读） |
| #9 | site/poetry-site-v1-2026-11-12 | **阶段C：Hugo v1 + 作者审阅全文站 + 旧站存档**（draft） |
| #10 | feat/author-review-system | 作者审阅系统（draft） |
| #11 | plan/final-implementation-2026-11-12 | 最终建设总策划（draft） |
| #12 | impl/phase1-candidate-2026-11-12 | **第一阶段实施：候选站 + 作者审阅交付**（draft） |
| #13 | design/phase1-visual-refinement-2026-11-13 | **视觉优化候选 · 方案 C（白底/墨黑/暗红）**（draft，base=impl 分支） |


## 视觉优化候选（POET-VISUAL-REFINEMENT-01）· 2026-11-13

基线 `impl/phase1-candidate-2026-11-12` @ `5573f5c`；分支
`design/phase1-visual-refinement-2026-11-13` @ `06e2fa4`（PR #13，draft，base=impl 分支）。

### 已完成

- 全站视觉改为**方案 C**：白底 `#FFFFFF` / 墨黑 `#242424` / 暗红 `#762B35` /
  中灰 `#777777` / 浅灰线 `#E2E0DE` / 极浅暖灰 `#F7F6F4`。
- 移除旧淡蓝 `#dceef2`、蓝绿链接、半透明浮层与全部渐变；系统衬线字体栈，无外部依赖。
- 诗歌正文行高 2.35、阅读宽度 42rem、方角年份标签、细分隔线列表。
- 作者审阅页沿用同一配色（仅样式）；表单、字段、数据与 API 未改。
- 隔离预览（端口 12001 / work-2），作者原有预览（端口 12000 / work-1）未受影响。

### 验证

- 137/137 诗逐字一致；`hugo/content/**`、`hugo.toml`、`hugo/static/**` 未改动。
- 154 个审阅 HTML「剥离 `<style>` 后内容」与基线 **0 处差异**。
- 22 条路由全部 200；`/review/` 无令牌（含 HEAD）→ 401；`?token=` → 303。
- 令牌未出现在预览产物、访问日志或任何截图；审阅记录 SHA 未变。
- 像素采样：背景 `#DCEEF2` → `#FFFFFF`，蓝色系像素 0。

### 报告与截图

- `docs/phase1/visual/README.md`、`design-notes.md`、`changes-and-risks.md`、
  `tests-content-functional-security.md`
- `docs/phase1/visual/screenshots/{before,after,compare}/`（各 22 张）

### 待办（需授权）

- 作者与审查方查看预览与截图后决定是否采纳方案 C。
- 可选：辅助灰 `#777777`（4.48:1）是否微调为 `#757575`（4.61:1）以达 WCAG AA。
- 不自行合并 PR #13，不部署正式站。


## 第二轮视觉设计候选（POET-VISUAL-REFINEMENT-02）· 2026-11-13

**分支**：`design/phase2-black-white-composition-2026-11-13`
（基线 `design/phase1-visual-refinement-2026-11-13` @ `b73178c`）

主题：**黑色骨架、白色空间、暗红细节**。第一轮已去蓝改白，但结构仍靠灰色细线，
块面力量不足；本轮做**整页构图优化**，建立黑色骨架。

### 已完成

- 全站建立黑色骨架：黑色页眉、首页全宽主视觉、黑色栏目标题条、黑色页脚。
- 诗歌正文页改为**黑色页头**（标题 + 作者/日期/语言）+ 白色正文（行高 2.35）。
- 卷目 / 年代索引 / 档案说明 / 小传 / 搜索 / 404 均加黑色标题条；
  说明类长文的 `h2` 章节标题改为黑色单元。
- 作者审阅页同步黑色页眉/页脚（仅样式与结构）；`page()` 增加 `depth` 参数以修正子目录相对链接。
- 辅助灰 `#777777`（4.48:1）→ `#757575`（4.61:1），达 WCAG AA（第一轮待确认项已落实）。
- 黑底暗红改用提亮衍生色 `#CB6E77`（黑底 5.15:1）；规范色 `#762B35` 黑底仅 1.85:1 不可用。

### 验证

- 137/137 诗逐字一致；`hugo/content/**`、`hugo.toml`、`hugo/static/**` 未改动。
- 154 个审阅 HTML「剥离样式/页眉/页脚后」与基线 **0 处差异**；`<div class="poem">` 正文 **0 处差异**。
- 25/25 路由 200；`/review/` 无令牌（含 HEAD）→ 401，错误/空令牌 → 401，`?token=` → 303。
- 令牌未出现在预览产物、访问日志或任何截图；审阅记录 SHA `7f311871818e8b15a496…` 未变。
- 像素采样确认「黑—白—黑」节奏（首页桌面端：黑 42.3% / 白 56.4%）。

### 报告与截图

- `docs/phase1/visual-r2/README.md`、`design-implementation-note.md`、`design-notes.md`、
  `changes-and-risks.md`、`tests-content-functional-security.md`
- `docs/phase1/visual-r2/screenshots/{round1,round2,compare}/`（各 18 张）

### 预览

- 第二轮候选：work-2（端口 12001）——本轮把第一轮预览端口重新指向最新候选。
- 作者原有预览：work-1（端口 12000）**未受影响**。

### 待办（需授权）

- 作者确认：黑底暗红衍生色 `#CB6E77` 是否接受；主视觉黑色比例；是否保留诗歌黑色页头。
- 不自行合并 PR #12 / #13，不部署正式站。
