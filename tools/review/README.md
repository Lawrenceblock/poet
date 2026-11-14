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

**备份是 fail-closed 的**：备份前会先从权威 `journal.jsonl` 刷新
`snapshot` / `decisions` / 导出文件；**只要刷新失败就立即中止、返回非零、不写任何
备份**，绝不把过期或残缺的派生文件当成成功备份。

**校验是严格、fail-closed 的**（`verify_backup`）：必须有 `manifest.json` 与
`SHA256SUMS.txt`；清单**非空、格式正确、无重复**；manifest 与清单**逐文件严格一致**，
且二者的“存在 + 声明缺失”必须**恰好覆盖全部数据文件**；只接受**预定义文件名**
（拒绝绝对路径、`../` 穿越、非法名、符号链接）；文件缺失或哈希不符即失败。

若目标与源在**同一文件系统**，备份会被**拒绝**（除非显式 `--allow-same-fs`）。
目标若位于记录目录**内部**也会被拒绝。恢复**必须先通过校验**，**没有跳过校验的
开关**（已移除 `--force`）；恢复前若无法为现有记录做安全备份，也会**拒绝覆盖**。

**journal 缺失绝不当作空数据**：若 `journal.jsonl` 不存在，但任一派生文件
（`snapshot.json` / `decisions.jsonl` / 导出文件）仍然存在，说明处于**异常状态**
（journal 丢失、派生数据仍在）。此时 `backup` 与 `restore` 都会**在写入任何东西之前
拒绝**（不刷新、不重建、不覆盖、不创建目录），返回非零并提示需人工检查。
只有 journal **与全部派生文件都不存在**时，才允许建立合法空基线。

**journal 必须是真正的普通文件**：`journal.jsonl` 若为**符号链接**（即使指向真实文件、
或为断裂链接）、**目录**、**FIFO**、**套接字**或**设备文件**，一律视为**异常**，
`backup` 与 `restore` 都会**拒绝**（非零退出、不刷新、不重建、不覆盖、不删除链接、
不新建 journal）。判断使用 `os.lstat()`（**不跟随符号链接**），
**绝不**用 `os.path.exists()` / `os.path.isfile()`（它们会跟随链接而误判）。
**零字节的普通文件是合法 journal**，不受影响；**不使用文件大小**做判断。

> ⚠️ **"不同文件系统" ≠ "异地"**。本沙盒里记录在 `/workspace`（ext4 挂载），
> 默认备份目录 `/home/openhands/...` 在容器 overlay 上，二者**确属不同文件系统**，
> 但**仍在同一个容器内**。**整个沙盒被回收时，两者会一起丢失。**
> 只有把备份**送出这台机器**（私有 Git 仓库或对象存储）才真正抵御沙盒回收。
> 不要把本地另一个目录称作"异地备份"。

## 记录追踪与恢复（沙盒重启后）

每次审阅后重新生成台账与摘要：

```bash
python3 tools/review/build_review_artifacts.py   # 刷新 decisions.jsonl + review-summary.md + recovery-report.md
```

沙盒/工作区被回收后的恢复顺序：

1. **先查 GitHub**：分支与提交是工作成果的正式记录（`git fetch && git branch -r`）。
2. 若存在备份（`~/poet-review-backups/author-review/<时间戳>` 或**私有远端**），
   先 `verify` 再 `restore`。注意本地默认目录与沙盒同容器，只能扛住工作区回收、
   扛不住整沙盒回收；真正依赖的是私有远端副本。
3. `python3 tools/review/rebuild_snapshot.py` 由 journal 重放 snapshot。
4. `python3 tools/review/build_review_artifacts.py` 重新生成台账与摘要。
5. `REVIEW_ACCESS_TOKEN=... python3 tools/review/serve_review.py --port 12000` 重新打开审阅页。

完整说明见 [`docs/author-review/review-records/recovery-report.md`](../../docs/author-review/review-records/recovery-report.md)。
**注意**：`journal.jsonl` / `decisions.jsonl` / `snapshot.json` / 导出文件均为私人数据，
**已被 `.gitignore` 忽略，切勿提交到公开仓库**；只有不含意见正文的
`review-summary.md` 与 `recovery-report.md` 会提交。

## 测试

```bash
python3 tools/review/test_backup_system.py   # 备份/恢复/严格校验/隐私：113 断言，全部用隔离临时目录
```

**备份格式**：`manifest.json` 带 `format` 标签与 `missing_files` 声明；必需文件
（4 个派生文件）必须存在，可选文件（`journal.jsonl`）若不存在必须**显式声明**。
详见 [`docs/author-review/2026-11-14-backup-verify-hardening.md`](../../docs/author-review/2026-11-14-backup-verify-hardening.md)。

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

