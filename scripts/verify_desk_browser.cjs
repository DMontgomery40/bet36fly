const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
// Run against the local, trained server. This exercises real paper-only inference.
// Supply PLAYWRIGHT_MODULE when Playwright is provided by a workspace runtime.
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1050},deviceScaleFactor:1});
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765/#desk');
  await page.getByRole('heading',{name:'Small brain. Big weekend.'}).waitFor();
  await page.getByRole('button',{name:'Run brain now',exact:true}).waitFor();
  await page.waitForFunction(()=>!document.querySelector('.desk-run').disabled);
  const before=await (await page.request.get('http://127.0.0.1:8765/api/desk')).json();
  const first=before.rows.find(r=>r.state==='upcoming');
  const neuralResponse=page.waitForResponse(r=>r.url().includes('/api/predict/')&&r.request().method()==='POST');
  await page.getByRole('button',{name:`Watch this pick: ${first.prediction.away} at ${first.prediction.home}`,exact:true}).click();
  const inference=await (await neuralResponse).json();
  await page.getByRole('slider',{name:'Recorded spike frame'}).waitFor();
  await page.getByRole('button',{name:'Replay spikes',exact:true}).waitFor({state:'visible'});
  const after=await (await page.request.get('http://127.0.0.1:8765/api/desk')).json();
  assert.equal(after.rows.find(r=>r.game_id===first.game_id).prediction.id,first.prediction.id);
  assert.ok(inference.activity.total_spikes>0);
  assert.equal(await page.locator('.desk-trace rect').count(),inference.activity.population.length);
  await page.getByRole('button',{name:'Replay spikes',exact:true}).click();
  await page.getByRole('slider',{name:'Recorded spike frame'}).press('Home');
  for(let i=0;i<5;i++) await page.getByRole('slider',{name:'Recorded spike frame'}).press('ArrowRight');
  assert.equal(await page.getByRole('slider',{name:'Recorded spike frame'}).inputValue(),'5');
  await page.getByRole('button',{name:'Soccer',exact:true}).click();
  assert.equal(await page.locator('.desk-pick').count(),3);
  assert.equal(await page.locator('.desk-pick').first().locator('.desk-match-meta>span').innerText(),'EPL');
  await page.getByRole('button',{name:'Results',exact:true}).click();
  assert.equal(await page.locator('.desk-table tbody tr').count(),before.by_sport.soccer.completed);
  await page.getByRole('button',{name:'Baseball',exact:true}).click();
  assert.equal(await page.locator('.desk-table tbody tr').count(),before.by_sport.baseball.completed);
  const completed=before.rows.find(r=>r.prediction.sport==='baseball' && ['won','lost'].includes(r.state));
  if(completed){
    await page.getByRole('button',{name:`Inspect recorded pick for ${completed.prediction.away} at ${completed.prediction.home}`,exact:true}).click();
    assert.equal(await page.locator('.desk-evidence').getAttribute('open'),'');
    assert.ok((await page.locator('.desk-evidence').innerText()).includes(`Final: ${completed.result.home_score}–${completed.result.away_score}`));
  }
  await page.getByRole('button',{name:'All',exact:true}).click();
  await page.getByRole('button',{name:'Upcoming & pending',exact:true}).click();
  const count=await page.locator('.desk-table tbody tr').count();
  await page.getByRole('button',{name:/Show 10 more/}).click();
  assert.equal(await page.locator('.desk-table tbody tr').count(),count+10);
  await page.getByRole('link',{name:'Training',exact:true}).click();
  await page.getByRole('link',{name:'Pick ledger',exact:true}).click();
  await page.getByRole('link',{name:'Observatory',exact:true}).click();
  await page.getByRole('heading',{name:'A small brain. A new game.'}).waitFor();
  await page.getByRole('link',{name:'Fly’s desk',exact:true}).click();
  await page.getByRole('button',{name:'Replay spikes',exact:true}).waitFor();
  await page.waitForFunction(()=>document.querySelector('input[aria-label="Recorded spike frame"]')?.value==='19');
  await page.locator('.desk-title').scrollIntoViewIfNeeded();
  await page.evaluate(()=>window.scrollTo(0,0));
  const widths=[];
  for(const width of [1440,1024,768,390,320]) {
    await page.setViewportSize({width,height:1050});
    await page.evaluate(()=>window.scrollTo(0,0));
    const geometry=await page.evaluate(()=>({inner:innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(geometry.scroll<=width,`Body overflow at ${width}: ${geometry.scroll}`);
    widths.push(geometry);
    if(width===1440||width===390) await page.screenshot({path:`docs/design/fly-desk-${width===1440?'desktop':'mobile'}.png`,fullPage:true});
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.getByRole('button',{name:'Run brain now',exact:true}).click();
  await page.getByRole('button',{name:'Replay spikes',exact:true}).waitFor();
  assert.equal(await page.getByRole('slider',{name:'Recorded spike frame'}).inputValue(),'19');
  assert.deepEqual(errors,[]);
  const evidence={checked_at:new Date().toISOString(),widths,first_prediction_id:first.prediction.id,inference:{active_neurons:inference.activity.active_neurons,total_spikes:inference.activity.total_spikes,wall_seconds:inference.activity.wall_seconds,bins:inference.activity.population.length},record:before.summary,checks:['direct fourth-tab route','actual neural POST','saved original pick unchanged','population bar count','replay and scrub','sport filters','results filter','completed pick evidence','pagination','other tabs','responsive body widths','reduced-motion replay','no JS errors']};
  await fs.writeFile('docs/design/fly-desk-browser-evidence.json',JSON.stringify(evidence,null,2)+'\n');
  console.log(JSON.stringify(evidence,null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
