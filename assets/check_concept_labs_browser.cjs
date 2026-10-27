'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({channel:process.env.PW_CHANNEL||'chrome',headless:true});
  const page=await browser.newPage();
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const origin=process.env.BASE_URL||'http://127.0.0.1:8781';
  const dirs=fs.readdirSync('.').filter(p=>/^ch\d+-/.test(p)).sort();
  let experiments=0,links=0;
  for(const dir of dirs){
    await page.goto(`${origin}/${dir}/index.html`,{waitUntil:'domcontentloaded'});
    const lab=page.locator('.concept-lab');await lab.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>document.querySelector('.concept-lab')?.dataset.ready==='true');
    assert.equal(await page.locator('.lab-node').count(),3);
    assert.equal(await lab.locator('.lab-choices button').count()>0,true);
    links+=await page.locator('.exercise-studio-link').count();
    await lab.locator('.lab-choices button').first().click();
    assert.equal(await lab.locator('.lab-position').innerText(),'Step 1');
    await lab.locator('[data-lab-control="back"]').click();
    assert.equal(await lab.locator('.lab-position').innerText(),'Step 0');
    await lab.locator('[data-lab-control="reset"]').click();
    experiments++;
  }
  await page.setViewportSize({width:390,height:844});
  await page.goto(`${origin}/ch6-replication/index.html`,{waitUntil:'domcontentloaded'});
  const lab=page.locator('.concept-lab');await lab.scrollIntoViewIfNeeded();
  await page.waitForFunction(()=>document.querySelector('.concept-lab')?.dataset.ready==='true');
  await page.evaluate(()=>{document.documentElement.lang='fa';document.documentElement.dir='rtl';document.documentElement.dataset.theme='dark';});
  await page.emulateMedia({reducedMotion:'reduce'});
  await lab.locator('[data-lab-action="write"]').click();await lab.locator('[data-lab-action="hold"]').click();await lab.locator('[data-lab-action="follower"]').click();
  assert.match(await lab.locator('.lab-node').first().innerText(),/v0/);
  assert.equal(await lab.evaluate(el=>el.scrollWidth<=el.clientWidth+1),true,'mobile lab overflows');
  const bounds=await lab.boundingBox();assert.ok(bounds.width<=390);
  const bg=await lab.evaluate(el=>getComputedStyle(el).backgroundColor);assert.notEqual(bg,'rgba(0, 0, 0, 0)');
  assert.equal(await lab.locator('.lab-scene').getAttribute('aria-label'),'وضعیت فعلی سیستم');
  await lab.locator('[data-lab-control="back"]').click();await lab.locator('[data-lab-action="leader"]').click();
  assert.match(await lab.locator('.lab-node').first().innerText(),/v1/);
  await lab.locator('[data-lab-control="reset"]').click();
  // Enter activates the focused action with the same semantics as a pointer.
  await lab.locator('[data-lab-action="write"]').focus();await page.keyboard.press('Enter');
  assert.equal(await lab.locator('.lab-position').innerText(),'گام 1');
  assert.equal(await page.evaluate(()=>document.activeElement.dataset.labAction),'hold');
  await lab.screenshot({path:'/tmp/ddia-chapter-lab-fa-mobile-dark.png'});
  assert.deepEqual(errors,[],'browser runtime errors');
  console.log(`Browser chapter labs passed: ${experiments} chapters, ${links} exercise links; decision/back/reset, stale/fresh branches, Persian RTL, dark, 390px, keyboard, reduced motion.`);
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});
