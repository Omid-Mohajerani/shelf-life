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
:root{--bg:#f6f8fa;--panel:#ffffff;--line:#d8dee4;--dim:#57606a;--fg:#1f2328;
 --grn:#1a7f37;--amb:#9a6700;--red:#cf222e;--blu:#0969da}
body{margin:0;background:var(--bg);color:var(--fg);
 font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:30px 24px 60px}
header{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
header .chan{margin-left:auto}
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
.go{background:#1f883d;border-color:#1a7f37;color:#fff;padding:13px 30px;font-weight:600}
.off{display:block;margin:12px 0 0;text-align:right}
.tiny{font-size:12px;color:var(--dim)}

/* live pipeline */
.pipe{margin:22px 0 0}
.pipe.busy{background:var(--panel);border:1px solid var(--line);border-radius:14px;
 padding:20px 24px;box-shadow:0 1px 2px rgba(31,35,40,.05)}
.leg{display:flex;align-items:center;gap:14px;padding:9px 0;font-size:14.5px;
 color:var(--dim);opacity:.4;transition:opacity .35s}
.leg.on,.leg.done{opacity:1}
.leg .mark{width:26px;height:26px;border-radius:7px;display:grid;place-items:center;
 font:800 10.5px/1 ui-sans-serif;color:#fff;letter-spacing:-.3px;flex:0 0 26px}
.leg.q .mark{background:#b02a37}
.leg.c .mark{background:#6f42c1}
.leg .nm{font-weight:600;color:var(--fg);min-width:186px}
.leg .st{flex:1}
.leg .ms{font:12.5px ui-monospace,Menlo,monospace;color:var(--grn);font-weight:600}
.spin{width:15px;height:15px;border-radius:50%;border:2px solid var(--line);
 border-top-color:var(--blu);animation:spin .7s linear infinite}
.tick{color:var(--grn);font-size:16px;font-weight:700}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.quip{color:var(--dim);font-size:14.5px;font-style:italic;margin:14px 0 0;
 padding-top:14px;border-top:1px solid var(--line);min-height:22px}

/* verdict */
.verdict{border-radius:14px;padding:22px 26px;margin:22px 0 18px;border:1px solid;
 animation:pop .35s ease}
@keyframes pop{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.verdict .lvl{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;
 font-weight:800;opacity:.9}
.vhead{display:flex;align-items:center;gap:14px;margin-bottom:9px;flex-wrap:wrap}
.badge{margin-left:auto;font:11.5px ui-monospace,Menlo,monospace;
 border:1px solid currentColor;border-radius:999px;padding:3px 11px;opacity:.7}
.verdict .big{font-size:20px;font-weight:600}
.verdict .sig{font-size:14.5px;margin-top:11px;opacity:.92}
.verdict .trace{margin-top:13px;padding-top:11px;
 border-top:1px solid rgba(0,0,0,.14);
 font:12.5px/1.55 ui-monospace,Menlo,monospace;opacity:.72}
.good{background:#e8f6ec;border-color:#2da44e;color:#0f5323}
.stale,.unproven{background:#fff8e6;border-color:#d4a72c;color:#7a4f01}
.superseded{background:#ffebe9;border-color:#cf222e;color:#8b1a24}
.none{background:var(--panel);border-color:var(--line);color:var(--dim)}

.cols{display:grid;gap:16px;grid-template-columns:1fr 1fr}
@media(max-width:840px){.cols{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;
 padding:20px 22px;box-shadow:0 1px 2px rgba(31,35,40,.05)}
.card h3{margin:0;font-size:13px;letter-spacing:.09em;text-transform:uppercase;
 display:flex;align-items:center;gap:9px}
.card .sub2{font-size:12px;color:var(--dim);margin:5px 0 14px}
.docs h3{color:var(--blu)} .chan h3{color:var(--grn)}
.silent{border-color:#d4a72c;background:#fffdf5} .silent h3{color:#7a4f01}
.ans{white-space:pre-wrap;color:var(--fg)}

/* people */
.who{margin-top:18px;background:var(--panel);border:1px solid var(--line);
 border-radius:14px;padding:19px 22px}
.who h3{margin:0 0 14px;font-size:12px;letter-spacing:.11em;text-transform:uppercase;
 color:var(--dim)}
.p{display:inline-flex;align-items:center;gap:12px;background:#f6f8fa;
 border:1px solid var(--line);border-radius:12px;padding:10px 16px 10px 10px;
 margin:0 10px 10px 0}
.av{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;
 font-weight:700;font-size:15px;color:#fff;letter-spacing:-.5px}
.p b{display:block;font-size:15px}
.p i{font-style:normal;color:var(--dim);font-size:12.5px}

/* evidence */
.ev{margin-top:18px}
.ev h3{font-size:12px;letter-spacing:.11em;text-transform:uppercase;color:var(--dim);
 margin:0 0 12px}
.msg{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--line);
 border-radius:0 10px 10px 0;padding:13px 17px;margin-bottom:10px;font-size:14.5px;
 display:flex;gap:13px}
.msg.u{border-left-color:var(--amb)} .msg.s{border-left-color:var(--red)}
.msg .av{width:32px;height:32px;font-size:12.5px;flex:0 0 32px}
.msg .m{color:var(--dim);font-size:12.5px;margin-bottom:3px}
.flag{font-size:12.5px;margin-top:6px;color:var(--amb)}
.flag.s{color:var(--red)}

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
.chan{color:var(--blu);text-decoration:none;font-size:13.5px;padding:7px 13px;
 border:1px solid var(--line);border-radius:9px;transition:.15s;background:var(--panel)}
.chan:hover{border-color:var(--blu)}
.think{display:flex;align-items:center;gap:10px;color:var(--dim);font-style:italic}
.think .dot{width:9px;height:9px;border-radius:50%;background:var(--amb);
 animation:pulse 1s infinite}
</style></head><body><div class=wrap>
<header><h1>Shelf&nbsp;Life</h1><em>every answer in a company has one</em>
 <a class=chan href="/chat" target="_blank">#voice-eng &rarr;</a></header>
<p class=sub><b>What the docs say</b> &middot; <b>what the team found</b> &middot;
 <b>how much to trust it</b> &middot; <b>who to ask</b></p>

<div class=ask>
 <input type=text id=q value="Our SFTP export connector won't connect but the credentials are correct. What is wrong?"
   onkeydown="if(event.key=='Enter')go()">
 <button class=go onclick=go()>Ask</button>
</div>
<label class="tiny off"><input type=checkbox id=off style="vertical-align:middle"> offline</label>

<div class=pipe id=pipe></div>
<div id=out class=muted>Ask something.</div>

<div class=foot><div><b>shelflife.ringamo.dev</b>
 <span class=tiny>&nbsp;&nbsp;cognee &middot; qdrant &middot; live now</span></div></div>
</div><script>
const COLORS={};
const PALETTE=['#0969da','#1a7f37','#9a6700','#bf3989','#8250df','#cf222e'];
function av(name){
 if(!(name in COLORS)) COLORS[name]=PALETTE[Object.keys(COLORS).length%PALETTE.length];
 const i=name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase();
 return '<span class=av style="background:'+COLORS[name]+'">'+i+'</span>';
}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
// The models answer in markdown. Render the bold rather than printing asterisks,
// and drop the source tag we put in the ingested text.
function md(s){return esc(s).replace(/[*][*](.+?)[*][*]/g,'<b>$1</b>')
 .replace(/[[]OFFICIAL DOCUMENTATION[\]]\s*/g,'').replace(/[[]TEAM CHANNEL[^\]]*[\]]\s*/g,'')}
function preset(t){document.getElementById('q').value=t;go()}

const QUIPS=["reading 14 months of scrollback\\u2026","asking the docs, politely\\u2026",
 "cognee is building the graph\\u2026","this is the part where it thinks\\u2026",
 "come on\\u2026","still going \\u2014 it is reading a whole thread, not a chunk\\u2026",
 "any second now\\u2026","worth the wait, promise\\u2026"];
let quipTimer=null,t0=0;

function legs(state,busy){
 const L=[['q','QD','Qdrant','scanning 32 messages for the evidence'],
          ['c','CG','cognee \u00b7 docs','reading 8 pages of official documentation'],
          ['c','CG','cognee \u00b7 #voice-eng','reading 8 threads, 14 months of channel']];
 const p=document.getElementById('pipe');
 p.className='pipe'+(busy?' busy':'');
 p.innerHTML=L.map((l,i)=>{
  const st=state[i]||'', ms=window.MS&&window.MS[i]!=null?window.MS[i]:null;
  const right = st=='done'&&ms!=null ? '<span class=ms>'+ms+'ms</span>'
              : st=='done' ? '<span class=tick>\u2713</span>'
              : st=='on'   ? '<span class=spin></span>' : '';
  return '<div class="leg '+l[0]+' '+st+'"><span class=mark>'+l[1]+'</span>'+
   '<span class=nm>'+l[2]+'</span><span class=st>'+l[3]+'</span>'+right+'</div>';
 }).join('')+(busy?'<div class=quip id=quip></div>':'');
}

async function go(){
 const out=document.getElementById('out');
 const Q=()=>document.getElementById('quip');
 const body=JSON.stringify({question:document.getElementById('q').value,
   offline:document.getElementById('off').checked});
 out.className='';out.innerHTML='';
 window.MS=[null,null,null];legs(['on','on','on'],true);
 t0=Date.now();clearInterval(quipTimer);
 (Q()||{}).textContent='asking Qdrant for the evidence\u2026';

 // Fast path: the verdict needs no LLM, so it lands in ~150ms.
 const vr=await fetch('/verdict',{method:'POST',
   headers:{'Content-Type':'application/json'},body:body});
 const v=await vr.json();
 window.MS[0]=(v.timing||{}).qdrant_ms;
 legs(['done','on','on'],true);
 v.trust.qdrant_ms=(v.timing||{}).qdrant_ms;out.innerHTML=render(v.trust,null);
 (Q()||{}).textContent='verdict in '+((Date.now()-t0)/1000).toFixed(2)+
   's \u2014 now cognee reads the whole thread\u2026';

 let n=0;
 quipTimer=setInterval(()=>{n++;(Q()||{}).textContent=QUIPS[Math.min(n,QUIPS.length-1)]+
   '   ('+((Date.now()-t0)/1000).toFixed(1)+'s)';},2200);

 // Slow path: two graph completions, in parallel.
 const r=await fetch('/ask',{method:'POST',
   headers:{'Content-Type':'application/json'},body:body});
 const d=await r.json();
 clearInterval(quipTimer);
 const tm=d.timing||{};
 window.MS=[tm.qdrant_ms||window.MS[0],tm.cognee_docs_ms,tm.cognee_channel_ms];
 legs(['done','done','done'],false);
 (Q()||{}).textContent=d.cached?'served from cache':
   'verdict 0.1s \u00b7 distilled answers '+((Date.now()-t0)/1000).toFixed(1)+'s';
 d.trust.qdrant_ms=(d.timing||{}).qdrant_ms;out.innerHTML=render(d.trust,d);
}

function render(t,d){
 let h='<div class="verdict '+t.level+'">'+
  '<div class=vhead><span class=lvl>'+esc(t.level)+'</span>'+
  '<span class=badge>computed from the messages in '+
  (((t.qdrant_ms!=null?t.qdrant_ms:100)/1000).toFixed(2))+'s \u00b7 no LLM</span></div>'+
  '<div class=big>'+esc(t.headline)+'</div>'+
  (t.signals.length?'<div class=sig>'+t.signals.map(esc).join('<br>')+'</div>':'')+
  (t.trace?'<div class=trace>'+esc(t.trace)+'</div>':'')+'</div>';
 const think='<div class=think><span class=dot></span>cognee is reading the whole thread'+
  ' \u2014 this part needs a model\u2026</div>';
 h+='<div class=cols>'+
  '<div class="card docs'+(d&&d.docs.silent?' silent':'')+'"><h3>Official documentation</h3>'+
   '<div class=sub2>'+(d?(d.docs.silent?'does not cover this':'authoritative, versioned'):'&nbsp;')+'</div>'+
   '<div class=ans>'+(d?md(d.docs.answer):think)+'</div></div>'+
  '<div class="card chan"><h3>What the team found</h3>'+
   '<div class=sub2>#voice-eng &middot; practitioner experience</div>'+
   '<div class=ans>'+(d?md(d.channel.answer):think)+'</div></div></div>';
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
legs(['','',''],false);
// ?q=... prefills and asks straight away, so each demo question can live in its
// own tab instead of a row of buttons.
(function(){
 const q=new URLSearchParams(location.search).get('q');
 if(q){document.getElementById('q').value=q;go();}
})();
</script></body></html>"""
