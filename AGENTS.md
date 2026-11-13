# AGENTS.md — 安然诗歌档案 / Anran Poetry Archive

Repository-specific knowledge for agents working in this repo.

## What this repo is

A Hugo site (`hugo/`) plus a set of read-only census/verification tools
(`tools/`) and an author-review system. **`main` is Jekyll-only (13 files).**
The full Hugo site and the author-review system live on the design branches,
not on `main`:

- `design/phase3-ammons-editorial-2026-11-13` — full Hugo site + author review
- `design/poet-visual-final-2026-11-13` — the visual-final candidate (built on phase3)

Do not conclude the Hugo site is missing just because `main` lacks it; check the
candidate branches and their history.

## Build & verify (must run from repo root)

Hugo **Extended v0.168.0** (matches `hugo/vercel.json` `HUGO_VERSION`).
On this sandbox it installs to `$HOME/bin`; run `export PATH="$HOME/bin:$PATH"`.

```bash
# Full preview (Hugo site + /review/ pages + verbatim check)
python3 tools/preview/build_preview.py --baseurl "http://localhost:12000/"

# Hugo-only production build
cd hugo && hugo --gc --minify --baseURL "https://poet.ismaelan.com/" -d /tmp/prod

# Verification suite (all read-only)
python3 tools/verify/check_links.py --root <build-dir>          # 0 broken links
python3 tools/verify/check_production_output.py --root <prod>   # no /review/ leaks
python3 tools/author-review/verify_verbatim.py                  # 137/137 poems identical
```

## Author-review system (`/review/`)

- 137 candidate poems; the committed HTML under `docs/author-review/site/` is the
  **verified content baseline**. Regenerating with `tools/author-review/build_review_site.py`
  requires the Blogger feed at `work/feed/feed-full-*.json`
  (fetch with `tools/poetry-discovery/fetch_feed.py`, then copy `work/feed-full-*.json`
  into `work/feed/`). With the feed present, regeneration is CSS-only vs. the baseline.
- Serve it with `REVIEW_ACCESS_TOKEN=... python3 tools/review/serve_review.py --port 12000`.
- Security gate: `/review/` and `/api/*` return **401** without a token
  (`?token=`, `X-Review-Token`, or `review_token` cookie). `?test=1` routes writes
  to an isolated test journal so acceptance tests never touch real records.
- **Never** weaken the gate or commit review records / tokens.

## Hard constraints for visual work

- Do not modify poem text, biography, preface, archive text, or review records.
- Do not change URLs, slugs, permalinks, or search behaviour.
- Do not touch `main`, merge PRs, deploy, or change DNS/domain/Vercel settings.
- Work on a new branch; open a draft PR for author review.

## Design system (visual-final)

`--paper #FAF9F7` / `--ink #141414` / `--black #0E0E0E` (structure) /
`--accent #7A2A34` (sparing). Black is confined to the home hero, the poem
page head, and the footer; interiors are paper-white editorial layouts.
CSS lives in `hugo/assets/css/style.css` and is inlined into the built HTML.

## Sandbox gotchas

- Hugo cannot install to `/usr/local/bin` (permissions); use `$HOME/bin`.
- Do not run `set -e`/`set -euo pipefail`; the runtime does not support them reliably.
- Screenshots: `tools/preview/shoot.py` (Playwright + Chromium headless shell);
  DOM/style analysis: `tools/preview/analyze_visual.py`. Images cannot be viewed
  directly — use PIL color/luminance analysis or ASCII grids to inspect them.
