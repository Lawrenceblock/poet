#!/usr/bin/env python3
"""Derive the canonical, task-spec review ledger: review-records/decisions.jsonl.

`journal.jsonl` stays the authoritative, append-only log written by
`store.save()`. This module projects it into a stable, self-describing line
format (one JSON object per candidate) so the author's decisions can be
exported, backed up, audited and re-imported independently of the web UI.

Schema per line (task-spec fields first):

  candidate_id     C#### (stable, matches docs/poetry-discovery/poetry-candidates.v2.csv)
  source_post_id   original Blogger post id
  source_url       original post URL (authoritative text source)
  title            current title (candidate_title, else source_post_title)
  decision         pending | keep | reject | reclassify | version_check | deferred
  reviewed_at      ISO-8601 (Beijing time) of the last save, "" if never reviewed
  record_source    where the decision came from (journal.jsonl, or a recovery tag)
  notes            the author's own comment (verbatim)

Extra fields kept for fidelity/auditing: status, nature, rev, reviewer.

`decision` is a *projection* of the UI status, so the web UI, its API and the
save logic are unchanged:
  pending -> pending, keep -> keep, hold -> deferred, exclude -> reject.
`reclassify` / `version_check` are reserved for the review UI's nature/comment
flags and are not emitted by the current UI; they are accepted on import.

Nothing here writes to poem text, the feed, or the candidate CSVs.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import store  # noqa: E402

DECISIONS = os.path.join(store.RECORDS, "decisions.jsonl")

STATUS_TO_DECISION = {
    "pending": "pending",
    "keep": "keep",
    "hold": "deferred",
    "exclude": "reject",
}
DECISION_TO_STATUS = {
    "pending": "pending",
    "keep": "keep",
    "reject": "exclude",
    "deferred": "hold",
}


def build(record_source="journal.jsonl"):
    """Return the ordered list of decision dicts for all candidates."""
    state = store.replay()
    out = []
    for c in store.load_candidates():
        cid = c["candidate_id"]
        r = state.get(cid, {})
        status = r.get("status", "pending")
        title = (c.get("candidate_title") or c.get("source_post_title") or "").strip()
        out.append({
            "candidate_id": cid,
            "source_post_id": c.get("source_post_id", ""),
            "source_url": c.get("source_url", ""),
            "title": title,
            "decision": STATUS_TO_DECISION.get(status, "pending"),
            "reviewed_at": r.get("updated_at", ""),
            "record_source": record_source if r else "none",
            "notes": r.get("comment", ""),
            "status": status,
            "nature": r.get("nature", "unset"),
            "rev": r.get("rev", 0),
            "reviewer": r.get("reviewer", ""),
        })
    return out


def write(path=None):
    path = path or DECISIONS
    rows = build()
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return rows


def summarize(rows):
    from collections import Counter
    dec = Counter(r["decision"] for r in rows)
    return {
        "total": len(rows),
        "reviewed": sum(1 for r in rows if r["decision"] != "pending"),
        "by_decision": dict(dec),
    }


if __name__ == "__main__":
    rows = write()
    print(json.dumps(summarize(rows), ensure_ascii=False))
