import json, re, sys
sys.path.insert(0, 'work')
from build_inventory import load_entries, get_link, get_labels, get_content, strip_html

ents = load_entries()
ents.sort(key=lambda e: e['published']['$t'])

CLUES = ['一篇诗话', '放牧的星星', '做啥呢', '今夜，所有切糕都死于沉默',
         '我是一个中国人', '要像一棵空乏的麦秸', '古典的雨滴', 'Home',
         '雅玛立克山', '那拉提', '青春的物语', '诗人小传', 'So, You Are Still Here']

for clue in CLUES:
    hits = []
    for e in ents:
        t = e['title']['$t']
        if clue in t:
            hits.append((e['published']['$t'][:10], t, get_link(e), get_labels(e)))
    print(f"--- clue {clue!r}: {len(hits)} title hit(s)")
    for h in hits:
        print("     ", h)

# search content for refugee / Warsan Shire / Home translation
print("\n=== content search: Warsan / 难民 / Shire ===")
for e in ents:
    c = strip_html(get_content(e))
    if re.search(r'Warsan|Shire|难民', c, re.I):
        print(e['published']['$t'][:10], '|', e['title']['$t'], '|', get_link(e))
