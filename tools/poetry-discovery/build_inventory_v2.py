#!/usr/bin/env python3
"""Phase 2: stricter authorship/translation rules (v2).

Does NOT overwrite the original CSVs. Writes NEW files:
  docs/poetry-discovery/blog-post-inventory.v2.csv
  docs/poetry-discovery/poetry-candidates.v2.csv
  docs/poetry-discovery/classification-diff-v1-v2.csv

v1 remains the frozen baseline (PR #2). See the Phase 2 review report.
"""
import re, csv, os
from collections import Counter, OrderedDict
import importlib.util

spec = importlib.util.spec_from_file_location("bi", "tools/poetry-discovery/build_inventory.py")
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)

OUT = "docs/poetry-discovery"

# ---- v2 stricter regexes -------------------------------------------------
# CJK byline: specific signature structures (NOT a bare name). Anchoring to a
# line start is deliberately NOT required, because Blogger's "##CONTINUE##"
# marker can be glued to the byline (e.g. "##CONTINUE##安然/文").
CJK_BYLINE = re.compile(
    r'(?:文|作者)[ \t]*[/|｜:：][ \t]*安然'
    r'|安然[ \t]*[/|｜][ \t]*文'
    r'|◎[ \t]*安然'
    r'|[/|｜][ \t]*安然[ \t]*(?=$|\n)', re.M)
# English byline with word boundaries; NOT the bare name.
EN_BYLINE = re.compile(r'(?<![A-Za-z])by[ \t]+An[ \t]+Ran(?![A-Za-z])', re.I)
# Translator markers: 安然 is the translator of ANOTHER author's work => category C.
# Colon is OPTIONAL (real text uses "翻译 安然" without a colon).
TRANSLATOR_MARK = re.compile(
    r'(?:translat\w*|trans\.)[ \t]*:?[ \t]*by[ \t]+An[ \t]+Ran'
    r'|安然[ \t]*[译譯]'
    r'|[译譯][ \t]*[:：]?[ \t]*安然'
    r'|(?:译者|譯者|翻译|翻譯)[ \t]*[:：]?[ \t]*安然', re.I)
# Title-level commentary / review markers (incl. AI review, English review).
REVIEW_TITLE = re.compile(
    r'(诗评|詩評|评论|評論|赏析|賞析|创作谈|創作談|诗话|詩話'
    r'|Poem\s*Review|Book\s*Review|\bReview\b|Critique)', re.I)
# In-body review / section markers (compound articles: poem + review).
REVIEW_BODY = re.compile(r'(AI\s*诗评|AI\s*詩評|诗评[:：]|詩評[:：]|Poem\s*Review)', re.I)


def classify_v2(title, labels, text):
    has_label = bi.POETRY_LABEL in labels
    title_hit = bool(bi.POETRY_TITLE_RE.search(title))
    vs, nlines = bi.verse_score(text)
    cjk_byline = bool(CJK_BYLINE.search(text))
    en_byline = bool(EN_BYLINE.search(text))
    translator = bool(TRANSLATOR_MARK.search(text))
    commentary_title = bool(bi.COMMENTARY_RE.search(title)) or bool(REVIEW_TITLE.search(title))
    quoted = bool(bi.QUOTED_AUTHOR_RE.search(text))
    multi = bool(bi.MULTI_POEM_RE.search(title))
    review_in_body = bool(REVIEW_BODY.search(text))

    poetry_signal = has_label or title_hit or (vs >= 0.6 and nlines >= 8)
    if not poetry_signal:
        return '', 0.0, []

    # D: commentary / review / poetics (title-level)
    if commentary_title:
        return 'D', 0.6, ['commentary/review keyword in title']

    # C: 安然 as translator (evaluated BEFORE author byline)
    if translator:
        return 'C', 0.7, ['安然-as-translator marker']

    # E: quoted/reposted other-author work with no byline
    if quoted and not (cjk_byline or en_byline):
        return 'E', 0.5, ['repost/quote marker without 安然 byline']

    # A: explicit anchored byline (NOT bare name)
    if cjk_byline or en_byline:
        r = ['explicit 安然 byline']
        if has_label:
            r.append('poetry label')
        if multi:
            r.append('multi-poem marker')
        if review_in_body:
            r.append('compound: review section present')
        conf = 0.9 if (has_label or title_hit) else 0.85
        return 'A', conf, r

    # A: poetry label + poetry title keyword (no byline) — kept, but flagged
    if has_label and title_hit:
        return 'A', 0.7, ['poetry label + poetry title keyword (NO byline)']

    # B: everything else with a poetry signal
    if has_label and vs >= 0.5:
        return 'B', 0.6, ['poetry label + verse structure, no explicit byline']
    if title_hit and vs >= 0.5:
        return 'B', 0.55, ['poetry title keyword + verse structure, no explicit byline']
    if has_label:
        return 'B', 0.5, ['poetry label only, authorship not established']
    if vs >= 0.6 and nlines >= 8:
        return 'B', 0.45, ['verse structure only, no label/title/byline']
    return 'B', 0.4, ['weak poetry signal']


def main():
    os.makedirs(OUT, exist_ok=True)
    ents = bi.load_entries()
    ents.sort(key=lambda e: e['published']['$t'])
    inventory, candidates, diffs = [], [], []
    cid = 0
    for e in ents:
        title = e['title']['$t']
        pub = e['published']['$t']
        url = bi.get_link(e)
        labels = bi.get_labels(e)
        plain = bi.strip_html(bi.get_content(e))
        lang = bi.detect_lang(plain)
        cat1, conf1, r1 = bi.classify(title, labels, plain)
        cat2, conf2, r2 = classify_v2(title, labels, plain)
        vs, nl = bi.verse_score(plain)
        inventory.append(OrderedDict([
            ('post_id', e['id']['$t'].split('post-')[-1]),
            ('title', title), ('published', pub), ('year', pub[:4]), ('url', url),
            ('labels', '|'.join(labels)), ('lang', lang),
            ('accessible', 'yes' if plain.strip() else 'no'),
            ('has_poetry_v1', 'yes' if cat1 else 'no'), ('category_v1', cat1),
            ('has_poetry_v2', 'yes' if cat2 else 'no'), ('category_v2', cat2),
            ('content_chars', len(plain)),
        ]))
        if cat2:
            cid += 1
            excerpt = ' '.join(plain.split())[:120]
            multi = 'yes' if bi.MULTI_POEM_RE.search(title) else 'no'
            note = excerpt
            if multi == 'yes':
                note = 'MULTI-POEM post (title marker) - needs manual split. ' + note
            if cat2 == 'A' and 'NO byline' in ' '.join(r2):
                note = 'NO BYLINE: attributed by label+title only. ' + note
            candidates.append(OrderedDict([
                ('candidate_id', f'C{cid:04d}'),
                ('work_title', title if bi.POETRY_TITLE_RE.search(title) else ''),
                ('source_post_title', title), ('published', pub), ('source_url', url),
                ('category', cat2), ('lang', lang),
                ('has_own_title', 'yes' if bi.POETRY_TITLE_RE.search(title) else 'unknown'),
                ('full_text_present', 'yes' if plain.strip() else 'no'),
                ('position_in_post', 'entire post (auto)'),
                ('multi_poem_flag', multi),
                ('authorship_evidence', '; '.join(r2)[:160]),
                ('labels', '|'.join(labels)),
                ('auto_basis', f'label={bi.POETRY_LABEL in labels}; '
                               f'title_kw={bool(bi.POETRY_TITLE_RE.search(title))}; '
                               f'verse={vs:.2f}/lines={nl}'),
                ('confidence', f'{conf2:.2f}'),
                ('human_review', 'pending'),
                ('note', note),
            ]))
        if cat1 != cat2:
            diffs.append(OrderedDict([
                ('post_title', title), ('published', pub[:10]), ('url', url),
                ('category_v1', cat1 or '(none)'), ('category_v2', cat2 or '(none)'),
                ('reason_v2', '; '.join(r2)[:160]),
            ]))

    def w(path, rows):
        with open(path, 'w', newline='', encoding='utf-8') as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            wr.writeheader()
            wr.writerows(rows)

    w(f'{OUT}/blog-post-inventory.v2.csv', inventory)
    w(f'{OUT}/poetry-candidates.v2.csv', candidates)
    if diffs:
        w(f'{OUT}/classification-diff-v1-v2.csv', diffs)
    else:
        open(f'{OUT}/classification-diff-v1-v2.csv', 'w').write(
            'post_title,published,url,category_v1,category_v2,reason_v2\n')

    c1 = Counter(i['category_v1'] for i in inventory if i['category_v1'])
    c2 = Counter(i['category_v2'] for i in inventory if i['category_v2'])
    print("v1 categories:", dict(sorted(c1.items())))
    print("v2 categories:", dict(sorted(c2.items())))
    print("v1 candidates:", sum(c1.values()), " v2 candidates:", sum(c2.values()))
    print("changed rows:", len(diffs))
    for d in diffs:
        print(f"   {d['published']} {d['category_v1']:>7} -> {d['category_v2']:<7} "
              f"{d['post_title'][:45]!r}")


if __name__ == '__main__':
    main()
