const assert=require('assert/strict'),fs=require('fs');
const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch({headless:true,...(process.env.PW_CHANNEL==='chromium'?{}:{channel:process.env.PW_CHANNEL||'chrome'})}),folder=process.cwd()+'/.impeccable/review/platform-recovery-finish';fs.mkdirSync(folder,{recursive:true});const report=[];
 for(const [name,width,lang,theme,reduce]of [['desktop-fa',1440,'fa','light',false],['mobile-fa',390,'fa','light',false],['desktop-en-dark',1440,'en','dark',false],['mobile-reduced',390,'fa','light',true],['tablet-fa',768,'fa','light',false],['mobile-en',390,'en','light',false]]){
  const c=await b.newContext({viewport:{width,height:960},reducedMotion:reduce?'reduce':'no-preference'}),p=await c.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));await p.addInitScript(({lang,theme})=>{localStorage.setItem('ddia-lang',lang);localStorage.setItem('ddia-theme',theme)},{lang,theme});await p.goto((process.env.BASE_URL||'http://127.0.0.1:8766')+'/final-project/index.html#start-here');await p.evaluate(()=>document.fonts.ready);
  assert.equal(await p.locator('#design-reference').getAttribute('open'),null);assert.equal(await p.locator('[data-workshop-step]:visible').count(),1);assert.equal(await p.locator('#estimate-cost').innerText(),'$2.80');assert.equal(await p.locator('#estimate-vectors').innerText(),'24.576 GB');assert.equal(await p.locator('.adr-record').count(),15);
  if(width<=700)await p.locator('#workshop-stage-select').selectOption('4');else await p.locator('[data-workshop-select="4"]').click();assert.equal(await p.locator('[data-workshop-step="4"]').isVisible(),true);
  await p.locator('[data-workshop-next]').click();assert.equal(await p.locator('[data-workshop-step="5"]').isVisible(),true);await p.locator('[data-workshop-prev]').click();assert.equal(await p.locator('[data-workshop-step="4"]').isVisible(),true);
  assert.equal(await p.locator('.equation').first().evaluate(e=>getComputedStyle(e).direction),'ltr');
  await p.locator('[name="runs"]').fill('200');await p.locator('#estimate-form button').click();assert.equal(await p.locator('#estimate-cost').innerText(),'$5.60');
  await p.locator('#architecture').scrollIntoViewIfNeeded();assert.equal(await p.locator('#flow-player').getAttribute('data-flow-step'),'0');assert.equal(await p.locator('#platform-flow-svg circle').getAttribute('visibility'),'hidden');
  await p.locator('[data-flow-play]').click();assert.equal(await p.locator('[data-flow-play]').getAttribute('aria-pressed'),'true');
  if(reduce)assert.equal(await p.locator('#platform-flow-svg circle').getAttribute('visibility'),'hidden');else{
   await p.waitForFunction(()=>document.querySelector('#platform-flow-svg circle').getAnimations()[0]?.currentTime>100);
   await p.locator('[data-flow-play]').click();const t=await p.locator('#platform-flow-svg circle').evaluate(async e=>{const a=e.getAnimations()[0];await a.ready;return a.currentTime});await p.waitForTimeout(160);const t2=await p.locator('#platform-flow-svg circle').evaluate(e=>e.getAnimations()[0].currentTime);assert(Math.abs(t2-t)<5,'Pause must freeze the marker');
  }
  await p.locator('[data-flow-next]').click();assert.equal(await p.locator('#flow-player').getAttribute('data-flow-step'),'1');await p.locator('[data-flow-prev]').click();assert.equal(await p.locator('#flow-player').getAttribute('data-flow-step'),'0');
  await p.locator('[data-flow-next]').focus();await p.keyboard.press('Enter');assert.equal(await p.locator('#platform-flow-svg circle').getAttribute('visibility'),'hidden','Keyboard step is instant');
  await p.locator('[data-flow-reset]').click();assert.equal(await p.locator('#flow-player').getAttribute('data-flow-step'),'0');
  await p.screenshot({path:folder+'/'+name+'-flow.png'});
  if(width<=700)await p.locator('#workshop-stage-select').selectOption('0');else await p.locator('[data-workshop-select="0"]').click();await p.locator('#start-here').scrollIntoViewIfNeeded();await p.screenshot({path:folder+'/'+name+'-workshop.png'});await p.locator('#estimates').scrollIntoViewIfNeeded();await p.screenshot({path:folder+'/'+name+'-estimates.png'});
  await p.locator('[name="runs"]').fill('100');await p.locator('#estimate-form button').click();
  for(const [id,suffix] of [['overview','overview'],['company-evidence','companies'],['I03','report-open'],['start-here','workshop'],['estimates','estimates'],['decisions','decisions'],['ADR-003','adr003'],['architecture','flow']]){await p.evaluate(id=>{const el=document.getElementById(id);if(el.tagName==='DETAILS')el.open=true;el.scrollIntoView({block:'start',behavior:'instant'})},id);await p.screenshot({path:folder+'/'+name+'-'+suffix+'.png'});}
  for(const [selector,suffix] of [['.project-problems','problems'],['.project-scope','scope']]){await p.locator(selector).evaluate(e=>e.scrollIntoView({block:'start',behavior:'instant'}));await p.screenshot({path:folder+'/'+name+'-'+suffix+'.png'});}
  assert.equal(await p.locator('.interview-record').count(),8);assert.equal(await p.locator('[data-evidence="official"]').count(),1);
  await p.locator('#recovery').evaluate(e=>e.scrollIntoView({block:'start',behavior:'instant'}));await p.screenshot({path:folder+'/'+name+'-recovery.png'});
  await p.locator('#R02').evaluate(e=>{e.open=true;e.scrollIntoView({block:'start',behavior:'instant'})});await p.screenshot({path:folder+'/'+name+'-recovery-open.png'});
  await p.locator('#outcome').evaluate(e=>e.scrollIntoView({block:'start',behavior:'instant'}));await p.screenshot({path:folder+'/'+name+'-outcome.png'});
  assert.equal(await p.locator('#pov-player').getAttribute('data-pov-step'),'0');assert.equal(await p.locator('[data-pov-play]').getAttribute('aria-pressed'),'false');
  await p.locator('#pov-player').scrollIntoViewIfNeeded();await p.screenshot({path:folder+'/'+name+'-pov.png'});
  await p.locator('[data-pov-play]').click();assert.equal(await p.locator('[data-pov-play]').getAttribute('aria-pressed'),'true');await p.locator('[data-pov-play]').click();assert.equal(await p.locator('[data-pov-play]').getAttribute('aria-pressed'),'false');
  if(width<=700)await p.locator('#pov-stage-select').selectOption('3');else await p.locator('[data-pov-select="3"]').click();
  assert.equal(await p.locator('#pov-player').getAttribute('data-pov-step'),'3');await p.locator('[data-pov-scene="3"]').evaluate(e=>Promise.all(e.getAnimations().map(a=>a.finished)));await p.screenshot({path:folder+'/'+name+'-pov-interrupted.png'});
  await p.locator('[data-pov-next]').focus();await p.keyboard.press('Enter');assert.equal(await p.locator('#pov-player').getAttribute('data-pov-step'),'4');assert.equal(await p.locator('[data-pov-scene="4"]').evaluate(e=>e.getAnimations().length),0);
  await p.locator('[data-pov-reset]').click();assert.equal(await p.locator('#pov-player').getAttribute('data-pov-step'),'0');
  const proof=await p.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,lang:document.documentElement.lang,dir:document.documentElement.dir,svgNodes:document.querySelectorAll('[data-flow-node]').length}));assert.equal(proof.width,proof.scrollWidth);assert.equal(proof.svgNodes,8);assert.deepEqual(errors,[]);
  await p.evaluate(()=>location.hash='chapter-8');await p.waitForFunction(()=>document.querySelector('#design-reference').open&&document.querySelector('#chapter-8').open);assert(await p.locator('#chapter-8').isVisible());
  report.push({name,...proof,errors,checks:['draft closed by default','guided lesson navigation','15 ADRs','estimates recalculated','play/pause/step/reset','reduced motion or keyboard instant','reference deep links','recovery contracts','POV manual controls, no autoplay and keyboard instant']});await c.close();
 }
 fs.writeFileSync(folder+'/browser-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
