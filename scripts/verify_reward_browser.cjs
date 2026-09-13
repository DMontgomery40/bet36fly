const { chromium } = require('playwright');
const fs = require('fs'), assert = require('assert/strict'), crypto = require('crypto'), path = require('path');
const { verifyReadOnlyServer } = require('./verification_server_guard.cjs');
const output = path.resolve(process.argv[2] || 'output/browser/reward-v3');
const base = process.env.BET36FLY_BASE_URL || 'http://127.0.0.1:8765';
(async () => {
 const verification=await verifyReadOnlyServer(base);
 fs.mkdirSync(output, {recursive:true});
 const browser = await chromium.launch({headless:true});
 const page = await browser.newPage({viewport:{width:1440,height:1100}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/#training');
 const mechanism=page.getByRole('region',{name:'Mechanism qualification'});
 await mechanism.locator('.mechanism-table tbody tr').first().waitFor();
 const diagnosticState=await page.request.get(base+'/api/reward-diagnostics').then(r=>r.json());
 assert.equal(await mechanism.locator('.mechanism-table tbody tr').count(),diagnosticState.diagnostics.length);
 const measuredPanels=[];
 for(const row of diagnosticState.diagnostics.filter(x=>x.validation_status==='validated'||x.missing_validation.length===2)) {
  const detail=mechanism.locator('details.diagnostic-detail').filter({has:page.locator('summary').filter({hasText:row.run_id})});
  await detail.locator(':scope > summary').click();
  const text=await detail.innerText();
  assert.ok(text.includes(row.validation_status==='validated'?`validated ${row.evidence_status}`:`stored only · ${row.evidence_status}`));
  const guards=detail.locator('table').filter({hasText:'Untaught guard · absolute mean'});
  for(const [key,value] of Object.entries(row.untaught_guard)) {
   const guard=await guards.locator('tbody tr').filter({hasText:key}).innerText();
   for(const field of ['mean','sd','limit']) assert.ok(guard.includes(value[field].toFixed(6)),`${row.run_id} ${key} ${field}`);
  }
  assert.equal(await detail.locator('table').filter({hasText:'Seven frozen mechanism criteria'}).locator('tbody tr').count(),7);
  if(row.tail_evidence) {
   assert.ok(text.includes(row.tail_evidence.equation));
   assert.ok(text.includes('does not extend neural time'));
   assert.ok(text.includes(`${row.tail_evidence.electrical_bound_observations} electrical / ${row.tail_evidence.tail_bound_observations} tail bound observations`));
   assert.ok(text.includes(`τr ${row.rate_tau_ms} ms`));
  }
  const link=detail.getByRole('link',{name:'Full stored diagnostic JSON and validation'});
  assert.equal(await link.getAttribute('href'),row.detail_url);
  const full=await page.request.get(base+row.detail_url).then(r=>r.json());
  assert.deepEqual(full.validation,row);
  assert.equal((await page.request.get(base+row.detail_url+'/trials.npz')).status(),404);
  measuredPanels.push({run_id:row.run_id,validation_status:row.validation_status,evidence_status:row.evidence_status,detail_matches:true});
  await detail.screenshot({path:path.join(output,row.run_id+'-detail.png')});
  await detail.locator(':scope > summary').click();
 }
 const bridgePair=diagnosticState.qualification_pairs.find(x=>x.learning_rule==='rate-bridge-v1'&&x.validation_status==='validated');
 assert.ok(bridgePair); assert.equal(bridgePair.evidence_status,'failed');
 await mechanism.getByRole('heading',{name:'Pair qualification · failed',exact:true}).waitFor();
 const conditioning=page.getByRole('region',{name:'Conditioning and reversal'});
 await conditioning.getByText(diagnosticState.conditioning.message,{exact:true}).waitFor();
 await mechanism.screenshot({path:path.join(output,'bet36fly-mechanism-desktop.png')});
 const panel=page.getByRole('region',{name:'On-circuit reward learning experiments'});
 await panel.getByText('Common-seed input discrimination',{exact:true}).waitFor();
 const state=await page.request.get(base+'/api/experiments').then(r=>r.json());
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
  const response=await page.request.get(base+artifact.url);
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
  await test.goto(base+'/#training',{waitUntil:'domcontentloaded'});
  const area=test.getByRole('region',{name:'On-circuit reward learning experiments'});
  const wanted=mode==='loading'?'Loading reward experiment registry…':mode==='empty'?'No dopamine-association experiment has started.':mode==='error'?'Browser acceptance simulated registry failure':'Browser acceptance fixture: '+mode;
  await area.getByText(wanted,{exact:false}).first().waitFor();
  if(mode==='running')assert.ok((await area.innerText()).includes('3 / 96'));
  scenarios.push({mode,verified:true,source:'isolated browser response fixture'});
  await test.close();
 }
 // Synthetic mechanism/conditioning states: no fixtures are written as measured artifacts.
 for(const mode of ['loading','empty','error','incomplete','running','cancelled','budget_stopped','unknown']) {
  const test=await browser.newPage({viewport:{width:390,height:844}});
  test.on('pageerror',e=>errors.push('mechanism-'+mode+': '+e.message));
  let retrySucceeds=false;
  await test.route('**/api/reward-diagnostics',async route=>{
   if(mode==='loading') return;
   if(mode==='error'&&!retrySucceeds) return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Synthetic mechanism evidence unavailable'})});
   const data=structuredClone(diagnosticState);
   if(mode==='empty') { data.diagnostics=[]; data.qualification_pairs=[]; }
   if(mode==='incomplete') { data.qualification_pairs=[]; data.diagnostics=data.diagnostics.slice(0,1).map(x=>({...x,validation_status:'incomplete',evidence_status:'incomplete',stored_verdict:null,criteria:Object.fromEntries(Object.keys(x.criteria).map(k=>[k,null]))})); }
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  if(['running','cancelled','budget_stopped','unknown'].includes(mode)) await test.route('**/api/experiments',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...state,experiments:[...state.experiments,{id:'synthetic-conditioning',kind:'dopamine-conditioning',status:mode,created_at:new Date().toISOString(),updated_at:new Date().toISOString(),artifacts:{},conditioning:{status_reason:'Synthetic response fixture: '+mode},jobs:[{id:'acquisition_ab',variant:'acquisition_ab',status:mode,phase:mode,completed:12,total:100,seed:1,gain_parameters:0,decoder_parameters:0,active_parameters:0}]}]})}));
  await test.goto(base+'/#training',{waitUntil:'domcontentloaded'});
  const area=test.getByRole('region',{name:'Mechanism qualification'});
  if(mode==='loading') await area.getByText('Loading mechanism evidence…',{exact:true}).waitFor();
  else if(mode==='empty') await area.getByText('No stored mechanism panels.',{exact:true}).waitFor();
  else if(mode==='error') {
   await area.getByRole('button',{name:'Retry evidence'}).waitFor();
   retrySucceeds=true;
   await area.getByRole('button',{name:'Retry evidence'}).click();
   await area.locator('.mechanism-table tbody tr').first().waitFor();
   assert.equal(await area.getByRole('button',{name:'Retry evidence'}).count(),0);
  }
  else if(mode==='incomplete') await area.locator('.mechanism-table').getByText('incomplete',{exact:true}).first().waitFor();
  else {
   const stage=test.getByRole('region',{name:'Conditioning and reversal'});
   await stage.getByText('Synthetic response fixture: '+mode,{exact:true}).waitFor();
   assert.ok((await stage.innerText()).includes('12 / 100'));
   assert.ok(!(await stage.innerText()).includes('Conditioning passed'));
  }
  assert.ok(await test.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),mode+' synthetic state overflows mobile');
  scenarios.push({mode:'mechanism-'+mode,verified:true,source:'isolated synthetic response fixture'});
  await test.close();
 }
 // Isolated conditioning validator fixtures are explicitly synthetic, never registered artifacts.
 for(const evidence of ['passed','failed','incomplete','unverified']) {
  const test=await browser.newPage({viewport:{width:390,height:844}});
  test.on('pageerror',e=>errors.push('conditioning-validation-'+evidence+': '+e.message));
  await test.route('**/api/experiments',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...state,experiments:[{
   id:'synthetic-conditioning-validation',kind:'dopamine-conditioning',status:'completed',created_at:'',updated_at:'',artifacts:{},
   jobs:[{id:'acquisition-primary',status:'completed',completed:616,total:616}],
   conditioning_validation:{validation_status:evidence==='unverified'?'invalid':'validated',evidence_status:evidence,all_passed:evidence==='passed'?true:null,
    validated_calls:evidence==='passed'?1632:616,error:null,note:'Synthetic browser fixture only: compact counts and native group bound observations.',stages:evidence==='passed'?Object.fromEntries(['acquisition-primary','acquisition-challenge','reversal'].map(name=>[name,{all_passed:true}])):{'acquisition-primary':{all_passed:false}}}
  }]})}));
  await test.goto(base+'/#training',{waitUntil:'domcontentloaded'});
  const area=test.getByRole('region',{name:'Conditioning and reversal'});
  await area.getByText('Conditioning scientific verdict: '+evidence+'.',{exact:false}).waitFor();
  assert.ok((await area.innerText()).includes('616 / 616'));
  assert.ok((await area.innerText()).includes('Synthetic browser fixture only'));
  assert.ok(await test.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  scenarios.push({mode:'conditioning-validation-'+evidence,verified:true,source:'isolated synthetic validator response fixture'});
  await test.close();
 }
 // Retain successful reads across a refresh error, then exercise real Retry and recovery.
 const stalePage=await browser.newPage({viewport:{width:390,height:844}});
 stalePage.on('pageerror',e=>errors.push('stale-retry: '+e.message));
 await stalePage.clock.install();
 let refreshFailure=false;
 for(const [endpoint,payload] of [['reward-diagnostics',diagnosticState],['experiments',state]]) {
  await stalePage.route('**/api/'+endpoint,route=>route.fulfill({status:refreshFailure?503:200,contentType:'application/json',body:JSON.stringify(refreshFailure?{detail:'Synthetic retained-state refresh failure'}:payload)}));
 }
 await stalePage.goto(base+'/#training');
 const staleMechanism=stalePage.getByRole('region',{name:'Mechanism qualification'});
 const staleConditioning=stalePage.getByRole('region',{name:'Conditioning and reversal'});
 await staleMechanism.locator('.mechanism-table tbody tr').first().waitFor();
 await staleConditioning.getByText(diagnosticState.conditioning.message,{exact:true}).waitFor();
 refreshFailure=true;
 await stalePage.clock.fastForward(31000);
 await staleMechanism.getByText('Showing last loaded mechanism evidence',{exact:false}).waitFor();
 await staleConditioning.getByText('Showing last loaded conditioning registry.',{exact:false}).waitFor();
 assert.equal(await staleMechanism.locator('.mechanism-table tbody tr').count(),diagnosticState.diagnostics.length);
 assert.equal(await staleMechanism.getByRole('heading',{name:'Pair qualification · passed',exact:true}).count(),0);
 refreshFailure=false;
 await staleMechanism.getByRole('button',{name:'Retry evidence'}).click();
 await staleMechanism.getByRole('heading',{name:'Pair qualification · failed',exact:true}).waitFor();
 assert.equal(await staleMechanism.getByRole('alert').count(),0);
 await stalePage.clock.fastForward(31000);
 await staleConditioning.getByRole('alert').waitFor({state:'hidden'});
 scenarios.push({mode:'stale-retained-retry-recovery',verified:true,source:'isolated synthetic refresh errors with retained recorded payloads'});
 await stalePage.close();
 // No schema-4 sports run exists. Exercise the integrated raw/mask display with
 // an explicitly labeled response fixture, never by inventing a saved result.
 const candidate=await browser.newPage({viewport:{width:1440,height:1100}});
 candidate.on('pageerror',e=>errors.push('raw-gamma: '+e.message));
 await candidate.route('**/api/experiments',async route=>{
  const data=JSON.parse(JSON.stringify(state));
  data.experiments=data.experiments.filter(x=>x.kind!=='dopamine-association'||x.id===reward.id);
  const exp=data.experiments.find(x=>x.id===reward.id);
  exp.status='incomplete';
  exp.protocol.dan_reference='none'; exp.protocol.away_plasticity_mask='gamma';
  exp.reward.rule='raw-event-biphasic-kc-dan (browser fixture)';
  exp.reward.scope='Browser response fixture only';
  exp.reward.note='Synthetic display coverage; no candidate learning result is recorded.';
  delete exp.reward.activity_gate; delete exp.reward.fixed_readout; delete exp.reward.prior_metrics;
  exp.reward.anatomy.plasticity_mask={
   home:{policy:'all',eligible_edges:4184,excluded_edges:0,by_class:{gamma:0,apbp:0,ab:0,other:0}},
   away:{policy:'gamma',eligible_edges:3239,excluded_edges:1443,by_class:{gamma:3239,apbp:1443,ab:0,other:0}},
  };
  exp.reward.outcome={status:'incomplete',message:'Browser response fixture only: raw-D/gamma display, no measured candidate result.'};
  exp.jobs=[]; exp.artifacts={};
  await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
 });
 await candidate.goto(base+'/#training');
 const candidatePanel=candidate.getByRole('region',{name:'On-circuit reward learning experiments'});
 await candidatePanel.getByText('Raw dopamine drive (schema 4):',{exact:true}).waitFor();
 const candidateText=await candidatePanel.innerText();
 for(const wanted of ['event-based approximation','Away eligibility mask (gamma)','3,239 of 4,682','Home is not filtered (4,184 of 4,184)','excluded edges keep transmitting','Browser response fixture only']) assert.ok(candidateText.includes(wanted),`raw/gamma fixture lacks: ${wanted}`);
 assert.ok(!candidateText.includes('tonic firing carries no teaching'));
 await candidatePanel.screenshot({path:path.join(output,'bet36fly-reward-raw-gamma-fixture.png')});
 scenarios.push({mode:'raw-gamma',verified:true,source:'isolated browser response fixture; no measured candidate result'});
 await candidate.close();
 assert.deepEqual(errors,[]);
 const evidence={mechanism:{panels:measuredPanels,pair:bridgePair,conditioning:diagnosticState.conditioning},checked_at:new Date().toISOString(),url:page.url(),verification,experiment:reward.id,status:reward.status,encoder:reward.protocol.encoder,gate_status:reward.reward.activity_gate.status,gated_experiment:gated.id,gated_status:gated.status,gate_message:gated.reward.activity_gate.message,active_v1:state.active_v1.run_id,v2_status:v2.status,v2_jobs:v2.jobs.reduce((a,j)=>(a[j.status]=(a[j.status]||0)+1,a),{}),arms,downloads,scenarios,desktop:{width:1440,height:1100},mobile:{width:390,height:844,horizontal_page_overflow:false,tested_widths:widths},errors,screenshots:[path.join(output,'bet36fly-reward-gate-passed.png'),path.join(output,'bet36fly-reward-gate-failed.png'),path.join(output,'bet36fly-reward-desktop.png'),path.join(output,'bet36fly-reward-arm.png'),path.join(output,'bet36fly-reward-mobile.png'),path.join(output,'bet36fly-reward-mobile-arm.png')]};
 fs.writeFileSync(path.join(output,'bet36fly-reward-browser-evidence.json'),JSON.stringify(evidence,null,2));
 console.log(JSON.stringify(evidence));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
