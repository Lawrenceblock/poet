#!/usr/bin/env python3
"""Build existing-site-comparison.csv: map the 3 posts on poet.ismaelan.com
against the blog inventory to detect duplicates and version differences."""
import csv, sys, re, os, json
sys.path.insert(0, 'work')
from build_inventory import load_entries, get_link, get_labels, get_content, strip_html, OUT

SITE = [
    # (site_url, site_file, title)
    ('/qing-chun-de-wu-yu/', '_posts/2026-04-07-qing-chun-de-wu-yu.md', '青春的物语'),
    ('/na-la-ti/',           '_posts/2026-09-07-na-la-ti.md',           '那拉提（未赴）'),
    ('/shi-ren-xiao-zhuan/', '_posts/2026-09-11-shi-ren-xiao-zhuan.md', '诗人小传'),
]

def body_of(path):
    t = open(os.path.join('poet', path), encoding='utf-8').read()
    m = re.match(r'^---\n.*?\n---\n', t, re.S)
    return t[m.end():] if m else t

def norm(s):
    s = strip_html(s)
    s = re.sub(r'\s+', '', s)
    return s

ents = load_entries()
rows = []
for url, path, title in SITE:
    site_body = body_of(path)
    nb = norm(site_body)
    match = None
    for e in ents:
        c = get_content(e)
        if norm(c) and (nb[:40] and nb[:40] in norm(c)):
            match = e
            break
    blog_url = get_link(match) if match else ''
    blog_date = match['published']['$t'][:10] if match else ''
    if match:
        blog_body = strip_html(get_content(match))
        same = 'identical (normalized)' if norm(blog_body) == nb else 'DIFFERS (normalized)'
        note = 'blog post found; manual version comparison required' if same.startswith('DIFFERS') else 'content matches blog (normalized)'
    else:
        same = 'no matching blog post found'
        note = 'post not located in blog by normalized prefix match'
    rows.append({
        'site_url': url,
        'site_file': path,
        'site_title': title,
        'blog_url': blog_url,
        'blog_date': blog_date,
        'duplicate': 'yes' if match else 'no',
        'version_diff': same,
        'url_mapping': f'{url}  <-  {blog_url}' if blog_url else 'unresolved',
        'needs_human_review': 'yes',
        'note': note,
    })

with open(f'{OUT}/existing-site-comparison.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

for r in rows:
    print(r['site_title'], '|', r['duplicate'], '|', r['version_diff'], '|', r['blog_url'])
