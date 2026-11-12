#!/usr/bin/env python3
"""Build the author-facing poetry review site (static HTML, self-contained).

Inputs (all read-only):
  * work/feed/feed-*.json                     raw public Blogger feed (gitignored)
  * docs/poetry-discovery/poetry-candidates.v2.csv   137 candidates
  * docs/poetry-discovery/blog-post-inventory.v2.csv 305 posts (URL map)

Outputs (docs/author-review/site/, committed):
  * index.html                    master catalogue
  * batch-A.html / batch-B.html / batch-CD.html
  * poem/<candidate_id>.html      one reading page per candidate
  * data/candidates.json          machine-readable index

Design notes
------------
* Verbatim text is preserved via extract_post_html.sanitize(); nothing is
  re-worded, re-punctuated or re-flowed.
* Each page clearly states it is a REVIEW copy, not the published version.
* The original Blogger URL is always shown as the authoritative source.
* No poem is marked "confirmed"; every row stays "待作者审阅".

The script only writes into docs/author-review/site/. It never edits the
source CSVs and never touches the Hugo site.
"""
import csv
import glob
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_post_html import sanitize, visible_text  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAND_CSV = os.path.join(ROOT, "docs", "poetry-discovery", "poetry-candidates.v2.csv")
INV_CSV = os.path.join(ROOT, "docs", "poetry-discovery", "blog-post-inventory.v2.csv")
FEED_GLOB = os.path.join(ROOT, "work", "feed", "feed-*.json")
OUT = os.path.join(ROOT, "docs", "author-review", "site")

CATEGORY_LABEL = {
    "A": "A · 脚本检测到明确署名（文/安然 等）",
    "B": "B · 有诗歌特征但无明确署名",
    "C": "C · 疑似译作（安然为译者）",
    "D": "D · 评论/创作谈/消息类",
    "E": "E · 引用/转载他人作品",
}

STATUS_OPTIONS = [
    "待作者审阅",
    "确认收入诗歌站",
    "不收入诗歌站",
    "需要修改分类",
    "需要确认版本",
    "暂缓决定",
]


def load_entries():
    entries = {}
    for f in sorted(glob.glob(FEED_GLOB)):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        for e in data["feed"].get("entry", []):
            pid = e["id"]["$t"].split(".post-")[-1]
            entries[pid] = e
    return entries


def post_url(entry):
    for l in entry.get("link", []):
        href = l.get("href", "")
        if "www.ismaelan.com" in href and "/feeds/" not in href:
            return href
    return ""


def esc(s):
    return html.escape(s or "", quote=True)


PAGE_CSS = """
:root{--ink:#23201c;--muted:#7a7268;--line:#e4ddd2;--bg:#faf7f2;--card:#fff;--accent:#8a5a2b;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.9;font-size:17px}
.wrap{max-width:760px;margin:0 auto;padding:28px 20px 64px}
a{color:var(--accent)}
h1{font-size:1.5rem;font-weight:600;margin:.2em 0 .6em}
h2{font-size:1.1rem;margin:1.6em 0 .4em}
.note{background:#fff8e8;border:1px solid #eadfc4;border-radius:8px;padding:12px 14px;
 color:#6b5a3a;font-size:.9rem;margin:16px 0}
.meta{color:var(--muted);font-size:.85rem;line-height:1.7}
.meta b{color:var(--ink);font-weight:600}
.tags span{display:inline-block;background:#f0ebe2;border-radius:999px;
 padding:1px 10px;margin:2px 4px 2px 0;font-size:.78rem;color:#5c5347}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
 padding:16px 18px;margin:14px 0}
.card h3{margin:0 0 .3em;font-size:1.02rem;font-weight:600}
.poem{background:#fff;border:1px solid var(--line);border-radius:10px;
 padding:22px 24px;margin:18px 0}
.poem p{margin:0 0 1.05em}
.poem img{max-width:100%;height:auto}
.verse{white-space:pre-wrap}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:#f3eee5}
.status{display:inline-block;border:1px dashed #c9bfae;border-radius:6px;
 padding:1px 8px;font-size:.78rem;color:#6b6152;background:#fbf8f2}
.foot{margin-top:40px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:14px}
.batchnav a{display:inline-block;margin-right:14px}
.banner{background:#eef6ee;border:1px solid #cfe3cf;border-radius:8px;
 padding:10px 14px;font-size:.85rem;color:#3c5a3c;margin-bottom:18px}
"""


def page(title, body, extra_head=""):
    return ("<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            "<meta name=\"robots\" content=\"noindex,nofollow\">\n"
            f"<title>{esc(title)}</title>\n"
            f"<style>{PAGE_CSS}</style>\n{extra_head}"
            "</head>\n<body><div class=\"wrap\">\n" + body +
            "\n<div class=\"foot\">安然诗歌档案 · 作者审阅材料 · "
            "本页为审阅副本，非正式发表版本。原文版权归作者所有。</div>\n"
            "</div></body></html>\n")


def status_block(cid):
    opts = "".join(f"<option>{esc(o)}</option>" for o in STATUS_OPTIONS)
    return (f"<p class=\"meta\">作者审阅状态（请在审阅记录中填写）："
            f"<span class=\"status\">待作者审阅</span> "
            f"<select data-candidate=\"{esc(cid)}\" disabled title=\"示意，正式记录见 CSV\">{opts}</select>"
            f"</p>")


def build():
    entries = load_entries()
    with open(CAND_CSV, encoding="utf-8") as fh:
        cand = list(csv.DictReader(fh))
    with open(INV_CSV, encoding="utf-8") as fh:
        inv = {r["post_id"]: r for r in csv.DictReader(fh)}

    os.makedirs(os.path.join(OUT, "poem"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

    by_cat = {"A": [], "B": [], "CD": []}
    index_rows = []

    # Assign every candidate to a batch chunk up front so poem pages can link
    # back to the exact chunk that contains them.
    cat_of = {"A": "A", "B": "B", "C": "CD", "D": "CD", "E": "CD"}
    ordered = {k: [c for c in cand if cat_of.get(c["category"], "CD") == k]
               for k in ("A", "B", "CD")}
    batch_of = {}
    batch_defs = []  # (key, label, n, chunk, filename)
    for key, label in (("A", "A 类候选"), ("B", "B 类候选"), ("CD", "C / D 类候选")):
        items = ordered[key]
        chunks = [items[i:i + 15] for i in range(0, len(items), 15)]
        multi = len(chunks) > 1
        for n, chunk in enumerate(chunks, 1):
            fn = f"batch-{key}-{n}.html" if multi else f"batch-{key}.html"
            batch_defs.append((key, label, n, chunk, fn))
            for c in chunk:
                batch_of[c["candidate_id"]] = fn

    for c in cand:
        cid = c["candidate_id"]
        pid = c["source_post_id"]
        e = entries.get(pid)
        src_url = c["source_url"]
        title = (c["candidate_title"] or c["source_post_title"] or "(无标题)").strip()
        raw = e["content"]["$t"] if e else ""
        safe = sanitize(raw)
        cat = c["category"]

        meta = {
            "candidate_id": cid,
            "title": title,
            "source_post_title": c["source_post_title"],
            "published": c["published"][:10],
            "source_url": src_url,
            "category": cat,
            "lang": c["lang"],
            "title_source": c["title_source"],
            "has_own_title": c["has_own_title"],
            "boundary_status": c["boundary_status"],
            "work_count_estimate": c["work_count_estimate"],
            "multi_poem_flag": c["multi_poem_flag"],
            "authorship_evidence": c["authorship_evidence"],
            "labels": c["labels"],
            "confidence": c["confidence"],
            "content_chars": len(visible_text(safe)),
        }
        index_rows.append(meta)

        # ---- per-poem reading page ----
        reasons = []
        reasons.append(f"脚本分类：{CATEGORY_LABEL.get(cat, cat)}")
        if c["authorship_evidence"]:
            reasons.append(f"署名线索：{c['authorship_evidence']}")
        if c["labels"]:
            reasons.append(f"原文标签：{c['labels']}")
        if c["title_source"]:
            reasons.append(f"标题来源：{c['title_source']}")
        if c["multi_poem_flag"] == "yes":
            reasons.append("标题含“组诗/外一首/二首”等线索，可能含多首，需作者确认边界。")
        if c["lang"] == "zh+en":
            reasons.append("检测到中英双语，审阅时请核对两种语言是否为同一作品。")
        if cat in ("C", "D"):
            reasons.append("该类不是明确诗歌，需作者判断是否收入诗歌站。")

        questions = []
        questions.append("这篇文章是“一首诗 / 多首诗 / 非诗（评论、消息、摄影等）”？")
        if c["multi_poem_flag"] == "yes":
            questions.append("若含多首，请分别给出各首标题（用于生成独立页面与链接）。")
        if c["lang"] == "zh+en":
            questions.append("中英文是否为同一作品的两种版本？以哪一版为准？")
        if cat in ("B", "C", "D"):
            questions.append("是否确认作者署名/归属？")
        if c["has_own_title"] == "no":
            questions.append("作品是否有独立标题？若无，页面标题用文章名还是“无题”？")

        body = []
        body.append(f"<p class=\"batchnav\"><a href=\"../index.html\">← 审阅总目录</a> "
                    f"<a href=\"../{esc(batch_of[cid])}\">本批目录</a></p>")
        body.append(f"<h1>{esc(title)}</h1>")
        body.append("<div class=\"note\"><b>这是审阅副本，不是正式发表版本。</b>"
                    "页面完整保留原文（含标点、诗行、段落、图片），仅移除脚本等不安全代码；"
                    "未经作者确认不会用于正式站点。</div>")
        body.append("<p class=\"meta\">"
                    f"候选编号 <b>{esc(cid)}</b>　"
                    f"原始发表日期 <b>{esc(meta['published'])}</b>　"
                    f"语言 <b>{esc(meta['lang'])}</b>　"
                    f"脚本分类 <b>{esc(cat)}</b><br>"
                    f"原始来源：<a href=\"{esc(src_url)}\" rel=\"noopener\">{esc(src_url)}</a></p>")
        if c["labels"]:
            body.append("<p class=\"tags\">" + "".join(
                f"<span>{esc(t)}</span>" for t in re.split(r"[|,]", c["labels"]) if t.strip()) + "</p>")
        body.append("<h2>为什么列出这篇</h2><ul class=\"meta\">" +
                    "".join(f"<li>{esc(r)}</li>" for r in reasons) + "</ul>")
        body.append("<h2>需要作者确认</h2><ul class=\"meta\">" +
                    "".join(f"<li>{esc(q)}</li>" for q in questions) + "</ul>")
        body.append(status_block(cid))
        body.append("<h2>原文（逐字保留）</h2>")
        if meta["content_chars"] < 20:
            body.append("<div class=\"note\">该文正文为空或极短（可能为图片/视频为主的文章）。"
                        "请点击上方原始来源链接查看原貌。</div>")
        body.append(f"<div class=\"poem\">{safe}</div>")
        body.append(f"<p class=\"meta\">如原页面与本页有任何差异，请以 "
                    f"<a href=\"{esc(src_url)}\" rel=\"noopener\">原始来源</a> 为准，并告知差异位置。</p>")

        with open(os.path.join(OUT, "poem", f"{cid}.html"), "w", encoding="utf-8") as fh:
            fh.write(page(f"{cid} · {title}", "\n".join(body)))

        key = "A" if cat == "A" else "B" if cat == "B" else "CD"
        by_cat[key].append(meta)

    # ---- batch pages (from the pre-computed chunks) ----
    batch_files = []
    for key, label, n, chunk, fn in batch_defs:
        body = [f"<p class=\"batchnav\"><a href=\"index.html\">← 审阅总目录</a></p>",
                f"<h1>{label} · 第 {n} 批（{len(chunk)} 篇）</h1>",
                "<div class=\"note\">点击每篇的“阅读全文”即可直接读诗。"
                "所有正文均逐字保留原文，并附原始来源链接。本批共 "
                f"{len(chunk)} 篇，全部状态为“待作者审阅”。</div>"]
        for c in chunk:
            m = next(x for x in index_rows if x["candidate_id"] == c["candidate_id"])
            body.append(
                "<div class=\"card\">"
                f"<h3>{esc(m['title'])}</h3>"
                f"<p class=\"meta\">{esc(m['published'])}　分类 {esc(m['category'])}　"
                f"{esc(m['lang'])}　{esc(m['candidate_id'])}</p>"
                f"<p><a href=\"poem/{esc(m['candidate_id'])}.html\">阅读全文 →</a>　"
                f"<a href=\"{esc(m['source_url'])}\" rel=\"noopener\">原始来源</a></p>"
                "</div>")
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as fh:
            fh.write(page(f"{label} · 第 {n} 批", "\n".join(body)))
        batch_files.append((key, label, n, len(chunk), fn))

    # ---- master index ----
    body = ["<h1>安然诗歌档案 · 作者审阅总目录</h1>",
            "<div class=\"banner\">这些页面是为了让作者<b>直接读到作品全文</b>而建立。"
            "每篇都保留原文标点、诗行与段落，并附原始来源链接。"
            "所有条目状态均为“待作者审阅”，未做任何收入决定。</div>",
            "<div class=\"note\"><b>重要：</b>“候选”是脚本按署名/标签线索筛出的<b>文章</b>，"
            "<b>不等于已经确认的诗歌</b>。例如某些文章实为摄影或评论。"
            "请作者逐篇判断：是不是诗、是一首还是多首、是否收入本站。</div>",
            f"<p class=\"meta\">共 <b>{len(cand)}</b> 篇候选："
            f"A 类 {len(by_cat['A'])}，B 类 {len(by_cat['B'])}，C/D 类 {len(by_cat['CD'])}。"
            f"其中 C 类 {sum(1 for m in by_cat['CD'] if m['category']=='C')}，"
            f"D 类 {sum(1 for m in by_cat['CD'] if m['category']=='D')}。</p>",
            "<h2>按批次阅读</h2>"]
    for key, label, n, cnt, fn in batch_files:
        body.append(f"<div class=\"card\"><h3><a href=\"{fn}\">{label} · 第 {n} 批</a></h3>"
                    f"<p class=\"meta\">{cnt} 篇</p></div>")

    body.append("<h2>完整清单</h2>")
    body.append("<table><tr><th>#</th><th>编号</th><th>标题</th><th>日期</th>"
                "<th>分类</th><th>语言</th><th>阅读</th><th>原始来源</th></tr>")
    for i, m in enumerate(index_rows, 1):
        body.append(f"<tr><td>{i}</td><td>{esc(m['candidate_id'])}</td>"
                    f"<td>{esc(m['title'])}</td><td>{esc(m['published'])}</td>"
                    f"<td>{esc(m['category'])}</td><td>{esc(m['lang'])}</td>"
                    f"<td><a href=\"poem/{esc(m['candidate_id'])}.html\">阅读</a></td>"
                    f"<td><a href=\"{esc(m['source_url'])}\" rel=\"noopener\">来源</a></td></tr>")
    body.append("</table>")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page("作者审阅总目录", "\n".join(body)))

    with open(os.path.join(OUT, "data", "candidates.json"), "w", encoding="utf-8") as fh:
        json.dump(index_rows, fh, ensure_ascii=False, indent=1)

    print(f"candidates: {len(cand)}")
    print(f"batch pages: {len(batch_files)}")
    for k, l, n, c, fn in batch_files:
        print(f"  {fn}: {c} 篇")
    print("index: docs/author-review/site/index.html")


if __name__ == "__main__":
    build()
