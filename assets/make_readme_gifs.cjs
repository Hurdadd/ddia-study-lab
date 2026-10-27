/* Records docs/media/*.gif for the README from the running local site (needs ffmpeg and Playwright Chromium).
   Usage: python3 -m http.server 8766 --bind 127.0.0.1 &  then  node assets/make_readme_gifs.cjs */
const {chromium}=require('playwright'),{execFileSync}=require('child_process'),fs=require('fs'),os=require('os'),path=require('path');
const BASE=process.env.BASE_URL||'http://127.0.0.1:8766',OUT=path.resolve(__dirname,'../docs/media');
fs.mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function encode(dir,name,interval,width){
  execFileSync('ffmpeg',['-y','-v','error','-framerate',String(1000/interval),'-i',path.join(dir,'f%03d.png'),'-vf',`scale=${width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=bayer:bayer_scale=4`,'-loop','0',path.join(OUT,name)]);
  fs.rmSync(dir,{recursive:true});console.log(name,(fs.statSync(path.join(OUT,name)).size/1e6).toFixed(2)+' MB');
}
async function record(name,target,count,interval,width){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'gif-'));
  for(let i=0;i<count;i++){const t=Date.now();await target.screenshot({path:path.join(dir,`f${String(i).padStart(3,'0')}.png`)});await sleep(Math.max(0,interval-(Date.now()-t)));}
  encode(dir,name,interval,width);
}
// Clip screenshots instead of element screenshots: scrolling would stop the lab's off-screen auto-pause timers.
async function clip(page,locator){const box=await locator.evaluate(el=>{const r=el.getBoundingClientRect();return {x:r.left+scrollX,y:r.top+scrollY,width:r.width,height:r.height};});return {screenshot:o=>page.screenshot({...o,clip:box,fullPage:true})};}
async function english(page){if(await page.evaluate(()=>document.documentElement.lang)!=='en')await page.click('[data-lang-toggle]');await sleep(300);}
(async()=>{
  const browser=await chromium.launch({channel:process.env.PW_CHANNEL||'chrome'}),ctx=await browser.newContext({viewport:{width:1100,height:760},reducedMotion:'no-preference',colorScheme:'light'});
  const page=await ctx.newPage();
  await page.goto(`${BASE}/studio/index.html?exercise=ch8-ex4`);await sleep(1200);await english(page);
  await page.click('#reference-tab');await sleep(700);
  const canvas=await clip(page,page.locator('#canvas-surface'));
  await page.click('#canvas-run');
  await record('studio-run.gif',canvas,36,110,880);
  await page.goto(`${BASE}/ch6-replication/index.html`);await sleep(1000);await english(page);
  const lab=page.locator('#try-replication');await lab.scrollIntoViewIfNeeded();await sleep(1500);
  const labClip=await clip(page,lab),dir=fs.mkdtempSync(path.join(os.tmpdir(),'gif-'));let n=0;
  // Drive the lab step by step (its auto-play pauses when a screenshot resizes the viewport).
  const snap=async times=>{for(let k=0;k<times;k++){await labClip.screenshot({path:path.join(dir,`f${String(n++).padStart(3,'0')}.png`)});await sleep(120);}};
  await snap(3);
  for(const id of ['write','hold','follower','deliver']){await lab.locator(`[data-lab-action="${id}"]`).click();await snap(5);}
  await lab.locator('[data-lab-control="reset"]').click();await snap(2);
  for(const id of ['write','hold','leader']){await lab.locator(`[data-lab-action="${id}"]`).click();await snap(5);}
  encode(dir,'chapter-lab.gif',260,640);
  await browser.close();
})();
