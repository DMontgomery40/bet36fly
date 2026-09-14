/* Current product acceptance. Browser plugin unavailable; use bundled Playwright. */
const { loadPlaywright } = require('./playwright.cjs');
const { chromium } = loadPlaywright();
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), crypto = require('crypto');
const { verifyReadOnlyServer } = require('./verification_server_guard.cjs');
const base = process.env.BET36FLY_BASE_URL || 'http://127.0.0.1:8765';
const output = path.resolve(process.argv[2] || '/tmp/bet36fly-sensory-browser');
(async () => {
  const guard = await verifyReadOnlyServer(base);
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  const errors = [], requests = [], checks = [], consoleMessages = [];
  let testingErrors = false;
  page.on('console', message => { if (['error','warning'].includes(message.type())) consoleMessages.push({text:message.text(), expected:testingErrors}); });
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => { if (r.url().startsWith(base+'/api/')) requests.push({ url:r.url(), method:r.method() }); });
  const check = async (name, action) => { await action(); checks.push(name); console.log('PASS', name); };
  const visible = async locator => { await locator.waitFor({state:'visible'}); };
  const snap = async name => { await page.evaluate(() => { if (document.activeElement?.id === 'main') document.activeElement.blur(); window.scrollTo(0,0); }); await page.screenshot({path:path.join(output,name+'.png'), fullPage:true, animations:'disabled'}); if (['overview-desktop','overview-mobile','matchup-mobile'].includes(name)) await page.screenshot({path:path.join(output,name+'-viewport.png'),fullPage:false, animations:'disabled'}); };
  try {
    await check('overview: identity, confirmation and comparators', async () => {
      await page.goto(base+'/#overview');
      await visible(page.getByRole('heading', {name:'A small circuit. A measured result.'}));
      assert.match(await page.title(), /Sensory research/);
      assert.match(await page.locator('.big-result').innerText(), /56.21/);
      assert.equal(await page.locator('.comparison-section tbody tr').count(),6);
      assert.equal(await page.locator('vite-error-overlay').count(),0);
      await snap('overview-desktop');
    });
    await check('all games: filters, paging and full versus subset summaries', async () => {
      await page.getByRole('link',{name:'Backtest explorer',exact:true}).click();
      await visible(page.getByText('2,423 matching games',{exact:true}));
      assert.equal(await page.locator('.games-table tbody tr').count(),50);
      await page.getByRole('button',{name:'Next →',exact:true}).click();
      await visible(page.getByText('Showing 51–100 of 2,423',{exact:true}));
      await page.getByLabel('Team',{exact:true}).selectOption('Atlanta Braves');
      await page.getByLabel('From (UTC)',{exact:true}).fill('2023-03-30');
      await page.getByLabel('Through (UTC)',{exact:true}).fill('2023-03-30');
      await visible(page.getByText('1 matching games',{exact:true}));
      assert.match(await page.locator('.filtered-summary').innerText(), /100.00%/);
      assert.match(await page.locator('.full-result-note').innerText(), /56.21%/);
      await snap('filtered-desktop');
    });
    await check('matchup: exact qualities, cells, requests and recorded outputs', async () => {
      await page.getByRole('link',{name:/Inspect Atlanta Braves/}).click();
      await visible(page.locator('.matchup-heading h1'));
      assert.equal(await page.locator('.probe-card').count(),2);
      assert.match(await page.locator('.quality-score').last().innerText(), /0.263/);
      assert.match(await page.locator('.probability-card').innerText(), /38.10%/);
      await page.locator('.probe-card').last().locator('summary').click();
      assert.match(await page.locator('.probe-card').last().locator('.body-ids').innerText(), /512551/);
      assert.equal(await page.locator('.output-row').count(),4);
      await page.getByText('Individual recorded seeds',{exact:true}).click();
      assert.equal(await page.locator('.output-chart tbody tr').count(),6);
      await snap('matchup-desktop');
      await page.getByRole('link',{name:'← Back to game results'}).click();
      await visible(page.getByText('1 matching games',{exact:true}));
    });
    await check('empty results, invalid dates and clearing filters', async () => {
      await page.getByLabel('From (UTC)',{exact:true}).fill('2024-01-01');
      await visible(page.getByText('Start date must be on or before end date.',{exact:true}));
      await page.getByLabel('Through (UTC)',{exact:true}).fill('2024-01-02');
      await visible(page.getByRole('heading',{name:'No games match these filters.'}));
      assert.match(await page.locator('.filtered-summary').innerText(), /Unavailable/);
      await snap('empty');
      await page.getByRole('button',{name:'Clear filters'}).click();
      await visible(page.getByText('2,423 matching games',{exact:true}));
    });
    await check('methods, provenance and every exact-byte download', async () => {
      await page.getByRole('link',{name:'Pipeline & methods',exact:true}).click();
      await visible(page.getByRole('heading',{name:'Follow the signal. Keep the limits in view.'}));
      await page.getByText('Identity, source and hashes',{exact:true}).click();
      const summary = await page.request.get(base+'/api/sensory/summary').then(r=>r.json());
      for (const item of summary.downloads) {
        const [download] = await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:item.label,exact:true}).click()]);
        const file = await download.path();
        assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),item.sha256);
      }
      await snap('methods-desktop');
    });
    await check('legacy hashes and path bookmarks resolve to current overview', async () => {
      for (const old of ['/#training','/#ledger','/#desk','/#observatory','/#v2','/training','/desk','/ledger','/observatory']) {
        await page.goto(base+old);
        await visible(page.getByRole('heading',{name:'A small circuit. A measured result.'}));
        assert.match(page.url(), /\/#overview$/);
      }
    });
    await check('no legacy polling or mutating product requests', async () => {
      const before = requests.length;
      await page.waitForTimeout(6500);
      assert.equal(requests.length,before);
      assert.ok(requests.every(r => r.method==='GET' && r.url.startsWith(base+'/api/sensory/')));
    });
    await check('keyboard skip navigation preserves the active page', async () => {
      await page.goto(base+'/#backtest');
      await visible(page.getByText('2,423 matching games',{exact:true}));
      await page.locator('.skip-link').focus(); await page.keyboard.press('Enter');
      assert.ok(page.url().endsWith('#backtest'));
      assert.equal(await page.evaluate(() => document.activeElement.id), 'main');
    });
    await check('responsive overview, explorer, details and methods', async () => {
      for (const width of [320,390,720,1024]) {
        await page.setViewportSize({width,height:844});
        for (const hash of ['#overview','#backtest','#backtest/baseball%3Amlb%3A718780','#methods']) {
          await page.goto(base+'/'+hash);
          await visible(page.locator('h1'));
          await page.waitForFunction(() => !document.body.innerText.includes('Loading'));
          assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1), `overflow ${width} ${hash}`);
          if (width===390) await snap(hash.includes('/')?'matchup-mobile':hash.slice(1)+'-mobile');
        }
      }
    });
    await page.setViewportSize({width:1440,height:1050});
    await check('loading and unavailable summary, retry recovery', async () => {
      let release; const gate = new Promise(resolve => { release=resolve; });
      await page.route('**/api/sensory/summary', async route => { await gate; await route.continue(); });
      await page.goto(base+'/?qa=loading#overview');
      await visible(page.getByRole('heading',{name:'Loading frozen confirmation…'}));
      release(); await visible(page.getByRole('heading',{name:'A small circuit. A measured result.'}));
      await page.unroute('**/api/sensory/summary');
      for (const status of ['unavailable','invalid']) {
        await page.route('**/api/sensory/summary', route => route.fulfill({json:{status,identity:'fixture',message:'Test fixture: evidence unavailable.'}}));
        await page.reload(); await visible(page.getByRole('heading',{name:'Confirmation unavailable'}));
        assert.equal(await page.locator('.big-result').count(),0);
        await snap(status);
        await page.unroute('**/api/sensory/summary');
        await page.getByRole('button',{name:'Try again',exact:true}).click();
        await visible(page.getByRole('heading',{name:'A small circuit. A measured result.'}));
      }
    });
    testingErrors = true;
    await check('game and detail errors, retry and unknown game', async () => {
      await page.route('**/api/sensory/games?*', route => route.fulfill({status:503,json:{detail:'Test fixture: game data failed.'}}));
      await page.goto(base+'/#backtest'); await visible(page.getByRole('heading',{name:'Evidence unavailable'}));
      await page.unroute('**/api/sensory/games?*');
      await page.getByRole('button',{name:'Try again',exact:true}).click(); await visible(page.getByText('2,423 matching games',{exact:true}));
      await page.goto(base+'/#backtest/unknown'); await visible(page.getByText('Confirmation game not found.',{exact:true}));
      await page.getByRole('link',{name:'← All confirmation games'}).click(); await visible(page.getByText('2,423 matching games',{exact:true}));
    });
    assert.deepEqual(errors,[]);
    assert.deepEqual(consoleMessages.filter(m=>!m.expected), []);
    fs.writeFileSync(path.join(output,'evidence.json'),JSON.stringify({base,guard,checks,errors,consoleMessages,requests,browser:'Playwright Chromium; Browser plugin unavailable',synthetic_states:['loading','unavailable','invalid','503 games'],screenshots:fs.readdirSync(output).filter(f=>f.endsWith('.png'))},null,2));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e); process.exitCode=1;});
