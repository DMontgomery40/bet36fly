const { chromium } = require('playwright');
const fs = require('fs'), assert = require('assert/strict'), crypto = require('crypto'), path = require('path');
const output = path.resolve(process.argv[2] || 'output/browser/reward-v3');
fs.mkdirSync(output, {recursive:true});
(async () => {
 const browser = await chromium.launch({headless:true});
 const page = await browser.newPage({viewport:{width:1440,height:1100}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/#training');
 const panel=page.getByRole('region',{name:'On-circuit reward learning experiments'});
 await panel.getByText('Common-seed input discrimination',{exact:true}).waitFor();
 const state=await page.request.get('http://127.0.0.1:8765/api/experiments').then(r=>r.json());
 const rewards=state.experiments.filter(x=>x.kind==='dopamine-association');
 const completed=rewards.filter(x=>x.status==='complete');
 const reward=completed[completed.length-1];
 const gated=rewards.find(x=>x.status==='failed'&&x.reward.activity_gate&&x.reward.activity_gate.status==='failed');
 const v2=state.experiments.find(x=>x.id==='v2-24a83145c27ab220116e');
 assert.ok(reward&&gated); assert.equal(v2.status,'paused'); assert.equal(state.active_v1.run_id,'20260910T232621Z');
 // The newest run opens first: the schema-3 pilot with the glomerular encoder and calibrated drive.
 assert.equal(rewards[rewards.length-1].id,reward.id);
 assert.equal(reward.protocol.encoder,'glomerular-tuning-v1'); assert.equal(reward.reward.activity_gate.status,'passed');
 const passedText=await panel.innerText();
 for(const wanted of ['Activity gate · passed','Sensory identity code (glomerular-tuning-v1)','Cell-type input gains','labeled lines','GABAergic APL neurons','Feature-to-glomerulus map','PAM12','MBON09','Fixed class-frequency prior']) assert.ok(passedText.includes(wanted),`passed-gate view lacks: ${wanted}`);
 const passedRows=await panel.locator('table').filter({hasText:'Teaching-check DAN response'}).locator('tbody tr').allInnerTexts();
 assert.equal(passedRows.length,2);
 assert.ok(passedRows[0].includes('PPL101')&&passedRows[0].includes('responsive')&&!passedRows[0].includes('not responsive'));
 assert.ok(passedRows[1].includes('PAM12')&&passedRows[1].includes(String(reward.reward.activity_gate.teaching_evoked_spikes[1])));
 await panel.locator('details.reward-encoder-map summary').click();
 assert.equal(await panel.locator('details.reward-encoder-map tbody tr').count(),reward.reward.anatomy.encoder.features.length);
 await panel.screenshot({path:path.join(output,'bet36fly-reward-gate-passed.png')});
 await panel.locator('label.reward-experiment-select select').selectOption(gated.id);
 await panel.getByText('Activity gate · failed',{exact:false}).first().waitFor();
 const gateText=await panel.innerText();
 for(const wanted of ['Activity gate · failed','Phasic dopamine drive','Declared gate margins','KC set overlap between calibration games','KCs still firing after stimulus offset','Tonic rate','Scheduled forced spikes','Evoked above tonic','not game-specific']) assert.ok(gateText.includes(wanted),`failed-gate view lacks: ${wanted}`);
 assert.ok(!gateText.includes('Sensory identity code'),'schema-2 run must not show a schema-3 encoder');
 const gateRows=await panel.locator('table').filter({hasText:'Teaching-check DAN response'}).locator('tbody tr').allInnerTexts();
 assert.equal(gateRows.length,2);
 assert.ok(gateRows[0].includes('PPL101')&&gateRows[0].includes('not responsive')&&gateRows[0].includes(String(gated.reward.activity_gate.teaching_evoked_spikes[0])));
 assert.ok(!gateText.includes('Validation class confusion'));
 await panel.screenshot({path:path.join(output,'bet36fly-reward-gate-failed.png')});
 await panel.locator('label.reward-experiment-select select').selectOption(reward.id);
 await panel.getByText('Fixed class-frequency prior',{exact:false}).first().waitFor();
 assert.ok((await panel.innerText()).includes('Fixed class-frequency prior'));
 const arms=[];
 for(const arm of ['paired','shuffled','frozen']) {
  await panel.getByRole('button',{name:arm,exact:true}).click();
  const detail=panel.getByRole('region',{name:'Selected reward arm details'});
  await detail.getByRole('heading',{name:arm,exact:true}).waitFor();
  assert.ok((await detail.innerText()).includes('Validation class confusion'));
  await detail.getByText('Learning-curve data',{exact:true}).click();
  assert.equal(await detail.locator('details tbody tr').count(),64);
  arms.push(arm);
 }
 await panel.getByRole('button',{name:'paired',exact:true}).click();
 await panel.getByText('Learning-curve data',{exact:true}).click();
 await panel.screenshot({path:path.join(output,'bet36fly-reward-desktop.png')});
 await panel.getByRole('region',{name:'Selected reward arm details'}).screenshot({path:path.join(output,'bet36fly-reward-arm.png')});
 const downloads=[];
 for(const artifact of Object.values(reward.artifacts)) {
  const response=await page.request.get('http://127.0.0.1:8765'+artifact.url);
  assert.equal(response.status(),200);
  const content=await response.body();
  assert.equal(crypto.createHash('sha256').update(content).digest('hex'),artifact.sha256);
  downloads.push({label:artifact.label,bytes:content.length,hash_matches:true});
 }
 await page.setViewportSize({width:390,height:844}); await panel.scrollIntoViewIfNeeded();
 const widths=[320,390,540,720,1024];
 for(const width of widths) {
  await page.setViewportSize({width,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),`Page overflows at ${width}px`);
 }
 await page.setViewportSize({width:390,height:844});
 await panel.getByRole('heading',{name:'On-circuit reward learning',exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(output,'bet36fly-reward-mobile.png')});
 await panel.getByRole('region',{name:'Selected reward arm details'}).screenshot({path:path.join(output,'bet36fly-reward-mobile-arm.png')});
 const scenarios=[];
 for(const mode of ['loading','empty','error','running','failed','budget_stopped']) {
  const test=await browser.newPage({viewport:{width:1100,height:900}});
  test.on('pageerror',e=>errors.push(mode+': '+e.message));
  await test.route('**/api/experiments',async route=>{
   if(mode==='loading') return;
   if(mode==='error') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Browser acceptance simulated registry failure"}'});
   const data=JSON.parse(JSON.stringify(state));
   if(mode==='empty')data.experiments=data.experiments.filter(x=>x.kind!=='dopamine-association');
   else {
    data.experiments=data.experiments.filter(x=>x.kind!=='dopamine-association'||x.id===reward.id);
    const exp=data.experiments.find(x=>x.kind==='dopamine-association'); exp.status=mode;
    exp.reward.outcome={status:mode,message:'Browser acceptance fixture: '+mode};
    delete exp.reward.prior_metrics;
    exp.jobs.forEach((j,i)=>{j.status=mode==='running'?(i===0?'running':'queued'):mode;j.phase=j.status;j.completed=i===0?3:0;delete j.metrics;delete j.reward_evidence;delete j.class_confusion;j.reward_curve=i===0?j.reward_curve.slice(0,3):[];});
    if(mode!=='running')exp.error='Browser acceptance fixture: '+mode;
   }
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  await test.goto('http://127.0.0.1:8765/#training',{waitUntil:'domcontentloaded'});
  const area=test.getByRole('region',{name:'On-circuit reward learning experiments'});
  const wanted=mode==='loading'?'Loading reward experiment registry…':mode==='empty'?'No dopamine-association experiment has started.':mode==='error'?'Browser acceptance simulated registry failure':'Browser acceptance fixture: '+mode;
  await area.getByText(wanted,{exact:false}).first().waitFor();
  if(mode==='running')assert.ok((await area.innerText()).includes('3 / 96'));
  scenarios.push({mode,verified:true,source:'isolated browser response fixture'});
  await test.close();
 }
 assert.deepEqual(errors,[]);
 const evidence={checked_at:new Date().toISOString(),url:page.url(),experiment:reward.id,status:reward.status,encoder:reward.protocol.encoder,gate_status:reward.reward.activity_gate.status,gated_experiment:gated.id,gated_status:gated.status,gate_message:gated.reward.activity_gate.message,active_v1:state.active_v1.run_id,v2_status:v2.status,v2_jobs:v2.jobs.reduce((a,j)=>(a[j.status]=(a[j.status]||0)+1,a),{}),arms,downloads,scenarios,desktop:{width:1440,height:1100},mobile:{width:390,height:844,horizontal_page_overflow:false,tested_widths:widths},errors,screenshots:[path.join(output,'bet36fly-reward-gate-passed.png'),path.join(output,'bet36fly-reward-gate-failed.png'),path.join(output,'bet36fly-reward-desktop.png'),path.join(output,'bet36fly-reward-arm.png'),path.join(output,'bet36fly-reward-mobile.png'),path.join(output,'bet36fly-reward-mobile-arm.png')]};
 fs.writeFileSync(path.join(output,'bet36fly-reward-browser-evidence.json'),JSON.stringify(evidence,null,2));
 console.log(JSON.stringify(evidence));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
