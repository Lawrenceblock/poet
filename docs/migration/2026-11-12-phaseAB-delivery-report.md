# 阶段A + 阶段B 交付报告

> 日期：2026-11-12
> 交付人：AI 助手（OpenHands）
> 状态：**材料与框架已交付；等待作者与负责人审阅授权；未进入任何下一阶段。**

---

## 一、本轮交付总览

| 阶段 | 分支 | PR | 提交 SHA | 状态 |
| --- | --- | --- | --- | --- |
| 阶段A：作者审阅材料 | `review/author-review-materials` | **#6** | `044341b` | ✅ 已推送 |
| 阶段B：Hugo 完整网站框架 | `site/hugo-poetry-site-foundation` | **#7** | `2b97af0` | ✅ 已推送 |

- PR #6：https://github.com/Lawrenceblock/poet/pull/6
- PR #7：https://github.com/Lawrenceblock/poet/pull/7

---

## 二、阶段A：作者审阅材料

### 目的

为**作者本人**提供可读、可勾选的材料，确认**作品边界与归属**。本阶段**只做材料，不做结论**。

### 交付内容（`docs/author-review/`）

| 文件 | 说明 |
| --- | --- |
| `2026-11-12-poetry-candidate-review-guide.md` | 总览（普通中文） |
| `poetry-candidates-author-review.csv` | 完整审阅表（137 行，字段有文档） |
| `batch-A.md` | A 类 104 条 |
| `batch-B.md` | B 类 31 条 |
| `batch-CD.md` | C/D 类 2 条 |
| `2026-11-12-priority-review-recommendations.md` | 第一批优先审阅建议 |
| `2026-11-12-work-boundary-notes.md` | 作品边界说明（一篇文章 ≠ 一首诗） |
| `README.md` | 索引与字段说明 |

工具：`tools/author-review/build_author_review.py`（**只读** v2 CSV，可重复生成）。

### 关键事实（已核验）

- 候选总数 **137**（A=104、B=31、C=1、D=1），与 v2 CSV **一致**。
- `作者确认状态` 初始一律 **“待作者审阅”**。
- **137 是文章级候选记录，不是 137 首诗**；独立作品总数**尚未确定**。
- **不拆分**作品、**不编造**归属、**不复制**全文（仅复用 v2 已有的截断摘录）。

---

## 三、阶段B：Hugo 完整网站框架

### 交付内容（`hugo/`）

- 首页、卷目 `/archive/`、年份 `/years/`、题记 `/preface/`、小传 `/shi-ren-xiao-zhuan/`、
  档案说明 `/about/`、站内搜索 `/search/`、RSS、sitemap、robots、404。
- 诗歌页模板 + `{{< poem >}}` 逐字保护短代码。
- 预览/正式域名隔离（canonical + robots）。
- `hugo/vercel.json`（构建配置，**未部署**）。

### 实测结论（已在干净克隆上复验）

| 项目 | 结果 |
| --- | --- |
| `hugo --gc --minify` | ✅ 成功，**无 ERROR/WARNING** |
| 产物文件数 | **21** |
| 本地 HTTP 全部页面 | ✅ **200** |
| 排版 15 用例（引号/`...`/`--`/`*`/HTML/空格/CJK 标点） | ✅ **全部通过** |
| 预览构建隔离（noindex + Disallow） | ✅ 已实测 |
| 合成样例数 | **6**（标题均以“【合成样例】”开头） |
| 真实作品迁入 | **0** |

### 关键文档

- `docs/migration/2026-11-12-url-compatibility-checklist.md`
- `docs/migration/2026-11-12-jekyll-isolation-proposal.md`（含**实测复现**证据）
- `docs/migration/2026-11-12-phaseB-hugo-site-build-report.md`
- `tools/verify/compare_urls.py`

---

## 四、发现的主要问题

| # | 问题 | 等级 | 状态 |
| --- | --- | --- | --- |
| 1 | 旧站 `/style.css` → 新站指纹路径，旧链接会 404 | 低 | 已给三方案，**未实施** |
| 2 | Jekyll 会把 `hugo/`、`docs/` 当页面发布（实测泄漏 14+4 文件） | 中 | 已给 `exclude` 提案，**未实施于 main** |
| 3 | 旧博客 305 篇 URL 策略**未定** | 高 | **待决策**，未猜测 |
| 4 | `baseof.html` 引用 `/favicon.ico` 但无该文件 | 低 | 已记录 |
| 5 | 一篇文章可能含多首（组诗），作品边界未确认 | 高 | **待作者确认** |
| 6 | `content/posts/` 含 6 篇合成样例，是否保留待定 | 低 | 已标注 |

---

## 五、迁移风险最高的三件事

1. **旧博客 305 篇的 URL 策略未定**——直接决定旧链接是否失效，必须在迁移正文前决策。
2. **作品边界未确认**——不确认“一篇文章含几首”，作品总数与目录结构都无法定稿。
3. **Jekyll 与新站共存期的构建污染**——`hugo/` 合入 `main` 前若不加 `exclude`，旧站会发布 Hugo 源文件。

---

## 六、尚未验证 / 待决事项

- Vercel 实际构建（`HUGO_VERSION=0.168.0`）**未验证**（未部署，未获授权）。
- 真实诗歌正文的迁移效果**未验证**（本阶段未迁移）。
- 旧站 3 篇与旧博客对应篇的正文差异**未裁定**。
- `bio.ismaelan.com` **未涉及**（独立网站，本任务边界外）。

---

## 七、边界遵守声明

本轮**未**：

- 修改 `main`（仍为 `ee94501c`）；
- 改动线上站点、DNS、域名、HTTPS、Vercel；
- 迁移任何真实诗歌/题记/小传正文；
- 拆分作品或编造归属；
- 将 `poet` 与 `bio.ismaelan.com` 混为一个项目。

所有写入均在**独立分支**，仅通过**草稿 PR** 提交，**未合并**。

---

## 八、下一步（**需授权后才进行**）

1. 作者填写 `poetry-candidates-author-review.csv` 的 `作者确认状态`；
2. 负责人决策旧博客 URL 策略与 `/style.css` 方案；
3. 授权后创建 Vercel **预览**项目（不影响旧站）；
4. 授权后进行首批真实作品迁移与逐页比对。

---

> 本报告由 AI 助手（OpenHands）代项目负责人整理，供审阅。**不得**据此自行进入下一阶段。
