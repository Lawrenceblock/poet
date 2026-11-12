#!/usr/bin/env python3
"""Phase 2: extract representative risk samples for the review report. Read-only."""
import re, importlib.util
spec = importlib.util.spec_from_file_location("bi", "tools/poetry-discovery/build_inventory.py")
bi = importlib.util.module_from_spec(spec); spec.loader.exec_module(bi)
ents = {bi.get_link(e): e for e in bi.load_entries()}

def show(url, note):
    e = ents.get(url)
    if not e: 
        print("  (not found)", url); return
    title = e['title']['$t']; plain = bi.strip_html(bi.get_content(e))
    print(f"\n[{note}] {e['published']['$t'][:10]} {title[:50]!r}")
    print(f"   labels={bi.get_labels(e)}")
    for rx in [r'文/安然', r'安然/文', r'安然[ \t]*[/|｜][ \t]*文', r'by[ \t]+An[ \t]+Ran',
               r'[译譯][ \t]*[:：]?[ \t]*安然', r'An[ \t]+Ran']:
        for m in re.finditer(rx, plain, re.I):
            print(f"   [{rx}] ...{plain[max(0,m.start()-25):m.end()+25]!r}...")

show('https://www.ismaelan.com/2008/09/blog-post_14.html', 'B->A fixed: 安然/文 byline + 诗歌 label')
show('https://www.ismaelan.com/2008/10/blog-post_02.html', 'A->B fixed: 安然 only in title, no body byline')
show('https://www.ismaelan.com/2015/11/poets-speak-out-for-refugees-no-one.html', 'C: translator 安然 (author Warsan Shire)')
show('https://www.ismaelan.com/2018/05/blog-post_31.html', 'A: author 安然, translator Hendan (reverse case)')
show('https://www.ismaelan.com/2010/01/2009.html', 'A-flagged: label+title, NO byline')
show('https://www.ismaelan.com/2012/06/blog-post_7583.html', 'A-flagged: label+title, NO byline (short news post)')
show('https://www.ismaelan.com/2025/05/blog-post_8.html', 'A-flagged: compound poem+review+translation')
