#!/usr/bin/env python3
"""Build the full PREVIEW bundle: Hugo site + author-review reading pages.

The review pages (docs/author-review/site/) contain the verbatim full text of
the 137 candidates. They are intentionally NOT part of the Hugo build, so a
normal production build never publishes unconfirmed works. This script copies
them into the preview output under /review/ only.

Usage:
    python3 tools/preview/build_preview.py [--baseurl URL]
"""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HUGO = os.path.join(ROOT, "hugo")
REVIEW_SRC = os.path.join(ROOT, "docs", "author-review", "site")
PUBLIC = os.path.join(HUGO, "public")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseurl",
                    default="https://work-1-koykqjjrzyyvyosg.prod-runtime.all-hands.dev/")
    args = ap.parse_args()

    # Regenerate review pages so they always match the committed CSVs, and
    # verify verbatim fidelity before shipping them.
    subprocess.run([sys.executable,
                    os.path.join(ROOT, "tools", "author-review", "build_review_site.py")],
                   check=True, cwd=ROOT)
    subprocess.run([sys.executable,
                    os.path.join(ROOT, "tools", "author-review", "verify_verbatim.py")],
                   check=True, cwd=ROOT)

    subprocess.run(["hugo", "--gc", "--minify", "--baseURL", args.baseurl],
                   check=True, cwd=HUGO,
                   env={**os.environ, "HUGO_PARAMS_ENABLEREVIEW": "true"})

    dst = os.path.join(PUBLIC, "review")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(REVIEW_SRC, dst)

    n = len(os.listdir(os.path.join(dst, "poem")))
    print(f"preview built at {PUBLIC}")
    print(f"  site  : {args.baseurl}")
    print(f"  review: {args.baseurl}review/  ({n} poem pages)")


if __name__ == "__main__":
    main()
