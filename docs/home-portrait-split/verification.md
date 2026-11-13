# 首页肖像与黑白几何构图修订 — 验证记录

任务编号：POET-HOME-PORTRAIT-SPLIT-01

## 基线

- **【事实】** 基线分支 `design/poet-visual-final-2026-11-13`，基线提交 `d880011`。
- **【事实】** 修订分支 `design/poet-home-portrait-split-2026-11-13`。

## 图片核实（实施前）

- **【事实】** `hugo/hugo.toml` 配置 `coverImage = "/assets/img/cover.png"`；
  文件 `hugo/static/assets/img/cover.png`（632×679，PNG，含透明通道）。
- **【事实】** 该图为**单色（100% 低饱和）人物立像**，是本站既有封面资源：
  旧站首页 `<img src="assets/img/cover.png" alt="封面">`，由仓库所有者提交
  （`ee94501`，main）。判断为作者希望保留的原有肖像，据此实施。

## 实际修改文件

- **【事实】** `hugo/layouts/index.html` — 仅替换 `<section class="hero">`，新增
  `.hero-portrait`（作者肖像）与 `.hero-text`；移除 `.hero-meta` 数据行。
- **【事实】** `hugo/assets/css/style.css` — 替换首页主视觉 CSS（`.hero` 及桌面/移动
  媒体查询）；同时移除 `@media (max-width:480px)` 中残留的 `.hero-meta` 与
  `.hero-title` 规则（已失效/冲突）。
- **【事实】** 未修改 `cover.png`（`git diff` 为空）；未改其他页面 CSS/模板。

## 构建

- **【事实】** Hugo Extended v0.168.0，`hugo --gc --minify` 成功，18 页，0 ERROR / 0 WARN。

## 几何测量（真实构建，Playwright）

| 项目 | 桌面 1440px | 移动 390px |
|---|---|---|
| 主视觉高度 | 557px | 260px |
| 左侧肖像区宽 | 420px | 137px |
| 右侧文字区宽 | 604px | 214px |
| 左/右比例 | **0.410 / 0.590** | 0.390 / 0.611 |
| 肖像自然尺寸 | 632×679 | 632×679 |
| 肖像显示框 | 340×365（比例 0.932，**未裁切**） | 121×129 |
| 横向溢出 | 无 | 无 |
| `.hero-meta` | 不存在 | 不存在 |

- **【事实】** 桌面比例 41/59，符合设计「左侧约 42%、右侧约 58%」。
- **【事实】** 肖像 `object-fit: contain`，显示框宽高比 = 原始比例，**未裁切人物**。
- **【事实】** 移动端仍为左右分割（未改上下排列），无横向溢出。

## 内容保真

- **【事实】** 公开站 6 首诗歌正文逐字节一致（`.poem-content` 比对）。
- **【事实】** 作者审阅 137 篇：`verify_verbatim.py` → `verbatim-identical: 137`，
  `OK: all checks passed`。
- **【事实】** `docs/author-review/` 站点 HTML 与 `tools/` 审阅代码相对基线**无改动**。

## URL 与功能

- **【事实】** 与基线生产输出比对：**HTML 文件集合完全一致**（22 个），
  仅 `index.html` 内容变化（主视觉区域），无 URL 漂移。
- **【事实】** `check_links.py`：22 页 / 279 内链 / **0 broken**。
- **【事实】** `check_production_output.py`：**PRODUCTION OUTPUT CLEAN**。

## 安全门禁

- **【事实】** `/review/` 无令牌 **401**；`?token=` **303**；带 cookie **200**。
- **【事实】** `/api/reviews` 无令牌 **401**；带 cookie **200**。
- **【事实】** `/assets/img/cover.png` → 200，195,938 字节（与仓库一致）。

## 截图

- **【事实】** `screenshots/home-portrait-split/`：
  - `base-desktop.png` / `base-mobile.png`（修改前整页）
  - `new-desktop.png` / `new-mobile.png`（修改后整页）
  - `base-desktop-hero.png` / `base-mobile-hero.png` / `new-desktop-hero.png` / `new-mobile-hero.png`（主视觉区域特写）

## 未完成 / 需作者决定

- **【尚未验证】** 作者主观验收。
- **【建议】** 移动端主视觉高度由 368px 收窄至 260px（按设计 `min-height:260px`）；
  如作者希望手机端更高，可调整 `@media (max-width:600px) .hero-inner { min-height }`。
- **【建议】** 预览地址为沙盒运行时地址，可能随会话结束失效；未做任何部署。
