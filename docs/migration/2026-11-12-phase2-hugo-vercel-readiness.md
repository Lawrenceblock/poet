# Phase 2/3 · Hugo 子目录 + Vercel 部署准备审计（阶段标识：Phase 2 主报告 + Phase 3 补充）

> 日期：**2026-11-12**
> 审计对象：`hugo/hugo.toml`、`hugo/vercel.json`、`hugo/README-HUGO.md`、`docs/migration/hugo-build-verification.md`
> 相关分支：`review/hugo-deployment-readiness-phase2`
> 结论一律区分：**【已验证事实】【推断】【建议】【待验证】**
> **本阶段只做审计；未创建/修改任何 Vercel 项目、未部署、未改 DNS、未改 GitHub Pages。**

---

## 0. 结论速览（**【已验证事实】**）

| 问题 | 结论 |
| --- | --- |
| Hugo 项目根目录 | **`hugo/`**（含 `hugo.toml`/`content`/`layouts`/`static`/`assets`/`vercel.json`） |
| Vercel Root Directory | 应设为 **`hugo`** |
| `hugo/vercel.json` 生效条件 | 当 Root Directory = `hugo` 时生效（Vercel 在**根目录**查找 `vercel.json`） |
| Build Command | `hugo --minify --gc`（**未**显式指定 `hugo` 路径，依赖 Vercel 安装 Hugo 并加入 PATH） |
| Output Directory | `public` |
| Hugo Extended 版本锁定 | `vercel.json` 中 `HUGO_VERSION` **未设置**；`framework` **未设置** → 存在**版本回退风险** |
| GitHub Pages 现状 | **legacy** 构建，`source=main:/`，`cname=poet.ismaelan.com`，HTTPS 已强制 |
| 是否需新建 Vercel 项目 | **需要**（当前仓库无 Vercel 项目；GitHub Pages 与 Vercel 互不相关） |

---

## 1. Hugo 项目根目录确认（**【已验证事实】**）

`hugo/` 目录含全部 Hugo 项目标记：

```
hugo/hugo.toml            # 站点配置（baseURL、permalinks、markup…）
hugo/content/             # 内容
hugo/layouts/             # 模板
hugo/static/              # 静态资源（assets/img/cover.png）
hugo/assets/              # Hugo Pipes 资源（css/style.css）
hugo/archetypes/          # 原型
hugo/vercel.json          # Vercel 配置
```

**本地模拟（root=hugo）**：`cd hugo && hugo --minify --gc` → exit 0，生成 `public/`（9 页、1 静态文件）。**【已验证事实】**

---

## 2. Vercel 关键配置（**【已验证事实】+【推断】）**

### 2.1 Root Directory = `hugo`

- **【已验证事实】** Vercel 的 `vercel.json` 是在**项目根目录**查找的。既然配置文件放在 `hugo/vercel.json`，则必须把 **Root Directory 设为 `hugo`**，该文件才会被读取。
- **【已验证事实】** 若 Root Directory 保持仓库根，则：
  - Vercel 会在**仓库根**找 `vercel.json`（找不到，因为它不在根）；
  - 框架检测会看到根目录的 `_config.yml`（Jekyll 标记），**可能误判为 Jekyll 项目**；
  - 构建将针对**根目录的 Jekyll 站点**，而非 `hugo/`。
- **【建议】** Root Directory = `hugo`。

### 2.2 `vercel.json` 内容核对（**【已验证事实】**）

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "hugo --minify --gc",
  "outputDirectory": "public",
  "framework": null,
  "trailingSlash": true,
  "headers": [ ... 缓存头 ... ]
}
```

- **【已验证事实】** JSON 合法，且与官方 schema 一致（`buildCommand`/`outputDirectory`/`framework`/`trailingSlash`/`headers` 均为合法字段）。
- **【已验证事实】** 官方 Hugo 预设（Vercel 源码 `packages/frameworks/src/frameworks.ts`）：
  - 检测器只认 `config.toml` / `config.yaml` / `config.json`（**不认 `hugo.toml`**，见风险 3.1）；
  - 默认 `buildCommand = hugo --gc`；
  - 默认 `outputDirectory = publishDir || public`；
  - `defaultVersion = 0.58.2`。
- **【已验证事实】** Vercel 会**优先安装 Hugo Extended**：源码 `packages/static-build/src/utils/hugo.ts` 中 `findFile(..., true)` 先尝试 `hugo_extended_*`，找不到才回退 `hugo_*`。因此**普通安装即得到 extended**。Hugo 0.168.0 确有 `hugo_extended_0.168.0_linux-amd64.tar.gz`。

### 2.3 版本锁定（**关键风险**）

- **【已验证事实】** 官方 Hugo 预设 `defaultVersion = 0.58.2`；`HUGO_VERSION` 环境变量可覆盖（Vercel 自带 fixture `33-hugo-zola-versions/vercel.json` 使用 `"build": {"env": {"HUGO_VERSION": ...}}`）。
- **【已验证事实】** 当前 `hugo/vercel.json` **未设置** `HUGO_VERSION`，也**未设置** `framework`。
- **【推断】** 若不设置 `HUGO_VERSION`，Vercel 可能使用默认 `0.58.2`（**过旧**），本框架的 `hugo.toml`（如 `[languages] locale/label`、`[outputFormats.robots]`、`[pagination] pagerSize`）**可能不被旧版支持**，导致构建失败或行为异常。
- **【建议】** 显式锁定 `HUGO_VERSION = 0.168.0`（见下）。

---

## 3. 明确部署配置说明（**【建议】**）

### 3.1 推荐 Vercel 项目设置

| 设置项 | 建议值 |
| --- | --- |
| **Root Directory** | `hugo` |
| Framework Preset | **Hugo**（同时建议在 `vercel.json` 显式 `"framework": "hugo"`） |
| Build Command | `hugo --minify --gc` |
| Output Directory | `public` |
| Install Command | 留空（Hugo 由 Vercel 安装） |
| Environment Variables | `HUGO_VERSION = 0.168.0` |

### 3.2 建议的 `vercel.json` 增补（**尚未应用，仅建议**）

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "hugo",
  "buildCommand": "hugo --minify --gc",
  "outputDirectory": "public",
  "trailingSlash": true,
  "build": { "env": { "HUGO_VERSION": "0.168.0" } },
  "headers": [ /* 保持现有缓存头 */ ]
}
```

> **【建议】** 将 `HUGO_VERSION` 同时设为 Vercel **项目环境变量**（更稳妥），`vercel.json` 的 `build.env` 作为补充。
> 注：`build` 字段在 schema 中标记为 `deprecated`，但仍是 Vercel 官方文档/fixture 的用法；两处都设最安全。

### 3.3 风险清单

| # | 风险 | 级别 | 说明 | 缓解 |
| --- | --- | --- | --- | --- |
| R1 | **未锁定 Hugo 版本** | 高 | 可能回退到 0.58.2，旧版不支持本配置 | 设 `HUGO_VERSION=0.168.0` |
| R2 | **Root Directory 设错** | 高 | 若保持根目录，会误建 Jekyll 站点 | Root Directory = `hugo` |
| R3 | **`hugo.toml` 不被预设识别** | 中 | 检测器不认 `hugo.toml`，可能不自动判定为 Hugo | 显式 `"framework": "hugo"` |
| R4 | **`framework: null`** | 中 | 置空即“不选框架”，可能影响默认命令/版本策略 | 改为 `"hugo"` |
| R5 | 旧站与 Hugo 同仓库并存 | 低 | 根目录 Jekyll 与 `hugo/` 并存，靠 Root Directory 隔离 | 已隔离；切换前不改变 main |
| R6 | 缓存头依赖路径 | 低 | `headers` 指向 `/assets/`、`/style.css`；Hugo 指纹 CSS 路径为 `/css/style.min.<hash>.css` | 核对缓存头路径是否覆盖指纹文件 |
| R7 | 图片等资源 | 低 | `static/assets/img/cover.png` → `/assets/img/cover.png`，与旧站一致 | 保持路径 |

---

## 4. GitHub Pages 现状（**【已验证事实】**，只读）

`GET /repos/Lawrenceblock/poet/pages`：

```json
{
  "status": "built",
  "cname": "poet.ismaelan.com",
  "build_type": "legacy",
  "source": { "branch": "main", "path": "/" },
  "public": true,
  "https_enforced": true,
  "https_certificate": { "state": "approved", "domains": ["poet.ismaelan.com"], "expires_at": "2027-02-04" }
}
```

**含义与关系**：

- **【已验证事实】** 现网站由 **GitHub Pages 的 legacy（内置 Jekyll）** 从 **`main` 根目录**构建，绑定 `poet.ismaelan.com`，HTTPS 已强制且证书已批准。
- **【已验证事实】** 该机制与 `hugo/` 目录、Vercel **完全无关**：GitHub Pages 只处理 `main` 根目录的 Jekyll；`hugo/` 子目录不参与 Pages 构建（除非被 Jekyll 误处理）。
- **【推断】** Jekyll 默认会忽略以 `_` 开头的目录，但 `hugo/` 不以 `_` 开头；由于 `_config.yml` 未 `exclude` `hugo/`，Jekyll 可能把 `hugo/` 下的 `.md` 也纳入构建。**需在切换前确认**（见待验证 V1）。
- **【已验证事实】** 线上旧 URL 均 200：`/`、`/qing-chun-de-wu-yu/`、`/na-la-ti/`、`/shi-ren-xiao-zhuan/`、`/archive/`、`/preface/`、`/assets/img/cover.png`、`/style.css`；`/那拉提未赴/` 为 404（证明 Jekyll 用**文件名 slug**，非中文标题）。

---

## 5. 是否需要新建 Vercel 项目？（**【推断】+【建议】**）

- **【已验证事实】** 本仓库当前**无 Vercel 项目**（无 `.vercel/`、无部署记录）。
- **【建议】** 需要**新建一个独立 Vercel 项目**：
  - 项目连接 GitHub 仓库 `Lawrenceblock/poet`，Root Directory = `hugo`；
  - **不要**改动 GitHub Pages 配置；
  - 先在 **预览域名**（`*.vercel.app`）验证，**最后**才考虑切换自定义域名（且切换 = DNS 变更，须另行授权）。
- **【建议】** 采用“**双轨并行**”：GitHub Pages 继续服务 `poet.ismaelan.com`；Vercel 用预览域名做比对，直到验收通过再谈域名切换。
- **【建议】** Vercel 上启用 **Deployment Protection Bypass**（生成 bypass secret），以便自动化对新旧页面逐页比对时能访问预览。

---

## 6. 不影响 GitHub Pages 的预览方案（**【建议】**）

1. 新建 Vercel 项目，Root = `hugo`，绑定**预览域名**（不改 DNS）。
2. 每次推送到迁移分支 → 自动生成 Vercel 预览。
3. 用脚本对“旧站 URL vs 预览 URL”逐页抓取比对（HTML 结构 / 文本 / 状态码）。
4. 验收通过后，才讨论把 `poet.ismaelan.com` 切到 Vercel（**需显式授权**，涉及 DNS）。

---

## 7. 尚未验证 / 待验证（**【待验证】**）

- **V1**：Jekyll 是否会把 `hugo/` 目录纳入 `main` 的 Pages 构建（需检查构建产物；未授权触发构建）。
- **V2**：Vercel 上以 `HUGO_VERSION=0.168.0` 的**实际构建结果**（本阶段未部署）。
- **V3**：Vercel 实际安装的是 extended 还是 standard（源码显示优先 extended，需实测确认）。
- **V4**：`headers` 缓存头对 Hugo 指纹 CSS 路径的实际覆盖效果。
- **V5**：`trailingSlash: true` 与旧站 URL（均带尾斜杠）的一致性（已初步一致）。

---

## 8. 本阶段边界声明

- **未**创建或修改任何 Vercel 项目；
- **未**部署任何站点；
- **未**修改 DNS、HTTPS、GitHub Pages 配置、分支保护；
- 仅**只读**查询了 GitHub Pages 配置与 Vercel 官方源码/文档。

---

## 9. Phase 3 补充验证（**【已验证事实】**）

> 日期：**2026-11-12** · 依据 ChatGPT 对 PR #5 的独立审阅。
> 本阶段**只做本地/文档层验证**；**未**创建 Vercel 项目、**未**部署、**未**改 DNS。

### 9.1 Jekyll 旧站隔离验证（在临时目录模拟构建）

**方法**：安装 `jekyll 4.3.4`，把仓库**当前分支内容**复制到 `/tmp`，运行 `jekyll build`（**不影响线上**）。

**【已验证事实 · 重要发现】** 未加隔离前，Jekyll **会**把 `hugo/`、`docs/` 目录**一并构建进 `_site/`**，例如：

```
_site/hugo/hugo.toml
_site/hugo/vercel.json
_site/hugo/README-HUGO.md
_site/hugo/layouts/404.html
_site/hugo/content/archive/index.html
_site/docs/migration/url-compatibility.md
...
```

并伴随构建告警：`Layout 'archive' requested in hugo/content/archive.md does not exist.`

**结论**：
- **【已验证事实】** `hugo/` **不**以 `_` 开头，**不在** Jekyll 默认忽略范围，因此**会被**根目录 Jekyll 纳入构建。
- **【已验证事实】** 但**当前线上不受影响**：`main` 分支**根本没有** `hugo/`、`docs/`、`tools/`（它们只存在于 PR 分支）。线上抽查 `/hugo/hugo.toml`、`/docs/migration/url-compatibility.md` 均 **404**。→ **在把 `hugo/` 合并进 `main` 之前，不会污染线上**。
- **【风险】** 一旦把 `hugo/` 合并进 `main` 并触发 Pages 构建，上述文件会出现在线上（`/hugo/...`、`/docs/...`），**且 `/hugo/content/**` 会生成多余的 HTML 页面**。

**最小化隔离方案（**【建议】**，**未**应用到 `main`）**：在 `_config.yml` 的 `exclude:` 中加入：

```yaml
exclude:
  - README.md
  - "元宝代码"
  - vendor
  - Gemfile
  - Gemfile.lock
  - hugo      # Phase 3: 排除 Hugo 迁移框架
  - docs      # Phase 3: 排除文档/审计报告
  - tools     # Phase 3: 排除脚本
  - PROGRESS.md
```

**验证（**【已验证事实】**）**：加 `exclude` 后重建，`_site/` **只剩**站点文件（`index.html`、`archive/`、`preface/`、`na-la-ti/`、`qing-chun-de-wu-yu/`、`shi-ren-xiao-zhuan/`、`assets/`、`style.css`、`CNAME`），**无**任何 `hugo/`、`docs/`、`tools/` 产物。

> **【建议】** 该 `exclude` 增补应在**专门的分支/PR**中提出并评审，**不得**在本审计阶段直接改 `main`。

### 9.2 `baseURL` 对预览构建的影响（**【已验证事实】**）

| 构建 | canonical | og:url | sitemap `<loc>` | robots `Sitemap:` | 内部导航链接 |
| --- | --- | --- | --- | --- | --- |
| `baseURL = https://poet.ismaelan.com/`（当前） | `https://poet.ismaelan.com/` | 同 | 生产域名 | 生产域名 | `/archive/`（相对） |
| `--baseURL https://poet-…vercel.app/` | **预览域名** | 预览域名 | **预览域名** | **预览域名** | `/archive/`（相对，**不变**） |

**结论**：
- **【已验证事实】** `baseURL` 决定 **canonical、og:url、sitemap、robots** 中的域名。**内部导航链接**用 `relURL`，为**相对路径**，**不**受 `baseURL` 影响。
- **【风险】** 若在 Vercel **预览**上使用**生产 `baseURL`**，预览页面的 canonical/sitemap 会指向**生产域名**——虽不影响功能，但会造成 SEO 混淆。
- **【建议】** 迁移期用 Vercel 环境变量 `HUGO_BASEURL` 或在构建命令中传 `--baseURL "$VERCEL_URL"`，使预览的 canonical 指向预览域名；**正式切换时**再固定为 `https://poet.ismaelan.com/`。
- **【建议】** 确认 `trailingSlash: true` 与旧站一致（旧站 URL 均带尾斜杠）。

### 9.3 `HUGO_VERSION` 锁定与 Extended 验证（**【已验证事实】**）

- **【已验证事实】** 官方预设 `defaultVersion = 0.58.2`；`HUGO_VERSION` 环境变量可覆盖（Vercel fixture `33-hugo-zola-versions`）。
- **【已验证事实】** Vercel 安装器**优先 Extended**（`packages/static-build/src/utils/hugo.ts` 先试 `hugo_extended_*`）；Hugo 0.168.0 存在 `hugo_extended_0.168.0_linux-amd64.tar.gz`。
- **【已验证事实】** 本框架**未使用 SCSS/图片处理**，仅用 `resources.Get` + `minify` + `fingerprint`（**standard 版即可**）。故即使装到 standard 版也能构建；Extended 为**更保险**。
- **【建议 · 最小 `vercel.json` 增补（**未**应用）】**：

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "hugo",
  "buildCommand": "hugo --minify --gc",
  "outputDirectory": "public",
  "trailingSlash": true,
  "build": { "env": { "HUGO_VERSION": "0.168.0" } },
  "headers": [ /* 见 9.4 */ ]
}
```

- **【建议】** `HUGO_VERSION` **同时**设为 Vercel 项目环境变量（更稳）。
- **【已验证事实】** `hugo.toml` **不被** Vercel 官方预设检测器识别（只认 `config.toml/yaml/json`），故应**显式** `"framework": "hugo"`。

### 9.4 指纹 CSS 与缓存头路径（**【已验证事实】+【建议】**）

- **【已验证事实】** Hugo 产出 `public/css/style.min.<hash>.css`（经 `minify | fingerprint`），**未**产出 `/style.css`。
- **【已验证事实】** `hugo/vercel.json` 现有两条 header：`/assets/(.*)` 与 **`/style.css`**。其中 **`/style.css` 规则是 no-op**（产物中不存在该路径）。
- **【建议 · 缓存头修正（**未**应用）】**：

```json
"headers": [
  { "source": "/assets/(.*)",  "headers": [ { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" } ] },
  { "source": "/css/(.*)",     "headers": [ { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" } ] }
]
```

> 指纹文件名本身即可安全长期缓存；用 `/css/(.*)` 覆盖所有指纹 CSS。

### 9.5 其它发现（**【已验证事实】+【建议】**）

- **【已验证事实】** `static/` 下**无** `style.css`（仅 `assets/img/cover.png`）。`url-compatibility.md` §3.3 声称“`static/style.css → /style.css`”，**与当前 Hugo 实现不符**：样式实际经 Hugo Pipes 指纹化为 `/css/style.min.<hash>.css`。
- **【风险】** 旧站 `/style.css`（200）在新 Hugo 站**不存在**（会 404）。**【建议】** 若要保留旧 `/style.css` 链接，需在 `static/style.css` 放一份（或加 Vercel 重定向）。
- **【已验证事实】** `layouts/_default/baseof.html` 引用 `/favicon.ico`，但 `static/` 中**无** favicon → 该请求会 404。**【建议】** 补 favicon 或移除该 link。
- **【已验证事实】** 封面路径一致：`static/assets/img/cover.png → /assets/img/cover.png`（与旧站相同）。

### 9.6 迁移期必须逐条验证（**【建议】**）

1. 预览域名下每页 **200**，正文**逐字**一致（含标点/空格/分行）。
2. `/style.css`（若需保留）与 `/assets/img/cover.png` 可达。
3. 旧 URL 对应表（见 `url-compatibility.md` §4）逐条 curl 通过。
4. canonical / sitemap / robots 的域名在预览期指向预览、切换后指向生产。
