"""Talk to it. A second front door onto the same memory.

Deliberately its own page and its own route - the web demo does not import any
of this, so if the voice leg misbehaves it cannot take the working demo with it.

Browser call rather than a phone number: no DID, no SBC, no DNS, and anyone in
the room can try it from their own laptop.

The visualiser is driven by real audio, not a loop: an AnalyserNode on the
microphone while you talk, and VAPI's volume-level events while it talks. On a
stage that difference reads instantly - the bars move when YOU move.
"""

TALK = """<!doctype html><html><head><meta charset=utf-8>
<title>Shelf Life — talk to it</title>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
:root{--bg:#f6f8fa;--panel:#fff;--line:#d8dee4;--dim:#57606a;--fg:#1f2328;
 --grn:#1a7f37;--red:#cf222e;--blu:#0969da;--vio:#8250df}
html,body{margin:0;min-height:100%;background:var(--bg);color:var(--fg);
 font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:800px;margin:0 auto;padding:40px 24px 60px}
h1{font-size:32px;margin:0;letter-spacing:-.03em}
h1 em{font-style:normal;color:var(--dim);font-weight:400;font-size:18px}
.sub{color:var(--dim);margin:10px 0 28px}

.stage{background:var(--panel);border:1px solid var(--line);border-radius:20px;
 padding:38px 30px 30px;text-align:center;box-shadow:0 1px 3px rgba(31,35,40,.06);
 transition:border-color .4s,box-shadow .4s}
.stage.you{border-color:#7fc4ff;box-shadow:0 0 0 4px rgba(9,105,218,.09)}
.stage.bot{border-color:#7ee2a0;box-shadow:0 0 0 4px rgba(26,127,55,.10)}

/* the visualiser */
.viz{height:120px;display:flex;align-items:center;justify-content:center;gap:5px;
 margin-bottom:8px}
.bar{width:7px;height:8px;border-radius:4px;background:#c9d3de;
 transition:background .35s}
.stage.you .bar{background:var(--blu)}
.stage.bot .bar{background:var(--grn)}

.label{font-size:13px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;
 color:var(--dim);min-height:20px;transition:color .3s}
.stage.you .label{color:var(--blu)}
.stage.bot .label{color:var(--grn)}
.state{margin:8px 0 24px;color:var(--dim);font-size:15px;min-height:24px}

button{font:inherit;cursor:pointer;border:0;border-radius:999px;padding:17px 42px;
 font-size:17px;font-weight:600;color:#fff;background:#1f883d;transition:.15s}
button:hover{background:#1a7f37;transform:translateY(-1px)}
button.on{background:var(--red)}
button:disabled{background:#8c959f;cursor:default;transform:none}

.hint{margin-top:26px;color:var(--dim);font-size:14.5px;text-align:left}
.hint b{color:var(--fg)}
.hint ul{margin:9px 0 0;padding-left:20px}
.hint li{margin:6px 0;cursor:default}
.log{margin-top:24px;text-align:left;font-size:15px}
.line{padding:11px 15px;border-radius:12px;margin-bottom:8px;background:#f0f2f5;
 animation:in .3s ease}
@keyframes in{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
.line.you{background:#ddeeff}
.line b{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.1em;
 color:var(--dim);margin-bottom:2px}
a{color:var(--blu);text-decoration:none}
.foot{margin-top:34px;padding-top:20px;border-top:1px solid var(--line);
 color:var(--dim);font-size:14px}
</style></head><body><div class=wrap>
<h1>Shelf Life <em>— talk to it</em></h1>
<p class=sub>The same memory, asked out loud. When an answer has been overturned,
 it says so <b>before</b> it answers.</p>

<div class=stage id=stage>
 <div class=viz id=viz></div>
 <div class=label id=label>ready</div>
 <div class=state id=state>Click below and allow the microphone. Nothing is recorded.</div>
 <button id=btn onclick=toggle()>Start talking</button>
</div>

<div class=hint><b>Try asking:</b>
 <ul>
  <li>&ldquo;The dialer isn't calling and the segment says Data Exhausted.&rdquo;</li>
  <li>&ldquo;Why won't our SFTP export connector connect? The credentials are correct.&rdquo;</li>
  <li>&ldquo;What does this team know that the docs don't?&rdquo;</li>
 </ul>
 Give it a few seconds &mdash; it reads whole threads, not chunks.
</div>

<div class=log id=log></div>
<div class=foot><a href="/">&larr; the web version</a> &middot;
 <a href="/chat">#voice-eng</a></div>
</div>

<script type="module">
import Vapi from "https://esm.sh/@vapi-ai/web@2.3.8";
const KEY="__KEY__", ASSISTANT="__ASSISTANT__";
const btn=document.getElementById('btn'), st=document.getElementById('state');
const stage=document.getElementById('stage'), label=document.getElementById('label');
const viz=document.getElementById('viz'), log=document.getElementById('log');

const N=28, bars=[];
for(let i=0;i<N;i++){const b=document.createElement('div');b.className='bar';
 viz.appendChild(b);bars.push(b);}

let vapi=null, live=false, mode='idle';
let audioCtx=null, analyser=null, data=null, stream=null, raf=null, botLevel=0;

if(!KEY||!ASSISTANT){btn.disabled=true;st.textContent='Voice is not configured on this server.';}

function setMode(m,text){
 mode=m; stage.className='stage'+(m==='you'?' you':m==='bot'?' bot':'');
 label.textContent={idle:'ready',connecting:'connecting',listen:'listening',
   you:'you are speaking',bot:'shelf life is speaking',think:'querying qdrant and cognee'}[m]||m;
 if(text!==undefined) st.textContent=text;
}

// A bell curve so the middle bars are tallest - reads as a voice, not a graph.
const shape=i=>{const x=(i-(N-1)/2)/((N-1)/2);return 1-0.72*x*x;};

function draw(){
 raf=requestAnimationFrame(draw);
 let mic=0;
 if(analyser){
  analyser.getByteTimeDomainData(data);
  let sum=0; for(let i=0;i<data.length;i++){const v=(data[i]-128)/128;sum+=v*v;}
  mic=Math.sqrt(sum/data.length);          // RMS
 }
 const speakingBot = botLevel>0.02;
 const amp = speakingBot ? botLevel*1.5 : mic*3.2;
 if(live && mode!=='think'){
  if(speakingBot) { if(mode!=='bot') setMode('bot'); }
  else if(mic>0.045){ if(mode!=='you') setMode('you'); }
  else if(mode!=='listen') setMode('listen');
 }
 for(let i=0;i<N;i++){
  const jitter=0.55+0.45*Math.sin(Date.now()/((speakingBot?90:150)+i*11)+i);
  const h = live ? 8+Math.min(1,amp)*92*shape(i)*jitter : 8;
  bars[i].style.height=h.toFixed(1)+'px';
 }
}

async function startMic(){
 try{
  stream=await navigator.mediaDevices.getUserMedia({audio:true});
  audioCtx=new (window.AudioContext||window.webkitAudioContext)();
  const src=audioCtx.createMediaStreamSource(stream);
  analyser=audioCtx.createAnalyser(); analyser.fftSize=1024;
  data=new Uint8Array(analyser.fftSize);
  src.connect(analyser);
 }catch(e){ /* the call still works; only the bars go quiet */ }
}
function stopMic(){
 if(stream) stream.getTracks().forEach(t=>t.stop());
 if(audioCtx) audioCtx.close();
 analyser=null; stream=null; audioCtx=null;
}

function say(who,text,mine){
 const d=document.createElement('div'); d.className='line'+(mine?' you':'');
 const b=document.createElement('b'); b.textContent=who; d.appendChild(b);
 d.appendChild(document.createTextNode(text));
 log.appendChild(d); d.scrollIntoView({behavior:'smooth',block:'nearest'});
}

window.toggle=async function(){
 if(live){ vapi.stop(); return; }
 if(!vapi){
  vapi=new Vapi(KEY);
  vapi.on('call-start',async()=>{live=true;btn.textContent='Stop';btn.className='on';
    await startMic(); setMode('listen','Just talk — it is listening.');});
  vapi.on('call-end',()=>{live=false;btn.textContent='Start talking';btn.className='';
    stopMic(); botLevel=0; setMode('idle','Call ended.');});
  vapi.on('volume-level',v=>{botLevel=v||0;});
  vapi.on('speech-start',()=>{botLevel=Math.max(botLevel,0.15);});
  vapi.on('speech-end',()=>{botLevel=0;});
  vapi.on('message',m=>{
    if(m.type==='transcript'&&m.transcriptType==='final')
      say(m.role==='user'?'you':'shelf life',m.transcript,m.role==='user');
    if(m.type==='tool-calls') setMode('think','Reading the docs and the channel…');
  });
  vapi.on('error',e=>{live=false;stopMic();btn.textContent='Start talking';
    btn.className='';setMode('idle','Error: '+((e&&e.message)||'call failed'));});
 }
 setMode('connecting','Connecting…');
 if(!raf) draw();
 try{ await vapi.start(ASSISTANT); }
 catch(e){ setMode('idle','Could not start: '+e.message); }
}
draw();
</script></body></html>"""
