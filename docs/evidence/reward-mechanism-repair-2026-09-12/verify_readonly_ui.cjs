const fs = require('fs');
const path = require('path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {verifyReadOnlyServer} = require(path.join(process.cwd(), 'scripts/verification_server_guard.cjs'));

(async () => {
  const base = process.env.BET36FLY_BASE_URL;
  assert(base);
  const marker = await verifyReadOnlyServer(base);
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  const mutations = [], errors = [];
  page.on('request', request => {
    if (request.url().startsWith(base) && !['GET','HEAD','OPTIONS'].includes(request.method())) {
      mutations.push({method:request.method(),url:request.url()});
    }
  });
  page.on('pageerror', error => errors.push(error.message));
  const surfaces = [];
  try {
    for (const tab of ['observatory','desk']) {
      await page.goto(`${base}/#${tab}`);
      await page.getByText('Read-only verification', {exact:false}).first().waitFor();
      const refresh = page.getByRole('button', {name:'Refresh games',exact:true});
      assert.equal(await refresh.isDisabled(), true);
      const selector = tab === 'observatory' ? 'button[aria-label^="Watch brain for "]' : 'button[aria-label^="Watch this pick:"],button.desk-run';
      await page.locator(selector).first().waitFor();
      const states = await page.locator(selector).evaluateAll(nodes => nodes.map(node => ({label:node.getAttribute('aria-label')||node.textContent,disabled:node.disabled})));
      assert(states.length > 0);
      assert(states.every(state => state.disabled));
      surfaces.push({tab,refresh_disabled:true,neural_controls:states});
    }
    assert.deepEqual(mutations,[]);
    assert.deepEqual(errors,[]);
    const output = path.join(process.cwd(),'output/browser/reward-mechanism-task4a/read-only-controls.json');
    fs.writeFileSync(output, JSON.stringify({checked_at:new Date().toISOString(),base,marker,surfaces,mutations,errors},null,2)+'\n');
    console.log(JSON.stringify({passed:true,output,counts:surfaces.map(s=>({tab:s.tab,disabled_neural_controls:s.neural_controls.length}))}));
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});
