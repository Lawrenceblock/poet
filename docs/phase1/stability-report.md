# P1-F · 候选站稳定性报告

- 日期：2026-11-12
- 结论：**候选站稳定，无断链、无 404；`/review/` 采用原子替换，重建期间不出现瞬时 404；生产构建不会泄露 `/review/`**

## 1. 独立可访问性（【已验证】）

- 临时域名：`https://work-1-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/`
- 站点 0.0.0.0 监听，经该域名外部可达；非仅 `127.0.0.1`。
- 公开页实测：`/`、`/archive/`、`/preface/`、`/search/`、`/about/` 均 200。

## 2. 断链检查（【已验证】）

新增 `tools/verify/check_links.py`，扫描构建产物中**每个** HTML 的内部 `href/src`：

| 产物 | 扫描页面 | 内部链接 | 断链 |
| --- | --- | --- | --- |
| 预览树（含 `/review/`） | 176 | 795 | **0** |
| 正式树（无 `/review/`） | 22 | 209 | **0** |

> 注：`/review/api/export.csv`、`/review/api/export.json` 为运行时 API，非静态文件，检查器按运行时端点处理（实测 HTTP 200）。

## 3. 重建期无瞬时 404（【已验证】）

- `/review/` 同步采用 **临时文件 + `os.replace` 原子替换**，并在新文件就位后才清理陈旧文件（`tools/preview/build_preview.py`）。
- 压力测试：连续 3 次并发重建期间，对 `/`、`/archive/`、`/review/`、`/review/poem/C0002.html`、`/style.css`、`/search/` 轮询共 **204 次请求，非 200 = 0**。

## 4. 生产构建不泄露 `/review/`（【已验证】）

- 发现：**Hugo v0.168.0 的 `--cleanDestinationDir` 不生效**（输出 `Cleaned 0`，陈旧文件仍保留）。因此从“上一次预览产物目录”直接跑 `hugo` 会残留 `/review/`。
- 处理：
  1. 正式构建必须从**干净输出目录**开始。Vercel 从干净检出构建，`hugo/public` 已被 `.gitignore` 忽略，天然满足。
  2. 新增 `tools/verify/check_production_output.py`：若产物中出现 `/review/`、`docs/`、`work/`、`private/` 或任何含 `author-review` 标记的文件，**直接失败**；并校验必需页面（`index.html`、`archive/`、`preface/`、`na-la-ti/`、`qing-chun-de-wu-yu/`、`shi-ren-xiao-zhuan/`、`style.css`、`sitemap.xml`、`robots.txt`、`404.html`）齐备。
- 实测：构造“脏产物”时守门脚本返回失败并列出问题；干净构建返回通过。

## 5. 服务端加固（见 P1-D）

- 令牌门禁覆盖 GET/HEAD/OPTIONS；日志不落令牌；`?token=` 一次性后重定向剥离。

## 6. 边界声明

- 未改动任何部署配置或线上站点；仅新增只读校验脚本与预览构建的原子替换逻辑。**【已验证】**
