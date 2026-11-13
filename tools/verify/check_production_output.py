#!/usr/bin/env python3
"""Guard: a production build must never contain preview-only material.

The author-review reading pages (/review/, with the verbatim full text of the
137 candidates) are copied into the output only by tools/preview/build_preview.py.
A plain `hugo` build must not contain them, nor any other private artifact.

This is a safety net for the "review must never reach the public site" rule.
Note: Hugo's --cleanDestinationDir is a no-op in v0.168.0, so a production build
must start from a clean output directory (Vercel builds from a clean checkout,
where hugo/public is git-ignored, so it always does).

Usage:
    python3 tools/verify/check_production_output.py [--root hugo/public]

Exit code 0 = clean.
"""
import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Paths that must never appear in a production build.
FORBIDDEN = ["review", "docs", "work", "private"]
# Files/dirs that legitimately belong to the production output.
REQUIRED = ["index.html", "archive/index.html", "preface/index.html",
            "shi-ren-xiao-zhuan/index.html", "na-la-ti/index.html",
            "qing-chun-de-wu-yu/index.html", "style.css", "sitemap.xml",
            "robots.txt", "404.html"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(ROOT, "hugo", "public"))
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"no build output at {root}")
        return 1

    problems = []
    for name in FORBIDDEN:
        p = os.path.join(root, name)
        if os.path.exists(p):
            problems.append(f"FORBIDDEN in output: /{name}")
    for name in REQUIRED:
        if not os.path.isfile(os.path.join(root, name)):
            problems.append(f"MISSING required page: /{name}")

    # The review pages embed candidate text; scan for the marker just in case.
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith((".html", ".json")):
                with open(os.path.join(dirpath, name), encoding="utf-8",
                          errors="replace") as fh:
                    if "author-review" in fh.read():
                        problems.append(
                            f"review material leaked: {os.path.relpath(os.path.join(dirpath, name), root)}")

    if problems:
        print("PRODUCTION OUTPUT NOT CLEAN:")
        for p in sorted(set(problems)):
            print(f"  {p}")
        return 1
    print("PRODUCTION OUTPUT CLEAN: no /review/, no private material; "
          "all required pages present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
