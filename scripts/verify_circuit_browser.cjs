/* Circuit page acceptance. Browser plugin unavailable; use bundled Playwright.
   Screenshots are taken at deviceScaleFactor 1, matching the owner's low-DPI monitors. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const { verifyReadOnlyServer } = require('./verification_server_guard.cjs');
const base = process.env.BET36FLY_BASE_URL || 'http://127.0.0.1:8765';
const output = path.resolve(process.argv[2] || path.join(__dirname, '..', 'docs/evidence/circuit-page-2026-09-14'));
(async () => {
  const guard = await verifyReadOnlyServer(base);
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1200 }, deviceScaleFactor: 1 });
  const errors = [], requests = [], checks = [], consoleMessages = [];
  let testingErrors = false;
  page.on('console', m => { if (['error', 'warning'].includes(m.type())) consoleMessages.push({ text: m.text(), expected: testingErrors }); });
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => { if (r.url().startsWith(base + '/api/')) requests.push({ url: r.url(), method: r.method() }); });
  const check = async (name, action) => { await action(); checks.push(name); console.log('PASS', name); };
  const visible = async locator => { await locator.waitFor({ state: 'visible' }); };
  const snap = async name => { await page.evaluate(() => { if (document.activeElement?.id === 'main') document.activeElement.blur(); window.scrollTo(0, 0); }); await page.screenshot({ path: path.join(output, name + '.png'), fullPage: true, animations: 'disabled' }); };
  const canvas = () => page.getByRole('img', { name: /Projection of/ });
  const options = () => page.getByLabel('Inspect displayed neuron', { exact: true }).locator('option');
  /** Walk a coarse grid until the hover tooltip proves a real node sits under the pointer. */
  const findNode = async () => {
    const box = await canvas().boundingBox();
    for (let y = 24; y < box.height - 24; y += 9) for (let x = 24; x < box.width - 24; x += 9) {
      await page.mouse.move(box.x + x, box.y + y);
      if (await page.locator('.neuron-preview').count()) return { x: box.x + x, y: box.y + y };
    }
    throw new Error('No neuron was hoverable anywhere on the canvas.');
  };
  try {
    await check('circuit page reached from the header nav and kept on its own hash', async () => {
      await page.goto(base + '/#overview');
      await page.getByRole('link', { name: 'Circuit', exact: true }).click();
      await visible(page.getByRole('heading', { name: 'The wiring the simulator runs on' }));
      await visible(canvas());
      // The valid-route list in App.tsx must include #circuit or this replaceStates to #overview.
      assert.match(page.url(), /\/#circuit$/);
      await page.reload();
      await visible(canvas());
      assert.match(page.url(), /\/#circuit$/);
    });
    await check('displayed and retained counts come from the payload', async () => {
      const payload = await page.request.get(base + '/api/brain').then(r => r.json());
      const expected = `${payload.displayed_neurons.toLocaleString('en-US')} displayed / ${payload.total_neurons.toLocaleString('en-US')} retained`;
      assert.match(await page.locator('.canvas-bottom').innerText(), new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
      assert.equal(payload.displayed_neurons, 2500);
      assert.equal(payload.total_neurons, 166700);
      assert.equal(await options().count(), payload.displayed_neurons + 1);
    });
    await check('the KC to MBON layer is named anatomically, never plastic or learned', async () => {
      await visible(page.getByLabel('KC→MBON output synapses', { exact: true }));
      const text = await page.locator('.circuit-page').innerText();
      assert.ok(text.includes('KC→MBON output synapses'), 'the anatomical layer name is not rendered');
      for (const banned of ['plastic', 'Plastic', 'learned gain', 'trained', 'Recorded pick', 'replay']) {
        assert.ok(!text.includes(banned), `page copy still contains "${banned}"`);
      }
    });
    await check('layer toggle changes only what is displayed', async () => {
      const before = await options().count();
      await page.getByLabel('Kenyon cells', { exact: true }).uncheck();
      const after = await options().count();
      assert.ok(after < before, `expected fewer selectable neurons, got ${after} of ${before}`);
      await page.getByLabel('Kenyon cells', { exact: true }).check();
      assert.equal(await options().count(), before);
      await page.getByLabel('KC→MBON output synapses', { exact: true }).uncheck();
      await visible(canvas());
      await page.getByLabel('KC→MBON output synapses', { exact: true }).check();
    });
    await check('hovering a real node previews it and clicking opens the inspector', async () => {
      const point = await findNode();
      const preview = await page.locator('.neuron-preview').innerText();
      assert.ok(preview.includes('Click to inspect'), preview);
      await page.mouse.click(point.x, point.y);
      const dialog = page.getByRole('dialog', { name: 'Circuit explanation inspector' });
      await visible(dialog);
      assert.match(await dialog.innerText(), /Neuron \d+/);
      assert.match(await dialog.innerText(), /Displayed incident connections/);
      await snap('circuit-inspector-desktop');
      await page.keyboard.press('Escape');
      await dialog.waitFor({ state: 'detached' });
    });
    await check('explainer topics pin into the inspector and close with Escape', async () => {
      await page.getByRole('button', { name: 'Explain Kenyon cells — KCs' }).click();
      const dialog = page.getByRole('dialog', { name: 'Circuit explanation inspector' });
      await visible(dialog);
      assert.match(await dialog.innerText(), /mushroom-body sensory representations/);
      await page.keyboard.press('Escape');
      await dialog.waitFor({ state: 'detached' });
    });
    await check('every rendered text size clears the 11px legibility floor', async () => {
      const small = await page.evaluate(() => [...document.querySelectorAll('.circuit-page *')]
        .filter(el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
        .map(el => ({ tag: el.className || el.tagName, size: parseFloat(getComputedStyle(el).fontSize) }))
        .filter(item => item.size < 11));
      assert.deepEqual(small, []);
      // Legend swatches must sit on the canvas ground; the same colors reach 1.4:1 on the card.
      const grounds = await page.evaluate(() => [...document.querySelectorAll('.circuit-swatch')].map(el => getComputedStyle(el).backgroundColor));
      assert.ok(grounds.length >= 7, `expected a swatch per layer, found ${grounds.length}`);
      assert.deepEqual([...new Set(grounds)], ['rgb(25, 34, 28)']);
    });
    await check('desktop screenshot at device scale factor 1', async () => {
      assert.equal(await page.evaluate(() => window.devicePixelRatio), 1);
      await snap('circuit-desktop-1920');
    });
    await check('no horizontal overflow from 320 px upward', async () => {
      for (const width of [320, 390, 720, 1024, 1440]) {
        await page.setViewportSize({ width, height: 844 });
        await page.goto(base + '/#circuit');
        await visible(canvas());
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `overflow at ${width}`);
        if (width === 320) await snap('circuit-mobile-320');
      }
      await page.setViewportSize({ width: 1920, height: 1200 });
    });
    await check('the circuit page runs no simulator and issues only GET reads', async () => {
      assert.ok(requests.length > 0);
      assert.ok(requests.every(r => r.method === 'GET'), JSON.stringify(requests.filter(r => r.method !== 'GET')));
      assert.ok(!requests.some(r => /\/api\/(predict|training|associative\/jobs)/.test(r.url)), 'a retired workflow route was requested');
      const before = requests.length;
      await page.waitForTimeout(6500);
      assert.equal(requests.length, before, 'the circuit page must not poll');
    });
    testingErrors = true;
    await check('connectome error state, explicit retry and recovery', async () => {
      await page.route('**/api/brain', route => route.fulfill({ status: 503, json: { detail: 'Test fixture: connectome unavailable.' } }));
      // A distinct query forces a real document load; re-visiting the same hash would not refetch.
      await page.goto(base + '/?qa=brain-error#circuit');
      await visible(page.getByRole('alert'));
      assert.match(await page.getByRole('alert').innerText(), /Test fixture: connectome unavailable\./);
      assert.equal(await canvas().count(), 0);
      await visible(page.getByRole('button', { name: 'Retry connectome' }));
      await snap('circuit-error');
      await page.unroute('**/api/brain');
      await page.getByRole('button', { name: 'Retry connectome' }).click();
      await visible(canvas());
    });
    await check('empty geometry states plainly that nothing can be drawn', async () => {
      await page.route('**/api/brain', route => route.fulfill({ json: { dataset: 'MaleCNS v1.0', nodes: [], edges: [], edge_metadata: [], displayed_neurons: 0, total_neurons: 0, coordinate_note: 'No annotated soma coordinates available.' } }));
      await page.goto(base + '/?qa=brain-empty#circuit');
      await visible(page.getByText('No display neurons available', { exact: true }));
      await visible(page.locator('.circuit-empty'));
      await snap('circuit-empty');
      await page.unroute('**/api/brain');
    });
    assert.deepEqual(errors, []);
    assert.deepEqual(consoleMessages.filter(m => !m.expected), []);
    fs.writeFileSync(path.join(output, 'evidence.json'), JSON.stringify({ base, guard, checks, errors, consoleMessages, requests,
      browser: 'Playwright Chromium; Browser plugin unavailable', device_scale_factor: 1,
      synthetic_states: ['503 brain', 'empty geometry'],
      screenshots: fs.readdirSync(output).filter(f => f.endsWith('.png')) }, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
