# Phase C 审计：旧版网站静态归档迁移方案

> 审计日期：2026-11-12
> 目标域名：`poet.ismaelan.com`（新版 Hugo 站 → 根目录；旧版 → `/legacy/`）
> 审计方法：只读。`git show main:...` + `curl` 线上抓取 + 临时目录静态归档实测。
> 状态标记：**已验证 / 部分验证 / 尚未验证 / 存在风险 / 需要作者决定**
>
> ⚠️ 本报告讨论的是**旧版网站页面**（约 6 个 HTML）的静态归档。
> **旧博客 305 篇文章**的迁移是**另一个独立问题**，见 `legacy-content-url-migration-plan.csv`
> 与 `phase-c-legacy-archive-migration-plan.md` 第 7 节。两者**不得混淆**。

---

## 1. 旧版网站清点（**已验证**）

项目所有者认为“可能只有两三个页面”；实测**不止**。旧站（`main` 分支根目录）实际有：

**仓库文件（`git ls-tree -r main`）**

| 类型 | 文件 | 说明 |
| --- | --- | --- |
| 配置 | `_config.yml` | Jekyll 配置（`permalink: /:title/`） |
| 配置 | `CNAME` | `poet.ismaelan.com` |
| 文档 | `README.md` | 仓库说明 |
| 模板 | `_layouts/default.html`、`_layouts/post.html` | Jekyll 布局 |
| 内容 | `_posts/2026-04-07-qing-chun-de-wu-yu.md` | 青春的物语 |
| 内容 | `_posts/2026-09-07-na-la-ti.md` | 那拉提（未赴） |
| 内容 | `_posts/2026-09-11-shi-ren-xiao-zhuan.md` | 诗人小传 |
| 页面 | `index.html` | 首页（独立 HTML，非 Jekyll 渲染） |
| 页面 | `archive.md` | 卷目 |
| 页面 | `preface.md` | 题记 |
| 样式 | `style.css` | 全站样式 |
| 资源 | `assets/img/cover.png` | 封面（195,938 字节） |

**线上页面（`curl` 实测，2026-11-12）**

| URL | 状态 | 字节 | 备注 |
| --- | --- | --- | --- |
| `/` | 200 | 1642 | 首页 |
| `/archive/` | 200 | 1039 | 卷目 |
| `/preface/` | 200 | 723 | 题记 |
| `/shi-ren-xiao-zhuan/` | 200 | 4237 | 诗人小传 |
| `/na-la-ti/` | 200 | 773 | 诗歌页 |
| `/qing-chun-de-wu-yu/` | 200 | 3071 | 诗歌页（中英双语） |
| `/style.css` | 200 | 1706 | 样式 |
| `/assets/img/cover.png` | 200 | 195938 | 封面 |
| `/CNAME` | 200 | — | 被 Pages 直接发布（**应移除**） |
| `/feed.xml`、`/sitemap.xml`、`/robots.txt`、`/404.html` | 404 | — | 旧站**无**这些 |
| `/README.md`、`/_config.yml`、`/archive.md`、`/preface.md` | 404 | — | 未被发布 |

**结论**：旧站**共 6 个 HTML 页面**（`index`、`archive`、`preface`、`shi-ren-xiao-zhuan`、`na-la-ti`、`qing-chun-de-wu-yu`）
＋ 1 个 CSS ＋ 1 张封面图。**不是两三个页面**。

**隐藏/意外文件**：`/CNAME` 可被公开访问（Jekyll 未排除），归档时应删除或排除。

---

## 2. 页面内部引用分析（**已验证**）

**检查方法**：抓取 6 个 HTML，正则提取所有 `href`/`src`。

| 页面 | 绝对路径引用（`/...`） | 相对引用 | 外部引用 |
| --- | --- | --- | --- |
| `index.html` | `/archive/`、`/preface/` | `style.css`、`assets/img/cover.png` | `https://bio.ismaelan.com/` |
| `archive.html` | `/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/shi-ren-xiao-zhuan/`、`/style.css` | — | — |
| `preface.html` | `/style.css` | `style.css`（重复，含一处 `<link>` 在 `<body>` 内） | — |
| `shi-ren-xiao-zhuan.html` | `/archive/`、`/style.css` | — | — |
| `na-la-ti.html` | `/archive/`、`/style.css` | — | — |
| `qing-chun-de-wu-yu.html` | `/archive/`、`/style.css` | — | — |

**关键发现**
1. 首页用**相对** `style.css` 与 `assets/img/cover.png`；其余页面用**绝对** `/style.css`。
2. 所有页面用**绝对** `/archive/`、`/preface/` 等站内链接——**指向新站根目录**。
3. 首页外链 `https://bio.ismaelan.com/`（独立站点，**本次不涉及**）。
4. `preface.html` 存在**重复 `<link rel=stylesheet>`**（`<head>` 一处、`<body>` 一处）。

---

## 3. 静态归档可行性测试（**已验证**）

**测试环境**：临时目录 `/tmp/hugo-legacy-test`（**合成/公开内容，未提交仓库**）。

**测试方法**
```bash
cp -r hugo /tmp/hugo-legacy-test
mkdir -p /tmp/hugo-legacy-test/static/legacy/assets/img
cp <6 html + style.css> static/legacy/
cp cover.png static/legacy/assets/img/
cd /tmp/hugo-legacy-test && /tmp/hugo --gc --minify
```

**实际结果**：Hugo **原样**把 `static/legacy/**` 输出到 `public/legacy/**`（8 个文件，逐一 200）：

```
public/legacy/index.html  archive.html  preface.html  bio.html(小传)
              nalati.html qingchun.html style.css  assets/img/cover.png
```

| 检查项 | 结果 | 状态 |
| --- | --- | --- |
| HTML 能否独立运行 | 能，页面可正常渲染 | **已验证** |
| 相对路径（首页） | 归档后 `style.css`、`assets/img/cover.png` 在 `/legacy/` 内解析正确 | **已验证** |
| 绝对路径（其余页） | `/style.css`、`/archive/` 指向**新站根目录**，**不是** `/legacy/` | **存在风险** |
| 图片显示 | `/legacy/assets/img/cover.png` → 200 | **已验证** |
| CSS 加载 | `/legacy/style.css` → 200；但页面引用的是 `/style.css`（新站无此文件→404） | **存在风险** |
| 内部链接 | `/archive/` 等指向新站同名页（新站有 `/archive/`），语义**可接受**；但 `/na-la-ti/` 在新站 404（尚未迁移） | **存在风险** |
| 外观与文字保持 | 未改动任何 HTML 字符，外观不变 | **已验证** |

**实测证据（根路径解析冲突）**
```
200  /legacy/                  （归档页本身）
200  /archive/                 ← 旧页面的 /archive/ 指向这里（新站）
404  /style.css                ← 旧页面的 /style.css 在这里 404
404  /na-la-ti/                ← 旧页面的 /na-la-ti/ 在这里 404
```

---

## 4. 需要修改的引用与最小修改方案（**建议，未实施**）

**目标**：让 `/legacy/` 下的旧页面**自包含**，不依赖新站根目录，也不被新站覆盖。

**方案（最小改动，可回滚）**：仅改**绝对路径引用**，不改任何**文字**。

| 位置 | 现状 | 建议 | 说明 |
| --- | --- | --- | --- |
| 5 个页面的 `/style.css` | 绝对 | `style.css` 或 `/legacy/style.css` | 指向归档内 CSS |
| `archive.html` 的 `/na-la-ti/` 等 | 绝对 | `/legacy/na-la-ti.html`（或保留指向新站） | **需作者/负责人决定**：是“旧页互链”还是“旧页→新页” |
| 各页 `/archive/` | 绝对 | `/legacy/archive.html` 或保留 `/archive/` | 同上 |
| `preface.html` 重复 `<link>` | 重复 | 删除 `<body>` 内那一处 | 纯清理，不改文字 |
| `/CNAME` | 被发布 | 不纳入归档（或删除） | 避免暴露配置文件 |

**两种互链策略（需决定）**
- **策略 A（推荐，历史存档）**：旧页之间**互相**链接（`/legacy/...`），归档为**自洽的历史快照**。
- **策略 B**：旧页链接**指向新站**（如 `/archive/`），把旧页当作新站的“历史入口”。
  ⚠️ 若新站尚未迁入对应作品，会产生 404。

> **本阶段只提出方案，未修改任何旧页面文件。**

---

## 5. 旧版 URL 对照表（**部分验证**）

| 旧版原始 URL | 归档后 URL | 需 301？ | 外链失效风险 | 搜索引擎收录 | 验证状态 |
| --- | --- | --- | --- | --- | --- |
| `/` | `/`（新站首页） | 否（同址，内容改为新站） | 低 | 是 | **已验证**（线上 200） |
| `/archive/` | `/archive/`（新站卷目） | 否 | 低 | 是 | **已验证** |
| `/preface/` | `/preface/`（新站题记） | 否 | 低 | 是 | **已验证** |
| `/shi-ren-xiao-zhuan/` | `/shi-ren-xiao-zhuan/`（新站小传） | 否 | 低 | 是 | **已验证** |
| `/na-la-ti/` | `/na-la-ti/`（新站作品，待迁移） | 否（保留同 URL） | 低 | 是 | **部分验证**（旧站 200；新站待迁入） |
| `/qing-chun-de-wu-yu/` | `/qing-chun-de-wu-yu/`（新站作品，待迁移） | 否 | 低 | 是 | **部分验证** |
| `/style.css` | `/css/style.min.<hash>.css` | **是**（或补 `/style.css`） | 低 | 可能 | **已验证**（新站无 `/style.css`） |
| `/assets/img/cover.png` | `/assets/img/cover.png` | 否（同路径保留） | 低 | — | **已验证**（新站已保留同路径） |
| `/CNAME` | —（移除） | 否 | 无 | 否 | **已验证**（不应公开） |

**新增入口**
| 目标 | 说明 |
| --- | --- |
| `/legacy/` | 旧版静态历史存档入口 |
| `/legacy/index.html` 等 6 页 | 旧版页面 |
| 新站页脚链接「旧版网站 · 历史存档」→ `/legacy/` | **建议新增**（未实施） |

> **注意**：本表与“305 篇文章 URL 迁移”**完全分开**。旧站 6 页保留原 URL（同址升级）；
> 305 篇博客文章另见独立 CSV。

---

## 6. Hugo 构建/清理/部署对归档的保护（**已验证 + 建议**）

**风险与实测**

| 风险 | 实测结果 | 结论 |
| --- | --- | --- |
| Hugo 构建**覆盖**归档文件 | `static/legacy/**` 每次**重新生成**（源在 `static/`，是权威源） | **可控**：归档源在 Git，构建可重放 |
| Hugo 构建**删除**归档 | **默认不删**（无 `cleanDestinationDir` 时旧文件残留） | **存在风险**：残留脏文件 |
| `--cleanDestinationDir` | 实测**只删目标目录内**内容，归档**仍在**（因源在 `static/`） | **已验证**，可安全启用 |
| 归档**内容/路径**被改 | Hugo 对 `static/` 文件**逐字节复制**，不改内容 | **已验证** |
| 破坏资源引用 | 见第 3 节：绝对路径冲突 | **存在风险**，按第 4 节修 |

**实测命令与结果**
```bash
echo STALE > public/legacy/stale-marker.txt
hugo --gc --minify                         # 默认：stale-marker 仍在（残留）
hugo --gc --minify --cleanDestinationDir   # 清理：stale-marker 消失，legacy/index.html 仍在
```

**最小化、可回滚的保护方案（建议，未实施）**
1. 旧版页面**源文件**放 `hugo/static/legacy/`（**唯一权威源**，随 Git 版本化）。
2. 归档**不使用** Hugo 动态模板，纯 `static/`（避免被模板逻辑改动）。
3. 部署使用 `--cleanDestinationDir`，确保无残留。
4. 归档加入**校验**：`tools/verify/compare_legacy.py`（建议新增）比对源与产物哈希。
5. **回滚**：`git revert` 归档提交即可；旧站 `main` 原文件**始终保留**。

---

## 7. 与“305 篇文章迁移”的区别（**重要**）

| 维度 | 旧版**网站页面**（本报告 §1–6） | 旧**博客 305 篇**（另一问题） |
| --- | --- | --- |
| 数量 | 6 个 HTML | 305 篇文章 |
| 来源 | `main` 根目录（Jekyll） | `www.ismaelan.com`（Blogger） |
| 现状 | 线上，`poet.ismaelan.com` | 线上，另一个域名 |
| 处理 | 静态归档到 `/legacy/` | **待作者确认**作品边界后迁移 |
| URL 策略 | **保留原 URL**（同址升级） | **待定**（见独立 CSV） |
| 本阶段动作 | 只做方案与实测 | 只做规划表 |

> 二者**必须分别整理**。旧站 6 页的 URL 风险很低（同址），
> 305 篇博客文章的 URL 风险**很高**（见第 8 节与 CSV）。

---

## 8. 旧版归档 URL 风险小结

1. **绝对路径**导致 `/legacy/` 页面引用落到新站根目录——**必须**按第 4 节修正（仅改路径，不改文字）。
2. **`/style.css`** 在新站不存在——旧站样式链接会 404；归档内应改用相对/`/legacy/` 路径。
3. **外链 `bio.ismaelan.com`**：独立站点，**保持不动**（本任务边界外）。
4. **`/CNAME` 暴露**：归档时排除。
5. 旧站**无** `robots.txt`/`sitemap.xml`/`feed.xml`——归档**不引入**这些，避免与 `/legacy/` 的 `noindex` 冲突（见部署报告 §5）。

---

## 9. 需要决定的事项

| # | 问题 | 选项 |
| --- | --- | --- |
| L1 | 旧页互链策略 | A：归档内互链（推荐）／B：指向新站 |
| L2 | 是否修正旧页绝对路径 | 是（推荐，仅改路径）／否（保留原样但接受 404） |
| L3 | 是否在旧站根目录保留旧 `index.html` | 否（根目录交给新站）／是（冲突） |
| L4 | 归档是否含 `/CNAME` | 否（推荐） |
| L5 | 新站页脚是否加「旧版网站 · 历史存档」→ `/legacy/` | 是（推荐，需实施） |

---

## 10. 未验证 / 无法验证

- **Vercel 实际部署**中 `static/legacy/` 的输出行为（**未部署**，仅本地 Hugo 实测）。
- 旧站是否被搜索引擎收录的具体条目（未查询外部收录数据）。
- 归档后旧页在**移动端**的显示（旧站无 `viewport`，见 UX 报告）。

---

## 11. 证据索引

| 证据 | 来源 |
| --- | --- |
| 旧站文件清单 | `git ls-tree -r main` |
| 线上状态 | `curl -o /dev/null -w '%{http_code}' https://poet.ismaelan.com/...` |
| 归档实测 | `/tmp/hugo-legacy-test`（临时，未提交） |
| 清理行为 | `hugo --cleanDestinationDir` 实测 |

> 本报告为**只读审计 + 临时目录实测**；**未**修改 `main`、未改动旧站、未部署。
