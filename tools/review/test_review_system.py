#!/usr/bin/env python3
"""Automated acceptance tests for the author-review system (stdlib only).

Runs the review server in a temp RECORDS dir and exercises the full API:
save -> read back -> update -> progress -> export -> failure case -> isolation.

  python3 tools/review/test_review_system.py
Exit code 0 = all tests passed.
"""
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PORT = 12117

fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


def wait_port(port, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=10) as r:
        return r.status, r.read().decode("utf-8")


def post(path, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def start_server(extra_env):
    env = {**os.environ, **extra_env}
    return subprocess.Popen([sys.executable, os.path.join(HERE, "serve_review.py"),
                             "--port", str(PORT)], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    tmp = tempfile.mkdtemp(prefix="review-test-")
    real_records = os.path.join(ROOT, "docs", "author-review", "review-records")
    before = sorted(os.listdir(real_records)) if os.path.isdir(real_records) else []

    srv = start_server({"REVIEW_RECORDS_DIR": tmp})
    try:
        if not wait_port(PORT):
            print("server did not start"); sys.exit(2)

        print("1-4. save a new record (keep / single_poem / Chinese comment)")
        st, j = post("/review/api/review", {"candidate_id": "C0010", "status": "keep",
                                            "nature": "single_poem",
                                            "comment": "测试：确认保留，与旧站版本一致。"})
        check("save returns ok", st == 200 and j.get("ok") is True, str(j))
        check("save returns rev=1", j.get("record", {}).get("rev") == 1, str(j))
        check("save returns updated_at", bool(j.get("record", {}).get("updated_at")))

        print("5-6. reopen (GET) returns the three fields intact")
        st, body = get("/review/api/review/C0010")
        rec = json.loads(body).get("record") or {}
        check("GET status=keep", rec.get("status") == "keep")
        check("GET nature=single_poem", rec.get("nature") == "single_poem")
        check("GET comment intact", rec.get("comment") == "测试：确认保留，与旧站版本一致。")

        print("6b. record persisted on disk (journal + snapshot)")
        jpath = os.path.join(tmp, "journal.jsonl")
        check("journal.jsonl exists", os.path.exists(jpath))
        check("journal has 1 line", len(open(jpath, encoding="utf-8").read().strip().splitlines()) == 1)
        snap = json.load(open(os.path.join(tmp, "snapshot.json"), encoding="utf-8"))
        check("snapshot contains C0010", "C0010" in snap.get("records", {}))

        print("7. change to hold, save again -> rev=2, updated")
        st, j = post("/review/api/review", {"candidate_id": "C0010", "status": "hold",
                                            "nature": "single_poem",
                                            "comment": "测试：改为暂缓。"})
        check("update ok", st == 200 and j.get("ok") is True)
        check("rev incremented to 2", j.get("record", {}).get("rev") == 2, str(j))
        st, body = get("/review/api/review/C0010")
        check("status now hold", json.loads(body)["record"]["status"] == "hold")

        print("8. progress reflects the update")
        st, body = get("/review/api/reviews")
        prog = json.loads(body)["progress"]
        check("reviewed == 1", prog["reviewed"] == 1, str(prog))
        check("total == 137", prog["total"] == 137, str(prog))
        check("by_status.hold == 1", prog["by_status"]["hold"] == 1, str(prog))

        print("9. export CSV contains the record")
        st, csv_text = get("/api/export.csv")
        check("csv status 200", st == 200)
        row = [l for l in csv_text.splitlines() if l.startswith("C0010,")]
        check("csv has C0010 row", len(row) == 1, str(row[:1]))
        check("csv row says 暂缓", row and "暂缓" in row[0])

        print("10. export JSON contains the record")
        st, js = get("/api/export.json")
        data = json.loads(js)
        r010 = [r for r in data["records"] if r["candidate_id"] == "C0010"]
        check("json has C0010", len(r010) == 1)
        check("json status hold", r010 and r010[0]["status"] == "hold")
        check("json comment intact", r010 and r010[0]["comment"] == "测试：改为暂缓。")

        print("12. two candidates do not overwrite each other")
        post("/review/api/review", {"candidate_id": "C0002", "status": "exclude",
                                    "nature": "non_poem", "comment": "测试：非诗。"})
        a = json.loads(get("/review/api/review/C0010")[1])["record"]
        b = json.loads(get("/review/api/review/C0002")[1])["record"]
        check("C0010 still hold", a["status"] == "hold" and a["nature"] == "single_poem")
        check("C0002 exclude/non_poem", b["status"] == "exclude" and b["nature"] == "non_poem")
        check("records independent", a["comment"] != b["comment"])

        print("invalid input is rejected (whitelist)")
        st, j = post("/review/api/review", {"candidate_id": "HACK", "status": "keep"})
        check("unknown candidate rejected", st == 400 and j.get("ok") is False, str(j))
        st, j = post("/review/api/review", {"candidate_id": "C0010", "status": "DROP TABLE"})
        check("bad status rejected", st == 400 and j.get("ok") is False, str(j))

        print("11. forced save failure is reported as failure (never success)")
        # start a second server that always fails writes
        port2 = PORT + 1
        env2 = {**os.environ, "REVIEW_RECORDS_DIR": tmp, "REVIEW_FORCE_SAVE_ERROR": "1"}
        srv2 = subprocess.Popen([sys.executable, os.path.join(HERE, "serve_review.py"),
                                 "--port", str(port2)], env=env2,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            ok = wait_port(port2)
            check("failure server started", ok)
            if ok:
                data = json.dumps({"candidate_id": "C0010", "status": "keep"}).encode()
                req = urllib.request.Request(f"http://127.0.0.1:{port2}/review/api/review",
                                             data=data, method="POST",
                                             headers={"Content-Type": "application/json"})
                try:
                    urllib.request.urlopen(req, timeout=10)
                    code, body = 200, {}
                except urllib.error.HTTPError as e:
                    code, body = e.code, json.loads(e.read().decode("utf-8"))
                check("forced-failure returns non-2xx", code >= 400, str(code))
                check("forced-failure says ok=false", body.get("ok") is False, str(body))
        finally:
            srv2.terminate()
            try:
                srv2.wait(timeout=5)
            except subprocess.TimeoutExpired:
                srv2.kill()

    finally:
        srv.terminate()
        try:
            srv.wait(timeout=5)
        except subprocess.TimeoutExpired:
            srv.kill()
        shutil.rmtree(tmp, ignore_errors=True)

    print("13. real records dir untouched by tests")
    after = sorted(os.listdir(real_records)) if os.path.isdir(real_records) else []
    check("no journal-test.jsonl leaked to real dir", "journal-test.jsonl" not in after)
    check("real dir unchanged", before == after, f"{before} -> {after}")

    print()
    if fails:
        print(f"FAILURES: {len(fails)} -> {fails}")
        sys.exit(1)
    print("OK: all review-system tests passed")


if __name__ == "__main__":
    main()
