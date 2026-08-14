"""Shelf Life - web front door. Single file, no external assets: venue wifi is
not a dependency a demo can afford."""
from __future__ import annotations

import json
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from live import inject, reset, state
from shelflife import answer

app = FastAPI(title="Shelf Life")

PRESETS = [
    ("SFTP connector won't connect", "Our SFTP export connector won't connect but the credentials are correct. What is wrong?"),
    ("Push callback status out", "How do I get callback completion status out to an external system?"),
    ("Authenticate to the API", "How do I authenticate to the platform API?"),
    ("Dialer not calling", "The dialer isn't calling and the segment says Data Exhausted. What do I do?"),
]

PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>Shelf Life</title><meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#e6edf3;
 font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:26px 22px 70px}
h1{font-size:31px;margin:0;letter-spacing:-.02em}
h1 span{color:#7d8590;font-weight:400;font-size:19px}
.tag{color:#7d8590;margin:8px 0 24px}
.ask{display:flex;gap:10px}
input{flex:1;font:inherit;background:#161b22;color:#e6edf3;
 border:1px solid #30363d;border-radius:8px;padding:12px 14px}
button{font:inherit;cursor:pointer;background:#161b22;color:#e6edf3;
 border:1px solid #30363d;border-radius:8px;padding:12px 18px}
button:hover{border-color:#58a6ff}
.go{background:#238636;border-color:#238636;color:#fff;padding:12px 26px}
.presets{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 26px}
.presets button{font-size:13.5px;color:#7d8590;padding:7px 13px}
.verdict{border-radius:11px;padding:18px 22px;margin-bottom:18px;
 border:1px solid;font-size:17px}
.verdict .lvl{font-size:12px;letter-spacing:.13em;text-transform:uppercase;
 font-weight:700;margin-bottom:7px;opacity:.85}
.verdict .sig{font-size:14.5px;margin-top:9px;opacity:.9}
.good{background:#0f2417;border-color:#2ea043;color:#7ee787}
.stale{background:#2b2411;border-color:#bb8009;color:#e3b341}
.unproven{background:#2b2411;border-color:#bb8009;color:#e3b341}
.superseded{background:#2d1214;border-color:#f85149;color:#ff9b95}
.none{background:#161b22;border-color:#30363d;color:#7d8590}
.cols{display:grid;gap:16px;grid-template-columns:1fr 1fr}
@media(max-width:820px){.cols{grid-template-columns:1fr}}
.card{background:#161b22;border:1px solid #30363d;border-radius:11px;padding:19px 21px}
.card h3{margin:0 0 4px;font-size:15px;letter-spacing:.04em;text-transform:uppercase}
.card .sub{font-size:12.5px;color:#7d8590;margin-bottom:13px}
.docs h3{color:#58a6ff}
.chan h3{color:#7ee787}
.silent{border-color:#bb8009}
.silent h3{color:#e3b341}
.ans{white-space:pre-wrap;font-size:16px}
.ask-who{margin-top:18px;background:#161b22;border:1px solid #30363d;
 border-radius:11px;padding:17px 21px}
.ask-who h3{margin:0 0 11px;font-size:13px;letter-spacing:.1em;
 text-transform:uppercase;color:#7d8590}
.person{display:inline-block;background:#1c2128;border:1px solid #30363d;
 border-radius:8px;padding:8px 14px;margin:0 9px 9px 0}
.person b{color:#58a6ff}
.person i{color:#7d8590;font-style:normal;font-size:13px}
.ev{margin-top:18px}
.ev h3{font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:#7d8590;
 margin:0 0 11px}
.msg{background:#161b22;border-left:3px solid #30363d;border-radius:0 8px 8px 0;
 padding:11px 15px;margin-bottom:9px;font-size:14.5px}
.msg.u{border-left-color:#bb8009}
.msg.s{border-left-color:#f85149}
.msg .m{color:#7d8590;font-size:12.5px;margin-bottom:4px}
.flag{color:#e3b341;font-size:12.5px;margin-top:5px}
.flag.s{color:#ff9b95}
.muted{color:#7d8590;padding:30px 0}
.trace{margin-top:11px;padding-top:10px;border-top:1px solid rgba(255,255,255,.13);
 font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;opacity:.75}
.foot{margin-top:34px;display:flex;align-items:center;gap:18px;color:#7d8590;
 border-top:1px solid #21262d;padding-top:20px}
.foot img{width:96px;height:96px;background:#fff;padding:6px;border-radius:8px}
.foot b{color:#e6edf3;font-size:17px}
</style></head><body><div class=wrap>
<h1>Shelf Life <span>&mdash; every answer in a company has one</span></h1>
<p class=tag>What the docs say &middot; what the team found &middot; how much to trust it &middot; who to ask</p>
<div class=ask>
 <input id=q placeholder="Ask something a colleague would know&hellip;"
   value="Our SFTP export connector won't connect but the credentials are correct. What is wrong?"
   onkeydown="if(event.key=='Enter')go()">
 <button class=go onclick=go()>Ask</button>
</div>
<div class=presets>__PRESETS__<label style="color:#7d8590;font-size:12.5px;margin-left:auto;align-self:center">
 <input type=checkbox id=off style="width:auto;vertical-align:middle"> offline</label></div>
<div id=out class=muted>Ask something.</div>
<div class=foot>__QR__<div><b>shelflife.ringamo.dev</b><br>
Try it from your seat &mdash; it is live now.</div></div>
</div><script>
function preset(t){q.value=t;go()}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function go(){
 out.className='muted';out.textContent='Reading the docs and the channel\\u2026';
 const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({question:q.value,offline:document.getElementById('off').checked})});
 const d=await r.json();
 const t=d.trust;
 let h='<div class="verdict '+t.level+'"><div class=lvl>'+esc(t.level)+'</div>'+
   esc(t.headline)+(d.cached?' <span style="opacity:.6;font-size:13px">(cached)</span>':'')+
   (t.signals.length?'<div class=sig>'+t.signals.map(esc).join('<br>')+'</div>':'')+
   (t.trace?'<div class=trace>'+esc(t.trace)+'</div>':'')+'</div>';
 h+='<div class=cols>'+
  '<div class="card docs'+(d.docs.silent?' silent':'')+'"><h3>Official documentation</h3>'+
   '<div class=sub>'+(d.docs.silent?'does not cover this':'authoritative, versioned')+'</div>'+
   '<div class=ans>'+esc(d.docs.answer)+'</div></div>'+
  '<div class="card chan"><h3>What the team found</h3>'+
   '<div class=sub>#voice-eng &middot; practitioner experience</div>'+
   '<div class=ans>'+esc(d.channel.answer)+'</div></div></div>';
 if(t.ask&&t.ask.length){
  h+='<div class=ask-who><h3>Who to ask</h3>'+t.ask.map(p=>
   '<span class=person><b>'+esc(p.name)+'</b> <i>'+esc(p.title)+
   ' &middot; '+p.n+' message'+(p.n>1?'s':'')+' on this, latest '+esc(p.latest)+'</i></span>'
  ).join('')+'</div>';
 }
 if(t.evidence&&t.evidence.length){
  h+='<div class=ev><h3>Evidence</h3>'+t.evidence.map(e=>
   '<div class="msg'+(e.unproven?' u':'')+(e.supersedes?' s':'')+'">'+
   '<div class=m>'+esc(e.date)+' &middot; '+esc(e.author)+'</div>'+esc(e.text)+
   (e.unproven?'<div class=flag>&#9888; author flagged this as unproven</div>':'')+
   (e.supersedes?'<div class="flag s">&#9888; this overturns an earlier answer</div>':'')+
   '</div>').join('')+'</div>';
 }
 out.className='';out.innerHTML=h;
}
</script></body></html>"""


def _qr() -> str:
    """QR for the live URL, inlined as a data URI - no external asset, because a
    demo page that fetches from the internet is a demo that can fail."""
    try:
        import base64
        import io

        import segno
        buf = io.BytesIO()
        segno.make("https://shelflife.ringamo.dev", error="m").save(
            buf, kind="png", scale=6, border=1)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="QR">'
    except Exception:
        return ""


def render() -> str:
    presets = "".join(
        f"""<button onclick="preset('{q.replace("'", "\\'")}')">{label}</button>"""
        for label, q in PRESETS
    )
    return PAGE.replace("__PRESETS__", presets).replace("__QR__", _qr())


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return render()


def _fallback() -> dict:
    """Answers captured while the network worked. See tools/capture_fallback.py."""
    path = os.path.join(os.path.dirname(__file__), "fallback.json")
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


@app.post("/ask")
async def ask(req: Request) -> JSONResponse:
    body = await req.json()
    question = (body.get("question") or "").strip()
    if not question:
        return JSONResponse({"error": "empty question"}, status_code=400)

    cache = _fallback()
    if body.get("offline"):
        if question in cache:
            return JSONResponse({**cache[question], "cached": True})
        return JSONResponse({"error": "not in the offline cache"}, status_code=404)

    try:
        return JSONResponse(await answer(question))
    except Exception:
        # Losing the network mid-demo should degrade, not collapse.
        if question in cache:
            return JSONResponse({**cache[question], "cached": True})
        raise


@app.post("/inject")
async def inject_msg() -> JSONResponse:
    """Post the new message. Same collection the verdict is computed from."""
    return JSONResponse(inject())


@app.post("/reset")
async def reset_msg() -> JSONResponse:
    return JSONResponse(reset())


@app.get("/state")
async def live_state() -> JSONResponse:
    return JSONResponse(state())


COLD_OPEN = """<!doctype html><html><head><meta charset=utf-8>
<title>Shelf Life</title><style>
html,body{margin:0;height:100%;background:#0d1117;color:#e6edf3;
 font:ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.c{height:100%;display:flex;flex-direction:column;justify-content:center;
 align-items:center;padding:6vw;text-align:left}
.m{max-width:1000px;background:#161b22;border-left:5px solid #bb8009;
 border-radius:0 14px 14px 0;padding:38px 44px}
.who{color:#7d8590;font-size:min(2.2vw,22px);margin-bottom:18px}
.who b{color:#e6edf3}
.t{font-size:min(4.4vw,52px);line-height:1.32;font-weight:600}
.f{color:#7d8590;font-size:min(2vw,20px);margin-top:34px;max-width:1000px}
.f b{color:#e3b341}
a{color:#58a6ff;text-decoration:none;font-size:16px;margin-top:40px;display:block}
</style></head><body><div class=c>
<div class=m>
 <div class=who><b>Marek Nowak</b> &middot; #voice-eng &middot; 23 July 2026</div>
 <div class=t>&ldquo;Flagging that as a guess, not a finding.<br>I haven&rsquo;t proven it.&rdquo;</div>
</div>
<div class=f>Twelve days later he retracted it. <b>Every bot demoed tonight
 will retrieve the guess and serve it to you as the answer.</b></div>
<a href="/">&rarr; shelflife.ringamo.dev</a>
</div></body></html>"""


@app.get("/open", response_class=HTMLResponse)
async def cold_open() -> str:
    """Full-screen opening slide. No logo, no title - just the message that
    argues with itself."""
    return COLD_OPEN


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
