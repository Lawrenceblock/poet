# 改动清单与风险说明 · POET-VISUAL-REFINEMENT-01

## 一、修改文件清单

分支：`design/phase1-visual-refinement-2026-11-13`（基线 `impl/phase1-candidate-2026-11-12` @ `5573f5c`）

### 1. 手写源码改动（5 个文件）

| 文件 | 改动性质 | 说明 |
| --- | --- | --- |
| `hugo/assets/css/style.css` | 视觉 | 配色改方案 C；字体栈、字号层级、行高、宽度、分隔线、方角化；删除淡蓝与渐变。选择器类名不变 |
| `hugo/layouts/index.html` | 视觉 | 首页「入口」列表：把行内 `— 说明` 改为 `<span class="hint">`，无功能变化 |
| `tools/author-review/build_review_site.py` | 视觉 | 仅替换内联 `PAGE_CSS` 常量。字段、表单、数据结构、API 行为均未触碰 |
| `tools/preview/build_preview.py` | 工具 | 新增可选参数 `--outdir`，默认值不变（`hugo/public`）。用于构建隔离预览 |
| `tools/preview/serve_preview.py` | 工具 | 新增可选参数 `--dir`，默认值不变。用于把静态服务指向隔离预览目录 |

### 2. 生成物（由 `build_review_site.py` 重新生成，非手改）

`docs/author-review/site/` 下 154 个 HTML（12 个批次/索引页 + 137 首诗页 + 5 个旧站页）
因内联样式集中在该文件的 `PAGE_CSS`，重新生成后样式随之更新。

> **关键验证**：对这 154 个文件逐一比对「剥离 `<style>` 块后的内容」与基线，
> **0 个文件正文发生变化**——即诗歌文本与审阅数据字段逐字未变，仅内联 CSS 改变。

### 3. 新增（本报告与截图）

`docs/phase1/visual/`（设计说明、测试报告、截图 `before/` `after/` `compare/`）。

### 4. 未改动（已核验）

- `hugo/content/**`（6 篇样例诗 + archive/years/about/preface/shi-ren-xiao-zhuan/search + tests）— **未改动**
- `docs/author-review/review-records/**`（审阅记录）— **未改动**（`journal.jsonl` SHA-256 仍为 `7f311871…ccb4d`）
- `docs/author-review/private/review-token.txt`（令牌）— **未改动**，仍被 git 忽略
- `hugo/hugo.toml`（permalink / 路由 / 输出格式）— **未改动**
- `hugo/static/**`（封面图、favicon、旧站快照、旧 `style.css`）— **未改动**
- `main` 分支、PR #12、域名、DNS、Vercel — **未触碰**

## 二、是否影响原有功能

**不影响。** 依据见 `tests-content-functional-security.md`：22 条路由全部 200，
搜索索引/JS 正常，审阅权限门禁与 API 行为与基线一致。

## 三、是否影响诗歌正文

**不影响。** 三层证据：

1. 137 篇候选诗逐字校验通过（`tools/author-review/verify_verbatim.py`）。
2. 154 个审阅页「剥离样式后内容」与基线 100% 一致。
3. 渲染后的 `.poem-content` 文本与基线构建逐字节一致（除首页说明块的预期改动）。

## 四、外部资源依赖

**无。** 页面不加载任何第三方字体、脚本、样式或图片 CDN。字体使用系统衬线栈，
搜索为纯前端脚本，封面图为仓库内静态资源。全部请求均指向本站自身。

## 五、预览服务是否依赖当前 Runtime 持续运行

**是。** 预览由 Runtime 容器内的 Python 进程提供：

- 视觉候选预览：`work-2`（端口 12001），由 `tools/review/serve_review.py --dir /tmp/visual-preview` 提供。
- 作者现有预览：`work-1`（端口 12000），未受影响。

若 Runtime Pod 再次重启，进程会消失，需重新执行：

```bash
export PATH=/workspace/bin:$PATH
python3 tools/preview/build_preview.py --outdir /tmp/visual-preview \
  --baseurl https://work-2-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/
REVIEW_ACCESS_TOKEN="$(cat docs/author-review/private/review-token.txt)" \
  python3 tools/review/serve_review.py --port 12001 --dir /tmp/visual-preview
```

## 六、风险与待决问题

| # | 事项 | 级别 | 说明与建议 |
| --- | --- | --- | --- |
| R1 | 辅助灰 `#777777` 对比度 4.48:1，略低于 AA 正文 4.5:1 | 低 | 系任务书指定色值，为忠于配色未擅自改动。如作者同意，改 `#757575` 即达标 |
| R2 | 预览依赖 Runtime 存活，Pod 重启即中断 | 中 | 与既有情况一致，非本次引入；已提供一键恢复命令 |
| R3 | 154 个审阅 HTML 重新生成，diff 较大 | 低 | 内容零变化（已逐文件验证），仅样式集中更新；审阅功能不受影响 |
| R4 | 中文字体在无 `Songti SC`/`SimSun` 的 Linux 环境回退到通用衬线 | 低 | 设计即依赖系统字体栈；作者在 macOS/Windows 上会得到预期宋体 |
| R5 | 首页「入口」条目结构微调（`span.hint`） | 极低 | 纯展示；如不希望，可回退为单行文本 |

## 七、回滚方式

本次全部改动都在独立分支 `design/phase1-visual-refinement-2026-11-13` 上。
`main` 与 `impl/phase1-candidate-2026-11-12` 均未改动。如需放弃：

```bash
git checkout impl/phase1-candidate-2026-11-12   # 回到基线
git branch -D design/phase1-visual-refinement-2026-11-13   # 删除候选分支
```

或直接不合并该分支 / 关闭对应 Draft PR 即可，不影响任何既有成果。
