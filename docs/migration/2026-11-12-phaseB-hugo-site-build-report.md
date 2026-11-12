# Phase B 交付报告：Hugo 诗歌网站完整框架

> 日期：2026-11-12
> 分支：`site/hugo-poetry-site-foundation`（基础：PR #5 已审阅框架 `8dc57c3`）
> 构建工具：Hugo Extended v0.168.0（`hugo v0.168.0-e27a6760c5547237f87d353aebe0580feadb20f4+extended`）
> 状态：**框架完成；未迁移任何真实作品；未部署；未改动旧站/main/域名/Vercel。**

## 1. 交付范围

在 PR #5 审阅通过的骨架基础上，构建**完整可运行的 Hugo 站点框架**：

| 项目 | 状态 |
| --- | --- |
| 首页（封面 + 最新作品 + 年份入口 + 说明） | ✅ |
| 卷目 `/archive/`（按年份分组） | ✅ |
| 年份归档 `/years/`（年份跳转） | ✅ |
| 题记 `/preface/`（占位） | ✅ |
| 诗人小传 `/shi-ren-xiao-zhuan/`（占位） | ✅ |
| 档案说明 `/about/` | ✅ |
| 站内搜索 `/search/`（纯前端） | ✅ |
| 诗歌页模板（`{{< poem >}}` 逐字保护） | ✅ |
| RSS / sitemap / robots / 404 | ✅ |
| 预览域名隔离（noindex + Disallow） | ✅ |
| Vercel 构建配置 | ✅ |
| URL 兼容清单 | ✅ |
| Jekyll 隔离提案（含实测证据） | ✅ |
| URL 比对工具 | ✅ |

## 2. 合成样例（**不是真实作品**）

`content/posts/` 仅含 **6 篇明确标注的合成样例**（标题均以“【合成样例】”开头），
用于验证排版与结构。**没有**迁入任何真实诗歌正文。

| slug | 语言 | 验证点 |
| --- | --- | --- |
| `demo-letter-unsent` | zh | 基本排版、诗节 |
| `demo-star-herder` | zh | 多诗节、标签 |
| `demo-the-quiet-room` | en | 中英混排（英文左对齐） |
| `demo-three-short-songs` | zh | **一篇文章含多首（组诗）**显示 |
| `demo-rain-at-nalati` | zh | 长诗 |
| `demo-snow-2026` | zh | 年份归档 |

## 3. 排版逐字保护（**已实测**）

`content/tests/typography-matrix.md`（draft + `build.render=never`，**不进正式构建**）
覆盖 15 个用例。实测结果：

| 用例 | 期望 | 结果 |
| --- | --- | --- |
| 连续诗行 / 单个空行 / 多个空行 / 多个诗节 | 换行与空行保留 | ✅ |
| 直引号 `"` `'` | **不**变弯引号 | ✅ |
| 中文引号 `“”‘’` | 原样 | ✅ |
| `...` 与 `……` | 原样（`...` 不省略号化） | ✅ |
| `--` | 原样（**不**变破折号） | ✅ |
| `*` `_` `**` `__` | **纯文本**（不解释为格式） | ✅ |
| `<` `&` `>` 与 `<b>` | HTML 转义（安全，不执行） | ✅ |
| 行首空格 / 行尾空格 | 保留（`white-space:pre-wrap`） | ✅ |
| 中文标点 / `——` / `……` | 原样 | ✅ |

保护机制：
1. `typographer = false`（Goldmark 不重写标点）；
2. `{{< poem >}}` 短代码用**纯文本**输出（HTML 转义、不解释 Markdown 强调）；
3. `.poem-verse { white-space: pre-wrap; }` 保留行首/行尾与连续空格。

## 4. 构建与产物（实测）

```bash
cd hugo && hugo --gc --minify
```

- 结果：**构建成功**，`Pages 20`、`Static files 2`、**无 ERROR/WARNING**。
- 产物：`public/` 下 **21 个文件**（6 篇样例 + 6 个特殊页 + 首页 + 404 + `index.json`
  + `index.xml` + `sitemap.xml` + `robots.txt` + 指纹 CSS + `search.js` + 封面图）。
- 本地 `http.server` 实测：首页/卷目/年份/题记/小传/说明/搜索/样例页/`index.json`
  /`robots.txt`/`sitemap.xml` **全部 200**。

## 5. 预览与正式域名隔离（**已实测**）

`head-meta.html` 与 `robots.txt` 依据 `baseURL` 主机名判断：

| 构建 | canonical | robots meta | robots.txt |
| --- | --- | --- | --- |
| `poet.ismaelan.com`（正式） | 输出 | `index,follow` | `Allow: /` |
| 其他（预览，如 `*.vercel.app`） | **不输出** | `noindex,nofollow` | `Disallow: /` |

已用 `--baseURL https://poet-preview.example.vercel.app/` 实测确认：
预览构建输出 `noindex,nofollow` 与 `Disallow: /`，**不会污染正式站 SEO**。

## 6. URL 兼容（详见 `2026-11-12-url-compatibility-checklist.md`）

- `permalinks.posts = "/:slug/"`，每篇**显式 `slug`** 复现旧扁平 URL。
- 特殊页用 front matter `url:` 固定，与旧站一致（`/archive/`、`/preface/`、`/shi-ren-xiao-zhuan/`）。
- **唯一已知不一致**：旧站 `/style.css` → 新站 `/css/style.min.<hash>.css`（风险低，已给三方案）。
- 旧博客 305 篇 URL 策略**待定**（**未猜测**）。

## 7. Vercel 构建配置（`hugo/vercel.json`）

- `framework: hugo`、`buildCommand: hugo --gc --minify`、`outputDirectory: public`。
- `HUGO_VERSION=0.168.0`（**建议**同时在 Vercel 项目环境变量中设置）。
- 静态资源长缓存头；`trailingSlash: true`。
- **本阶段未创建任何 Vercel 项目、未部署。**

## 8. Jekyll 隔离（详见 `2026-11-12-jekyll-isolation-proposal.md`）

**实测复现**：含 `hugo/` 的分支上跑 `jekyll build`，会把 `hugo/layouts/*.html`、`hugo/README-HUGO.md`、
`docs/*` 当作旧站页面输出（泄漏 14 + 4 个文件）。
**提案**（**未实施于 main**）：在 `_config.yml` 的 `exclude` 增加 `hugo`、`docs`、`tools`、`PROGRESS.md`。
补丁后实测：泄漏 **0**，旧站 6 个页面**仍正常生成**。

## 9. 边界遵守声明

本阶段**未**：

- 修改 `main`、提交到 `main`、改 Pages 设置或分支保护；
- 改动旧站任何内容、DNS、域名、HTTPS、Vercel；
- 迁移任何真实诗歌正文、题记正文、小传正文；
- 拆分任何作品、编造任何作品归属。

所有写入均在**独立分支** `site/hugo-poetry-site-foundation`。
`main` 仍为 `ee94501c`。

## 10. 待作者/负责人决定

1. 6 篇合成样例是否保留（或改为 `draft`）；
2. 旧博客 305 篇的 URL 策略；
3. `/style.css` 兼容方案选择；
4. `_config.yml` 隔离补丁是否合入（涉及旧站，需授权）；
5. 是否创建 Vercel 预览项目（需授权）。
