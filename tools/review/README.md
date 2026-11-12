# 作者审阅系统（本地）

在现有 137 篇诗歌阅读站 `/review/` 之上，加入**可保存、可回读、可导出**的作者审阅功能。
不引入数据库、不引入第三方服务，只用 Python 标准库。

设计说明见 [`docs/author-review/review-records/DESIGN.md`](../../docs/author-review/review-records/DESIGN.md)。

## 目录

| 路径 | 作用 |
| --- | --- |
| `tools/review/store.py` | 存储层：追加式流水账 + 快照 + 导出 |
| `tools/review/serve_review.py` | 静态预览 + `/api/*` JSON 接口 |
| `tools/review/rebuild_snapshot.py` | 从流水账重建快照与导出（恢复用） |
| `tools/review/test_review_system.py` | 端到端验收测试 |
| `docs/author-review/review-records/journal.jsonl` | 权威数据（每次保存追加一行，永不覆盖） |
| `docs/author-review/review-records/snapshot.json` | 派生：每篇当前最新记录 |
| `docs/author-review/review-records/export-review-records.{csv,json}` | 派生：导出文件 |

## 启动（本地预览）

```bash
python3 tools/preview/build_preview.py          # 生成 hugo/public（含 /review/）
python3 tools/review/serve_review.py --port 12000
```

打开 `http://localhost:12000/review/`。

## 界面操作

1. 在总目录点击“阅读/审阅”进入作品页。
2. 填写 ①审阅结论 ②作品性质 ③作者意见，点“保存审阅”。
3. 显示“保存成功 / 上次保存时间（第 N 版）”即为已落盘。
4. 重新打开页面会自动回读已保存内容。
5. 总目录顶部有进度条与“导出 CSV / 导出 JSON”。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/reviews` | 全部记录 + 进度 |
| GET | `/api/review/<id>` | 单条记录 |
| POST | `/api/review` | 保存一条 `{candidate_id,status,nature,comment}` |
| GET | `/api/export.csv` | 下载 CSV |
| GET | `/api/export.json` | 下载 JSON |

枚举：`status` = `pending|keep|hold|exclude`；
`nature` = `unset|single_poem|multi_poem|non_poem|unsure`。
写入只接受合法 `candidate_id` 与合法枚举值，其它一律拒绝。

## 测试与验收

```bash
python3 tools/review/test_review_system.py   # 全流程：保存→回读→更新→进度→导出→失败→隔离
python3 tools/author-review/verify_verbatim.py  # 137 篇逐字一致 + 链接完整
```

测试写入 `journal-test.jsonl`，**不污染**正式数据；测后 `--purge-test` 清理。

## 备份 / 恢复 / 迁移

```bash
# 备份：整个目录都是文本，直接复制或随 Git 提交
cp -r docs/author-review/review-records /path/to/backup

# 恢复：把 journal.jsonl 放回后重建
python3 tools/review/rebuild_snapshot.py
```

审阅数据与作品正文、候选 CSV **完全独立**；正式 Hugo 构建不含 `/review/`
（`enableReview=false`），审阅数据不会进入生产站。
