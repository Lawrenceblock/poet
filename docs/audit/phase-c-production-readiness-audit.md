# Phase C 审计：生产准备度、文学作品保护与整体架构

> 审计日期：2026-11-12
> 审计对象：`hugo/`（PR #7 分支 `site/hugo-poetry-site-foundation`，HEAD `172ec94`）与仓库根目录 Jekyll 站（`main`）
> 审计方法：只读。`git show` + 本地 Hugo 0.168.0 构建 + `curl` 线上核对。
> 状态标记：**已验证 / 部分验证 / 尚未验证 / 存在风险 / 需要作者决定**

---

## 0. 结论摘要

| 检查项 | 结论 | 状态 |
| --- | --- | --- |
| Hugo 版本兼容性 | 本地 v0.168.0 extended 构建通过；**Vercel 端未验证** | **部分验证** |
| Root Directory 设置 | 需设为 `hugo` | **已验证（本地）** |
| Build/Output 设置 | `hugo --gc --minify` → `public` | **已验证（本地）** |
| 预览/生产环境区分 | `baseURL` 主机名判定，实测正确 | **已验证** |
| 预览 noindex/robots | 实测 `noindex,nofollow` + `Disallow: /` | **已验证** |
| 生产 sitemap/RSS/canonical/HTTPS | 实测输出正确 | **已验证（本地）** |
| 部署后路径错误风险 | 存在：**favicon.ico 缺失**、`/style.css` 缺失 | **存在风险** |
| `/legacy/` 随构建输出 | 实测 `static/legacy/**` → `public/legacy/**` | **已验证（本地）** |
| Vercel 清理是否影响归档 | **未验证**（未部署） | **尚未验证** |

---

## 1. Hugo 版本兼容性（**部分验证**）

**已验证（本地）**
```
hugo v0.168.0-e27a6760c5547237f87d353aebe0580feadb20f4+extended linux/amd64
```
- `hugo --gc --minify` 成功，无 ERROR/WARNING。
- 配置使用 Hugo **v0.158+ 语法**（`locale`/`label` 取代 `languageCode`/`languageName`），
  在 0.168.0 下正常。

**尚未验证**
- Vercel 构建镜像是否提供 **extended** 版（模板未用 SCSS，但 `hugo.toml` 未声明 extended 需求）。
- `HUGO_VERSION=0.168.0` 在 Vercel 上的实际解析（`vercel.json` 的 `build.env` **仅作补充**，
  Vercel 官方建议用**项目环境变量**；见 `hugo/README-HUGO.md`）。

**风险**：若 Vercel 拉取的是 **non-extended** 或版本漂移，构建可能失败或产物不同。
**建议**：在 Vercel 项目环境变量显式设 `HUGO_VERSION=0.168.0`，并在首次部署后核对
`<meta name=generator content="Hugo 0.168.0">`。

---

## 2. Root Directory / Build / Output（**已验证（本地）**）

| 项 | 建议值 | 依据 |
| --- | --- | --- |
| Root Directory | `hugo` | Hugo 源在 `hugo/` 子目录；仓库根目录是旧 Jekyll 站 |
| Framework Preset | `Hugo` | `hugo/vercel.json` 已声明 `"framework": "hugo"` |
| Build Command | `hugo --gc --minify` | 实测通过 |
| Output Directory | `public` | Hugo 默认输出 |
| Install Command | （默认，Hugo 无需） | — |
| Node/Python 依赖 | 无 | 纯 Hugo |

**风险（部署后路径错误）**：若 Root Directory 误设为仓库根，Vercel 会：
1. 找不到 `hugo.toml`（在 `hugo/`），**或**
2. 把根目录的 Jekyll 文件当站点发布，**或**
3. 触发 **Jekyll 构建污染**（见 §6）。

**建议**：Root Directory 必须为 `hugo`；首次部署后逐项核对（见 §7）。

---

## 3. 环境变量与 baseURL（**已验证**）

**设计**：`hugo.toml` 的 `baseURL = "https://poet.ismaelan.com/"` 为生产值；
预览构建通过 `--baseURL` 覆盖。

**实测**
```bash
hugo --baseURL "https://poet-preview.vercel.app/" -d /tmp/preview
```
| 环境 | canonical | robots meta | robots.txt | sitemap host |
| --- | --- | --- | --- | --- |
| 生产（`poet.ismaelan.com`） | 输出 | `index,follow` | `Allow: /` | `poet.ismaelan.com` |
| 预览（其他主机） | **不输出** | `noindex,nofollow` | `Disallow: /` | 预览主机 |

**实测证据**
- 预览 `index.html`：`<meta name=robots content="noindex,nofollow">`，**无** canonical。
- 预览 `robots.txt`：`Disallow: /`。
- 生产 `index.html`：`<link rel=canonical href=https://poet.ismaelan.com/>` + `index,follow`。
- 生产 `robots.txt`：`Allow: /`。

**结论**：预览**不会**污染正式站 SEO。✅

**风险（尚未验证）**：Vercel **Preview 部署**若**未**显式传 `--baseURL`，会用 `hugo.toml`
的生产 `baseURL` → 预览页会输出**生产 canonical 与 `index,follow`**，可能被收录。
**建议**：在 Vercel 为 Preview 环境设置 `HUGO_ENV`/`VERCEL_ENV` 并让构建脚本在非生产时
自动改用预览 `baseURL`（**需实施**，本阶段仅建议）。

---

## 4. 生产 sitemap / RSS / canonical / HTTPS（**已验证（本地）**）

| 产物 | 实测 | 说明 |
| --- | --- | --- |
| `sitemap.xml` | ✅ | 含全部 6 首合成样例 + 首页；**不含** `/legacy/`（static 不进 sitemap，符合预期） |
| `index.xml`（RSS） | ✅ | 标题/链接/pubDate 正确 |
| canonical | ✅ | 仅生产域名输出 |
| HTTPS | ✅（现状） | GitHub Pages 已 `https_enforced: true`，证书 `approved`（见 §5） |
| `index.json` | ✅ | 6 条；搜索用 |

**风险**：`/legacy/` **不在** sitemap（正确），但**也没有** `noindex` meta——
生产构建下 `/legacy/` 会被搜索引擎**收录**。**需决定**是否给归档加 `noindex`。

---

## 5. GitHub Pages 现状（**已验证**）

**API 实测**（`GET /repos/Lawrenceblock/poet/pages`）
```json
{
  "status": "built",
  "cname": "poet.ismaelan.com",
  "build_type": "legacy",
  "source": { "branch": "main", "path": "/" },
  "https_enforced": true,
  "https_certificate": { "state": "approved", "domains": ["poet.ismaelan.com"],
                         "expires_at": "2027-02-04" }
}
```

**结论**
- 当前发布：**legacy 构建**（GitHub 内置 Jekyll），来源 `main` 根目录。
- 自定义域名 `poet.ismaelan.com`，HTTPS 强制，证书有效。
- **无** GitHub Actions 工作流（`main` 无 `.github/`）。
- `custom_404: false`（旧站无 404 页，实测 `/404.html` 404）。

**DNS 实测**
```
poet.ismaelan.com  -> 185.199.108-111.153 (lawrenceblock.github.io)   [GitHub Pages A 记录]
www.ismaelan.com   -> ghs.google.com                                  [Blogger]
bio.ismaelan.com   -> grokpoet.vercel.app                             [Vercel，独立站点]
ismaelan.com       -> 15.197.225.128 / 3.33.251.168                   [apex]
```
- `poet.ismaelan.com` 的 A 记录**符合** GitHub Pages 要求。
- `bio.ismaelan.com` 指向 Vercel，**与 `poet` 无关**（本任务边界外，不得改动）。

---

## 6. Jekyll 退出生产构建流程（**已验证 + 建议**）

**现状**
- 生产构建入口：**GitHub Pages legacy 构建**（`main` 根目录，内置 Jekyll）。
- **无** `.github/workflows`，**无** Vercel 生产项目（`poet.ismaelan.com` 未指向 Vercel）。
- 故“Jekyll 参与生产”目前**仅**指 GitHub Pages 的内置构建。

**已复现的问题（独立复核，Jekyll 4.4.1）**
在含 `hugo/`、`docs/`、`tools/` 的分支（`site/hugo-poetry-site-foundation`）上运行 `jekyll build`，
会把它们当页面发布。**独立复核结果**（干净克隆 + `jekyll build`）：

| 泄漏源 | 泄漏文件数（实测） |
| --- | --- |
| `hugo/`（不以 `_` 开头） | **27** |
| `docs/` | **8** |
| `tools/` | **1** |
| `PROGRESS.md` | 1 |
| 合计泄漏 | **37** |

实测命令与结果：
```bash
git clone --branch site/hugo-poetry-site-foundation https://github.com/Lawrenceblock/poet.git /tmp/jk3
cd /tmp/jk3 && jekyll build
find _site/hugo -type f | wc -l      # 27
find _site/docs -type f | wc -l      # 8
find _site/tools -type f | wc -l     # 1
test -f _site/PROGRESS.md            # yes
```
（注：`hugo/` 下 39 个源文件中，`.gitignore`、`layouts/*.html` 等以 `_` 开头或不满足发布规则者
不被 Jekyll 输出，故泄漏 27 个；`hugo/layouts/*.html` 会被当作 Jekyll 页面处理并报
`Layout 'years' requested ... does not exist` 警告。）

**注意**：`main` 当前**没有**这些目录，故**线上暂不受影响**；
但**合并 Hugo 源到 `main` 之前**必须解决，否则旧站会发布 Hugo 源文件。

**退出路径（建议，分阶段，均需授权）**

| 阶段 | 动作 | 影响 |
| --- | --- | --- |
| S1 | `_config.yml` 增加 `exclude: [hugo, docs, tools, PROGRESS.md, ...]` | 旧站不再泄漏（已实测泄漏=0，旧站 6 页仍生成） |
| S2 | 新建 Vercel 项目（Root=`hugo`）**预览**，不改域名 | 新站可预览，旧站不动 |
| S3 | 切换 DNS `poet.ismaelan.com` → Vercel；GitHub Pages 停用或改为 `legacy` 分支 | **重大变更，需授权与回滚预案** |
| S4 | 将 Jekyll 旧站文件**归档**（`static/legacy/` 或独立分支），移除 Pages 构建 | Jekyll 彻底退出 |

**回滚**：DNS 切回 GitHub Pages 记录；`main` 旧文件**始终保留**（**不得删除**）。

**风险**：DNS 切换有 **TTL 传播期**与 **HTTPS 证书重签**（Vercel 需重新签发），
切换窗口内可能出现短暂证书告警。**需在低峰期执行并保留回滚窗口。**

---

## 7. 部署后路径错误风险清单（**存在风险**）

| # | 风险 | 实测/推断 | 建议 |
| --- | --- | --- | --- |
| P1 | `favicon.ico` 缺失，`head-meta` 引用它 → 404 | **已验证**（无该文件） | 添加 favicon 或移除引用 |
| P2 | 旧站 `/style.css` 在新站 404 | **已验证** | 补 `/style.css` 兼容或接受 |
| P3 | Preview 未传 `--baseURL` → 生产 canonical | **推断**（未部署） | 构建脚本按环境切换 baseURL |
| P4 | `/legacy/` 被收录 | **已验证**（无 noindex） | 决定是否加 noindex |
| P5 | Root Directory 误设 → Jekyll 污染 | **已验证**（可复现） | Root=`hugo`；加 `exclude` |
| P6 | `/legacy/` 绝对路径引用新站根 | **已验证** | 按归档报告 §4 修正 |

---

## 8. 文学作品保护机制审查（**部分验证**）

| 能力 | 现状 | 状态 |
| --- | --- | --- |
| 1. 原文不被自动改写 | `typographer=false`；`{{< poem >}}` 纯文本 | **已验证**（15 用例全过） |
| 2. 换行/空格/标点保留 | `hardWraps=true` + `white-space:pre-wrap` | **已验证** |
| 3. 不同版本并存 | Git 版本化；**无**“作品版本”字段 | **存在风险** |
| 4. 修改历史可追溯 | Git 提交级可追溯；**无**逐篇修订记录 | **部分验证** |
| 5. 审阅状态与发表状态分离 | **未分离**（见作者审阅审计 §7） | **存在风险** |
| 6. 类别不被混淆 | v2 分类 A–E；但审阅系统未落地三字段 | **部分验证** |
| 7. 创作/首发/修改时间字段 | **无**（仅有 `date`） | **存在风险** |
| 8. 原始文件与展示文件关系 | **无**显式映射（`content/` 直接是展示源） | **存在风险** |
| 9. 自动化不覆盖原始作品 | 生成脚本会**覆盖**审阅表（非作品原文）；作品原文在 Git | **部分验证** |
| 10. 作者决定公开/时间/版本 | **无**机制 | **存在风险** |

**核心风险**：当前设计把 `hugo/content/posts/*.md` **同时**当作“原始作品”与“网站展示文件”。
一旦为了排版调整 Markdown，**原始文本与展示文本就混为一体**。

**建议（未实施）——引入“源作品层”与“展示层”分离**
```
content-source/          # 权威原始作品（逐字，含完整 front matter，不参与构建）
  poems/<id>.md
hugo/content/posts/      # 展示层（可由脚本从 content-source 生成，附展示字段）
```
配合字段：`work_id`、`version`、`created`、`first_published`、`modified`、
`publication_status`、`author_confirmed`、`source_ref`。

**长期原则（本项目已确立，本报告重申）**：**网站是展示层，GitHub 仓库是源文件与版本记录**，
不能让网站平台成为作品**唯一**保存处。

---

## 9. 建议的未来目录结构（**仅设计，不实施**）

```
poet/
├─ hugo/                      # 1. 新版 Hugo 网站源文件（构建入口，Root Directory）
│  ├─ hugo.toml
│  ├─ layouts/  assets/  static/
│  ├─ static/legacy/          # 4. 旧版静态历史归档（→ /legacy/）
│  └─ content/
│     ├─ posts/               # 3. 展示层内容（由 source 生成或同步）
│     └─ *.md
├─ content-source/            # 2. 正式文学作品权威源（逐字原文 + 元数据）
│  └─ poems/  essays/  novels/  reviews/  translations/
├─ media/                     # 3'. 图片/音频等大文件（与展示层分离，可选）
├─ docs/
│  ├─ author-review/          # 5. 作者审阅材料
│  ├─ audit/                  # 6. 技术文档与审计报告
│  ├─ migration/              # 6'. 迁移文档
│  └─ poetry-discovery/       # 6''. 普查数据
├─ tools/                     # 7. 自动化脚本（只读生成、校验）
├─ legacy-jekyll/             # 4'. 旧 Jekyll 源（冻结保留，不参与构建）
└─ .github/workflows/         # 7. CI/部署配置（未来）
```

**说明**
- `hugo/` 是**唯一构建入口**（Vercel Root Directory）。
- `content-source/` 与 `hugo/content/` **分离**，保证原文与展示文本解耦。
- `legacy-jekyll/` 冻结保存旧 Jekyll 源，**满足“不删除旧文件”**；静态产物另存 `static/legacy/`。
- `docs/`、`tools/` 加入 Jekyll `exclude`（若旧站仍需构建）。

---

## 10. 新旧网站目标架构图

```
                        poet.ismaelan.com
                               │
                 ┌─────────────┴──────────────┐
                 │                            │
          /  (新版 Hugo 站)            /legacy/ (旧版静态归档)
                 │                            │
   ┌─────────────┼─────────────┐      ┌───────┴────────┐
   │             │             │      │                │
 /archive/    /years/      /search/  index.html   archive.html
 /preface/    /about/      /<slug>/  preface.html shi-ren-xiao-zhuan.html
   │                                   na-la-ti.html  qing-chun-de-wu-yu.html
   └── 作品（待作者确认后迁入）          style.css  assets/img/cover.png

  页脚链接：「旧版网站 · 历史存档」 → /legacy/

  构建：Vercel（Root=hugo）  ←→  GitHub 仓库（源文件/版本记录，权威保存）
  旧 Jekyll：冻结归档，退出生产构建
```

---

## 11. 需要作者/负责人作出的决定

| # | 决定 | 关联 |
| --- | --- | --- |
| D1 | 是否采用“源作品层 + 展示层”分离（`content-source/`） | §8 |
| D2 | 是否拆分“归属/边界/发表授权”三字段 | 审阅审计 §7 |
| D3 | 旧页互链策略（归档内互链 / 指向新站） | 归档报告 §4 |
| D4 | `/legacy/` 是否加 `noindex` | §4、§7-P4 |
| D5 | 是否补 `/style.css` 兼容与 favicon | §7-P1/P2 |
| D6 | 305 篇博客 URL 策略（见 CSV） | CSV |
| D7 | 是否授权 Jekyll `exclude` 补丁（S1） | §6 |
| D8 | 是否授权创建 Vercel 预览项目（S2，不动域名） | §6 |

---

## 12. 未验证 / 无法验证

- Vercel 实际构建（未部署）：版本、`baseURL`、缓存头、清理行为、`/legacy/` 输出。
- DNS 切换与 HTTPS 证书重签的实际行为（未执行）。
- GitHub Pages 停用/切换 `legacy` 分支的实际影响（未执行）。
- 搜索引擎对旧站/新站的实际收录（未查询外部数据）。

---

## 13. 证据索引

| 证据 | 来源 |
| --- | --- |
| Hugo 构建 | `cd hugo && hugo --gc --minify`（v0.168.0 extended） |
| 预览隔离 | `--baseURL https://poet-preview.vercel.app/` 实测 |
| Pages 配置 | `GET https://api.github.com/repos/Lawrenceblock/poet/pages` |
| DNS | `socket.gethostbyname_ex` |
| Jekyll 泄漏 | 远程克隆分支 `jekyll build` 实测 |
| 归档输出 | `/tmp/hugo-legacy-test` 实测 |
| 配置 | `hugo/hugo.toml`、`hugo/vercel.json`、`hugo/layouts/**` @ `172ec94` |

> 本报告为**只读审计 + 临时目录实测**；**未**修改 `main`、未部署、未改 DNS/Vercel。
