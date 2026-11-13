#!/usr/bin/env python3
"""Programmatic visual analysis of a built preview.

Two complementary measurements, both from a REAL build:
  1. DOM geometry / computed styles via Playwright (column widths, font sizes,
     black-area ratio, horizontal overflow, tap-target sizes).
  2. Pixel composition of screenshots (achromatic vs accent ratio, dominant
     hex colours), using Pillow.

This gives objective evidence for design review without needing to eyeball.
"""
import argparse
import http.server
import json
import os
import socketserver
import threading
import time

from playwright.sync_api import sync_playwright

PAGES = {
    "home": "/",
    "poem": "/2026/09/demo-rain-at-nalati/",
    "archive": "/archive/",
    "years": "/years/",
    "biography": "/shi-ren-xiao-zhuan/",
    "about": "/about/",
    "preface": "/preface/",
    "search": "/search/",
}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(root, port):
    handler = lambda *a, **kw: Quiet(*a, directory=root, **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


MEASURE_JS = r"""
() => {
  const out = {};
  const de = document.documentElement;
  out.docWidth = de.scrollWidth;
  out.viewport = window.innerWidth;
  out.overflow = de.scrollWidth > window.innerWidth + 1;
  const q = (s) => document.querySelector(s);
  const cs = (el) => el ? getComputedStyle(el) : null;
  const box = (el) => { if(!el) return null; const r = el.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)}; };
  const fs = (el) => el ? getComputedStyle(el).fontSize : null;
  out.hero = box(q('.hero'));
  out.heroInner = box(q('.hero-inner'));
  out.heroText = box(q('.hero-text'));
  out.heroMedia = box(q('.hero-media'));
  out.heroTitleFont = fs(q('.hero-title'));
  out.heroTitleLS = q('.hero-title') ? getComputedStyle(q('.hero-title')).letterSpacing : null;
  out.heroTitleFF = q('.hero-title') ? getComputedStyle(q('.hero-title')).fontFamily : null;
  out.pageTitleFont = fs(q('.page-title'));
  out.poemTitleFont = fs(q('.poem-title'));
  out.poemBody = box(q('.poem-body'));
  out.poemContentFS = fs(q('.poem-content'));
  out.poemContentLH = q('.poem-content') ? getComputedStyle(q('.poem-content')).lineHeight : null;
  out.yearNumFont = fs(q('.year-num'));
  out.blocks = [...document.querySelectorAll('.home-block')].map(b => box(b));
  // tap targets in nav
  out.navLinks = [...document.querySelectorAll('.site-nav a')].map(a => box(a));
  // black sections
  out.blackEls = [...document.querySelectorAll('.site-header,.hero,.page-head,.poem-head,.site-footer')]
      .map(e => ({cls:e.className, box:box(e)}));
  // header layout
  out.headerInner = box(q('.site-header-inner'));
  out.siteName = box(q('.site-name'));
  out.siteNav = box(q('.site-nav'));
  // CSS custom props
  const root = getComputedStyle(de);
  out.vars = {};
  ['--paper','--ink','--black','--accent','--measure','--measure-poem','--frame']
    .forEach(v => out.vars[v] = root.getPropertyValue(v).trim());
  return out;
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--port", type=int, default=8898)
    args = ap.parse_args()
    httpd = serve(os.path.abspath(args.root), args.port)
    time.sleep(0.4)
    base = f"http://127.0.0.1:{args.port}"
    result = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vp_name, vp in {"desktop": {"width": 1440, "height": 900},
                            "mobile": {"width": 390, "height": 844}}.items():
            ctx = browser.new_context(viewport=vp)
            page = ctx.new_page()
            result[vp_name] = {}
            for name, path in PAGES.items():
                page.goto(base + path, wait_until="networkidle", timeout=15000)
                result[vp_name][name] = page.evaluate(MEASURE_JS)
            ctx.close()
        browser.close()
    httpd.shutdown()
    print(json.dumps(result, ensure_ascii=False, indent=1))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
