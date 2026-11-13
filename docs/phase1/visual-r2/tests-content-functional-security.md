# 第二轮视觉设计 · 内容 / 功能 / 安全测试报告（POET-VISUAL-REFINEMENT-02）

基线：`design/phase1-visual-refinement-2026-11-13` @ `b73178c`。
分支：`design/phase2-black-white-composition-2026-11-13`。
被测产物：`/tmp/visual-preview-r2`（Hugo 构建 + 审阅页），服务端口 12001。

## A. 内容逐字保护

| 检查 | 方法 | 结果 |
| --- | --- | --- |
| 137 篇候选逐字一致 | `tools/author-review/verify_verbatim.py` | **137/137 一致，全部通过** |
| 审阅页正文未变 | 154 个 HTML 去除 `<style>` + 页眉 + 页脚后逐字节比较 | **0 处差异** |
| 审阅页 `<div class="poem">` 正文 | 与基线逐字节比较 | **0 处差异** |
| 已渲染诗歌正文 | 6 个诗歌页 `poem-content` 与第一轮构建比较 | **0 处差异** |
| `hugo/content/**` | `git diff b73178c` | **UNCHANGED** |
| `hugo/hugo.toml` | `git diff b73178c` | **UNCHANGED** |
| `hugo/static/**`（含 `/legacy/` 历史存档） | `git diff b73178c` | **UNCHANGED** |

结论：**诗歌、题记、小传等文学内容逐字不变**；本轮仅改样式与页眉/页脚结构。

## B. 功能

25/25 路由返回 200：

```
/  /archive/  /years/  /preface/  /shi-ren-xiao-zhuan/  /about/  /search/  /legacy/
/404.html  /index.xml  /sitemap.xml  /robots.txt  /index.json  /style.css  /js/search.js
/assets/img/cover.png
/2026/11/demo-snow-2026/  /2008/03/demo-letter-unsent/  /2019/06/demo-the-quiet-room/
/2026/04/demo-three-short-songs/  /2008/10/demo-star-herder/  /2026/09/demo-rain-at-nalati/
/review/  /review/poem/C0001.html  /review/oldsite/
```

- URL / 路由与第一轮完全一致（未触碰 permalink、content 路径、配置）。
- 站内链接（页眉导航、页脚、返回卷目、年份跳转）均指向有效路由。

## C. 安全

| 探测 | 结果 |
| --- | --- |
| `/review/` 无令牌 | 401 |
| `/review/` 错误令牌 | 401 |
| `/review/` 空令牌 | 401 |
| `/review/` 有效令牌 | 200 |
| `HEAD /review/` 无令牌 / 有效令牌 | 401 / 200 |
| `/review/poem/C0001.html` 无令牌 | 401 |
| `/review/oldsite/` 无令牌 | 401 |
| `/review/api/reviews` 无令牌 / POST | 401 / 401 |
| `/review/?token=…` 引导 | 303（写入 Cookie） |

**4/4 认证探测正确。**

令牌泄漏扫描（全部 0 = 干净）：

- 预览产物 `/tmp/visual-preview-r2`：**0**
- 预览服务访问日志：**0**
- 全部 54 张截图（`round1` + `round2` + `compare`）：**0**

## D. 审阅数据完整性

- `docs/author-review/review-records/journal.jsonl` SHA-256 前缀：
  `7f311871818e8b15a496…`（与第一轮**一致，未变**）。
- `docs/author-review/review-records/**`、`docs/author-review/private/**`：`git diff` 为 **UNCHANGED**。
- `/review/api/reviews` 返回记录数：19（与第一轮一致）。

## E. 视觉验证（像素采样）

对第二轮截图做 40×60 网格采样，统计纯黑（亮度 <60）与纯白（>225）占比。
用于验证「黑色骨架、白色空间」的结构节奏确实建立：

| 页面 | 黑色占比 | 白色占比 |
| --- | --- | --- |
| 01-home-desktop | 42.3% | 56.4% |
| 01-home-mobile | 42.7% | 52.3% |
| 02-poem-desktop | 33.2% | 66.4% |
| 02-poem-mobile | 49.9% | 48.2% |
| 03-archive-desktop | 41.6% | 58.1% |
| 04-years-desktop | 38.2% | 61.3% |
| 05-about-desktop | 16.7% | 80.9% |
| 06-bio-desktop | 49.7% | 48.0% |
| 07-search-desktop | 54.4% | 44.9% |
| 08-review-desktop | 3.4% | 90.7% |
| 09-legacy-desktop | 0.5% | 98.7% |

垂直亮度剖面（首页桌面端）确认「黑—白—黑」节奏：

```
y 0–18%   黑色   页眉 + 主视觉
y 20–78%  白色   内容（被黑色栏目标题条切分）
y 83–95%  黑色   页脚
```

说明：
- `/legacy/`（09）几乎全白/浅色，属**正常**——它是旧站只读快照，
  保留原始蓝色 `#dceef2` 外观，**有意不套用新版黑色骨架**（历史存档须逐字节保持）。
- `/review/`（08）黑色占比低，因审阅页以表单与诗歌副本为主，仅页眉/页脚为黑色。

## F. 可访问性（对比度）

| 组合 | 对比度 | 判定 |
| --- | --- | --- |
| 白字 `#FFFFFF` / 黑底 `#171717` | 17.93:1 | AAA |
| 浅灰 `#A0A0A0` / 黑底 | 6.86:1 | AA |
| 暗红衍生 `#CB6E77` / 黑底 | 5.15:1 | AA |
| 辅助灰 `#757575` / 白底 | 4.61:1 | AA |
| 暗红 `#762B35` / 白底 | 9.69:1 | AAA |
| 正文 `#242424` / 白底 | 15.52:1 | AAA |

第一轮报告中「待确认」的辅助灰 `#777777`（4.48:1，未达 AA）本轮已调整为
`#757575`（4.61:1，达 AA）。

## G. 移动端

- 320 / 360 / 414px 三档宽度检查：页眉无横向溢出，导航居中换行不重叠。
- 主视觉、栏目标题条、页脚在移动端均正确堆叠。

## H. 边界遵守

- 未改动 `main`（仍为 `ee94501`）。
- 未合并 PR #12 / #13。
- 未部署正式站，未改 DNS / 域名 / Vercel。
- 作者原有预览（work-1 / 12000）与 bio.ismaelan.com 未触碰。
- 未改动任何文学内容、审阅数据、令牌或 API。
