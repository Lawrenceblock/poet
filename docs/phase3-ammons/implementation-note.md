# Phase 3 · 实施说明（Implementation Note）

> 视觉设计重构：Ammons/Tubik 编辑设计语言。
> 研究依据：`docs/phase3-ammons/research.md`；规范：`design-system.md`；页面：`page-design.md`。
> 分支：`design/phase3-ammons-editorial-2026-11-13`；基线 commit：`6c9bd55`（Phase 2）。

---

## 1. 改了什么（代码）

| 文件 | 变更 | 说明 |
|------|------|------|
| `hugo/assets/css/style.css` | 重写（504 → 711 行） | 新设计变量与全部组件样式 |
| `hugo/layouts/index.html` | 重排版 | 非对称主视觉 + 5/7 交错内容栅格 |
| `hugo/layouts/_default/single.html` | 重排版 | 黑色页头窄带 + 纸白正文区 |
| `hugo/layouts/_default/archive.html` | 重排版 | 大字号年份 + 编号 + 细线 |
| `hugo/layouts/_default/years.html` | 重排版 | 同上（含年份跳转） |
| `hugo/layouts/_default/list.html` | 重排版 | 统一页头 + 列表 |
| `hugo/layouts/_default/preface.html` | 重排版 | 黑色页头 + 安静阅读区 |
| `hugo/layouts/_default/about.html` | 重排版 | 黑色页头 + `prose` |
| `hugo/layouts/_default/search.html` | 重排版 | 下边框式输入框 |
| `hugo/layouts/404.html` | 重排版 | 统一页头 |
| `tools/author-review/build_review_site.py` | 仅调 `PAGE_CSS` 配色/字族 | 审阅页与公开页视觉一致（不含数据/结构/API） |

**新增（非代码）**

- `docs/phase3-ammons/`：`research.md`、`design-system.md`、`page-design.md`、本文件、`test-report.md`
- `screenshots/phase3/`：桌面 9 张 + 移动 5 张 + 审阅页 2 张

---

## 2. 设计要点（相对 Phase 2 的变化）

- **取消**「黑色栏目标题条」等宽卡片式单元 → 改为**大字号左对齐标题 + 上方细线 + 英文小标签**。
- **新增非对称版式**：首页主视觉 `7fr/5fr`；内容块 `5fr/7fr` 交错（实测块宽 400/560）。
- **字号层级**：Display `clamp(2.6rem,9vw,4.6rem)`（实测 73.6px）、H1 `clamp(1.7rem,4.2vw,2.6rem)`（41.6px）。
- **配色**：纸白 `#FAF9F7` / 墨黑 `#141414` / 结构黑 `#0E0E0E`；暗红 `#7A2A34` 仅用于链接与细线（面积 <2%）。
- **诗歌页**：黑色页头窄带（标题 + 元信息）→ 纸白正文（`--measure-poem: 38rem`），行高 2.3 不变。
- **字体**：中文宋体系；英文/数字/标签用无衬线；**不引入远程字体**。
- **无障碍**：全部文字配色 ≥ AA（正文 17.51:1）；移动导航触控高 44px；无横向溢出。

---

## 3. 硬约束的遵守情况

| 约束 | 状态 | 证据 |
|------|------|------|
| 不改诗歌/小传/题记/档案正文 | ✅ | `git status` 中 `hugo/content/**` 无改动；诗歌 verse HTML 与 Phase 2 逐字一致（见 test-report） |
| 不改 `hugo.toml` 路由/内容配置 | ✅ | `hugo/hugo.toml` 未出现在改动列表 |
| 不改审阅记录/CSV/API/令牌逻辑 | ✅ | 仅 `PAGE_CSS` 字符串变更；137/137 正文逐字一致；401 门禁不变 |
| 不改域名/DNS/正式部署 | ✅ | 未做任何域名或部署操作 |
| 不复制 Ammons/Tubik 素材 | ✅ | 未新增任何图片；参考图仅本地分析 |
| 不动 `main` / 不动 Phase 1、2 | ✅ | 全部提交在 `design/phase3-...` 分支；`main` 未动 |
| 可回滚 | ✅ | 见 §5 |

---

## 4. 预览地址

- **Phase 3 候选预览（work-2，端口 12001）**：
  `https://work-2-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/`
- **作者原始预览（work-1，端口 12000）**：保持**未改动**（仍是作者原先看到的版本）。
- 审阅区需令牌：`/review/?token=…`（令牌值见私密文件，不在报告中记录）。

> 说明：环境仅暴露 work-1 / work-2 两个外部端口。本轮将 Phase 3 放在 work-2，
> 替换掉其上的第二轮候选（第二轮完整保留于 git 分支 `6c9bd55`，随时可重建）。

---

## 5. 回滚方法

1. **看第二轮效果**：
   `git worktree add /tmp/p2wt 6c9bd55`，用 `tools/preview/build_preview.py --outdir …` 构建，
   或直接用已保存在 `/tmp/visual-preview-r2` 的成品（若仍在）。
2. **回退代码**：`git checkout 6c9bd55 -- hugo tools` 即可恢复第二轮全部文件。
3. **丢弃本轮**：删除分支 `design/phase3-ammons-editorial-2026-11-13` 即可，`main` 与第二轮不受影响。
4. 本轮**未触碰** `main`，故不存在需要撤销的主干提交。

---

## 6. 未做的事（明确边界）

- 未修改任何诗歌、作者小传、题记、档案记录的文字或结构。
- 未新增/删除任何内容文件；未改 front matter。
- 未改 `hugo.toml`、GitHub Pages 配置、Actions、仓库设置。
- 未改 DNS、域名、HTTPS、Vercel 配置；未创建/部署 Vercel 项目。
- 未合并任何 PR；未向 `main` 提交。
- 未把参考项目的照片、字体或商业素材纳入仓库。
- 审阅页只调了 CSS 变量（配色/字族），**未改**其 HTML 结构、字段、数据与安全逻辑。
