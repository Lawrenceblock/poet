#!/usr/bin/env python3
"""Capture screenshots of the built preview for visual review.

Usage:
    python3 tools/preview/shoot.py --root <build dir> --out <screenshot dir> [--base URL]

Screenshots are taken from a real build served over HTTP, never from concept
art. Desktop = 1440x900, mobile = 390x844 (iPhone 12-ish), full page.
"""
import argparse
import http.server
import os
import socketserver
import threading
import time

from playwright.sync_api import sync_playwright

PAGES = [
    ("01-home", "/"),
    ("02-poem", "/2026/09/demo-rain-at-nalati/"),
    ("03-archive", "/archive/"),
    ("04-years", "/years/"),
    ("05-biography", "/shi-ren-xiao-zhuan/"),
    ("06-about", "/about/"),
    ("07-preface", "/preface/"),
    ("08-search", "/search/"),
    ("09-404", "/404.html"),
]

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(root, port):
    handler = lambda *a, **kw: Quiet(*a, directory=root, **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--prefix", default="")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    httpd = serve(os.path.abspath(args.root), args.port)
    time.sleep(0.4)
    base = f"http://127.0.0.1:{args.port}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vp_name, vp in VIEWPORTS.items():
            ctx = browser.new_context(viewport=vp, device_scale_factor=2)
            page = ctx.new_page()
            for name, path in PAGES:
                url = base + path
                try:
                    page.goto(url, wait_until="networkidle", timeout=15000)
                    page.wait_for_timeout(250)
                    out = os.path.join(args.out, f"{args.prefix}{name}-{vp_name}.png")
                    page.screenshot(path=out, full_page=True)
                    print("saved", out)
                except Exception as e:
                    print("FAIL", url, e)
            ctx.close()
        browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    main()
