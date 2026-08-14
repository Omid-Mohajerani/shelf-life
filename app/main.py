"""Shelf Life - web front door. Single file, no external assets: venue wifi is
not a dependency a demo can afford."""
from __future__ import annotations

import json
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from live import inject, reset, state
from shelflife import answer, verdict_only
import chat
from ui import LOGOS, PAGE

app = FastAPI(title="Shelf Life")




def render() -> str:
    return (PAGE.replace("__LOGO_Q__", LOGOS["qdrant"])
                .replace("__LOGO_C__", LOGOS["cognee"]))


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


@app.post("/verdict")
async def verdict(req: Request) -> JSONResponse:
    """Fast path: the trust verdict without waiting on the graph."""
    body = await req.json()
    question = (body.get("question") or "").strip()
    if not question:
        return JSONResponse({"error": "empty question"}, status_code=400)
    if body.get("offline"):
        cached = _fallback().get(question)
        if cached:
            return JSONResponse({**{k: cached[k] for k in ("question", "trust")},
                                 "timing": cached.get("timing", {}), "cached": True})
    return JSONResponse(verdict_only(question))


@app.post("/inject")
async def inject_msg(req: Request) -> JSONResponse:
    """Post a message into both stores, exactly as the corpus went in."""
    try:
        body = await req.json()
    except Exception:
        body = {}
    return JSONResponse(inject(body.get("text")))


@app.post("/reset")
async def reset_msg() -> JSONResponse:
    return JSONResponse(reset())


@app.get("/state")
async def live_state() -> JSONResponse:
    return JSONResponse(state())


COLD_OPEN = """<!doctype html><html><head><meta charset=utf-8>
<title>Shelf Life</title><style>
html,body{margin:0;height:100%;background:#f6f8fa;color:#1f2328;
 font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
/* The quote is set in serif on purpose: it should read as a statement on a
   wall, not as another dark-mode app screen. */
.t,.who{font-family:Georgia,"Iowan Old Style","Times New Roman",serif}
.c{height:100%;display:flex;flex-direction:column;justify-content:center;
 align-items:center;padding:6vw;text-align:left}
.m{max-width:1000px;background:#fff;border-left:5px solid #d4a72c;
 box-shadow:0 2px 12px rgba(31,35,40,.08);
 border-radius:0 14px 14px 0;padding:38px 44px}
.who{color:#57606a;font-size:min(2.2vw,22px);margin-bottom:18px}
.who b{color:#1f2328}
.t{font-size:min(4.4vw,52px);line-height:1.32;font-weight:600}
.f{color:#57606a;font-size:min(2vw,20px);margin-top:34px;max-width:1000px}
.f b{color:#9a6700}
a{color:#0969da;text-decoration:none;font-size:16px;margin-top:40px;display:block}
</style></head><body><div class=c>
<div class=m>
 <div class=who><b>Marek Nowak</b> &middot; #voice-eng &middot; 23 July 2026</div>
 <div class=t>&ldquo;Flagging that as a guess, not a finding.<br>I haven&rsquo;t proven it.&rdquo;</div>
</div>
<div class=f>Twelve days later he retracted it. <b>Every bot demoed tonight
 will retrieve the guess and serve it to you as the answer.</b></div>
<a href="/">&rarr; shelflife.ringamo.dev</a>
</div></body></html>"""


@app.get("/chat", response_class=HTMLResponse)
async def channel() -> str:
    """#voice-eng itself - the raw material the verdict is computed from."""
    return chat.render()


@app.get("/open", response_class=HTMLResponse)
async def cold_open() -> str:
    """Full-screen opening slide. No logo, no title - just the message that
    argues with itself."""
    return COLD_OPEN


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
