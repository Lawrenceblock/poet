# 第二轮安全审查报告 · 审阅记录备份与 PR #21 加固

- 日期：2026-11-14
- 分支：`review/author-review-records-recovery-2026-11-14`
- 审查前 HEAD：`4341376`
- 基线：`main` @ `c12d1c4`
- 性质：对 PR #21 的**第二轮安全审查**。修复备份可靠性缺陷、补充自动化测试、
  修正误导性文档，并为**私有异地备份**做准备。不修改诗歌正文、审阅 API、
  令牌机制或访问控制；不触碰 `main`；不上传任何私人数据。

标记约定：**【事实】**=有直接证据；**【推断】**=由事实推导；**【建议】**=待作者决定。

---

## 1. 发现的问题

### 问题 1（高危）：派生文件刷新失败时，备份**错误地继续并报告成功**

**【事实】** `cmd_backup()` 中刷新派生文件的代码为
`try: store.rebuild(); build_decisions.write() except Exception: print(warning)`。
异常只打印警告后**继续**执行，随后仍打印 `backup written` 并 `return 0`。

**【事实·已复现】** 将记录目录设为只读后运行备份：

```
warning: could not refresh derived records: [Errno 13] Permission denied ...
backup written: .../20261114-094223
  files        : journal.jsonl, decisions.jsonl
EXIT=0
```

结果：备份**成功退出（0）**，但其中的 `decisions.jsonl` 是**过期内容**
（journal 已 `keep`，备份里仍是 `pending`）。**风险**：作者可能把一个过时/残缺的
备份当成有效备份，从而在真正的恢复场景中丢失决定。

### 问题 2（中危）：同一秒内第二次备份会**覆盖**上一次有效备份

**【事实·已复现】** 备份目录名只用秒级时间戳
`YYYYMMDD-HHMMSS`，`os.makedirs(dest, exist_ok=True)`。同一秒内再次备份会**写进同一目录**，
覆盖已有文件。

```
第一次备份 -> 目录 .../094305
第二次备份（同一秒） -> dirs now: 1
MARKER-KEEP.txt: GONE
journal.jsonl: （已被新内容覆盖）
```

**风险**：一次误操作或脚本连跑两次，会静默摧毁上一份有效备份。

### 问题 3（中危）：`restore` 不重新生成 `decisions.jsonl`，且安全备份失败仍继续覆盖

**【事实】** `cmd_restore()` 只调用 `store.rebuild()`（重建 snapshot + 导出），
**没有**调用 `build_decisions.write()`，恢复后 `decisions.jsonl` 可能是旧的。
**【事实】** 恢复前为现有记录做的“安全备份”返回值被忽略；即使安全备份失败
（例如目标同盘被拒），恢复仍会继续覆盖现有权威记录。

### 问题 4（低危）：独立备份判断在“目标路径未知”时**静默放行（fail-open）**

**【事实】** 原代码 `probe = dest_root if exists else dirname(dest_root)`，
且整个判断包在 `try/except OSError: pass` 里。当目标与父目录都不存在、
或权限导致无法 `stat` 时，异常被吞掉，**不做任何检查就继续备份**。

### 问题 5（文档，误导性）：把本地“不同文件系统”描述成可抵御容器回收

**【事实】** README 与生成的 `recovery-report.md` 写“在**不同文件系统**的目录生成
带 SHA256 的独立副本”，并暗示能抵御沙盒回收。**本沙盒实测**：

| 路径 | 设备号 | 挂载 |
| --- | --- | --- |
| 记录 `docs/author-review/review-records/` | 66309 | `/workspace`（ext4，`/dev/nvme0n2`） |
| 默认备份 `/home/openhands/poet-review-backups/` | 240 | 容器 overlay（`/`） |

**【事实】** 二者**确属不同文件系统**（设备号不同），但**同处一个容器**。
因此该备份**只能扛住工作区回收，扛不住整沙盒回收**。原措辞会让作者高估其保护力。

---

## 2. 实际修复内容

全部改动仅在 `tools/review/` 与文档内，未触及诗歌正文、候选 CSV、审阅 API、
访问控制或令牌机制。

| 问题 | 修复 | 位置 |
| --- | --- | --- |
| 1 高危 | 刷新改为 **fail-closed**：异常即打印 `ERROR … fail-closed` 并 `return 1`，**不写任何备份**；错误信息不含私人意见 | `backup_review_data.py::cmd_backup` |
| 2 中危 | 备份目录名**防碰撞**：`_unique_dest()` 在时间戳后追加 `-2`、`-3`…，**绝不覆盖已有备份** | 同上 |
| 3 中危 | `restore` 后调用 `build_decisions.write()` 重建台账；恢复前的安全备份改为**检查返回值**，失败即 `return 1`，**拒绝覆盖** | `cmd_restore` |
| 4 低危 | 新增 `_probe_dev()`：沿父链找**最近存在祖先**的 `st_dev`；无法判定则**拒绝**（fail-closed）；`stat` 出错也**拒绝** | `_probe_dev` / `cmd_backup` |
| 附加 | 拒绝把备份目录建在**记录目录内部**（否则会被一并纳入记录） | `cmd_backup` |
| 5 文档 | README、生成的 `recovery-report.md`、工具 docstring 与默认路径注释，全部改为**如实说明**“不同文件系统 ≠ 异地，同容器仍会一起丢失” | `README.md`、`build_review_artifacts.py`、`backup_review_data.py` |

**未改动且经确认无需改动**：
- 审阅 API、`store.py` 的保存/回放逻辑、令牌门禁、`serve_review.py`——第二轮审查未发现严重安全问题，按要求**不扩大修改范围**。
- `.gitignore` 的私人数据忽略规则——经测试确认仍然有效（见第 4 节）。

---

## 3. 测试结果

新增 `tools/review/test_backup_system.py`（纯标准库，**全部使用隔离临时目录与
合成数据，绝不触碰真实作者记录**）。运行：

```
python3 tools/review/test_backup_system.py
OK: all backup-system tests passed
```

覆盖任务要求的全部场景：

| # | 场景 | 结果 |
| --- | --- | --- |
| 1 | 正常备份成功且可校验 | PASS |
| 2 | 派生文件刷新失败 → 备份失败（非零、无备份、无私人信息泄漏） | PASS |
| 3 | 同一文件系统目标被拒绝 | PASS |
| 4 | 备份校验失败时恢复被拒绝，且目标记录不变 | PASS |
| 5 | 空数据集可建立基线备份（137 行 pending） | PASS |
| 6 | 恢复后逐项校验（journal/snapshot/decisions/导出）一致 | PASS |
| 7 | 私人意见不进入公开产物（summary/report/预览构建产物） | PASS |
| 8 | 令牌/私人数据不进入 gitignore、被跟踪文件、工作区 diff | PASS |
| 9 | 重复备份不覆盖此前有效备份 | PASS |
| 10 | 覆盖已有记录时，安全备份失败则拒绝恢复，现有记录不变 | PASS |
| 11 | 多次备份↔恢复循环保持一致 | PASS |

回归（确认未破坏既有系统）：

```
python3 tools/review/test_review_system.py   -> OK: all review-system tests passed (15 组)
python3 tools/author-review/verify_verbatim.py -> 137/137 逐字一致
```

---

## 4. 隐私与安全检查结果

**【事实】**
- `journal.jsonl` / `journal-test.jsonl` / `snapshot.json` / `decisions.jsonl` /
  `export-review-records.{csv,json}` 经 `git check-ignore` 确认**全部仍被忽略**。
- 被 Git 跟踪的文件中**没有任何**私人数据文件；`test_backup_system.py` 的测试
  #8 会扫描全部被跟踪文件，确认**无硬编码令牌**、**无合成私密串**。
- 备份/恢复**失败信息不含**作者意见或令牌（测试 #2 断言）。
- 构建产物：预览构建目录中**未发现**合成私密串（测试 #7）。
- 生成的公开文档 `review-summary.md` / `recovery-report.md` **不含任何作者意见正文**。
- 本轮**未上传**任何私人数据到任何远端；**未**新建仓库/对象存储。

---

## 5. 异地备份方案推荐

详见 [`docs/author-review/2026-11-14-offsite-backup-plan.md`](2026-11-14-offsite-backup-plan.md)。
**结论（【建议】）**：推荐 **A. 私有 Git 仓库 + 加密**（若作者已有一个私有仓库）
或 **B. 对象存储 + 加密**（若作者更希望零仓库维护）。两者都能抵御整沙盒回收、
支持历史版本、可用 `SHA256SUMS.txt` 校验完整性。**本轮不上传任何数据**，
需要作者确认唯一必要事项：**提供一个作者信任的私有存储位置**。

---

## 6. 是否需要作者提供信息

1. **唯一必需**：一个作者信任的**私有**存储位置（私有仓库 URL，或对象存储
   bucket + 凭据），用于异地备份。**在得到确认前不会上传任何数据。**
2. **可选**：是否希望我准备平台管理员咨询文本（见第 7 节），询问旧沙盒是否
   留有可恢复的历史卷快照。

---

## 7. 当前 PR 是否可以进入最终验收

**【事实】** 全部测试通过；备份刷新失败**明确失败**（非零、无假成功）；私人数据
未进入公开仓库；`main` 无任何改动；PR 仍为 Draft；无未经授权的远端上传；
未修改诗歌内容或审阅结果。

**【建议】** 代码与文档层面**已具备进入最终验收的条件**；但**功能完整性**仍取决于
作者决定的两件事：(a) 是否提供私有异地备份目标；(b) 是否推进“保留→正式作品集”。
在作者给出结论前，**保持 Draft，不合并**。
