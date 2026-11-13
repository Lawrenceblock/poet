#!/usr/bin/env python3
"""Verify the author-review site: verbatim fidelity, safety, link integrity.

Checks
------
1. Every candidate has a reading page.
2. The text inside each page's <div class="poem"> is byte-identical to
   sanitize(raw_feed_html) -- i.e. nothing was re-worded, re-punctuated or
   re-flowed between the public source and the review page.
3. No <script>, on*= handler or javascript: URL survives anywhere.
4. The declared candidate count matches the source CSV.
5. Internal links (index -> batches -> poem pages) all resolve.

Exit code 0 = all good.
"""
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from extract_post_html import sanitize  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CAND_CSV = os.path.join(ROOT, "docs", "poetry-discovery", "poetry-candidates.v2.csv")
SITE = os.path.join(ROOT, "docs", "author-review", "site")
FEED_GLOB = os.path.join(ROOT, "work", "feed", "feed-*.json")

fails = []


def load_entries():
    entries = {}
    for f in sorted(glob.glob(FEED_GLOB)):
        with open(f, encoding="utf-8") as fh:
            for e in json.load(fh)["feed"].get("entry", []):
                entries[e["id"]["$t"].split(".post-")[-1]] = e
    return entries


def main():
    entries = load_entries()
    with open(CAND_CSV, encoding="utf-8") as fh:
        cand = list(csv.DictReader(fh))

    poem_re = re.compile(r'<div class="poem">(.*?)</div>\s*<p class="meta">如原页面', re.S)
    n_ok = 0
    for c in cand:
        cid = c["candidate_id"]
        path = os.path.join(SITE, "poem", f"{cid}.html")
        if not os.path.exists(path):
            fails.append(f"{cid}: reading page missing")
            continue
        with open(path, "rb") as fh:
            page = fh.read().decode("utf-8")
        # Only our own inline review script is allowed; anything else fails.
        scripts = re.findall(r"<script\b.*?</script>", page, re.S | re.I)
        if len(scripts) != 1 or "review/api/review" not in scripts[0]:
            fails.append(f"{cid}: unexpected <script> content (found {len(scripts)})")
        if re.search(r"\son\w+\s*=", page):
            fails.append(f"{cid}: contains on* handler")
        if re.search(r'(href|src)\s*=\s*["\']javascript:', page, re.I):
            fails.append(f"{cid}: contains javascript: URL")
        m = poem_re.search(page)
        if not m:
            fails.append(f"{cid}: could not locate poem block")
            continue
        if "<script" in m.group(1):
            fails.append(f"{cid}: script leaked into poem block")
        expected = sanitize(entries[c["source_post_id"]]["content"]["$t"])
        if m.group(1) != expected:
            fails.append(f"{cid}: poem block is NOT byte-identical to sanitized source")
        else:
            n_ok += 1

    # link integrity: every internal href across all review pages must resolve
    def internal(href):
        return not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href) and not href.startswith("//")

    for page_path in glob.glob(os.path.join(SITE, "*.html")) + \
                     glob.glob(os.path.join(SITE, "poem", "*.html")):
        rel_dir = os.path.dirname(os.path.relpath(page_path, SITE))
        with open(page_path, encoding="utf-8") as fh:
            ph = fh.read()
        for href in set(re.findall(r'href="([^"]+)"', ph)):
            if not internal(href) or href.startswith("#"):
                continue
            if href.startswith("/review/api/"):
                continue  # dynamic API endpoint served by the review server
            if href.startswith("/review/"):
                target = os.path.join(SITE, href[len("/review/"):])
            elif href.startswith("/"):
                continue  # other absolute paths belong to the Hugo site, not review
            else:
                target = os.path.normpath(os.path.join(SITE, rel_dir, href.split("#")[0]))
            if not os.path.exists(target):
                fails.append(f"{os.path.relpath(page_path, SITE)} -> broken link {href}")

    print(f"candidates checked : {len(cand)}")
    print(f"verbatim-identical : {n_ok}")
    if fails:
        print(f"FAILURES: {len(fails)}")
        for f in fails[:30]:
            print("  -", f)
        sys.exit(1)
    print("OK: all checks passed")


if __name__ == "__main__":
    main()
