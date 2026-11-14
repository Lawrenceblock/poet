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

Commands
--------
  backup [--to DIR]     copy records to DIR/<timestamp>/ + SHA256SUMS + manifest
  verify DIR            strictly verify a backup (fail-closed; see verify_backup)
  restore DIR [--yes]   verify, then restore the backup's exact state (makes a
                        safety backup of the current records first)

Verification is strict and fail-closed: a backup is only accepted when it has a
valid manifest.json and a non-empty, well-formed SHA256SUMS.txt that agree with
each other, cover exactly the data files (present + declared-missing == the full
universe), and match on disk. Any missing file, empty/duplicated checksum list,
path traversal, absolute path, illegal name, symlink, uncovered file, or hash
mismatch fails verification. `restore` depends on this check and has no bypass.

A missing journal is NEVER treated as empty data. If journal.jsonl is absent
while any derived file (snapshot/decisions/exports) still exists, the state is
ambiguous — a lost journal over live data — and both `backup` and `restore`
refuse before writing anything (no rebuild, no refresh, no overwrite). Only when
the journal AND all derived files are absent is an empty baseline legitimate.

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
# The complete universe of files a backup may contain.
DATA_FILES = ["journal.jsonl", "snapshot.json", "decisions.jsonl",
              "export-review-records.csv", "export-review-records.json"]
# Required files: produced by the pre-backup refresh, so they must ALWAYS be
# present in a valid backup (even for an empty baseline).
REQUIRED_FILES = ["snapshot.json", "decisions.jsonl",
                  "export-review-records.csv", "export-review-records.json"]
# Optional files: may legitimately be absent (journal.jsonl is missing until the
# author saves the first review). Absence MUST be declared in the manifest.
OPTIONAL_FILES = ["journal.jsonl"]
# Manifest format tag. Verification refuses any other value, so the absence rule
# is explicit and cannot be guessed.
BACKUP_FORMAT = "poet-review-backup/2"
CHECKSUM_NAME = "SHA256SUMS.txt"
MANIFEST_NAME = "manifest.json"
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


def _records_dir_state(records_dir):
    """Classify a records directory PURELY by file presence — no writes, no
    rebuild, no repair. Shared by backup and restore so both apply the same rule.

    Returns a dict:
      exists    : the directory itself exists
      journal   : journal.jsonl is present
      derived   : sorted list of present derived files (REQUIRED_FILES)
      empty     : nothing we care about is present

    A MISSING journal is never treated as "no data": if any derived file is
    present while the journal is absent, the state is ambiguous (possibly a lost
    journal over live data) and callers MUST refuse to write.
    """
    journal = os.path.join(records_dir, "journal.jsonl")
    derived = [n for n in REQUIRED_FILES
               if os.path.lexists(os.path.join(records_dir, n))]
    return {
        "exists": os.path.isdir(records_dir),
        "journal": os.path.lexists(journal),
        "derived": sorted(derived),
        "empty": not os.path.lexists(journal) and not derived,
    }


class BackupInvalid(Exception):
    """A backup failed strict integrity verification."""


def _is_plain_name(name):
    """True only for a bare, safe file name (no directory part, no traversal).

    Rejects absolute paths, any '/' or '\\', '.' and '..', and empty names.
    """
    if not name or not isinstance(name, str):
        return False
    if name in (".", ".."):
        return False
    if "/" in name or "\\" in name or "\x00" in name:
        return False
    return os.path.basename(name) == name


def _read_checksums(path):
    """Parse SHA256SUMS.txt strictly. Returns an ordered list of (name, hex).

    Raises BackupInvalid for a missing/empty/malformed file, an illegal or
    duplicate name, or a non-hex digest. Never returns an empty list.
    """
    if not os.path.isfile(path):
        raise BackupInvalid(f"missing {CHECKSUM_NAME}")
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as e:
        raise BackupInvalid(f"cannot read {CHECKSUM_NAME}: {e}")
    if not raw.strip():
        raise BackupInvalid(f"{CHECKSUM_NAME} is empty")
    entries = []
    seen = set()
    for i, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        digest, sep, name = line.partition("  ")
        if not sep or not name:
            raise BackupInvalid(f"{CHECKSUM_NAME} line {i} malformed: {line!r}")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
            raise BackupInvalid(f"{CHECKSUM_NAME} line {i} has a non-hex digest")
        if not _is_plain_name(name):
            raise BackupInvalid(f"{CHECKSUM_NAME} line {i} has an unsafe file name: {name!r}")
        if name in seen:
            raise BackupInvalid(f"{CHECKSUM_NAME} has a duplicate entry: {name!r}")
        seen.add(name)
        entries.append((name, digest.lower()))
    if not entries:
        raise BackupInvalid(f"{CHECKSUM_NAME} lists no files")
    return entries


def _read_manifest(path):
    """Parse manifest.json strictly and return (present, missing) file lists.

    The present/missing split is explicit: `files` are the data files that must
    exist, `missing_files` are the optional files declared absent. Raises
    BackupInvalid on a missing file, bad JSON, wrong format tag, unknown file
    names, overlap, or any inconsistency between the two lists and the universe
    of data files.
    """
    if not os.path.isfile(path):
        raise BackupInvalid(f"missing {MANIFEST_NAME}")
    try:
        with open(path, encoding="utf-8") as fh:
            m = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        raise BackupInvalid(f"cannot parse {MANIFEST_NAME}: {e}")
    if not isinstance(m, dict):
        raise BackupInvalid(f"{MANIFEST_NAME} is not a JSON object")
    if m.get("format") != BACKUP_FORMAT:
        raise BackupInvalid(f"{MANIFEST_NAME} format is not {BACKUP_FORMAT!r}")
    files = m.get("files")
    missing = m.get("missing_files")
    if not isinstance(files, list) or not isinstance(missing, list):
        raise BackupInvalid(f"{MANIFEST_NAME} must list 'files' and 'missing_files'")
    for name in files + missing:
        if not _is_plain_name(name) or name not in DATA_FILES:
            raise BackupInvalid(f"{MANIFEST_NAME} names an unknown/unsafe file: {name!r}")
    if len(set(files)) != len(files) or len(set(missing)) != len(missing):
        raise BackupInvalid(f"{MANIFEST_NAME} lists a file twice")
    if set(files) & set(missing):
        raise BackupInvalid(f"{MANIFEST_NAME} lists a file as both present and missing")
    if set(files) | set(missing) != set(DATA_FILES):
        raise BackupInvalid(
            f"{MANIFEST_NAME} does not account for every data file "
            f"(files={sorted(files)}, missing={sorted(missing)})")
    if set(REQUIRED_FILES) - set(files):
        raise BackupInvalid(
            f"{MANIFEST_NAME} omits a required file: "
            f"{sorted(set(REQUIRED_FILES) - set(files))}")
    return files, missing


def verify_backup(d):
    """Strictly verify a backup directory. Returns (present_files, missing_files).

    Fail-closed: raises BackupInvalid on ANY doubt, so a caller can never treat
    an unverifiable backup as good. Enforces, in order:

      * the directory exists;
      * manifest.json exists, parses, has the right format and fully accounts
        for every data file (present + declared-missing == the whole universe);
      * SHA256SUMS.txt exists, is non-empty, well-formed, free of duplicates,
        and contains only bare legal file names (no absolute paths, no '..');
      * the checksum list names exactly the manifest's present files;
      * every checksummed file exists, is a regular file (not a symlink) and
        matches its digest;
      * no unaccounted data file is present in the directory.
    """
    if not os.path.isdir(d):
        raise BackupInvalid(f"not a directory: {d}")
    files, missing = _read_manifest(os.path.join(d, MANIFEST_NAME))
    entries = _read_checksums(os.path.join(d, CHECKSUM_NAME))
    if [n for n, _ in entries] != sorted(files):
        raise BackupInvalid(
            f"{CHECKSUM_NAME} does not match {MANIFEST_NAME} "
            f"(checksums={sorted(n for n, _ in entries)}, manifest={sorted(files)})")
    for name in missing:
        if os.path.lexists(os.path.join(d, name)):
            raise BackupInvalid(
                f"{name} is declared missing but exists in the backup")
    for name, digest in entries:
        p = os.path.join(d, name)
        if os.path.islink(p):
            raise BackupInvalid(f"{name} is a symlink, not a regular file")
        if not os.path.isfile(p):
            raise BackupInvalid(f"missing data file: {name}")
        got = _sha256(p)
        if got != digest:
            raise BackupInvalid(f"{name} checksum mismatch")
    # Nothing in the backup directory may be an unaccounted data file.
    for entry in os.listdir(d):
        if entry in DATA_FILES and entry not in files:
            raise BackupInvalid(
                f"{entry} is present but not covered by {MANIFEST_NAME}/{CHECKSUM_NAME}")
    return files, missing


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
    # Integrity pre-check BEFORE any refresh. A missing journal is NOT an empty
    # dataset: if any derived file still exists, the state is ambiguous (a lost
    # journal over live data). Refuse and touch nothing — do not rebuild, do not
    # write, do not create any directory.
    st = _records_dir_state(src)
    if not st["journal"] and st["derived"]:
        print(f"REFUSING: {src}/journal.jsonl is missing while derived review "
              f"data still exists ({', '.join(st['derived'])}).")
        print("This is an abnormal state (a lost journal over existing data); "
              "refusing to back up so the existing files are not overwritten or "
              "rebuilt as if the data were empty.")
        print("no refresh, no rebuild, no write was performed (fail-closed).")
        return 1
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
    if not st["journal"]:
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
    missing = []
    for name in DATA_FILES:
        p = os.path.join(src, name)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(dest, name))
            copied.append(name)
        else:
            missing.append(name)
    # A valid backup must always contain the required (refreshed) files.
    absent_required = [n for n in REQUIRED_FILES if n not in copied]
    if absent_required:
        shutil.rmtree(dest, ignore_errors=True)
        print(f"ERROR: required file(s) missing from the source after refresh: "
              f"{absent_required}; no backup was written (fail-closed).")
        return 1
    sums = []
    for name in sorted(copied):
        sums.append(f"{_sha256(os.path.join(dest, name))}  {name}")
    with open(os.path.join(dest, CHECKSUM_NAME), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sums) + "\n")
    manifest = {
        "format": BACKUP_FORMAT,
        "created_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "source": src,
        "files": sorted(copied),
        "missing_files": sorted(missing),
        **{f"source_{k}": v for k, v in _stats(src).items()},
    }
    with open(os.path.join(dest, MANIFEST_NAME), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(f"backup written: {dest}")
    print(f"  files        : {', '.join(copied)}")
    if missing:
        print(f"  declared absent: {', '.join(missing)}")
    print(f"  journal lines: {manifest['source_journal_lines']}")
    print(f"  candidates   : {manifest['source_unique_candidates']}")
    return 0


def cmd_verify(args):
    d = args.dir
    try:
        files, missing = verify_backup(d)
    except BackupInvalid as e:
        print(f"  INVALID: {e}")
        print("VERIFY FAILED")
        return 1
    for name in files:
        print(f"  OK      {name}")
    if missing:
        print(f"  declared absent (per manifest): {', '.join(missing)}")
    st = _stats(d)
    print(f"  journal lines: {st['journal_lines']}  "
          f"unique candidates: {st['unique_candidates']}")
    m = json.load(open(os.path.join(d, MANIFEST_NAME), encoding="utf-8"))
    print(f"  manifest created_at: {m.get('created_at')}")
    print("VERIFY OK")
    return 0


def cmd_restore(args):
    d = args.dir
    # Restore MUST depend on a passing integrity check. There is deliberately no
    # --force bypass: an unverifiable backup is never restored over live records.
    try:
        present, declared_missing = verify_backup(d)
    except BackupInvalid as e:
        print(f"  INVALID: {e}")
        print("refusing to restore from a backup that failed verification")
        return 1
    if not args.yes:
        print(f"would restore {d} -> {store.RECORDS}")
        print(f"  files to copy   : {', '.join(present)}")
        print(f"  declared absent : {', '.join(declared_missing) or '(none)'}")
        print("re-run with --yes to actually restore")
        return 0
    # Safety: snapshot current records before overwriting. Fail-closed — if the
    # current records cannot be safely backed up, do not clobber them.
    #
    # First classify the target PURELY (no writes): a missing journal is not an
    # empty target. If the journal is gone but any derived file remains, the
    # target is in an ambiguous/incomplete state — refuse rather than skip the
    # safety backup or overwrite files that may hold the author's work.
    tgt_state = _records_dir_state(store.RECORDS)
    if not tgt_state["journal"] and tgt_state["derived"]:
        print(f"REFUSING: target {store.RECORDS} has no journal.jsonl but still "
              f"contains derived review data ({', '.join(tgt_state['derived'])}).")
        print("The target directory is in an incomplete/abnormal state; refusing "
              "to restore. Inspect it by hand before proceeding — no file was "
              "overwritten or removed.")
        return 1
    if tgt_state["journal"]:
        rc = cmd_backup(argparse.Namespace(to=DEFAULT_TO, allow_same_fs=False))
        if rc != 0:
            print("refusing to restore: could not back up the current records "
                  "first (see error above).")
            return 1
    os.makedirs(store.RECORDS, exist_ok=True)
    for name in present:
        src = os.path.join(d, name)
        tgt = os.path.join(store.RECORDS, name)
        if os.path.islink(tgt):
            os.unlink(tgt)
        shutil.copy2(src, tgt)
    # Files the backup explicitly declares absent are removed from the target, so
    # a restore reproduces the backup's exact state (no stale journal survives).
    for name in declared_missing:
        tgt = os.path.join(store.RECORDS, name)
        if os.path.lexists(tgt):
            os.unlink(tgt)
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
    r.set_defaults(func=cmd_restore)
    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
