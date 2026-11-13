#!/usr/bin/env python3
"""Build the Phase 1 content lists for the author's review.

Reads the read-only sources and writes three Markdown lists under
docs/author-review/phase1/:

  * candidate-list.md       — all 137 article-level candidates
  * review-status.md        — current review progress from the journal
  * to-confirm.md           — every item the author still has to decide

Nothing here rewrites, reorders or infers poem text: titles, dates and
categories come straight from the candidate CSV, and anything uncertain is
marked 待作者确认 rather than filled in.
"""
import csv
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CAND_CSV = os.path.join(ROOT, "docs", "poetry-discovery", "poetry-candidates.v2.csv")
JOURNAL = os.path.join(ROOT, "docs", "author-review", "review-records", "journal.jsonl")
OUT = os.path.join(ROOT, "docs", "author-review", "phase1")
# The review-status list quotes the author's own decisions, so it is private:
# it is written under a git-ignored directory and never committed to this
# public repository (see .gitignore).
OUT_PRIVATE = os.path.join(ROOT, "docs", "author-review", "private")

CAT_MEANING = {
    "A": "有结构化作者署名（很可能是原创诗作）",
    "B": "出现作者姓名/笔名，但署名结构不完整（需作者确认）",
    "C": "可能为译作或转载（需作者确认）",
    "D": "边界/归属不明（需作者确认）",
    "E": "疑似非诗内容（需作者确认）",
}
STATUS_LABEL = {"keep": "保留", "hold": "暂缓", "exclude": "排除", "pending": "待审阅"}
NATURE_LABEL = {"single_poem": "单首", "multi_poem": "多首/组诗",
                "non_poem": "非诗", "unsure": "不确定", "unset": "（未填写）"}


def load_candidates():
    with open(CAND_CSV, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_latest():
    """Latest non-test record per candidate, from the append-only journal."""
    latest = {}
    if not os.path.exists(JOURNAL):
        return latest
    with open(JOURNAL, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("test"):
                continue
            latest[r["candidate_id"]] = r
    return latest


def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def title_of(r):
    t = (r.get("candidate_title") or "").strip()
    if t:
        return t
    return f"（无独立标题，取文章标题）{r.get('source_post_title','')}".strip()


def write_candidate_list(cands):
    lines = ["# 候选作品完整清单（137 条文章级候选）", "",
             "> 生成：由 `tools/author-review/build_phase1_lists.py` 从只读的",
             "> `docs/poetry-discovery/poetry-candidates.v2.csv` 生成。",
             "> **本清单是文章级候选，不是 137 首诗**；独立作品总数待作者确认。",
             "> 分类为脚本判定，**非作者确认**。", ""]
    lines.append(f"- 候选总数：**{len(cands)}**")
    lines.append(f"- 分类分布：{dict(Counter(r['category'] for r in cands))}")
    lines.append(f"- 语言分布：{dict(Counter(r['lang'] for r in cands))}")
    lines.append(f"- 含多首线索（multi_poem_flag=yes）：{sum(1 for r in cands if r['multi_poem_flag']=='yes')}")
    lines.append("")
    lines.append("| ID | 标题/定位 | 原始文章日期 | 分类 | 语言 | 多首线索 | 原文章 URL |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for r in cands:
        lines.append("| {id} | {t} | {d} | {c} | {l} | {m} | {u} |".format(
            id=r["candidate_id"], t=esc(title_of(r)),
            d=esc((r.get("published") or "")[:10]), c=r["category"],
            l=r["lang"], m=r["multi_poem_flag"], u=r["source_url"]))
    lines.append("")
    lines.append("## 分类含义")
    for k, v in CAT_MEANING.items():
        lines.append(f"- **{k}**：{v}")
    return "\n".join(lines) + "\n"


def write_review_status(cands, latest):
    reviewed = [r for r in cands if r["candidate_id"] in latest]
    by_status = Counter(latest[r["candidate_id"]].get("status", "pending") for r in reviewed)
    lines = ["# 作者审阅状态清单", "",
             "> 数据源：`docs/author-review/review-records/journal.jsonl`（作者真实审阅，追加式）。",
             "> 测试记录（test=true）不计入。", ""]
    lines.append(f"- 候选总数：**{len(cands)}**")
    lines.append(f"- 已审阅：**{len(reviewed)}**")
    lines.append(f"- 未审阅：**{len(cands) - len(reviewed)}**")
    lines.append(f"- 结论分布：{ {STATUS_LABEL.get(k, k): v for k, v in by_status.items()} }")
    lines.append("")
    lines.append("| ID | 标题/定位 | 结论 | 作品性质 | 意见摘要 | 更新时间 | 版本 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for r in cands:
        cid = r["candidate_id"]
        if cid not in latest:
            continue
        rec = latest[cid]
        lines.append("| {id} | {t} | {s} | {n} | {cm} | {u} | {rev} |".format(
            id=cid, t=esc(title_of(r)),
            s=STATUS_LABEL.get(rec.get("status"), rec.get("status")),
            n=NATURE_LABEL.get(rec.get("nature"), rec.get("nature")),
            cm=esc((rec.get("comment") or "")[:60]),
            u=esc(rec.get("updated_at", "")), rev=rec.get("rev", "")))
    lines.append("")
    lines.append("## 未审阅候选（待作者继续）")
    lines.append("")
    unreviewed = [r["candidate_id"] for r in cands if r["candidate_id"] not in latest]
    lines.append(", ".join(unreviewed) if unreviewed else "（全部已审阅）")
    return "\n".join(lines) + "\n"


def write_to_confirm(cands):
    lines = ["# 待作者确认事项清单", "",
             "> 本清单**只提出问题，不替作者决定**。凡脚本无法确定的，一律标记待确认。", ""]
    lines.append("## 一、需要作者逐项确认的作品问题")
    lines.append("")
    no_title = [r for r in cands if r["has_own_title"] != "yes"]
    lines.append(f"1. **标题**：{len(no_title)} 条候选未检测到独立标题（脚本取文章标题或留空），需作者确认每篇的真实标题。")
    multi = [r for r in cands if r["multi_poem_flag"] == "yes"]
    lines.append(f"2. **组诗拆分**：{len(multi)} 条含多首线索，需作者确认是否拆分及各首边界：{', '.join(r['candidate_id'] for r in multi)}。")
    lines.append("3. **创作时间**：脚本仅有发布日期，**创作时间**需作者提供（缺失的不得由 AI 推断）。")
    lines.append("4. **首次发表时间**：需作者确认（脚本无此字段）。")
    lines.append("5. **作品版本**：如《青春的物语》存在旧站版与博客版差异，采用哪一版需作者裁定。")
    lines.append("6. **收录范围**：137 候选是否为最终收录集？旧博客另有 168 篇未列入候选，是否纳入需作者决定。")
    lines.append("7. **归属存疑**：《放牧的星星》《安然》等正文无署名的候选是否确为作者原创，需作者确认。")
    lines.append("")
    lines.append("## 二、分类待复核")
    lines.append("")
    lines.append("| 分类 | 数量 | 待确认内容 |")
    lines.append("| --- | --- | --- |")
    for k in ["B", "C", "D"]:
        n = sum(1 for r in cands if r["category"] == k)
        lines.append(f"| {k} | {n} | {CAT_MEANING[k]} |")
    lines.append("")
    lines.append("## 三、作者资料")
    lines.append("")
    lines.append("8. **诗人小传**定稿文本（现有为占位/旧站内容）。")
    lines.append("9. **题记**定稿文本。")
    lines.append("10. **版权/许可**声明文本（`/about/`）。")
    lines.append("")
    lines.append("## 四、技术选择（需作者或负责人决定）")
    lines.append("")
    lines.append("11. 旧博客域名 `www.ismaelan.com` 是否保留、是否设置 301。")
    lines.append("12. 是否需要为中文标题文章指定可读英文 slug。")
    lines.append("")
    lines.append("> 以上任一项在作者明确回复前，均保持现状，不做改动。")
    return "\n".join(lines) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT_PRIVATE, exist_ok=True)
    cands = load_candidates()
    latest = load_latest()
    public = {
        "candidate-list.md": write_candidate_list(cands),
        "to-confirm.md": write_to_confirm(cands),
    }
    for name, text in public.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {os.path.relpath(os.path.join(OUT, name), ROOT)}")
    # Private: quotes the author's decisions, kept out of the public repo.
    priv = os.path.join(OUT_PRIVATE, "review-status.md")
    with open(priv, "w", encoding="utf-8") as fh:
        fh.write(write_review_status(cands, latest))
    print(f"wrote (private) {os.path.relpath(priv, ROOT)}")
    print(f"candidates={len(cands)} reviewed={len(latest)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
