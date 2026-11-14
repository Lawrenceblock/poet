#!/usr/bin/env python3
"""Acceptance tests for the author-review BACKUP / RESTORE tooling (stdlib only).

Exercises tools/review/backup_review_data.py end to end in isolated temp dirs:

  1. a normal backup succeeds and is verifiable
  2. a refresh failure aborts the backup (fail-closed, no stale backup)
  3. a same-filesystem destination is refused
  4. restore is refused when the backup fails verification
  5. an empty dataset can still produce a baseline backup
  6. restore into an empty directory is complete and consistent
  7. private review comments never reach the public artefacts
  8. no token / private data in tracked files, gitignore or the working tree
  9. a repeat backup never overwrites an earlier valid backup

Every test uses throwaway temp directories and a synthetic journal. The real
author records under docs/author-review/review-records/ are never read or
written. Exit code 0 = all tests passed.

  python3 tools/review/test_backup_system.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TOOL = os.path.join(HERE, "backup_review_data.py")
ARTIFACTS = os.path.join(HERE, "build_review_artifacts.py")
REAL_RECORDS = os.path.join(ROOT, "docs", "author-review", "review-records")

DATA_FILES = ["journal.jsonl", "snapshot.json", "decisions.jsonl",
              "export-review-records.csv", "export-review-records.json"]

fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


def run(tool, args, records_dir, backup_dir=None, extra_env=None):
    env = {**os.environ, "REVIEW_RECORDS_DIR": records_dir}
    if backup_dir is not None:
        env["REVIEW_BACKUP_DIR"] = backup_dir
    if extra_env:
        env.update(extra_env)
    p = subprocess.run([sys.executable, tool, *args], env=env,
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def write_journal(records_dir, lines):
    os.makedirs(records_dir, exist_ok=True)
    with open(os.path.join(records_dir, "journal.jsonl"), "w", encoding="utf-8") as fh:
        for obj in lines:
            import json
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


def main():
    tmp = tempfile.mkdtemp(prefix="backup-test-")
    try:
        _run_all(tmp)
    finally:
        # Restore any read-only dirs before cleanup.
        for dirpath, dirnames, _files in os.walk(tmp):
            for d in dirnames:
                try:
                    os.chmod(os.path.join(dirpath, d), 0o755)
                except OSError:
                    pass
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
        for name in ["journal.jsonl", "snapshot.json", "decisions.jsonl",
                     "SHA256SUMS.txt", "manifest.json"]:
            check(f"backup contains {name}", os.path.exists(os.path.join(dest, name)))
        rc2, out2, _ = run(TOOL, ["verify", dest], records)
        check("verify exits 0", rc2 == 0 and "VERIFY OK" in out2, out2)

    # 2. A refresh failure aborts the backup (fail-closed).
    print("2. a refresh failure aborts the backup (fail-closed)")
    ro_records = os.path.join(tmp, "records-ro")
    sentinel = f"PRIVATE-{uuid.uuid4().hex}"
    write_journal(ro_records, [rec("C0002", "keep", sentinel)])
    ro_backup = os.path.join(tmp, "backup-ro")
    os.makedirs(ro_backup, exist_ok=True)
    os.chmod(ro_records, 0o555)  # derived-file refresh must now fail
    try:
        rc, out, err = run(TOOL, ["backup", "--to", ro_backup, "--allow-same-fs"],
                           ro_records)
    finally:
        os.chmod(ro_records, 0o755)
    check("backup exits non-zero", rc != 0, f"rc={rc}")
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
    before = open(os.path.join(target, "journal.jsonl"), encoding="utf-8").read()
    rc, out, err = run(TOOL, ["restore", bad, "--yes"], target,
                       backup_dir=os.path.join(tmp, "safety"))
    check("verify of tampered backup fails", "VERIFY FAILED" in out, out)
    check("restore refused (non-zero)", rc != 0, f"rc={rc} out={out}")
    check("target records unchanged",
          open(os.path.join(target, "journal.jsonl"), encoding="utf-8").read() == before)

    # 5. An empty dataset can still produce a baseline backup.
    print("5. an empty dataset can still produce a baseline backup")
    empty = os.path.join(tmp, "records-empty")
    os.makedirs(empty, exist_ok=True)
    empty_bk = os.path.join(tmp, "backup-empty")
    rc, out, err = run(TOOL, ["backup", "--to", empty_bk, "--allow-same-fs"], empty)
    check("empty backup exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    edest = first_backup_dir(empty_bk)
    check("baseline backup created", edest is not None)
    if edest:
        dpath = os.path.join(edest, "decisions.jsonl")
        check("decisions.jsonl present", os.path.exists(dpath))
        if os.path.exists(dpath):
            n = len([ln for ln in open(dpath, encoding="utf-8").read().splitlines() if ln.strip()])
            check("all 137 candidates listed as pending", n == 137, f"n={n}")

    # 6. Restore into an empty directory is complete and consistent.
    print("6. restore into an empty directory is complete and consistent")
    src_records = os.path.join(tmp, "records-src")
    write_journal(src_records, [rec("C0003", "keep", "第一首"), rec("C0004", "exclude", "第二首")])
    src_bk = os.path.join(tmp, "backup-src")
    run(TOOL, ["backup", "--to", src_bk, "--allow-same-fs"], src_records)
    sdest = first_backup_dir(src_bk)
    fresh = os.path.join(tmp, "records-fresh")  # no journal -> no safety backup needed
    os.makedirs(fresh, exist_ok=True)
    rc, out, err = run(TOOL, ["restore", sdest, "--yes"], fresh)
    check("restore exits 0", rc == 0, f"rc={rc} out={out} err={err}")
    import hashlib

    def sha(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest()

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
    # If a preview build exists, the comment must not be in it either.
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
    # A token-looking assignment must not appear in any tracked text file.
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
    # The synthetic secret must not appear anywhere tracked or in the diff.
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

    # 10. Restoring over existing records is protected (fail-closed safety backup).
    print("10. restoring over existing records is protected (fail-closed safety backup)")
    tgt = os.path.join(tmp, "records-overwrite")
    write_journal(tgt, [rec("C0007", "keep", "current authoritative")])
    tgt_before = sha(os.path.join(tgt, "journal.jsonl"))
    good_src = os.path.join(tmp, "backup-goodsrc")
    write_journal(os.path.join(tmp, "records-goodsrc"), [rec("C0007", "exclude", "restored")])
    run(TOOL, ["backup", "--to", good_src, "--allow-same-fs"],
        os.path.join(tmp, "records-goodsrc"))
    gdest = first_backup_dir(good_src)
    # Force the pre-restore safety backup onto the SAME filesystem as the target
    # records, so it must be refused and the restore must therefore abort.
    same_fs_safety = os.path.join(tmp, "safety-same-fs")
    os.makedirs(same_fs_safety, exist_ok=True)
    rc, out, err = run(TOOL, ["restore", gdest, "--yes"], tgt,
                       backup_dir=same_fs_safety)
    check("restore refused when safety backup impossible", rc != 0, f"rc={rc} out={out}")
    check("existing records untouched by refused restore",
          sha(os.path.join(tgt, "journal.jsonl")) == tgt_before)

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


if __name__ == "__main__":
    main()
