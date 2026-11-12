#!/usr/bin/env python3
"""Back up / verify / restore the author-review records (stdlib only).

The live records live in docs/author-review/review-records/. That directory is
inside the working workspace, so it survives a server restart but NOT the
workspace being recycled. This tool makes an independent, checksummed copy
somewhere else, and can verify and restore it.

Commands
--------
  backup [--to DIR]     copy records to DIR/<timestamp>/ + SHA256SUMS + manifest
  verify DIR            check checksums and record counts of a backup
  restore DIR [--yes]   restore journal+snapshot from a backup (makes a safety
                        backup of the current records first)

Nothing here writes to poem text, the feed, or the candidate CSVs. A backup is
plain text so it can be reviewed, diffed and (if the author chooses) committed
to a PRIVATE repository. Do not commit it to the public repo.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import store  # noqa: E402

TZ = timezone(timedelta(hours=8))
# Files that make up the authoritative + derived record set.
DATA_FILES = ["journal.jsonl", "snapshot.json",
              "export-review-records.csv", "export-review-records.json"]
DEFAULT_TO = "/workspace/backups/author-review"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _stats(records_dir):
    journal = os.path.join(records_dir, "journal.jsonl")
    lines = 0
    uniq = set()
    if os.path.exists(journal):
        with open(journal, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                lines += 1
                try:
                    uniq.add(json.loads(line)["candidate_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    return {"journal_lines": lines, "unique_candidates": len(uniq)}


def cmd_backup(args):
    src = store.RECORDS
    if not os.path.exists(os.path.join(src, "journal.jsonl")):
        print(f"no journal at {src}/journal.jsonl — nothing to back up")
        return 1
    stamp = datetime.now(TZ).strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(args.to, stamp)
    os.makedirs(dest, exist_ok=True)
    copied = []
    for name in DATA_FILES:
        p = os.path.join(src, name)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(dest, name))
            copied.append(name)
    sums = []
    for name in sorted(copied):
        sums.append(f"{_sha256(os.path.join(dest, name))}  {name}")
    with open(os.path.join(dest, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sums) + "\n")
    manifest = {
        "created_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "source": src,
        "files": copied,
        **{f"source_{k}": v for k, v in _stats(src).items()},
    }
    with open(os.path.join(dest, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(f"backup written: {dest}")
    print(f"  files        : {', '.join(copied)}")
    print(f"  journal lines: {manifest['source_journal_lines']}")
    print(f"  candidates   : {manifest['source_unique_candidates']}")
    return 0


def cmd_verify(args):
    d = args.dir
    if not os.path.isdir(d):
        print(f"not a directory: {d}")
        return 1
    sums_path = os.path.join(d, "SHA256SUMS.txt")
    if not os.path.exists(sums_path):
        print(f"missing SHA256SUMS.txt in {d}")
        return 1
    ok = True
    with open(sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            want, _, name = line.partition("  ")
            p = os.path.join(d, name)
            if not os.path.exists(p):
                print(f"  MISSING {name}")
                ok = False
                continue
            got = _sha256(p)
            if got == want:
                print(f"  OK      {name}")
            else:
                print(f"  BAD     {name} (checksum mismatch)")
                ok = False
    st = _stats(d)
    print(f"  journal lines: {st['journal_lines']}  "
          f"unique candidates: {st['unique_candidates']}")
    man = os.path.join(d, "manifest.json")
    if os.path.exists(man):
        m = json.load(open(man, encoding="utf-8"))
        print(f"  manifest created_at: {m.get('created_at')}")
    print("VERIFY OK" if ok else "VERIFY FAILED")
    return 0 if ok else 1


def cmd_restore(args):
    d = args.dir
    if cmd_verify(args) != 0 and not args.force:
        print("refusing to restore from a backup that failed verification "
              "(use --force to override)")
        return 1
    if not args.yes:
        print(f"would restore {d} -> {store.RECORDS}")
        print("re-run with --yes to actually restore")
        return 0
    # Safety: snapshot current records before overwriting.
    if os.path.exists(os.path.join(store.RECORDS, "journal.jsonl")):
        args.to = DEFAULT_TO
        cmd_backup(argparse.Namespace(to=DEFAULT_TO))
    os.makedirs(store.RECORDS, exist_ok=True)
    for name in DATA_FILES:
        src = os.path.join(d, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(store.RECORDS, name))
    store.rebuild()
    print(f"restored from {d} -> {store.RECORDS}")
    print(json.dumps(store.progress(), ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--to", default=DEFAULT_TO)
    b.set_defaults(func=cmd_backup)
    v = sub.add_parser("verify")
    v.add_argument("dir")
    v.set_defaults(func=cmd_verify)
    r = sub.add_parser("restore")
    r.add_argument("dir")
    r.add_argument("--yes", action="store_true")
    r.add_argument("--force", action="store_true")
    r.set_defaults(func=cmd_restore)
    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
