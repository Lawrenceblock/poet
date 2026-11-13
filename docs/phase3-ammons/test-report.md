# Phase 3 · 测试报告（Test Report）

> 分支 `design/phase3-ammons-editorial-2026-11-13`，基线 `6c9bd55`（Phase 2）。
> 所有测试均为**只读或隔离构建**，未触碰 `main`、域名、部署与内容。
> 报告区分 **【实测】**（本次运行的真实结果）与 **【说明】**。

---

## 1. 构建

**【实测】**

| 项目 | 结果 |
|------|------|
| `hugo --gc --minify`（预览 baseURL） | 成功，18 页 |
| `hugo --gc --minify`（生产 baseURL `poet.ismaelan.com`） | 成功，22 个 HTML |
| `tools/preview/build_preview.py` | 成功，含 `/review/` 137 个诗歌页 |
| Hugo 版本 | v0.168.0 extended |

---

## 2. 内容保护（最关键）

**【实测】**

| 检查 | 方法 | 结果 |
|------|------|------|
| 公开站 6 首诗正文逐字不变 | 提取 `<div class="poem-verse">` 文本，Phase 2 vs Phase 3 比对 | **6/6 逐字节一致** |
| 诗歌 verse HTML 结构不变 | 比对 `<div class="poem-verse">…</div>` 原样 | **一致** |
| 审阅页 137 篇正文不变 | `git show HEAD:` 与当前 `<div class="poem">` 逐一比对 | **137/137 逐字节一致** |
| 审阅 verbatim 校验 | `tools/author-review/verify_verbatim.py` | **137 检查 / 137 一致 / OK** |
| 内容与配置未被改动 | `git status` 检查 `hugo/content/**`、`hugo.toml`、`hugo/static/**` | **无改动** |

**【说明】** 公开站页面文本相对 Phase 2 确有**新增**，但全部是**界面标签**
（如 `安然 · 作品`、`卷目 · Archive`、月份编号 `09`、`3 篇`），
**不涉及任何诗歌、小传、题记、档案记录的文字**。诗歌正文本身零改动。

---

## 3. URL 兼容性

**【实测】** 用 `git worktree` 在隔离目录构建 Phase 2 与 Phase 3 的**生产**输出，比对全部 HTML 路径：

```
Phase 2 页面: 22    Phase 3 页面: 22
diff → 完全一致（无新增、无删除、无重命名）
```

结论：**本轮零 URL 漂移**。permalink 规则、`/archive/`、`/years/`、`/preface/`、
`/shi-ren-xiao-zhuan/`、`/about/`、`/search/`、`/YYYY/MM/slug/`、`#year-YYYY` 锚点均未变。

---

## 4. 链接完整性

**【实测】** `tools/verify/check_links.py --root <预览构建>`：

```
pages scanned   : 176
internal links  : 1303
runtime /api/   : 2
broken          : 0
```

---

## 5. 生产输出清洁度

**【实测】** `tools/verify/check_production_output.py --root <生产构建>`：

```
PRODUCTION OUTPUT CLEAN: no /review/, no private material; all required pages present
```

- 生产构建**不含** `/review/`，不泄漏任何候选全文。
- 生产页 `robots: index,follow` + `canonical: https://poet.ismaelan.com/...`。
- 预览域 `robots: noindex,nofollow`，且不输出 canonical（防止污染正式站）。

---

## 6. 安全与访问控制（未削弱）

**【实测】** 外部实测（work-2，Phase 3 预览）：

| 请求 | 结果 |
|------|------|
| `/review/`（无令牌） | **401** |
| `/review/poem/C0001.html`（无令牌） | **401** |
| `/api/reviews`（无令牌） | **401** |
| `/api/review/C0001`（错令牌） | **401** |
| `/api/reviews?token=正确令牌` | 303 → 随后带 cookie 200 |
| 带 cookie 后 `/review/` | 200，可见 **137** 个诗歌页 |

**【实测】** 与**未改动的作者原始预览（work-1）**对比：

```
work-1  /review/poem/C0001.html -> 401    work-2 -> 401
work-1  /review/ (无令牌)        -> 401    work-2 -> 401
```

结论：门禁行为与改动前**完全一致**，未因视觉调整而放松。

---

## 7. 布局与响应式（客观实测，非主观）

**【实测】** 用 headless 浏览器测量计算样式与几何：

桌面（1440px）首页：

| 元素 | 实测 |
|------|------|
| 主视觉栅格 | 文字列 551px / 图列 393px（7:5 非对称） |
| 内容块宽度 | 400 / 560 / 400 / 560（交错，非等宽） |
| 主标题字号 | **73.6px**，宋体系 |
| 区块标题 | 24px，左对齐 |
| 年份数字 | 38.4px |
| 页脚 | 黑色 `#0E0E0E` |

诗歌页（1440px）：

| 元素 | 实测 |
|------|------|
| 页头 | 黑色 `#0E0E0E`，通栏 |
| 标题 | 41.6px |
| 正文栏宽 | **608px**（`--measure-poem`），居中 |
| 正文行高 | 39.1px（= 17px × 2.3，与 Phase 2 一致） |

移动端（390px）**横向溢出检查**（9 个页面）：

```
所有页面 scrollWidth - clientWidth = 0px   （无横向滚动）
导航触控高度 = 44px                         （达到目标）
```

---

## 8. 无障碍（对比度实测）

| 前景 / 背景 | 实测比值 | AA |
|-------------|----------|----|
| `#141414` / `#FAF9F7` | **17.51:1** | ✅ |
| `#6B6B6B` / `#FAF9F7` | **5.06:1** | ✅ |
| `#7A2A34` / `#FAF9F7` | **9.04:1** | ✅ |
| `#F2F1EE` / `#0E0E0E` | **17.09:1** | ✅ |
| `#A8A6A2` / `#0E0E0E` | **7.94:1** | ✅ |

保留「跳到正文」跳转链接与语义化地标（header/main/nav/footer）。

---

## 9. 功能回归

**【实测】** 站内搜索（外部同源实测）：

```
载入：已载入 6 条作品索引。
查询「雨」→ 找到 2 条结果。
查询「雪」→ 找到 1 条结果。
```

`#search-input` / `#search-status` / `#search-results` 的 id 与 `search.js`、`/index.json` 均保留。

---

## 10. 未能验证 / 限制

- **【说明】作者随任务书上传的截图未在本环境找到**（已全盘扫描）。本轮参考以
  Tubik 官方案例页与 Dribbble 原稿为依据。若作者持有特定截图，可再提供核对。
- **【说明】** 本环境的视觉「观感」结论以几何/计算样式实测 + 设计规范为准；
  主观美感最终需作者确认。
- **【说明】** 正式域名 `poet.ismaelan.com` 与 Vercel 未做任何操作，未验证其现状。
