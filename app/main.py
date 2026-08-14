"""Clearance - web front door. Single file, no external assets: venue wifi is
not a dependency the demo can afford."""
from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from clearance import Workspace, ask_clearance, ask_naive

app = FastAPI(title="Clearance")
WS = Workspace.load()

DEMO_QUESTIONS = [
    "Why is hiring frozen?",
    "Am I going to be made permanent?",
    "How do we deploy?",
]

PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>Clearance</title><meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#e6edf3;
 font:16px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 22px 60px}
h1{font-size:30px;margin:0;letter-spacing:-.02em}
h1 span{color:#7d8590;font-weight:400}
.tag{color:#7d8590;margin:6px 0 26px;font-size:17px}
.bar{display:flex;gap:22px;flex-wrap:wrap;align-items:flex-end;
 background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px 18px}
label{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.08em;
 color:#7d8590;margin-bottom:6px}
select,input,button{font:inherit;background:#0d1117;color:#e6edf3;
 border:1px solid #30363d;border-radius:7px;padding:9px 12px}
input{width:100%}
button{cursor:pointer}
button:hover{border-color:#58a6ff}
.modes{display:flex;gap:0}
.modes button{border-radius:0;border-right:none}
.modes button:first-child{border-radius:7px 0 0 7px}
.modes button:last-child{border-radius:0 7px 7px 0;border-right:1px solid #30363d}
.modes button.on{background:#1f6feb;border-color:#1f6feb;color:#fff}
.ask{display:flex;gap:10px;margin:18px 0 10px}
.ask button{background:#238636;border-color:#238636;color:#fff;padding:9px 22px}
.presets{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:26px}
.presets button{font-size:13px;color:#7d8590;padding:6px 12px}
.scope{margin:22px 0 12px;font-size:15px;color:#7d8590}
.scope b{color:#e6edf3}
.chip{display:inline-block;background:#1c2128;border:1px solid #30363d;
 border-radius:20px;padding:3px 12px;margin-right:7px;font-size:14px}
.chip.p{border-color:#bb8009;color:#e3b341}
.chip.no{border-color:#30363d;color:#484f58;text-decoration:line-through}
.cards{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:18px 20px}
.card.p{border-color:#bb8009}
.card.naive{border-color:#f85149;grid-column:1/-1}
.ch{font-size:15px;font-weight:600;margin-bottom:12px;color:#58a6ff}
.card.p .ch{color:#e3b341}
.card.naive .ch{color:#f85149}
.ans{white-space:pre-wrap;font-size:16px}
.src{margin-top:14px;padding-top:12px;border-top:1px solid #21262d;
 font-size:12.5px;color:#7d8590;white-space:pre-wrap}
.warn{background:#2d1214;border:1px solid #f85149;border-radius:10px;
 padding:16px 20px;margin-bottom:16px;color:#ff9b95}
.muted{color:#7d8590;padding:26px 0}
</style></head><body><div class=wrap>
<h1>Clearance <span>&mdash; your Slack has a memory, and it knows what you're cleared to know</span></h1>
<p class=tag>Northwind workspace &middot; 44 messages &middot; #general, #eng, #leadership-private</p>

<div class=bar>
 <div><label>Asking as</label>
  <select id=who>__PEOPLE__<option value="">Unknown caller (outsider)</option></select></div>
 <div><label>Mode</label><div class=modes>
  <button id=mNaive onclick="setMode('naive')">Naive</button>
  <button id=mClear class=on onclick="setMode('clearance')">Clearance</button>
 </div></div>
 <div style=flex:1><label>Question</label>
  <input id=q value="Why is hiring frozen?" onkeydown="if(event.key=='Enter')go()"></div>
 <button onclick=go()>Ask</button>
</div>

<div class=presets>__PRESETS__</div>
<div id=scope></div>
<div id=out class=muted>Ask something.</div>
</div><script>
let mode='clearance';
function setMode(m){mode=m;
 mNaive.className=m=='naive'?'on':'';mClear.className=m=='clearance'?'on':'';}
function preset(t){q.value=t;go()}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function go(){
 out.className='muted';out.textContent='Thinking...';scope.innerHTML='';
 const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({question:q.value,user_id:who.value,mode:mode})});
 const d=await r.json();
 if(d.mode=='naive'){
  scope.innerHTML='<div class=scope>Queried: <b>the entire workspace</b>, including channels this person cannot see.</div>';
  out.className='cards';
  out.innerHTML='<div class="card naive"><div class=ch>&#9888; one memory, no scoping</div>'+
   '<div class=ans>'+esc(d.cards[0].answer)+'</div>'+
   (d.cards[0].sources.length?'<div class=src>'+esc(d.cards[0].sources.join('\\n'))+'</div>':'')+'</div>';
  return;
 }
 if(d.outsider){
  out.className='';
  out.innerHTML='<div class=warn><b>Unknown caller.</b> No identity, so no channels. '+
   'Least privilege by default &mdash; which is why it is safe to give a stranger the number.</div>';
  return;
 }
 scope.innerHTML='<div class=scope>Queried <b>'+d.channels.length+'</b> channel(s): '+
  d.all.map(c=>'<span class="chip'+(d.channels.includes(c)?(d.private.includes(c)?' p':''):' no')+'">#'+c+'</span>').join('')+
  '<br><span style="font-size:13.5px">Struck-through channels were never queried. You cannot leak what you did not ask.</span></div>';
 out.className='cards';
 out.innerHTML=d.cards.map(c=>'<div class="card'+(c.is_private?' p':'')+'">'+
  '<div class=ch>#'+esc(c.channel)+(c.is_private?' &middot; private':'')+'</div>'+
  '<div class=ans>'+esc(c.answer)+'</div>'+
  (c.sources.length?'<div class=src>'+esc(c.sources.join('\\n'))+'</div>':'')+'</div>').join('');
}
</script></body></html>"""


def render() -> str:
    people = "".join(
        f'<option value="{uid}"{" selected" if p["name"].startswith("Sam") else ""}>'
        f'{p["name"]} &mdash; {p["title"]}</option>'
        for uid, p in WS.people.items()
    )
    presets = "".join(
        f"""<button onclick="preset('{q.replace("'", "\\'")}')">{q}</button>"""
        for q in DEMO_QUESTIONS
    )
    return PAGE.replace("__PEOPLE__", people).replace("__PRESETS__", presets)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return render()


@app.post("/ask")
async def ask(req: Request) -> JSONResponse:
    body = await req.json()
    question = (body.get("question") or "").strip()
    if not question:
        return JSONResponse({"error": "empty question"}, status_code=400)

    if body.get("mode") == "naive":
        return JSONResponse(await ask_naive(question))

    user_id = body.get("user_id") or None
    result = await ask_clearance(WS, question, user_id)
    result["all"] = list(WS.channels)
    result["private"] = [n for n, c in WS.channels.items() if c["is_private"]]
    return JSONResponse(result)


@app.post("/voice")
async def voice(req: Request) -> JSONResponse:
    """VAPI webhook. The caller's number IS the identity - no login, and an
    unknown number is an outsider by construction."""
    body = await req.json()
    msg = body.get("message", {})
    number = (msg.get("call", {}).get("customer", {}) or {}).get("number")
    args = (msg.get("toolCalls") or [{}])[0].get("function", {}).get("arguments") or {}
    question = args.get("question") or msg.get("transcript") or ""

    user_id = WS.resolve_phone(number)
    result = await ask_clearance(WS, question, user_id)
    if result["outsider"]:
        spoken = ("I don't recognise this number, so I can't share anything from "
                  "this workspace.")
    else:
        who = WS.people[user_id]["name"]
        spoken = f"For {who}. " + " ".join(
            f"From {c['channel']}: {c['answer']}" for c in result["cards"])
    return JSONResponse({"results": [{"toolCallId":
                        (msg.get("toolCalls") or [{}])[0].get("id"), "result": spoken}]})


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "people": len(WS.people), "channels": list(WS.channels)}
