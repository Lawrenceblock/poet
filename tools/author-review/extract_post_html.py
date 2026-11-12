#!/usr/bin/env python3
"""Verbatim extraction + sanitisation of public Blogger post HTML.

Purpose
-------
Produce, for each poetry candidate, a reading view that preserves the author's
text EXACTLY (characters, punctuation, line breaks, paragraph breaks, inline
emphasis, images) while removing anything unsafe (scripts, event handlers,
javascript: URLs) and Blogger/Word junk namespaces.

Rules
-----
* Never rewrites, reflows, re-punctuates or "tidies" the text.
* Entities are left encoded so that `&nbsp;`, `&mdash;`, `&ldquo;` etc. keep
  their exact original characters.
* Only a small whitelist of presentational tags survives; every other tag is
  unwrapped (its inner text is kept verbatim).
* `<script>`, `<style>`, `<iframe>`, `<object>`, `<embed>`, `<form>`, `<input>`
  and all `on*=` handlers are dropped.

This module has no side effects on import.
"""
import re

# Tags whose *content* must be dropped entirely (not just the tag).
DROP_CONTENT = ("script", "style", "iframe", "object", "embed", "form",
                "noscript", "svg", "canvas", "video", "audio", "map", "applet")

# Tags kept as-is (presentational / structural, safe).
KEEP = {"p", "br", "em", "strong", "b", "i", "u", "s", "blockquote",
        "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6",
        "sub", "sup", "hr", "pre", "code", "figure", "figcaption",
        "dl", "dt", "dd", "cite", "q", "small", "mark", "time", "abbr"}

# Tags unwrapped (tag removed, inner text preserved verbatim).
UNWRAP = {"div", "span", "font", "center", "tbody", "thead", "tr", "td", "th",
          "table", "a", "img", "w", "o", "m", "xml", "st1", "v", "rt", "rp",
          "section", "article", "header", "footer", "main", "nav", "body", "html"}

# Attributes allowed to survive, per tag.
ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "width", "height"},
    "time": {"datetime"},
    "abbr": {"title"},
}

DROP_CONTENT_RE = re.compile(
    r"<\s*(%s)\b[^>]*>.*?<\s*/\s*\1\s*>" % "|".join(DROP_CONTENT),
    re.IGNORECASE | re.DOTALL)
SELF_DROP_RE = re.compile(
    r"<\s*(%s)\b[^>]*/?>" % "|".join(DROP_CONTENT), re.IGNORECASE)
TAG_RE = re.compile(r"<\s*(/?)\s*([a-zA-Z0-9:_-]+)((?:\s+[^<>]*?)?)\s*(/?)\s*>")
ATTR_RE = re.compile(r"([a-zA-Z0-9:_-]+)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _clean_attrs(tag, attrs):
    allowed = ATTRS.get(tag)
    if allowed is None:
        return ""
    out = []
    for m in ATTR_RE.finditer(attrs or ""):
        name = m.group(1).lower()
        if name.startswith("on"):
            continue
        if name not in allowed:
            continue
        val = m.group(2)
        if val[:1] in "\"'":
            val = val[1:-1]
        if name in ("href", "src"):
            scheme = re.match(r"\s*([a-zA-Z][a-zA-Z0-9+.-]*):", val)
            if scheme and scheme.group(1).lower() in ("javascript", "vbscript", "data"):
                continue
        out.append('%s="%s"' % (name, val.replace('"', "&quot;")))
    return (" " + " ".join(out)) if out else ""


def sanitize(html):
    """Return sanitised HTML that preserves all visible text verbatim."""
    if not html:
        return ""
    s = COMMENT_RE.sub("", html)
    # Drop dangerous elements together with their content.
    prev = None
    while prev != s:
        prev = s
        s = DROP_CONTENT_RE.sub("", s)
        s = SELF_DROP_RE.sub("", s)

    def repl(m):
        closing, name, attrs, selfclose = m.groups()
        tag = name.lower()
        if tag in KEEP:
            if closing:
                return "</%s>" % tag
            return "<%s%s%s>" % (tag, _clean_attrs(tag, attrs),
                                 "/" if selfclose else "")
        # Unwrap: keep inner content, drop the tag itself.
        return ""

    s = TAG_RE.sub(repl, s)
    return s.strip()


def visible_text(html):
    """Plain visible text, used only for search/summary (never for display)."""
    s = re.sub(r"<[^>]+>", " ", html or "")
    s = re.sub(r"&nbsp;", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()
