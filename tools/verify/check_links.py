#!/usr/bin/env python3
"""Check every internal link in the built site (read-only).

Walks hugo/public, extracts href/src from every HTML file and verifies each
internal target resolves to a file that actually exists in the output. External
links (http/https/mailto/tel/data) and pure fragments are skipped.

Usage:
    python3 tools/verify/check_links.py [--root hugo/public] [--json out.json]

Exit code 0 = no broken internal links.
"""
import argparse
import html.parser
import json
import os
import re
import sys
from urllib.parse import urlsplit, unquote

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class LinkExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("href", "src") and v:
                self.links.append(v)

    handle_startendtag = handle_starttag


def resolve(base_path, link):
    """Return the URL path a link points at, or None if it is external."""
    link = link.strip()
    if not link or link.startswith("#"):
        return None
    low = link.lower()
    if low.startswith(("http://", "https://", "mailto:", "tel:", "data:",
                       "javascript:", "//")):
        return None
    sp = urlsplit(link)
    path = unquote(sp.path)
    if not path:
        return None
    if path.startswith("/"):
        return path
    base_dir = os.path.dirname(base_path)
    return os.path.normpath(os.path.join(base_dir, path)).replace(os.sep, "/")


def target_exists(root, url_path):
    rel = url_path.lstrip("/")
    cand = os.path.join(root, rel)
    if url_path.endswith("/"):
        return os.path.isfile(os.path.join(cand, "index.html"))
    if os.path.isfile(cand):
        return True
    if os.path.isfile(cand + ".html"):
        return True
    if os.path.isfile(os.path.join(cand, "index.html")):
        return True
    return False


def is_runtime_endpoint(url_path):
    # /api/... targets are served by the review server at run time, not by a
    # static file, so they are not "broken" when absent from the output tree.
    return "/api/" in url_path or url_path.endswith("/api")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(ROOT, "hugo", "public"))
    ap.add_argument("--json")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    pages = 0
    checked = 0
    runtime = 0
    broken = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not name.endswith(".html"):
                continue
            full = os.path.join(dirpath, name)
            url_path = "/" + os.path.relpath(full, root).replace(os.sep, "/")
            if url_path.endswith("/index.html"):
                url_path = url_path[:-len("index.html")]
            pages += 1
            with open(full, encoding="utf-8", errors="replace") as fh:
                p = LinkExtractor()
                p.feed(fh.read())
            for link in p.links:
                target = resolve(url_path, link)
                if target is None:
                    continue
                if is_runtime_endpoint(target):
                    runtime += 1
                    continue
                checked += 1
                if not target_exists(root, target):
                    broken.append({"page": url_path, "link": link,
                                   "resolved": target})

    print(f"pages scanned   : {pages}")
    print(f"internal links  : {checked}")
    print(f"runtime /api/   : {runtime}")
    print(f"broken          : {len(broken)}")
    for b in broken[:40]:
        print(f"  {b['page']}  ->  {b['link']}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"pages": pages, "links": checked, "runtime": runtime,
                       "broken": broken}, fh, ensure_ascii=False, indent=1)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
