/* Local teaching controls. This player never calls a platform API or a model. */
(function(){
 'use strict';
 const root=document.documentElement, lang=()=>root.lang==='en'?1:0;
 const text=(fa,en)=>lang()?en:fa;
 const pair=(a,b)=>{const f=document.createElement('span');f.className='fa';f.textContent=a;const e=document.createElement('span');e.className='en';e.textContent=b;return [f,e]};
 const nodes=[
  ['developer','Developer','app + input','#ffcfb8'],['api','API & Policy','tenant + scope','#c3ceff'],
  ['store','Run Store','durable state','#d3c3f2'],['runtime','Runtime','step + owner','#d3c3f2'],
  ['gateway','Model Gateway','budget + route','#ffe08a'],['provider','Model','proposed output','#ffe08a'],
  ['tools','Tool Gateway','validate + authorize','#bfe6c9'],['data','Context / Tools','scoped evidence','#bfe6c9']
 ];
 const steps=[
  ['developer','api','ADR-001','توسعه‌دهنده یک run می‌خواهد','A developer requests a run','نیاز را از اینجا می‌گیریم: یک app، یک ورودی و یک نتیجهٔ قابل‌پیگیری. هنوز هیچ سرویسی در این نمایش اجرا نمی‌شود.','Start from a need: an app, an input, and a traceable result. This illustration runs no services.'],
  ['api','store','ADR-004','پذیرش باید پایدار باشد','Admission must be durable','API هویت، scope و کلید idempotency را بررسی می‌کند؛ run باید پیش از پاسخِ پذیرش commit شود. چرا؟ چون پاسخ ممکن است گم شود.','Validate identity, scope, and idempotency; commit the run before acknowledging it, because responses can be lost.'],
  ['store','runtime','ADR-005','یک worker، مالک اجرای step می‌شود','A worker takes step ownership','Runtime از وضعیت پایدار ادامه می‌دهد. claim و epoch باید جلوی commit مالک قدیمی را بگیرند؛ یک فلش در شکل این تضمین را پیاده نمی‌کند.','Resume from durable state. Claims/epochs must reject stale commits; an arrow does not implement that guarantee.'],
  ['runtime','gateway','ADR-008','درخواست مدل از دروازه می‌گذرد','Inference passes through the gateway','به‌جای پخش کلید provider در appها، budget، deadline، مدل و trace را در یک مرز کنترل می‌کنیم. این انتخاب هنوز پیشنهادی است.','Keep credentials out of apps and centralize budgets, deadlines, model routing, and tracing. This remains a proposal.'],
  ['gateway','provider','ADR-003','حالا نوبت inference است','Inference is dispatched','برای اولین token مفید می‌توانیم فرضِ ۳ ثانیه را آزمایش کنیم. حرکتِ این نشان زمانِ واقعیِ provider یا نتیجهٔ benchmark نیست.','Test the proposed three-second useful-first-token goal. Marker movement is not provider latency or benchmark evidence.'],
  ['provider','gateway','ADR-009','خروجی مدل، مجوز اجرا نیست','Model output is not authority','ممکن است مدل tool call پیشنهاد کند؛ متنِ مدل به‌تنهایی اجازهٔ خواندن داده یا اجرای عملیات نمی‌دهد.','The model may propose a tool call; its text alone grants no data access or execution authority.'],
  ['gateway','runtime','ADR-005','خروجی مدل در یک step ثبت می‌شود','Persist the model step','اگر پس از دریافت خروجی crash کنیم، replay باید از نتیجهٔ ثبت‌شده ادامه دهد؛ call مجدد مدل ممکن است نتیجهٔ دیگری بدهد.','After a crash, replay should use recorded output; a fresh model call can produce a different result.'],
  ['runtime','tools','ADR-009','ابزار پیشنهادی اعتبارسنجی می‌شود','Validate the proposed tool call','Tool Gateway schema، tenant، مجوز فعلی و limit را بررسی می‌کند. نسخهٔ اول ابزار خواندنی دارد؛ اثر بیرونی قرارداد جدا می‌خواهد.','Check schema, tenant, current permissions, and limits. Start with reads; side effects require additional contracts.'],
  ['tools','data','ADR-007','دادهٔ مجاز بازیابی می‌شود','Retrieve authorized evidence','برای دادهٔ متنی baseline جست‌وجو می‌خواهیم؛ برای telemetry، ابزار query. لازم نیست همهٔ داده‌ها را embedding کنیم.','Use a retrieval baseline for text and query tools for telemetry; not all data needs embeddings.'],
  ['data','tools','ADR-010','شواهد باید نسخه و منبع داشته باشند','Evidence needs provenance','نتیجه با source، revision و بازهٔ زمانی برمی‌گردد. سند حذف‌شده یا context با ACL قدیمی نباید دوباره قابل‌خواندن شود.','Return source, revision, and time interval; deleted documents or revoked context must not become readable again.'],
  ['tools','runtime','ADR-005','نتیجه به اجرای پایدار برمی‌گردد','Return to durable execution','step بعدی تنها پس از ثبت نتیجه و بررسی مالکیت شروع می‌شود. اگر شواهد کافی نباشد، پاسخِ نامطمئن هم می‌تواند خروجی درست باشد.','Persist results and check ownership before the next step; insufficient evidence can be a correct outcome.'],
  ['runtime','store','ADR-011','نتیجه و trace برای بررسی می‌مانند','Keep results and traces inspectable','نتیجهٔ مجاز را ذخیره می‌کنیم و توسعه‌دهنده از API می‌خواند. کیفیتِ نسخه با eval جدا سنجیده می‌شود؛ رسیدن نشان به آخر، اثباتِ پیاده‌سازی نیست.','Persist authorized results for API retrieval; evaluate quality separately. Finishing the animation does not prove implementation.']
 ];
 const svg=document.getElementById('platform-flow-svg'), player=document.getElementById('flow-player');
 if(!svg||!player)return;
 const ns='http://www.w3.org/2000/svg';
 const make=(tag,attrs,parent)=>{const el=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));parent.appendChild(el);return el};
 const defs=make('defs',{},svg);const marker=make('marker',{id:'flow-arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto'},defs);make('path',{d:'M0 1L9 5L0 9',fill:'none',stroke:'currentColor','stroke-width':1.5},marker);
 const lines=make('g',{'aria-hidden':'true'},svg), boxes=make('g',{},svg),cursor=make('circle',{r:7,fill:'#6743bc','aria-hidden':'true',visibility:'hidden'},svg);
 let positions={},paths=[],index=0,playing=false,animation=null,timer=null,due=0,remaining=2850,motionEnabled=true;
 const reduce=matchMedia('(prefers-reduced-motion: reduce)');
 const play=player.querySelector('[data-flow-play]'),prev=player.querySelector('[data-flow-prev]'),next=player.querySelector('[data-flow-next]');
 function points(a,b){
  const A=positions[a],B=positions[b];let start,end;
  if(A.x===B.x&&Math.abs(A.y-B.y)>220){const x=210;return [[A.x+A.w,A.y+A.h/2],[x,A.y+A.h/2],[x,B.y+B.h/2],[B.x+B.w,B.y+B.h/2]]}
  if(A.x===B.x){start=[A.x+A.w/2,A.y+(B.y>A.y?A.h:0)];end=[B.x+B.w/2,B.y+(B.y>A.y?0:B.h)];return [start,end]}
  if(A.y===B.y){start=[A.x+(B.x>A.x?A.w:0),A.y+A.h/2];end=[B.x+(B.x>A.x?0:B.w),B.y+B.h/2];return [start,end]}
  // The runtime-to-tool branch has a clear corridor between the compact columns.
  if((a==='runtime'&&b==='tools')||(a==='tools'&&b==='runtime')){const x=210;return [[A.x+A.w,A.y+A.h/2],[x,A.y+A.h/2],[x,B.y+B.h/2],[B.x+B.w,B.y+B.h/2]]}
  start=[A.x+A.w/2,A.y+(B.y>A.y?A.h:0)];end=[B.x+B.w/2,B.y+(B.y>A.y?0:B.h)];return [start,[start[0],(start[1]+end[1])/2],[end[0],(start[1]+end[1])/2],end]
 }
 function pathString(pts){return pts.map((p,i)=>(i?'L':'M')+p.join(' ')).join(' ')}
 function layout(){
  const compact=player.clientWidth<600;
  const desktop=[[30,40],[340,40],[650,40],[340,245],[30,245],[30,450],[650,245],[650,450]];
  const mobile=[[15,35],[230,35],[230,220],[15,220],[15,405],[230,405],[15,590],[230,590]];
  svg.setAttribute('viewBox',compact?'0 0 420 720':'0 0 900 580');positions={};lines.replaceChildren();boxes.replaceChildren();
  nodes.forEach(([id,label,sub,fill],i)=>{const [x,y]=(compact?mobile:desktop)[i],w=compact?175:220,h=90;positions[id]={x,y,w,h};const g=make('g',{'data-flow-node':id},boxes);make('rect',{x,y,width:w,height:h,rx:12,fill,stroke:'#71685e','stroke-width':1.4},g);const t=make('text',{x:x+w/2,y:y+37,'text-anchor':'middle','font-size':compact?18:20,'font-weight':800},g);t.textContent=label;const s=make('text',{x:x+w/2,y:y+65,'text-anchor':'middle','font-size':15},g);s.textContent=sub});
  paths=steps.map(s=>{const pts=points(s[0],s[1]);const el=make('path',{d:pathString(pts),fill:'none',stroke:'#837994','stroke-width':1.7,'marker-end':'url(#flow-arrow)'},lines);return {el,pts}});
  pause();render(false);
 }
 function label(){play.querySelector('[data-flow-play-label]').replaceChildren(...pair(playing?'توقف':'پخش فلو',playing?'Pause':'Play flow'));play.setAttribute('aria-pressed',String(playing));prev.disabled=index===0;next.disabled=index===steps.length-1;const ratio=document.createElement('bdi');ratio.dir='ltr';ratio.textContent=(index+1)+' / '+steps.length;player.querySelector('[data-flow-counter]').replaceChildren(document.createTextNode(text('گام ','Step ')),ratio)}
 function render(animate){
  animation?.cancel();animation=null;cursor.setAttribute('visibility','hidden');remaining=2850;
  const s=steps[index];player.dataset.flowStep=String(index);
  player.querySelector('[data-flow-title]').replaceChildren(...pair(s[3],s[4]));player.querySelector('[data-flow-explanation]').replaceChildren(...pair(s[5],s[6]));const link=player.querySelector('[data-flow-adr]');link.textContent=s[2];link.href='#'+s[2];
  player.querySelector('[data-flow-route]').textContent=nodes.find(n=>n[0]===s[0])[1]+' → '+nodes.find(n=>n[0]===s[1])[1];
  boxes.querySelectorAll('g').forEach(g=>g.classList.toggle('is-active',g.dataset.flowNode===s[1]));
  paths.forEach((p,i)=>{p.el.classList.toggle('is-active',i===index);p.el.style.opacity=i===index?'1':'.32'});lines.appendChild(paths[index].el);label();
  if(animate&&!reduce.matches){
   const pts=paths[index].pts;let total=0;const distances=[0];for(let i=1;i<pts.length;i++){total+=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);distances.push(total)}
   cursor.setAttribute('visibility','visible');animation=cursor.animate(pts.map((p,i)=>({transform:`translate(${p[0]}px, ${p[1]}px)`,offset:distances[i]/total})),{duration:1800,easing:'linear',fill:'forwards'});
  }
 }
 function schedule(ms){clearTimeout(timer);remaining=ms;due=performance.now()+ms;timer=setTimeout(()=>{if(!playing)return;if(index===steps.length-1){pause();return}index++;render(motionEnabled);schedule(2850)},ms)}
 function pause(){if(playing)remaining=Math.max(0,due-performance.now());playing=false;clearTimeout(timer);timer=null;if(animation?.playState==='running')animation.pause();label()}
 function navigate(n,animate){pause();index=Math.max(0,Math.min(steps.length-1,n));render(animate)}
 play.addEventListener('click',e=>{if(playing){pause();return}motionEnabled=e.detail!==0&&!reduce.matches;if(index===steps.length-1){index=0;render(motionEnabled)}else if(animation?.playState==='paused'&&motionEnabled){animation.play()}else if(!animation||!motionEnabled){render(motionEnabled)}document.dispatchEvent(new Event('platform-flow-play'));playing=true;label();schedule(remaining)});
 prev.addEventListener('click',e=>navigate(index-1,e.detail!==0));next.addEventListener('click',e=>navigate(index+1,e.detail!==0));player.querySelector('[data-flow-reset]').addEventListener('click',()=>navigate(0,false));
 document.addEventListener('pov-play',pause);document.addEventListener('visibilitychange',()=>{if(document.hidden)pause()});reduce.addEventListener('change',()=>{pause();render(false)});
 new ResizeObserver(()=>layout()).observe(player.querySelector('.flow-stage'));
 new MutationObserver(label).observe(root,{attributes:true,attributeFilter:['lang']});
 const nav=document.querySelector('.workshop-step-nav'),mobileNav=document.querySelector('.workshop-mobile-nav'),stageSelect=document.getElementById('workshop-stage-select'),lessonControls=document.querySelector('.lesson-controls');let lesson=0;
 nav.hidden=false;mobileNav.hidden=false;lessonControls.hidden=false;
 function lessonLanguage(){const n=v=>v.toLocaleString(lang()?'en-US':'fa-IR');STAGE_LABELS.forEach((labels,i)=>stageSelect.options[i].textContent=text('گام '+n(i+1)+' از ۷','Stage '+n(i+1)+' of 7')+' · '+labels[lang()]);lessonControls.querySelector('[data-workshop-count]').textContent=text('گام '+n(lesson+1)+' از ۷','Stage '+n(lesson+1)+' of 7')}
 const STAGE_LABELS=Array.from(nav.querySelectorAll('button')).map(b=>[b.querySelector('.fa').textContent,b.querySelector('.en').textContent]);
 function select(i){lesson=Math.max(0,Math.min(6,i));document.querySelectorAll('[data-workshop-step]').forEach(el=>el.hidden=Number(el.dataset.workshopStep)!==lesson);nav.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.workshopSelect)===lesson)));stageSelect.value=String(lesson);lessonControls.querySelector('[data-workshop-prev]').disabled=lesson===0;lessonControls.querySelector('[data-workshop-next]').disabled=lesson===6;lessonLanguage()}
 nav.addEventListener('click',e=>{const b=e.target.closest('button');if(b)select(Number(b.dataset.workshopSelect))});stageSelect.addEventListener('change',()=>select(Number(stageSelect.value)));lessonControls.querySelector('[data-workshop-prev]').addEventListener('click',()=>select(lesson-1));lessonControls.querySelector('[data-workshop-next]').addEventListener('click',()=>select(lesson+1));new MutationObserver(lessonLanguage).observe(root,{attributes:true,attributeFilter:['lang']});select(0);
 function revealHash(){if(location.hash!=='#architecture')pause();let el;try{el=document.getElementById(decodeURIComponent(location.hash.slice(1)))}catch{return}if(!el)return;let ancestor=el.closest('details');while(ancestor){ancestor.open=true;ancestor=ancestor.parentElement?.closest('details')}if(location.hash)requestAnimationFrame(()=>el.scrollIntoView({block:'start',behavior:'instant'}))}
 addEventListener('hashchange',revealHash);revealHash();
 const form=document.getElementById('estimate-form'),error=document.getElementById('estimate-error');
 function recalc(e){e?.preventDefault();if(!form.reportValidity())return;const v=Object.fromEntries(new FormData(form));const n={};for(const [k,value]of Object.entries(v)){n[k]=Number(value);if(!Number.isSafeInteger(n[k])||n[k]<1||n[k]>1e9){error.hidden=false;error.textContent=text('همهٔ ورودی‌ها باید عدد صحیح بین ۱ و یک میلیارد باشند.','Use whole numbers from 1 to one billion.');return}}error.hidden=true;const calls=n.runs*n.calls,cost=calls*(n.input/1e6+4*n.output/1e6),seed=n.documents/n.seed,backlog=seed*5,raw=n.documents*4*1536*4;const values={tokens:(calls*(n.input+n.output)).toLocaleString(lang()?'en-US':'fa-IR'),cost:'$'+cost.toFixed(2),month:'$'+(cost*30).toFixed(2),vectors:(raw/1e9).toFixed(3)+' GB',generations:(raw*3/1e9).toFixed(3)+' GB',snapshot:(seed/3600).toFixed(3)+' h',backlog:Math.ceil(backlog).toLocaleString(lang()?'en-US':'fa-IR'),catchup:(backlog/25/60).toFixed(3)+' min'};Object.entries(values).forEach(([key,value])=>document.getElementById('estimate-'+key).textContent=value)}
 form.addEventListener('submit',recalc);new MutationObserver(()=>recalc()).observe(root,{attributes:true,attributeFilter:['lang']});recalc();layout();
})();
