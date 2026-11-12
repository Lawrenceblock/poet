#!/usr/bin/env python3
"""Author-review server: static preview + JSON review API (stdlib only).

Serves the built preview (hugo/public) exactly like serve_preview.py, and adds
a tiny JSON API backed by tools/review/store.py so the author can really save,
re-read and export review decisions.

Endpoints
---------
  GET  /api/health                 -> {"ok": true}
  GET  /api/review/<candidate_id>  -> current record for one candidate
  GET  /api/reviews                -> all records + progress
  POST /api/review                 -> save one record  {"candidate_id",...}
  GET  /api/export.csv             -> download CSV of all candidates
  GET  /api/export.json            -> download JSON of all candidates

Safety
------
  * Writes go only through store.save(), which whitelists candidate_id and
    enum values and never touches poem text, the feed or the candidate CSV.
  * REVIEW_FORCE_SAVE_ERROR=1 makes every save fail (used to test the UI's
    failure feedback; it must never report success).
"""
import argparse
import json
import os
import socketserver
import sys
import http.server

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import store  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PUBLIC = os.path.join(ROOT, "hugo", "public")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=PUBLIC, **kw)

    def log_message(self, *a):
        pass

    # ---------- helpers ----------
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _is_test(self):
        q = self.path.split("?", 1)[1] if "?" in self.path else ""
        return "test=1" in q

    def _send_file(self, path, ctype, download_name=None):
        if not os.path.exists(path):
            self._json(404, {"ok": False, "error": "not found"})
            return
        with open(path, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        if download_name:
            self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
        self.end_headers()
        self.wfile.write(data)

    def _apipath(self):
        """Return the API path, accepting it mounted at /api/ or /review/api/."""
        path = self.path.split("?", 1)[0]
        i = path.find("/api/")
        if i == -1:
            return path if path.endswith("/api") else None
        return path[i:]

    # ---------- GET ----------
    def do_GET(self):
        path = self._apipath()
        if path is not None:
            return self._api_get(path)
        return super().do_GET()

    def _api_get(self, path):
        if path == "/api/health":
            return self._json(200, {"ok": True})
        if path == "/api/reviews":
            return self._json(200, {"ok": True, "progress": store.progress(),
                                    "records": store.get_all()})
        if path.startswith("/api/review/"):
            cid = path[len("/api/review/"):].strip("/")
            rec = store.replay_test().get(cid) if self._is_test() else store.get_one(cid)
            return self._json(200, {"ok": True, "candidate_id": cid, "record": rec})
        if path == "/api/export.csv":
            store.rebuild()
            return self._send_file(store.EXPORT_CSV, "text/csv; charset=utf-8",
                                   "export-review-records.csv")
        if path == "/api/export.json":
            store.rebuild()
            return self._send_file(store.EXPORT_JSON, "application/json; charset=utf-8",
                                   "export-review-records.json")
        return self._json(404, {"ok": False, "error": "unknown api"})

    # ---------- POST ----------
    def do_POST(self):
        path = self._apipath()
        if path is None:
            return super().do_POST()
        if path != "/api/review":
            return self._json(404, {"ok": False, "error": "unknown api"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        raw = self.rfile.read(n) if n else b""
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"ok": False, "error": "请求体不是合法 JSON"})

        if os.environ.get("REVIEW_FORCE_SAVE_ERROR") == "1":
            return self._json(500, {"ok": False, "error": "服务端模拟写入失败（测试用）"})

        try:
            rec = store.save(payload)
        except ValueError as e:
            return self._json(400, {"ok": False, "error": str(e)})
        except Exception as e:  # noqa: BLE001 - surface any storage error to the client
            return self._json(500, {"ok": False, "error": f"保存失败：{e}"})
        return self._json(200, {"ok": True, "record": rec,
                                "progress": store.progress()})


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=12000)
    args = ap.parse_args()
    if not os.path.isdir(PUBLIC):
        print(f"ERROR: {PUBLIC} not found; run tools/preview/build_preview.py first")
        sys.exit(1)
    with ThreadingServer(("0.0.0.0", args.port), Handler) as httpd:
        print(f"serving {PUBLIC} + /api/* on 0.0.0.0:{args.port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
