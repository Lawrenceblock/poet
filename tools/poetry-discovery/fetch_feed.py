#!/usr/bin/env python3
"""Fetch the public Blogger feed + sitemap for https://www.ismaelan.com/.

This is the ONLY network step needed to reproduce the poetry census. It writes
raw JSON/XML into work/ (NOT committed to git - see README.md). It fetches
metadata + post HTML exactly as Blogger serves it publicly.

Usage:
    python3 tools/poetry-discovery/fetch_feed.py [--outdir work]

Reproducibility notes:
  * Blogger caps max-results at 500, but a single page can be truncated, so we
    page in blocks of 150 (start-index 1, 151, 301, ...) until no entries remain.
  * We also fetch sitemap.xml as an INDEPENDENT count cross-check.
  * No authentication is used; this only reads public content.
"""
import argparse, hashlib, json, os, sys, time, urllib.request

SITE = "https://www.ismaelan.com"
FEED = SITE + "/feeds/posts/default?alt=json&max-results={n}&start-index={s}"
SITEMAP = SITE + "/sitemap.xml"
UA = "poetry-discovery-census/1.0 (+read-only; contact: repo owner)"


def get(url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if attempt == retries:
                raise
            print(f"  retry {attempt}/{retries} after error: {e}", file=sys.stderr)
            time.sleep(2 * attempt)


def fetch_feed(outdir, page=150):
    os.makedirs(outdir, exist_ok=True)
    start = 1
    total = None
    files = []
    while True:
        url = FEED.format(n=page, s=start)
        raw = get(url)
        data = json.loads(raw)
        feed = data["feed"]
        if total is None:
            total = int(feed["openSearch$totalResults"]["$t"])
            print(f"Blogger reports totalResults = {total}")
        entries = feed.get("entry", [])
        path = os.path.join(outdir, f"feed-full-{start}.json")
        with open(path, "wb") as f:
            f.write(raw)
        sha = hashlib.sha256(raw).hexdigest()
        files.append((path, len(raw), sha, len(entries)))
        print(f"  wrote {path}  entries={len(entries)}  bytes={len(raw)}  sha256={sha[:16]}")
        if len(entries) == 0:
            break
        start += page
        if start > total + page:
            break
    return files, total


def fetch_sitemap(outdir):
    os.makedirs(outdir, exist_ok=True)
    raw = get(SITEMAP)
    path = os.path.join(outdir, "sitemap.xml")
    with open(path, "wb") as f:
        f.write(raw)
    n = raw.count(b"<loc>")
    sha = hashlib.sha256(raw).hexdigest()
    print(f"  wrote {path}  <loc> count={n}  sha256={sha[:16]}")
    return path, n, sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="work")
    args = ap.parse_args()

    print("=== fetching Blogger JSON feed (paged) ===")
    files, total = fetch_feed(args.outdir)
    print("=== fetching sitemap.xml ===")
    _, loc_count, _ = fetch_sitemap(args.outdir)

    n_entries = sum(f[3] for f in files)
    print()
    print(f"feed pages: {len(files)}   total entries fetched: {n_entries}")
    print(f"Blogger totalResults: {total}   sitemap <loc>: {loc_count}")
    if n_entries == total == loc_count:
        print("OK: feed entries == totalResults == sitemap <loc> (cross-check passed)")
    else:
        print("WARN: counts differ - inspect before trusting the census")
    print()
    print("Next: python3 tools/poetry-discovery/build_inventory.py  (writes CSVs)")


if __name__ == "__main__":
    main()
