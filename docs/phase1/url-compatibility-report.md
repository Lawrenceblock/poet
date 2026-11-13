# P1-G · URL 兼容与内容迁移报告

- 日期：2026-11-12
- 结论：**旧 URL 全部可保持；无 slug 冲突；`/review/` 不进入正式产物**

## 1. 旧 URL 规则（【已验证】）

- 旧诗站（Jekyll，`poet.ismaelan.com`）：`permalink: /:title/`，**扁平、无日期、带尾斜杠**。
- 旧博客（`www.ismaelan.com`）：`/YYYY/MM/slug.html`（**不同域名**）。

## 2. 旧 → 新 URL 对应表（【已验证】）

### 2.1 旧诗站扁平页面

| 旧 URL | 新 URL | 状态 |
| --- | --- | --- |
| `/` | `/` | 一致 |
| `/archive/` | `/archive/` | 一致 |
| `/preface/` | `/preface/` | 一致 |
| `/na-la-ti/` | `/na-la-ti/` | 一致 |
| `/qing-chun-de-wu-yu/` | `/qing-chun-de-wu-yu/` | 一致 |
| `/shi-ren-xiao-zhuan/` | `/shi-ren-xiao-zhuan/` | 一致 |
| `/style.css` | `/style.css` | 一致（静态文件逐字节相同） |
| `/assets/img/cover.png` | `/assets/img/cover.png` | 一致 |

实现方式：各文件 front matter 显式 `url:`；`/style.css` 与封面图置于 `hugo/static/`。

### 2.2 旧博客 305 篇

- 映射：`https://www.ismaelan.com/YYYY/MM/slug.html` → `https://poet.ismaelan.com/YYYY/MM/slug/`（去 `.html`、加尾斜杠）。
- 完整清单：`docs/migration/legacy-url-redirect-map.csv`（**305 行，与 305 篇清单一一对应，0 遗漏、0 多余**）。
- 实现方式：`hugo.toml` 的 `permalinks.posts = "/:year/:month/:slug/"`。

## 3. slug 冲突检查（【已验证】）

- 137 个候选：**全路径唯一**（137/137），无非标准路径。
- 305 篇博客：**全路径唯一**（305/305），无非标准路径。
- 末段 slug 重复（如 `blog-post`）**不构成冲突**，因为完整路径含年/月前缀后各不相同。
- **结论：只要保留 `/YYYY/MM/slug/` 结构，无冲突，无需改 slug。**
- 与站点保留路径（`archive`、`preface`、`years`、`search`、`about`、`legacy`、`index`、`review`、`style`、`sitemap`、`robots`）**无冲突**。

## 4. 迁移清单（【已验证】）

| 类别 | 数量 | 迁移方式 |
| --- | --- | --- |
| 扁平旧页（首页/卷目/题记/小传等） | 6 | front matter 显式 `url:` |
| 静态资源（style.css、封面图、favicon） | 3 | `hugo/static/` 原样保留 |
| 旧博客文章 | 305 | `permalinks.posts` 规则 |
| 审阅候选（文章级） | 137 | **不进入正式站**；仅存于审阅材料 |

## 5. 风险与待验证（【已知未解决】）

- **重定向归属**：`www.ismaelan.com` 的 301 必须由**旧主机**下发；本站（`poet.ismaelan.com`）无法替代。待项目负责人确认旧主机是否可控。**【待验证】**
- **外部旧链**：是否有第三方网站引用旧博客 URL，本轮**未做全网抓取**，无法确认。**【待验证】**
- **旧站线上渲染**：本轮以构建产物与仓库文件为准；线上 Jekyll 渲染细节未逐一比对。**【待验证】**

## 6. 边界声明

- 未修改任何 URL、重定向或部署配置；未触碰 DNS。**【已验证】**
