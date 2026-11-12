# 安然诗客栈 · Hugo 站点（迁移框架）

> 本目录是 **Hugo 迁移框架**，与仓库根目录的现有 Jekyll 站点**并存**。
> 现有线上站点（GitHub Pages，`main` 分支根目录）**不受本目录影响**。

## 构建环境

- **Hugo Extended v0.168.0**（`hugo_extended_0.168.0_linux-amd64`）
  - 已验证可用：`hugo v0.168.0-e27a6760c5547237f87d353aebe0580feadb20f4+extended linux/amd64`
  - 注意：构建需使用 **extended** 版本（含 SCSS/图片处理）。
- Vercel 部署时需在项目设置中指定 `HUGO_VERSION=0.168.0`（或使用官方 Hugo 构建镜像）。

## 本地构建

```bash
cd hugo
hugo --minify --gc          # 输出到 ./public
hugo server -D              # 本地预览（含草稿）
```

## 目录结构

```
hugo/
├─ hugo.toml                 # 配置（permalink /:slug/、hardWraps、SEO）
├─ content/
│  ├─ archive.md             # url: /archive/
│  ├─ preface.md             # url: /preface/
│  └─ posts/                 # 诗歌（每篇需显式 slug）
├─ layouts/
│  ├─ _default/{baseof,single,list,archive,preface,rss.xml}
│  ├─ index.html             # 首页
│  ├─ 404.html
│  ├─ robots.txt
│  └─ shortcodes/poem.html   # 诗歌分行保护短代码
├─ static/assets/img/cover.png
├─ assets/css/style.css
├─ archetypes/posts.md
├─ ../../docs/migration/url-compatibility.md
└─ vercel.json
```

## 关键约定

1. **URL 兼容**：`permalinks.posts = "/:slug/"`，每篇**必须显式写 `slug`**（见 `../../docs/migration/url-compatibility.md`）。
2. **诗歌分行**：`markup.goldmark.renderer.hardWraps = true`，行尾换行渲染为 `<br>`；如需完全控制，用 `{{< poem >}}` 短代码。
3. **原文保护**：**逐字保留**诗歌正文，不润色、不删减。双语作品中英分段保留。
4. **本阶段不迁移正文**：仅建立框架；`content/posts/` 仅含一个 `draft` 验证样例。
