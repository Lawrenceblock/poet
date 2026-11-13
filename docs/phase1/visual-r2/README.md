# POET-VISUAL-REFINEMENT-02 · 第二轮视觉设计候选

本目录是「安然诗歌档案」第二阶段**视觉设计候选**（第二轮）的交付材料。
任务性质：**仅候选分支内的整页视觉重构**；不迁移、不合并、不部署正式站。

- 任务书：安然诗歌档案网站第二轮视觉设计任务书（黑色骨架、白色空间、暗红细节）
- 分支：`design/phase2-black-white-composition-2026-11-13`
- 基线：`design/phase1-visual-refinement-2026-11-13` @ `b73178c`（第一轮成果）
- 上级基线：`impl/phase1-candidate-2026-11-12` @ `5573f5c`（PR #12，draft）
- `main` 未改动；PR #12、PR #13 均保持 draft、未合并。

## 本轮目标（来自任务书）

第一轮已把蓝色主题改为白色主题（方案 C），但作者反馈：

1. 仍过于依赖「白底 + 灰色细线」，缺乏块面力量；
2. 需要更强的**黑 / 白块面对比**；
3. 希望有「现代文学期刊 + 个人档案」的质感；
4. 这是**整页构图优化**，不只是换色。

本轮据此建立**黑色骨架**：黑色页眉、黑色主视觉、黑色栏目标题条、黑色页脚，
把白色空间留给诗歌正文与条目，形成「黑—白—黑—白」的阅读节奏。

## 预览地址（实际访问验证通过）

| 用途 | 地址 | 状态 |
| --- | --- | --- |
| 第二轮候选（公开阅读） | https://work-2-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/ | 200 |
| 第二轮候选（作者审阅，需令牌） | https://work-2-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/review/ | 无令牌 401 / 有效令牌 200 |
| 作者原有预览（未受影响） | https://work-1-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/ | 200 |

> 说明：本轮把**第一轮预览所在端口（work-2 / 12001）**重新指向第二轮候选，
> 以便作者在同一个地址看到最新版本。第一轮成果完整保存在 git（分支 + 提交）与
> 截图中，未丢失。作者原有预览（work-1 / 12000）**始终未改动**。

审阅入口仍受令牌保护：`?token=…` 引导（返回 303 并写入 Cookie），或 `X-Review-Token` 请求头。
**本目录不含令牌明文。**

## 交付文件

| 文件 | 内容 |
| --- | --- |
| `design-implementation-note.md` | 实施前的现状审查与设计规范（配色、结构、逐页处理） |
| `design-notes.md` | 本轮视觉设计说明与逐页变化 |
| `changes-and-risks.md` | 修改文件清单、影响评估、风险与回滚 |
| `tests-content-functional-security.md` | 内容 / 功能 / 安全测试报告 |
| `screenshots/round1/` | 第一轮基线截图（18 张：9 页 × 桌面/移动） |
| `screenshots/round2/` | 第二轮候选截图（18 张） |
| `screenshots/compare/` | 第一轮 ↔ 第二轮对照图（18 张） |

## 预览服务恢复（Runtime 重启后）

预览由容器内 Python 进程提供，Pod 重启后需重新启动：

```bash
cd /workspace/audit/poet
export PATH=/workspace/bin:$PATH

# 构建第二轮候选产物
python3 tools/preview/build_preview.py --outdir /tmp/visual-preview-r2 \
  --baseurl https://work-2-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/

# 启动预览服务（作者可见端口）
REVIEW_ACCESS_TOKEN="$(cat docs/author-review/private/review-token.txt)" \
  python3 tools/review/serve_review.py --port 12001 --dir /tmp/visual-preview-r2
```

## 边界声明

- 未改动 `hugo/content/**`、`hugo/hugo.toml`、`hugo/static/**`。
- 未改动作者资料、审阅记录、令牌、API、URL/路由。
- 未改动 `main`；未合并 PR #12 / #13；未部署正式站。
- 作者原有预览（work-1 / 12000）与 bio.ismaelan.com 均未触碰。
