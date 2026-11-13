#!/usr/bin/env python3
"""Detect real substring false positives: bare 'An Ran' matching inside a larger
English word (no word boundary), in the actual 305 posts. Read-only."""
import re, importlib.util
spec = importlib.util.spec_from_file_location("bi", "tools/poetry-discovery/build_inventory.py")
bi = importlib.util.module_from_spec(spec); spec.loader.exec_module(bi)
ents = bi.load_entries(); ents.sort(key=lambda e: e['published']['$t'])

# bare, case-insensitive, no boundary (as in current script)
BARE = re.compile(r'An\s+Ran', re.I)
# boundary-anchored version
BARE_B = re.compile(r'(?<![A-Za-z])An\s+Ran(?![A-Za-z])', re.I)

fp_posts = []
for e in ents:
    title = e['title']['$t']; plain = bi.strip_html(bi.get_content(e))
    text = title + '\n' + plain
    loose = list(BARE.finditer(text))
    strict = list(BARE_B.finditer(text))
    if len(loose) > len(strict):
        fp_posts.append((e, loose, strict))
        for m in loose:
            seg = text[max(0,m.start()-15):m.end()+15]
            if not BARE_B.match(m.group(0)):
                pass
        print(f"FP CANDIDATE: {e['published']['$t'][:10]} {title[:50]!r}")
        for m in loose:
            print(f"    loose: ...{text[max(0,m.start()-20):m.end()+20]!r}...")
        for m in strict:
            print(f"    strict: ...{text[max(0,m.start()-20):m.end()+20]!r}...")
        print()
print(f"posts with substring-only 'An Ran' matches: {len(fp_posts)}")
