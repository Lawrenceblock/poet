# 旧 URL 兼容方案（Jekyll → Hugo + Vercel）

> 本文件说明 Hugo 迁移中如何保持旧站 URL 不失效。
> 依据：`docs/audit/2026-11-12-pre-hugo-migration-audit.md` 的实测结果。
> 状态：**【建议】**，尚未实施迁移。

---

## 1. 旧站 URL 规则（**【已验证事实】**）

旧站 `_config.yml`：`permalink: /:title/`（自初始提交起未变）。
实测线上（2026-11-12）：

| 页面 | 旧 URL | 状态 |
| --- | --- | --- |
| 首页 | `/` | 200 |
| 卷目 | `/archive/` | 200 |
| 题记 | `/preface/` | 200 |
| 青春的物语 | `/qing-chun-de-wu-yu/` | 200 |
| 那拉提（未赴） | `/na-la-ti/` | 200 |
| 诗人小传 | `/shi-ren-xiao-zhuan/` | 200 |
| 静态样式 | `/style.css` | 200 |
| 封面图 | `/assets/img/cover.png` | 200 |
| README 中错误示例 | `/2026/09/07/na-la-ti/` | **404**（不存在） |

**结论**：旧站为**扁平、无日期、带尾斜杠**的 `/:slug/` 结构。

---

## 2. Hugo 的关键陷阱（**【已验证事实】**）

Hugo **不**默认用文件名生成 URL。经实测（v0.168.0）：

- `permalinks.posts = "/:slug/"` + 仅 `title` + `date` → URL 取 **`title` 的 slug 化**（中文标题会生成**中文 URL**，如 `/那拉提未赴/`），**与旧站不符**。
- `permalinks.posts = "/:contentbasename/"` → 保留**日期前缀**（`/2026-09-07-na-la-ti/`），**与旧站不符**。
- **`slug` 显式指定 + `/:slug/`** → 生成 **`/na-la-ti/`**，**与旧站完全一致**。

---

## 3. 采用的方案（**【建议】**）

### 3.1 核心规则

```toml
# hugo.toml
[permalinks]
  posts = "/:slug/"
```

**每篇内容必须在 Front Matter 显式给出 `slug`**，值 = 旧站 slug：

```yaml
---
title: "那拉提（未赴）"
date: 2026-09-07
slug: "na-la-ti"      # ← 与旧站 /na-la-ti/ 完全一致
---
```

### 3.2 页面 URL

`archive.md`、`preface.md` 用 Front Matter `url` 固定：

```yaml
# content/archive.md
url: "/archive/"
# content/preface.md
url: "/preface/"
```

### 3.3 静态资源

- `static/assets/img/cover.png` → `/assets/img/cover.png`（与旧站一致）
- **样式**：`assets/css/style.css` 经 Hugo Pipes `minify | fingerprint` 输出为
  **`/css/style.min.<hash>.css`**（**不是** `/style.css`）。
  - **【风险 · Phase 3】** 旧站 `/style.css`（线上 200）在新 Hugo 站**不存在**。
    若要保留旧 `/style.css` 链接，需在 `static/style.css` 另放一份（或加 Vercel 重定向）。
  - **【已验证事实】** 当前 `hugo/static/` 下**无** `style.css`。

---

## 4. 旧 URL → 新 URL 对应表（**【建议】**）

| 旧 URL | 新 URL（Hugo） | 保持方式 |
| --- | --- | --- |
| `/` | `/` | `layouts/index.html` |
| `/archive/` | `/archive/` | `content/archive.md` + `url` |
| `/preface/` | `/preface/` | `content/preface.md` + `url` |
| `/qing-chun-de-wu-yu/` | `/qing-chun-de-wu-yu/` | `slug: "qing-chun-de-wu-yu"` |
| `/na-la-ti/` | `/na-la-ti/` | `slug: "na-la-ti"` |
| `/shi-ren-xiao-zhuan/` | `/shi-ren-xiao-zhuan/` | `slug: "shi-ren-xiao-zhuan"` |
| `/style.css` | `/css/style.min.<hash>.css`（指纹） | ⚠️ 需另存 `static/style.css` 才可保留 `/style.css` |
| `/assets/img/cover.png` | `/assets/img/cover.png` | `static/assets/img/` |
| `/index.html` | `/index.html` | Hugo 首页同时生成（可选保留） |

> 未来新作品：**slug 由作者/维护者显式指定**，沿用扁平风格，避免中文 URL。

---

## 5. 重定向与别名策略（**【建议】**）

1. **首选**：URL 完全一致，无需重定向。
2. **双保险**：对每篇可加 Hugo `aliases`（仅在 URL 万一不一致时生效）：
   ```yaml
   aliases: ["/na-la-ti/"]
   ```
3. **尾斜杠**：Vercel 建议 `trailingSlash: true`，与旧站 `/na-la-ti/` 行为一致。
4. **旧日期 URL**：README 中的 `/2026/09/07/na-la-ti/` **从未存在**（404），**无需**为其建立重定向。
5. **GitHub Pages 备用入口**：`lawrenceblock.github.io/poet/*` 现 301 到自定义域名。若迁移后停用 Pages，需评估是否保留该入口（**【待验证】**）。

---

## 6. 迁移后必须逐条验证（**【建议】**）

对第 4 节表中**每一个旧 URL**，在新站上 curl 验证：
- 返回 **200**；
- 正文与旧站**逐字一致**（含标点、空格、分行）。

**未通过验证前，不得切换正式域名。**

---

## 7. 待验证 / 待决策

- **【待验证】** 是否有外部网站引用旧诗歌 URL（本次无外链分析工具授权）。
- **【待决策】** 是否保留 `lawrenceblock.github.io/poet/` 备用入口。
- **【待决策】** 未来新作品 slug 命名规范（建议 ASCII 拼音/英文）。
