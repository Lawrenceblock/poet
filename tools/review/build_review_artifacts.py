#!/usr/bin/env python3
"""Generate the durable, human-readable review artefacts (stdlib only).

Outputs (both committed to the repo, neither contains private tokens):

  docs/author-review/review-records/review-summary.md
      A compact, regenerable progress summary for the author: counts by
      decision, and the list of candidates already decided (id, title,
      decision, reviewed_at). Regenerate after every review session.

  docs/author-review/review-records/recovery-report.md
      A self-describing note explaining the record format, where the data
      lives, how it is backed up, and how to recover it after a sandbox
      restart. This is the "persistent, traceable record mechanism" the
      task asks for.

Private review comments are NOT written here (they can be long and personal);
only counts, ids, titles and timestamps. The full comments live in
journal.jsonl / decisions.jsonl / the exports, which are gitignored.
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import store  # noqa: E402
import build_decisions  # noqa: E402

RECORDS = store.RECORDS
SUMMARY = os.path.join(RECORDS, "review-summary.md")
RECOVERY = os.path.join(RECORDS, "recovery-report.md")

DECISION_LABEL = {
    "pending": "待作者审阅",
    "keep": "保留",
    "reject": "排除",
    "reclassify": "需修改分类",
    "version_check": "需确认版本",
    "deferred": "暂缓决定",
}


def _journal_stats():
    lines = store.read_journal()
    return len(lines), len({r.get("candidate_id") for r in lines})


def write_summary():
    rows = build_decisions.build()
    by = Counter(r["decision"] for r in rows)
    reviewed = sum(1 for r in rows if r["decision"] != "pending")
    lines = []
    lines.append("# 作者审阅 · 进度摘要")
    lines.append("")
    lines.append("> 本文件由 `tools/review/build_review_artifacts.py` 生成，可随时重新生成。")
    lines.append("> 只含**汇总计数**；逐篇决定与作者意见属私人内容，")
    lines.append("> 仅保存在 gitignore 的 `decisions.jsonl` / `journal.jsonl` 中，不提交。")
    lines.append("")
    lines.append(f"- 候选总数：**{len(rows)}**")
    lines.append(f"- 已作决定：**{reviewed}**")
    lines.append(f"- 尚未审阅：**{len(rows) - reviewed}**")
    lines.append("")
    lines.append("## 按决定统计（仅计数）")
    lines.append("")
    lines.append("| 决定 | 数量 |")
    lines.append("| --- | --- |")
    for k in ["keep", "deferred", "reject", "reclassify", "version_check", "pending"]:
        if by.get(k):
            lines.append(f"| {DECISION_LABEL.get(k, k)} (`{k}`) | {by[k]} |")
    lines.append("")
    text = "\n".join(lines) + "\n"
    with open(SUMMARY, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def write_recovery_report():
    jlines, juni = _journal_stats()
    rows = build_decisions.build()
    by = Counter(r["decision"] for r in rows)
    text = f"""# 作者审阅记录 · 持久化与恢复说明

> 生成时间：{store._now()}　|　由 `tools/review/build_review_artifacts.py` 生成

## 1. 记录保存在哪里

| 文件 | 角色 | 是否提交到 Git |
| --- | --- | --- |
| `review-records/journal.jsonl` | **权威**：每次“保存审阅”追加一行，永不覆盖 | 否（私有，gitignore） |
| `review-records/decisions.jsonl` | 投影台账：每候选一行，字段规范、便于审计/导入 | 否（私有，gitignore） |
| `review-records/snapshot.json` | 由 journal 重放得到的最新状态 | 否（私有，gitignore） |
| `review-records/export-review-records.csv` / `.json` | 供作者下载留档 | 否（私有，gitignore） |
| `review-records/review-summary.md` | 进度摘要（无私人意见正文） | 是（公开可提交） |
| `review-records/recovery-report.md` | 本说明文件 | 是（公开可提交） |

当前权威记录：**{jlines} 行 / {juni} 条唯一候选**；
已作决定 {len(rows) - by.get('pending', 0)} / {len(rows)}。

`decisions.jsonl` 每行字段：

```
candidate_id   候选编号（C####，与 poetry-candidates.v2.csv 一致）
source_post_id 原始 Blogger 文章 id
source_url     原文地址（正文的权威来源）
title          当前标题
decision       pending | keep | reject | reclassify | version_check | deferred
reviewed_at    最后保存时间（北京时间 ISO-8601），未审阅为空
record_source  决定来源（journal.jsonl 或恢复标记）
notes          作者本人意见（逐字）
```

## 2. 为什么之前会“看起来丢了”

- 审阅记录是作者的私人意见，仓库为**公开**仓库，因此记录文件被 `.gitignore`
  排除，从不进入 Git 历史。
- 因此一次沙盒/工作区回收就会连同记录一起消失；GitHub 上查不到任何痕迹。

## 3. 如何避免再次丢失（本次建立的机制）

1. **规范台账**：`decisions.jsonl` 提供稳定、可校验、可导入的字段结构。
2. **可校验备份（严格 fail-closed）**：
   ```bash
   python3 tools/review/backup_review_data.py backup --to <目录>
   python3 tools/review/backup_review_data.py verify <备份目录>
   python3 tools/review/backup_review_data.py restore <备份目录> --yes
   ```
   备份含 `SHA256SUMS.txt` + `manifest.json`（带 `format` 与 `missing_files` 声明）。
   **校验严格且 fail-closed**：manifest 与清单必须存在、非空、无重复、逐文件一致，
   且“存在 + 声明缺失”恰好覆盖全部数据文件；拒绝绝对路径/`../`/非法名/符号链接；
   文件缺失或哈希不符即失败。**恢复必须先通过校验，没有跳过校验的开关。**
   备份前先从权威 journal 刷新派生文件；**刷新失败即中止、返回非零、不写任何备份**。
   同文件系统目标、以及位于记录目录内部的目标，都会被拒绝。
3. **定期导出**：审阅页顶部可导出 CSV/JSON，供作者自行留档。
4. **私有远端（建议，需作者授权）**：把备份推送到**私有**仓库或对象存储，
   才能真正抵御整容器回收。

> ⚠️ **本地"不同文件系统"≠"异地"。** 本沙盒里记录在 `/workspace`（ext4 挂载），
> 默认备份目录在容器 overlay 上——**确属不同文件系统，但仍在同一容器内**。
> 整个沙盒被回收时两者一起丢失。只有把备份**送出这台机器**（私有仓库/对象存储）
> 才真正抵御沙盒回收。不要把本地另一个目录称为"异地备份"。

## 4. 沙盒重启后的恢复顺序

1. 先查 GitHub 分支与提交（工作成果都在 Git 上）。
2. 若存在**私有远端**备份，`verify` 校验后 `restore`；本地默认目录只能扛住
   工作区回收，扛不住整沙盒回收。
3. `python3 tools/review/rebuild_snapshot.py` 重放 journal → snapshot。
4. 重新生成台账与摘要：`python3 tools/review/build_review_artifacts.py`。
5. 启动审阅服务：`REVIEW_ACCESS_TOKEN=... python3 tools/review/serve_review.py --port 12000`。

## 5. 边界

- 记录中不含任何令牌；令牌单独存放且已 gitignore。
- 本机制不修改诗歌正文、作者小传、题记或既有 API。
- 备份/恢复的自动化验收：`python3 tools/review/test_backup_system.py`（隔离临时目录）。
"""
    with open(RECOVERY, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def main():
    store.rebuild()
    build_decisions.write()
    write_summary()
    write_recovery_report()
    print("wrote review-summary.md and recovery-report.md")
    print(json.dumps(build_decisions.summarize(build_decisions.build()),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
