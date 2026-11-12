# 安然诗客栈 · 迁移前技术审计报告（Jekyll → Hugo + Vercel）

> 本报告为**独立只读技术审计**，不是迁移实施记录。所有结论基于对 GitHub 仓库、GitHub 配置、DNS 与线上页面的实际核查。报告严格区分 **【事实】**（已实测/已读文件）、**【推断】**（由证据合理推得，尚未直接验证）、**【建议】**（主观方案）。
>
> 审计者角色：独立审计员（非项目开发者）。未对原站、`main` 分支、域名、DNS、GitHub Pages 设置或 Vercel 做任何修改。

---

## 1. 审计日期

- 审计执行时间：**2026-11-12**（UTC 约 06:05–06:15）
- 报告文件：`docs/audit/2026-11-12-pre-hugo-migration-audit.md`
- 冲突检查：审计开始时仓库根目录**不存在** `docs/` 目录，故未覆盖任何历史报告。

---

## 2. 仓库地址与审计提交 SHA

| 项目 | 值 |
| --- | --- |
| 仓库 | https://github.com/Lawrenceblock/poet |
| 默认分支 | `main` |
| 审计提交 SHA（HEAD） | `ee94501c321c9eddbaff3c2421e7fa05428850fa` |
| 该提交时间 / 作者 | 2026-09-13 07:07:24 +0800 / ismaelan |
| 该提交信息 | `Update index.html`（为诗人小传页面添加自定义二级链接 https://bio.ismaelan.com/） |
| 仓库可见性 | public（**事实**：`gh api repos/...` 返回 `"visibility":"public"`） |
| 仓库创建时间 | 2026-09-07T02:17:52Z |
| 最近 push 时间 | 2026-09-12T23:07:24Z |
| 仓库大小 | 218 KB（GitHub 计量） |
| 仓库描述 | `My poem collection` |
| License | 无 |

**所有结论均针对 SHA `ee94501c321c9eddbaff3c2421e7fa05428850fa`。** 若 `main` 在审计后发生变更，本报告结论需以该 SHA 为准重新核对。

---

## 3. 审计范围

1. **仓库完整性**：默认分支、提交历史、完整目录树、全部文件（非仅 README）、文件计数、未纳入版本控制的文件、分支/标签/PR/Issue 保留需求。
2. **Jekyll 构建与发布机制**：`_config.yml`、GitHub Pages 发布来源、Actions 工作流、插件/主题/Gemfile、permalink、Front Matter、Liquid 模板。
3. **诗歌与文学内容保护**：全部文章清单（路径/标题/日期/标签/别名）、双语内容、HTML/内联样式/特殊换行、外部资源引用、非诗歌页面、内容重复与格式异常。
4. **永久链接与 SEO**：实际 permalink、每篇文章 URL、首页/卷目/题记/小传 URL、站内链接写法、旧链接失效风险。
5. **视觉与用户体验**：首页、封面、卷目、题记、阅读页、移动端、字体行距、中英混排、导航、返回卷目、加载与可访问性。
6. **域名与部署状态**（只读）：GitHub Pages 状态、自定义域名、CNAME、HTTPS、DNS 记录、是否存在旧托管关系。
7. **Hugo + Vercel 迁移可行性**：目录结构、内容映射、Front Matter 转换、模板转换、permalink 兼容、静态资源、Vercel 配置、预览隔离、逐页比对、验收条件、回滚。

**明确排除**：`bio.ismaelan.com` 是另一个独立站点，本报告不审查、不修改、不迁移它。仅在“确认二者相互独立”的范围内引用其存在。

---

## 4. 检查过的文件与目录

### 4.1 完整受版本控制文件清单（**事实**：`git ls-files`，共 **13 个文件**）

| 文件 | 字节 | 行 | 类型 |
| --- | ---: | ---: | --- |
| `CNAME` | 17 | 1 | 域名文件 |
| `README.md` | 4905 | 161 | 运维备忘 |
| `_config.yml` | 1209 | 44 | Jekyll 配置 |
| `_layouts/default.html` | 212 | 11 | 布局 |
| `_layouts/post.html` | 301 | 14 | 布局 |
| `_posts/2026-04-07-qing-chun-de-wu-yu.md` | 2563 | 112 | 诗歌（中英双语） |
| `_posts/2026-09-07-na-la-ti.md` | 412 | 26 | 诗歌 |
| `_posts/2026-09-11-shi-ren-xiao-zhuan.md` | 3330 | 79 | 诗人小传 |
| `archive.md` | 593 | 22 | 卷目页 |
| `assets/img/cover.png` | 195938 | — | 封面图（PNG，632×679） |
| `index.html` | 1642 | 85 | 首页 |
| `preface.md` | 590 | 24 | 题记页 |
| `style.css` | 1706 | 105 | 全局样式 |

按类型统计：**Markdown 6、HTML 3、CSS 1、PNG 1、其他 2（`CNAME`、`_config.yml`）**。
`_posts/` 目录下文章数：**3**。

### 4.2 未纳入版本控制的文件（**事实**）

- 工作区 `git status` 干净；`find` 结果与 `git ls-files` 完全一致。
- **不存在** `.gitignore`、`.nojekyll`、`Gemfile`、`Gemfile.lock`、`vendor/`。
- `_config.yml` 的 `exclude:` 列出了 `README.md`、`元宝代码`、`vendor`、`Gemfile`、`Gemfile.lock`；其中 **`元宝代码`、`vendor`、`Gemfile`、`Gemfile.lock` 在仓库中均不存在**（**事实**：逐项 `[ -e ]` 检测为 MISSING）。这些排除项属于无效/历史残留配置，非“未纳入版本控制的重要文件”。

### 4.3 历史提交与分支（**事实**）

- 提交总数（全 ref）：**14**。
- 分支：仅 `main`（本地与远端）。无其他分支。
- 标签：**无**。Release：**无**。
- PR：**无**（`state=all` 为空）。Issue：**无**。
- Stash：**无**。`git log --diff-filter=D` 显示 **历史上从未删除过任何文件**。
- 提交历史（正序）：

```
375ee79 init: 安然诗客栈基础站点
3f063c5 fix: nav links to archive/preface permalinks
8ee014d fix: use permalink paths for archive/preface
09e2f24 Create CNAME
afba0bd fix: nav links for custom domain
f5963d3 fix: post back link to /archive/
5cc132f add: README AND 青春的物语
7524485 fix: 青春物语正文换行/诗节
ba67ceb Update 2026-04-07-qing-chun-de-wu-yu.md
ca206d7 Update 2026-04-07-qing-chun-de-wu-yu.md
d221bc0 Update index.html
70046c8 Update index.html
f53a918 Add files via upload
ee94501 Update index.html
```

**需要保留的内容**：全部 14 个提交构成完整的文学与配置演进史（含两次“青春物语正文换行/诗节”修订），是唯一的历史记录，迁移时**必须完整保留 `main` 分支与全部历史**。

### 4.4 特别核实项（任务点名文件）与实际结构差异

| 任务点名 | 实际 | 说明 |
| --- | --- | --- |
| `_config.yml` | ✅ 存在 | — |
| `_posts/` | ✅ 存在 | 含 3 个 `.md` |
| `_layouts/` | ✅ 存在 | `default.html`、`post.html` |
| `index.html` | ✅ 存在 | — |
| `archive.md` | ✅ 存在 | — |
| `preface.md` | ✅ 存在 | — |
| `style.css` | ✅ 存在 | — |
| `assets/` | ✅ 存在 | 仅 `assets/img/cover.png` |
| `CNAME` | ✅ 存在 | 内容 `poet.ismaelan.com` |
| `README.md` | ✅ 存在 | — |

**实际结构与任务列表一致，无额外未点名的重要文件。**

---

## 5. 当前技术架构

### 5.1 构建与发布（**事实**）

- **框架**：Jekyll，`markdown: kramdown`，`highlighter: rouge`。
- **发布来源**：GitHub Pages **legacy 构建**。`gh api repos/Lawrenceblock/poet/pages` 返回 `"build_type":"legacy"`、`"source":{"branch":"main","path":"/"}`。
- **Actions 工作流**：仅 1 个，名为 `pages-build-deployment`，路径 `dynamic/pages/pages-build-deployment`——这是 **GitHub Pages 内置的构建工作流**（由平台动态生成），**不是**仓库自有的 `.github/workflows/` 文件。**事实**：`gh api .../contents/.github` 返回 404，仓库中**不存在 `.github/` 目录**。
- **是否依赖 GitHub Pages 内置 Jekyll**：**是**。无自定义构建、无 Gemfile、无插件声明，完全依赖 Pages 内置 Jekyll 运行时。
- **最近构建**：`workflow_runs` 显示最近 5 次 `pages build and deployment` 全部 `success`，最新一次对应 `ee94501c`。

### 5.2 关键配置（**事实**：`_config.yml`）

```yaml
title: 安然诗客栈
author: 安然
description: 未赴之境 · 安然诗集
lang: zh-CN
repository: Lawrenceblock/poet
url: "https://poet.ismaelan.com"
baseurl: ""
markdown: kramdown
highlighter: rouge
permalink: /:title/
paginate: 10
paginate_path: "/page:num/"
defaults:
  - scope: {path: "", type: "posts"}   -> layout: post
  - scope: {path: "", type: "pages"}   -> layout: default
exclude: [README.md, 元宝代码, vendor, Gemfile, Gemfile.lock]
github: {is_public: true}
```

**重要发现（**事实**）**：`permalink: /:title/` 自初始提交 `375ee79` 起从未改变（`git log -p -- _config.yml` 全历史均为此值）。

**README 与配置不一致（**事实**）**：`README.md` 第 71 行声称“诗歌正文：由 Jekyll 按日期自动生成，如 `/2026/09/07/na-la-ti/`”。这与 `_config.yml` 的 `permalink: /:title/` **矛盾**。实测线上 `/2026/09/07/na-la-ti/` 返回 **404**，而 `/na-la-ti/` 返回 **200**——**证明 README 该处描述错误，应以 `_config.yml` 为准**。

### 5.3 模板与 Liquid 逻辑（**事实**）

- `_layouts/default.html`：输出 `{{ page.title }} · 安然诗客栈`，引入 `/style.css`，输出 `{{ content }}`。
- `_layouts/post.html`：`layout: default`；输出 `{{ page.title }}`、`{{ page.date | date: "%Y.%m.%d" }}`、`{{ content }}`，并含固定返回链接 `<a href="/archive/">← 卷目</a>`。
- `archive.md`：`layout: default`，`permalink: /archive/`；核心 Liquid 循环：

```liquid
{% for post in site.posts %}
  <div class="archive-item">
    <span class="idx">{{ forloop.index }}</span>
    <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    <span class="dots"></span>
    <span class="date">{{ post.date | date: "%Y.%m" }}</span>
  </div>
{% endfor %}
```

- `preface.md`：`layout: default`，`permalink: /preface/`；**含一条冗余的 `<link rel="stylesheet" href="style.css">`**（相对路径）。
- `index.html`：**纯静态 HTML，无任何 Front Matter，无 Liquid**；内联 `<style>` 与 `style.css` 中 `.cover/.title/.copy/.note` 等规则**重复定义**（首页内联样式为权威版本）。

### 5.4 Jekyll 特有、迁移 Hugo 时需处理的内容（**事实/推断**）

1. **Liquid 循环 + 过滤器**：`{% for %}`、`forloop.index`、`| relative_url`、`| date:`。Hugo 无 Liquid，需改用 Go 模板（`range`、`.Permalink`、`.Date.Format`）。**【事实】**
2. **`site.posts` 排序**：Jekyll 默认按日期倒序（最新在前）。实测 `/archive/` 顺序为：诗人小传(2026-09-11) → 那拉提(2026-09-07) → 青春的物语(2026-04-07)。**【事实】** Hugo 默认同样按日期倒序，但需显式确认。
3. **Kramdown 与 Hugo Goldmark 的行为差异**：见第 6 节，这是本审计最关键的迁移风险。**【事实+推断】**
4. **`_posts/` 日期前缀命名**：Hugo 的 `content/posts/` 可沿用，但 Hugo 优先使用 Front Matter 的 `date`。
5. **`paginate` 配置**：当前站点只有 3 篇文章、无分页页面输出，`paginate` 实际未生效。**【推断】**（线上无 `/page2/` 类页面）。

---

## 6. 内容资产清单

### 6.1 文章总表（**事实**：逐文件读取 + 线上核对）

| # | 文件路径 | 标题 | 日期 | 标签 | 别名 | 线上 URL | 内容形态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `_posts/2026-04-07-qing-chun-de-wu-yu.md` | 青春的物语 | 2026-04-07 | `[诗歌]` | 无 | `/qing-chun-de-wu-yu/` | **中英双语**，纯 HTML |
| 2 | `_posts/2026-09-07-na-la-ti.md` | 那拉提（未赴） | 2026-09-07 | `[新疆, 未赴]` | 无 | `/na-la-ti/` | 中文，HTML 包裹纯文本 |
| 3 | `_posts/2026-09-11-shi-ren-xiao-zhuan.md` | 诗人小传 | 2026-09-11 | `[#诗人, #传记, #回族, #文学]` | `安然`、`崔浩新`、`伊斯玛义勒` | `/shi-ren-xiao-zhuan/` | 中文 Markdown（标题/引用/有序列表） |

**文章总数 = 3。** 其中**真正的“诗”为 2 篇**（青春的物语、那拉提）；第 3 篇是**诗人小传**（传记性非诗歌内容，虽置于 `_posts/`）。

Front Matter 字段汇总（**事实**）：
- 文章 1：`layout, title, date, author, tags`（**唯一含 `author` 的文章**）
- 文章 2：`title, date, layout, tags`
- 文章 3：`title, aliases, tags, created, modified`（**无 `date` 字段**；`layout` 由 `_config.yml` 的 defaults 注入为 `post`）

> ⚠️ 注意：文章 3 的 `tags` 使用了带 `#` 前缀的 Obsidian 风格标签（`#诗人` 等），且含 `created/modified`——这明显是从 **Obsidian/元宝导出** 的笔记格式，非标准 Jekyll Front Matter 惯例。文章 3 的 `aliases` 是 Obsidian 别名，**Jekyll 不识别**。

### 6.2 逐篇内容特征与排版细节（**事实**）

**文章 1 `青春的物语`（中英双语）**
- 结构：`<div class="poem">` 内含中文诗（`<div style="text-align: center;">` + 大量 `<br>`），随后**字面 `---` 分隔行**，再是两个英文 `<div style="text-align: center;">` 块。
- 特殊排版：大量 `<br>` 强制换行；英文块内使用了 **Markdown 语法写在 HTML `<div>` 内**（`**Youth's Tale**`、`*by **An Ran** *`）——**Kramdown 未转换它们**，线上原样输出星号。**【事实】**（实测线上 `**Youth's Tale**` 与 `*by **An Ran** *` 字面出现）
- 字面 `---`：位于两个 `<div>` 之间、前后有空行，**Kramdown 未渲染为 `<hr>`**，线上**原样输出 `---` 三个字符**。**【事实】**（实测线上第 63 行输出 `---`，`<hr` 检索为 0）
- 外部资源：**无**图片、无外链。
- 双语：中文在前、英文在后，**逐段对应**（非逐行对照）。

**文章 2 `那拉提（未赴）`**
- 结构：`<div class="poem">` + **纯文本诗行**（无内联 style），诗节之间用 `<br>` 分隔。
- **特殊换行（关键）**：正文诗行采用 **Markdown 行尾双空格硬换行**（`  ` 结尾），共 **9 处**（实测）。线上渲染为**同一段落内的 `<br>` 换行**。
- **实测渲染结果**：由于外层是原始 HTML `<div class="poem">`，Kramdown 对块级 HTML 内部**不做 Markdown 处理**，行尾双空格被保留为**字面尾随空格**而非 `<br>`；浏览器对空白折叠后，**诗行之间的换行丢失**——实测 `innerText` 显示第一诗节被折叠为一行：`那拉提的风我没能赶上 北门外的雪替我去了`（两行挤在一行），仅 `<br />` 处换行。**【事实，已用无头浏览器实测】**
- 外部资源：**无**。

**文章 3 `诗人小传`**
- 结构：H1 标题（`# 诗人小传`、`# 此生行止`）、引用块（`>`）、H2（`## 年谱`）、12 项有序列表（含加粗年份标题 + 缩进段落）。
- 含**个人敏感信息**（生日、籍贯、民族、亲属命名、被问话/拘留经历等）。**迁移时须原样保留，不得改写、脱敏或删减。**
- Front Matter 含 Obsidian 风格 `aliases` 与 `#` 标签。
- 外部资源：**无**（正文提到 `@ismaelan` 与“X/Twitter”，但无超链接）。

### 6.3 非诗歌页面（**事实**）

| 页面 | 文件 | 说明 |
| --- | --- | --- |
| 首页 | `index.html` | 封面 + 站名 + 三个导航（卷目/题记/小传） |
| 卷目 | `archive.md` | 自动生成目录 |
| 题记 | `preface.md` | 手写 HTML 散文 |

### 6.4 图片、附件与外部资源（**事实**）

- **图片**：全站仅 **1 张**——`assets/img/cover.png`（632×679，195938 字节），仅首页引用（`<img src="assets/img/cover.png">`，相对路径）。
- **外部链接**：全站仅 **1 条**——首页“小传”指向 `https://bio.ismaelan.com/`（2026-09-13 由 `https://grokpoet.vercel.app/` 改来，见 `ee94501` diff）。
- **历史旧外链**：`https://grokpoet.vercel.app/`（旧“小传”地址）。**事实**：该域名仍可访问（HTTP 200），但**是否仍被外部引用未验证**。
- 内容中**无**其他图片、附件、CDN、字体文件或第三方脚本。

### 6.5 内容重复、失效链接与格式异常（**事实/推断**）

- **格式异常 1（**事实**）**：`青春的物语` 英文块中的 `**…**` / `*…*` 未渲染为加粗/斜体，**线上显示字面星号**。
- **格式异常 2（**事实**）**：`青春的物语` 的字面 `---` **未渲染为分隔线**，线上显示字面 `---`。
- **格式异常 3（**事实**）**：`那拉提（未赴）` 依赖行尾双空格换行，但因处于原始 HTML 块中而**未生效**，诗行被折叠。
- **样式缺失（**事实**）**：`.poem`、`.archive`、`.archive-item`、`.preface`、`.sign`、`.site-name`、`.sub`、`.idx`、`.dots`、`.date`、`.nav-sep` 等**在 `style.css` 中均无定义**（`style.css` 只定义了 `.poem-*` 系列与 `.cover/.title/.copy/.note`）。因此卷目页、题记页、诗歌外层容器**实际无专属样式**，全靠浏览器默认排版。`.poem-content p { text-indent: 2em }` 也基本不生效（诗歌正文几乎不产生 `<p>`）。
- **`preface.md` 冗余/失效样式（**事实**）**：`<link rel="stylesheet" href="style.css">` 为**相对路径**，在 `/preface/` 下解析为 `/preface/style.css`，**实测返回 404**（无效），但 `_layouts/default.html` 已用绝对路径 `/style.css` 引入，故视觉无影响。
- **内容重复**：**未发现**文章内容重复。
- **站内链接**：仅 `index.html`（`/archive/`、`/preface/`）、`_layouts/post.html`（`/archive/`）含站内链接，写法统一为**绝对根路径 + 尾斜杠**，实测均 200。
- **未发现失效站内链接**。

---

## 7. 永久链接与 URL 风险

### 7.1 实际 URL 规则（**事实**）

- 文章：`permalink: /:title/` → `/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/shi-ren-xiao-zhuan/`。
- 卷目：Front Matter `permalink: /archive/`。
- 题记：Front Matter `permalink: /preface/`。
- 首页：`/`（`index.html`）。
- 无日期层级、无 `.html` 后缀、**URL 带尾斜杠**。实测 `/na-la-ti`（无尾斜杠）**301 重定向**到 `/na-la-ti/`。

### 7.2 线上实测状态码（**事实**，全部实测于 2026-11-12）

| URL | 状态 |
| --- | --- |
| `https://poet.ismaelan.com/` | 200 |
| `https://poet.ismaelan.com/archive/` | 200 |
| `https://poet.ismaelan.com/preface/` | 200 |
| `https://poet.ismaelan.com/na-la-ti/` | 200 |
| `https://poet.ismaelan.com/qing-chun-de-wu-yu/` | 200 |
| `https://poet.ismaelan.com/shi-ren-xiao-zhuan/` | 200 |
| `https://poet.ismaelan.com/2026/09/07/na-la-ti/` | **404**（README 所声称的格式，实际不存在） |
| `https://poet.ismaelan.com/index.html` | 200 |
| `https://poet.ismaelan.com/na-la-ti`（无斜杠） | 301 → `/na-la-ti/` |
| `https://poet.ismaelan.com/archive`（无斜杠） | 301 → `/archive/` |
| `https://poet.ismaelan.com/404.html` | 404（无自定义 404 页） |
| `https://poet.ismaelan.com/robots.txt` | 404 |
| `https://poet.ismaelan.com/sitemap.xml` | 404 |
| `https://poet.ismaelan.com/feed.xml` | 404 |
| `https://poet.ismaelan.com/style.css` | 200（1706 字节） |
| `https://poet.ismaelan.com/assets/img/cover.png` | 200（195938 字节，image/png） |
| `https://poet.ismaelan.com/CNAME` | 200（内容 `poet.ismaelan.com`，即 CNAME 文件被发布） |
| `https://poet.ismaelan.com/preface/style.css` | **404**（preface 相对路径失效） |
| `https://poet.ismaelan.com/README.html` | 404（README 已被 exclude，未发布） |
| `https://lawrenceblock.github.io/poet/` | **301**（跳转至自定义域名） |

### 7.3 旧 URL → 建议新 URL 对应表（**建议**，用于 Hugo 迁移）

| 旧 URL（Jekyll 现状） | 建议 Hugo 目标 URL | 保持策略 | 状态 |
| --- | --- | --- | --- |
| `/` | `/` | Hugo 首页 `layouts/index.html` 或 `content/_index.md` | **必须保持** |
| `/archive/` | `/archive/` | `content/archive.md` + `url: /archive/` 或 `aliases` | **必须保持** |
| `/preface/` | `/preface/` | `content/preface.md` + `url: /preface/` | **必须保持** |
| `/na-la-ti/` | `/na-la-ti/` | 见下方 permalink 兼容策略 | **必须保持** |
| `/qing-chun-de-wu-yu/` | `/qing-chun-de-wu-yu/` | 同上 | **必须保持** |
| `/shi-ren-xiao-zhuan/` | `/shi-ren-xiao-zhuan/` | 同上 | **必须保持** |
| `/index.html` | `/index.html` | 次要；Hugo 默认 `/` 即 200 | 建议保持（可选） |
| `/style.css` | `/style.css` | 静态资源放 `static/style.css` | 建议保持 |
| `/assets/img/cover.png` | `/assets/img/cover.png` | 放 `static/assets/img/` | **必须保持**（避免外链失效） |
| `/CNAME` | 不再需要 | Vercel 不用 CNAME 文件；如保留需评估是否仍发布 | 可移除（Vercel 环境） |
| `https://lawrenceblock.github.io/poet/*` | 保持重定向至 `poet.ismaelan.com/*` | 迁移后 GitHub Pages 若停用，需评估该备用入口 | **待验证** |

**待验证项（不得猜测）**：
- 【待验证】是否存在**外部网站**引用 `poet.ismaelan.com` 的具体诗歌 URL。本次审计**未检索外部引用来源**（无访问搜索引擎/外链分析工具的授权），无法确认外部反向链接分布。
- 【待验证】`https://grokpoet.vercel.app/`（旧“小传”地址）是否仍被外部引用、是否有历史流量。
- 【待验证】`lawrenceblock.github.io/poet/` 301 目标是 GitHub Pages 自动行为还是显式配置，迁移后是否仍需保留该备用入口。

### 7.4 URL 风险结论（**推断**）

- 现状 URL 结构**极其简单**（扁平 `/:title/`），**迁移到 Hugo 保持完全一致的成本很低**——这是本次迁移的有利条件。
- **唯一高风险动作**：若 Hugo 采用默认的 `/:year/:month/:title/` 或 `/posts/:title/`，将导致**全部现有诗歌链接失效**。**【建议】必须显式配置 `permalinks` 保持扁平结构。**
- 由于现有文章 slug 为拼音（`na-la-ti` 等），Hugo 从文件名生成 slug 时**默认行为与 Jekyll 一致**（取文件名去掉日期前缀），风险可控。**【推断】**

---

## 8. GitHub Pages 与域名状态

### 8.1 GitHub Pages（**事实**，`gh api repos/Lawrenceblock/poet/pages`）

```json
{
  "status": "built",
  "cname": "poet.ismaelan.com",
  "custom_404": false,
  "html_url": "https://poet.ismaelan.com/",
  "build_type": "legacy",
  "source": {"branch": "main", "path": "/"},
  "public": true,
  "https_certificate": {"state": "approved", "domains": ["poet.ismaelan.com"], "expires_at": "2027-02-04"},
  "https_enforced": true
}
```

- Pages 状态：**built**（已构建）。
- 发布源：**`main` 分支根目录**，**legacy 构建**（非 Actions 自定义）。
- HTTPS：**强制启用**（`https_enforced: true`），证书**已批准**，覆盖 `poet.ismaelan.com`，**2027-02-04 到期**。
- 实测 HTTP → HTTPS：`http://poet.ismaelan.com/` **301 → https://poet.ismaelan.com/**（**事实**）。
- 无自定义 404 页（`custom_404: false`，实测 `/404.html` 404）。

### 8.2 自定义域名与 CNAME（**事实**）

- 仓库根 `CNAME` 文件内容：`poet.ismaelan.com`（**事实**，实测线上 `/CNAME` 也返回该内容）。
- GitHub Pages 配置的 `cname`：`poet.ismaelan.com`。**两者一致。**

### 8.3 DNS（**事实**，通过 Cloudflare DoH 与系统解析实测）

| 查询 | 结果 |
| --- | --- |
| `poet.ismaelan.com` CNAME | `lawrenceblock.github.io.`（TTL 3600） |
| `poet.ismaelan.com` A | 185.199.108.153 / .109.153 / .110.153 / .111.153（GitHub Pages 官方 IP 段） |
| `ismaelan.com` NS | `ns05.domaincontrol.com.`、`ns06.domaincontrol.com.`（**GoDaddy 托管 DNS**） |
| `ismaelan.com` apex A | 15.197.225.128、3.33.251.168（非 GitHub Pages 段；apex 与本站无关） |
| `bio.ismaelan.com` | 216.198.79.131、64.29.17.131（**Vercel**；与本站不同托管） |

- **结论（**事实**）**：`poet` 子域的 CNAME 正确指向 `lawrenceblock.github.io.`，与 GitHub Pages 官方要求一致。DNS 解析正常，HTTPS 生效。
- **`poet` 与 `bio` 分属不同托管**：`poet` → GitHub Pages；`bio` → Vercel（实测响应头 `server: Vercel`）。**二者确为独立站点。**

### 8.4 旧部署或其他托管关系（**事实/推断**）

- 【事实】首页“小传”链接现指向 `bio.ismaelan.com`，其上一版本（`ee94501` 之前）指向 `https://grokpoet.vercel.app/`。
- 【事实】`grokpoet.vercel.app` 当前仍可访问（200），说明**曾存在一个 Vercel 部署**，其与 `bio.ismaelan.com` 的关系**待验证**。
- 【推断】`grokpoet.vercel.app` 很可能是 `bio.ismaelan.com` 的早期 Vercel 部署地址或独立项目；**本报告不审查、不修改 bio 相关项目**。
- 【事实】仓库内**无**任何 Vercel 配置（无 `vercel.json`、无 `.vercel/`），本站当前**与 Vercel 无部署关系**。

---

## 9. 视觉与用户体验问题（现状评估，未做任何修改）

评估基于线上实测（含无头浏览器 390px / 1280px 视口渲染）与 CSS 静态分析。

### 9.1 首页（`/`）— 实测

- 布局：`body` 使用 flex 居中，`.cover` 最大 520px，封面图 `max-width: 360px; max-height: 52vh`，居中对齐。视觉为**安静、极简**风格，符合文学阅读定位。
- **封面图**：632×679 的 PNG，`object-fit: contain`，正常显示（实测 200，195938 字节）。
- **导航**：`卷目 · 题记 · 小传`，居中，`letter-spacing` 风格统一。
- 问题：
  - **【问题·事实】样式重复**：首页内联 `<style>` 与 `style.css` 对 `.cover/.title/.copy/.note` **重复定义**，且首页 HTML 只用了 `.site-name/.sub/.note` 类，而 `.title/.copy` 类**在 HTML 中未被使用**（`index.html` 里用的是 `site-name`/`sub`/`note`，但内联样式和 `style.css` 却定义 `.title`/`.copy`）。→ **样式与结构不匹配**，说明历史重构留下死代码。
  - **【问题·事实】缺少 viewport meta**：首页、卷目、题记、诗歌页**均无 `<meta name="viewport">`**。实测 iPhone 模拟下 `window.innerWidth = 980`、`visualViewport.scale ≈ 0.398`——移动端**被迫按 980px 桌面宽度渲染后整体缩放**，字体偏小、需双指放大，移动阅读体验差。**这是最明显的 UX 缺陷。**
  - **【问题·事实】无 `<meta name="description">`、无 canonical、无 Open Graph/Twitter Card**，社交分享与 SEO 表现弱。
  - **【问题·事实】`<title>` 为硬编码 `安然诗客栈`**（首页），无站点级 SEO 结构化。

### 9.2 卷目页（`/archive/`）— 实测

- 结构：`卷一 · 未赴之境` 标题 + 分隔线 + 3 条目录（序号、链接、点线、`YYYY.MM` 日期）+ 页脚。
- **【问题·事实】`.archive*` 类在 `style.css` 中无定义**，`.dots`（点线）、`.idx`、`.date` 均无样式。实际呈现为**无样式的默认列表**——卷目的“雅致”设计**未落地**。
- **【问题·事实】`.dots` 元素为空 `<span class="dots"></span>`**，即使有 CSS 也需要 `flex`/`border-bottom` 技巧才能呈现点线，当前完全没有。
- 排序：按日期倒序（小传→那拉提→青春），符合预期。
- 日期格式 `2026.09` 仅到月，与诗歌页 `2026.09.07` 不一致（设计取舍，非缺陷）。

### 9.3 题记页（`/preface/`）— 实测

- 手写 HTML 散文，`<p>` 段落 + `<br>` 断行，末尾 `.sign` 署名。
- **【问题·事实】`.preface`、`.sign` 在 `style.css` 中无定义**，呈现为默认段落样式（宋体、左对齐、无行距/字号调整）。
- **【问题·事实】冗余且失效的 `<link rel="stylesheet" href="style.css">`**（相对路径解析为 `/preface/style.css` → 404）。因布局已引入 `/style.css`，视觉未受影响，但属无效代码。

### 9.4 诗歌阅读页（`/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/shi-ren-xiao-zhuan/`）— 实测

- 结构：`.poem-page`（max-width 560px，`margin: 6em auto`）+ 标题 + 日期 + 正文 + 返回卷目。
- **【问题·事实，重要】诗歌换行丢失**：`那拉提（未赴）` 的正文诗行依赖行尾双空格换行，但外层为原始 HTML `<div class="poem">`，Kramdown 不处理其内部 Markdown，双空格未转成 `<br>`。实测 `innerText` 把第一诗节折叠成一行：`那拉提的风我没能赶上 北门外的雪替我去了`。**诗歌的分行结构在线上已被破坏**（仅显式 `<br />` 处换行）。
- **【问题·事实，重要】Markdown 语法未渲染**：`青春的物语` 英文块中的 `**Youth's Tale**`、`*by **An Ran** *` 线上显示**字面星号**；块间字面 `---` 未渲染为分隔线。
- **【问题·事实】`.poem` 类无样式**；`.poem-content p { text-indent: 2em }` 基本不生效（诗歌正文几乎无 `<p>`）。`.poem-content` 的 `line-height: 2.4` 生效，阅读行距舒适。
- **【事实】`诗人小传`** 是唯一真正走 Markdown 渲染的文章：H1/H2、引用块、有序列表、加粗均正常输出，阅读体验良好。
- **【事实】中英混排**：`青春的物语` 中英均用 `Songti SC/SimSun` 衬线字体，中文行距 2.4，英文在移动端**因无 viewport 而被缩得很小**；桌面端英文单行过长（实测单行宽达 559px，接近容器上限）。
- **【事实】返回卷目**：每篇诗歌页底部有 `← 卷目`，链接 `/archive/`，实测有效。

### 9.5 移动端（实测）

- **【问题·事实】无 viewport** → 移动端按 980px 宽渲染后缩放，字号过小，是**首要移动端问题**。
- 诗歌页 `.poem-page` 无移动端断点，`padding: 0 1.2em`，`max-width: 560px`——在无 viewport 的情况下未按真实移动宽度适配。
- 首页 `.cover` 使用 `%` 与 `max-*`，本身是响应式的，但受 viewport 缺失拖累。

### 9.6 中文字体与行距（**事实**）

- 字体栈：`"Songti SC", "SimSun", serif`——依赖**用户系统字体**，无 web font。Windows 回退 `SimSun`，macOS/iOS 用 `Songti SC`，Linux/Android 可能回退到默认衬线（**跨平台不一致**，【推断】）。
- 行距：`.poem-content` 2.4，首页标题 `letter-spacing: 0.32em`——**排版取向克制、雅致**，与“安静、以文学阅读为中心”的定位一致。

### 9.7 加载与可访问性（**事实**）

- 页面体积极小（诗歌页 ~773 字节 HTML + 1.7KB CSS + 首页 196KB 封面图）。**加载极快**。
- 缓存：GitHub Pages 返回 `cache-control: max-age=600`。
- **可访问性缺陷**：
  - 无 viewport（移动可读性差）。
  - `cover.png` 有 `alt="封面"`（✅）。
  - 无 `lang` 之外的语义化标签（诗歌页无 `<main>`/`<article>`，**推断**影响读屏语义）。
  - 导航 `<a>` 无 `aria-*`，但文本清晰，影响有限。
  - 颜色对比度：`#9aa3a6`/`#b8c0c2` 灰字于 `#dceef2` 底——**对比度偏低**（【推断】，未做 WCAG 量化计算），小字 `.note`（0.76rem）可能不易读。

### 9.8 改善建议（**建议**，仅针对未来设计阶段，本阶段不实施）

1. **补 `<meta name="viewport" content="width=device-width, initial-scale=1">`**（最高优先，直接修复移动端）。
2. 在 `style.css` 中补齐 `.archive*`、`.preface`、`.sign`、`.poem` 等缺失类，或删除未使用的死代码（`.title`/`.copy`）。
3. 统一首页样式来源，消除内联 `<style>` 与 `style.css` 的重复。
4. 修复诗歌换行：**统一改为纯 Markdown 或统一为纯 HTML `<br>`**，二者不混用（详见第 10 节）。
5. 移除 `preface.md` 中失效的相对样式链接。
6. 保持**安静、简洁、阅读中心**的风格；**不建议**引入博客资讯式侧栏、标签云、评论系统或复杂导航。

---

## 10. Hugo + Vercel 迁移可行性

> 以下全部为 **【建议】**。本阶段**不实施**任何迁移。

### 10.1 推荐 Hugo 目录结构

```
poet-hugo/
├─ hugo.toml                      # 或 config/_default/*.toml
├─ content/
│  ├─ _index.md                   # 首页内容（可选）
│  ├─ archive.md                  # url: /archive/
│  ├─ preface.md                  # url: /preface/
│  └─ posts/
│     ├─ na-la-ti.md
│     ├─ qing-chun-de-wu-yu.md
│     └─ shi-ren-xiao-zhuan.md
├─ layouts/
│  ├─ _default/
│  │  ├─ baseof.html              # 对应 default.html
│  │  ├─ single.html              # 对应 post.html
│  │  └─ list.html
│  └─ index.html                  # 首页（对应 index.html）
├─ static/
│  ├─ style.css                   # 对应 /style.css
│  └─ assets/img/cover.png        # 对应 /assets/img/cover.png
└─ vercel.json                    # 构建与缓存配置
```

**关键点**：`static/` 下的路径即站点根路径，因此 `static/style.css` → `/style.css`、`static/assets/img/cover.png` → `/assets/img/cover.png`，**与现状完全一致**。

### 10.2 Jekyll 内容如何映射到 Hugo

| Jekyll | Hugo | 说明 |
| --- | --- | --- |
| `_posts/*.md` | `content/posts/*.md` | 保留原文件名（Hugo 从文件名推 slug，行为与 Jekyll 一致） |
| `index.html`（无 FM） | `layouts/index.html` | 纯静态首页直接作为 Hugo 首页模板 |
| `archive.md` | `content/archive.md` | Front Matter 加 `url: /archive/` |
| `preface.md` | `content/preface.md` | Front Matter 加 `url: /preface/` |
| `_layouts/default.html` | `layouts/_default/baseof.html` | `{{ content }}` → `{{ block "main" . }}` |
| `_layouts/post.html` | `layouts/_default/single.html` | 见 10.4 |
| `style.css` | `static/style.css` | 原样复制，**逐字不改** |
| `assets/img/cover.png` | `static/assets/img/cover.png` | 原样复制 |
| `CNAME` | 不使用 | Vercel 以项目域名配置代替 |
| `README.md` | 不入 `content/` | 保留在仓库根作运维文档（Hugo 不发布根目录文件） |

### 10.3 Front Matter 转换策略（**建议**）

| Jekyll 字段 | Hugo 处理 | 备注 |
| --- | --- | --- |
| `layout: post` | **删除** | Hugo 依 `content/posts/` 目录自动选 `single.html` |
| `title` | 保留 | 完全相同 |
| `date` | 保留（补时间可加 `T00:00:00+08:00`） | 影响排序与 `.Date.Format` |
| `author` | 保留（可选转 `params.author`） | 仅文章 1 有 |
| `tags: [诗歌]` | 保留为 `tags` 数组 | Hugo 原生支持 |
| `tags: [#诗人, ...]`（文章 3） | **需清洗**：去掉 `#` 前缀 | Hugo 会原样输出 `#`，破坏标签 URL |
| `aliases: [安然, ...]`（文章 3） | **注意语义冲突** | Obsidian 的“别名”≠ Hugo 的 URL 别名（`aliases` 在 Hugo 表示重定向）。**建议改名为 `params.aliases` 或自定义字段**，避免 Hugo 生成错误重定向 |
| `created` / `modified`（文章 3） | 保留为自定义字段或 `lastmod` | 语义保留 |
| 文章 3 无 `date` | **必须补 `date: 2026-09-11`** | 否则 Hugo 用文件 mtime，排序不稳定 |

### 10.4 模板与 Liquid 逻辑如何转换（**建议**）

`archive.md` 的 Liquid 循环：

```liquid
{% for post in site.posts %}
  <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
  <span class="date">{{ post.date | date: "%Y.%m" }}</span>
{% endfor %}
```

对应 Hugo（`layouts/_default/list.html` 或短代码）：

```go-html-template
{{ range site.RegularPages.ByDate.Reverse }}
  <a href="{{ .RelPermalink }}">{{ .Title }}</a>
  <span class="date">{{ .Date.Format "2006.01" }}</span>
{{ end }}
```

- `site.posts` → `site.RegularPages`（或用 `where .Site.RegularPages "Section" "posts"`）。
- 默认按日期倒序需**显式** `.ByDate.Reverse`（**建议**，避免依赖默认行为）。
- `| relative_url` → `.RelPermalink`。
- `| date: "%Y.%m"` → `.Date.Format "2006.01"`。
- `{{ page.date | date: "%Y.%m.%d" }}` → `{{ .Date.Format "2006.01.02" }}`。
- `_layouts/post.html` 的固定链接 `/archive/` 直接写死即可（与现状一致）。

### 10.5 Permalink 兼容策略（**建议，最高优先**）

在 `hugo.toml` 中**显式固定扁平 permalink**：

```toml
[permalinks]
  posts = "/:slug/"          # 关键：保持 /na-la-ti/ 等旧 URL
```

- 确保 `:slug` 与 Jekyll 的 `:title`（文件名 slug）一致：`na-la-ti`、`qing-chun-de-wu-yu`、`shi-ren-xiao-zhuan`。
- 页面的 `url:` 前置字段固定 `/archive/`、`/preface/`。
- **可选双保险**：为每篇加 Hugo `aliases` 指向旧路径（若 permalink 已一致则冗余，但可作为防御）。
- **必须验证**：迁移后逐一 curl 上表所有旧 URL，确认全部 200。

### 10.6 图片及静态资源迁移策略（**建议**）

- `assets/img/cover.png` → `static/assets/img/cover.png`，**路径与文件名逐字不变**，保证 `<img src="assets/img/cover.png">` 与任何外部引用不失效。
- `style.css` → `static/style.css`，**逐字复制，先不重构**（先保真，后美化）。
- 首页 `<img src="assets/img/cover.png">` 为**相对路径**，在首页 `/` 下解析正确；Hugo 首页同路径，保持可用。
- **禁止**在迁移阶段重命名、压缩或转换图片格式（会改变外链指纹）。

### 10.7 Vercel 构建配置建议（**建议**）

- 在**独立仓库或独立分支**配置 Hugo + Vercel，**不触碰 `main`**。
- `vercel.json` 示例（Hugo 静态站）：

```json
{
  "buildCommand": "hugo --minify",
  "outputDirectory": "public",
  "installCommand": "apt-get update && apt-get install -y hugo || true",
  "framework": null
}
```

- **【建议】** 更稳妥的做法：在 Vercel 项目设置里指定 Hugo 版本（`HUGO_VERSION` 环境变量），使用官方推荐的 Hugo 构建镜像，避免 `apt-get` 版本漂移。
- **缓存与重定向**：Vercel 默认对静态资源做 CDN 缓存；如需保留 `/archive`→`/archive/` 的尾斜杠行为，可加 `trailingSlash: true`（**建议**，与 GitHub Pages 行为对齐）。
- **【事实】当前 Vercel 上已有 `bio.ismaelan.com`**，**不要**复用或覆盖该项目的任何配置；`poet` 应作为**全新独立 Vercel 项目**。

### 10.8 如何在不影响现有 GitHub Pages 的情况下建立预览（**建议**）

1. **独立分支方案（推荐）**：在 `Lawrenceblock/poet` 仓库新建分支（如 `hugo-migration`），放置 Hugo 站点文件；`main` 保持 Jekyll 不变，GitHub Pages 继续从 `main` 构建，**线上完全不受影响**。
2. **Vercel 预览**：将该分支接入一个**新的 Vercel 项目**（用 Preview 部署），生成 `*.vercel.app` 预览地址。
3. **绝不**在预览阶段绑定 `poet.ismaelan.com` 或修改 DNS——**域名切换必须留到最终验收后**。
4. **【建议】** 若预览需受保护，启用 Vercel Deployment Protection + Protection Bypass Secret，供逐页比对使用。
5. **禁止**在迁移期修改 GitHub Pages 设置、分支保护或 `main`。

### 10.9 如何进行新旧页面逐一比对（**建议**）

对以下**全部** URL 做“旧站 vs 预览站”逐项比对：

| 比对项 | 方法 |
| --- | --- |
| HTTP 状态码 | 逐一 curl，全部应为 200（旧 URL 集见 7.2/7.3） |
| 诗歌正文**逐字**一致 | 提取渲染后的正文文本（去除 `<br>`/标签差异后）做 diff，**必须 0 差异** |
| 标题、日期、作者 | 逐字段核对 |
| 中英双语顺序与分段 | 人工 + 文本 diff |
| 换行/诗节结构 | 截图对比 + `innerText` diff |
| 图片与 CSS 可访问性 | curl `/assets/img/cover.png`、`/style.css` 均 200 |
| 导航与返回卷目链接 | 逐链接点击验证 |
| 移动端渲染 | 无头浏览器 390px 截图对比 |
| HTML `<title>` | 逐页核对 |

**特别提示**：比对时**不要用审计报告本身作为证据**，应以**两台真实部署的响应**互相比对。

### 10.10 最终切换域名前必须满足的验收条件（**建议**）

1. 上表**所有旧 URL** 在新站返回 200，且**正文逐字一致**（含标点、空格、换行）。
2. 中英双语文章内容完整、顺序正确、格式不退化（不得把线上已有的“星号/`---`/换行丢失”问题带过去，也不得**额外**引入新差异）。
3. `style.css`、`cover.png` 路径可用且内容一致。
4. 首页/卷目/题记/小传 4 类页面视觉与旧站一致（或经作者明确批准的改进）。
5. **回滚预案已验证**：可一键切回 GitHub Pages（DNS 回切 + `main` 未动）。
6. **作者书面授权**切换域名（本阶段不进行）。
7. `main` 分支与全部 14 个历史提交**完整保留**，原始 Jekyll 文件未被删除。
8. 迁移**不触碰** `bio.ismaelan.com` 项目。

### 10.11 回滚策略（**建议，强制**）

- **原始 Jekyll 内容与历史提交完整保留**：迁移**不改写、不删除** `main` 上的任何文件；所有 Hugo 产物放独立分支/仓库。
- **DNS 层面可回滚**：切换时保留原 CNAME 记录值（`lawrenceblock.github.io.`），如需回滚只需把 DNS 指回 GitHub Pages。
- **GitHub Pages 保持可用**直至切换确认稳定；不建议在切换前关闭 Pages。
- **禁止**在 `main` 上直接删除 Jekyll 文件；**禁止** force-push。

### 10.12 文学内容保护（**建议，最高优先**）

- **逐字不改**：诗歌正文、作者小传、题记、署名、日期、标签**一律原样搬运**。
- **禁止润色/删减/改写**：包括标点（全角/半角）、省略号（`……`）、书名号（`「」`）、破折号、空格。
- **不可自动转换的内容**（**建议保留原始 HTML**）：
  - `青春的物语`：整篇为手工 HTML（含内联 `text-align`、`<br>`、字面 `---`、字面 `**`）。**建议原样保留 HTML**，不做 Markdown 化，避免改变现有（哪怕是“有缺陷”的）呈现。
  - `那拉提（未赴）`：正文行尾双空格换行。**建议在迁移时明确决策**：是（a）原样保留（接受线上现状），还是（b）修正为 `{{< br >}}`/`<br>` 让诗行正确分行。**该决策须由作者确认**，审计阶段不代决。
  - `诗人小传`：标准 Markdown，可直接转换；但须清理 `#` 标签、处理 `aliases` 语义冲突、补 `date`。
- **建议迁移前建立“正文指纹”**：对每篇文章的正文做 SHA256，迁移后逐一比对，作为**逐字不变**的客观证据。

---

## 11. 尚未解决的问题 / 待验证事项

| # | 待验证项 | 原因 | 建议验证方式 |
| --- | --- | --- | --- |
| 1 | 是否存在**外部网站**引用旧诗歌 URL | 审计**未检索外链来源**（无搜索引擎/外链工具授权） | 作者自查 Google Search Console、外链分析工具 |
| 2 | `https://grokpoet.vercel.app/` 与 `bio.ismaelan.com` 的关系及外部引用 | 属 bio 项目，**本任务不审查** | 由作者在 bio 项目内确认 |
| 3 | `lawrenceblock.github.io/poet/` 备用入口迁移后是否需保留 | 当前 301 到自定义域名，机制**未深查** | 迁移方案确定后评估 |
| 4 | 分支保护规则 | API 返回 403（`Resource not accessible by integration`），**无权限读取** | 仓库所有者查看 Settings |
| 5 | 站点的 Google/Bing 收录与 sitemap | 站点**无 sitemap.xml/robots.txt**，无 SEO 提交记录 | Search Console |
| 6 | 移动端真实设备渲染 | 仅用无头浏览器模拟，**未在真机验证** | 真机测试 |
| 7 | 中文字体在 Linux/Android 的回退效果 | 仅分析字体栈，**未实测各平台** | 多平台截图 |
| 8 | 颜色对比度是否达 WCAG AA | **未做量化计算** | 对比度工具 |

**明确标注**：以上均为“尚未验证”，**不得**在后续实施中当作已知事实。

---

## 12. 风险等级与优先级

| 优先级 | 风险项 | 等级 | 说明 | 依据 |
| --- | --- | --- | --- | --- |
| **P0** | 迁移改变 permalink → 全部诗歌 URL 失效 | **高** | Hugo 默认路径与现状不同；一旦切换，现有链接全断 | 第 7 节 |
| **P0** | 诗歌正文换行/Markdown 渲染差异导致内容呈现变化 | **高** | `那拉提` 换行已丢失、`青春` 星号未渲染；迁移若不慎会**再次改变**呈现 | 第 6、9 节（实测） |
| **P0** | 误改/丢失文学内容（小传含敏感经历） | **高** | 内容不可自动转换部分多，人工干预风险大 | 第 6.2 节 |
| **P1** | `main` 分支与历史被破坏、无法回滚 | **高** | 若在 main 直接迁移，回滚困难 | 第 10.11 节 |
| **P1** | 移动端无 viewport（现状缺陷，迁移可一并修复） | **中** | 影响所有移动读者 | 第 9.5 节（实测） |
| **P1** | Front Matter 语义冲突（`aliases`/`#` 标签/缺 `date`） | **中** | 处理不当会产生错误重定向或排序错乱 | 第 10.3 节 |
| **P2** | 样式类缺失、首页样式重复 | **中** | 影响观感，但不影响内容 | 第 9.1/9.2/9.3 节 |
| **P2** | 无 SEO 元数据/sitemap/robots | **中** | 影响收录与分享 | 第 9.1 节 |
| **P2** | 误将 `bio` 项目混入 | **中** | 已明确隔离，需在实施中守住边界 | 第 8.3 节 |
| **P3** | 字体跨平台不一致、对比度偏低 | **低** | 观感问题 | 第 9.6/9.7 节 |

### 迁移风险最高的三个事项（结论）

1. **Permalink 兼容**：必须显式固定 `/:slug/`，否则全部旧诗歌链接失效（P0）。
2. **诗歌正文逐字保真（尤其换行与 HTML 混排）**：`那拉提` 的行尾双空格换行与 `青春` 的 HTML/字面符号，任何自动转换都可能改变呈现；须建立正文指纹并逐字比对（P0）。
3. **`main` 分支与历史不可破坏 + 可回滚**：迁移必须在独立分支/独立 Vercel 项目进行，保留全部 14 个提交与原始 Jekyll 文件（P0/P1）。

---

## 13. 后续实施阶段建议

> 以下为**建议**，须经项目负责人审阅与授权后执行。本阶段**不进入**下一阶段。

**阶段 0（本次）**：审计与建档 —— **已完成**（本报告）。

**阶段 1：内容基线固化（只读）**
- 对 `main` @ `ee94501c` 打 tag 或记录 SHA 作为迁移基线。
- 对 3 篇文章正文做 SHA256 指纹，保存为比对基准。
- 导出全部线上页面 HTML 快照（作为旧站证据）。

**阶段 2：Hugo 骨架（独立分支 `hugo-migration`）**
- 搭建 10.1 目录结构，复制 `style.css`、`cover.png`（逐字不变）。
- 配置 `hugo.toml` 的 `permalinks` 与 `url`，确保 URL 一致。
- 逐篇转换 Front Matter（按 10.3），**正文原样搬运**。

**阶段 3：Vercel 预览（新项目，Preview 部署）**
- 接入 `hugo-migration` 分支，生成 `*.vercel.app` 预览。
- **不绑定** `poet.ismaelan.com`，**不改** DNS。

**阶段 4：逐页比对（按 10.9）**
- 旧站 vs 预览站，全 URL + 正文指纹逐项比对，输出比对报告。

**阶段 5：作者验收（按 10.10）**
- 作者确认内容逐字一致、视觉可接受、换行策略决策（`那拉提`）。

**阶段 6：切换（需单独授权）**
- 仅在全部验收通过且作者**书面授权**后，才进行域名/DNS 切换；保留回滚路径。

**阶段 7：观察与收尾**
- 切换后观察收录与访问；确认稳定后再评估是否关闭 GitHub Pages 构建（**不删除** `main` 与历史）。

---

## 附：审计方法与证据说明

- **仓库**：`git clone` 全量克隆，`git ls-files`/`git log`/`git show` 核查；SHA 锚定 `ee94501c321c9eddbaff3c2421e7fa05428850fa`。
- **GitHub**：`gh api` 只读调用（repo/pages/branches/actions/PR/issue/collaborators）。分支保护因权限返回 403，已如实标注“未验证”。
- **线上**：`curl` 逐 URL 实测状态码与响应体；无头浏览器（Playwright/Chromium）在 390px/1280px 视口实测渲染与 `innerText`；移动模拟实测 `innerWidth` 与缩放比。
- **DNS**：Cloudflare DoH + 系统解析实测 CNAME/A/NS。
- **未做**：任何写操作（除本报告文件本身）；未访问搜索引擎做外链分析；未读取分支保护规则；未修改 DNS/域名/Pages/Vercel。
