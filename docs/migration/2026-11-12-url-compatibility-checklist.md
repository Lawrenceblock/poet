# URL 兼容清单（Jekyll 旧站 → Hugo 新站）

> 日期：2026-11-12
> 分支：`site/hugo-poetry-site-foundation`
> 依据：旧站实测（`https://poet.ismaelan.com/`，逐页 `curl` 核对）+ 仓库 `_config.yml`
> 状态：**【建议】本阶段不修改旧站、不设置线上重定向。**

## 1. 旧站 permalink 规则（实测）

- `_config.yml`：`permalink: /:title/`
- 旧站页面为**扁平结构**：`/na-la-ti/`、`/qing-chun-de-wu-yu/`（无 `/posts/`、无日期）。
- 首页 `/`、卷目 `/archive/`、题记 `/preface/`、小传 `/shi-ren-xiao-zhuan/`。

## 2. Hugo 新站对应规则

- `permalinks.posts = "/:slug/"` → 每篇**显式 `slug`** 即可复现旧扁平 URL。
- 特殊页用 front matter `url:` 固定：`/archive/`、`/years/`、`/preface/`、`/shi-ren-xiao-zhuan/`、`/about/`、`/search/`。

## 3. 旧 → 新 URL 对应表

| 旧 URL（实测状态） | 新 Hugo URL | 是否一致 | 处理 |
| --- | --- | --- | --- |
| `/` | `/` | ✅ 一致 | — |
| `/archive/` | `/archive/` | ✅ 一致 | `content/archive.md` `url` |
| `/preface/` | `/preface/` | ✅ 一致 | `content/preface.md` `url` |
| `/shi-ren-xiao-zhuan/` | `/shi-ren-xiao-zhuan/` | ✅ 一致 | `content/shi-ren-xiao-zhuan.md` `url` |
| `/na-la-ti/` | `/na-la-ti/` | ✅ 计划一致 | 迁移时 `slug: na-la-ti` |
| `/qing-chun-de-wu-yu/` | `/qing-chun-de-wu-yu/` | ✅ 计划一致 | 迁移时 `slug: qing-chun-de-wu-yu` |
| `/style.css` | `/css/style.min.<hash>.css` | ❌ **不一致** | 见 §4 |
| `/assets/img/cover.png` | `/assets/img/cover.png` | ✅ 一致 | `static/assets/img/` |
| `/CNAME` | 无（Vercel 不需要） | — | Vercel 用项目域名，无需 CNAME 文件 |
| 旧博客 305 篇 `/YYYY/MM/xxx.html` | 见 §5 | ⚠️ **待定** | 见 §5 |

> 说明：`/na-la-ti/`、`/qing-chun-de-wu-yu/` 在本框架中**尚未迁入真实正文**，
> 因此当前新站**没有**这两个路径；上表为**迁移后应达到**的状态。

## 4. `/style.css` 不一致（需处理）

- 旧站页面引用 `/style.css`（部分页面为相对 `style.css`）。
- 新站 CSS 经 Hugo Pipes **指纹化**为 `/css/style.min.<hash>.css`，`/style.css` 会 **404**。
- **建议方案（择一，本阶段未实施）**：
  1. 在 `static/` 放一个 `style.css`（可用 `@import` 指向指纹文件，或直接复制）；
  2. 或在 Vercel `redirects`/`rewrites` 中把 `/style.css` 指向指纹文件；
  3. 或接受变更（旧 CSS 链接对新站意义有限，因为样式已重写）。
- **风险等级**：低（样式表链接失效不影响诗歌正文与阅读）。

## 5. 旧博客 305 篇 URL（**待定，需迁移决策**）

- 旧博客文章 URL 形如 `https://www.ismaelan.com/YYYY/MM/<slug>.html`（不同域）。
- 旧站（`poet.ismaelan.com`）目前**仅 3 篇**，与博客**不同域、不同路径**。
- **因此**：把博客文章迁入新站时，**旧博客 URL 与旧站 URL 是两套**：
  - 旧站 3 篇 → 保持 `/na-la-ti/` 等（见 §3）；
  - 旧博客 305 篇 → 新站路径**尚未决定**（`/:slug/`？保留 `/YYYY/MM/`？）。
- **【待验证】** 博客迁移的 URL 策略需作者/负责人确认后再定，**本阶段不猜测**。

## 6. 需要重定向的情况

| 情况 | 是否需要重定向 | 备注 |
| --- | --- | --- |
| `/style.css` | 可选 | 见 §4 |
| 旧博客 → 新站 | **待定** | 取决于 §5 决策 |
| 旧站 3 篇 | 否 | 路径保持一致 |

## 7. 路径冲突检查

- 新站特殊页 `/about/`、`/search/`、`/years/` 在旧站**不存在** → **无冲突**。
- 若某首诗的 `slug` 恰为 `archive`/`preface`/`about`/`search`/`years`，会与特殊页冲突 → **迁移时需检查**。
- **【建议】** 迁移脚本应对每篇 `slug` 做保留字校验。

## 8. 尚未迁移 / 需保留

- **尚未迁移**：旧站 3 篇正文、旧博客全部诗歌、题记正文、小传正文。
- **必须保留**：所有旧 URL（见 §3、§5）——迁移后**逐一比对**。
