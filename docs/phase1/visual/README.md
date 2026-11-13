# POET-VISUAL-REFINEMENT-01 · 视觉优化候选

本目录是「安然诗歌档案」第一阶段**视觉优化候选**的交付材料。
任务性质：**仅候选分支内的视觉设计修改**；不迁移、不合并、不部署正式站。

- 分支：`design/phase1-visual-refinement-2026-11-13`
- 基线：`impl/phase1-candidate-2026-11-12` @ `5573f5c`
- `main` 未改动；PR #12 仍为 draft，未合并。

## 预览地址（实际访问验证通过）

| 用途 | 地址 | 状态 |
| --- | --- | --- |
| 公开阅读（视觉候选） | https://work-2-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/ | 200 |
| 作者审阅（视觉候选，需令牌） | https://work-2-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/review/ | 无令牌 401 / 有效令牌 200 |
| 作者原有预览（未受影响） | https://work-1-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/ | 200 |

审阅入口仍受令牌保护，令牌通过 `?token=…` 引导（返回 303 并写入 Cookie），
或使用 `X-Review-Token` 请求头。**本目录不含令牌明文。**

## 交付文件

| 文件 | 内容 |
| --- | --- |
| `design-notes.md` | 视觉设计说明、配色与字体使用说明、逐页变化 |
| `changes-and-risks.md` | 修改文件清单、影响评估、风险与回滚 |
| `tests-content-functional-security.md` | 内容/功能/安全测试报告 |
| `screenshots/before/` | 优化前截图（22 张） |
| `screenshots/after/` | 优化后截图（22 张） |
| `screenshots/compare/` | 优化前后对照图（22 张） |

## 预览服务恢复（Runtime 重启后）

预览由容器内 Python 进程提供，Pod 重启后需重新启动：

```bash
cd /workspace/audit/poet
export PATH=/workspace/bin:$PATH
python3 tools/preview/build_preview.py --outdir /tmp/visual-preview \
  --baseurl https://work-2-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/
REVIEW_ACCESS_TOKEN="$(cat docs/author-review/private/review-token.txt)" \
  python3 tools/review/serve_review.py --port 12001 --dir /tmp/visual-preview
```

## 边界确认

未修改 `main`；未合并 PR #12；未改动诗歌正文/作者资料/题记/时间记录；
未改动审阅记录与令牌；未改动正式网站、DNS、Vercel；未重做 Jekyll→Hugo 迁移；
未暴露审阅令牌。等待作者与审查方查看预览与截图后另行授权。
