# 补充修复报告 · 备份完整性校验加固与独立验收准备

- 日期：2026-11-14
- 分支：`review/author-review-records-recovery-2026-11-14`
- 修复前 HEAD：`4bfbfeb`
- 基线：`main` @ `c12d1c4`
- 性质：PR #21 的**补充修复**（独立代码审查发现的校验缺陷）。只改
  `tools/review/` 与相关文档；不修改诗歌正文、审阅业务规则、审阅 API、
  令牌或访问控制；不上传任何私人数据；**不合并 PR、不部署生产环境**。

标记约定：**【事实】**=有直接证据；**【推断】**=由事实推导；**【建议】**=待作者决定。

---

## 1. 修复前发现的问题

### 问题 A（高危，fail-open）：`cmd_verify()` 校验过于宽松，可被“空清单/漏文件”绕过

**【事实】** 修复前的 `cmd_verify()`：

1. **不要求 `manifest.json`**——缺失时只是跳过打印，仍可 `VERIFY OK`。
2. **不检查 `SHA256SUMS.txt` 是否为空**——空文件时循环体不执行，`ok` 保持 `True`，
   直接 `VERIFY OK`。
3. **不做 manifest 与 checksum 清单的一致性核对**——两者可任意不一致。
4. **不检查覆盖完整性**——若某数据文件（如 `journal.jsonl`）不在清单里，即使它
   存在于备份目录，也不会被校验，`decisions.jsonl` 等派生文件却被校验，于是“漏一个
   关键文件”仍能通过。
5. **不校验文件名合法性**——`../` 穿越、绝对路径等异常条目会被当作普通名字拼接。
6. **不拒绝重复条目**。

**【事实·后果】** `cmd_restore()` 原先在 `--force` 下可跳过校验直接覆盖现有记录；
即使不加 `--force`，上述宽松校验也可能对**不完整**的备份返回成功，从而在未真正
验证全部数据的情况下覆盖私人记录。这与本轮 fail-closed 原则直接冲突。

**【事实·已复现（修复前逻辑）】** 清空 `SHA256SUMS.txt` 后 `verify` 仍打印
`VERIFY OK`；删除 `manifest.json` 后 `verify` 仍打印 `VERIFY OK`。

### 问题 B（中危）：`restore` 存在 `--force` 绕过通道

**【事实】** `cmd_restore()` 逻辑为
`if cmd_verify(args) != 0 and not args.force:`——`--force` 可在**校验失败**时继续
覆盖现有记录，属于设计上的 fail-open 通道。

### 问题 C（测试可靠性）：故障注入依赖 `chmod 0555`

**【事实】** 旧测试用 `os.chmod(records_dir, 0o555)` 制造“刷新失败”。在 root
或特权容器下该权限位不生效，可能造成**假阴性/假阳性**（测试结果依赖运行用户与容器权限）。

---

## 2. 修复后实现

全部改动位于 `tools/review/backup_review_data.py`、`tools/review/test_backup_system.py`
与相关文档。

### 2.1 严格、fail-closed 的 `verify_backup(d)`

新增核心函数 `verify_backup()`（`cmd_verify` 与 `cmd_restore` 共用），任一疑问即抛
`BackupInvalid`，**绝不**把不可验证的备份当作有效。逐项：

| 要求 | 实现 |
| --- | --- |
| 1 缺少 `manifest.json` 必须失败 | `_read_manifest()` 首先要求文件存在，否则 `BackupInvalid("missing manifest.json")` |
| 2 缺少 `SHA256SUMS.txt` 必须失败 | `_read_checksums()` 首先要求文件存在 |
| 3 空/格式错误清单必须失败 | 内容 `strip()` 为空 → `BackupInvalid`；逐行要求 `<64位十六进制>` + 双空格 + 名字，否则报错 |
| 4 manifest 与 checksum 文件列表必须严格一致 | `[n for n,_ in entries] != sorted(files)` → 失败 |
| 5 所有数据文件必须被校验 | manifest 的 `files ∪ missing_files` 必须**等于** `DATA_FILES` 全集，否则失败；checksum 必须精确等于 `files` |
| 6 manifest 声明存在的文件必须真实存在 | 逐个 `os.path.isfile()` 检查，缺失 → `BackupInvalid` |
| 7 哈希不匹配必须失败 | 逐文件比对 SHA-256 |
| 8 不允许重复条目 | checksum 与 manifest 各自查重 |
| 9 不允许绝对路径/`..`/异常路径 | `_is_plain_name()`：拒绝含 `/`、`\`、`\x00`、`.`、`..`、空名、以及 `basename != name` 的条目 |
| 10 只允许预定义合法文件名 | 名字必须 ∈ `DATA_FILES` |
| 11 存在未覆盖的数据文件必须失败 | 扫描备份目录，任何 ∈ `DATA_FILES` 但不在 manifest `files` 中的文件 → 失败 |
| 12 空数据集必须有明确合法格式 | 见 2.3 的 `missing_files` 规则 |

**额外加固**：
- 被校验文件若是**符号链接**（`os.path.islink`）→ 失败（防止通过链接指向外部文件）。
- manifest 若声明某文件 `missing`，但该文件**实际存在** → 失败（防止用“声明缺失”掩盖真实文件）。

### 2.2 恢复严格依赖校验结果，且移除绕过

**【事实】** `cmd_restore()` 现在：

- **先**调用 `verify_backup()`；`BackupInvalid` 时打印 `INVALID …` 与
  `refusing to restore from a backup that failed verification` 并 `return 1`，
  **不复制、不重建、不覆盖任何文件**。
- **已移除 `--force`**（连同 argparse 参数），不再存在跳过校验的通道。
- 只复制**校验通过**的文件；对 manifest 声明 `missing` 的文件，**删除目标目录中的同名
  文件**，使恢复结果与备份状态**精确一致**（避免残留旧 journal）。
- 恢复前若目标已有 `journal.jsonl`，仍先做安全备份；安全备份失败即**拒绝覆盖**
  （保持上一轮的 fail-closed 原则）。
- 恢复时若目标存在同名**符号链接**，先 `os.unlink` 再写入，避免跟随链接写到目录外。
- 复制仅使用**预定义文件名**（来自已校验的 manifest），不拼接任意路径，杜绝目录逃逸。

### 2.3 合法空基线的明确规则

**【事实】** manifest 现在显式携带：

```json
{
  "format": "poet-review-backup/2",
  "files":        ["decisions.jsonl", "export-review-records.csv",
                   "export-review-records.json", "snapshot.json"],
  "missing_files": ["journal.jsonl"]
}
```

- `format` 必须等于 `poet-review-backup/2`，否则校验失败（旧格式不被静默接受）。
- **必需文件**（`REQUIRED_FILES`：刷新必产出的 4 个派生文件）**必须**出现在 `files`，
  缺一即失败——空数据集也必须有这 4 个文件。
- **可选文件**（`OPTIONAL_FILES`：`journal.jsonl`，作者尚未保存任何决定时确实不存在）
  必须**显式**列入 `missing_files`；既不列入 `files` 也不列入 `missing_files` 即失败。
- `backup` 端若刷新后**必需文件缺失**，会删除刚建的目录并 `return 1`（fail-closed）。

### 2.4 校验与恢复之间的返回值/异常/退出码

**【事实】** `cmd_verify` 捕获 `BackupInvalid` → 打印 `VERIFY FAILED` → `return 1`；
`cmd_restore` 同样捕获 → `return 1`；`main()` 以 `sys.exit(args.func(args))` 传播，
因此 CLI 退出码与内部结果一致，**不存在“异常被吞后仍返回 0”** 的情况。

---

## 3. 新增与更新的自动化测试

文件：`tools/review/test_backup_system.py`（**全部使用隔离临时目录 + 合成数据，
绝不接触真实作者记录**）。运行命令：

```
python3 tools/review/test_backup_system.py
```

**【事实·实测结果】** `113 PASS / 0 FAIL / 0 SKIP`，退出码 `0`。

功能组：

| # | 场景 | 验证的风险 |
| --- | --- | --- |
| 1 | 正常备份可校验 | 基线正确性 |
| 2 | **mock 注入**刷新异常 → 备份失败、无目录、无私人信息泄漏 | fail-closed 与隐私 |
| 3 | 同文件系统目标被拒 | 假备份防护 |
| 4 | 校验失败的备份 → 恢复被拒且目标不变 | 恢复依赖校验 |
| 5 | 空数据集基线合法（format / missing_files / 137 pending） | 空基线规则 |
| 6 | 恢复到空目录逐项一致 | 恢复完整性 |
| 7 | 私人意见不进公开产物 | 隐私 |
| 8 | 令牌/私人数据不进 gitignore/跟踪文件/diff | 隐私 |
| 9 | 重复备份不覆盖此前备份 | 备份可靠性 |
| 10 | **mock 注入**安全备份失败 → 拒绝覆盖 | 恢复 fail-closed |
| 11 | 多次备份↔恢复一致 | 一致性 |

严格校验组（**每组都同时断言 `verify` 失败、错误信息命中、`restore` 被拒、目标目录
逐文件哈希不变**）：

| # | 篡改 | 期望 |
| --- | --- | --- |
| 12 | 清空 `SHA256SUMS.txt` | 失败（empty） |
| 13 | 清单漏 `journal.jsonl` | 失败（does not match） |
| 14 | manifest 与清单不一致 | 失败（does not match） |
| 15 | 删除 `manifest.json` | 失败（missing manifest.json） |
| 16 | 删除 `SHA256SUMS.txt` | 失败（missing SHA256SUMS.txt） |
| 17 | 删除某数据文件 | 失败（missing data file） |
| 18 | 修改文件内容 | 失败（checksum mismatch） |
| 19 | 重复条目 | 失败（duplicate） |
| 20 | `../` 路径穿越 | 失败（unsafe file name） |
| 21 | 绝对路径 | 失败（unsafe file name） |
| 22 | 声明 missing 但文件存在 | 失败（declared missing） |
| 23 | 数据文件被替换为符号链接 | 失败（symlink） |
| 24 | 清单含未知/非法文件名 | 失败（does not match） |
| 25 | **正向对照**：合法备份成功覆盖恢复 | 恢复确实可用 |

**【事实】** 测试中**未使用任何真实私人数据**（全部为合成 `C####` 记录与随机
`PRIVATE-<uuid>` 哨兵串，且仅存在于临时目录）。故障注入改为 **mock/`lambda` 抛异常**
（测试 2、10），**不再依赖 `chmod` 或 root 权限**。

---

## 4. 回归测试结果

**【事实·实测】**

```
python3 tools/review/test_backup_system.py     -> OK: all backup-system tests passed (113 PASS / 0 FAIL)
python3 tools/review/test_review_system.py     -> OK: all review-system tests passed (15 组)
python3 tools/author-review/verify_verbatim.py -> verbatim-identical : 137 / OK: all checks passed
```

---

## 5. Git 安全检查结果

**【事实】** 见本任务最终报告；要点：`git status` 无私人数据进入暂存/提交；
`.gitignore` 仍忽略全部私人数据文件；`git diff --check` 无空白错误；
`git diff --stat` 仅涉及上述文件。

---

## 6. 部署状态（准确区分）

- **Production Deployment**：**未部署生产环境**。本分支未合并、未触发生产部署。
- **GitHub PR Preview（Vercel 自动）**：PR #21 的 head 提交上，Vercel 的
  **PR Preview** 部署状态为 **success**（`Vercel` / `Vercel Preview Comments`）。
  **这不代表生产环境已经部署，也不代表生产环境已被修改。**

> 准确表述：**未部署生产环境；Vercel 已自动生成 PR Preview，预览部署状态成功。**

---

## 7. 尚未解决的问题与风险

1. **旧记录仍不可找回**：本沙盒内不可恢复；唯一途径是平台侧旧卷快照
   （见 `2026-11-14-platform-admin-inquiry.md`）。
2. **真正的异地备份仍未落地**：不同文件系统 ≠ 异地；同一容器/主机的多份备份可能
   随整机灾难一起丢失。需作者提供一个**私有**存储位置并做**上传前加密**
   （见 `2026-11-14-offsite-backup-plan.md`）。**本轮未上传任何数据。**
3. **备份格式升级**：manifest 现为 `poet-review-backup/2`。若存在更早格式的历史备份，
   需按新规则重新生成（本仓库无已提交的旧格式备份，故无迁移负担）。
