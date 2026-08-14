"""Talk to it. A second front door onto the same memory.

Deliberately its own page and its own route - the web demo does not import any
of this, so if the voice leg misbehaves it cannot take the working demo with it.

Browser call rather than a phone number: no DID, no SBC, no DNS, and anyone in
the room can try it from their own laptop.
"""

TALK = """<!doctype html><html><head><meta charset=utf-8>
<title>Shelf Life — talk to it</title>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
:root{--bg:#f6f8fa;--panel:#fff;--line:#d8dee4;--dim:#57606a;--fg:#1f2328;
 --grn:#1a7f37;--red:#cf222e;--blu:#0969da}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);
 font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:44px 24px}
h1{font-size:32px;margin:0;letter-spacing:-.03em}
h1 em{font-style:normal;color:var(--dim);font-weight:400;font-size:18px}
.sub{color:var(--dim);margin:10px 0 30px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;
 padding:30px;text-align:center;box-shadow:0 1px 3px rgba(31,35,40,.06)}
button{font:inherit;cursor:pointer;border:0;border-radius:999px;padding:18px 40px;
 font-size:18px;font-weight:600;color:#fff;background:#1f883d;transition:.15s}
button:hover{background:#1a7f37;transform:translateY(-1px)}
button.on{background:var(--red)}
button:disabled{background:#8c959f;cursor:default;transform:none}
.state{margin-top:18px;color:var(--dim);font-size:15px;min-height:24px}
.orb{width:96px;height:96px;border-radius:50%;margin:0 auto 22px;
 background:radial-gradient(circle at 34% 30%,#79c0ff,#0969da);opacity:.28;
 transition:.3s}
.orb.live{opacity:1;animation:breathe 1.7s ease-in-out infinite}
.orb.speaking{animation:breathe .55s ease-in-out infinite}
@keyframes breathe{0%,100%{transform:scale(1)}50%{transform:scale(1.13)}}
.hint{margin-top:28px;color:var(--dim);font-size:14.5px;text-align:left}
.hint b{color:var(--fg)}
.hint ul{margin:9px 0 0;padding-left:20px}
.hint li{margin:5px 0}
.log{margin-top:22px;text-align:left;font-size:14.5px;max-height:280px;overflow-y:auto}
.line{padding:9px 13px;border-radius:10px;margin-bottom:7px;background:#f0f2f5}
.line.you{background:#ddf4e4}
.line b{display:block;font-size:11.5px;text-transform:uppercase;letter-spacing:.09em;
 color:var(--dim);margin-bottom:2px}
a{color:var(--blu);text-decoration:none}
.foot{margin-top:34px;padding-top:20px;border-top:1px solid var(--line);
 color:var(--dim);font-size:14px}
</style></head><body><div class=wrap>
<h1>Shelf Life <em>— talk to it</em></h1>
<p class=sub>The same memory, asked out loud. It tells you how much to trust its
 own answer before it gives you one.</p>

<div class=card>
 <div class=orb id=orb></div>
 <button id=btn onclick=toggle()>Start talking</button>
 <div class=state id=state>Microphone permission needed. Nothing is recorded.</div>
</div>

<div class=hint><b>Try asking:</b>
 <ul>
  <li>&ldquo;Why won't our SFTP export connector connect? The credentials are correct.&rdquo;</li>
  <li>&ldquo;The dialer isn't calling and the segment says Data Exhausted.&rdquo;</li>
  <li>&ldquo;What does this team know that the docs don't?&rdquo;</li>
 </ul>
 It takes a few seconds to answer &mdash; it is reading whole threads, not chunks.
</div>

<div class=log id=log></div>

<div class=foot><a href="/">&larr; the web version</a> &middot;
 <a href="/chat">#voice-eng</a></div>
</div>

<script type="module">
import Vapi from "https://esm.sh/@vapi-ai/web@2.3.8";
const KEY="__KEY__", ASSISTANT="__ASSISTANT__";
const btn=document.getElementById('btn'), st=document.getElementById('state');
const orb=document.getElementById('orb'), log=document.getElementById('log');
let vapi=null, live=false;

if(!KEY||!ASSISTANT){ btn.disabled=true; st.textContent='Voice is not configured on this server.'; }

function say(who,text,mine){
 const d=document.createElement('div'); d.className='line'+(mine?' you':'');
 d.innerHTML='<b></b>'; d.querySelector('b').textContent=who;
 d.appendChild(document.createTextNode(text));
 log.appendChild(d); log.scrollTop=log.scrollHeight;
}

window.toggle=async function(){
 if(live){ vapi.stop(); return; }
 if(!vapi){
  vapi=new Vapi(KEY);
  vapi.on('call-start',()=>{live=true;btn.textContent='Stop';btn.className='on';
    orb.className='orb live';st.textContent='Listening — just talk.';});
  vapi.on('call-end',()=>{live=false;btn.textContent='Start talking';btn.className='';
    orb.className='orb';st.textContent='Call ended.';});
  vapi.on('speech-start',()=>{orb.className='orb live speaking';});
  vapi.on('speech-end',()=>{orb.className='orb live';});
  vapi.on('message',m=>{
    if(m.type==='transcript'&&m.transcriptType==='final')
      say(m.role==='user'?'you':'shelf life',m.transcript,m.role==='user');
    if(m.type==='tool-calls')
      st.textContent='Querying Qdrant and cognee…';
  });
  vapi.on('error',e=>{st.textContent='Error: '+(e&&e.message?e.message:'call failed');
    orb.className='orb';btn.textContent='Start talking';btn.className='';live=false;});
 }
 st.textContent='Connecting…';
 try{ await vapi.start(ASSISTANT); }
 catch(e){ st.textContent='Could not start: '+e.message; }
}
</script></body></html>"""
