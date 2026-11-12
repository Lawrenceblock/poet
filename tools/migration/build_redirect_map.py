#!/usr/bin/env python3
"""Build the old-blog -> new-site URL mapping for the 305 archived posts.

Rationale
---------
The old blog lives at https://www.ismaelan.com/YYYY/MM/<slug>.html (Blogger).
The new Hugo site uses permalink "/:year/:month/:slug/" for the `posts`
section. Therefore, when a post keeps its Blogger slug, the new URL is exactly
the old URL with the trailing ".html" removed.

This script proves that mapping is (a) one-to-one and (b) collision-free, and
writes it to docs/migration/ for the record. It is read-only w.r.t. the source
inventory and writes only the mapping CSV.

Cross-domain caveat
-------------------
Old links live on www.ismaelan.com, new links on poet.ismaelan.com. A 301 from
the old host must be served BY the old host (Blogger/other), not by the new
site. The CSV records the intended mapping; implementing the redirect on the
old host is a separate, explicitly-authorized step.
"""
import csv
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INV = os.path.join(ROOT, "docs", "poetry-discovery", "blog-post-inventory.v2.csv")
OUT = os.path.join(ROOT, "docs", "migration", "legacy-url-redirect-map.csv")

OLD_HOST = "https://www.ismaelan.com"
NEW_HOST = "https://poet.ismaelan.com"


def new_url(old_url):
    path = old_url.replace(OLD_HOST, "")
    if path.endswith(".html"):
        path = path[:-5]
    if not path.endswith("/"):
        path += "/"
    return NEW_HOST + path


def main():
    with open(INV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    seen_new = {}
    seen_old = set()
    out = []
    for r in rows:
        old = r["url"].strip()
        if not old.startswith("http"):
            old = OLD_HOST + "/" + old.lstrip("/")
        seen_old.add(old)
        n = new_url(old)
        seen_new.setdefault(n, old)
        out.append({
            "post_id": r["post_id"],
            "published": r["published"][:10],
            "title": r["title"],
            "old_url": old,
            "new_url": n,
            "status": "proposed",
            "notes": "new = old minus .html (slug preserved); redirect must be served by old host",
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["post_id", "published", "title",
                                           "old_url", "new_url", "status", "notes"])
        w.writeheader()
        w.writerows(out)

    uniq_new = len(set(x["new_url"] for x in out))
    print(f"posts           : {len(out)}")
    print(f"distinct old URL: {len(seen_old)}")
    print(f"distinct new URL: {uniq_new}")
    print(f"collisions      : {len(out) - uniq_new}")
    print(f"written         : {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
