#!/usr/bin/env python3
"""Archive the legacy Jekyll site into hugo/static/legacy/ as a self-contained
historical snapshot.

Design
------
* Source HTML is fetched verbatim from the live legacy site (read-only) and
  stored under work/legacy/ (gitignored).
* The ONLY edits applied to the archived pages are PATH rewrites so the
  snapshot is self-contained under /legacy/:
      /style.css              -> style.css
      /archive/               -> archive.html
      /preface/               -> preface.html
      /shi-ren-xiao-zhuan/    -> shi-ren-xiao-zhuan.html
      /na-la-ti/              -> na-la-ti.html
      /qing-chun-de-wu-yu/    -> qing-chun-de-wu-yu.html
  No text, punctuation, layout or literary content is changed.
* An external link to bio.ismaelan.com is left untouched (separate site).
* A noindex marker is injected so the archive is preserved for humans but not
  indexed as fresh content (avoids competing with the new site).

Usage:  python3 tools/legacy/archive_legacy_site.py
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "work", "legacy")
DST = os.path.join(ROOT, "hugo", "static", "legacy")

PAGES = {
    "index.html": "/",
    "archive.html": "/archive/",
    "preface.html": "/preface/",
    "shi-ren-xiao-zhuan.html": "/shi-ren-xiao-zhuan/",
    "na-la-ti.html": "/na-la-ti/",
    "qing-chun-de-wu-yu.html": "/qing-chun-de-wu-yu/",
}

REWRITES = [
    ('href="/style.css"', 'href="style.css"'),
    ('href="/archive/"', 'href="archive.html"'),
    ('href="/preface/"', 'href="preface.html"'),
    ('href="/shi-ren-xiao-zhuan/"', 'href="shi-ren-xiao-zhuan.html"'),
    ('href="/na-la-ti/"', 'href="na-la-ti.html"'),
    ('href="/qing-chun-de-wu-yu/"', 'href="qing-chun-de-wu-yu.html"'),
]

NOINDEX = ('<meta name="robots" content="noindex,nofollow">'
           '<meta name="description" content="安然诗客栈旧版网站历史存档（只读）。">')

# Old flat URLs whose real content has NOT yet been confirmed for the new site.
# We keep them alive with a clearly-labelled redirect to the archived original,
# so no existing link 404s. Replace with a real page once the author confirms.
REDIRECTS = {
    "na-la-ti": ("那拉提（未赴）", "/legacy/na-la-ti.html"),
    "qing-chun-de-wu-yu": ("青春的物语", "/legacy/qing-chun-de-wu-yu.html"),
}

REDIRECT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="refresh" content="0; url={target}">
<title>{title} · 安然诗歌档案</title>
<style>body{{font-family:"Noto Serif SC","Songti SC",serif;background:#faf7f2;
color:#23201c;line-height:1.9;max-width:620px;margin:12vh auto;padding:0 22px}}
a{{color:#8a5a2b}}</style>
</head>
<body>
<p>旧链接 <code>/{slug}/</code> 对应的作品尚未经作者确认收入新版站点。</p>
<p>原文已只读保存于历史存档：<a href="{target}">{target}</a></p>
<p><small>本页仅为链接兼容占位，内容不参与新站展示。</small></p>
</body>
</html>
"""


def rewrite(html):
    for a, b in REWRITES:
        html = html.replace(a, b)
    return html


def inject_noindex(html):
    if "<head>" in html:
        return html.replace("<head>", "<head>" + NOINDEX, 1)
    if "<head " in html:
        return re.sub(r"(<head[^>]*>)", r"\1" + NOINDEX, html, count=1)
    return NOINDEX + html


def main():
    os.makedirs(DST, exist_ok=True)
    report = []
    for fn, live in PAGES.items():
        src = os.path.join(SRC, fn)
        if not os.path.exists(src):
            raise SystemExit(f"missing source page: {src} (fetch it first)")
        with open(src, encoding="utf-8") as fh:
            original = fh.read()
        out = inject_noindex(rewrite(original))
        with open(os.path.join(DST, fn), "w", encoding="utf-8") as fh:
            fh.write(out)
        changed = sum(1 for a, b in REWRITES if a in original)
        report.append((fn, live, changed))

    shutil.copy2(os.path.join(SRC, "style.css"), os.path.join(DST, "style.css"))
    img_dir = os.path.join(DST, "assets", "img")
    os.makedirs(img_dir, exist_ok=True)
    shutil.copy2(os.path.join(SRC, "assets", "img", "cover.png"),
                 os.path.join(img_dir, "cover.png"))

    # Old-URL compatibility stubs (so existing flat links never 404).
    for slug, (title, target) in REDIRECTS.items():
        d = os.path.join(ROOT, "hugo", "static", slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(REDIRECT_HTML.format(slug=slug, title=title, target=target))

    # Keep the old stylesheet reachable at /style.css (audit item P2).
    shutil.copy2(os.path.join(SRC, "style.css"),
                 os.path.join(ROOT, "hugo", "static", "style.css"))

    for fn, live, changed in report:
        print(f"  {fn:26s} <- {live:24s} rewrites={changed}")
    print(f"  compat stubs: {', '.join('/' + s + '/' for s in REDIRECTS)}")
    print(f"archive written to {os.path.relpath(DST, ROOT)}")


if __name__ == "__main__":
    main()
