# 作者审阅系统（本地）

在现有 137 篇诗歌阅读站 `/review/` 之上，加入**可保存、可回读、可导出**的作者审阅功能。
不引入数据库、不引入第三方服务，只用 Python 标准库。

设计说明见 [`docs/author-review/review-records/DESIGN.md`](../../docs/author-review/review-records/DESIGN.md)。

## 目录

| 路径 | 作用 |
| --- | --- |
| `tools/review/store.py` | 存储层：追加式流水账 + 快照 + 导出 |
| `tools/review/serve_review.py` | 静态预览 + `/api/*` JSON 接口 |
| `tools/review/build_decisions.py` | 由 journal 生成规范台账 `decisions.jsonl` |
| `tools/review/build_review_artifacts.py` | 生成进度摘要 `review-summary.md` 与恢复说明 `recovery-report.md` |
| `tools/review/rebuild_snapshot.py` | 从流水账重建快照与导出（恢复用） |
| `tools/review/backup_review_data.py` | 备份 / 校验 / 恢复审阅数据（独立副本 + SHA256） |
| `tools/review/test_review_system.py` | 端到端验收测试 |
| `docs/author-review/review-records/journal.jsonl` | 权威数据（每次保存追加一行，永不覆盖） |
| `docs/author-review/review-records/decisions.jsonl` | 派生：每候选一行的规范台账（便于审计/备份/导入） |
| `docs/author-review/review-records/snapshot.json` | 派生：每篇当前最新记录 |
| `docs/author-review/review-records/export-review-records.{csv,json}` | 派生：导出文件 |
| `docs/author-review/review-records/review-summary.md` | 进度摘要（无私人意见正文，**已提交**） |
| `docs/author-review/review-records/recovery-report.md` | 持久化与恢复说明（**已提交**） |

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

审阅数据位于工作区的 `docs/author-review/review-records/`。它**能扛住服务重启**，
但**工作区被回收（重新分配容器）后会丢失**，所以必须定期把数据拷到工作区之外。

```bash
# 备份（在**不同文件系统**的目录生成带 SHA256 的独立副本；默认 /home/openhands/...）
python3 tools/review/backup_review_data.py backup --to ~/poet-review-backups/author-review

# 校验一份备份是否完好
python3 tools/review/backup_review_data.py verify ~/poet-review-backups/author-review/<时间戳>

# 恢复（先自动给当前数据做一次安全备份，再从指定副本恢复）
python3 tools/review/backup_review_data.py restore ~/poet-review-backups/author-review/<时间戳> --yes
```

恢复时若校验不通过会**拒绝执行**（除非加 `--force`）。若目标与源在**同一文件系统**，
备份会被**拒绝**（除非显式 `--allow-same-fs`）——同盘副本不算真备份。

## 记录追踪与恢复（沙盒重启后）

每次审阅后重新生成台账与摘要：

```bash
python3 tools/review/build_review_artifacts.py   # 刷新 decisions.jsonl + review-summary.md + recovery-report.md
```

沙盒/工作区被回收后的恢复顺序：

1. **先查 GitHub**：分支与提交是工作成果的正式记录（`git fetch && git branch -r`）。
2. 若存在备份（`~/poet-review-backups/author-review/<时间戳>` 或私有远端），
   先 `verify` 再 `restore`。
3. `python3 tools/review/rebuild_snapshot.py` 由 journal 重放 snapshot。
4. `python3 tools/review/build_review_artifacts.py` 重新生成台账与摘要。
5. `REVIEW_ACCESS_TOKEN=... python3 tools/review/serve_review.py --port 12000` 重新打开审阅页。

完整说明见 [`docs/author-review/review-records/recovery-report.md`](../../docs/author-review/review-records/recovery-report.md)。
**注意**：`journal.jsonl` / `decisions.jsonl` / `snapshot.json` / 导出文件均为私人数据，
**已被 `.gitignore` 忽略，切勿提交到公开仓库**；只有不含意见正文的
`review-summary.md` 与 `recovery-report.md` 会提交。

审阅数据与作品正文、候选 CSV **完全独立**；正式 Hugo 构建不含 `/review/`
（`enableReview=false`），审阅数据不会进入生产站。**本仓库是公开仓库**，
`review-records/` 下的数据文件已在 `.gitignore` 中忽略，**切勿提交**（作者意见属私人内容）。

## 访问控制（预览主机可被他人访问时）

预览接口默认**无鉴权**，任何拿到链接的人都能读写。若预览主机对他人可达，请设置令牌：

```bash
REVIEW_ACCESS_TOKEN=$(python3 -c "import secrets;print(secrets.token_urlsafe(24))") \
  python3 tools/review/serve_review.py --port 12000
```

之后用 `https://<host>/review/?token=<令牌>` 首次打开（会写入 Cookie），
或用 `X-Review-Token` 头访问 API。未带令牌的 `/review/` 与 `/api/*` 一律返回 401。

