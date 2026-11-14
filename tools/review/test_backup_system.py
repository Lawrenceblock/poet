#!/usr/bin/env python3
"""Acceptance tests for the author-review BACKUP / RESTORE tooling (stdlib only).

Exercises tools/review/backup_review_data.py end to end in isolated temp dirs:

  functional
    1. a normal backup succeeds and is verifiable
    2. a refresh failure aborts the backup (fail-closed, no stale backup)
    3. a same-filesystem destination is refused
    4. restore is refused when the backup fails verification
    5. an empty dataset produces a valid baseline backup (explicit manifest rule)
    6. restore into an empty directory is complete and consistent
    7. private review comments never reach the public artefacts
    8. no token / private data in tracked files, gitignore or the working tree
    9. a repeat backup never overwrites an earlier valid backup
   10. restoring over existing records is refused when the safety backup fails
   11. repeated backup -> restore cycles stay consistent

  strict verification (each tampered backup must FAIL verify and must NOT change
  the restore target)
   12. empty SHA256SUMS.txt
   13. checksum list omits journal.jsonl
   14. manifest and checksum file lists disagree
   15. missing manifest.json
   16. missing SHA256SUMS.txt
   17. a checksummed data file is missing
   18. a data file's content was changed (hash mismatch)
   19. a duplicate checksum entry
   20. a '../' path-traversal name
   21. an absolute-path name
   22. a data file declared missing but present
   23. a data file replaced by a symlink
   24. an unknown/illegal file name in the checksum list

  positive control
   25. a valid backup restores over existing records

  journal-missing data protection (a missing journal is NEVER empty data)
   26. Group A: backup refuses when the journal is gone but derived files remain
       (each: non-zero, clear message, hashes unchanged, no backup dir, and
       store.rebuild/build_decisions.write are NOT called)
   27. Group B: a truly empty records dir still yields a valid empty baseline
   28. Group C: restore refuses an incomplete target (no journal but derived
       files), never overwrites, never bypasses the safety backup; an empty
       target and a journalled target still restore; no --force flag exists

  journal file-type protection (a symlink / non-regular file is NEVER the journal)
   29. Group A: backup refuses a symlink (external/internal/broken), a directory
       and a FIFO — with and without derived files — non-zero, clear message, no
       refresh/rebuild, no backup dir, target + link + external file unchanged
   30. Group B: restore refuses the same target types without overwriting,
       deleting or replacing the link/file; no refresh is called
   31. Group C: a zero-byte regular journal is accepted; a truly empty records dir
       still yields a valid empty baseline; a normal journal backs up and restores

Every test uses throwaway temp directories and a synthetic journal. The real
author records under docs/author-review/review-records/ are never read or
written. Exit code 0 = all tests passed.

  python3 tools/review/test_backup_system.py
"""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TOOL = os.path.join(HERE, "backup_review_data.py")
ARTIFACTS = os.path.join(HERE, "build_review_artifacts.py")

DATA_FILES = ["journal.jsonl", "snapshot.json", "decisions.jsonl",
              "export-review-records.csv", "export-review-records.json"]
REQUIRED_FILES = ["snapshot.json", "decisions.jsonl",
                  "export-review-records.csv", "export-review-records.json"]

fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run(tool, args, records_dir, backup_dir=None, extra_env=None):
    env = {**os.environ, "REVIEW_RECORDS_DIR": records_dir}
    if backup_dir is not None:
        env["REVIEW_BACKUP_DIR"] = backup_dir
    if extra_env:
        env.update(extra_env)
    p = subprocess.run([sys.executable, tool, *args], env=env,
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def run_inproc(records_dir, snippet):
    """Run `snippet` in-process with store/backup imported. Used for direct unit
    checks and deterministic mock-based fault injection (no OS-permission tricks)."""
    boot = (f"import sys; sys.path.insert(0, {HERE!r}); "
            f"import store, backup_review_data as B; ")
    p = subprocess.run([sys.executable, "-c", boot + snippet],
                       env={**os.environ, "REVIEW_RECORDS_DIR": records_dir},
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def write_journal(records_dir, lines):
    os.makedirs(records_dir, exist_ok=True)
    with open(os.path.join(records_dir, "journal.jsonl"), "w", encoding="utf-8") as fh:
        for obj in lines:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def rec(cid, status, comment="", nature="single_poem", rev=1):
    return {"candidate_id": cid, "status": status, "nature": nature,
            "comment": comment, "reviewer": "", "test": False, "rev": rev,
            "updated_at": "2026-01-01T00:00:00+08:00"}


def first_backup_dir(root):
    if not os.path.isdir(root):
        return None
    entries = sorted(d for d in os.listdir(root)
                     if os.path.isdir(os.path.join(root, d)))
    return os.path.join(root, entries[0]) if entries else None


def tree_state(root):
    """Map every file under `root` to its sha256, so partial overwrites show up."""
    state = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            p = os.path.join(dirpath, name)
            state[os.path.relpath(p, root)] = sha(p)
    return state


def load_manifest(d):
    return json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))


def save_manifest(d, m):
    with open(os.path.join(d, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def write_checksums(d, names, extra_lines=()):
    lines = [f"{sha(os.path.join(d, n))}  {n}" for n in sorted(names)]
    lines += list(extra_lines)
    with open(os.path.join(d, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def mk_valid(tmp, tag):
    """Create a records dir with one journal line and a valid backup."""
    records = os.path.join(tmp, f"records-{tag}")
    write_journal(records, [rec("C0001", "keep", f"comment-{tag}")])
    bk = os.path.join(tmp, f"bk-{tag}")
    rc, out, err = run(TOOL, ["backup", "--to", bk, "--allow-same-fs"], records)
    assert rc == 0, f"setup backup for {tag} failed: {out} {err}"
    return records, first_backup_dir(bk)


def cross_fs_base(records_dir):
    """A writable dir on a different filesystem from records_dir, or None."""
    src_dev = os.stat(records_dir).st_dev
    for cand in ["/workspace", "/dev/shm", "/run", "/home"]:
        if not os.path.isdir(cand):
            continue
        try:
            if os.stat(cand).st_dev == src_dev:
                continue
            probe = os.path.join(cand, f".backup-test-probe-{os.getpid()}")
            os.makedirs(probe, exist_ok=True)
            os.rmdir(probe)
            return cand
        except OSError:
            continue
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="backup-test-")
    try:
        _run_all(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if fails:
        print(f"FAILURES: {len(fails)} -> {fails}")
        sys.exit(1)
    print("OK: all backup-system tests passed")


def _run_all(tmp):
    records = os.path.join(tmp, "records")
    backup = os.path.join(tmp, "backup")

    # 1. Normal backup succeeds and is verifiable.
    print("1. a normal backup succeeds and is verifiable")
    write_journal(records, [rec("C0001", "keep", "正常备份")])
    rc, out, err = run(TOOL, ["backup", "--to", backup, "--allow-same-fs"], records)
    check("backup exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    dest = first_backup_dir(backup)
    check("a backup directory was created", dest is not None)
    if dest:
        for name in DATA_FILES + ["SHA256SUMS.txt", "manifest.json"]:
            check(f"backup contains {name}", os.path.exists(os.path.join(dest, name)))
        rc2, out2, _ = run(TOOL, ["verify", dest], records)
        check("verify exits 0", rc2 == 0 and "VERIFY OK" in out2, out2)

    # 2. A refresh failure aborts the backup (fail-closed).
    #    Deterministic injection: patch store.rebuild to raise, so the test does
    #    not depend on filesystem permissions or on running as root.
    print("2. a refresh failure aborts the backup (fail-closed)")
    ro_records = os.path.join(tmp, "records-ro")
    sentinel = f"PRIVATE-{uuid.uuid4().hex}"
    write_journal(ro_records, [rec("C0002", "keep", sentinel)])
    ro_backup = os.path.join(tmp, "backup-ro")
    snippet = ("store.rebuild = lambda *a, **k: (_ for _ in ()).throw("
               "RuntimeError('mock refresh failure')); "
               f"raise SystemExit(B.cmd_backup(type('A',(),{{'to':{ro_backup!r},"
               f"'allow_same_fs':True}})()))")
    rc, out, err = run_inproc(ro_records, snippet)
    check("backup fails when refresh raises", rc == 1, f"rc={rc} out={out} err={err}")
    check("no backup directory written", first_backup_dir(ro_backup) is None)
    check("reports fail-closed", "fail-closed" in out, out)
    check("private comment not printed", sentinel not in out and sentinel not in err)

    # 3. A same-filesystem destination is refused.
    print("3. a same-filesystem destination is refused")
    same = os.path.join(tmp, "backup-same")
    rc, out, err = run(TOOL, ["backup", "--to", same], records)  # no --allow-same-fs
    check("same-fs backup refused (non-zero)", rc != 0, f"rc={rc} out={out}")
    check("says same filesystem", "same filesystem" in out, out)
    check("no backup written", first_backup_dir(same) is None)

    # 4. Restore is refused when the backup fails verification.
    print("4. restore is refused when the backup fails verification")
    good = first_backup_dir(backup)
    bad = os.path.join(tmp, "backup-bad")
    shutil.copytree(good, bad)
    with open(os.path.join(bad, "decisions.jsonl"), "a", encoding="utf-8") as fh:
        fh.write('{"tampered": true}\n')
    target = os.path.join(tmp, "records-target")
    write_journal(target, [rec("C0009", "hold", "keep me")])
    before = tree_state(target)
    rc, out, err = run(TOOL, ["restore", bad, "--yes"], target,
                       backup_dir=os.path.join(tmp, "safety"))
    check("restore reports the invalid backup", "INVALID" in out, out)
    check("restore refused (non-zero)", rc != 0, f"rc={rc} out={out}")
    check("target records unchanged", tree_state(target) == before)

    # 5. An empty dataset produces a valid baseline backup (explicit manifest rule).
    print("5. an empty dataset produces a valid baseline backup")
    empty = os.path.join(tmp, "records-empty")
    os.makedirs(empty, exist_ok=True)
    empty_bk = os.path.join(tmp, "backup-empty")
    rc, out, err = run(TOOL, ["backup", "--to", empty_bk, "--allow-same-fs"], empty)
    check("empty backup exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    edest = first_backup_dir(empty_bk)
    check("baseline backup created", edest is not None)
    if edest:
        m = load_manifest(edest)
        check("manifest format tag is set",
              m.get("format") == "poet-review-backup/2", str(m.get("format")))
        check("journal.jsonl declared missing",
              m.get("missing_files") == ["journal.jsonl"], str(m.get("missing_files")))
        check("all required files declared present",
              sorted(m.get("files", [])) == sorted(REQUIRED_FILES), str(m.get("files")))
        dpath = os.path.join(edest, "decisions.jsonl")
        n = len([ln for ln in open(dpath, encoding="utf-8").read().splitlines() if ln.strip()])
        check("all 137 candidates listed as pending", n == 137, f"n={n}")
        rc, out, _ = run(TOOL, ["verify", edest], empty)
        check("empty baseline verifies OK", rc == 0 and "VERIFY OK" in out, out)
        rc, out, err = run_inproc(
            empty, f"f, m = B.verify_backup({edest!r}); print(sorted(f)); print(sorted(m))")
        check("verify_backup returns (required, ['journal.jsonl'])",
              rc == 0 and str(sorted(REQUIRED_FILES)) in out and "['journal.jsonl']" in out,
              f"rc={rc} out={out} err={err}")

    # 6. Restore into an empty directory is complete and consistent.
    print("6. restore into an empty directory is complete and consistent")
    src_records = os.path.join(tmp, "records-src")
    write_journal(src_records, [rec("C0003", "keep", "第一首"), rec("C0004", "exclude", "第二首")])
    src_bk = os.path.join(tmp, "backup-src2")
    run(TOOL, ["backup", "--to", src_bk, "--allow-same-fs"], src_records)
    sdest = first_backup_dir(src_bk)
    fresh = os.path.join(tmp, "records-fresh")  # no journal -> no safety backup needed
    os.makedirs(fresh, exist_ok=True)
    rc, out, err = run(TOOL, ["restore", sdest, "--yes"], fresh)
    check("restore exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    for name in DATA_FILES:
        s, t = os.path.join(sdest, name), os.path.join(fresh, name)
        if os.path.exists(s):
            check(f"restored {name} identical to backup",
                  os.path.exists(t) and sha(s) == sha(t))
    check("decisions.jsonl regenerated on restore",
          os.path.exists(os.path.join(fresh, "decisions.jsonl")))
    rc, out, _ = run(TOOL, ["verify", sdest], fresh)
    check("restored source still verifies", rc == 0)

    # 7. Private review comments never reach the public artefacts.
    print("7. private review comments never reach the public artefacts")
    priv = os.path.join(tmp, "records-priv")
    secret = f"PRIVATE-SENTINEL-{uuid.uuid4().hex}"
    write_journal(priv, [rec("C0005", "keep", secret)])
    rc, out, err = run(ARTIFACTS, [], priv)
    check("artefacts generated", rc == 0, f"rc={rc} err={err}")
    for doc in ["review-summary.md", "recovery-report.md"]:
        p = os.path.join(priv, doc)
        if os.path.exists(p):
            body = open(p, encoding="utf-8").read()
            check(f"{doc} has no private comment", secret not in body)
    public = os.path.join(ROOT, "hugo", "public")
    if os.path.isdir(public):
        leaked = []
        for dirpath, _dirs, files in os.walk(public):
            for name in files:
                try:
                    with open(os.path.join(dirpath, name), "rb") as fh:
                        if secret.encode() in fh.read():
                            leaked.append(os.path.join(dirpath, name))
                except OSError:
                    pass
        check("comment absent from preview build output", not leaked, str(leaked))

    # 8. No token / private data in tracked files, gitignore or working tree.
    print("8. no token / private data in tracked files, gitignore or working tree")
    import re
    for name in DATA_FILES + ["journal-test.jsonl"]:
        rel = f"docs/author-review/review-records/{name}"
        gi = subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT)
        check(f"{name} is gitignored", gi.returncode == 0)
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT,
                             capture_output=True, text=True).stdout.splitlines()
    priv_tracked = [f for f in tracked
                    if "review-records/" in f and
                    os.path.basename(f) in DATA_FILES + ["journal-test.jsonl"]]
    check("no private data file is tracked", not priv_tracked, str(priv_tracked))
    tok_re = re.compile(r"(X-Review-Token|review_token|REVIEW_ACCESS_TOKEN)\s*[:=]\s*[A-Za-z0-9_\-]{8,}")
    tok_hits = []
    for f in tracked:
        p = os.path.join(ROOT, f)
        try:
            txt = open(p, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if tok_re.search(txt):
            tok_hits.append(f)
    check("no hardcoded token in tracked files", not tok_hits, str(tok_hits))
    diff = subprocess.run(["git", "diff", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout
    check("secret absent from working-tree diff", secret not in diff)

    # 9. A repeat backup never overwrites an earlier valid backup.
    print("9. a repeat backup never overwrites an earlier valid backup")
    rp_records = os.path.join(tmp, "records-repeat")
    rp_bk = os.path.join(tmp, "backup-repeat")
    write_journal(rp_records, [rec("C0006", "keep", "OLD")])
    run(TOOL, ["backup", "--to", rp_bk, "--allow-same-fs"], rp_records)
    d1 = first_backup_dir(rp_bk)
    marker = os.path.join(d1, "MARKER-KEEP.txt")
    open(marker, "w").write("keep")
    old_hash = sha(os.path.join(d1, "journal.jsonl"))
    write_journal(rp_records, [rec("C0006", "exclude", "NEW", rev=2)])
    run(TOOL, ["backup", "--to", rp_bk, "--allow-same-fs"], rp_records)
    dirs = sorted(d for d in os.listdir(rp_bk) if os.path.isdir(os.path.join(rp_bk, d)))
    check("two distinct backups exist", len(dirs) == 2, str(dirs))
    check("earlier backup marker preserved", os.path.exists(marker))
    check("earlier backup content unchanged",
          os.path.exists(marker) and sha(os.path.join(d1, "journal.jsonl")) == old_hash)

    # 10. Restoring over existing records is refused when the safety backup fails.
    #     Deterministic injection: patch store.rebuild to raise, so the pre-restore
    #     safety backup (cmd_backup) fails and the restore must abort.
    print("10. restoring over existing records is refused when the safety backup fails")
    tgt = os.path.join(tmp, "records-overwrite")
    write_journal(tgt, [rec("C0007", "keep", "current authoritative")])
    tgt_before = tree_state(tgt)
    _, gdest = mk_valid(tmp, "goodsrc")
    snippet = ("store.rebuild = lambda *a, **k: (_ for _ in ()).throw("
               "RuntimeError('mock safety-backup failure')); "
               f"raise SystemExit(B.cmd_restore(type('A',(),{{'dir':{gdest!r},"
               f"'yes':True}})()))")
    rc, out, err = run_inproc(tgt, snippet)
    check("restore refused when safety backup fails", "refusing to restore" in out, out)
    check("existing records untouched by refused restore", tree_state(tgt) == tgt_before)

    # 11. Repeated backup -> restore cycles stay consistent.
    print("11. repeated backup -> restore cycles stay consistent")
    cyc = os.path.join(tmp, "records-cycle")
    write_journal(cyc, [rec("C0008", "keep", "cycle-1"), rec("C0001", "hold", "cycle-1b")])
    cyc_bk = os.path.join(tmp, "backup-cycle")
    hashes = []
    for i in range(2):
        run(TOOL, ["backup", "--to", cyc_bk, "--allow-same-fs"], cyc)
        latest = sorted(d for d in os.listdir(cyc_bk)
                        if os.path.isdir(os.path.join(cyc_bk, d)))[-1]
        latest = os.path.join(cyc_bk, latest)
        hashes.append(sha(os.path.join(latest, "decisions.jsonl")))
        fresh2 = os.path.join(tmp, f"records-cycle-restore-{i}")
        os.makedirs(fresh2, exist_ok=True)
        rc, out, err = run(TOOL, ["restore", latest, "--yes"], fresh2)
        check(f"cycle {i}: restore exits 0", rc == 0, f"rc={rc} out={out}")
        check(f"cycle {i}: decisions.jsonl matches backup",
              sha(os.path.join(fresh2, "decisions.jsonl")) == hashes[-1])
    check("two cycles produced identical decisions", hashes[0] == hashes[1])

    # 12-24. Strict verification: each tampered backup must fail verify AND must
    # not change the restore target.
    _verification_suite(tmp)

    # 25. Positive control: a valid backup DOES restore over existing records
    # (using a cross-filesystem safety-backup target so the guard can proceed).
    print("25. a valid backup restores over existing records (positive control)")
    base = cross_fs_base(tmp)
    if base is None:
        print("  [SKIP] no writable cross-filesystem dir available for the safety backup")
    else:
        tgt2 = os.path.join(tmp, "records-pos")
        write_journal(tgt2, [rec("C0001", "hold", "old")])
        _, vdest = mk_valid(tmp, "pos-src")
        safety = os.path.join(base, f"poet-backup-test-safety-{os.getpid()}")
        try:
            rc, out, err = run(TOOL, ["restore", vdest, "--yes"], tgt2, backup_dir=safety)
            check("valid restore exits 0", rc == 0, f"rc={rc} out={out} err={err}")
            check("target now matches the backup journal",
                  sha(os.path.join(tgt2, "journal.jsonl")) == sha(os.path.join(vdest, "journal.jsonl")))
        finally:
            shutil.rmtree(safety, ignore_errors=True)

    # 26-28. journal-missing data-protection (a missing journal is NEVER empty
    # data): backup/restore must refuse when derived files remain.
    _journal_missing_suite(tmp)

    # 29-31. journal file-type protection (a symlink / non-regular file is NEVER
    # the authoritative journal).
    _journal_type_suite(tmp)


def _journal_type_suite(tmp):
    # journal.jsonl must be a real regular file. Build the abnormal cases purely
    # from synthetic data + temp dirs. "derived" toggles whether derived files are
    # also present (the refusal must not depend on them).
    def make_records(tag, kind, with_derived):
        records = os.path.join(tmp, f"jtype-{tag}")
        os.makedirs(records, exist_ok=True)
        jpath = os.path.join(records, "journal.jsonl")
        ext = os.path.join(tmp, f"jtype-ext-{tag}.jsonl")
        info = {}
        if kind == "regular":
            with open(jpath, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(rec("C0001", "keep", f"jtype-{tag}")) + "\n")
        elif kind == "ext-symlink":
            with open(ext, "w", encoding="utf-8") as fh:
                fh.write("EXTERNAL-AUTHOR-DATA\n")
            os.symlink(ext, jpath)
            info["ext"] = ext
        elif kind == "int-symlink":
            target = os.path.join(records, "journal-real.jsonl")
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(rec("C0001", "keep", "inner")) + "\n")
            os.symlink(target, jpath)
            info["target"] = target
        elif kind == "broken-symlink":
            os.symlink(os.path.join(tmp, f"nope-{tag}.jsonl"), jpath)
        elif kind == "dir":
            os.mkdir(jpath)
        elif kind == "fifo":
            os.mkfifo(jpath)
        if with_derived:
            for n in REQUIRED_FILES:
                with open(os.path.join(records, n), "w", encoding="utf-8") as fh:
                    fh.write(f"derived {n}\n")
        return records, info

    def lstat_snapshot(records, info):
        """Filename -> (type, hash) for the records dir, plus the external file
        hash, so we can prove nothing changed (link preserved, no new files)."""
        snap = {}
        for name in sorted(os.listdir(records)):
            p = os.path.join(records, name)
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                snap[name] = ("symlink", os.readlink(p))
            elif stat.S_ISREG(st.st_mode):
                snap[name] = ("regular", sha(p))
            elif stat.S_ISDIR(st.st_mode):
                snap[name] = ("dir", None)
            else:
                snap[name] = ("other", None)
        if "ext" in info and os.path.exists(info["ext"]):
            snap["<ext>"] = ("regular", sha(info["ext"]))
        return snap

    def backup_tracks(records, dest):
        snippet = (
            "calls = []\n"
            "def boom(*a, **k):\n"
            "    calls.append('x')\n"
            "    raise RuntimeError('SHOULD-NOT-BE-CALLED')\n"
            "store.rebuild = boom\n"
            "B.build_decisions.write = boom\n"
            f"rc = B.cmd_backup(type('A',(),{{'to':{dest!r},'allow_same_fs':True}})())\n"
            "print('RC', rc)\n"
            "print('REFRESH_CALLS', len(calls))\n")
        return run_inproc(records, snippet)

    def restore_tracks(target, backup_dir):
        snippet = (
            "calls = []\n"
            "def boom(*a, **k):\n"
            "    calls.append('x')\n"
            "    raise RuntimeError('SHOULD-NOT-BE-CALLED')\n"
            "store.rebuild = boom\n"
            "B.build_decisions.write = boom\n"
            f"rc = B.cmd_restore(type('A',(),{{'dir':{backup_dir!r},'yes':True}})())\n"
            "print('RC', rc)\n"
            "print('REFRESH_CALLS', len(calls))\n")
        return run_inproc(target, snippet)

    def state_of(records):
        return run_inproc(records,
                          "print('STATE', B._records_dir_state(" + repr(records) + "))")

    fifo_ok = hasattr(os, "mkfifo")
    cases = [
        ("A1 symlink -> external file", "ext-symlink", True),
        ("A2 symlink -> internal file", "int-symlink", True),
        ("A3 broken symlink", "broken-symlink", True),
        ("A4 path is a directory", "dir", True),
        ("A5 symlink -> external (no derived)", "ext-symlink", False),
    ]
    if fifo_ok:
        cases.append(("A6 FIFO", "fifo", True))

    print("29. Group A: backup refuses a symlink / non-regular journal")
    for i, (label, kind, with_derived) in enumerate(cases):
        records, info = make_records(f"A{i}", kind, with_derived)
        before = lstat_snapshot(records, info)
        # classification sanity: the journal must be flagged bad, never "ok".
        rc0, out0, _ = state_of(records)
        check(f"{label}: classifier marks journal_bad",
              "'journal_bad': True" in out0, out0)
        check(f"{label}: classifier marks journal_ok False",
              "'journal_ok': False" in out0, out0)
        dest = os.path.join(tmp, f"jbkA{i}")
        rc, out, err = run(TOOL, ["backup", "--to", dest, "--allow-same-fs"], records)
        check(f"{label}: backup refuses (non-zero)", rc != 0, f"rc={rc} out={out}")
        check(f"{label}: message flags a non-regular journal",
              "is not a regular file" in out, out)
        check(f"{label}: no backup directory written", first_backup_dir(dest) is None)
        check(f"{label}: records dir (types+hashes) unchanged",
              lstat_snapshot(records, info) == before)
        if "ext" in info:
            check(f"{label}: external linked file unchanged",
                  lstat_snapshot(records, info).get("<ext>") == before.get("<ext>"))
        rc2, out2, err2 = backup_tracks(records, os.path.join(tmp, f"jbkA{i}t"))
        check(f"{label}: store.rebuild/build_decisions.write NOT called",
              "REFRESH_CALLS 0" in out2 and "RC 1" in out2, f"out={out2} err={err2}")
        check(f"{label}: tracked-call run wrote no backup",
              first_backup_dir(os.path.join(tmp, f"jbkA{i}t")) is None)

    # Group B: restore refuses the same target types.
    print("30. Group B: restore refuses a symlink / non-regular target journal")
    _, good_backup = mk_valid(tmp, "jtype-src")
    rcases = [("B1 symlink -> external file", "ext-symlink"),
              ("B2 broken symlink", "broken-symlink"),
              ("B3 path is a directory", "dir")]
    if fifo_ok:
        rcases.append(("B4 FIFO", "fifo"))
    for i, (label, kind) in enumerate(rcases):
        target, info = make_records(f"B{i}", kind, True)
        before = lstat_snapshot(target, info)
        rc, out, err = run(TOOL, ["restore", good_backup, "--yes"], target,
                           backup_dir=os.path.join(tmp, f"jsafetyB{i}"))
        check(f"{label}: restore refused (non-zero)", rc != 0, f"rc={rc} out={out}")
        check(f"{label}: message flags a non-regular journal",
              "is not a regular file" in out, out)
        check(f"{label}: target (types+hashes) unchanged",
              lstat_snapshot(target, info) == before)
        # the link/file must still be exactly what it was
        jp = os.path.join(target, "journal.jsonl")
        if kind.endswith("symlink"):
            check(f"{label}: symlink itself not removed/replaced", os.path.islink(jp))
        if "ext" in info:
            check(f"{label}: external linked file unchanged",
                  lstat_snapshot(target, info).get("<ext>") == before.get("<ext>"))
        rc2, out2, err2 = restore_tracks(target, good_backup)
        check(f"{label}: store.rebuild/build_decisions.write NOT called",
              "REFRESH_CALLS 0" in out2 and "RC 1" in out2, f"out={out2} err={err2}")
        check(f"{label}: tracked-call run left target unchanged",
              lstat_snapshot(target, info) == before)

    # Group C: positive compatibility — regular journals keep working.
    print("31. Group C: zero-byte regular journal + normal flow still work")
    # C1: a zero-byte REGULAR journal is accepted (not a symlink, not missing).
    zero = os.path.join(tmp, "jtype-zero")
    os.makedirs(zero, exist_ok=True)
    open(os.path.join(zero, "journal.jsonl"), "w").close()
    rc0, out0, _ = state_of(zero)
    check("C1 zero-byte journal classified regular",
          "'journal_type': 'regular'" in out0 and "'journal_ok': True" in out0, out0)
    zdest = os.path.join(tmp, "jbk-zero")
    rc, out, err = run(TOOL, ["backup", "--to", zdest, "--allow-same-fs"], zero)
    check("C1 zero-byte journal backup exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    zdir = first_backup_dir(zdest)
    check("C1 zero-byte journal backup created", zdir is not None)
    if zdir:
        m = load_manifest(zdir)
        check("C1 journal captured (not declared missing)",
              "journal.jsonl" in m.get("files", []) and
              m.get("missing_files") == [], str(m))
        rc, out, _ = run(TOOL, ["verify", zdir], zero)
        check("C1 zero-byte journal backup verifies OK",
              rc == 0 and "VERIFY OK" in out, out)
    # C2: truly empty records dir -> legal empty baseline (regression guard).
    truly = os.path.join(tmp, "jtype-empty")
    os.makedirs(truly, exist_ok=True)
    edest = os.path.join(tmp, "jbk-empty")
    rc, out, err = run(TOOL, ["backup", "--to", edest, "--allow-same-fs"], truly)
    check("C2 empty baseline backup exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    edir = first_backup_dir(edest)
    check("C2 empty baseline created", edir is not None)
    if edir:
        rc, out, _ = run(TOOL, ["verify", edir], truly)
        check("C2 empty baseline verifies OK", rc == 0 and "VERIFY OK" in out, out)
    # C3: a normal regular journal backs up and restores normally.
    nrec, nbackup = mk_valid(tmp, "jtype-normal")
    check("C3 normal journal backup produced a dir", nbackup is not None)
    tgt = os.path.join(tmp, "jtype-normal-tgt")
    os.makedirs(tgt, exist_ok=True)
    rc, out, err = run(TOOL, ["restore", nbackup, "--yes"], tgt)
    check("C3 normal journal restores into an empty target",
          rc == 0 and os.path.exists(os.path.join(tgt, "journal.jsonl")),
          f"rc={rc} out={out} err={err}")
    if os.path.exists(os.path.join(tgt, "journal.jsonl")):
        check("C3 restored journal matches the backup",
              sha(os.path.join(tgt, "journal.jsonl")) ==
              sha(os.path.join(nbackup, "journal.jsonl")))


def _journal_missing_suite(tmp):
    # A missing journal with derived files present is the dangerous state. Build
    # it by generating derived files, then deleting the journal (and optionally
    # trimming the derived set).
    def records_missing_journal(tag, keep):
        records = os.path.join(tmp, f"records-{tag}")
        write_journal(records, [rec("C0001", "keep", f"comment-{tag}")])
        run(TOOL, ["backup", "--to", os.path.join(tmp, f"bkgen-{tag}"),
                   "--allow-same-fs"], records)
        os.remove(os.path.join(records, "journal.jsonl"))
        for n in REQUIRED_FILES:
            p = os.path.join(records, n)
            if n not in keep and os.path.exists(p):
                os.remove(p)
        return records

    def backup_tracks_calls(records, dest):
        snippet = (
            "calls = []\n"
            "def boom(*a, **k):\n"
            "    calls.append('x')\n"
            "    raise RuntimeError('SHOULD-NOT-BE-CALLED')\n"
            "store.rebuild = boom\n"
            "B.build_decisions.write = boom\n"
            f"rc = B.cmd_backup(type('A',(),{{'to':{dest!r},'allow_same_fs':True}})())\n"
            "print('RC', rc)\n"
            "print('REFRESH_CALLS', len(calls))\n")
        return run_inproc(records, snippet)

    def restore_tracks_calls(target, backup_dir):
        snippet = (
            "calls = []\n"
            "def boom(*a, **k):\n"
            "    calls.append('x')\n"
            "    raise RuntimeError('SHOULD-NOT-BE-CALLED')\n"
            "store.rebuild = boom\n"
            "B.build_decisions.write = boom\n"
            f"rc = B.cmd_restore(type('A',(),{{'dir':{backup_dir!r},'yes':True}})())\n"
            "print('RC', rc)\n"
            "print('REFRESH_CALLS', len(calls))\n")
        return run_inproc(target, snippet)

    # --- Group A: backup refuses when the journal is gone but derived files remain.
    print("26. Group A: backup refuses when journal is missing but derived data remains")
    group_a = [
        ("A1 decisions only", ["decisions.jsonl"]),
        ("A2 snapshot only", ["snapshot.json"]),
        ("A3 CSV only", ["export-review-records.csv"]),
        ("A4 JSON only", ["export-review-records.json"]),
        ("A5 all derived", list(REQUIRED_FILES)),
    ]
    for i, (label, keep) in enumerate(group_a):
        records = records_missing_journal(f"A{i}", keep)
        before = tree_state(records)
        dest = os.path.join(tmp, f"bkA{i}")
        rc, out, err = run(TOOL, ["backup", "--to", dest, "--allow-same-fs"], records)
        check(f"{label}: backup refuses (non-zero)", rc != 0, f"rc={rc} out={out}")
        check(f"{label}: message names the missing journal",
              "journal.jsonl is missing" in out, out)
        check(f"{label}: message flags the abnormal state",
              "abnormal state" in out, out)
        check(f"{label}: no refresh/rebuild message (guard fired first)",
              "could not refresh" not in out, out)
        check(f"{label}: no backup directory written", first_backup_dir(dest) is None)
        check(f"{label}: derived file hashes unchanged", tree_state(records) == before)
        # Prove no rebuild / build_decisions.write was called.
        rc2, out2, err2 = backup_tracks_calls(records, os.path.join(tmp, f"bkA{i}t"))
        check(f"{label}: store.rebuild/build_decisions.write NOT called",
              "REFRESH_CALLS 0" in out2 and "RC 1" in out2, f"out={out2} err={err2}")
        check(f"{label}: tracked-call run wrote no backup",
              first_backup_dir(os.path.join(tmp, f"bkA{i}t")) is None)

    # --- Group B: a genuinely empty records dir still yields a valid baseline.
    print("27. Group B: a truly empty records dir still yields a valid empty baseline")
    empty = os.path.join(tmp, "records-trueempty")
    os.makedirs(empty, exist_ok=True)
    rc, out, err = run_inproc(
        empty, f"print('EMPTY', B._records_dir_state({empty!r})['empty'])")
    check("state classifies the dir as empty", "EMPTY True" in out, out)
    ebk = os.path.join(tmp, "bk-trueempty")
    rc, out, err = run(TOOL, ["backup", "--to", ebk, "--allow-same-fs"], empty)
    check("empty baseline backup exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    edest = first_backup_dir(ebk)
    check("baseline backup created", edest is not None)
    if edest:
        m = load_manifest(edest)
        check("format is poet-review-backup/2",
              m.get("format") == "poet-review-backup/2", str(m.get("format")))
        check("journal.jsonl declared missing",
              m.get("missing_files") == ["journal.jsonl"], str(m.get("missing_files")))
        check("four required files present",
              sorted(m.get("files", [])) == sorted(REQUIRED_FILES), str(m.get("files")))
        rc, out, _ = run(TOOL, ["verify", edest], empty)
        check("empty baseline verifies OK", rc == 0 and "VERIFY OK" in out, out)
        dpath = os.path.join(edest, "decisions.jsonl")
        n = len([ln for ln in open(dpath, encoding="utf-8").read().splitlines() if ln.strip()])
        check("137 pending candidates preserved", n == 137, f"n={n}")

    # --- Group C: restore target protection.
    print("28. Group C: restore refuses an incomplete target and never overwrites")
    _, good_backup = mk_valid(tmp, "c-refsrc")

    def target_with(tag, keep, with_journal=False):
        t = os.path.join(tmp, f"target-{tag}")
        os.makedirs(t, exist_ok=True)
        if with_journal:
            write_journal(t, [rec("C0002", "hold", "target-journal")])
        for n in keep:
            with open(os.path.join(t, n), "w", encoding="utf-8") as fh:
                fh.write(f"pre-existing {n}\n")
        return t

    refuse_cases = [
        ("C1 no journal, decisions present", ["decisions.jsonl"]),
        ("C2 no journal, snapshot present", ["snapshot.json"]),
        ("C3 no journal, CSV present", ["export-review-records.csv"]),
        ("C4 no journal, JSON present", ["export-review-records.json"]),
    ]
    for i, (label, keep) in enumerate(refuse_cases):
        tgt = target_with(f"C{i}", keep)
        before = tree_state(tgt)
        rc, out, err = run(TOOL, ["restore", good_backup, "--yes"], tgt,
                           backup_dir=os.path.join(tmp, f"safetyC{i}"))
        check(f"{label}: restore refused (non-zero)", rc != 0, f"rc={rc} out={out}")
        check(f"{label}: message flags incomplete target",
              "incomplete" in out or "abnormal" in out, out)
        check(f"{label}: target files/hashes unchanged", tree_state(tgt) == before)
        check(f"{label}: no journal created in target",
              not os.path.exists(os.path.join(tgt, "journal.jsonl")))
        # Prove the refusal happens before any rebuild / safety backup side effects.
        rc2, out2, err2 = restore_tracks_calls(tgt, good_backup)
        check(f"{label}: store.rebuild/build_decisions.write NOT called",
              "REFRESH_CALLS 0" in out2 and "RC 1" in out2, f"out={out2} err={err2}")
        check(f"{label}: tracked-call run left target unchanged",
              tree_state(tgt) == before)

    # C5: a completely empty target is allowed to restore.
    print("C5 no journal, no derived files -> restore allowed")
    empty_tgt = os.path.join(tmp, "target-empty")
    os.makedirs(empty_tgt, exist_ok=True)
    rc, out, err = run(TOOL, ["restore", good_backup, "--yes"], empty_tgt)
    check("C5: restore exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    check("C5: journal restored",
          os.path.exists(os.path.join(empty_tgt, "journal.jsonl")))
    check("C5: restored journal matches backup",
          sha(os.path.join(empty_tgt, "journal.jsonl")) ==
          sha(os.path.join(good_backup, "journal.jsonl")))

    # C6: a target WITH a journal restores normally once the safety backup succeeds.
    print("C6 target has a journal -> safety backup then restore (positive control)")
    base = cross_fs_base(tmp)
    if base is None:
        print("  [SKIP] no writable cross-filesystem dir for the safety backup")
    else:
        tgt = target_with("C6", [], with_journal=True)
        safety = os.path.join(base, f"poet-backup-test-c6-{os.getpid()}")
        try:
            rc, out, err = run(TOOL, ["restore", good_backup, "--yes"], tgt, backup_dir=safety)
            check("C6: restore exits 0", rc == 0, f"rc={rc} out={out} err={err}")
            check("C6: target matches the backup journal",
                  sha(os.path.join(tgt, "journal.jsonl")) ==
                  sha(os.path.join(good_backup, "journal.jsonl")))
            check("C6: a safety backup of the prior state was written",
                  first_backup_dir(safety) is not None)
        finally:
            shutil.rmtree(safety, ignore_errors=True)

    # C7: a target WITH a journal but a failing safety backup is refused.
    print("C7 target has a journal but safety backup fails -> restore refused")
    tgt = target_with("C7", [], with_journal=True)
    before = tree_state(tgt)
    snippet = ("store.rebuild = lambda *a, **k: (_ for _ in ()).throw("
               "RuntimeError('mock safety-backup failure')); "
               f"raise SystemExit(B.cmd_restore(type('A',(),{{'dir':{good_backup!r},"
               f"'yes':True}})()))")
    rc, out, err = run_inproc(tgt, snippet)
    check("C7: restore refused", "refusing to restore" in out, out)
    check("C7: target unchanged after refusal", tree_state(tgt) == before)

    # C8: no --force (or any bypass) exists on the restore parser.
    print("C8 restore has no --force / bypass flag")
    rc, out, err = run(TOOL, ["restore", good_backup, "--yes", "--force"], empty_tgt)
    check("C8: --force is rejected as an unknown option", rc != 0, f"rc={rc} out={out}")
    check("C8: error mentions force", "force" in (out + err).lower(), f"out={out} err={err}")


def _verification_suite(tmp):
    def m_empty_checksum(d):
        open(os.path.join(d, "SHA256SUMS.txt"), "w").close()

    def m_drop_journal_checksum(d):
        write_checksums(d, [n for n in DATA_FILES if n != "journal.jsonl"])

    def m_list_mismatch(d):
        write_checksums(d, ["snapshot.json", "decisions.jsonl"])
        for n in ["export-review-records.csv", "export-review-records.json", "journal.jsonl"]:
            os.remove(os.path.join(d, n))

    def m_rm_manifest(d):
        os.remove(os.path.join(d, "manifest.json"))

    def m_rm_checksum(d):
        os.remove(os.path.join(d, "SHA256SUMS.txt"))

    def m_rm_file(d):
        os.remove(os.path.join(d, "decisions.jsonl"))

    def m_corrupt(d):
        with open(os.path.join(d, "decisions.jsonl"), "a", encoding="utf-8") as fh:
            fh.write('{"tampered": true}\n')

    def m_dup(d):
        line = open(os.path.join(d, "SHA256SUMS.txt"), encoding="utf-8").read().strip().splitlines()[0]
        with open(os.path.join(d, "SHA256SUMS.txt"), "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def m_traversal(d):
        write_checksums(d, DATA_FILES, extra_lines=[f"{'a'*64}  ../evil"])

    def m_absolute(d):
        write_checksums(d, DATA_FILES, extra_lines=[f"{'a'*64}  /etc/passwd"])

    def m_declared_missing_present(d):
        m = load_manifest(d)
        m["files"] = [n for n in m["files"] if n != "journal.jsonl"]
        m["missing_files"] = sorted(m["missing_files"] + ["journal.jsonl"])
        save_manifest(d, m)
        write_checksums(d, [n for n in DATA_FILES if n != "journal.jsonl"])

    def m_symlink(d):
        real = os.path.join(d, "_real.jsonl")
        shutil.move(os.path.join(d, "journal.jsonl"), real)
        os.symlink(real, os.path.join(d, "journal.jsonl"))

    def m_unknown_name(d):
        write_checksums(d, DATA_FILES, extra_lines=[f"{'a'*64}  evil.txt"])

    cases = [
        ("12 empty checksum list", m_empty_checksum, "empty"),
        ("13 checksum omits journal.jsonl", m_drop_journal_checksum, "does not match"),
        ("14 manifest/checksum list mismatch", m_list_mismatch, "does not match"),
        ("15 missing manifest.json", m_rm_manifest, "missing manifest.json"),
        ("16 missing SHA256SUMS.txt", m_rm_checksum, "missing SHA256SUMS.txt"),
        ("17 missing data file", m_rm_file, "missing data file"),
        ("18 content changed (hash mismatch)", m_corrupt, "checksum mismatch"),
        ("19 duplicate checksum entry", m_dup, "duplicate"),
        ("20 '../' path traversal", m_traversal, "unsafe file name"),
        ("21 absolute path", m_absolute, "unsafe file name"),
        ("22 declared missing but present", m_declared_missing_present, "declared missing"),
        ("23 data file replaced by symlink", m_symlink, "symlink"),
        ("24 unknown/illegal file name", m_unknown_name, "does not match"),
    ]

    for label, mutate, expect in cases:
        print(f"{label}: must fail verification and never touch the target")
        tag = label.split()[0]
        src_records, dest = mk_valid(tmp, f"v{tag}")
        mutate(dest)
        rc, out, err = run(TOOL, ["verify", dest], src_records)
        check(f"{label}: verify fails", rc != 0 and "VERIFY FAILED" in out, out)
        check(f"{label}: message mentions '{expect}'", expect in out, out)
        target = os.path.join(tmp, f"target-{tag}")
        write_journal(target, [rec("C0099", "keep", "must survive")])
        before = tree_state(target)
        rc2, out2, err2 = run(TOOL, ["restore", dest, "--yes"], target,
                              backup_dir=os.path.join(tmp, f"safety-{tag}"))
        check(f"{label}: restore refused", rc2 != 0, f"rc={rc2} out={out2}")
        check(f"{label}: target unchanged", tree_state(target) == before)


if __name__ == "__main__":
    main()
