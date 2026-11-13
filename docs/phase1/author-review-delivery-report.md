# P1-H · 作者审阅交付报告

- 日期：2026-11-12
- 结论：**候选站已上线可访问，作者审阅系统可安全使用，数据持久且可导出**

## 1. 候选站访问方式（【已验证】）

| 入口 | URL | 令牌 |
| --- | --- | --- |
| 公开阅读（首页） | `https://work-1-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/` | 不需要 |
| 作者审阅 | `https://work-1-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/review/` | **需要令牌** |
| 导出 CSV | `/review/api/export.csv` | 需要令牌 |
| 导出 JSON | `/review/api/export.json` | 需要令牌 |

- 审阅令牌**不在本报告中明文出现**；存放位置见 P1-E。
- 打开方式：`/review/?token=<令牌>` 首次进入后自动重定向并写入 Cookie，之后无需再带令牌。

## 2. 作者如何浏览与审阅（【已验证】）

1. 打开 `/review/`，顶部进度条显示整体审阅进度（含已审阅数量）。
2. 列表按 A/B/C/D 分类分批；每篇显示候选编号、标题、日期、语言、脚本分类。
3. 点“阅读/审阅”进入单篇：上方为**逐字保留的原文**与原始来源链接，下方为审阅表单。
4. 表单三项：① 审阅结论（待审阅/保留/暂缓/排除）② 作品性质（一首诗/多首诗/非诗/尚不确定）③ 作者意见（≤20000 字）。
5. 点“保存审阅”写入；刷新不丢草稿，**只有“已保存”才算正式记录**。
6. 顶部可**导出 CSV / JSON**，供作者留档或提交变更。

## 3. 审阅状态与进度（【已验证】）

- 当前真实记录：`journal.jsonl`，**23 行 / 19 条唯一候选**（其余为修订记录）。
- 候选总数 137；已审阅 19；待审阅 118。
- 真实数据 SHA-256：`7f311871818e8b15a49654171f4ea20de726cc5879f513f1a257f5f5cb7ccb4d`（全程未变）。

## 4. 数据持久化与导出（【已验证】）

- 记录持久化于 JSONL 日志（追加 + 重放最新态）；有 `snapshot.json` 快照。
- 跨文件系统独立备份与还原演练见 P1-E。
- 导出 CSV/JSON 与前端展示一致（字段：candidate_id/title/published/category/status/nature/comment/reviewer/updated_at/rev/reviewed）。

## 5. 清单交付（【已验证】）

- 公开：`docs/author-review/phase1/candidate-list.md`（137 条）、`to-confirm.md`（待作者确认项）。
- 私有（git-ignore）：`docs/author-review/private/review-status.md`（含作者意见）。

## 6. 交付判定

- **候选站：已交付且稳定**（稳定性见 P1-F）。
- **审阅系统：可安全使用**（安全见 P1-D）。
- 未解决：异地/云端持久备份（见 P1-E，非阻塞）；标题实体转义瑕疵（见 P1-C，1 篇）。

## 7. 边界声明

- 未将 `/review/` 内容发布到正式站点；未修改任何诗歌、作者小传或题记。**【已验证】**
- 未修改 `main` 分支、域名、DNS 或 Vercel。**【已验证】**
