#!/usr/bin/env python3
"""Build blog post inventory + poetry candidate detection from Blogger JSON feed.

Data source: Blogger public JSON feed
  https://www.ismaelan.com/feeds/posts/default?alt=json&max-results=150&start-index=N
All 305 posts retrieved with full HTML content (verified 2026-11-12).

Privacy: this script records metadata + short evidence excerpts only.
It does NOT write full poem bodies into any CSV.
"""
import json, re, html, csv, os, hashlib
from collections import Counter, OrderedDict

T = "$t"
OUT = "docs/poetry-discovery"

# ---------- feed loading ----------
def load_entries():
    """Load all work/feed-full-*.json pages (produced by fetch_feed.py).

    Auto-discovers pages instead of hardcoding start-index 1/151/301, so the
    pipeline still works if Blogger changes its page size.
    """
    import glob
    entries = []
    paths = sorted(glob.glob('work/feed-full-*.json'),
                   key=lambda p: int(re.search(r'-(\d+)\.json$', p).group(1)))
    if not paths:
        raise SystemExit(
            "No work/feed-full-*.json found. Run first:\n"
            "  python3 tools/poetry-discovery/fetch_feed.py\n"
            "(raw feed is not stored in git; see tools/poetry-discovery/README.md)")
    for p in paths:
        with open(p) as f:
            d = json.load(f)
        entries += d['feed'].get('entry', [])
    seen = OrderedDict()
    for e in entries:
        seen[e['id'][T]] = e
    return list(seen.values())

def get_link(e):
    for l in e.get('link', []):
        if l.get('rel') == 'alternate':
            return l['href']
    return ''

def get_labels(e):
    return [c['term'] for c in e.get('category', [])]

def get_content(e):
    return e.get('content', {}).get(T, '')

def strip_html(h):
    h = re.sub(r'<br\s*/?>', '\n', h, flags=re.I)
    h = re.sub(r'</p>', '\n', h, flags=re.I)
    h = re.sub(r'<[^>]+>', '', h)
    h = html.unescape(h)
    return h

def detect_lang(text):
    cjk = len(re.findall(r'[\u4e00-\u9fff]', text))
    latin = len(re.findall(r'[A-Za-z]', text))
    if cjk and latin and latin > 40:
        return 'zh+en'
    if cjk:
        return 'zh'
    if latin:
        return 'en'
    return 'unknown'

# ---------- poetry signal detection ----------
POETRY_TITLE_RE = re.compile(r'(诗|組詩|组诗|詩|歌|诗话|詩話|吟|谣|謠|赋|賦)')
POETRY_LABEL = '诗歌'
# known transl. / commentary signals
TRANSLATION_RE = re.compile(r'(译|譯|翻译|翻譯|试译|試譯|translat)', re.I)
# strong translator markers: author-as-translator phrases, not incidental "翻译" mentions
STRONG_TRANSLATION_RE = re.compile(
    r'(翻译\s*[:：]?\s*安然|安然\s*译|安然\s*翻譯|譯\s*[:：]?\s*安然'
    r'|作者\s*[:：]?\s*[^，。\n]{1,40}?(翻译|翻譯|譯|译)\s*[:：]?\s*安然)', re.I)
COMMENTARY_RE = re.compile(r'(诗话|詩話|创作谈|創作談|评论|評論|评析|詩論|诗论|译后|譯後|译序|譯序|序言|赏析|賞析|关于.*诗|談詩|谈诗)')
QUOTED_AUTHOR_RE = re.compile(r'(转载|轉載|摘自|引自|原作[:：]|原文作者)')
# explicit original-authorship markers for 安然
ORIGINAL_AUTHOR_RE = re.compile(
    r'(文\s*[/|｜]\s*安然|安然\s*[/|｜]\s*文|文/安然|作者\s*[:：]\s*安然'
    r'|[/|｜]\s*安然\s*$|by\s+an\s+ran|An\s+Ran)', re.I)
# translated-by markers (English side)
TRANSLATED_BY_RE = re.compile(r'Translated\s+by|trans\.\s*by', re.I)
# multi-poem markers
MULTI_POEM_RE = re.compile(r'(两首|二首|三首|组诗|組詩|外一首)')
# verse structure: many short lines
def verse_score(text):
    lines = [l.strip() for l in text.split('\n')]
    lines = [l for l in lines if l]
    if len(lines) < 4:
        return 0.0, 0
    short = sum(1 for l in lines if 0 < len(l) <= 30)
    return short / len(lines), len(lines)

def classify(title, labels, text):
    """Return (category, confidence, reasons). Category A/B/C/D/E or '' if not poetry.

    Categories (per task spec):
      A = 明确属于安然原创的诗歌 (explicit authorship evidence)
      B = 疑似安然原创的诗歌 (poetry present, authorship/boundary unclear)
      C = 翻译作品 (translation by 安然 of another poet's work)
      D = 诗歌评论、创作谈及相关论述
      E = 引用、转述或转载他人的诗歌
    """
    reasons = []
    has_label = POETRY_LABEL in labels
    title_hit = bool(POETRY_TITLE_RE.search(title))
    vs, nlines = verse_score(text)
    strong_translation = bool(STRONG_TRANSLATION_RE.search(text))
    translated_by = bool(TRANSLATED_BY_RE.search(text))
    original_marker = bool(ORIGINAL_AUTHOR_RE.search(text)) or bool(ORIGINAL_AUTHOR_RE.search(title))
    commentary = bool(COMMENTARY_RE.search(title))
    quoted = bool(QUOTED_AUTHOR_RE.search(text))
    multi = bool(MULTI_POEM_RE.search(title))

    poetry_signal = has_label or title_hit or (vs >= 0.6 and nlines >= 8)
    if not poetry_signal:
        return '', 0.0, []

    # D: poetics commentary / creative talk (takes priority)
    if commentary:
        return 'D', 0.6, ['commentary/poetics keyword in title']

    # C: explicit translation where 安然 is the translator (or English side says translated by)
    if strong_translation or (translated_by and not original_marker):
        r = []
        if strong_translation:
            r.append('安然-as-translator marker')
        if translated_by:
            r.append('"Translated by" marker')
        return 'C', 0.65, r

    # E: explicitly quoted / reposted other-author work
    if quoted and not original_marker:
        return 'E', 0.5, ['repost/quote marker without 安然 authorship']

    # A: explicit original-authorship evidence
    if original_marker:
        conf = 0.9 if (has_label or title_hit) else 0.8
        r = ['explicit 安然 authorship marker']
        if has_label:
            r.append('poetry label')
        if multi:
            r.append('multi-poem marker')
        return 'A', conf, r

    # A: strong combination (label + title keyword) even without signature
    if has_label and title_hit:
        return 'A', 0.8, ['poetry label + poetry title keyword']

    # B: poetry present but authorship/boundary not fully established
    if has_label and vs >= 0.5:
        return 'B', 0.6, ['poetry label + verse structure, no explicit authorship']
    if title_hit and vs >= 0.5:
        return 'B', 0.55, ['poetry title keyword + verse structure, no explicit authorship']
    if has_label:
        return 'B', 0.5, ['poetry label only, authorship not established']
    if vs >= 0.6 and nlines >= 8:
        return 'B', 0.45, ['verse structure only, no label/title/authorship']
    return 'B', 0.4, reasons or ['weak poetry signal']

def main():
    os.makedirs(OUT, exist_ok=True)
    ents = load_entries()
    ents.sort(key=lambda e: e['published'][T])

    inventory = []
    candidates = []
    cid = 0
    for e in ents:
        title = e['title'][T]
        pub = e['published'][T]
        url = get_link(e)
        labels = get_labels(e)
        content = get_content(e)
        plain = strip_html(content)
        lang = detect_lang(plain)
        accessible = bool(content.strip())
        cat, conf, reasons = classify(title, labels, plain)
        has_poetry = cat != ''

        inventory.append(OrderedDict([
            ('post_id', e['id'][T].split('post-')[-1]),
            ('title', title),
            ('published', pub),
            ('year', pub[:4]),
            ('url', url),
            ('labels', '|'.join(labels)),
            ('lang', lang),
            ('accessible', 'yes' if accessible else 'no'),
            ('full_text_read', 'yes' if accessible else 'no'),
            ('has_poetry', 'yes' if has_poetry else 'no'),
            ('category', cat),
            ('evidence', '; '.join(reasons)[:160]),
            ('verify_status', 'auto-detected, pending human review' if has_poetry else 'auto-scanned'),
            ('content_chars', len(plain)),
        ]))

        if has_poetry:
            cid += 1
            excerpt = ' '.join(plain.split())[:120]
            multi_flag = 'yes' if MULTI_POEM_RE.search(title) else 'no'
            note = excerpt
            if multi_flag == 'yes':
                note = 'MULTI-POEM post (title marker) - needs manual split into separate works. ' + note
            candidates.append(OrderedDict([
                ('candidate_id', f'C{cid:04d}'),
                ('work_title', title if POETRY_TITLE_RE.search(title) else ''),
                ('source_post_title', title),
                ('published', pub),
                ('source_url', url),
                ('category', cat),
                ('lang', lang),
                ('has_own_title', 'yes' if POETRY_TITLE_RE.search(title) else 'unknown'),
                ('full_text_present', 'yes' if accessible else 'no'),
                ('position_in_post', 'entire post (auto)'),
                ('multi_poem_flag', multi_flag),
                ('authorship_evidence', '; '.join(reasons)[:160]),
                ('labels', '|'.join(labels)),
                ('auto_basis', f'label={POETRY_LABEL in labels}; title_kw={bool(POETRY_TITLE_RE.search(title))}; verse={verse_score(plain)[0]:.2f}/lines={verse_score(plain)[1]}'),
                ('confidence', f'{conf:.2f}'),
                ('human_review', 'pending'),
                ('note', note),
            ]))

    with open(f'{OUT}/blog-post-inventory.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(inventory[0].keys()))
        w.writeheader(); w.writerows(inventory)

    with open(f'{OUT}/poetry-candidates.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(candidates[0].keys()))
        w.writeheader(); w.writerows(candidates)

    # stats
    cats = Counter(c['category'] for c in candidates)
    print(f"posts total: {len(inventory)}")
    print(f"accessible: {sum(1 for i in inventory if i['accessible']=='yes')}")
    print(f"with poetry: {len(candidates)}")
    print("categories:", dict(sorted(cats.items())))
    print("years of candidates:", dict(sorted(Counter(c['published'][:4] for c in candidates).items())))

if __name__ == '__main__':
    main()
