#!/usr/bin/env python3
"""Rebuild the review snapshot + exports from the append-only journal.

Use after restoring review-records/journal.jsonl from a backup.

  python3 tools/review/rebuild_snapshot.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store  # noqa: E402


def main():
    state = store.rebuild()
    p = store.progress()
    print(f"records: {len(state)}")
    print(f"progress: {p['reviewed']}/{p['total']} reviewed "
          f"(keep={p['by_status']['keep']} hold={p['by_status']['hold']} "
          f"exclude={p['by_status']['exclude']} pending={p['by_status']['pending']})")
    print(f"snapshot: {store.SNAPSHOT}")
    print(f"export  : {store.EXPORT_CSV}")
    print(f"export  : {store.EXPORT_JSON}")


if __name__ == "__main__":
    main()
