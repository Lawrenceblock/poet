# 作者审核记录 · 追踪、抢救与持久化修复报告

- 日期：2026-11-14
- 任务：OpenHands 总任务书 · 诗歌新站作者审核记录追踪、抢救与持久化修复
- 性质：**只读调查 + 持久化机制修复**。不修改任何诗歌正文、作者小传、题记、
  既有审阅 API 或访问控制；不触碰 `main`、域名。**未部署生产环境**（Vercel 已为
  本 PR 自动生成 **PR Preview**，预览部署状态成功；这不等于生产部署，也不等于
  生产环境被修改）。
- 结论摘要：**此前 19 条已保存的作者决定在当前沙盒中无法找回（已穷尽检索）；
  审阅系统本身完好且可用；本次已建立可校验、可追踪、可恢复的持久化机制。**

标记约定：**【事实】**=有直接证据；**【推断】**=由事实推导，非直接证据；
**【建议】**=尚未实施、待作者决定。

---

## 1. 调查目标与结论

### 1.1 作者审核记录是否真实存在过？

**【事实】** 存在过。`5b423d8`（“fix(review): harden author-review system after
batch-2 404 investigation”）的提交说明明确写着 **“Real review data (19 candidates,
23 journal lines)”** 未被改动。多份报告给出同一权威数据的 SHA-256：

- `docs/phase1/author-review-delivery-report.md`
- `docs/phase1/security-hardening-report.md`
- `docs/phase1/visual/tests-content-functional-security.md`
- `docs/phase1/visual-r2/tests-content-functional-security.md`
- `PROGRESS.md`

> 真实数据 SHA-256：`7f311871818e8b15a49654171f4ea20de726cc5879f513f1a257f5f5cb7ccb4d`
> （`journal.jsonl`，23 行 / 19 条唯一候选）

### 1.2 记录保存在哪里、作者如何点击“保留”？

**【事实】** 审阅页 `/review/poem/C####.html` 内嵌真实表单（`id="f-save"`），
点击“保存审阅” → `POST /review/api/review` → `tools/review/store.py::save()`
→ **追加一行**写入 `docs/author-review/review-records/journal.jsonl`（追加式，
永不覆盖），随后重建 `snapshot.json` 与导出文件。表单三项：审阅结论
（待审阅/保留/暂缓/排除）、作品性质、作者意见。

**【事实】** 作者若点击“保留”，其 `status` 即为 `keep`（中文标签“保留”）。

### 1.3 这些记录现在在哪里？能否找回？

**【事实】** **不在当前沙盒，也不在 Git 历史中。**

穷尽检索的范围与结果：

| 检索位置 | 方法 | 结果 |
| --- | --- | --- |
| 全仓 Git 历史（86 提交，已 `--unshallow`） | 遍历全部 blob，匹配 `journal`/`snapshot`/CSV 含 `keep` 行/JSONL 记录 | **0 命中** |
| 全部远端分支与引用 | `git rev-list --objects --all` 逐一 `cat-file` | **0 命中** |
| 工作区与文件系统 | `find /` 搜 `journal*.jsonl`、`review-status*.md`、`review-token.txt` | **0 命中** |
| 本地会话存档 `/var/openhands/conversations/` | 仅当前会话 | **0 命中** |
| OpenHands Cloud 全部 24 个会话事件流 | 逐会话分页扫描 4 个关键词 | **0 命中**（仅审计会话反复提到沙盒主机名，无记录内容） |
| 备份目录 `/home/openhands/poet-review-backups/` | 直接查看 | **不存在**（不同容器） |

**【事实】** 记录文件被 `.gitignore` 排除
（`journal.jsonl` / `journal-test.jsonl` / `snapshot.json` / 导出文件），
原因见 `.gitignore` 注释：**本仓库是公开仓库，作者意见属私人内容，绝不能提交**。
因此记录从未进入 Git，任何克隆都查不到。

**【事实】** 记录原生于**另一个沙盒**（`work-1-koykqjjrzyyvyosg.prod-runtime...`，
见交付报告）。该沙盒现在返回 **404**，已不存在。同一时期的“锁定会话故障调查”
会话（`cf4e71e3…`，2026-11-13）正是在排查此类会话/沙盒丢失问题。

**【事实】** 该沙盒内的“独立备份”落在 `/home/openhands/poet-review-backups/`
——但报告 `docs/phase1/backup-recovery-report.md` 自己指出：**`/home` 与 `/`
同 overlay，容器整体回收会同时丢失源与备份**。即备份并非真正异地。

**【推断】** 19 条作者决定随该沙盒/容器回收而丢失，**在本沙盒内不可恢复**。

**【建议】** 唯一可能的找回途径是平台侧：该旧沙盒的快照/卷（若 OpenHands Cloud
保留了容器卷快照）。这需要平台管理员操作，超出本沙盒权限，且**不得**为恢复而
冒险操作旧环境。请作者/平台管理员确认是否存在可挂载的旧卷快照。

### 1.4 审阅系统本身是否还可用？

**【事实】** 完好且可用。`tools/review/` 全套（`store.py`、`serve_review.py`、
`build_review_site.py`、`test_review_system.py`、`backup_review_data.py`、
`rebuild_snapshot.py`）在位；`docs/author-review/site/` 下 137 个审阅页含真实表单。

**【事实】** 端到端验收测试 `test_review_system.py` **15 组全部通过**
（保存→回读→更新→进度→导出→失败反馈→隔离→令牌门禁→日志无令牌→阅读页开放）。

---

## 2. 本次建立的持久化与追踪机制

### 2.1 规范台账 `decisions.jsonl`（新增）

**【事实】** 新增 `tools/review/build_decisions.py`，把权威 `journal.jsonl`
投影为**每候选一行**的规范台账，字段固定、可校验、可导入：

```
candidate_id   source_post_id   source_url   title
decision       reviewed_at      record_source   notes(作者意见逐字)
（附加）status nature rev reviewer
```

`decision` 取值：`pending | keep | reject | reclassify | version_check | deferred`，
是 UI `status` 的**投影**（`keep→keep`、`exclude→reject`、`hold→deferred`），
因此**审阅页、其 API 与保存逻辑完全未改**。

### 2.2 可校验备份（增强）

**【事实】** `tools/review/backup_review_data.py` 已加入 `decisions.jsonl`；
备份生成 `SHA256SUMS.txt` + `manifest.json`，支持 `backup / verify / restore`。
备份**fail-closed**：先从权威 journal 刷新派生文件，**刷新失败即中止、返回非零、
不写任何备份**。同文件系统目标与记录目录内部目标均被**拒绝**；恢复在校验失败或
无法为现有记录做安全备份时被**拒绝**。已实测：备份 → `verify` **全部 OK** →
恢复到空目录 → 记录逐项一致。

**【事实·重要限定】** 本沙盒中记录在 `/workspace`（ext4 挂载，设备号 66309），
默认备份目录 `/home/openhands/...` 在容器 overlay 上（设备号 240）——**确属不同
文件系统，但仍在同一容器内**。因此它只能扛住**工作区回收**，**扛不住整沙盒回收**。
只有把备份送出本机（私有仓库或对象存储）才真正抵御沙盒回收。**不得**把本地另一个
目录称为"异地备份"。（第二轮安全审查已就此修正文档措辞，见下方第二轮报告。）

### 2.3 进度摘要与恢复说明（新增，随仓库提交）

**【事实】** 新增 `tools/review/build_review_artifacts.py`，生成两份**不含私人意见正文**
的可提交文件：

- `docs/author-review/review-records/review-summary.md`（计数 + 已决定候选清单）
- `docs/author-review/review-records/recovery-report.md`（格式与恢复步骤）

### 2.4 提交策略

**【事实】** `.gitignore` 新增忽略 `decisions.jsonl`（私人数据）；而
`review-summary.md` 与 `recovery-report.md` **明确不忽略、随仓库提交**，
以保证“记录格式与恢复方法”在沙盒丢失后仍可追溯。

---

## 3. “保留”作品进入正式作品集的流程（**【建议】**，尚未实施）

**【事实】** 当前 Hugo 站 `hugo/content/posts/` 仅有 6 篇 demo + `_index`，
**尚无真实诗歌正文**；真实诗歌目前在审阅站（由 feed 生成）内。因此“保留”
尚未、也不应自动进入正式站。

**【建议】** 采用“审阅 → 队列 → 授权 → 发布”四步，**不自动发布**：

1. 审阅页把候选标为 `keep`（作者操作，已有）。
2. `build_decisions.py` 生成 `decisions.jsonl`，`decision=keep` 的行进入**待发布队列**
   （仅记录，不动站点）。
3. 作者**明确授权**后，由一次性脚本把该候选正文**逐字**转为
   `hugo/content/posts/<slug>.md`，并保持既有 URL 规则（`/:slug/`）。
4. 构建校验：逐字保真 + URL 不变 + 生产产物不含 `/review/`。

在作者授权前，本流程只停留在第 1–2 步，**不生成任何正式内容**。

---

## 4. 边界声明

**【事实】** 本次未修改任何诗歌正文、作者小传、题记、候选 CSV、审阅记录或
既有 API；未削弱 `/review/` 访问控制；未触碰 `main`、域名、DNS。**未部署生产
环境**（Vercel 已为本 PR 自动生成 **PR Preview**，预览部署状态成功；这不等于
生产部署）。令牌与私人意见未写入任何提交。恢复记录文件均为 gitignore，未提交。

---

## 5. 需要作者决定的事项

1. **旧记录是否值得平台侧抢救**：是否请管理员查找旧沙盒卷快照（唯一找回途径）。
2. **是否接受重做 19 条审阅**：若旧记录不可找回，作者可能需在新系统重审。
3. **私有异地备份目标**：请提供可写目标（私有仓库或对象存储），以真正抵御容器回收。
4. **是否推进“保留 → 正式作品集”**：若推进，请明确授权范围。
