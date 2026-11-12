#!/usr/bin/env python3
"""Build the "old poet site" review section.

The current site (poet.ismaelan.com, Jekyll) already publishes a few pages:
  那拉提（未赴）, 青春的物语, 诗人小传, 题记.
Moving them to the new Hugo site is a decision for the author, and one of them
(青春的物语) exists in TWO versions (old poet site vs. the blog). This section
lets the author read them verbatim and answer the version question.

Output: docs/author-review/site/oldsite/*.html (NOT part of the Hugo build;
copied to /review/oldsite/ only for the preview).

Text is taken verbatim from the committed old-site sources (_posts/*.md,
preface.md) and from the public blog feed (work/feed, for the comparison).
Nothing is re-worded.
"""
import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_review_site import PAGE_CSS, page, esc  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "docs", "author-review", "site", "oldsite")

SRC_PAGES = [
    ("na-la-ti.html", "_posts/2026-09-07-na-la-ti.md", "那拉提（未赴）", "2026.09.07", "/na-la-ti/"),
    ("qing-chun-de-wu-yu.html", "_posts/2026-04-07-qing-chun-de-wu-yu.md", "青春的物语", "2026.04.07", "/qing-chun-de-wu-yu/"),
    ("shi-ren-xiao-zhuan.html", "_posts/2026-09-11-shi-ren-xiao-zhuan.md", "诗人小传", "2026.09.11", "/shi-ren-xiao-zhuan/"),
    ("preface.html", "preface.md", "题记", "", "/preface/"),
]


def read_body(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        s = fh.read()
    m = re.match(r"^---\s*\n.*?\n---\s*\n", s, re.S)
    return s[m.end():] if m else s


def blog_version_of_qingchun():
    """Locate the blog copy of 青春的物语 and report whether it differs."""
    import difflib
    entries = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "work", "feed", "feed-*.json"))):
        with open(f, encoding="utf-8") as fh:
            for e in json.load(fh)["feed"].get("entry", []):
                entries[e["id"]["$t"].split(".post-")[-1]] = e
    url = "https://www.ismaelan.com/2026/04/blog-post_7.html"
    for e in entries.values():
        if url in [l["href"] for l in e["link"]]:
            blog = e["content"]["$t"]
            break
    else:
        return None

    poet = read_body("_posts/2026-04-07-qing-chun-de-wu-yu.md")

    def norm(h):
        h = re.sub(r"<[^>]+>", "", h)
        h = h.replace("&nbsp;", "").replace("&mdash;", "—").replace("&amp;", "&")
        return re.sub(r"\s+", "", h)

    a, b = norm(poet), norm(blog)
    ratio = round(difflib.SequenceMatcher(None, a, b).ratio(), 4)
    return {"url": url, "identical": a == b, "ratio": ratio,
            "poet_len": len(a), "blog_len": len(b)}


def main():
    os.makedirs(OUT, exist_ok=True)
    links = []
    for fn, rel, title, date, oldpath in SRC_PAGES:
        body_html = read_body(rel)
        body = [
            "<p class=\"batchnav\"><a href=\"../index.html\">← 审阅总目录</a> "
            "<a href=\"index.html\">旧站页面</a></p>",
            f"<h1>{esc(title)}</h1>",
            "<div class=\"note\"><b>本页逐字取自旧站源码（"
            f"<code>{esc(rel)}</code>），未作任何改写。</b>"
            "旧站该页当前线上地址："
            f"<a href=\"https://poet.ismaelan.com{oldpath}\" rel=\"noopener\">"
            f"https://poet.ismaelan.com{oldpath}</a></div>",
            f"<p class=\"meta\">旧站日期 {esc(date) or '（无）'}　旧路径 {esc(oldpath)}</p>",
        ]
        if fn == "qing-chun-de-wu-yu.html":
            cmp = blog_version_of_qingchun()
            body.append("<div class=\"note\"><b>版本问题（需作者确认）：</b>"
                        "这首诗在<b>旧诗站</b>和<b>旧博客</b>各有一个版本。"
                        "两者正文（忽略空格与 Markdown 符号后）内容一致，"
                        "但旧诗站版本里残留了字面量的 <code>**</code>、<code>---</code> 等 "
                        "Markdown 符号（旧站渲染遗留），博客版本为干净 HTML。")
            if cmp:
                body.append(f"<p class=\"meta\">博客版本："
                            f"<a href=\"{esc(cmp['url'])}\" rel=\"noopener\">{esc(cmp['url'])}</a>　"
                            f"相似度 {cmp['ratio']}（归一化后{'完全一致' if cmp['identical'] else '有差异'}）</p>")
            body.append("请作者确认：新版应采用<b>哪个版本</b>？是否需要保留中英双语？</div>")
        body.append("<h2>旧站原文（逐字）</h2>")
        body.append(f"<div class=\"poem\">{body_html}</div>")
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as fh:
            fh.write(page(f"{title} · 旧站原文", "\n".join(body)))
        links.append((fn, title, oldpath))

    idx = ["<p class=\"batchnav\"><a href=\"../index.html\">← 审阅总目录</a></p>",
           "<h1>旧站现有页面（审阅）</h1>",
           "<div class=\"note\">这些页面<b>现在已在 poet.ismaelan.com 上线</b>。"
           "迁移到新版 Hugo 站点前，请作者确认它们是否保留、以及是否采用旧站版本。"
           "本站不擅自改动任何一首诗、题记或小传。</div>"]
    for fn, title, oldpath in links:
        idx.append(f"<div class=\"card\"><h3><a href=\"{fn}\">{esc(title)}</a></h3>"
                   f"<p class=\"meta\">旧路径 {esc(oldpath)}</p></div>")
    idx.append("<div class=\"note\"><b>迁移要点：</b>旧路径 "
               "<code>/na-la-ti/</code> 与 <code>/qing-chun-de-wu-yu/</code> "
               "在新站已保留为兼容页（不会 404），但其<b>正文是否搬入新版正式页面</b>，"
               "须由作者确认。确认前，新版对应页面只显示指向历史存档的说明。</div>")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page("旧站现有页面", "\n".join(idx)))

    print(f"oldsite review pages: {len(links)} + index -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
