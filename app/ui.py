"""The page. Single file, no external assets - a demo that fetches from the
internet is a demo that can fail in a back courtyard in Kreuzberg."""

# Two questions, not four. Two minutes is an argument, not a tour.
# The other two stay reachable by typing, so a judge poking at the URL later
# still finds them.
PRESETS = [
    ("The docs are wrong",
     "Our SFTP export connector won't connect but the credentials are correct. What is wrong?"),
    ("The answer was retracted",
     "The dialer isn't calling and the segment says Data Exhausted. What do I do?"),
]

PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>Shelf Life</title><meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
:root{--bg:#0a0d12;--panel:#141a22;--line:#232c38;--dim:#7d8da3;--fg:#e8eef7;
 --grn:#3fb950;--amb:#e3b341;--red:#f85149;--blu:#58a6ff}
body{margin:0;background:var(--bg);color:var(--fg);
 font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:30px 24px 60px}
header{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
h1{font-size:34px;margin:0;letter-spacing:-.03em}
h1 em{font-style:normal;color:var(--dim);font-weight:400;font-size:19px;
 letter-spacing:0}
.sub{color:var(--dim);margin:10px 0 26px;font-size:15px}
.sub b{color:var(--fg);font-weight:600}
.ask{display:flex;gap:10px}
input[type=text]{flex:1;font:inherit;background:var(--panel);color:var(--fg);
 border:1px solid var(--line);border-radius:10px;padding:14px 16px}
input[type=text]:focus{outline:none;border-color:var(--blu)}
button{font:inherit;cursor:pointer;background:var(--panel);color:var(--fg);
 border:1px solid var(--line);border-radius:10px;padding:13px 18px;transition:.15s}
button:hover{border-color:var(--blu);transform:translateY(-1px)}
.go{background:#238636;border-color:#2ea043;color:#fff;padding:13px 30px;font-weight:600}
.row{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin:14px 0 8px}
.row button{font-size:13.5px;color:var(--dim);padding:8px 14px}
.spacer{margin-left:auto}
.tiny{font-size:12px;color:var(--dim)}

/* live pipeline */
.pipe{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0 4px;min-height:34px}
.leg{display:flex;align-items:center;gap:9px;background:var(--panel);
 border:1px solid var(--line);border-radius:999px;padding:6px 15px;font-size:13px;
 color:var(--dim);opacity:.45;transition:.3s}
.leg.on{opacity:1}
.leg.done{opacity:1;border-color:#2d4a35}
.leg .dot{width:8px;height:8px;border-radius:50%;background:var(--dim)}
.leg.on .dot{background:var(--amb);animation:pulse 1s infinite}
.leg.done .dot{background:var(--grn);animation:none}
.leg b{color:var(--fg);font-weight:600}
.leg .ms{font:12px ui-monospace,Menlo,monospace;color:var(--grn)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.quip{color:var(--dim);font-size:14px;font-style:italic;margin:10px 0 0;min-height:22px}

/* verdict */
.verdict{border-radius:14px;padding:22px 26px;margin:22px 0 18px;border:1px solid;
 animation:pop .35s ease}
@keyframes pop{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.verdict .lvl{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;
 font-weight:800;margin-bottom:8px;opacity:.9}
.verdict .big{font-size:20px;font-weight:600}
.verdict .sig{font-size:14.5px;margin-top:11px;opacity:.92}
.verdict .trace{margin-top:13px;padding-top:11px;
 border-top:1px solid rgba(255,255,255,.14);
 font:12.5px/1.55 ui-monospace,Menlo,monospace;opacity:.72}
.good{background:#0d2818;border-color:#2ea043;color:#7ee787}
.stale,.unproven{background:#2b2411;border-color:#bb8009;color:var(--amb)}
.superseded{background:#2d1214;border-color:var(--red);color:#ff9b95}
.none{background:var(--panel);border-color:var(--line);color:var(--dim)}

.cols{display:grid;gap:16px;grid-template-columns:1fr 1fr}
@media(max-width:840px){.cols{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;
 padding:20px 22px}
.card h3{margin:0;font-size:13px;letter-spacing:.09em;text-transform:uppercase;
 display:flex;align-items:center;gap:9px}
.card .sub2{font-size:12px;color:var(--dim);margin:5px 0 14px}
.docs h3{color:var(--blu)} .chan h3{color:var(--grn)}
.silent{border-color:#7a5a10} .silent h3{color:var(--amb)}
.ans{white-space:pre-wrap}

/* people */
.who{margin-top:18px;background:var(--panel);border:1px solid var(--line);
 border-radius:14px;padding:19px 22px}
.who h3{margin:0 0 14px;font-size:12px;letter-spacing:.11em;text-transform:uppercase;
 color:var(--dim)}
.p{display:inline-flex;align-items:center;gap:12px;background:#1b2430;
 border:1px solid var(--line);border-radius:12px;padding:10px 16px 10px 10px;
 margin:0 10px 10px 0}
.av{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;
 font-weight:700;font-size:15px;color:#0a0d12;letter-spacing:-.5px}
.p b{display:block;font-size:15px}
.p i{font-style:normal;color:var(--dim);font-size:12.5px}

/* evidence */
.ev{margin-top:18px}
.ev h3{font-size:12px;letter-spacing:.11em;text-transform:uppercase;color:var(--dim);
 margin:0 0 12px}
.msg{background:var(--panel);border-left:3px solid var(--line);
 border-radius:0 10px 10px 0;padding:13px 17px;margin-bottom:10px;font-size:14.5px;
 display:flex;gap:13px}
.msg.u{border-left-color:var(--amb)} .msg.s{border-left-color:var(--red)}
.msg .av{width:32px;height:32px;font-size:12.5px;flex:0 0 32px}
.msg .m{color:var(--dim);font-size:12.5px;margin-bottom:3px}
.flag{font-size:12.5px;margin-top:6px;color:var(--amb)}
.flag.s{color:#ff9b95}

/* post-an-update panel */
.post{margin:22px 0 0;background:var(--panel);border:1px dashed #3a4757;
 border-radius:14px;padding:18px 22px}
.post h3{margin:0 0 6px;font-size:12px;letter-spacing:.11em;text-transform:uppercase;
 color:var(--dim)}
.post .t{color:var(--dim);font-size:14px;margin-bottom:13px}
.post textarea{width:100%;background:#0f151d;color:var(--fg);border:1px solid var(--line);
 border-radius:10px;padding:12px 14px;font:14px/1.55 inherit;resize:vertical;min-height:74px}
.post .b{display:flex;gap:10px;margin-top:11px;align-items:center}
.send{background:#8957e5;border-color:#a371f7;color:#fff;font-weight:600}
.ok{color:var(--grn);font-size:13.5px}

.foot{margin-top:38px;display:flex;align-items:center;gap:18px;color:var(--dim);
 border-top:1px solid var(--line);padding-top:22px}
.foot img{width:78px;height:78px;background:#fff;padding:5px;border-radius:9px}
.foot b{color:var(--fg);font-size:16px}
.muted{color:var(--dim);padding:26px 0}
.chan{color:var(--blu);text-decoration:none;font-size:13.5px;padding:8px 14px;
 border:1px solid var(--line);border-radius:10px;transition:.15s}
.chan:hover{border-color:var(--blu)}
.think{display:flex;align-items:center;gap:10px;color:var(--dim);font-style:italic}
.think .dot{width:9px;height:9px;border-radius:50%;background:var(--amb);
 animation:pulse 1s infinite}
</style></head><body><div class=wrap>
<header><h1>Shelf&nbsp;Life</h1><em>every answer in a company has one</em></header>
<p class=sub><b>What the docs say</b> &middot; <b>what the team found</b> &middot;
 <b>how much to trust it</b> &middot; <b>who to ask</b></p>

<div class=ask>
 <input type=text id=q value="Our SFTP export connector won't connect but the credentials are correct. What is wrong?"
   onkeydown="if(event.key=='Enter')go()">
 <button class=go onclick=go()>Ask</button>
</div>
<div class=row>__PRESETS__
 <a href="/chat" target="_blank" class=chan>#voice-eng &rarr;</a>
 <label class="tiny spacer"><input type=checkbox id=off style="vertical-align:middle"> offline</label>
</div>

<div class=pipe id=pipe></div>
<div class=quip id=quip></div>
<div id=out class=muted>Ask something.</div>

<div class=foot><div><b>shelflife.ringamo.dev</b>
 <span class=tiny>&nbsp;&nbsp;cognee &middot; qdrant &middot; live now</span></div></div>
</div><script>
const COLORS={};
const PALETTE=['#58a6ff','#3fb950','#e3b341','#f778ba','#a371f7','#ff9b95'];
function av(name){
 if(!(name in COLORS)) COLORS[name]=PALETTE[Object.keys(COLORS).length%PALETTE.length];
 const i=name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase();
 return '<span class=av style="background:'+COLORS[name]+'">'+i+'</span>';
}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function preset(t){document.getElementById('q').value=t;go()}

const QUIPS=["reading 14 months of scrollback\\u2026","asking the docs, politely\\u2026",
 "cognee is building the graph\\u2026","this is the part where it thinks\\u2026",
 "come on\\u2026","still going \\u2014 it is reading a whole thread, not a chunk\\u2026",
 "any second now\\u2026","worth the wait, promise\\u2026"];
let quipTimer=null,t0=0;

function legs(state){
 const L=[['Qdrant','32 messages'],['Cognee \\u00b7 docs','8 pages'],
          ['Cognee \\u00b7 #voice-eng','8 threads']];
 document.getElementById('pipe').innerHTML=L.map((l,i)=>
  '<span class="leg '+(state[i]||'')+'"><span class=dot></span><b>'+l[0]+'</b> '+
  l[1]+(window.MS&&window.MS[i]!=null?' <span class=ms>'+window.MS[i]+'ms</span>':'')+
  '</span>').join('');
}

async function go(){
 const out=document.getElementById('out'), quip=document.getElementById('quip');
 const body=JSON.stringify({question:document.getElementById('q').value,
   offline:document.getElementById('off').checked});
 out.className='';out.innerHTML='';
 window.MS=[null,null,null];legs(['on','','']);
 t0=Date.now();clearInterval(quipTimer);
 quip.textContent='asking Qdrant for the evidence\u2026';

 // Fast path: the verdict needs no LLM, so it lands in ~150ms.
 const vr=await fetch('/verdict',{method:'POST',
   headers:{'Content-Type':'application/json'},body:body});
 const v=await vr.json();
 window.MS[0]=(v.timing||{}).qdrant_ms;
 legs(['done','on','on']);
 out.innerHTML=render(v.trust,null);
 quip.textContent='verdict in '+((Date.now()-t0)/1000).toFixed(2)+
   's \u2014 now cognee reads the whole thread\u2026';

 let n=0;
 quipTimer=setInterval(()=>{n++;quip.textContent=QUIPS[Math.min(n,QUIPS.length-1)]+
   '   ('+((Date.now()-t0)/1000).toFixed(1)+'s)';},2200);

 // Slow path: two graph completions, in parallel.
 const r=await fetch('/ask',{method:'POST',
   headers:{'Content-Type':'application/json'},body:body});
 const d=await r.json();
 clearInterval(quipTimer);
 const tm=d.timing||{};
 window.MS=[tm.qdrant_ms||window.MS[0],tm.cognee_docs_ms,tm.cognee_channel_ms];
 legs(['done','done','done']);
 quip.textContent=d.cached?'served from cache':
   'verdict 0.1s \u00b7 distilled answers '+((Date.now()-t0)/1000).toFixed(1)+'s';
 out.innerHTML=render(d.trust,d);
}

function render(t,d){
 let h='<div class="verdict '+t.level+'"><div class=lvl>'+esc(t.level)+'</div>'+
  '<div class=big>'+esc(t.headline)+'</div>'+
  (t.signals.length?'<div class=sig>'+t.signals.map(esc).join('<br>')+'</div>':'')+
  (t.trace?'<div class=trace>'+esc(t.trace)+'</div>':'')+'</div>';
 const think='<div class=think><span class=dot></span>cognee is reading the thread\u2026</div>';
 h+='<div class=cols>'+
  '<div class="card docs'+(d&&d.docs.silent?' silent':'')+'"><h3>Official documentation</h3>'+
   '<div class=sub2>'+(d?(d.docs.silent?'does not cover this':'authoritative, versioned'):'&nbsp;')+'</div>'+
   '<div class=ans>'+(d?esc(d.docs.answer):think)+'</div></div>'+
  '<div class="card chan"><h3>What the team found</h3>'+
   '<div class=sub2>#voice-eng &middot; practitioner experience</div>'+
   '<div class=ans>'+(d?esc(d.channel.answer):think)+'</div></div></div>';
 if(t.ask&&t.ask.length)
  h+='<div class=who><h3>Who to ask</h3>'+t.ask.map(p=>'<span class=p>'+av(p.name)+
   '<span><b>'+esc(p.name)+'</b><i>'+esc(p.title)+' &middot; '+p.n+' message'+
   (p.n>1?'s':'')+', latest '+esc(p.latest)+'</i></span></span>').join('')+'</div>';
 if(t.evidence&&t.evidence.length)
  h+='<div class=ev><h3>The messages this verdict is computed from</h3>'+
   t.evidence.map(e=>'<div class="msg'+(e.unproven?' u':'')+(e.supersedes?' s':'')+'">'+
   av(e.author)+'<div><div class=m>'+esc(e.author)+' &middot; '+esc(e.date)+'</div>'+
   esc(e.text)+
   (e.unproven?'<div class=flag>\u26a0 the author flagged this as unproven</div>':'')+
   (e.supersedes?'<div class="flag s">\u26a0 this overturns an earlier answer</div>':'')+
   '</div></div>').join('')+'</div>';
 return h;
}

async function post(){
 const el=document.getElementById('posted');el.textContent='posting\\u2026';
 await fetch('/inject',{method:'POST'});
 el.textContent='\\u2713 posted to #voice-eng \\u2014 now ask again';
}
async function undo(){
 const el=document.getElementById('posted');
 await fetch('/reset',{method:'POST'});
 el.textContent='\\u21a9 removed';
}
legs(['','','']);
</script></body></html>"""
