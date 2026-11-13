#!/usr/bin/env python3
"""Serve the built preview (hugo/public) on the exposed work port.

Kept intentionally tiny: it only serves static files over HTTP so the author
can open a clickable HTTPS link. Run build_preview.py first.
"""
import argparse
import http.server
import os
import socketserver

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PUBLIC = os.path.join(ROOT, "hugo", "public")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, directory=None, **kw):
        super().__init__(*a, directory=directory or PUBLIC, **kw)

    def log_message(self, *a):  # keep the console quiet
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=12000)
    # Serve a specific directory (e.g. an isolated visual-refinement preview
    # built with build_preview.py --outdir). Defaults to hugo/public.
    ap.add_argument("--dir", default=PUBLIC)
    args = ap.parse_args()
    root = os.path.abspath(args.dir)

    def handler(*a, **kw):
        return Handler(*a, directory=root, **kw)

    with socketserver.TCPServer(("0.0.0.0", args.port), handler) as httpd:
        print(f"serving {root} on 0.0.0.0:{args.port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
