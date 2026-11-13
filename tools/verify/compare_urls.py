#!/usr/bin/env python3
"""新旧站点 URL 逐一比对（只读）。

用法：
    python3 tools/verify/compare_urls.py --old https://poet.ismaelan.com \
        --new https://poet-preview.vercel.app --urls-file urls.txt

urls.txt 每行一个路径（以 / 开头）。
输出：每条路径在旧站/新站的 HTTP 状态与是否一致。
"""
import argparse
import urllib.request
import urllib.error
import sys


def head_status(base, path, timeout=15):
    url = base.rstrip("/") + path
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "poet-url-compare/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001
        return f"ERR({e.__class__.__name__})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--urls-file", required=True)
    args = ap.parse_args()

    paths = [ln.strip() for ln in open(args.urls_file, encoding="utf-8")
             if ln.strip() and not ln.startswith("#")]
    if not paths:
        print("没有可比较的路径。", file=sys.stderr)
        return 2

    print(f"{'路径':<40} {'旧站':>6} {'新站':>6}  一致")
    print("-" * 66)
    mismatch = 0
    for p in paths:
        o = head_status(args.old, p)
        n = head_status(args.new, p)
        same = "✅" if o == n else "❌"
        if o != n:
            mismatch += 1
        print(f"{p:<40} {str(o):>6} {str(n):>6}  {same}")
    print("-" * 66)
    print(f"共 {len(paths)} 条，{mismatch} 条不一致。")
    return 1 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
