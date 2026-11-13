# 安然诗客栈 · 迁移前技术审查：独立复核与现状差异报告

> **报告性质**：独立、只读技术复核。**不是**首份审计（首份审计已于 2026-11-12 完成，见 §0），
> 也**不是**迁移实施记录。
>
> **报告原则**：严格区分 **【事实】**（本次实测 / 已读文件）、**【推断】**（由证据合理推得，未直接验证）、
> **【建议】**（主观方案）。**不把推断写成事实**；无法确认者标注 **【待验证】**。
>
> **审计者角色**：独立审计员（非项目开发者）。**未修改**原站、`main` 分支、域名、DNS、
> GitHub Pages 设置或 Vercel；唯一写操作是新增本报告文件（§14）。

---

## 0. 首要发现：本任务所指的审计**已经存在**

**【事实】** 本次任务书要求产出的「迁移前技术审计报告」，**已于 2026-11-12 完成并提交**：

| 项目 | 值 |
| --- | --- |
| 报告路径 | `docs/audit/2026-11-12-pre-hugo-migration-audit.md` |
| 所在分支 | `audit/pre-hugo-migration-2026-11-12`（远程存在） |
| 提交 SHA | `eaac3a4f0a36441ccd07786f5dd5191d4a04fc85`（`docs(audit): add pre-Hugo-migration technical audit report`） |
| Pull Request | **PR #1**（`https://github.com/Lawrenceblock/poet/pull/1`，state=open，base=`main`，head=`audit/pre-hugo-migration-2026-11-12`，1 file，+710 行） |
| 报告规模 | 710 行 / 47,549 字节；含任务要求的全部 13 个章节 |
| 报告锚定 SHA | `ee94501c321c9eddbaff3c2421e7fa05428850fa`（= 当前 `main` HEAD） |
| 在线地址 | `https://github.com/Lawrenceblock/poet/blob/audit/pre-hugo-migration-2026-11-12/docs/audit/2026-11-12-pre-hugo-migration-audit.md` |

**【事实】** 该报告**尚未合并进 `main`**（`git ls-tree origin/main` 中无 `docs/`），因此它以
**PR #1（draft=false，open）** 的形式等待审阅，而非已生效的仓库文件。

**【事实】** 本任务书建议的报告路径正是
`docs/audit/2026-11-12-pre-hugo-migration-audit.md`——**与既有报告同名**。依据任务书
「若已存在则不得覆盖、应另取不冲突文件名」的要求，本报告改用新文件名
`2026-11-13-independent-verification-and-delta.md`，**不覆盖**旧报告。

**【事实】** 自 2026-11-12 首次审计以来，项目已显著推进：复核前仓库已有 **16 个远程分支、15 个 PR**
（不含本次审计新增的分支），并已建成完整 Hugo 站点（`hugo/`）、作者审阅系统与 137 篇候选全文站。
因此本报告的定位是 **「复核 + 差异 + 现状」**，而非从零重写首份审计。

---

## 1. 审计日期

- 复核执行时间：**2026-11-13**（UTC 约 06:05–06:15，`date -u` 实测 `Fri Nov 13 06:12 UTC 2026`）。
- 首份审计时间：**2026-11-12**（见 §0）。
- 本报告文件名：`docs/audit/2026-11-13-independent-verification-and-delta.md`。
- 冲突检查：**【事实】** 复核开始时，`main` 分支**不存在** `docs/` 目录；同名旧报告位于
  `audit/pre-hugo-migration-2026-11-12` 分支，故未覆盖任何历史报告。

---

## 2. 仓库地址与审计提交 SHA

| 项目 | 值 | 证据 |
| --- | --- | --- |
| 仓库 | `https://github.com/Lawrenceblock/poet` | 【事实】 |
| 默认分支 | `main` | 【事实】`api/repos` → `default_branch: main` |
| 本次复核基线 SHA | `ee94501c321c9eddbaff3c2421e7fa05428850fa` | 【事实】`api/repos/.../commits/main` |
| 该提交信息 / 日期 | `Update index.html` / 2026-09-12T23:07:24Z（+0800 2026-09-13） | 【事实】 |
| `main` 提交总数 | **14** | 【事实】`git rev-list --count main` |
| 仓库可见性 | **public** | 【事实】`api/repos` → `visibility: public` |
| 仓库大小 | 5,763 KB（GitHub 计量） | 【事实】 |
| 仓库描述 | `My poem collection` | 【事实】 |
| License | **无** | 【事实】`license: null` |
| 创建 / 最近 push | 2026-09-07 / 2026-11-13 | 【事实】 |
| 标签 / Release | **0 / 0** | 【事实】 |
| Issue（非 PR） | **0** | 【事实】`api/issues` 过滤 `pull_request` |

**本报告全部结论锚定 SHA `ee94501c321c9eddbaff3c2421e7fa05428850fa`。**
**【事实】** 复核期间该 SHA 与首份审计一致，`main` 未发生变更。

---

## 3. 审计范围

本次为**复核 + 差异**，覆盖任务书第 1–7 项，并额外比对「首份审计结论」与「当前实际状态」：

1. 仓库完整性（默认分支、提交、完整目录树、全部文件、版本控制外文件、历史/分支保留）。
2. Jekyll 构建与发布机制（`_config.yml`、Pages 来源、Actions、插件/主题/Gemfile、permalink、Front Matter、Liquid）。
3. 诗歌与文学内容保护（文章清单、双语、HTML/换行、外部资源、非诗歌页、重复/失效/异常）。
4. 永久链接与 SEO（实际 permalink、各页 URL、站内链接、外链风险、旧 URL 对应）。
5. 视觉与用户体验（现状评估，只读）。
6. 域名与部署状态（只读）。
7. Hugo + Vercel 迁移可行性（复核既有建议 + 补充现状）。

**明确排除**：`bio.ismaelan.com` 是**独立站点**，本报告不审查、不修改、不迁移；仅在「确认二者独立」范围内引用。

---

## 4. 检查过的文件与目录

### 4.1 `main` 受版本控制文件清单（**【事实】**：`git ls-tree -r origin/main`，共 **13 个文件**）

| 文件 | 类型 | 备注 |
| --- | --- | --- |
| `CNAME` | 域名 | 内容 `poet.ismaelan.com` |
| `README.md` | 运维备忘 | 161 行 |
| `_config.yml` | Jekyll 配置 | 44 行 |
| `_layouts/default.html` | 布局 | 全局底版 |
| `_layouts/post.html` | 布局 | 诗歌详情模板（含「返回卷目」） |
| `_posts/2026-04-07-qing-chun-de-wu-yu.md` | 诗歌 | 中英双语 |
| `_posts/2026-09-07-na-la-ti.md` | 诗歌 | 中文 |
| `_posts/2026-09-11-shi-ren-xiao-zhuan.md` | 诗人小传 | 非诗歌 |
| `archive.md` | 卷目页 | Liquid 循环 |
| `assets/img/cover.png` | 图片 | 632×679，195,938 字节 |
| `index.html` | 首页 | 内联样式 |
| `preface.md` | 题记页 | 手写 HTML |
| `style.css` | 样式 | 1,706 字节 |

**按类型统计【事实】**：Markdown 6、HTML 3、CSS 1、PNG 1、其他 2（`CNAME`、`_config.yml`）。
**`_posts/` 文章数 = 3。** 全历史**从未删除或重命名任何文件**（`git log --diff-filter=D/R` 为空）。

### 4.2 未纳入版本控制的文件（**【事实】**）

- 复核时工作区 `git status` 干净（就 `main` 而言）。
- **不存在** `.gitignore`、`.nojekyll`、`Gemfile`、`Gemfile.lock`、`vendor/`（逐项 `git cat-file -e` 实测 **absent**）。
- `_config.yml` 的 `exclude:` 列出 `README.md`、`元宝代码`、`vendor`、`Gemfile`、`Gemfile.lock`；
  其中 **`元宝代码`、`vendor`、`Gemfile`、`Gemfile.lock` 均不存在**（**【事实】**：逐项检测 MISSING）——
  属**无效/历史残留配置**，非「未纳入版本控制的重要文件」。

### 4.3 历史提交与分支（**【事实】**）

- `main` 提交总数 **14**；无标签、无 Release、无 Issue。
- **全历史从未删除任何文件**（`git log --diff-filter=D` 为空）。
- `main` 提交（正序）：

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

- **需保留内容【事实】**：全部 14 个提交构成完整文学与配置演进史（含两次「青春物语正文换行/诗节」修订），
  迁移时**必须完整保留 `main` 与全部历史**。
- **远程分支【事实】**：共 16 个（含 `main`、`audit/*`、`design/*`、`migration/*`、`site/*`、`impl/*`、`plan/*`、`feat/*`、`review/*`、`research/*`）。

### 4.4 任务点名文件核实（**【事实】**）

`_config.yml`、`_posts/`、`_layouts/`、`index.html`、`archive.md`、`preface.md`、`style.css`、
`assets/`、`CNAME`、`README.md` —— **均存在**，实际结构与任务列表一致，无额外未点名的重要文件。
任务点名的三篇 `_posts/2026-04-07-qing-chun-de-wu-yu.md`、`2026-09-07-na-la-ti.md`、
`2026-09-11-shi-ren-xiao-zhuan.md` 均在，且**仓库仅此 3 篇**。

---

## 5. 当前技术架构（`main`）

### 5.1 构建与发布（**【事实】**）

- **框架**：Jekyll，`markdown: kramdown`，`highlighter: rouge`。
- **发布来源**：GitHub Pages **legacy 构建**。`api/repos/.../pages` → `build_type: legacy`、
  `source: {branch: main, path: /}`。
- **Actions 工作流**：`api/repos/.../contents/.github` → **404**，仓库中**无 `.github/` 目录**，
  即**无仓库自有工作流**；仅依赖 Pages 平台内置的 `pages-build-deployment`。**【事实】**
- **是否依赖 Pages 内置 Jekyll**：**是**。无自定义构建、无 Gemfile、无插件声明。
- **HTTPS**：**【事实】** `https_enforced: true`；线上 `https://poet.ismaelan.com/` 直返 **200**（0 重定向）。

### 5.2 关键配置（**【事实】**：`_config.yml`）

```yaml
title: 安然诗客栈
author: 安然
url: "https://poet.ismaelan.com"
baseurl: ""
markdown: kramdown
highlighter: rouge
permalink: /:title/          # ← 关键
paginate: 10
defaults: [ posts→layout:post, pages→layout:default ]
exclude: [ README.md, 元宝代码, vendor, Gemfile, Gemfile.lock ]
```

### 5.3 布局与模板（**【事实】**）

- `_layouts/default.html`：极简，仅 `<head>` + `{{ content }}`，**未含 `<meta name="viewport">`**。
- `_layouts/post.html`：`.poem-page` / `.poem-title` / `.poem-date` / `.poem-content` + **「← 卷目」**返回链接。
- `archive.md`：`permalink: /archive/`，用 Liquid `{% for post in site.posts %}` 自动生成卷目。
- `preface.md`：`permalink: /preface/`，手写 HTML，含一条**冗余相对路径** `<link rel="stylesheet" href="style.css">`。

### 5.4 README 与配置不一致（**【事实】**）

`README.md` 声称「诗歌正文：由 Jekyll 按日期自动生成，如 `/2026/09/07/na-la-ti/`」，
**与 `_config.yml` 的 `permalink: /:title/` 矛盾**。线上实测：`/2026/09/07/na-la-ti/` → **404**，
`/na-la-ti/` → **200**。**应以 `_config.yml` 为准；README 该处描述错误。**（此项与首份审计一致）

---

## 6. 内容资产清单

### 6.1 文章总表（**【事实】**：逐文件读取 + 线上核对）

| # | 文件路径 | 标题 | 日期 | 标签 | 别名 | 线上 URL | 形态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `_posts/2026-04-07-qing-chun-de-wu-yu.md` | 青春的物语 | 2026-04-07 | `[诗歌]` | 无 | `/qing-chun-de-wu-yu/` | 中英双语，纯 HTML |
| 2 | `_posts/2026-09-07-na-la-ti.md` | 那拉提（未赴） | 2026-09-07 | `[新疆, 未赴]` | 无 | `/na-la-ti/` | 中文，HTML 包裹 |
| 3 | `_posts/2026-09-11-shi-ren-xiao-zhuan.md` | 诗人小传 | 2026-09-11 | `[#诗人,#传记,#回族,#文学]` | `安然`、`崔浩新`、`伊斯玛义勒` | `/shi-ren-xiao-zhuan/` | 中文 Markdown |

**文章总数 = 3；真正的「诗」为 2 篇**（青春的物语、那拉提），第 3 篇为**诗人小传**（传记，非诗歌）。

**【事实】** Front Matter 字段：
- 文章 1：`layout, title, date, author, tags`（**唯一含 `author`**）。
- 文章 2：`title, date, layout, tags`。
- 文章 3：`title, aliases, tags, created, modified`（**无 `date`**；`layout` 由 `_config.yml` defaults 注入）。
- 文章 3 的 `tags` 为 **Obsidian 风格 `#` 前缀**，含 `created/modified`；`aliases` 为 **Obsidian 别名，Jekyll 不识别**。

### 6.2 逐篇排版细节（**【事实】**）

**文章 1 青春的物语（中英双语）**
- `<div class="poem">` 内中文诗（`<div style="text-align:center">` + 大量 `<br>`），随后**字面 `---`**，再两个英文块。
- **格式异常（事实）**：英文块用 Markdown 语法写在 HTML `<div>` 内（`**Youth's Tale**`、`*by **An Ran** *`），
  Kramdown **未转换**，线上**原样输出星号**。实测线上页面出现字面 `**Youth`、`*by`。
- **字面 `---`（事实）**：实测线上页面 `<hr` 计数 **0**，字面 `---` 原样输出。

**文章 2 那拉提（未赴）**
- `<div class="poem">` + 纯文本诗行；**行尾双空格硬换行**（`cat -A` 实测每行以 `  $` 结尾）。
- **格式异常（事实）**：外层为原始 HTML 块，Kramdown 不做 Markdown 处理，行尾双空格**未转 `<br>`**；
  浏览器空白折叠后**诗行换行丢失**。实测 390px 下 `innerText` 显示第一诗节挤为一行：
  `那拉提的风我没能赶上 北门外的雪替我去了`。

**文章 3 诗人小传**
- H1（`# 诗人小传`/`# 此生行止`）、引用块、H2（`## 年谱`）、12 项有序列表。
- 含**个人敏感信息**（生日、籍贯、民族、亲属命名、被问话/拘留经历等）。
  **【建议】迁移时须原样保留，不得改写、脱敏或删减。**
- Front Matter 含 Obsidian `aliases` 与 `#` 标签。

### 6.3 非诗歌页面（**【事实】**）

首页 `index.html`（封面 + 站名 + 导航）、卷目 `archive.md`（自动目录）、题记 `preface.md`（手写 HTML）。

### 6.4 图片 / 附件 / 外部资源（**【事实】**）

- **图片**：全站**仅 1 张** `assets/img/cover.png`（632×679，195,938 字节），仅首页引用（相对路径）。
- **外部链接**：全站**仅 1 条**——首页「小传」→ `https://bio.ismaelan.com/`。
- 历史外链：`https://grokpoet.vercel.app/`（旧「小传」地址）。**【事实】** 实测该域仍 **200**。
- 内容中**无**其他图片、附件、CDN、字体文件或第三方脚本。

### 6.5 内容重复 / 失效链接 / 格式异常（**【事实】**）

- 格式异常 1–3：见 §6.2（星号未渲染、`---` 未渲染、换行丢失）。
- **样式缺失（事实）**：`.poem`、`.archive*`、`.preface`、`.sign`、`.site-name`、`.sub`、`.idx`、
  `.dots`、`.date`、`.nav-sep` 等在 `style.css` 中**均无定义**；卷目/题记/诗歌外层容器实际**无专属样式**。
- **`preface.md` 冗余失效样式（事实）**：相对路径 `<link href="style.css">` 在 `/preface/` 下解析为
  `/preface/style.css`，实测 **404**（但 `default.html` 已用绝对路径 `/style.css` 引入，视觉无影响）。
- 内容重复：**未发现**。站内链接：写法统一为**绝对根路径 + 尾斜杠**，实测均 200。**未发现失效站内链接。**

---

## 7. 永久链接与 URL 风险

### 7.1 实际 URL 规则（**【事实】**）

- 文章：`permalink: /:title/` → `/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/shi-ren-xiao-zhuan/`。
- 卷目：`permalink: /archive/`；题记：`permalink: /preface/`；首页：`/`。
- 无日期层级、无 `.html` 后缀、**带尾斜杠**。实测无尾斜杠 → **301** 重定向（`/na-la-ti`、`/archive`）。

### 7.2 线上实测状态码（**【事实】**，本次 2026-11-13 实测）

| URL | 状态 |
| --- | --- |
| `/` `/archive/` `/preface/` | 200 |
| `/na-la-ti/` `/qing-chun-de-wu-yu/` `/shi-ren-xiao-zhuan/` | 200 |
| `/2026/09/07/na-la-ti/`（README 所声称格式） | **404** |
| `/index.html` | 200 |
| `/na-la-ti`、`/archive`（无斜杠） | **301** → 带斜杠 |
| `/style.css` | 200 |
| `/assets/img/cover.png` | 200 |
| `/CNAME` | 200（CNAME 文件被发布） |
| `/preface/style.css` | **404**（相对路径失效） |
| `/404.html` `/robots.txt` `/sitemap.xml` `/feed.xml` | **404**（无自定义 404 / 无 SEO 文件） |
| `https://lawrenceblock.github.io/poet/` | **301**（跳转自定义域名，redirects=1） |

### 7.3 旧 URL → 建议新 URL 对应表（**【建议】**）

| 旧 URL（Jekyll 现状） | 建议 Hugo 目标 | 保持策略 | 状态 |
| --- | --- | --- | --- |
| `/` | `/` | Hugo 首页 `layouts/index.html` | **必须保持** |
| `/archive/` | `/archive/` | `content/archive.md` + `url` / `aliases` | **必须保持** |
| `/preface/` | `/preface/` | `content/preface.md` + `url` | **必须保持** |
| `/na-la-ti/` | `/na-la-ti/` | 显式扁平 permalink | **必须保持** |
| `/qing-chun-de-wu-yu/` | `/qing-chun-de-wu-yu/` | 同上 | **必须保持** |
| `/shi-ren-xiao-zhuan/` | `/shi-ren-xiao-zhuan/` | 同上 | **必须保持** |
| `/index.html` | `/index.html` | 可选 | 建议保持 |
| `/style.css` | `/style.css` | 静态资源 | 建议保持 |
| `/assets/img/cover.png` | `/assets/img/cover.png` | `static/assets/img/` | **必须保持**（防外链失效） |
| `/CNAME` | 不再需要 | Vercel 不用 CNAME 文件 | 可移除（Vercel 环境） |
| `lawrenceblock.github.io/poet/*` | 保持 301 至 `poet.ismaelan.com/*` | 迁移后若停用 Pages 需评估备用入口 | **【待验证】** |

**【待验证】**（不得猜测）：
1. 是否存在**外部网站**引用具体诗歌 URL —— 本次**未检索外链来源**（无搜索引擎/外链工具授权）。
2. `https://grokpoet.vercel.app/` 是否仍被外部引用、是否有历史流量。
3. `lawrenceblock.github.io/poet/` 的 301 是 Pages 自动行为还是显式配置，迁移后是否需保留。
4. 站点 Google/Bing 收录与 sitemap —— 站点**无 sitemap/robots**，无 SEO 提交记录可查。

### 7.4 URL 风险结论（**【推断】**）

- 现状 URL **极其简单**（扁平 `/:title/`），**迁移保持完全一致的成本很低**。
- **唯一高风险动作**：若 Hugo 采用默认 `/:year/:month/:title/` 或 `/posts/:title/`，将**全部旧链接失效**。
  **【建议】必须显式固定扁平 permalink。**
- **【事实】** 现存的 Hugo 站点（`hugo/hugo.toml`）当前配置为 `posts = "/:year/:month/:slug/"` ——
  **与旧站扁平结构不同**。若照此切换，`/na-la-ti/` 等旧链接将失效。**（迁移最高风险，见 §12）**

---

## 8. GitHub Pages 与域名状态

### 8.1 GitHub Pages（**【事实】**，`api/repos/.../pages`）

```json
{ "status": "built", "build_type": "legacy",
  "source": { "branch": "main", "path": "/" },
  "cname": "poet.ismaelan.com", "https_enforced": true,
  "html_url": "https://poet.ismaelan.com/" }
```

### 8.2 域名与 DNS（**【事实】**，Cloudflare DoH + 系统解析）

- `poet.ismaelan.com` **CNAME → `lawrenceblock.github.io.`**
- A 记录解析为 GitHub Pages 四个 IP：`185.199.108–111.153`
- 权威 NS：`ns05.domaincontrol.com` / `ns06.domaincontrol.com`（GoDaddy）
- HTTPS：`https_enforced: true`，线上直返 200，0 重定向。

**【推断】** 自定义域名指向 GitHub Pages，与 `CNAME` 文件、Pages `cname` 字段三方一致；**未发现**其他托管关系。

### 8.3 与 `bio.ismaelan.com` 的关系（**【事实】**）

- 首页「小传」链接指向 `https://bio.ismaelan.com/`（2026-09-13 由 `grokpoet.vercel.app` 改来）。
- 实测 `bio.ismaelan.com` **200**，`grokpoet.vercel.app` **200**，二者**独立于本仓库**。
- **【建议】** 迁移中保持 `bio` 为外链，**不得**把 `bio` 项目并入 `poet`。

### 8.4 未验证项

- **【待验证】** 分支保护规则（API 返回 403，无权限读取）。
- **【待验证】** 备用入口 `lawrenceblock.github.io/poet/` 的 301 机制细节。

---

## 9. 视觉与用户体验问题（现状评估，未做任何修改）

**【事实】** 本次用无头 Chromium 在 1280px / 390px 实测线上页面：

| 项目 | 实测 |
| --- | --- |
| `<meta name="viewport">` | **缺失**（首页与诗歌页均为 false） |
| 首页 body 背景 | `rgb(220,238,242)`（浅蓝） |
| 封面图 | 632×679，居中，`max-width: 360px` |
| 诗歌页（`/na-la-ti/`） | 诗行**被折叠**（见 §6.2 换行异常） |
| 横向溢出 | 首页 390px 下 **0**（未溢出） |

**主要问题（【事实】）**
1. **无 viewport** → 移动端按桌面宽度缩放，所有页面阅读体验差（影响全部移动读者）。
2. **诗歌换行丢失**：`那拉提` 诗节挤行，改变阅读节奏（**文学呈现受损**）。
3. **字面 Markdown 符号外泄**：`青春的物语` 线上显示 `**`、`*`、`---`。
4. **样式缺失**：卷目/题记/诗歌容器大量 class 无定义，全靠浏览器默认排版。
5. **无 SEO 元数据 / sitemap / robots / 自定义 404**。
6. **`preface` 相对路径样式 404**（视觉无影响，但属失效请求）。

**改善建议（【建议】）**
- 迁移时**一并修复** viewport、换行策略、Markdown 渲染与样式缺失；但**任何修复都不得改动诗歌文字本身**。
- 保持**安静、简洁、以文学阅读为中心**的风格；**不建议**做成商业门户或资讯博客。
- 具体视觉方案见 `docs/phase1/visual*` 与 `docs/phase3-ammons/`（既有设计研究），本报告不重复设计。

---

## 10. Hugo + Vercel 迁移可行性（复核既有建议）

**【事实】** 仓库**已建成** Hugo 站点（`hugo/`，Hugo Extended 0.168.0），含 `hugo.toml`、
`content/posts`、`layouts`、`static/legacy`（旧站只读存档）、`tools/preview`、`tools/verify`、
`tools/author-review`（137 候选 + 令牌门禁）。首份审计（PR #1）§10 已给出完整目录结构与转换策略。

**复核要点（【建议】）**

1. **Hugo 目录结构**：沿用既有 `hugo/` 结构（`content/posts`、`layouts/_default/{baseof,single,list}`、`static/`）。
2. **内容映射**：3 篇 `_posts/*.md` → `content/posts/*.md`，**正文原样搬运**（不重排、不润色）。
3. **Front Matter 转换**：`layout/title/date/tags` 直接映射；`aliases`（Obsidian）→ 评估后**丢弃或转 Hugo `aliases`**；
   `#` 前缀标签 → 去 `#` 或保留为字符串；缺 `date` 的文章 3 → 补 `date: 2026-09-11` 或显式排序权重。
4. **Liquid → Hugo 模板**：`{% for post in site.posts %}` → `{{ range .Site.RegularPages }}`；
   `{{ post.url | relative_url }}` → `{{ .RelPermalink }}`；`{{ forloop.index }}` → 循环计数变量。
5. **permalink 兼容（最关键）**：**必须**在 `hugo.toml` 显式固定扁平结构以匹配 `/:title/`
   （或为 3 篇各设 `url`/`aliases`）；**当前 `hugo/hugo.toml` 的 `/:year/:month/:slug/` 与旧站不一致，须修正**。
6. **静态资源**：`style.css`、`assets/img/cover.png` 原样搬入 `static/`，路径不变。
7. **Vercel 构建**：`hugo` 为构建命令，输出 `hugo/public`（或 `publishDir`）；**Preview 部署**，**不绑定正式域名**。
8. **预览隔离**：**【事实】** 既有 `tools/preview/build_preview.py` 已实现「正式构建不含 `/review/`」；
   生产产物经 `tools/verify/check_production_output.py` 守门。
9. **新旧逐页比对**：**【事实】** 既有 `tools/verify/compare_urls.py`（旧站 vs 新站逐 URL 状态比对）
   与 `tools/author-review/verify_verbatim.py`（逐字保真）可直接复用。
10. **切换验收条件（【建议】）**：全部旧 URL 200 且内容指纹一致；正文逐字比对通过；作者书面授权；
    已备回滚方案；`bio` 保持外链独立。

**【事实】** 迁移**可回滚**：`main` 与 14 个提交、原始 Jekyll 文件均未动；Hugo 在独立分支/目录。

---

## 11. 尚未解决的问题 / 待验证事项

| # | 待验证项 | 原因 | 建议验证方式 |
| --- | --- | --- | --- |
| 1 | 外部网站引用旧诗歌 URL | 未检索外链来源 | Google Search Console / 外链工具 |
| 2 | `grokpoet.vercel.app` 与 `bio` 关系及外链 | 属 bio 项目，本任务不审查 | 作者在 bio 项目内确认 |
| 3 | `lawrenceblock.github.io/poet/` 301 机制与去留 | 未深查 | 迁移方案确定后评估 |
| 4 | 分支保护规则 | API 403，无权限 | 仓库所有者查 Settings |
| 5 | 站点收录 / sitemap | 无 sitemap/robots | Search Console |
| 6 | 移动端真机渲染 | 仅无头模拟 | 真机测试 |
| 7 | 中文字体跨平台回退 | 仅分析字体栈 | 多平台截图 |
| 8 | 颜色对比度量化 | 本次未逐项计算线上配色 | 对比度工具 |
| 9 | 既有 Hugo 站 `permalinks` 与旧站不一致的影响 | 需实施阶段决策 | 实施前显式修正并比对 |

**明确标注**：以上均为「尚未验证」，**不得**在后续实施中当作已知事实。

---

## 12. 风险等级与优先级

| 优先级 | 风险项 | 等级 | 说明 |
| --- | --- | --- | --- |
| **P0** | 迁移改变 permalink → 全部诗歌 URL 失效 | **高** | 既有 Hugo 配置 `/:year/:month/:slug/` 与旧站扁平结构**不一致**，切换即全断 |
| **P0** | 诗歌正文换行/渲染差异改变呈现 | **高** | `那拉提` 换行已丢失、`青春` 星号/`---` 未渲染；迁移若不慎会**再次改变** |
| **P0** | 误改/丢失文学内容（小传含敏感经历） | **高** | 不可自动转换部分多，人工干预风险大 |
| **P1** | `main` 与历史被破坏、无法回滚 | **高** | 须在独立分支/独立项目进行 |
| **P1** | 移动端无 viewport | **中** | 影响所有移动读者（迁移可一并修复） |
| **P1** | Front Matter 语义冲突（`aliases`/`#` 标签/缺 `date`） | **中** | 处理不当产生错误重定向或排序错乱 |
| **P2** | 样式类缺失、首页样式重复 | **中** | 影响观感，不影响内容 |
| **P2** | 无 SEO 元数据/sitemap/robots | **中** | 影响收录与分享 |
| **P2** | 误将 `bio` 项目混入 | **中** | 已明确隔离，须在实施中守住 |
| **P3** | 字体跨平台不一致、对比度 | **低** | 观感问题 |

### 迁移风险最高的三个事项（结论）

1. **Permalink 兼容**：**必须**显式固定扁平 `/:slug/`，否则全部旧诗歌链接失效（P0）。
2. **诗歌正文逐字保真（尤其换行与 HTML 混排）**：须建立正文指纹并逐字比对（P0）。
3. **`main` 与历史不可破坏 + 可回滚**：迁移必须在独立分支/独立项目进行（P0/P1）。

---

## 13. 后续实施阶段建议

> 以下为**【建议】**，须经项目负责人审阅与授权后执行。**本阶段不进入下一阶段。**

- **阶段 0（已完成）**：审计与建档 —— 首份审计 PR #1（2026-11-12）+ 本复核报告（2026-11-13）。
- **阶段 1：内容基线固化（只读）**：对 `main @ ee94501c` 记录 SHA/tag；对 3 篇正文做 SHA256 指纹；
  导出线上页面 HTML 快照作为旧站证据。
- **阶段 2：Hugo 骨架（独立分支）**：修正 `hugo.toml` 的 `permalinks` 为扁平结构；逐篇转换 Front Matter；正文原样搬运。
- **阶段 3：Vercel 预览（新项目，Preview）**：接入迁移分支，生成 `*.vercel.app`；**不绑定**正式域名、**不改** DNS。
- **阶段 4：逐页比对**：旧站 vs 预览站，全 URL + 正文指纹逐项比对，输出报告。
- **阶段 5：作者验收**：确认内容逐字一致、视觉可接受、换行策略决策。
- **阶段 6：切换（需单独授权）**：仅在全部验收通过且作者书面授权后进行域名/DNS 切换，保留回滚路径。
- **阶段 7：观察与收尾**：确认稳定后评估是否关闭 Pages 构建（**不删除** `main` 与历史）。

---

## 14. 本次复核的只读边界遵守情况

**唯一写操作**：新增本报告文件
`docs/audit/2026-11-13-independent-verification-and-delta.md`，经独立分支 + PR 提交，**不直接提交 `main`**。

**未做（【事实】）**：
- 未修改、删除或新增任何既有仓库文件；未改任何诗歌/小传/题记文字。
- 未向 `main` 提交；未合并任何 PR；未改 GitHub Pages / Actions / 仓库设置 / 分支保护。
- 未改 DNS、域名、HTTPS、Vercel；未创建/部署 Vercel 项目。
- 未将 Jekyll 转 Hugo；未把 `poet` 与 `bio` 混为一谈。
- 未覆盖同名旧报告（改用不冲突的新文件名）。

**证据基础**：`git ls-tree/log/show`、`gh`/`api.github.com` 只读调用、`curl` 线上逐 URL 实测、
无头 Chromium（Playwright）1280px/390px 渲染实测、Cloudflare DoH DNS 查询。

---

## 附：首份审计（PR #1）与本次复核的一致性核对

| 首份审计结论（2026-11-12） | 本次复核（2026-11-13） | 结论 |
| --- | --- | --- |
| 受版本控制文件 13 个 | 13 个 | **一致** |
| `_posts` 文章 3 篇 | 3 篇 | **一致** |
| permalink `/:title/`，README 描述错误 | 线上 `/na-la-ti/` 200、`/2026/09/07/...` 404 | **一致** |
| 无 `.github/`、依赖 Pages 内置 Jekyll | `contents/.github` → 404 | **一致** |
| CNAME=`poet.ismaelan.com`、HTTPS 启用 | API + DoH + 线上实测 | **一致** |
| 无 viewport、换行丢失、星号/`---` 外泄 | 无头浏览器实测复现 | **一致** |
| 外链仅 `bio.ismaelan.com` 一条 | 实测一致 | **一致** |
| 无 sitemap/robots/自定义 404 | 逐 URL 实测 404 | **一致** |
| 迁移最高风险：permalink / 正文保真 / 可回滚 | 复核确认，并补充「既有 Hugo 配置与旧站不一致」 | **一致 + 强化** |

**【事实】** 首份审计的全部可核验要点，本次复核**逐项独立复现并一致**；未发现其存在事实性错误。

---

*本报告由 AI agent（OpenHands）以独立审计员身份生成，仅供项目负责人审阅。*
