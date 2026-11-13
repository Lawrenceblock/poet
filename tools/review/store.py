#!/usr/bin/env python3
"""Author-review storage layer (stdlib only).

Two-layer, append-only design:

  review-records/journal.jsonl   authoritative append-only log (one JSON per line)
  review-records/snapshot.json   materialised current state (rebuilt from journal)
  review-records/export-review-records.{csv,json}   downloadable exports

Nothing here ever writes to the poem text, the feed, or the candidate CSVs.
"""
import csv
import json
import os
import tempfile
import threading
from datetime import datetime, timezone, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RECORDS = os.environ.get("REVIEW_RECORDS_DIR") or os.path.join(
    ROOT, "docs", "author-review", "review-records")
JOURNAL = os.path.join(RECORDS, "journal.jsonl")
JOURNAL_TEST = os.path.join(RECORDS, "journal-test.jsonl")
SNAPSHOT = os.path.join(RECORDS, "snapshot.json")
EXPORT_CSV = os.path.join(RECORDS, "export-review-records.csv")
EXPORT_JSON = os.path.join(RECORDS, "export-review-records.json")
CAND_CSV = os.path.join(ROOT, "docs", "poetry-discovery", "poetry-candidates.v2.csv")
SEED_CSV = os.path.join(ROOT, "docs", "author-review", "poetry-candidates-author-review.csv")

TZ = timezone(timedelta(hours=8))  # 北京时间

STATUSES = ["pending", "keep", "hold", "exclude"]
STATUS_LABEL = {"pending": "待审阅", "keep": "保留", "hold": "暂缓", "exclude": "排除"}
NATURES = ["unset", "single_poem", "multi_poem", "non_poem", "unsure"]
NATURE_LABEL = {
    "unset": "（未填写）", "single_poem": "一首诗", "multi_poem": "多首诗",
    "non_poem": "非诗（评论/消息/摄影等）", "unsure": "尚不确定",
}

_lock = threading.Lock()


def _now():
    return datetime.now(TZ).isoformat(timespec="seconds")


def _atomic_write(path, text):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_candidates():
    with open(CAND_CSV, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def candidate_ids():
    return {c["candidate_id"] for c in load_candidates()}


def read_journal(path=None):
    path = path or JOURNAL
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def replay(records=None, include_test=False):
    """Last-wins per candidate_id, ordered by rev. Real records live in
    journal.jsonl; test records live in a *separate* journal-test.jsonl so they
    can never pollute the authoritative data."""
    records = read_journal() if records is None else records
    state = {}
    for r in records:
        if r.get("test") and not include_test:
            continue
        cid = r.get("candidate_id")
        if cid not in candidate_ids():
            continue
        cur = state.get(cid)
        if cur is None or r.get("rev", 0) >= cur.get("rev", 0):
            state[cid] = r
    return state


def replay_test():
    return replay(read_journal(JOURNAL_TEST), include_test=True)


def validate(payload):
    cid = str(payload.get("candidate_id", "")).strip()
    if cid not in candidate_ids():
        raise ValueError(f"未知候选编号：{cid!r}")
    status = payload.get("status", "pending")
    if status not in STATUSES:
        raise ValueError(f"非法审阅结论：{status!r}")
    nature = payload.get("nature", "unset")
    if nature not in NATURES:
        raise ValueError(f"非法作品性质：{nature!r}")
    comment = str(payload.get("comment", "") or "")
    if len(comment) > 20000:
        raise ValueError("意见过长（上限 20000 字）")
    return {
        "candidate_id": cid,
        "status": status,
        "nature": nature,
        "comment": comment,
        "reviewer": str(payload.get("reviewer", "") or "")[:200],
        "test": bool(payload.get("test", False)),
    }


def save(payload):
    """Validate, append to journal, rebuild snapshot+exports, verify read-back."""
    rec = validate(payload)
    is_test = rec["test"]
    journal_path = JOURNAL_TEST if is_test else JOURNAL
    with _lock:
        if is_test:
            prev_rev = max([r.get("rev", 0) for r in read_journal(JOURNAL_TEST)
                            if r.get("candidate_id") == rec["candidate_id"]] or [0])
        else:
            prev_rev = replay().get(rec["candidate_id"], {}).get("rev", 0)
        rec["rev"] = prev_rev + 1
        rec["updated_at"] = _now()

        os.makedirs(RECORDS, exist_ok=True)
        with open(journal_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

        if is_test:
            state = replay_test()
            got = state.get(rec["candidate_id"])
        else:
            rebuild_locked()
            got = replay().get(rec["candidate_id"])

        if not got or got.get("rev") != rec["rev"] or got.get("comment") != rec["comment"]:
            raise IOError("写入后校验失败，请重试")
        return got


def rebuild_locked():
    state = replay()
    payload = {
        "generated_at": _now(),
        "count": len(state),
        "records": state,
    }
    _atomic_write(SNAPSHOT, json.dumps(payload, ensure_ascii=False, indent=1))
    _write_exports(state)
    return state


def rebuild():
    with _lock:
        return rebuild_locked()


def _write_exports(state):
    cands = load_candidates()
    rows = []
    for c in cands:
        cid = c["candidate_id"]
        r = state.get(cid, {})
        st = r.get("status", "pending")
        na = r.get("nature", "unset")
        rows.append({
            "candidate_id": cid,
            "title": (c.get("candidate_title") or c.get("source_post_title") or "").strip(),
            "published": c.get("published", "")[:10],
            "category": c.get("category", ""),
            "status": st,
            "status_label": STATUS_LABEL[st],
            "nature": na,
            "nature_label": NATURE_LABEL[na],
            "comment": r.get("comment", ""),
            "reviewer": r.get("reviewer", ""),
            "updated_at": r.get("updated_at", ""),
            "rev": r.get("rev", 0),
            "reviewed": "yes" if st != "pending" else "no",
        })
    with open(EXPORT_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    _atomic_write(EXPORT_JSON, json.dumps(
        {"generated_at": _now(), "count": len(rows), "records": rows},
        ensure_ascii=False, indent=1))
    return rows


def get_one(cid):
    return replay().get(cid)


def get_all():
    return replay()


def progress():
    state = replay()
    total = len(candidate_ids())
    counts = {s: 0 for s in STATUSES}
    reviewed = 0
    for cid in candidate_ids():
        st = state.get(cid, {}).get("status", "pending")
        counts[st] = counts.get(st, 0) + 1
        if st != "pending":
            reviewed += 1
    return {"total": total, "reviewed": reviewed,
            "unreviewed": total - reviewed, "by_status": counts}


def purge_test():
    """Remove the test journal entirely; real data is untouched. Returns count."""
    with _lock:
        recs = read_journal(JOURNAL_TEST)
        if os.path.exists(JOURNAL_TEST):
            os.unlink(JOURNAL_TEST)
        return len(recs)


def import_seed():
    """Merge the legacy 作者确认状态 column as *initial* values, without
    overwriting any existing review record and without touching the source CSV.
    Returns the number of candidates seeded."""
    if not os.path.exists(SEED_CSV):
        return 0
    state = replay()
    seeded = 0
    with open(SEED_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            cid = row.get("candidate_id", "").strip()
            raw = (row.get("作者确认状态", "") or "").strip()
            if cid not in candidate_ids() or not raw or raw == "待作者审阅":
                continue
            if cid in state:  # never overwrite a real review
                continue
            st = "keep"
            if "不收入" in raw or "排除" in raw:
                st = "exclude"
            elif "暂缓" in raw:
                st = "hold"
            save({"candidate_id": cid, "status": st, "nature": "unset",
                  "comment": f"[导入自 CSV 作者确认状态] {raw}"})
            seeded += 1
    return seeded


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--purge-test", action="store_true")
    ap.add_argument("--import-seed", action="store_true")
    ap.add_argument("--progress", action="store_true")
    a = ap.parse_args()
    if a.rebuild:
        s = rebuild()
        print(f"snapshot rebuilt: {len(s)} reviewed records")
    if a.purge_test:
        print(f"purged test records: {purge_test()}")
    if a.import_seed:
        print(f"seeded from CSV: {import_seed()}")
    if a.progress:
        print(json.dumps(progress(), ensure_ascii=False))
