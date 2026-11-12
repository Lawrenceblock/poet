#!/usr/bin/env python3
"""Phase 2 analysis: which A-class candidates are triggered by the overly broad
ORIGINAL_AUTHOR_RE sub-patterns, especially bare 'An Ran'.

Read-only analysis. Does NOT write CSVs. Reuses build_inventory helpers.
"""
import re, sys, os, importlib.util

spec = importlib.util.spec_from_file_location("bi", "tools/poetry-discovery/build_inventory.py")
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)

SUBPATTERNS = {
    'wen_slash_anran':  r'文\s*[/|｜]\s*安然',
    'anran_slash_wen':  r'安然\s*[/|｜]\s*文',
    'wen_anran_lit':    r'文/安然',
    'author_anran':     r'作者\s*[:：]\s*安然',
    'slash_anran_eol':  r'[/|｜]\s*安然\s*$',
    'by_an_ran':        r'by\s+an\s+ran',
    'an_ran_bare':      r'An\s+Ran',
}
COMPILED = {k: re.compile(v, re.I | re.M) for k, v in SUBPATTERNS.items()}

ents = bi.load_entries()
ents.sort(key=lambda e: e['published']['$t'])

rows = []
for e in ents:
    title = e['title']['$t']
    labels = bi.get_labels(e)
    plain = bi.strip_html(bi.get_content(e))
    cat, conf, reasons = bi.classify(title, labels, plain)
    if cat != 'A':
        continue
    text = plain
    hits = {}
    for name, rx in COMPILED.items():
        m = rx.search(text) or rx.search(title)
        if m:
            hits[name] = m
    matched = sorted(hits.keys())
    def ctx(m):
        s = max(0, m.start()-25); en = min(len(text), m.end()+25)
        return text[s:en].replace('\n', ' ')
    rows.append({
        'title': title, 'url': bi.get_link(e), 'pub': e['published']['$t'][:10],
        'labels': labels, 'matched': matched,
        'ctx_bare': ctx(hits['an_ran_bare']) if 'an_ran_bare' in hits else '',
        'ctx_by': ctx(hits['by_an_ran']) if 'by_an_ran' in hits else '',
    })

print("A-class total:", len(rows))
only_bare = [r for r in rows if set(r['matched']) <= {'an_ran_bare'}]
only_by_or_bare = [r for r in rows if set(r['matched']) <= {'an_ran_bare', 'by_an_ran'}]
has_bare = [r for r in rows if 'an_ran_bare' in r['matched']]
has_by = [r for r in rows if 'by_an_ran' in r['matched']]

print("A rows triggered by bare 'An Ran':", len(has_bare))
print("A rows triggered by 'by An Ran':", len(has_by))
print("A rows whose ONLY evidence is bare 'An Ran':", len(only_bare))
print("A rows whose ONLY evidence is 'An Ran' and/or 'by An Ran':", len(only_by_or_bare))
print()
print("=== A rows where bare 'An Ran' is the ONLY evidence ===")
for r in only_bare:
    print(f"- {r['pub']} {r['title']!r}\n    url: {r['url']}\n    ctx: {r['ctx_bare']!r}")
print()
print("=== A rows where 'An Ran' appears (incl. alongside other markers) ===")
for r in has_bare:
    print(f"- {r['pub']} {r['title']!r} matched={r['matched']}\n    ctx_bare: {r['ctx_bare']!r}")
