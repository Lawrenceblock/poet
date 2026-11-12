# 安然诗歌档案 · Hugo 站点（Phase B 完整框架）

> 本目录是 **Hugo 新站**，与仓库根目录的现有 Jekyll 站点**并存**。
> 现有线上站点（GitHub Pages，`main` 分支根目录）**不受本目录影响**。
>
> 分支：`site/hugo-poetry-site-foundation`
> 基础：PR #5 已审阅框架（`8dc57c3`）

## 构建环境

- **Hugo Extended v0.168.0**（含 SCSS/图片处理，构建必须用 extended）
  - 已验证：`hugo v0.168.0-e27a6760c5547237f87d353aebe0580feadb20f4+extended linux/amd64`
- Vercel 部署时需设置 **`HUGO_VERSION=0.168.0`**（项目环境变量优先，`vercel.json` 的 `build.env` 作为补充）。

## 本地构建

```bash
cd hugo
hugo --gc --minify                 # 生产构建 → ./public
hugo server -D                     # 本地预览（含草稿）
hugo --gc --minify -d /tmp/preview \
     --baseURL "https://poet-preview.example.vercel.app/"   # 预览域名构建
```

## 目录结构

```
hugo/
├─ hugo.toml                 # 配置：permalink /:slug/、hardWraps、typographer=false、菜单、搜索索引
├─ content/
│  ├─ archive.md             # url: /archive/  （卷目，按年份）
│  ├─ years.md               # url: /years/    （年份归档）
│  ├─ preface.md             # url: /preface/  （题记，占位）
│  ├─ shi-ren-xiao-zhuan.md  # url: /shi-ren-xiao-zhuan/（小传，占位）
│  ├─ about.md               # url: /about/    （档案说明）
│  ├─ search.md              # url: /search/   （站内搜索）
│  ├─ posts/                 # 诗歌（每篇显式 slug）；含 _index.md
│  └─ tests/                 # 排版测试（draft + build.render=never，不进正式构建）
├─ layouts/
│  ├─ _default/{baseof,single,list,archive,years,preface,about,search,rss.xml}
│  ├─ partials/{head-meta,pagination}.html
│  ├─ shortcodes/poem.html   # 诗歌分行保护短代码
│  ├─ index.html             # 首页
│  ├─ index.searchindex.json # 站内搜索索引
│  ├─ robots.txt
│  └─ 404.html
├─ assets/css/style.css      # 样式（Hugo Pipes 指纹化）
├─ static/{assets/img/cover.png, js/search.js}
└─ vercel.json
```

## 关键约定

1. **URL 兼容**：`permalinks.posts = "/:slug/"`，每篇**必须显式写 `slug`**
   （见 `../docs/migration/url-compatibility.md`）。
2. **诗歌分行**：`hardWraps = true`，行尾换行 → `<br>`；需要完全控制时用 `{{< poem >}}` 短代码。
3. **逐字保护**：`typographer = false`（不改引号/省略号/破折号）；
   `{{< poem >}}` 为**纯文本**（转义 HTML，不解释 `*`/`_`）；`.poem-verse{white-space:pre-wrap}` 保留行首/行尾空格。
4. **预览隔离**：仅当 `baseURL` 主机为 `poet.ismaelan.com` 时输出 canonical + `index,follow`；
   否则 `noindex,nofollow` 且 robots.txt `Disallow: /`。
5. **站内搜索**：纯前端读取 `/index.json`，无第三方依赖（当前仅覆盖合成样例）。
6. **本阶段不迁移正文**：`content/posts/` 仅含**明确标注的合成样例**（不是真实作品）。
