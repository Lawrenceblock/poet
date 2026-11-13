#!/usr/bin/env python3
"""Build the author-facing poetry review site (static HTML, self-contained).

Inputs (all read-only):
  * work/feed/feed-*.json                     raw public Blogger feed (gitignored)
  * docs/poetry-discovery/poetry-candidates.v2.csv   137 candidates
  * docs/poetry-discovery/blog-post-inventory.v2.csv 305 posts (URL map)

Outputs (docs/author-review/site/, committed):
  * index.html                    master catalogue
  * batch-A.html / batch-B.html / batch-CD.html
  * poem/<candidate_id>.html      one reading page per candidate
  * data/candidates.json          machine-readable index

Design notes
------------
* Verbatim text is preserved via extract_post_html.sanitize(); nothing is
  re-worded, re-punctuated or re-flowed.
* Each page clearly states it is a REVIEW copy, not the published version.
* The original Blogger URL is always shown as the authoritative source.
* No poem is marked "confirmed"; every row stays "待作者审阅".

The script only writes into docs/author-review/site/. It never edits the
source CSVs and never touches the Hugo site.
"""
import csv
import glob
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_post_html import sanitize, visible_text  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAND_CSV = os.path.join(ROOT, "docs", "poetry-discovery", "poetry-candidates.v2.csv")
INV_CSV = os.path.join(ROOT, "docs", "poetry-discovery", "blog-post-inventory.v2.csv")
FEED_GLOB = os.path.join(ROOT, "work", "feed", "feed-*.json")
OUT = os.path.join(ROOT, "docs", "author-review", "site")

CATEGORY_LABEL = {
    "A": "A · 脚本检测到明确署名（文/安然 等）",
    "B": "B · 有诗歌特征但无明确署名",
    "C": "C · 疑似译作（安然为译者）",
    "D": "D · 评论/创作谈/消息类",
    "E": "E · 引用/转载他人作品",
}

STATUS_OPTIONS = [
    "待作者审阅",
    "确认收入诗歌站",
    "不收入诗歌站",
    "需要修改分类",
    "需要确认版本",
    "暂缓决定",
]


def load_entries():
    entries = {}
    for f in sorted(glob.glob(FEED_GLOB)):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        for e in data["feed"].get("entry", []):
            pid = e["id"]["$t"].split(".post-")[-1]
            entries[pid] = e
    return entries


def post_url(entry):
    for l in entry.get("link", []):
        href = l.get("href", "")
        if "www.ismaelan.com" in href and "/feeds/" not in href:
            return href
    return ""


def esc(s):
    return html.escape(s or "", quote=True)


PAGE_CSS = """
/* 作者审阅材料 · 视觉与公开阅读页统一：纸白底、墨黑正文、暗红点缀（Phase 3 编辑设计）。
   仅调整外观（配色与字族）；不改动任何审阅数据、字段、HTML 结构或 API 行为。 */
:root{--black:#0E0E0E;--ink:#141414;--ink-2:#4A4A4A;--muted:#6B6B6B;--line:#DAD8D4;--line-strong:#C4C1BC;
 --bg:#FAF9F7;--bg-soft:#F2F1EE;--accent:#7A2A34;--accent-soft:#F3E9EA;
 --on-black:#F2F1EE;--on-black-muted:#A8A6A2;--on-black-accent:#C98A92;--on-black-rule:#2A2A2A}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:"Songti SC","Noto Serif CJK SC","Source Han Serif SC",Georgia,serif;line-height:1.9;font-size:17px}
/* 页眉与公开站一致：纸白 + 细线（刊物页眉），不再使用黑色标题条。 */
.rv-head{background:var(--bg);color:var(--ink);border-bottom:1px solid var(--ink)}
.rv-head-inner{max-width:760px;margin:0 auto;padding:16px 20px;display:flex;flex-wrap:wrap;
 align-items:baseline;justify-content:space-between;gap:6px 16px}
.rv-head .brand{color:var(--ink);letter-spacing:.18em;font-size:1.05rem}
.rv-head .brand-en{display:block;color:var(--muted);font-size:.58rem;
 letter-spacing:.28em;text-transform:uppercase;margin-top:3px}
.rv-head nav{font-size:.85rem}
.rv-head nav a{color:var(--ink-2);margin-left:14px}
.rv-head nav a:hover{color:var(--accent)}
.rv-head nav a.cur{color:var(--accent)}
.wrap{max-width:760px;margin:0 auto;padding:28px 20px 60px}
.rv-foot{background:var(--black);color:var(--on-black-muted);font-size:.8rem;line-height:1.9}
.rv-foot-inner{max-width:760px;margin:0 auto;padding:22px 20px}
.rv-foot a{color:#c9c7c4}
.rv-foot a:hover{color:var(--on-black-accent)}
a{color:var(--accent)}
h1{font-size:1.5rem;font-weight:600;margin:.2em 0 .6em;letter-spacing:.04em}
h2{font-size:1.08rem;margin:1.6em 0 .4em;letter-spacing:.04em}
.note{background:var(--bg-soft);border:1px solid var(--line);border-left:3px solid var(--accent);
 padding:12px 14px;color:var(--muted);font-size:.9rem;margin:16px 0}
.meta{color:var(--muted);font-size:.85rem;line-height:1.75}
.meta b{color:var(--ink);font-weight:600}
.tags span{display:inline-block;background:var(--bg-soft);border:1px solid var(--line);
 padding:1px 10px;margin:2px 4px 2px 0;font-size:.78rem;color:var(--muted)}
.card{background:#fff;border:1px solid var(--line);padding:16px 18px;margin:14px 0}
.card h3{margin:0 0 .3em;font-size:1.02rem;font-weight:600}
.card h3 a{color:var(--ink)}
.card h3 a:hover{color:var(--accent)}
.poem{background:#fff;border:1px solid var(--line);border-top:2px solid var(--accent);
 padding:22px 24px;margin:18px 0}
.poem p{margin:0 0 1.05em}
.poem img{max-width:100%;height:auto}
.verse{white-space:pre-wrap}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--bg-soft);font-weight:600}
.status{display:inline-block;border:1px solid var(--line-strong);
 padding:2px 10px;font-size:.8rem;color:var(--muted);background:var(--bg-soft)}
.status.s-keep{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}
.status.s-hold{background:var(--bg-soft);border-color:var(--line-strong);color:#8a6d2f}
.status.s-exclude{background:#f4f1f1;border-color:#d9c9c9;color:#8a4a4a}
.status.s-pending{background:var(--bg-soft);border-color:var(--line);color:var(--muted)}
.foot{margin-top:40px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:14px}
.batchnav a{display:inline-block;margin-right:14px}
.banner{background:var(--bg-soft);border:1px solid var(--line);border-left:3px solid var(--accent);
 padding:10px 14px;font-size:.85rem;color:var(--muted);margin-bottom:18px}
/* ---- review form ---- */
.rv{border:1px solid var(--line);border-top:2px solid var(--accent);background:#fff;padding:16px 16px 8px;margin:18px 0}
.rv h2{margin-top:.2em}
.rv label{display:block;font-weight:600;margin:14px 0 6px;font-size:.95rem}
.rv select,.rv textarea{width:100%;font:inherit;font-size:16px;padding:12px 12px;
 border:1px solid var(--line-strong);background:#fff;color:var(--ink)}
.rv select{min-height:48px}
.rv textarea{min-height:120px;line-height:1.8;resize:vertical}
.rv .hint{color:var(--muted);font-size:.8rem;margin:4px 0 0}
.rvbar{position:sticky;bottom:0;background:#fff;
 padding:12px 0 4px;margin-top:8px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;
 border-top:1px solid var(--line)}
.btn{font:inherit;font-size:16px;min-height:48px;padding:10px 22px;
 border:1px solid var(--accent);background:var(--accent);color:#fff;font-weight:600;cursor:pointer}
.btn.secondary{background:#fff;color:var(--accent)}
.btn:disabled{opacity:.5;cursor:default}
.save-state{font-size:.9rem;padding:6px 12px;border:1px solid var(--line);background:var(--bg-soft);color:var(--muted)}
.save-state.ok{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}
.save-state.err{background:#f4f1f1;border-color:#d9c9c9;color:#8a4a4a}
.save-state.busy{background:var(--bg-soft);border-color:var(--line-strong);color:var(--muted)}
.last-saved{color:var(--muted);font-size:.82rem;width:100%}
.pill{display:inline-block;padding:2px 10px;font-size:.78rem;border:1px solid var(--line)}
.pill.done{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}
.pill.todo{background:var(--bg-soft);border-color:var(--line);color:var(--muted)}
.bar{height:12px;background:var(--bg-soft);overflow:hidden;border:1px solid var(--line)}
.bar>i{display:block;height:100%;background:var(--accent)}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 6px}
.filters a{display:inline-block;min-height:44px;line-height:44px;padding:0 16px;
 border:1px solid var(--line);background:#fff;text-decoration:none;color:var(--ink);font-size:.9rem}
.filters a.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.exportbar{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.exportbar a{display:inline-flex;align-items:center;min-height:48px;padding:0 18px;
 border:1px solid var(--accent);text-decoration:none;font-weight:600}
.rowdone{background:var(--bg-soft)}
.hide{display:none}
"""


def page(title, body, extra_head="", depth=0):
    """depth = directory levels below the review root (poem/ and oldsite/ = 1)."""
    up = "../" * depth
    header = (
        "<header class=\"rv-head\"><div class=\"rv-head-inner\">"
        f"<a class=\"brand\" href=\"{up}\">安然诗歌档案"
        "<span class=\"brand-en\">Author Review</span></a>"
        f"<nav><a href=\"{up}\">总目录</a>"
        f"<a href=\"{up}index.html\">批次索引</a></nav>"
        "</div></header>")
    footer = (
        "<footer class=\"rv-foot\"><div class=\"rv-foot-inner\">"
        "安然诗歌档案 · 作者审阅材料 · 本页为审阅副本，非正式发表版本。"
        "原文版权归作者所有。</div></footer>")
    return ("<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            "<meta name=\"robots\" content=\"noindex,nofollow\">\n"
            f"<title>{esc(title)}</title>\n"
            f"<style>{PAGE_CSS}</style>\n{extra_head}"
            "</head>\n<body>" + header + "<div class=\"wrap\">\n" + body +
            "\n<div class=\"foot\">安然诗歌档案 · 作者审阅材料 · "
            "本页为审阅副本，非正式发表版本。原文版权归作者所有。</div>\n"
            "</div>" + footer + "</body></html>\n")


# Options shown in the author-review form (value -> Chinese label).
STATUS_FORM = [("pending", "待审阅"), ("keep", "保留"),
               ("hold", "暂缓"), ("exclude", "排除")]
NATURE_FORM = [("unset", "（未填写）"), ("single_poem", "一首诗"),
               ("multi_poem", "多首诗"), ("non_poem", "非诗（评论/消息/摄影等）"),
               ("unsure", "尚不确定")]


def review_form(cid):
    """A real, submittable review form. Behaviour lives in REVIEW_JS."""
    sopts = "".join(f"<option value=\"{v}\">{esc(l)}</option>" for v, l in STATUS_FORM)
    nopts = "".join(f"<option value=\"{v}\">{esc(l)}</option>" for v, l in NATURE_FORM)
    return (
        "<div class=\"rv\" id=\"review\" data-candidate=\"" + esc(cid) + "\">"
        "<h2>作者审阅</h2>"
        "<p class=\"hint\">只需填写你要填的部分；填写后请点“保存审阅”。"
        "未保存前刷新页面不会丢失草稿，但只有“已保存”才算正式记录。</p>"
        "<label for=\"f-status\">① 审阅结论</label>"
        f"<select id=\"f-status\" name=\"status\">{sopts}</select>"
        "<label for=\"f-nature\">② 作品性质</label>"
        f"<select id=\"f-nature\" name=\"nature\">{nopts}</select>"
        "<label for=\"f-comment\">③ 作者意见（版本问题、是否需修改、是否需与旧站比较等）</label>"
        "<textarea id=\"f-comment\" name=\"comment\" "
        "placeholder=\"例如：与旧站版本不同，以本版为准；需要再核对第二段换行……\"></textarea>"
        "<p class=\"hint\">可只填部分字段。意见最多 20000 字。</p>"
        "<div class=\"rvbar\">"
        "<button type=\"button\" class=\"btn\" id=\"f-save\">保存审阅</button>"
        "<span class=\"save-state\" id=\"f-state\" aria-live=\"polite\">尚未保存</span>"
        "<span class=\"last-saved\" id=\"f-last\"></span>"
        "</div></div>")


REVIEW_JS = """
<script>
(function(){
  var root=document.getElementById('review');
  if(!root) return;
  var cid=root.getAttribute('data-candidate');
  var elStatus=document.getElementById('f-status');
  var elNature=document.getElementById('f-nature');
  var elComment=document.getElementById('f-comment');
  var elSave=document.getElementById('f-save');
  var elState=document.getElementById('f-state');
  var elLast=document.getElementById('f-last');
  var api='/review/api/review/'+encodeURIComponent(cid);
  var apiSave='/review/api/review';
  var LS='reviewDraft:'+cid;
  // ?test=1 routes writes to the isolated test journal so acceptance tests
  // never touch the author's real review records.
  var TEST=/[?&]test=1(&|$)/.test(location.search);
  if(TEST){ api+='?test=1'; LS='reviewDraft-test:'+cid; }

  function setState(kind,text){
    elState.className='save-state'+(kind?' '+kind:'');
    elState.textContent=text;
  }
  function fmt(ts){ return ts?('上次保存：'+ts.replace('T',' ').slice(0,16)):''; }

  // restore unsaved draft (never treated as a saved record)
  try{
    var d=JSON.parse(localStorage.getItem(LS)||'null');
    if(d){ if(d.status)elStatus.value=d.status; if(d.nature)elNature.value=d.nature;
           if(d.comment)elComment.value=d.comment; setState('','有未保存的草稿'); }
  }catch(e){}

  function markDirty(){
    try{localStorage.setItem(LS,JSON.stringify({status:elStatus.value,
      nature:elNature.value,comment:elComment.value}));}catch(e){}
    if(!elState.classList.contains('ok')) setState('','有未保存的修改');
  }
  [elStatus,elNature,elComment].forEach(function(el){
    el.addEventListener('input',markDirty); el.addEventListener('change',markDirty);});

  // load the saved record from the server
  fetch(api,{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){
    if(j&&j.record){
      if(!localStorage.getItem(LS)){
        elStatus.value=j.record.status||'pending';
        elNature.value=j.record.nature||'unset';
        elComment.value=j.record.comment||'';
      }
      elLast.textContent=fmt(j.record.updated_at)+(j.record.rev?('（第 '+j.record.rev+' 版）'):'');
      setState('ok','已保存');
    }else{
      setState('','尚未保存');
    }
  }).catch(function(){ setState('err','无法读取历史记录（服务器离线）'); });

  elSave.addEventListener('click',function(){
    elSave.disabled=true; setState('busy','正在保存…');
    fetch(apiSave,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({candidate_id:cid,status:elStatus.value,
        nature:elNature.value,comment:elComment.value,test:TEST})})
    .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
    .then(function(res){
      elSave.disabled=false;
      if(res.ok&&res.j&&res.j.ok){
        try{localStorage.removeItem(LS);}catch(e){}
        var rec=res.j.record||{};
        elLast.textContent=fmt(rec.updated_at)+(rec.rev?('（第 '+rec.rev+' 版）'):'');
        setState('ok','保存成功');
      }else{
        var msg=(res.j&&res.j.error)?res.j.error:'保存失败';
        setState('err','保存失败：'+msg);
      }
    }).catch(function(){
      elSave.disabled=false;
      setState('err','保存失败：网络错误（未保存）');
    });
  });
})();
</script>
"""


INDEX_JS = """
<script>
(function(){
  var LB={pending:'待审阅',keep:'保留',hold:'暂缓',exclude:'排除'};
  var CLS={pending:'todo',keep:'done',hold:'done',exclude:'done'};
  var state={records:{},progress:null,filter:'all'};

  function render(){
    var p=state.progress||{total:0,reviewed:0,unreviewed:0,by_status:{}};
    var pct=p.total?Math.round(p.reviewed*100/p.total):0;
    document.getElementById('pbar').style.width=pct+'%';
    var bs=p.by_status||{};
    document.getElementById('ptext').textContent=
      '共 '+p.total+' 篇　已审阅 '+p.reviewed+' 篇（'+pct+'%）　未审阅 '+p.unreviewed+
      ' 篇　｜　保留 '+(bs.keep||0)+'　暂缓 '+(bs.hold||0)+'　排除 '+(bs.exclude||0)+
      '　待审阅 '+(bs.pending||0);
    var rows=document.querySelectorAll('#list tr[data-cid]');
    rows.forEach(function(tr){
      var cid=tr.getAttribute('data-cid');
      var rec=state.records[cid];
      var st=(rec&&rec.status)||'pending';
      var pill=document.getElementById('st-'+cid);
      if(pill){ pill.textContent=LB[st]||st; pill.className='pill '+(CLS[st]||'todo'); }
      tr.classList.toggle('rowdone', st!=='pending');
      var show=(state.filter==='all')||(st===state.filter);
      tr.classList.toggle('hide', !show);
    });
  }

  document.querySelectorAll('#filters a').forEach(function(a){
    a.addEventListener('click',function(e){
      e.preventDefault();
      state.filter=a.getAttribute('data-f');
      document.querySelectorAll('#filters a').forEach(function(x){x.classList.remove('active');});
      a.classList.add('active'); render();
    });
  });

  function load(){
    fetch('/review/api/reviews',{cache:'no-store'}).then(function(r){return r.json();})
    .then(function(j){
      if(j&&j.ok){ state.records=j.records||{}; state.progress=j.progress||null; render(); }
      else { document.getElementById('ptext').textContent='无法读取审阅进度（服务器返回错误）'; }
    }).catch(function(){
      document.getElementById('ptext').textContent='无法读取审阅进度（服务器离线）——页面仍可阅读。';
    });
  }
  load();
})();
</script>
"""


def build():
    entries = load_entries()
    with open(CAND_CSV, encoding="utf-8") as fh:
        cand = list(csv.DictReader(fh))
    with open(INV_CSV, encoding="utf-8") as fh:
        inv = {r["post_id"]: r for r in csv.DictReader(fh)}

    os.makedirs(os.path.join(OUT, "poem"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

    by_cat = {"A": [], "B": [], "CD": []}
    index_rows = []

    # Assign every candidate to a batch chunk up front so poem pages can link
    # back to the exact chunk that contains them.
    cat_of = {"A": "A", "B": "B", "C": "CD", "D": "CD", "E": "CD"}
    ordered = {k: [c for c in cand if cat_of.get(c["category"], "CD") == k]
               for k in ("A", "B", "CD")}
    batch_of = {}
    batch_defs = []  # (key, label, n, chunk, filename)
    for key, label in (("A", "A 类候选"), ("B", "B 类候选"), ("CD", "C / D 类候选")):
        items = ordered[key]
        chunks = [items[i:i + 15] for i in range(0, len(items), 15)]
        multi = len(chunks) > 1
        for n, chunk in enumerate(chunks, 1):
            fn = f"batch-{key}-{n}.html" if multi else f"batch-{key}.html"
            batch_defs.append((key, label, n, chunk, fn))
            for c in chunk:
                batch_of[c["candidate_id"]] = fn

    for c in cand:
        cid = c["candidate_id"]
        pid = c["source_post_id"]
        e = entries.get(pid)
        src_url = c["source_url"]
        title = (c["candidate_title"] or c["source_post_title"] or "(无标题)").strip()
        raw = e["content"]["$t"] if e else ""
        safe = sanitize(raw)
        cat = c["category"]

        meta = {
            "candidate_id": cid,
            "title": title,
            "source_post_title": c["source_post_title"],
            "published": c["published"][:10],
            "source_url": src_url,
            "category": cat,
            "lang": c["lang"],
            "title_source": c["title_source"],
            "has_own_title": c["has_own_title"],
            "boundary_status": c["boundary_status"],
            "work_count_estimate": c["work_count_estimate"],
            "multi_poem_flag": c["multi_poem_flag"],
            "authorship_evidence": c["authorship_evidence"],
            "labels": c["labels"],
            "confidence": c["confidence"],
            "content_chars": len(visible_text(safe)),
        }
        index_rows.append(meta)

        # ---- per-poem reading page ----
        reasons = []
        reasons.append(f"脚本分类：{CATEGORY_LABEL.get(cat, cat)}")
        if c["authorship_evidence"]:
            reasons.append(f"署名线索：{c['authorship_evidence']}")
        if c["labels"]:
            reasons.append(f"原文标签：{c['labels']}")
        if c["title_source"]:
            reasons.append(f"标题来源：{c['title_source']}")
        if c["multi_poem_flag"] == "yes":
            reasons.append("标题含“组诗/外一首/二首”等线索，可能含多首，需作者确认边界。")
        if c["lang"] == "zh+en":
            reasons.append("检测到中英双语，审阅时请核对两种语言是否为同一作品。")
        if cat in ("C", "D"):
            reasons.append("该类不是明确诗歌，需作者判断是否收入诗歌站。")

        questions = []
        questions.append("这篇文章是“一首诗 / 多首诗 / 非诗（评论、消息、摄影等）”？")
        if c["multi_poem_flag"] == "yes":
            questions.append("若含多首，请分别给出各首标题（用于生成独立页面与链接）。")
        if c["lang"] == "zh+en":
            questions.append("中英文是否为同一作品的两种版本？以哪一版为准？")
        if cat in ("B", "C", "D"):
            questions.append("是否确认作者署名/归属？")
        if c["has_own_title"] == "no":
            questions.append("作品是否有独立标题？若无，页面标题用文章名还是“无题”？")

        body = []
        body.append(f"<p class=\"batchnav\"><a href=\"../index.html\">← 审阅总目录</a> "
                    f"<a href=\"../{esc(batch_of[cid])}\">本批目录</a></p>")
        body.append(f"<h1>{esc(title)}</h1>")
        body.append("<div class=\"note\"><b>这是审阅副本，不是正式发表版本。</b>"
                    "页面完整保留原文（含标点、诗行、段落、图片），仅移除脚本等不安全代码；"
                    "未经作者确认不会用于正式站点。</div>")
        body.append("<p class=\"meta\">"
                    f"候选编号 <b>{esc(cid)}</b>　"
                    f"原始发表日期 <b>{esc(meta['published'])}</b>　"
                    f"语言 <b>{esc(meta['lang'])}</b>　"
                    f"脚本分类 <b>{esc(cat)}</b><br>"
                    f"原始来源：<a href=\"{esc(src_url)}\" rel=\"noopener\">{esc(src_url)}</a></p>")
        if c["labels"]:
            body.append("<p class=\"tags\">" + "".join(
                f"<span>{esc(t)}</span>" for t in re.split(r"[|,]", c["labels"]) if t.strip()) + "</p>")
        body.append("<h2>为什么列出这篇</h2><ul class=\"meta\">" +
                    "".join(f"<li>{esc(r)}</li>" for r in reasons) + "</ul>")
        body.append("<h2>需要作者确认</h2><ul class=\"meta\">" +
                    "".join(f"<li>{esc(q)}</li>" for q in questions) + "</ul>")
        body.append(review_form(cid))
        body.append("<h2>原文（逐字保留）</h2>")
        if meta["content_chars"] < 20:
            body.append("<div class=\"note\">该文正文为空或极短（可能为图片/视频为主的文章）。"
                        "请点击上方原始来源链接查看原貌。</div>")
        body.append(f"<div class=\"poem\">{safe}</div>")
        body.append(f"<p class=\"meta\">如原页面与本页有任何差异，请以 "
                    f"<a href=\"{esc(src_url)}\" rel=\"noopener\">原始来源</a> 为准，并告知差异位置。</p>")
        body.append(REVIEW_JS)  # at end of body so the DOM already exists

        with open(os.path.join(OUT, "poem", f"{cid}.html"), "w", encoding="utf-8") as fh:
            fh.write(page(f"{cid} · {title}", "\n".join(body), depth=1))

        key = "A" if cat == "A" else "B" if cat == "B" else "CD"
        by_cat[key].append(meta)

    # ---- batch pages (from the pre-computed chunks) ----
    batch_files = []
    for key, label, n, chunk, fn in batch_defs:
        body = [f"<p class=\"batchnav\"><a href=\"index.html\">← 审阅总目录</a></p>",
                f"<h1>{label} · 第 {n} 批（{len(chunk)} 篇）</h1>",
                "<div class=\"note\">点击每篇的“阅读全文”即可直接读诗。"
                "所有正文均逐字保留原文，并附原始来源链接。本批共 "
                f"{len(chunk)} 篇，全部状态为“待作者审阅”。</div>"]
        for c in chunk:
            m = next(x for x in index_rows if x["candidate_id"] == c["candidate_id"])
            body.append(
                "<div class=\"card\">"
                f"<h3>{esc(m['title'])}</h3>"
                f"<p class=\"meta\">{esc(m['published'])}　分类 {esc(m['category'])}　"
                f"{esc(m['lang'])}　{esc(m['candidate_id'])}</p>"
                f"<p><a href=\"poem/{esc(m['candidate_id'])}.html\">阅读全文 →</a>　"
                f"<a href=\"{esc(m['source_url'])}\" rel=\"noopener\">原始来源</a></p>"
                "</div>")
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as fh:
            fh.write(page(f"{label} · 第 {n} 批", "\n".join(body)))
        batch_files.append((key, label, n, len(chunk), fn))

    # ---- master index ----
    body = ["<h1>安然诗歌档案 · 作者审阅总目录</h1>",
            "<div class=\"banner\">这些页面是为了让作者<b>直接读到作品全文</b>而建立。"
            "每篇都保留原文标点、诗行与段落，并附原始来源链接。"
            "点击“阅读/审阅”即可阅读全文并填写审阅结论。</div>",
            "<div class=\"note\"><b>重要：</b>“候选”是脚本按署名/标签线索筛出的<b>文章</b>，"
            "<b>不等于已经确认的诗歌</b>。例如某些文章实为摄影或评论。"
            "请作者逐篇判断：是不是诗、是一首还是多首、是否收入本站。</div>",
            "<h2>审阅进度</h2>",
            "<div id=\"progress\"><div class=\"bar\"><i id=\"pbar\" style=\"width:0%\"></i></div>"
            "<p class=\"meta\" id=\"ptext\">正在加载进度…</p></div>",
            "<div class=\"exportbar\">"
            "<a href=\"/review/api/export.csv\">导出 CSV</a>"
            "<a href=\"/review/api/export.json\">导出 JSON</a>"
            "</div>",
            "<div class=\"filters\" id=\"filters\">"
            "<a href=\"#\" data-f=\"all\" class=\"active\">全部</a>"
            "<a href=\"#\" data-f=\"pending\">待审阅</a>"
            "<a href=\"#\" data-f=\"keep\">保留</a>"
            "<a href=\"#\" data-f=\"hold\">暂缓</a>"
            "<a href=\"#\" data-f=\"exclude\">排除</a>"
            "</div>",
            "<h2>旧站现有页面</h2>",
            "<div class=\"card\"><h3><a href=\"oldsite/index.html\">旧站现有页面（审阅）</a></h3>"
            "<p class=\"meta\">那拉提（未赴）· 青春的物语 · 诗人小传 · 题记 —— "
            "这些页面现在已在 poet.ismaelan.com 上线，迁移前请作者确认。</p></div>",
            "<h2>按批次阅读</h2>"]
    for key, label, n, cnt, fn in batch_files:
        body.append(f"<div class=\"card\"><h3><a href=\"{fn}\">{label} · 第 {n} 批</a></h3>"
                    f"<p class=\"meta\">{cnt} 篇</p></div>")

    body.append("<h2>完整清单</h2>")
    body.append("<table id=\"list\"><tr><th>#</th><th>编号</th><th>标题</th><th>日期</th>"
                "<th>分类</th><th>语言</th><th>审阅</th><th>阅读/审阅</th><th>原始来源</th></tr>")
    for i, m in enumerate(index_rows, 1):
        cid = m["candidate_id"]
        body.append(f"<tr data-cid=\"{esc(cid)}\">"
                    f"<td>{i}</td><td>{esc(cid)}</td>"
                    f"<td>{esc(m['title'])}</td><td>{esc(m['published'])}</td>"
                    f"<td>{esc(m['category'])}</td><td>{esc(m['lang'])}</td>"
                    f"<td class=\"cell-status\"><span class=\"pill todo\" id=\"st-{esc(cid)}\">待审阅</span></td>"
                    f"<td><a href=\"poem/{esc(cid)}.html\">阅读/审阅</a></td>"
                    f"<td><a href=\"{esc(m['source_url'])}\" rel=\"noopener\">来源</a></td></tr>")
    body.append("</table>")
    body.append(INDEX_JS)  # at end of body so the DOM already exists
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page("作者审阅总目录", "\n".join(body)))

    with open(os.path.join(OUT, "data", "candidates.json"), "w", encoding="utf-8") as fh:
        json.dump(index_rows, fh, ensure_ascii=False, indent=1)

    print(f"candidates: {len(cand)}")
    print(f"batch pages: {len(batch_files)}")
    for k, l, n, c, fn in batch_files:
        print(f"  {fn}: {c} 篇")
    print("index: docs/author-review/site/index.html")


if __name__ == "__main__":
    build()
