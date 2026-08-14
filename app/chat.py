"""#voice-eng - the channel itself.

The answer page argues about trust. This page is the raw material: fourteen
months of a real-looking engineering channel, threads and all. Being able to
scroll it matters for the demo - it makes "the answer is four replies down,
written a year ago" a thing the room can see rather than a claim.

Posting here writes to the same Qdrant collection the verdict is computed from,
so you can post a retraction, tab back, ask again, and watch the verdict age.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

EXPORT = os.path.join(os.path.dirname(__file__), "..", "corpus2", "channel")


def messages() -> list[dict]:
    out = []
    if os.path.isdir(EXPORT):
        for fn in sorted(os.listdir(EXPORT)):
            out.extend(json.load(open(os.path.join(EXPORT, fn))))
    return sorted(out, key=lambda m: (m["date"], m.get("thread") or ""))


PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>#voice-eng</title><meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
:root{--bg:#f6f8fa;--panel:#ffffff;--line:#d8dee4;--dim:#57606a;--fg:#1f2328;
 --grn:#1a7f37;--amb:#9a6700;--red:#cf222e;--blu:#0969da}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);
 font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.app{height:100%;display:grid;grid-template-columns:232px 1fr}
.side{background:#f0f2f5;border-right:1px solid var(--line);padding:20px 0;
 display:flex;flex-direction:column;overflow:hidden}
.side .ws{padding:0 18px 16px;border-bottom:1px solid var(--line);margin-bottom:16px}
.side .ws b{font-size:16px;display:block}
.side .ws span{color:var(--dim);font-size:12px}
.side h4{color:var(--dim);font-size:11px;letter-spacing:.12em;text-transform:uppercase;
 margin:0 0 8px;padding:0 18px}
.side a{display:flex;align-items:center;gap:9px;padding:7px 18px;color:var(--dim);
 text-decoration:none;font-size:14.5px}
.side a:hover{background:#e4e8ed;color:var(--fg)}
.side a.on{background:#0969da;color:#fff;font-weight:600}
.side a .c{opacity:.55;font-size:13px;margin-left:auto}
.main{display:flex;flex-direction:column;min-width:0}
@media(max-width:760px){.app{grid-template-columns:1fr}.side{display:none}}
.hd{padding:20px 26px 16px;border-bottom:1px solid var(--line);display:flex;
 align-items:baseline;gap:14px;flex-wrap:wrap}
.hd h1{margin:0;font-size:25px;letter-spacing:-.02em}
.hd .n{color:var(--dim);font-size:14px}
.hd a{margin-left:auto;color:var(--blu);text-decoration:none;font-size:14px}
.feed{flex:1;overflow-y:auto;padding:22px 26px 10px}
.day{display:flex;align-items:center;gap:14px;color:var(--dim);font-size:12px;
 margin:22px 0 14px;letter-spacing:.04em}
.day:before,.day:after{content:"";flex:1;height:1px;background:var(--line)}
.m{display:flex;gap:13px;padding:9px 12px;border-radius:10px;margin-bottom:3px}
.m:hover{background:#f2f4f7}
.m.new{background:#e8f6ec;animation:land .5s ease}
@keyframes land{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.av{width:38px;height:38px;border-radius:9px;display:grid;place-items:center;
 font-weight:700;font-size:14px;color:#fff;flex:0 0 38px}
.b .who{font-weight:600;font-size:15px}
.b .who span{color:var(--dim);font-weight:400;font-size:12px;margin-left:9px}
.b .tx{white-space:pre-wrap;font-size:15px;margin-top:2px}
.thread{color:var(--dim);font-size:12px;margin-top:5px}
.tag{display:inline-block;font-size:11.5px;padding:2px 9px;border-radius:20px;
 margin-top:7px;border:1px solid}
.tag.u{color:#7a4f01;border-color:#d4a72c;background:#fff8e6}
.tag.s{color:#8b1a24;border-color:#cf222e;background:#ffebe9}
.comp{border-top:1px solid var(--line);padding:16px 26px 22px;background:var(--bg)}
.comp .box{background:var(--panel);border:1px solid var(--line);border-radius:12px;
 padding:12px 14px}
.comp textarea{width:100%;background:transparent;color:var(--fg);border:0;
 font:15px/1.6 inherit;resize:vertical;min-height:66px;outline:none}
.comp .bar{display:flex;align-items:center;gap:11px;margin-top:9px}
.comp .as{color:var(--dim);font-size:13px;margin-right:auto;display:flex;
 align-items:center;gap:9px}
.comp .as .av{width:26px;height:26px;font-size:11px;border-radius:7px}
button{font:inherit;cursor:pointer;border-radius:9px;padding:9px 18px;
 border:1px solid var(--line);background:var(--panel);color:var(--fg)}
.send{background:#1f883d;border-color:#1a7f37;color:#fff;font-weight:600}
.send:hover{background:#1a7f37}
.ok{color:var(--grn);font-size:13.5px}
.working{color:var(--dim);font-size:13.5px;font-style:italic}
.working{color:var(--dim);font-size:13.5px;font-style:italic}
</style></head><body><div class=app>
<div class=side>
 <div class=ws><b>Northwind CX</b><span>Sprinklr delivery team</span></div>
 <h4>Sources</h4>
 <a href="/chat" class=on># voice-eng<span class=c>32</span></a>
 <a href="#" onclick="return false">&#128196; Sprinklr Docs<span class=c>8</span></a>
 <h4 style="margin-top:20px">Members</h4>
 <a href="#" onclick="return false">Omid Mohajerani</a>
 <a href="#" onclick="return false">Jonas Weber</a>
 <a href="#" onclick="return false">Marek Nowak</a>
 <a href="#" onclick="return false">Priya Raman</a>
 <a href="#" onclick="return false">Sam Beck</a>
</div>
<div class=main>
<div class=hd><h1>#voice-eng</h1>
 <span class=n>__N__ messages &middot; 5 members &middot; since June 2025</span>
 <a href="/">&larr; back to Shelf Life</a></div>
<div class=feed id=feed>__FEED__</div>
<div class=comp><div class=box>
 <textarea id=msg>Update on the SFTP connector - today's platform release ships a modern SSH client, so it negotiates rsa-sha2-256 properly now. Don't go re-enabling ssh-rsa on any more servers; the workaround above is obsolete.</textarea>
 <div class=bar>
  <span class=as><span class=av style="background:#0969da">OM</span>
   posting as <b style="color:var(--fg)">Omid Mohajerani</b></span>
  <span class=ok id=ok></span>
  <button onclick=undo()>Undo</button>
  <button class=send onclick=send()>Send</button>
 </div>
</div></div>
</div></div><script>
async function send(){
 const ok=document.getElementById('ok');
 const t=document.getElementById('msg').value;
 const t0=Date.now(); let n=0;
 const steps=['posting to #voice-eng…',
   'cognee is re-reading the channel…',
   'rebuilding the graph around this thread…',
   'almost — it re-reads the whole thread, not just the message…'];
 ok.className='working'; ok.textContent=steps[0];
 const tick=setInterval(()=>{n++;ok.textContent=steps[Math.min(n,steps.length-1)]+
   '  ('+((Date.now()-t0)/1000).toFixed(1)+'s)';},2500);

 // Show the message land immediately - the wait is cognee re-reading, not the post.
 const d=document.createElement('div'); d.className='m new';
 d.innerHTML='<span class=av style="background:#0969da">OM</span><div class=b>'+
  '<div class=who>Omid Mohajerani <span>Senior Voice Engineer · just now</span></div>'+
  '<div class=tx></div><span class="tag s">⚠ overturns an earlier answer</span></div>';
 d.querySelector('.tx').textContent=t;
 document.getElementById('feed').appendChild(d);
 d.scrollIntoView({behavior:'smooth',block:'center'});

 const r=await fetch('/inject',{method:'POST',
   headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
 const j=await r.json();
 clearInterval(tick); ok.className='ok';
 ok.textContent='✓ Qdrant '+j.qdrant_ms+'ms · cognee re-read '+
   (j.cognee_ms/1000).toFixed(1)+'s — now ask again';
}

async function undo(){
 const ok=document.getElementById('ok');
 ok.className='working';
 ok.textContent='removing — a graph has no undo, so it rebuilds…';
 await fetch('/reset',{method:'POST'});
 document.querySelectorAll('.m.new').forEach(e=>e.remove());
 ok.className='ok'; ok.textContent='↩ back to the original channel';
}
const f=document.getElementById('feed');f.scrollTop=f.scrollHeight;
</script></body></html>"""


PALETTE = ["#0969da", "#1a7f37", "#9a6700", "#bf3989", "#8250df"]


def _pretty(d: str) -> str:
    dt = datetime.strptime(d, "%Y-%m-%d")
    if d == "2026-08-14":
        return "Today"
    return dt.strftime("%A, %-d %B %Y")


def render() -> str:
    msgs = messages()
    colors, feed, last_date = {}, [], None
    clock = 0

    for m in msgs:
        who = m["author"]
        colors.setdefault(who, PALETTE[len(colors) % len(PALETTE)])
        if m["date"] != last_date:
            feed.append(f'<div class=day>{_pretty(m["date"])}</div>')
            last_date, clock = m["date"], 0
        # Deterministic wall-clock times: the corpus only carries dates, but a
        # channel without timestamps does not read as a channel.
        clock += 1
        hh, mm = 9 + (clock * 37) // 60, (clock * 37) % 60
        stamp = f"{min(hh, 18):02d}:{mm:02d}"

        initials = "".join(w[0] for w in who.split()[:2]).upper()
        tags = ""
        if m.get("unproven"):
            tags += '<span class="tag u">&#9888; the author flagged this as unproven</span>'
        if m.get("supersedes"):
            tags += '<span class="tag s">&#9888; overturns an earlier answer</span>'
        thread = (f'<div class=thread>in thread &ldquo;{m["thread"]}&rdquo;</div>'
                  if m.get("thread") else "")
        text = (m["text"].replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))
        feed.append(
            f'<div class=m><span class=av style="background:{colors[who]}">{initials}</span>'
            f'<div class=b><div class=who>{who}'
            f'<span>{m["author_title"]} &middot; {stamp}</span></div>'
            f'<div class=tx>{text}</div>{thread}{tags}</div></div>'
        )

    return PAGE.replace("__FEED__", "\n".join(feed)).replace("__N__", str(len(msgs)))
