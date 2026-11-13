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
    # Output directory. Default keeps the historical behaviour (hugo/public).
    # Pass --outdir to build an isolated preview (e.g. a visual-refinement
    # candidate) without touching the directory the running server serves.
    ap.add_argument("--outdir", default=PUBLIC)
    args = ap.parse_args()
    out = os.path.abspath(args.outdir)

    # Regenerate review pages so they always match the committed CSVs, and
    # verify verbatim fidelity before shipping them.
    subprocess.run([sys.executable,
                    os.path.join(ROOT, "tools", "author-review", "build_review_site.py")],
                   check=True, cwd=ROOT)
    subprocess.run([sys.executable,
                    os.path.join(ROOT, "tools", "author-review", "build_oldsite_review.py")],
                   check=True, cwd=ROOT)
    subprocess.run([sys.executable,
                    os.path.join(ROOT, "tools", "author-review", "verify_verbatim.py")],
                   check=True, cwd=ROOT)

    subprocess.run(["hugo", "--gc", "--minify", "--baseURL", args.baseurl,
                    "-d", out],
                   check=True, cwd=HUGO,
                   env={**os.environ, "HUGO_PARAMS_ENABLEREVIEW": "true"})

    # Sync the review pages into the preview tree WITHOUT ever removing the
    # live directory. A plain rmtree+copytree leaves a window in which every
    # /review/ URL 404s; copying file-by-file via a temp file + atomic replace
    # means a served page is always either the old or the new copy, never
    # missing. Stale files are pruned only after the new ones are in place.
    dst = os.path.join(out, "review")
    os.makedirs(dst, exist_ok=True)
    wanted = set()
    for root, _dirs, files in os.walk(REVIEW_SRC):
        rel = os.path.relpath(root, REVIEW_SRC)
        outdir = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(outdir, exist_ok=True)
        for name in files:
            src = os.path.join(root, name)
            tgt = os.path.join(outdir, name)
            wanted.add(os.path.relpath(tgt, dst))
            tmp = tgt + ".tmp"
            shutil.copy2(src, tmp)
            os.replace(tmp, tgt)
    for root, dirs, files in os.walk(dst, topdown=False):
        for name in files:
            full = os.path.join(root, name)
            if os.path.relpath(full, dst) not in wanted:
                os.unlink(full)
        for name in dirs:
            full = os.path.join(root, name)
            if not os.listdir(full):
                os.rmdir(full)

    n = len(os.listdir(os.path.join(dst, "poem")))
    print(f"preview built at {out}")
    print(f"  site  : {args.baseurl}")
    print(f"  review: {args.baseurl}review/  ({n} poem pages)")


if __name__ == "__main__":
    main()
