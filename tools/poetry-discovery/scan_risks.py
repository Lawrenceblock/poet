#!/usr/bin/env python3
"""Targeted false-positive risk scan for the broad 'An Ran' rule. Read-only."""
import re, importlib.util
spec = importlib.util.spec_from_file_location("bi", "tools/poetry-discovery/build_inventory.py")
bi = importlib.util.module_from_spec(spec); spec.loader.exec_module(bi)
ents = bi.load_entries(); ents.sort(key=lambda e: e['published']['$t'])

# Risk 1: "Translated by An Ran" / "trans. by An Ran" => 安然 is TRANSLATOR
R1 = re.compile(r'(translat\w*|trans\.)\s*(:)?\s*by\s+an\s+ran', re.I)
# Risk 2: bare mention of pen name in prose
R2 = re.compile(r'(pen\s*name|pseudonym)', re.I)

print("=== RISK 1: 'translated by An Ran' (translator, NOT author) ===")
found1 = 0
for e in ents:
    title = e['title']['$t']; plain = bi.strip_html(bi.get_content(e))
    for m in R1.finditer(plain):
        found1 += 1
        print(f"  {e['published']['$t'][:10]} {title[:45]!r}")
        print(f"     ctx: ...{plain[max(0,m.start()-50):m.end()+40]!r}...")
print(f"  total: {found1}")
print()
print("=== Posts mentioning 'An Ran' NOT as a 'by An Ran' byline, WITH a poetry signal ===")
RX = re.compile(r'an\s+ran', re.I); BY = re.compile(r'by\s+an\s+ran', re.I)
for e in ents:
    title = e['title']['$t']; labels = bi.get_labels(e); plain = bi.strip_html(bi.get_content(e))
    if not RX.search(plain): continue
    # is there a byline?
    has_byline = bool(BY.search(plain))
    if has_byline: continue
    cat, conf, reasons = bi.classify(title, labels, plain)
    print(f"  [{cat or '-'}] {e['published']['$t'][:10]} {title[:45]!r}")
    print(f"        labels={labels} url={bi.get_link(e)}")
    for m in RX.finditer(plain):
        print(f"        ctx: ...{plain[max(0,m.start()-40):m.end()+40]!r}...")
