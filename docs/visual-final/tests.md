# 视觉候选 · 验证报告（Build / Content / URL / Function / Security）

> 分支 `design/poet-visual-final-2026-11-13`，基线 `1037d1b`。
> 所有结果均为**本会话真实运行**所得，构建产物来自真实 Hugo 构建。

---

## 1. 构建验证

| 项目 | 结果 |
|------|------|
| Hugo 版本 | **Extended v0.168.0**（与 `hugo/vercel.json` 的 `HUGO_VERSION` 一致） |
| `hugo --gc --minify`（预览 baseURL） | ✅ 成功，18 页，0 ERROR / 0 WARN |
| `hugo --gc --minify`（生产 baseURL `poet.ismaelan.com`） | ✅ 成功，22 个 HTML |
| `tools/preview/build_preview.py` | ✅ 成功，含 `/review/` 137 页 |
| verbatim 校验（`tools/author-review/verify_verbatim.py`） | ✅ 137 检查 / 137 一致 / OK |

## 2. 内容保真（最关键）

| 检查 | 方法 | 结果 |
|------|------|------|
| 公开站 6 首诗正文逐字不变 | 解析 `div.poem-content` 纯文本，基线（第三轮构建）vs 本轮构建 | **6/6 逐字节一致** |
| 旧站存档页不变 | `diff -rq` 两个构建的 `legacy/` 目录 | **完全一致** |
| 审阅页 137 篇正文不变 | 剥离 `<style>` 后逐文件比对（本轮重生成 vs 已提交基线） | **154/154 仅样式块不同，正文 0 处差异** |
| 审阅数据文件不变 | `data/candidates.json` JSON 结构比对 | **一致** |
| 内容与配置未被改动 | `git status` 检查 `hugo/content/**`、`hugo/hugo.toml`、`hugo/static/**`、`docs/poetry-discovery/**` | **无改动** |

> 说明：审阅页由 `tools/author-review/build_review_site.py` 从公开 feed 重新生成，
> 结果显示**只有内联样式块变化**，137 篇诗歌正文（`<div class="poem">` 内容）逐字一致。
> 该生成脚本本轮只改动了 `PAGE_CSS`（页眉配色），未触及任何数据/结构/API 逻辑。

## 3. URL 兼容性

用 `git worktree` 分别构建基线（`1037d1b`）与本轮的生产输出，比对全部文件路径：

```
基线页面: 22   本轮页面: 22
仅基线有: []   仅本轮有: []
HTML 路径完全一致；全部产物路径一致（忽略 CSS 指纹哈希）
```

结论：**零 URL 漂移**。`/archive/`、`/years/`、`/preface/`、`/shi-ren-xiao-zhuan/`、
`/about/`、`/search/`、`/YYYY/MM/slug/`、`/legacy/`、`#year-YYYY` 锚点均未变。

## 4. 功能验证

| 功能 | 方法 | 结果 |
|------|------|------|
| 导航 | 页眉/页脚链接 | ✅ |
| 内部链接完整性 | `tools/verify/check_links.py` | 176 页 / 1302 链接 / **0 broken** |
| 搜索 | headless 输入「雨」/「雪」，读取 `/index.json` | ✅ 命中 2 / 1 条，状态文案正确 |
| 年份跳转 | `/years/` 锚点 | ✅ `#year-2008 / 2019 / 2026` |
| 作品返回链接 | 诗歌页 `← 卷目` | ✅ |
| RSS | `index.xml` 生成 | ✅ |
| Sitemap | `sitemap.xml` 生成 | ✅ |
| robots.txt | 生产 `Allow: /`；预览 `Disallow: /` | ✅ |
| 404 | `404.html` 生成，含返回首页/卷目链接 | ✅ |
| 生产输出清洁度 | `tools/verify/check_production_output.py` | ✅ PRODUCTION OUTPUT CLEAN（无 `/review/`、无私有材料） |
| canonical / robots | 生产输出 `index,follow` + canonical；预览 `noindex,nofollow` | ✅ |

## 5. 安全门禁（作者审阅系统，未削弱）

以 `REVIEW_ACCESS_TOKEN` 启动 `tools/review/serve_review.py` 后实测：

| 请求 | 结果 |
|------|------|
| `/review/`（无令牌） | **401** |
| `/review/poem/C0001.html`（无令牌） | **401** |
| `/review/`（HEAD，无令牌） | **401** |
| `/api/reviews`（无令牌） | **401** |
| `/api/health`（无令牌） | **401** |
| `/api/reviews?token=错` | **401** |
| `/review/?token=正确` | **303** → 重定向去掉令牌 |
| `/review/`（带 cookie） | **200** |
| `/api/reviews`（带 cookie） | **200**，`progress.total=137` |
| `POST /api/review`（无令牌） | **401** |
| `POST /api/review?test=1`（正确令牌） | ✅ 保存成功；仅写入隔离的 `journal-test.jsonl`，**真实记录未触碰** |

- 审阅记录目录中**只有 `DESIGN.md` 与临时测试文件**，真实 journal/snapshot 未被写入（测试后已清理）。
- 令牌未写入预览产物、日志或截图。

## 6. 视觉度量（真实构建）

| 页面 | 桌面黑占比 | 移动黑占比 | 横向溢出 |
|------|-----------|-----------|----------|
| 首页 | 44% | 34% | 无 |
| 诗歌 | 38% | 37% | 无 |
| 卷目 | 24% | 28% | 无 |
| 说明 | 17% | 20% | 无 |

- 首页主视觉高度 492px（桌面）/ 368px（移动），不再撑满首屏。
- 首页内容块宽度 400 / 560px 交错（非对称）。
- 诗歌正文栏 576px（桌面），行高 39.1px（17px × 2.3）。

## 7. 截图

真实构建的候选页面截图见 `screenshots/visual-final/`（桌面 + 移动，共 22 张）：

- `final-01-home-*`、`final-02-poem-*`、`final-03-archive-*`、`final-04-years-*`
- `final-05-biography-*`、`final-06-about-*`、`final-07-preface-*`
- `final-08-search-*`、`final-09-404-*`
- `final-15-review-index-*`、`final-16-review-poem-*`（作者审阅页）

## 8. 尚未验证 / 需作者决定

- 作者对视觉的**主观验收**（本报告只提供客观度量与截图，不能替代作者判断）。
- 移动端真机字体渲染（本环境使用 headless Chromium；系统宋体栈在不同设备上观感可能不同）。
- 外部 HTTPS 预览地址：本环境沙盒的 work-1/work-2 地址由运行时提供，若失效需重建。
