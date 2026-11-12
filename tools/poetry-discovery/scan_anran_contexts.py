#!/usr/bin/env python3
"""Scan ALL 305 posts for 'An Ran' / 'by An Ran' occurrences and classify the
surrounding context: byline vs mention vs translation vs quote. Read-only."""
import re, importlib.util
from collections import Counter
spec = importlib.util.spec_from_file_location("bi", "tools/poetry-discovery/build_inventory.py")
bi = importlib.util.module_from_spec(spec); spec.loader.exec_module(bi)
ents = bi.load_entries(); ents.sort(key=lambda e: e['published']['$t'])

RX = re.compile(r'(?:by\s+)?an\s+ran', re.I)
BYRX = re.compile(r'by\s+an\s+ran', re.I)
TR_RX = re.compile(r'(translat|译|翻譯)', re.I)

total_hits = 0; posts_with = 0
by_ctx = Counter()
for e in ents:
    title = e['title']['$t']; plain = bi.strip_html(bi.get_content(e))
    hits = list(RX.finditer(plain)) + list(RX.finditer(title))
    if not hits: continue
    posts_with += 1
    for m in hits:
        total_hits += 1
        s = max(0, m.start()-45); en = min(len(plain), m.end()+45)
        ctx = plain[s:en].replace('\n',' ')
        # crude context classification
        if TR_RX.search(plain[max(0,m.start()-60):m.end()+60]):
            by_ctx['near translation word'] += 1
        elif BYRX.search(ctx):
            by_ctx['byline (by An Ran)'] += 1
        else:
            by_ctx['bare mention / other'] += 1
        if BYRX.search(ctx) is None:
            print(f"  [{'TITLE' if m.start()<len(title) else 'BODY'}] {e['published']['$t'][:10]} {title[:40]!r}\n      ...{ctx}...")

print(f"\nposts containing 'An Ran': {posts_with} / {len(ents)}")
print(f"total occurrences: {total_hits}")
print("context breakdown:", dict(by_ctx))
