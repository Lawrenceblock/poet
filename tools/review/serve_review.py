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
  * ?test=1 (or a body field "test": true) routes a save to the isolated test
    journal; the query flag alone is enough, so a test link can never write to
    the author's real records.
  * If REVIEW_ACCESS_TOKEN is set, every /review/ page and /api/ request must
    present it (via ?token=, X-Review-Token header, or the review_token cookie
    set on first use). Without it the preview is open to anyone who has the URL,
    so set it whenever the preview host is reachable by others.
  * REVIEW_FORCE_SAVE_ERROR=1 makes every save fail (used to test the UI's
    failure feedback; it must never report success).
"""
import argparse
import json
import os
import secrets
import socketserver
import sys
import http.server

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import store  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PUBLIC = os.path.join(ROOT, "hugo", "public")
ACCESS_TOKEN = os.environ.get("REVIEW_ACCESS_TOKEN") or ""


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=PUBLIC, **kw)

    def log_message(self, fmt, *a):
        # Keep the console quiet for normal hits, but always record non-2xx
        # responses (e.g. a 404 for a poem page) so a fault leaves a trace.
        # The query string is stripped so an access token passed as ?token=
        # is never written to the log.
        try:
            code = a[1] if len(a) > 1 else ""
            if str(code).startswith("2"):
                return
            safe = self.path.split("?", 1)[0]
            sys.stderr.write(f"[review] {self.address_string()} "
                             f"{self.command} {safe} -> {code}\n")
            sys.stderr.flush()
        except Exception:
            pass

    # ---------- access control ----------
    def _presented_token(self):
        if "?" in self.path:
            for pair in self.path.split("?", 1)[1].split("&"):
                if pair.startswith("token="):
                    return pair[len("token="):]
        if self.headers.get("X-Review-Token"):
            return self.headers.get("X-Review-Token")
        for c in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = c.strip().partition("=")
            if k == "review_token":
                return v
        return None

    def _authorized(self):
        if not ACCESS_TOKEN:
            return True
        return secrets.compare_digest(self._presented_token() or "", ACCESS_TOKEN)

    def _needs_auth(self):
        # Only the review area and its API are private. The reading pages stay
        # open so the author can browse them without a token; the review pages
        # and every /api/ endpoint require it.
        if not ACCESS_TOKEN:
            return False
        path = self.path.split("?", 1)[0]
        return path == "/review" or path.startswith("/review/") \
            or path == "/api" or path.startswith("/api/")

    def _deny(self):
        body = json.dumps({"ok": False, "error": "需要访问令牌（?token=…）"},
                          ensure_ascii=False).encode("utf-8")
        self.send_response(401)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("WWW-Authenticate", 'Bearer realm="author-review"')
        self.end_headers()
        self.wfile.write(body)

    def _maybe_set_cookie(self):
        tok = self._presented_token()
        if ACCESS_TOKEN and tok and secrets.compare_digest(tok, ACCESS_TOKEN):
            self.send_header("Set-Cookie",
                             f"review_token={tok}; Path=/; HttpOnly; SameSite=Lax")

    def end_headers(self):
        self._maybe_set_cookie()
        super().end_headers()

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
        if self._needs_auth() and not self._authorized():
            return self._deny()
        # A token supplied in the URL is accepted once, then stripped: redirect
        # to the same path without it so it does not linger in history, logs or
        # shared links. The cookie set by end_headers() keeps the session valid.
        if "?" in self.path and "token=" in self.path.split("?", 1)[1]:
            path = self.path.split("?", 1)[0]
            self.send_response(303)
            self.send_header("Location", path)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
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
        if not self._authorized():
            return self._deny()
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

        # ?test=1 must be enough on its own to keep test writes out of the
        # author's real journal, so force the flag when the query asks for it.
        if self._is_test():
            payload["test"] = True

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

    # ---------- HEAD / OPTIONS ----------
    def _deny_head(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Bearer realm="author-review"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        # SimpleHTTPRequestHandler answers HEAD without going through do_GET, so
        # it needs its own gate; otherwise a HEAD leaks whether a page exists.
        if self._needs_auth() and not self._authorized():
            return self._deny_head()
        return super().do_HEAD()

    def do_OPTIONS(self):
        if self._needs_auth() and not self._authorized():
            return self._deny_head()
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    global PUBLIC
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=12000)
    # Serve a specific preview tree (e.g. an isolated visual-refinement
    # candidate). Access control, /api/* and token handling are unchanged.
    ap.add_argument("--dir", default=PUBLIC)
    args = ap.parse_args()
    PUBLIC = os.path.abspath(args.dir)
    if not os.path.isdir(PUBLIC):
        print(f"ERROR: {PUBLIC} not found; run tools/preview/build_preview.py first")
        sys.exit(1)
    with ThreadingServer(("0.0.0.0", args.port), Handler) as httpd:
        print(f"serving {PUBLIC} + /api/* on 0.0.0.0:{args.port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
