"""Talk to it. A second front door onto the same memory.

Its own page and its own route - the web demo imports none of this, so if the
voice leg misbehaves it cannot take the working demo down with it.

Browser call rather than a phone number: no DID, no SBC, no DNS, and anyone in
the room can try it from their own laptop.

The orb is driven by real audio - an AnalyserNode on the microphone while you
talk, VAPI volume-level events while it talks. It moves because you moved.
"""

TALK = """<!doctype html><html><head><meta charset=utf-8>
<title>Shelf Life — talk to it</title>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
:root{--vio:#8b5cf6;--pink:#ec4899;--teal:#14b8a6;--dim:#8b93a7}
html,body{margin:0;min-height:100%;background:#07070d;color:#eef1f8;
 font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
 overflow-x:hidden}
body:before,body:after{content:"";position:fixed;border-radius:50%;
 filter:blur(120px);pointer-events:none;z-index:0}
body:before{width:60vw;height:60vw;top:-22vw;left:-16vw;
 background:radial-gradient(circle,rgba(99,70,220,.42),transparent 65%)}
body:after{width:62vw;height:62vw;bottom:-26vw;right:-16vw;
 background:radial-gradient(circle,rgba(20,184,166,.26),transparent 62%)}
.glow3{position:fixed;width:46vw;height:46vw;bottom:-20vw;left:16vw;
 filter:blur(130px);border-radius:50%;z-index:0;pointer-events:none;
 background:radial-gradient(circle,rgba(236,72,153,.24),transparent 62%)}

.wrap{position:relative;z-index:1;max-width:760px;margin:0 auto;
 padding:8vh 24px 60px;text-align:center;min-height:100vh;
 display:flex;flex-direction:column;align-items:center}

/* the orb */
.orbwrap{position:relative;width:200px;height:200px;display:grid;place-items:center;
 margin-bottom:26px}
.ring{position:absolute;inset:0;border-radius:50%;border:1px solid rgba(255,255,255,.10)}
.pulse{position:absolute;inset:14px;border-radius:50%;
 border:1px solid rgba(139,92,246,.5);opacity:0;pointer-events:none}
.live .pulse{animation:ripple 2.4s ease-out infinite}
.live .pulse:nth-of-type(2){animation-delay:.8s}
.live .pulse:nth-of-type(3){animation-delay:1.6s}
@keyframes ripple{0%{transform:scale(1);opacity:.55}100%{transform:scale(1.6);opacity:0}}
.orb{width:108px;height:108px;border-radius:50%;display:grid;place-items:center;
 background:linear-gradient(140deg,var(--vio),var(--pink));
 box-shadow:0 0 46px rgba(139,92,246,.55);transition:box-shadow .25s,background .5s;
 will-change:transform}
.bot .orb{background:linear-gradient(140deg,#10b981,var(--teal));
 box-shadow:0 0 52px rgba(20,184,166,.6)}
.think .orb{background:linear-gradient(140deg,#6366f1,#8b5cf6)}
.orb svg{width:42px;height:42px;fill:#fff;opacity:.96}

h1{font-size:40px;margin:0;letter-spacing:-.035em;font-weight:700}
.kicker{color:#a78bfa;font-size:12.5px;letter-spacing:.22em;text-transform:uppercase;
 font-weight:700;margin:9px 0 16px}
.bot .kicker{color:#5eead4}
.tag{color:var(--dim);font-size:17px;margin:0 0 30px;max-width:520px;line-height:1.55}
.tag b{color:#eef1f8;font-weight:600}

button{font:inherit;cursor:pointer;border:0;border-radius:999px;padding:17px 46px;
 font-size:17px;font-weight:600;color:#fff;letter-spacing:.01em;
 background:linear-gradient(100deg,var(--vio),var(--pink));
 box-shadow:0 8px 30px rgba(139,92,246,.4);transition:.18s}
button:hover{transform:translateY(-2px);box-shadow:0 12px 38px rgba(139,92,246,.55)}
button.on{background:linear-gradient(100deg,#f43f5e,#ef4444);
 box-shadow:0 8px 30px rgba(244,63,94,.4)}
button:disabled{background:#2a2a3a;box-shadow:none;cursor:default;transform:none}
.note{color:#6b7280;font-size:13.5px;margin-top:13px;min-height:20px}

.hint{margin-top:38px;color:var(--dim);font-size:14.5px;text-align:left;
 max-width:560px;background:rgba(255,255,255,.032);
 border:1px solid rgba(255,255,255,.07);border-radius:16px;padding:18px 22px}
.hint b{color:#eef1f8}
.hint ul{margin:9px 0 0;padding-left:19px}
.hint li{margin:6px 0}
.log{margin-top:26px;text-align:left;max-width:640px;width:100%;font-size:15px}
.line{padding:12px 16px;border-radius:14px;margin-bottom:9px;
 background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.06);
 animation:in .3s ease}
.line.you{background:rgba(139,92,246,.15);border-color:rgba(139,92,246,.3)}
@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.line b{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.14em;
 color:var(--dim);margin-bottom:3px}
a{color:#a78bfa;text-decoration:none}
.foot{margin-top:40px;color:#6b7280;font-size:13.5px}

/* the work, shown while it talks */
.work{width:100%;max-width:700px;margin-top:30px;text-align:left}
.pipe{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
 border-radius:16px;padding:16px 20px}
.leg{display:flex;align-items:center;gap:13px;padding:8px 0;font-size:14px;
 color:var(--dim);opacity:.35;transition:opacity .35s}
.leg.on,.leg.done{opacity:1}
.leg img{width:24px;height:24px;border-radius:6px;background:#fff;padding:2px;
 flex:0 0 24px;object-fit:contain}
.leg .nm{font-weight:600;color:#eef1f8;min-width:172px}
.leg .st{flex:1}
.leg .ms{font:12px ui-monospace,Menlo,monospace;color:#5eead4;font-weight:600}
.sp{width:14px;height:14px;border-radius:50%;border:2px solid rgba(255,255,255,.15);
 border-top-color:#a78bfa;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.vd{border-radius:14px;padding:16px 20px;margin-top:14px;border:1px solid;font-size:15px}
.vd .lv{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:800;
 margin-bottom:5px;opacity:.9}
.vd .tr{margin-top:10px;padding-top:9px;border-top:1px solid rgba(255,255,255,.14);
 font:11.5px/1.5 ui-monospace,Menlo,monospace;opacity:.72}
.good{background:rgba(16,185,129,.13);border-color:#10b981;color:#6ee7b7}
.superseded{background:rgba(244,63,94,.13);border-color:#f43f5e;color:#fda4af}
.unproven,.stale{background:rgba(234,179,8,.13);border-color:#eab308;color:#fde047}
.cards{display:grid;gap:12px;grid-template-columns:1fr 1fr;margin-top:12px}
@media(max-width:700px){.cards{grid-template-columns:1fr}}
.cd{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
 border-radius:14px;padding:15px 18px;font-size:14px}
.cd h4{margin:0 0 8px;font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;
 color:#a78bfa}
.cd.t h4{color:#5eead4}
.ask{margin-top:12px;background:rgba(255,255,255,.04);
 border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:14px 18px}
.ask h4{margin:0 0 10px;font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;
 color:var(--dim)}
.who{display:inline-flex;align-items:center;gap:11px;margin:0 10px 6px 0}
.av{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;
 font-weight:700;font-size:12.5px;color:#fff}
.who b{display:block;font-size:14.5px;color:#eef1f8}
.who i{font-style:normal;color:var(--dim);font-size:12px}
</style></head><body>
<div class=glow3></div>
<div class=wrap id=wrap>

<div class=orbwrap id=orbwrap>
 <div class=ring></div>
 <div class=pulse></div><div class=pulse></div><div class=pulse></div>
 <div class=orb id=orb><svg viewBox="0 0 24 24"><path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z"/><path d="M19 11a1 1 0 1 0-2 0 5 5 0 0 1-10 0 1 1 0 1 0-2 0 7 7 0 0 0 6 6.92V21h-2a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-2v-3.08A7 7 0 0 0 19 11z"/></svg></div>
</div>

<h1>Shelf Life</h1>
<div class=kicker id=kicker>workspace memory</div>
<p class=tag>Ask it anything about the team's channel. When an answer has been
 overturned, <b>it tells you before it answers.</b></p>

<button id=btn onclick=toggle()>Talk to it</button>
<div class=note id=note>Works in your browser — no app needed</div>

<div class=hint><b>Try asking:</b>
 <ul>
  <li>&ldquo;The dialer isn't calling and the segment says Data Exhausted.&rdquo;</li>
  <li>&ldquo;Why won't our SFTP export connector connect? The credentials are correct.&rdquo;</li>
  <li>&ldquo;What does this team know that the docs don't?&rdquo;</li>
 </ul>
</div>

<div class=work id=work></div>
<div class=log id=log></div>
<div class=foot><a href="/text">the text version</a> &middot; <a href="/chat">#voice-eng</a></div>
</div>

<script type="module">
import Vapi from "https://esm.sh/@vapi-ai/web@2.3.8";
const KEY="__KEY__", ASSISTANT="__ASSISTANT__";
const LOGO_Q="__LOGO_Q__", LOGO_C="__LOGO_C__";
const btn=document.getElementById('btn'), note=document.getElementById('note');
const wrap=document.getElementById('wrap'), orb=document.getElementById('orb');
const orbwrap=document.getElementById('orbwrap');
const kicker=document.getElementById('kicker'), log=document.getElementById('log');

let vapi=null, live=false, mode='idle', thinkUntil=0;
let audioCtx=null, analyser=null, data=null, stream=null, raf=null, botLevel=0, smooth=0;

if(!KEY||!ASSISTANT){btn.disabled=true;note.textContent='Voice is not configured on this server.';}

const LABEL={idle:'workspace memory',connecting:'connecting',listen:'listening',
 you:'you are speaking',bot:'shelf life is speaking',think:'reading the channel'};

function setMode(m,text){
 if(m===mode && text===undefined) return;
 mode=m;
 wrap.className='wrap'+(m==='bot'?' bot':m==='think'?' think':'');
 orbwrap.className='orbwrap'+(live?' live':'');
 kicker.textContent=LABEL[m]||m;
 if(text!==undefined) note.textContent=text;
}

function draw(){
 raf=requestAnimationFrame(draw);
 let mic=0;
 if(analyser){
  analyser.getByteTimeDomainData(data);
  let sum=0; for(let i=0;i<data.length;i++){const v=(data[i]-128)/128;sum+=v*v;}
  mic=Math.sqrt(sum/data.length);
 }
 const speakingBot=botLevel>0.02;
 // 'think' is a hint while the tool call is out - it expires, and the assistant
 // speaking cancels it immediately. Otherwise the orb freezes mid-call.
 const thinking = Date.now()<thinkUntil && !speakingBot;
 if(live){
  if(thinking) setMode('think');
  else if(speakingBot) setMode('bot');
  else if(mic>0.045) setMode('you');
  else setMode('listen');
 }
 const target = live ? Math.min(1,(speakingBot?botLevel*1.6:mic*3.4)) : 0;
 smooth += (target-smooth)*0.22;
 orb.style.transform='scale('+(1+smooth*0.30).toFixed(3)+')';
 const c = mode==='bot' ? '20,184,166' : '139,92,246';
 orb.style.boxShadow='0 0 '+(44+smooth*70).toFixed(0)+'px rgba('+c+','+(0.5+smooth*0.45).toFixed(2)+')';
}

async function startMic(){
 try{
  stream=await navigator.mediaDevices.getUserMedia({audio:true});
  audioCtx=new (window.AudioContext||window.webkitAudioContext)();
  const src=audioCtx.createMediaStreamSource(stream);
  analyser=audioCtx.createAnalyser(); analyser.fftSize=1024;
  data=new Uint8Array(analyser.fftSize); src.connect(analyser);
 }catch(e){ /* the call still works; only the orb goes still */ }
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

// The agent answers over the server webhook; the browser runs the SAME query so
// the room can watch the work while it talks. Two views of one memory.
const work=document.getElementById('work');
function esc(t){return (t||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function md(t){return esc(t).replace(/[*][*](.+?)[*][*]/g,'<b>$1</b>')
 .replace(/[[]OFFICIAL DOCUMENTATION[\]]\s*/g,'').replace(/[[]TEAM CHANNEL[^\]]*[\]]\s*/g,'')}
function legs(state,ms){
 const L=[['q','Qdrant','scanning 32 messages'],
          ['c','cognee · docs','reading 8 doc pages'],
          ['c','cognee · #voice-eng','reading 8 threads']];
 return '<div class=pipe>'+L.map((l,i)=>{
  const st=state[i]||'', v=ms&&ms[i]!=null?ms[i]:null;
  const r = st==='done'&&v!=null?'<span class=ms>'+v+'ms</span>'
          : st==='done'?'<span class=ms>done</span>'
          : st==='on'?'<span class=sp></span>':'';
  return '<div class="leg '+st+'"><img src="'+(l[0]==='q'?LOGO_Q:LOGO_C)+'" alt="">'+
   '<span class=nm>'+l[1]+'</span><span class=st>'+l[2]+'</span>'+r+'</div>';
 }).join('')+'</div>';
}
function verdictHtml(t,d){
 let h='<div class="vd '+t.level+'"><div class=lv>'+esc(t.level)+'</div>'+
  esc(t.headline)+(t.signals.length?'<br>'+t.signals.map(esc).join('<br>'):'')+
  (t.trace?'<div class=tr>'+esc(t.trace)+'</div>':'')+'</div>';
 if(t.ask&&t.ask.length){
  const P=['#8b5cf6','#10b981','#ec4899','#f59e0b','#3b82f6'];
  h+='<div class=ask><h4>Who to ask</h4>'+t.ask.map((p,i)=>{
   const ini=p.name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase();
   return '<span class=who><span class=av style="background:'+P[i%P.length]+'">'+ini+
    '</span><span><b>'+esc(p.name)+'</b><i>'+esc(p.title)+' · '+p.n+' message'+
    (p.n>1?'s':'')+', latest '+esc(p.latest)+'</i></span></span>';
  }).join('')+'</div>';
 }
 if(d) h+='<div class=cards><div class=cd><h4>Official documentation</h4>'+
   md(d.docs.answer.slice(0,420))+'</div><div class="cd t"><h4>What the team found</h4>'+
   md(d.channel.answer.slice(0,420))+'</div></div>';
 return h;
}
window.showWork=async function(q){
 const body=JSON.stringify({question:q});
 work.innerHTML=legs(['on','on','on']);
 const vr=await fetch('/verdict',{method:'POST',
   headers:{'Content-Type':'application/json'},body:body});
 const v=await vr.json();
 const qms=(v.timing||{}).qdrant_ms;
 work.innerHTML=legs(['done','on','on'],[qms,null,null])+verdictHtml(v.trust,null);
 const r=await fetch('/ask',{method:'POST',
   headers:{'Content-Type':'application/json'},body:body});
 const d=await r.json(); const tm=d.timing||{};
 work.innerHTML=legs(['done','done','done'],
   [tm.qdrant_ms||qms,tm.cognee_docs_ms,tm.cognee_channel_ms])+verdictHtml(d.trust,d);
}

window.toggle=async function(){
 if(live){ vapi.stop(); return; }
 if(!vapi){
  vapi=new Vapi(KEY);
  vapi.on('call-start',async()=>{live=true;btn.textContent='End call';btn.className='on';
    await startMic(); setMode('listen','Just talk — it is listening.');});
  vapi.on('call-end',()=>{live=false;btn.textContent='Talk to it';btn.className='';
    stopMic(); botLevel=0; setMode('idle','Works in your browser — no app needed');});
  vapi.on('volume-level',v=>{botLevel=v||0;});
  vapi.on('speech-start',()=>{thinkUntil=0;botLevel=Math.max(botLevel,0.15);});
  vapi.on('speech-end',()=>{botLevel=0;});
  vapi.on('message',m=>{
    if(m.type==='transcript'&&m.transcriptType==='final')
      say(m.role==='user'?'you':'shelf life',m.transcript,m.role==='user');
    if(m.type==='tool-calls'){thinkUntil=Date.now()+45000;
      setMode('think','Querying Qdrant and cognee…');
      const c=(m.toolCalls||m.toolCallList||[])[0]; let a=(c&&c.function&&c.function.arguments)||{};
      if(typeof a==='string'){try{a=JSON.parse(a);}catch(e){a={};}}
      if(a.question) window.showWork(a.question);}
  });
  vapi.on('error',e=>{live=false;stopMic();btn.textContent='Talk to it';btn.className='';
    setMode('idle','Error: '+((e&&e.message)||'call failed'));});
 }
 setMode('connecting','Connecting…');
 try{ await vapi.start(ASSISTANT); }
 catch(e){ setMode('idle','Could not start: '+e.message); }
}
draw();
</script></body></html>"""
