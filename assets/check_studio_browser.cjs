'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
fs.mkdirSync('.impeccable/studio-review', { recursive: true });
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.PW_CHANNEL || 'chrome' });
  try {
    for (const lang of ['fa', 'en']) {
      const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.addInitScript(lang => localStorage.setItem('ddia-lang', lang), lang);
      await page.goto((process.env.BASE_URL || 'http://127.0.0.1:8766') + '/studio/?problem=ch6-ex1');
      await page.waitForFunction(() => window.DDIAStudio);
      const fixture = { nodes: [
        { id: 'client', type: 'client', label: 'Client', x: 60, y: 200, config: {} },
        { id: 'app', type: 'app-server', label: 'API', x: 400, y: 200, config: {} },
        { id: 'db', type: 'sql-db', label: 'DB', x: 740, y: 200, config: {} },
      ], edges: [] };
      await page.evaluate(g => DDIAStudio.loadGraph(g), fixture);
      await page.locator('[data-port="client"]').click();
      await page.locator('[data-node="app"] .node-body').click();
      assert.equal(await page.evaluate(() => DDIAStudio.getGraph().edges.length), 1);
      const label = page.locator('#selection-panel input[aria-label]').first();
      await label.fill('Read profile / خواندن پروفایل');
      await label.press('Tab');
      assert.equal(await page.locator('.edge-label').textContent(), 'Read profile / خواندن پروفایل');
      const original = await page.evaluate(() => DDIAStudio.getGraph().edges[0]);
      await page.locator('[data-endpoint="target"]').selectOption('db');
      assert.equal(await page.evaluate(() => DDIAStudio.getGraph().edges[0].target), 'db');
      await page.locator('#undo').click();
      assert.equal(await page.evaluate(() => DDIAStudio.getGraph().edges[0].target), original.target);
      await page.locator('[data-node="app"] .node-body').click({ button: 'right' });
      await page.locator('#canvas-context-menu button').filter({ hasText: lang === 'fa' ? 'ساخت کپی' : 'Duplicate' }).click();
      assert.equal(await page.evaluate(() => DDIAStudio.getGraph().nodes.length), 4);
      await page.locator('#undo').click();
      assert.equal(await page.evaluate(() => DDIAStudio.getGraph().nodes.length), 3);
      const surface = await page.locator('#design-canvas').boundingBox();
      await page.mouse.click(surface.x + surface.width / 2, surface.y + 100, { button: 'right' });
      await page.locator('#canvas-context-menu button').filter({ hasText: lang === 'fa' ? 'افزودن یادداشت' : 'Add note here' }).click();
      const note = page.locator('#selection-panel textarea');
      await note.fill('Editable annotation');await note.press('Tab');
      assert.equal(await page.evaluate(() => DDIAStudio.getGraph().annotations[0].text), 'Editable annotation');
      await page.locator('#undo').click();
      await page.locator('#undo').click();
      assert.equal(await page.evaluate(() => DDIAStudio.getGraph().annotations.length), 0);
      await page.locator('.graph-edge .edge-label').click({ button: 'right' });
      await page.locator('#canvas-context-menu button').filter({ hasText: lang === 'fa' ? 'برعکس' : 'Reverse' }).click();
      assert.equal(await page.evaluate(() => DDIAStudio.getGraph().edges[0].source), 'app');
      await page.locator('#undo').click();
      await page.locator('#walkthrough-header').click();
      assert.ok((await page.locator('#panel-walkthrough').innerText()).includes(lang === 'fa' ? 'اول سه history' : 'Write the three histories'));
      assert.ok(await page.locator('.lesson-diagram').count() >= 2);
      await page.locator('#panel-walkthrough button').filter({ hasText: lang === 'fa' ? 'ویرایش این نمودار' : 'Edit this reasoning' }).first().click();
      const run = await page.evaluate(() => DDIAStudio.simulate());
      assert.equal(run.valid, false, 'A reasoning diagram must not invent traffic numbers');
      await page.locator('#undo').click();
      await page.evaluate(() => { DDIAStudio.loadGraph(DDIAStudio.getProblem().reference); });
      const evaluation = await page.evaluate(() => DDIAStudio.evaluate());
      assert.equal(evaluation.total, 100);
      assert.equal(evaluation.mode, 'exercise-coverage');
      await page.locator('[data-panel="simulation"]').click();
      await page.locator('#traffic-qps').fill('2000');
      assert.equal(await page.locator('.evaluation-score').count(), 0, 'Changed inputs invalidate the old score');
      await page.evaluate(() => DDIAStudio.evaluate());
      assert.deepEqual(errors, []);
      await page.screenshot({ path: `.impeccable/studio-review/studio-${lang}.png`, fullPage: true });
      await page.close();
      console.log(`${lang}: port connection, custom label, reconnect, right-click duplicate/reverse, undo, authored walkthrough, honest run, reference coverage passed`);
    }
    const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await mobile.goto((process.env.BASE_URL || 'http://127.0.0.1:8766') + '/studio/?problem=ch6-ex1');
    await mobile.waitForFunction(() => window.DDIAStudio);
    assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth), 390);
    assert.ok(await mobile.locator('[data-tool="connect"]').isVisible());
    await mobile.locator('[data-tool="connect"]').click();
    assert.ok((await mobile.locator('#canvas-hint').textContent()).length > 10);
    await mobile.screenshot({ path: '.impeccable/studio-review/studio-mobile.png' });
    await mobile.close();
    console.log('Mobile: no horizontal overflow; Connect and its instructions are visible.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
