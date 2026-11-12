# 安然诗歌档案 · 最终建设总策划书（FINAL IMPLEMENTATION PLAN）

> 文档性质：**总策划书**（规划，不实施）。
> 编制：OpenHands AI 代理 · 日期：2026-11-12
> 目标仓库：`Lawrenceblock/poet`
> 编制时基线：分支 `feat/author-review-system` @ `5b423d8`；PR #10（open, draft, base `site/poetry-site-v1-2026-11-12`）；`main` @ `ee94501`
> 事实标注约定：**【已验证】**= 本轮只读复核确认；**【推断】**= 由证据推断；**【建议】**= 方案主张；**【待确认】**= 需作者或负责人决定。

---

## 0. 文档目的与边界

本策划书把项目从「零散 Phase」收敛为**两阶段、可一次做完**的完整建设方案：

- **第一阶段**：项目收尾 + 预验收交付（形成作者可浏览的候选版本）。
- **第二阶段**：最终验收 + 正式发布（需显式授权）。

**本轮只做规划。** 未修改任何现有文件、未创建实施 PR、未合并、未改 `main`、未部署、未改 DNS/Vercel、未外传任何审阅数据。本策划书以**独立交付物**形式提交（见 §15）。

**贯穿全程的硬约束**（见 §7.5 与 §12）：不得提交作者审阅意见到 Public 仓库；不得把私人审阅数据只放在工作区；不得用未保护的公开链接传递令牌；不得在日志记录令牌或私人内容；不得删除/覆盖真实审阅记录；不得把测试记录混入正式数据；不得改诗歌正文；不得擅自改 DNS/Vercel；不得未经授权合并 PR。

---

## 1. 项目现状审计

### 1.1 仓库与分支状态【已验证】

| 项 | 值 | 说明 |
| --- | --- | --- |
| 仓库可见性 | **public** | 隐私风险最高，审阅数据严禁提交 |
| 默认分支 | `main` @ `ee94501`「Update index.html」 | **仍是旧 Jekyll 站**（`_config.yml`/`_posts`/`index.html`/`CNAME`） |
| PR #10 | open · **draft** · head `feat/author-review-system` @ `5b423d8` · base `site/poetry-site-v1-2026-11-12` @ `8247026` | 未合并 |
| base 相对 main | **领先 28 个提交，落后 0** | `main` 是 base 的祖先 |
| 线上 `poet.ismaelan.com` | HTTP 200，`server: GitHub.com` | **当前由 GitHub Pages 服务旧 Jekyll 站** |

### 1.2 分支拓扑【已验证】

`main`（旧 Jekyll，`ee94501`）→（领先 28）→ `site/poetry-site-v1-2026-11-12`（`8247026`，含 `hugo/`、`docs/`、`tools/`）→ `feat/author-review-system`（`5b423d8`，+2 提交：作者审阅系统 + 加固）。

其余分支均为**已并入 base 的历史工作**（`research/poetry-discovery`、`migration/hugo-poetry-foundation`、`audit/*`、`review/*`、`site/hugo-poetry-site-foundation`），对应 PR #1–#9，均**未合并**。

### 1.3 历史工作回顾（必须避免重复建设）【已验证】

| 工作 | 载体 | 状态 |
| --- | --- | --- |
| 诗歌收集/整理/编号 | `docs/poetry-discovery/`（305 篇清单、137 候选、分类 v1/v2、对照表） | 完成 |
| 候选分类复核 | `review/poetry-classification-phase2`（PR #4） | 完成（A=104,B=31,C=1,D=1） |
| Hugo 框架 | `migration/hugo-poetry-foundation`（PR #3）+ `site/hugo-poetry-site-foundation`（PR #7） | 完成 |
| 逐字保真核对 | `tools/author-review/verify_verbatim.py` → **137/137 一致** | 完成 |
| 旧站题记/小传/存档 | `hugo/static/legacy/`、`docs/author-review/site/oldsite/` | 完成 |
| 导航与页面设计 | `hugo/layouts/**`（首页/卷目/年份/题记/小传/说明/搜索/404/RSS） | 完成 |
| 站内链接检查 | 585 条链接 0 断链（本轮复测） | 完成 |
| 预览与作者审阅流程 | `tools/preview/build_preview.py`、`tools/review/serve_review.py` | 完成 |
| 审阅保存/导出/恢复 | `tools/review/store.py`、`backup_review_data.py` | 完成 |
| 数据权限与隐私 | `.gitignore`、令牌门禁（本轮发现缺口，见 1.5） | 部分 |
| 自动化测试与正式构建 | `tools/review/test_review_system.py`（通过）；**Hugo 全量构建未验证** | 部分 |

### 1.4 PR #10 综合验收报告要点（2026-11-12）【已验证】

- 真实审阅数据 **23 行 journal / 19 个唯一候选 / 0 条测试记录**，备份于 `/workspace/backups/author-review/`（两份，SHA256 校验通过）。
- 第 2 批 404 = **预览构建 `rmtree`+`copytree` 竞态**（非文件缺失）；已改原子替换，复测 **0×404**。
- `?test=1` 曾不隔离 POST（造成一次真实写入，已从备份逐字节还原，SHA 一致）；已修复。
- 无鉴权 API 已加 `REVIEW_ACCESS_TOKEN` 门禁。

### 1.5 本轮只读复查**新发现的问题**（未在旧报告中完整覆盖）

| # | 问题 | 证据 | 严重度 |
| --- | --- | --- | --- |
| N1 | **`HEAD` 绕过令牌门禁**：`serve_review.py` 只重写了 `do_GET`/`do_POST`，未重写 `do_HEAD`。实测带令牌启动后，`curl -I /review/` **无令牌返回 200** | 实测 200 | 中（门禁不完整） |
| N2 | **访问日志泄漏令牌**：日志记录完整 `self.path`，`?token=SECRET` 被写入日志 | 实测日志含明文令牌 | 中（违反硬约束 §12.4） |
| N3 | **备份与源数据同卷**：`backup_review_data.py` 默认 `--to /workspace/backups/...`，与源数据同在 `/workspace`（同一 ext4 卷）。工作区回收时**两者同时丢失** | `df` 显示同一 `/dev/nvme0n2` | 高（伪独立备份） |
| N4 | **正式站 URL 结构存在两套**：`hugo.toml` 的 `[permalinks] posts="/:year/:month/:slug/"` 只对 section `posts` 生效；而线上旧站用扁平 `/:title/`（`/na-la-ti/`、`/qing-chun-de-wu-yu/`）。旧站 **6 页扁平** vs 旧博客 **305 篇日期路径** | 实测线上 `/na-la-ti/` 200、`/archive.html` 404 | 中（需统一并锁定） |
| N5 | **`/style.css` 兼容缺口**：线上 `/style.css` 200，新站静态为 `style.css` 但 CSS 管线另出指纹文件；`hugo/layouts/_default/baseof.html` 引用需核对 | 旧站全页引用 `style.css` | 中（旧链接会 404） |
| N6 | **favicon 缺失**：`hugo/static/favicon.ico` 存在（本轮已见），但历史报告称缺失——需在构建后核对实际输出 | 文件存在，输出待构建确认 | 低 |
| N7 | **Hugo 二进制缺失**：环境中无 `hugo`，全量构建与产物核对无法进行 | `which hugo` 空 | **高（阻塞 F 项验收）** |

> N1–N3、N5 必须纳入第一阶段修复批次（§8）。

### 1.6 内容资产清单【已验证】

- 候选总数 **137**（文章级候选，**不等于 137 首诗**）；分类 A=104 / B=31 / C=1 / D=1；`human_review` 全为 `pending`。
- 审阅页 **154**（137 诗页 + 11 批次页 + 5 旧站页 + 索引）；旧站存档 6 页 + 2 首诗。
- 旧博客 **305** 篇，**135 个不同 slug**，扁平 `/:slug/` 将产生 **170 处冲突** → 必须用日期路径或作者指定唯一 slug。
- 旧 URL 映射表 `docs/migration/legacy-url-redirect-map.csv`（305 行，0 冲突）。

### 1.7 线上 URL 实测【已验证】

| URL | 结果 |
| --- | --- |
| `/`、`/archive/`、`/preface/`、`/shi-ren-xiao-zhuan/`、`/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/style.css` | **200** |
| `/archive.html`、`/preface.html`、`/2026/09/nalati.html`、`/robots.txt`、`/sitemap.xml` | **404** |

> 说明：旧站用**目录式**扁平 URL（`/na-la-ti/`），`/archive.html` 已非有效路径。新站必须保留 `/`、`/archive/`、`/preface/`、`/shi-ren-xiao-zhuan/`、`/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/style.css` 这 7 个线上有效路径不失效。

---

## 2. 同类项目研究

> 方法说明：本轮 Tavily 检索额度已耗尽（返回 432），改为**直接核验官方文档与真实运行站点**（HTTP 状态 + 内容），下附可复核链接。**未采信未经验证的二手结论。**

### 2.1 值得采用的经验

| 主题 | 结论 | 参考 |
| --- | --- | --- |
| 静态站 URL 兼容 | Hugo 用 `url:`/`[permalinks]`/`aliases` 精确控制路径与旧链接跳转；`aliases` 生成跳转页 | https://gohugo.io/content-management/urls/ （含 `#aliases`） |
| 目录结构 | Hugo 标准目录（content/layouts/static/assets/config）利于长期维护 | https://gohugo.io/getting-started/directory-structure/ |
| 版本与修订溯源 | `page.GitInfo` 可把每篇的提交时间/作者/哈希写入页面，天然记录「修订版本」 | https://gohugo.io/methods/page/gitinfo/ |
| 双语/多语言 | Hugo 原生多语言，适合中英对照诗 | https://gohugo.io/content-management/multilingual/ |
| 长期可维护 | 尽量用 Hugo 内置能力（无外部服务）；`Hugo Modules` 管理依赖 | https://gohugo.io/hugo-modules/ |
| 部署环境可复现 | Vercel 构建镜像可锁 `HUGO_VERSION`；部署保护可护预览 | https://vercel.com/docs/builds/build-image · https://vercel.com/docs/security/deployment-protection |
| 版本化文本档案 | 数字人文领域以 TEI P5 表达「作品/版本/校勘」，是文本档案的权威参考（**取其思想，非引入其工具链**） | https://www.tei-c.org/release/doc/tei-p5-doc/en/html/index.html |
| 公开 vs 私有仓库 | GitHub 明确定义 public/private 及可见性 | https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories |

### 2.2 不适合当前项目的技术

- **引入数据库/后端 CMS**：与「静态、低维护、无外部依赖」目标冲突。作者审阅用**本地 stdlib 服务 + 文件流水账**已够。
- **TEI XML 全量转换**：会重写作品文本、增加工具链负担，违反「正文逐字不变」。**仅借鉴其「原始版本 vs 修订版本分离」思想**（用 Front Matter 字段表达，不改正文）。
- **复杂前端框架/搜索服务**：当前纯前端 `index.json` 搜索已足；不上 Algolia 等外部依赖。
- **把审阅后台与公开站混部**：必须隔离（见 §6、§7）。

### 2.3 是否需要引入新工具

**【建议】不引入新工具。** 现有 Python 标准库工具链 + Hugo 已覆盖全部需求。唯一需要「补齐」的是**Hugo 二进制**（构建环境，非新依赖）与**工作区之外的备份目的地**（存储位置，非新工具）。

### 2.4 参考：同类个人诗歌站/档案的组织方式（【推断】，基于公开常识，未逐一实测）

个人诗歌站普遍采用：扁平或日期 URL、按年份/主题索引、单篇阅读页（大留白、衬线中文字体）、「关于/小传」固定页、RSS。本项目的 Hugo 框架（卷目/年份/题记/小传/搜索）**已符合该范式**，无需重构。

---

## 3. 最终产品定位

**一个安静、简洁、以文学阅读为中心、可长期保存与维护的个人诗歌档案网站。**

- 不做商业门户、不做资讯流、不做花哨交互。
- 核心价值：**正文准确、可溯源、可长期维护、作者可持续修订**。
- 三类读者：**作者本人**（审阅/修订）、**读者**（安静阅读）、**维护者**（构建/备份）。

---

## 4. 网站信息架构（IA）

### 4.1 页面结构【建议】

```
/                     首页（封面 + 入口：卷目 / 题记 / 小传）
/archive/             卷目（按卷/主题；当前按年份聚合）
/years/               年份归档（时间线）
/preface/             题记
/shi-ren-xiao-zhuan/  诗人小传
/about/               档案说明（来源、版本与修订说明、版权）
/search/              站内搜索（纯前端）
/:year/:month/:slug/  诗歌正文（旧博客 305 篇映射）
/<slug>/              旧站 6 页的扁平兼容路径（na-la-ti、qing-chun-de-wu-yu 等）
/style.css            旧样式兼容路径（保留）
/legacy/**            旧站只读存档（noindex）
/review/**            作者审阅（**仅预览构建**，正式站不含）
```

### 4.2 导航【建议】

顶部固定菜单：卷目 / 年份 / 题记 / 小传 / 档案说明 / 搜索（现有 `[menu.main]` 已定义）。
每篇阅读页：标题 → 日期 → 正文 → 「← 卷目」返回（现有 `post.html`/`single.html` 已实现）。

### 4.3 交叉导航【建议】

- 诗歌页 → 卷目、相邻篇、年份。
- 卷目 → 每篇、年份。
- 题记/小传 → 卷目。
- 站点地图 `/sitemap.xml` + RSS。

---

## 5. 技术架构

### 5.1 现状【已验证】

- **静态生成**：Hugo（`hugo/hugo.toml`；`baseURL=https://poet.ismaelan.com/`；`typographer=false`、`hardWraps=true`、`unsafe=true` 保护诗歌排版）。
- **部署**：目标 Vercel（`hugo/vercel.json`：`framework=hugo`、`HUGO_VERSION=0.168.0`、`outputDirectory=public`）；**尚未部署**。参考先例：`bio.ismaelan.com` 已在 Vercel【已验证 `server: Vercel`】。
- **旧站**：`main` 的 Jekyll 站仍由 GitHub Pages 服务。
- **审阅**：Python stdlib 本地服务 + 文件存储（与公开站隔离）。

### 5.2 目标架构【建议】

```
开发者/维护者 ──构建──> Hugo ──> public/ ──部署──> Vercel ──> poet.ismaelan.com
                                      └──（仅预览）review/ ──> 作者审阅（令牌保护）
审阅数据（私有）──> 独立备份目的地（工作区之外）
```

- **构建可复现**：锁定 Hugo extended 版本（`HUGO_VERSION`），CI/本地一致。
- **审阅隔离**：正式构建 `enableReview=false`，`/review/` 不进入生产产物【已验证】。
- **数据分层**：公开内容（诗歌，逐字）／私有审阅（流水账）／派生（快照/导出）分离。

### 5.3 待补的技术决策【待确认】

- URL 方案统一：旧站 6 页保留扁平，旧博客 305 篇用 `/:year/:month/:slug/`（**建议**，见 §1.3/§14）。
- `/style.css`、`favicon.ico` 兼容与产物核对（§8 修复）。
- `main` 与部署分支的关系（§10/§11，§14 决策）。

---

## 6. 作者审阅系统设计

### 6.1 现有能力【已验证】

- 三层存储：`journal.jsonl`（追加、权威）→ `snapshot.json`（派生当前值）→ 导出 CSV/JSON。
- 页面内真实表单：①审阅结论（keep/hold/exclude/pending）②作品性质（single/multi/non/unsure）③作者意见。
- 保存后回读、进度条、按状态筛选、导出下载。
- 失败明确报错（`REVIEW_FORCE_SAVE_ERROR` 测试）。
- 测试隔离（`?test=1`，本轮已修复查询参数即生效）。
- 令牌门禁（本轮已加，但 **N1/N2 需补**）。

### 6.2 必须完成的加固【建议】

| 项 | 内容 |
| --- | --- |
| 门禁全覆盖 | 重写 `do_HEAD`（及 `do_OPTIONS` 等）纳入 `_authorized`，确保**所有**方法/入口受控（修 N1） |
| 令牌不进日志 | 日志前剥离查询串中的 `token=`，或记录 `self.path.split('?')[0]`（修 N2） |
| 令牌不外泄 | 优先用 `X-Review-Token` 头或 Cookie；`?token=` 仅一次性引导，且**立即**转 Cookie（硬约束 §12.3） |
| 私有化 | 审阅数据仅存私有位置；公开仓库永不提交（现有 `.gitignore` 保留并复核） |
| 版本与审计 | 每条记录保留 `rev`/`updated_at`；导出附带 `generated_at` |

### 6.3 边界声明【建议】

- 审阅系统**只写审阅数据**，永不触碰作品正文/feed/候选 CSV。
- 作者意见**未经作者确认不得外泄**；导出文件亦视为私人内容。

---

## 7. 数据保护与备份方案

### 7.1 数据分类【已验证】

| 类别 | 位置 | 是否公开 |
| --- | --- | --- |
| 公开内容（诗歌正文） | `hugo/content/**`、`docs/author-review/site/**`（预览用） | 公开站可见（经确认后） |
| 私有审阅数据 | `docs/author-review/review-records/{journal.jsonl,snapshot.json,export-*}` | **严禁提交** |
| 派生/中间物 | 快照、导出、`work/`（feed 抓取） | 不提交 |

### 7.2 备份方案（**修复 N3 的关键**）【建议】

**原则：至少一份备份位于工作区之外（不同卷/不同存储）。**

1. **本地副本**（现有）：`/workspace/backups/author-review/<时间戳>/` + SHA256SUMS + manifest。
2. **工作区外副本**（**必须**）——三选一，按可用性：
   - (a) **私有 GitHub 仓库**（如 `poet-review-records`，**private**）：`git push` 审阅数据。优点：异地、有历史、可恢复。**注意：必须 private，且绝不放入公开 `poet` 仓库。**
   - (b) **外部对象存储/网盘**（作者自己的云盘/对象存储）：定期上传备份目录。
   - (c) **作者本地机器**：下载导出 CSV/JSON 保存。
3. **备份频率**：每次作者审阅会话结束后、以及每个实施批次结束时。
4. **恢复演练**：第一阶段必须实测「从工作区外备份恢复到空环境」，并出具报告。

### 7.3 恢复机制【已验证可用】

`tools/review/backup_review_data.py backup|verify|restore`；恢复前自动给当前数据做安全备份；校验失败**拒绝**恢复。**待补**：把 `--to` 默认指向工作区外目的地，或在文档中强制要求。

### 7.4 灾难恢复（DR）【建议】

- 明确 **RPO**（可接受丢失量）= 一次审阅会话；**RTO**（恢复时间）= 分钟级（复制+`restore`）。
- 演练：模拟「工作区被回收」→ 从私有仓库/外部副本恢复 → 校验 19 条记录一致。

### 7.5 隐私硬约束（项目级，不可违反）【建议，与 §12 一致】

1. 审阅意见**永不**提交到 Public 仓库。
2. 审阅数据**永不**只存在于唯一工作区。
3. **不用**未保护的公开链接传递令牌。
4. 日志**不记录**令牌或私人审阅内容。
5. **不删除/覆盖**真实审阅记录（追加式；删除须作者授权）。
6. 测试记录**不混入**正式数据（`test:true` + 独立 `journal-test.jsonl`）。
7. **不改**诗歌正文。
8. **不擅自改** DNS/Vercel/部署。
9. **不未经授权合并** PR。
10. **不因某项测试通过就跳过其他独立验收项**。

---

## 8. 第一阶段：全部实施任务（批次化）

> 原则：**合并为完整批次**，一次做完，避免负责人逐项参与。每批次末尾更新 `PROGRESS.md`。

### 批次 P1-A：环境与构建基础
- 安装/固定 **Hugo extended**（与 `vercel.json` 的 `0.168.0` 对齐），记录 `hugo version`。
- 复核 `hugo/hugo.toml`（permalink、`typographer=false`、`hardWraps`）。
- **修复 N5/N6**：`/style.css` 兼容、`favicon.ico` 产物核对。
- 产出：构建环境说明 + 版本锁定。

### 批次 P1-B：内容完整性与保真
- 运行 `verify_verbatim.py`（**137/137**）、链接检查（**0 断链**）。
- 生成**完整候选清单**（137 行，含分类、边界问题、待确认问题）。
- 生成**审阅状态清单**（当前 19 已审 / 118 未审）。
- 生成**待作者确认清单**（标题/正文/时间/发表信息中不确定项，**不得自行补全**）。
- 产出：三份清单 + 保真报告。

### 批次 P1-C：页面设计与导航
- 复核首页/卷目/年份/题记/小传/说明/搜索/404 的呈现。
- **移动端适配**核对（中文字体、行距、中英混排）。
- 交叉导航与返回卷目核对。
- 产出：视觉与可用性问题清单 + 改善建议（**不擅自改诗**）。

### 批次 P1-D：作者审阅系统加固
- **修 N1**（`do_HEAD` 等门禁全覆盖）。
- **修 N2**（日志脱敏）。
- 复核 `?test=1` 隔离与失败反馈。
- 扩充自动化测试（门禁/隔离/恢复/失败）。
- 产出：加固报告 + 测试结果。

### 批次 P1-E：数据保护与恢复演练
- **修 N3**（备份默认指向工作区外；建立私有异地副本）。
- 执行备份 → 校验 → **恢复到空环境**演练。
- 复核公开仓库无任何审阅数据（历史/分支/PR/导出）。
- 产出：备份与恢复验证报告 + 隐私审计报告。

### 批次 P1-F：预览稳定性
- 复核 `build_preview.py` 原子替换（**0×404** 复测）。
- 预览服务器令牌保护 + 访问日志。
- 产出：预览稳定性测试报告。

### 批次 P1-G：全站构建与链接测试
- **Hugo 全量构建**（`hugo --gc --minify`）→ 核对产物（`/review/` 不含、`/style.css`、`favicon`、`sitemap`、`robots`、`legacy/`）。
- 全站链接测试（含旧 URL 兼容）。
- 产出：构建报告 + 链接测试报告。

### 批次 P1-H：候选版本交付
- 生成**完整可浏览预览**（作者链接）。
- 汇总第一阶段的 8 份交付物（§9）。
- 更新 `PROGRESS.md`，**停止所有开发**。
- 产出：最终预验收报告。

---

## 9. 第一阶段验收标准

**全部满足方可提交验收：**

1. 网站能完整构建（Hugo 全量成功）。
2. 所有主要页面可正常浏览（含移动端）。
3. 诗歌内容形成完整候选清单（137 行 + 边界问题）。
4. 正文保真检查通过（137/137）。
5. 作者审阅系统可正常使用（保存/回读/导出）。
6. 私人审阅意见有**工作区之外**的独立备份。
7. 数据恢复测试通过（空环境恢复演练成功）。
8. 重大安全问题已解决（N1/N2/N3 修复；无鉴权缺口）。
9. 未发生未经授权的内容修改（正文逐字不变）。
10. 所有未解决问题均已列明（待作者确认清单）。

**第一阶段交付物（8 份）**：①可浏览预览 ②候选清单 ③审阅状态清单 ④待作者确认清单 ⑤技术测试报告 ⑥隐私与安全审计报告 ⑦备份与恢复验证报告 ⑧最终预验收报告。

**第一阶段结束后：停止开发，等待作者与 ChatGPT 审查。第一阶段完成不自动获得第二阶段权限。**

---

## 10. 第二阶段：发布流程

> **前提**：第一阶段验收通过 + 作者完成确认 + 负责人**显式授权**。

1. 按批准的分支方案合并 PR（见 §11.1）。
2. 将验收版本并入**发布分支**（**建议** `release/poet-v1`，或经授权的 `main` 合并路径）。
3. 配置正式部署（Vercel 项目，Root Directory=`hugo`）。
4. 检查 Vercel 构建（`HUGO_VERSION`、产物）。
5. 检查域名与 DNS（`poet.ismaelan.com`）。
6. 检查 HTTPS。
7. 逐页检查正式站（首页/卷目/年份/题记/小传/说明/搜索/诗歌/旧链接）。
8. 检查搜索、导航、作品链接、旧 URL 兼容（7 个线上路径不失效）。
9. **检查审阅系统与公开站隔离**（正式产物无 `/review/`、无审阅数据）。
10. 发布后回归测试（链接、RSS、sitemap、robots、404）。

### 10.1 分支与合并路径（修 G）【建议】

**问题**：PR #10 的 base 是 `site/poetry-site-v1-2026-11-12` 而非 `main`，因为 `main` 仍是**旧 Jekyll 站**，而新站结构（`hugo/`、`docs/`、`tools/`）在 base 分支上。这是**正确的历史原因**，但需要一条**安全的收尾路径**。

**建议路径（任一，经负责人批准）**：
- **方案 1（推荐，最安全）**：新建 `release/poet-v1`（自 `site/poetry-site-v1-2026-11-12`），第一阶段产物与第二阶段发布均在此分支；**最后**再以受控方式把 `main` 切到该版本（或把 Pages/Vercel 指向该分支）。保留 `main` 旧站可回滚。
- **方案 2**：第一阶段合并 PR #10 → `site/poetry-site-v1-2026-11-12`；第二阶段以 `site/poetry-site-v1-2026-11-12` → `main` 的 PR 发布（需负责人授权）。
- **方案 3**：维持 `main` 为旧站不动，部署侧改用 Vercel 指向新分支（需评估 GitHub Pages 与 Vercel 并存期）。

**回退**：任何发布前，`main`/旧站**保持可服务**；发布后如需回退，DNS/Vercel 切回旧站（**需授权**）。

---

## 11. 第二阶段验收标准

1. 正式网站可正常访问（HTTPS）。
2. 作品内容与作者最终确认版本一致（逐字）。
3. 页面及导航检查通过。
4. 备份系统正常运行（含工作区外副本）。
5. 私人审阅资料**没有**进入公开网站。
6. 所有发布变更均有记录。
7. 最终版本 commit SHA 明确。
8. 负责人确认正式交付。

### 11.1 第二阶段前置检查清单

- [ ] 作者已确认全部收录作品与正文。
- [ ] 作者已确认题记/创作时间/发表信息。
- [ ] 作者已确认小传。
- [ ] 第一阶段全部验收项通过。
- [ ] 负责人书面授权合并/部署/改 DNS。
- [ ] 回滚方案就绪（旧站可服务）。

---

## 12. 项目风险及回退机制

| 风险 | 等级 | 缓解 | 回退 |
| --- | --- | --- | --- |
| 审阅数据随工作区回收丢失 | **高** | 工作区外私有副本 + 恢复演练 | 从私有仓库/外部副本恢复 |
| Public 仓库泄漏作者意见 | **高** | `.gitignore` + 历史/分支/PR 扫描 + 私有备份 | 若泄漏：移除文件、轮换、通知 |
| 令牌门禁不完整（N1）/日志泄漏（N2） | 中 | 全覆盖门禁 + 日志脱敏 | 关闭预览、重置令牌 |
| 预览 404 竞态 | 中 | 原子替换（已修） | 重启预览 |
| URL 迁移导致旧链接失效 | 中 | 日期路径 + `aliases` + `/style.css` 兼容 | 保留旧站/加 301 |
| Hugo 构建环境缺失（N7） | **高** | 第一阶段安装并锁定 | 本地构建，暂不部署 |
| 正文被意外修改 | **高** | `verify_verbatim` 门禁 + 只读数据源 | 从 git 历史恢复 |
| 合并/DNS 误操作 | 高 | 授权关卡（§14 权限表） | 旧站仍可服务 |

**回退总原则**：`main`/旧站**在切换完成前始终保持可服务**；任何破坏性操作前先做可校验备份。

---

## 13. 预计工作量

> 以「批次」为单位，**每批次一次完成**，避免负责人逐项参与。

| 阶段 | 批次 | 预估 | 依赖 |
| --- | --- | --- | --- |
| 一 | P1-A 环境与构建 | 0.5 天 | Hugo 二进制 |
| 一 | P1-B 内容与保真 | 0.5 天 | 无 |
| 一 | P1-C 设计与导航 | 1 天 | 无 |
| 一 | P1-D 审阅加固 | 0.5 天 | 无 |
| 一 | P1-E 备份与恢复演练 | 0.5 天 | 工作区外目的地 |
| 一 | P1-F 预览稳定性 | 0.25 天 | 无 |
| 一 | P1-G 全站构建与链接 | 0.5 天 | P1-A |
| 一 | P1-H 候选版本交付 | 0.5 天 | P1-A…G |
| 二 | 发布与回归 | 1 天 | 作者确认 + 授权 |
| | **合计** | **≈5.25 天** | |

---

## 14. 权限与授权关卡

| 操作 | 第一阶段 | 第二阶段 |
| --- | --- | --- |
| 只读检查仓库 | 允许 | 允许 |
| 修改 PR 分支 | 按批准方案允许 | 按批准方案允许 |
| 创建预览版本 | 允许 | 允许 |
| 修改 `main` | **禁止** | **单独授权** |
| 合并正式 PR | **禁止** | **单独授权** |
| 修改 DNS | **禁止** | **单独授权** |
| 修改 Vercel | **禁止** | **单独授权** |
| 正式部署 | **禁止** | **单独授权** |
| 正式公开发布 | **禁止** | **单独授权** |

---

## 15. 需要作者决定的问题（汇总）

**内容与作品**
1. 137 个文章级候选中，哪些收入正式站？是否还有 305 篇中未被识别的作品应纳入？
2. 组诗/多首文章（7 篇已标记）是否拆分？拆分后各首如何命名与排布？
3. 《青春的物语》旧站版 vs 旧博客版采用哪一版？是否保留中英双语？
4. 《那拉提（未赴）》《诗人小传》来源与定稿确认。
5. 每篇的**标题 / 创作时间 / 发表信息**最终确认（不确定项已标「待确认」，AI 不补全）。
6. 作者小传与题记的最终文本。
7. 是否需要为中文标题文章指定**可读英文 slug**（由作者命名）。

**技术与发布**
8. URL 方案：旧站 6 页保留扁平、旧博客 305 篇用 `/:year/:month/:slug/`，是否同意？
9. 旧博客域名 `www.ismaelan.com` 是否保留、是否设 301（跨域，需由旧站自身实施）。
10. 审阅数据**工作区外备份目的地**选哪一种（私有仓库 / 云盘 / 本地）。
11. 分支与合并路径：方案 1 / 2 / 3（§10.1）。
12. 版权与许可声明（`/about/`）文本。

---

## 16. 参考链接（本轮已核验可达）

- Hugo URLs / aliases：https://gohugo.io/content-management/urls/
- Hugo 目录结构：https://gohugo.io/getting-started/directory-structure/
- Hugo GitInfo：https://gohugo.io/methods/page/gitinfo/
- Hugo 多语言：https://gohugo.io/content-management/multilingual/
- Hugo Modules：https://gohugo.io/hugo-modules/
- Hugo 配置：https://gohugo.io/configuration/all/
- Vercel 构建镜像：https://vercel.com/docs/builds/build-image
- Vercel 项目配置：https://vercel.com/docs/project-configuration
- Vercel 部署保护：https://vercel.com/docs/security/deployment-protection
- Vercel 框架：https://vercel.com/docs/frameworks
- TEI P5（数字文本档案思想参考）：https://www.tei-c.org/release/doc/tei-p5-doc/en/html/index.html
- GitHub 仓库可见性：https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories
- GitHub Pages 说明：https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages

> 说明：因检索额度限制，未做更广泛的同类站点普查；上述为官方/一手来源。后续可补做同类诗人站点的可视化对比。

---

## 17. 结论与下一步

- 项目**已接近可交付**：内容、Hugo 框架、审阅系统、保真与链接检查均已就绪；**剩余为收尾、加固与构建验证**。
- 关键缺口：**Hugo 构建环境（N7）**、**审阅门禁全覆盖（N1）**、**日志脱敏（N2）**、**工作区外备份（N3）**、**URL/样式兼容（N4/N5）**。
- 建议按 §8 的 **P1-A…P1-H** 批次一次性完成第一阶段，交付作者可浏览的候选版本与 8 份报告，然后**停下等待审查**。
- 第二阶段**须显式授权**，按 §10 流程执行，保留可回滚。

> 本策划书由 AI 代理（OpenHands）编制，供 ChatGPT 审核、项目负责人决策、作者确认。
