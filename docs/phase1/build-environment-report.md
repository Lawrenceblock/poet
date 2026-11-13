# P1-A · 构建环境与基础设施报告

- 日期：2026-11-12
- 分支：`impl/phase1-candidate-2026-11-12`（基线 `5b423d8`）
- 结论：**构建环境就绪，Hugo 全量构建成功**

## 1. 构建环境（【已验证】）

| 项 | 值 |
| --- | --- |
| Hugo | `v0.168.0-e27a6760c5547237f87d353aebe0580feadb20f4+extended` linux/amd64 |
| 来源 | 官方 GitHub Release `gohugoio/hugo` v0.168.0（`hugo_extended_..._linux-amd64.tar.gz`） |
| 安装路径 | `/workspace/bin/hugo`（已加入 PATH） |
| Python | 3.x（仅标准库，无第三方依赖） |
| 操作系统 | Linux x86_64 |

- 版本与 `FINAL-IMPLEMENTATION-PLAN.md` 要求一致（0.168.0 extended）。**【已验证】**
- 环境原无 Hugo（`which hugo` 为空），本轮安装；**该二进制位于工作区内，工作区回收后需重新安装**。**【已验证】**

## 2. 站点配置核对（【已验证】）

`hugo/hugo.toml`：

- `baseURL = "https://poet.ismaelan.com/"`（正式域名；预览构建用 `--baseURL` 覆盖）。
- `permalink posts = "/:year/:month/:slug/"`（旧博客 305 篇路径 `/YYYY/MM/slug.html` 去 `.html` 后一致）。
- 扁平旧页（`/archive/`、`/preface/`、`/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/shi-ren-xiao-zhuan/`）由各文件 front matter 的显式 `url:` 决定。
- 中文字体：`--serif` 为宋体系列（`Songti SC, SimSun, Noto Serif CJK SC, Source Han Serif SC, Georgia, serif`）。
- 诗歌排版：`.poem-content { line-height: 2.4; text-align: center; }`，`.poem-verse { white-space: pre-wrap; }`。
- `markup.goldmark.typographer = false`（防止智能标点改写诗歌引号/破折号）；`hardWraps = true`（保留换行）；`unsafe = true`（允许诗歌内嵌原始 HTML）。

以上均已核对，未改动排版原则。**【已验证】**

## 3. `/style.css` 兼容（N5）——【已验证：无需修改】

- `hugo/static/style.css` 与旧站 `main:style.css` **逐字节相同**（`diff` 无差异），构建后输出 `public/style.css`（HTTP 200）。
- 旧链接 `/style.css` 保持有效。**结论：N5 不存在遗留缺口，无需修复。**

## 4. favicon（N6）——【已验证：已进入产物】

- `hugo/static/favicon.ico` 存在，构建后 `public/favicon.ico` 存在。
- `head-meta.html` 输出 `<link rel="icon" href="/favicon.ico">`。
- **结论：N6 已满足，无需修复。**

## 5. 发现（本轮新增）

- **Hugo `--cleanDestinationDir` 在 v0.168.0 中不生效**（输出 `Cleaned 0`，陈旧文件仍保留）。因此从“预览输出目录”直接跑 `hugo` 会残留 `/review/`。**【已验证】**
- 处理：正式构建必须从**干净输出目录**开始（Vercel 从干净检出构建，`hugo/public` 已被 `.gitignore` 忽略，天然满足）；并新增 `tools/verify/check_production_output.py` 作为产物守门（见 P1-G）。

## 6. 交付判定

- 构建环境：**就绪**（含一处环境依赖说明）。
- 未解决：Hugo 二进制不在版本控制中（工作区回收需重装）——已列为非阻塞项。
