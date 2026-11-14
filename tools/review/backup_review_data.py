#!/usr/bin/env python3
"""Back up / verify / restore the author-review records (stdlib only).

The live records live in docs/author-review/review-records/. That directory is
inside the working workspace, so it survives a server restart but NOT the
workspace being recycled. This tool makes an independent, checksummed copy
somewhere else, and can verify and restore it.

IMPORTANT — what "independent" does and does not mean here. The tool refuses a
destination on the same *filesystem* as the source (that is the weakest useful
check: a single recycled workspace would lose both). But a different filesystem
inside the SAME container is still lost if the whole sandbox is recycled. Only a
copy that leaves the machine — a PRIVATE git repo or object storage — actually
survives a sandbox recycle. Do not call a local path "off-site".

Nothing here writes to poem text, the feed, or the candidate CSVs. A backup is
plain text so it can be reviewed, diffed and (if the author chooses) committed
to a PRIVATE repository. Do not commit it to the public repo.

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
import build_decisions  # noqa: E402

TZ = timezone(timedelta(hours=8))
# Files that make up the authoritative + derived record set.
DATA_FILES = ["journal.jsonl", "snapshot.json", "decisions.jsonl",
              "export-review-records.csv", "export-review-records.json"]
# Default backup destination. It MUST sit on a different filesystem from the
# records (which live under /workspace), otherwise a recycled workspace would
# take the source and its only backup down together. Here /workspace is an ext4
# mount (/dev/nvme0n2) and /home/openhands is on the container's overlay, so the
# default is a *different filesystem* — but still inside the SAME container, so
# it does NOT survive a full sandbox recycle. Override with REVIEW_BACKUP_DIR.
DEFAULT_TO = os.environ.get("REVIEW_BACKUP_DIR",
                            "/home/openhands/poet-review-backups/author-review")


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


def _probe_dev(path):
    """Return st_dev of the nearest existing ancestor of `path`, or None.

    Walking up the parent chain means the check works even when the destination
    directory does not exist yet, and it follows symlinks the way os.stat does.
    """
    p = os.path.abspath(path)
    while True:
        if os.path.exists(p):
            return os.stat(p).st_dev
        parent = os.path.dirname(p)
        if parent == p:
            return None
        p = parent


def _unique_dest(dest_root):
    """Return a fresh, non-colliding backup directory under dest_root.

    The name is the timestamp plus a numeric suffix, so two backups in the same
    second never overwrite each other (an existing backup is never reused).
    """
    stamp = datetime.now(TZ).strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(dest_root, stamp)
    n = 1
    while os.path.exists(dest):
        n += 1
        dest = os.path.join(dest_root, f"{stamp}-{n}")
    return dest


def cmd_backup(args):
    src = store.RECORDS
    # Refresh derived artefacts (snapshot + decisions + exports) from the
    # authoritative journal FIRST, so the backup always captures current state.
    # This is FAIL-CLOSED: if the refresh raises, we abort instead of copying a
    # stale/partial set and reporting a successful backup.
    try:
        store.rebuild()
        build_decisions.write()
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: refusing to back up — could not refresh derived records "
              f"from {src}: {type(e).__name__}: {e}")
        print("no backup was written (fail-closed).")
        return 1
    if not os.path.exists(os.path.join(src, "journal.jsonl")):
        print(f"note: no journal at {src}/journal.jsonl yet — backing up the "
              f"empty baseline (decisions.jsonl marks all candidates pending)")
    dest_root = os.path.abspath(args.to)
    # Enforce an independent backup: refuse to treat a copy on the same
    # filesystem as the source as a real backup (a recycled workspace would
    # lose both). --allow-same-fs overrides for throwaway/local use.
    try:
        src_dev = os.stat(src).st_dev
        dst_dev = _probe_dev(dest_root)
        if dst_dev is None:
            print(f"REFUSING: could not determine the filesystem of {dest_root} "
                  f"(its parent chain is not accessible). Pass --allow-same-fs "
                  f"to override if you are certain it is independent.")
            return 1
        if src_dev == dst_dev and not args.allow_same_fs:
            print(f"REFUSING: destination {dest_root} is on the same filesystem "
                  f"as the source ({src}).\n"
                  f"A backup there would be lost together with the source. "
                  f"Choose a different filesystem, or pass --allow-same-fs.")
            return 1
    except OSError as e:
        print(f"ERROR: could not check backup independence: {type(e).__name__}: {e}")
        return 1
    # Never nest a backup inside the records directory (would be backed up too).
    if dest_root == src or dest_root.startswith(src + os.sep):
        print(f"REFUSING: destination {dest_root} is inside the records directory "
              f"{src}; choose a directory outside it.")
        return 1
    dest = _unique_dest(dest_root)
    os.makedirs(dest, exist_ok=False)
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
    # Safety: snapshot current records before overwriting. Fail-closed — if the
    # current records cannot be safely backed up, do not clobber them.
    if os.path.exists(os.path.join(store.RECORDS, "journal.jsonl")):
        rc = cmd_backup(argparse.Namespace(to=DEFAULT_TO, allow_same_fs=False))
        if rc != 0:
            print("refusing to restore: could not back up the current records "
                  "first (see error above).")
            return 1
    os.makedirs(store.RECORDS, exist_ok=True)
    for name in DATA_FILES:
        src = os.path.join(d, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(store.RECORDS, name))
    store.rebuild()
    build_decisions.write()  # regenerate the canonical ledger for the restored data
    print(f"restored from {d} -> {store.RECORDS}")
    print(json.dumps(store.progress(), ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--to", default=DEFAULT_TO)
    b.add_argument("--allow-same-fs", action="store_true",
                   help="allow a destination on the same filesystem as the "
                        "source (not a real independent backup)")
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
