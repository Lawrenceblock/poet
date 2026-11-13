#!/usr/bin/env python3
"""Build author-facing review materials from the v2 poetry census.

Reads the frozen v2 classification CSV (read-only) and emits, into
docs/author-review/:

  * poetry-candidates-author-review.csv   (one row per candidate article)
  * batch-A.md  batch-B.md  batch-CD.md    (mobile-friendly batch guides)

The CSV adds clearly-documented author-review fields on top of the v2 columns.
Author confirmation status always starts as "待作者审阅" (pending author review);
nothing here claims author confirmation.

The script never copies full poem text: it only reuses the truncated `note`
snippet that already exists in the v2 CSV.

Usage:
    python3 tools/author-review/build_author_review.py
"""
import csv
import os
import re

SRC = "docs/poetry-discovery/poetry-candidates.v2.csv"
OUT = "docs/author-review"

CATEGORY_LABEL = {
    "A": "A · 有明确作者署名线索（脚本判定，≠ 作者确认）",
    "B": "B · 疑似原创，但缺少结构性署名（需作者判断）",
    "C": "C · 译者身份 / 翻译作品",
    "D": "D · 评论、创作谈或消息类",
    "E": "E · 引用/转载他人作品",
}

# A structural byline means a real byline pattern, not a bare name in prose.
STRUCTURAL_BYLINE_HINTS = (
    "explicit 安然 byline",
)

TRANSLATOR_HINTS = ("安然-as-translator", "translator", "译", "translat")

STATUS_PENDING = "待作者审阅"


def yn(value):
    return "yes" if value else "no"


def has_name(text):
    return bool(re.search(r"安然|An\s+Ran|AN\s+RAN", text or ""))


def looks_translator(text):
    return bool(re.search(r"译者|翻译|translat|Translated|译[:：]", text or ""))


def boundary_question(row):
    """A concrete question for the author about this record's work boundary."""
    if row["boundary_status"] == "needs_split":
        return "标题含“组诗/外一首/二首”等标记，请确认文章内实际有几首诗、各自标题与边界。"
    if row["category"] == "C":
        return "请确认这是“安然翻译他人作品”，还是另有情况；并确认原作者与篇名。"
    if row["category"] == "D":
        return "请确认这是评论/创作谈/消息，还是其中也包含独立诗作。"
    if "compound" in row["authorship_evidence"]:
        return "本文疑似“诗 + 评论/译文”复合内容，请指出其中的诗歌部分范围。"
    return "请确认本文是“一首诗 / 多首诗 / 非诗（消息、评论等）”，以及作品边界。"


def question_for(row):
    """The single most important question for this record."""
    if row["category"] == "B" and not any(
        h in row["authorship_evidence"] for h in STRUCTURAL_BYLINE_HINTS
    ):
        return "正文没有结构化署名。请确认本文是否为安然原创诗歌。"
    if row["category"] == "C":
        return "请确认安然在此文的身份是“译者”还是“作者”。"
    if row["category"] == "D":
        return "请确认本文是否为诗歌作品，而非评论/创作谈/消息。"
    if row["boundary_status"] == "needs_split":
        return "请确认本文含几首诗及其边界（组诗/多首）。"
    return "请确认本文是否为安然原创诗歌，以及作品边界。"


def classify_for_author(row):
    note_title = (row["note"] or "") + " " + (row["source_post_title"] or "")
    byline = any(h in row["authorship_evidence"] for h in STRUCTURAL_BYLINE_HINTS)
    name_present = has_name(note_title) or byline
    translator = looks_translator(note_title) or row["category"] == "C"
    multi = row["multi_poem_flag"] == "yes"
    return byline, name_present, translator, multi


def build_rows(rows):
    out = []
    for i, row in enumerate(rows, 1):
        byline, name_present, translator, multi = classify_for_author(row)
        out.append(
            {
                "序号": i,
                "candidate_id": row["candidate_id"],
                "原始文章日期": row["published"][:10],
                "文章标题": row["source_post_title"],
                "原始文章URL": row["source_url"],
                "当前分类": row["category"],
                "分类含义": CATEGORY_LABEL.get(row["category"], ""),
                "分类依据（脚本）": row["authorship_evidence"],
                "是否有结构化作者署名": yn(byline),
                "是否出现作者姓名或笔名": yn(name_present),
                "是否可能存在译者身份": yn(translator) if translator else "unknown",
                "是否有组诗或多首作品线索": "yes" if multi else "unknown",
                "当前作品数量估计": row["work_count_estimate"],
                "需要作者确认的问题": question_for(row),
                "作品边界问题": boundary_question(row),
                "作者确认状态": STATUS_PENDING,
                "备注（脚本，截断摘录）": row["note"],
                "语言": row["lang"],
                "置信度（脚本）": row["confidence"],
                "source_post_id": row["source_post_id"],
            }
        )
    return out


def write_csv(out_rows):
    path = os.path.join(OUT, "poetry-candidates-author-review.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    return path


def batch_md(rows, title, intro):
    lines = [f"# {title}", "", intro, ""]
    for r in rows:
        lines.append(f"## {r['序号']}. {r['文章标题']}")
        lines.append("")
        lines.append(f"> 候选 ID：`{r['candidate_id']}`（与 `poetry-candidates-author-review.csv` 对应）")
        lines.append("")
        lines.append(f"- **原始文章日期**：{r['原始文章日期']}")
        lines.append(f"- **原始文章链接**：{r['原始文章URL']}")
        lines.append(f"- **当前分类**：{r['分类含义']}")
        lines.append(f"- **脚本判定依据**：`{r['分类依据（脚本）']}`")
        lines.append(f"- **是否有结构化署名**：{r['是否有结构化作者署名']}")
        lines.append(f"- **是否出现作者姓名/笔名**：{r['是否出现作者姓名或笔名']}")
        lines.append(f"- **是否可能为译者身份**：{r['是否可能存在译者身份']}")
        lines.append(f"- **组诗/多首线索**：{r['是否有组诗或多首作品线索']}")
        lines.append(f"- **作品数量估计**：{r['当前作品数量估计']}")
        lines.append(f"- **需要作者确认**：{r['需要作者确认的问题']}")
        lines.append(f"- **作品边界问题**：{r['作品边界问题']}")
        lines.append(f"- **作者确认状态**：{r['作者确认状态']}")
        lines.append("")
        lines.append("<details><summary>脚本截断摘录（用于定位，非全文）</summary>")
        lines.append("")
        lines.append(f"> {r['备注（脚本，截断摘录）']}")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines)


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(SRC, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out_rows = build_rows(rows)
    write_csv(out_rows)

    a = [r for r in out_rows if r["当前分类"] == "A"]
    b = [r for r in out_rows if r["当前分类"] == "B"]
    cd = [r for r in out_rows if r["当前分类"] in ("C", "D", "E")]

    with open(os.path.join(OUT, "batch-A.md"), "w", encoding="utf-8") as f:
        f.write(
            batch_md(
                a,
                f"A 类候选（{len(a)} 条）· 作者审阅",
                "A 类表示脚本检测到**明确的结构化署名**。注意：**A 类 ≠ 作者已确认**；"
                "仍需作者确认作品边界与归属。",
            )
        )
    with open(os.path.join(OUT, "batch-B.md"), "w", encoding="utf-8") as f:
        f.write(
            batch_md(
                b,
                f"B 类候选（{len(b)} 条）· 作者审阅",
                "B 类表示**疑似原创但缺少结构性署名**，最需要作者判断归属。",
            )
        )
    with open(os.path.join(OUT, "batch-CD.md"), "w", encoding="utf-8") as f:
        f.write(
            batch_md(
                cd,
                f"C/D/E 类候选（{len(cd)} 条）· 作者审阅",
                "C = 译作；D = 评论/创作谈/消息；E = 引用/转载他人作品。",
            )
        )

    print(f"rows: {len(out_rows)}  A={len(a)} B={len(b)} C/D/E={len(cd)}")
    print("wrote:", os.path.join(OUT, "poetry-candidates-author-review.csv"))


if __name__ == "__main__":
    main()
