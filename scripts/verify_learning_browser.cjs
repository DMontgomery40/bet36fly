/* Browser acceptance for the /#learning dopamine-learning stage page.
 * Modelled on verify_sensory_browser.cjs: refuses to run against anything but the
 * guarded read-only verification server, then drives real DOM checks against the
 * four separate stage claims, the conditioning runs, season backtests, the
 * read-only job/probe forms, cross-page navigation and responsive layout.
 *
 * Every check runs to completion even if an earlier one failed, so a single
 * regression (e.g. a responsive-layout overflow) never suppresses the rest of
 * the report or the screenshots. The process still exits non-zero if any
 * check failed, if a page error was thrown, or if the console logged an
 * unexpected error/warning. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const { verifyReadOnlyServer } = require('./verification_server_guard.cjs');
const base = process.env.BET36FLY_BASE_URL || 'http://127.0.0.1:8765';
const output = path.resolve(process.argv[2] || '/tmp/bet36fly-learning-browser');

(async () => {
  const guard = await verifyReadOnlyServer(base);
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  const errors = [], requests = [], checks = [], consoleMessages = [];
  // The two read-only 405 checks deliberately trigger a failed network request; Chromium
  // logs that resource failure to the console itself (not something app JS can suppress).
  // Messages captured while testingErrors is true are recorded but not treated as failures.
  let testingErrors = false;
  page.on('console', message => { if (['error', 'warning'].includes(message.type())) consoleMessages.push({ text: message.text(), expected: testingErrors }); });
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => { if (r.url().startsWith(base + '/api/')) requests.push({ url: r.url(), method: r.method() }); });
  // Each check is best-effort and independent: a failure is recorded but never aborts
  // the run, so later checks (and the screenshots/report) still execute.
  const check = async (name, action) => {
    try { await action(); checks.push({ name, pass: true }); console.log('PASS', name); }
    catch (e) { checks.push({ name, pass: false, error: e.message }); console.error('FAIL', name, '-', e.message); }
  };
  const visible = async locator => { await locator.waitFor({ state: 'visible' }); };
  const section = title => page.locator('.learning-section').filter({ hasText: title });
  const snap = async name => {
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(output, name + '.png'), fullPage: true, animations: 'disabled' });
  };
  const observed = {};

  try {
    await check('nav: Dopamine learning link present, stage heading renders', async () => {
      await page.goto(base + '/#learning');
      await visible(page.locator('nav[aria-label="Main navigation"]').getByRole('link', { name: 'Dopamine learning', exact: true }));
      await visible(page.getByRole('heading', { level: 1, name: 'Stage: dopamine-dependent learning on the MaleCNS circuit' }));
      assert.equal(await page.locator('vite-error-overlay').count(), 0);
    });

    await check('four separate stage badges, last says no learned checkpoint in the product', async () => {
      const badges = page.locator('.learning-badge');
      await visible(badges.first());
      assert.equal(await badges.count(), 4);
      const titles = await badges.locator('h3').allInnerTexts();
      observed.badgeTitles = titles;
      assert.deepEqual(titles, [
        'Mechanism implemented',
        'Controlled acquisition, retention and reversal qualified',
        'Plasticity improves held-out prediction',
        'Application uses a learned checkpoint',
      ]);
      const applicationDetail = await badges.nth(3).locator('p').innerText();
      observed.applicationBadgeDetail = applicationDetail;
      assert.match(applicationDetail, /remain the frozen sensory confirmation/);
      assert.match(applicationDetail, /checkpoints are inspectable only/);
      const applicationState = await badges.nth(3).locator('.learning-verdict').innerText();
      observed.applicationBadgeState = applicationState;
      // The verdict pill is CSS text-transform:uppercase ("NO"); the underlying DOM text is "No".
      assert.equal(applicationState.toUpperCase(), 'NO');
      await snap('learning-desktop');
    });

    await check('conditioning section lists at least two runs including one qualified and one not, count matches the API', async () => {
      const evidencePayload = await page.request.get(base + '/api/associative/evidence').then(r => r.json());
      const apiConditioningCount = (evidencePayload.conditioning || []).length;
      observed.apiConditioningCount = apiConditioningCount;
      const conditioning = section('Does the rule learn a cue, and only from pairing?');
      await visible(conditioning);
      const runs = conditioning.locator('article.learning-card');
      const runCount = await runs.count();
      observed.conditioningRunCount = runCount;
      assert.ok(runCount >= 2, `expected at least 2 conditioning run cards, saw ${runCount}`);
      assert.equal(runCount, apiConditioningCount,
        `expected the rendered conditioning card count to match /api/associative/evidence (${apiConditioningCount}), saw ${runCount}`);
      const identities = await runs.locator('.learning-card-head h3').allInnerTexts();
      const verdicts = await runs.locator('.learning-card-head .learning-verdict').allInnerTexts();
      observed.conditioningIdentities = identities;
      observed.conditioningVerdicts = verdicts;
      assert.ok(identities.includes('associative-conditioning-d1d3992e38c1dfa5fef1'));
      assert.ok(identities.includes('associative-conditioning-42845736c62d3ac9841e'));
      const passedIndex = identities.indexOf('associative-conditioning-d1d3992e38c1dfa5fef1');
      const notQualifiedIndex = identities.indexOf('associative-conditioning-42845736c62d3ac9841e');
      // The verdict pill is CSS text-transform:uppercase; compare case-insensitively.
      assert.equal(verdicts[passedIndex].toUpperCase(), 'QUALIFIED');
      assert.equal(verdicts[notQualifiedIndex].toUpperCase(), 'DID NOT QUALIFY');
    });

    await check('season backtests table lists at least one arm', async () => {
      const sports = section('Does plasticity change a held-out prediction?');
      await visible(sports);
      const rows = sports.locator('table').first().locator('tbody tr');
      const rowCount = await rows.count();
      observed.sportsArmRows = rowCount;
      assert.ok(rowCount >= 1, `expected at least one season arm row, saw ${rowCount}`);
    });

    await check('start-job form exists and its 405 is rendered verbatim without mutating', async () => {
      const jobsBefore = await page.request.get(base + '/api/associative/jobs').then(r => r.json());
      const jobs = section('Run an arm.');
      await visible(jobs);
      await visible(jobs.getByRole('button', { name: 'Start training job', exact: true }));
      testingErrors = true;
      await jobs.getByRole('button', { name: 'Start training job', exact: true }).click();
      const errorBlock = jobs.locator('.learning-error');
      await visible(errorBlock);
      testingErrors = false;
      const text = await errorBlock.innerText();
      observed.startJobErrorText = text;
      assert.equal(text, 'Verification mode is read-only.');
      const jobsAfter = await page.request.get(base + '/api/associative/jobs').then(r => r.json());
      assert.deepEqual(jobsAfter, jobsBefore);
    });

    await check('checkpoint probe form lists checkpoints and its 405 is rendered verbatim', async () => {
      const probe = section('Read one immutable checkpoint.');
      await visible(probe);
      // Not getByLabel: the <select> has no explicit aria-label (unlike the sensory
      // "Team" filter), so its accname is computed from label content and folds in the
      // currently-selected option's own text ("Select a checkpoint"), which defeats an
      // exact-name match. There is exactly one <select> in this section, so target it directly.
      const select = probe.locator('select');
      // Checkpoints load asynchronously from /api/associative/checkpoints; wait for a
      // real option (index 1) to attach, not just the "Select a checkpoint" placeholder.
      await select.locator('option').nth(1).waitFor({ state: 'attached' });
      const optionCount = await select.locator('option').count();
      observed.checkpointOptionCount = optionCount;
      assert.ok(optionCount >= 2, `expected a placeholder plus at least one checkpoint option, saw ${optionCount}`);
      await select.selectOption({ index: 1 });
      const submit = probe.getByRole('button', { name: 'Probe checkpoint', exact: true });
      await visible(submit);
      assert.equal(await submit.isDisabled(), false);
      testingErrors = true;
      await submit.click();
      const errorBlock = probe.locator('.learning-error');
      await visible(errorBlock);
      testingErrors = false;
      const text = await errorBlock.innerText();
      observed.probeErrorText = text;
      assert.equal(text, 'Verification mode is read-only.');
    });

    await check('continual-learning section renders >=5 run cards with baseline and recovery arms, each with a chart, recovery cards show rho', async () => {
      const stress = section('Continual learning: dopamine-gated recovery');
      await visible(stress);
      const cards = stress.locator('article.learning-card');
      const cardCount = await cards.count();
      observed.stressCardCount = cardCount;
      assert.ok(cardCount >= 5, `expected at least 5 continual-learning run cards, saw ${cardCount}`);
      let baselineCount = 0, recoveryCount = 0;
      const chartCounts = [], rhoValues = [], armTexts = [];
      for (let i = 0; i < cardCount; i++) {
        const card = cards.nth(i);
        const meta = card.locator('.learning-meta li');
        const armLi = await meta.first().innerText();
        const rhoLi = await meta.nth(1).innerText();
        armTexts.push(armLi);
        const isBaseline = /baseline/i.test(armLi);
        const isRecovery = /recovery/i.test(armLi) && !isBaseline;
        if (isBaseline) baselineCount += 1;
        if (isRecovery) recoveryCount += 1;
        chartCounts.push(await card.locator('svg.learning-chart').count());
        if (isRecovery) rhoValues.push(rhoLi);
      }
      observed.stressArmTexts = armTexts;
      observed.stressChartCounts = chartCounts;
      observed.stressRhoValues = rhoValues;
      assert.ok(baselineCount >= 1, `expected at least one card with a "baseline" arm label, saw ${JSON.stringify(armTexts)}`);
      assert.ok(recoveryCount >= 1, `expected at least one card with a "recovery" arm label, saw ${JSON.stringify(armTexts)}`);
      assert.ok(chartCounts.every(c => c >= 1), `expected every continual-learning card to render an SVG chart, saw counts ${JSON.stringify(chartCounts)}`);
      assert.ok(rhoValues.length >= 1, 'expected at least one recovery card');
      assert.ok(rhoValues.every(v => /Recovery strength ρ\s*[-\d.]/.test(v)), `expected every recovery card to show a numeric rho value, saw ${JSON.stringify(rhoValues)}`);
      await snap('learning-continual');
    });

    await check('season backtests section renders evaluation cards with metrics tables and a plasticity-does-not-contribute verdict, count matches the API', async () => {
      const evidencePayload = await page.request.get(base + '/api/associative/evidence').then(r => r.json());
      const apiEvaluations = evidencePayload.evaluations || [];
      observed.apiEvaluationCount = apiEvaluations.length;
      const sports = section('Does plasticity change a held-out prediction?');
      await visible(sports);
      const evaluationCards = sports.locator('article.learning-card');
      const renderedCount = await evaluationCards.count();
      observed.renderedEvaluationCount = renderedCount;
      assert.ok(renderedCount >= 1, 'expected at least one rendered evaluation card');
      assert.equal(renderedCount, apiEvaluations.length,
        `expected the rendered evaluation card count to match /api/associative/evidence (${apiEvaluations.length}), saw ${renderedCount}`);
      let metricsTableSeen = false, doesNotContributeSeen = false;
      const verdictLines = [];
      for (let i = 0; i < renderedCount; i++) {
        const card = evaluationCards.nth(i);
        const caption = await card.locator('table').first().locator('caption').innerText().catch(() => '');
        if (/Held-out metrics/.test(caption)) metricsTableSeen = true;
        const verdictLine = await card.locator('.learning-verdict-line').filter({ hasText: 'Plasticity contributes' }).innerText();
        verdictLines.push(verdictLine);
        if (/Plasticity contributes:\s*no\b/i.test(verdictLine)) doesNotContributeSeen = true;
      }
      observed.evaluationVerdictLines = verdictLines;
      assert.ok(metricsTableSeen, 'expected at least one evaluation card to render a "Held-out metrics" table');
      assert.ok(doesNotContributeSeen, `expected at least one verdict line reading plasticity does not contribute, saw ${JSON.stringify(verdictLines)}`);
      const allFalseInApi = apiEvaluations.every(item => item.plasticity_contributes === false);
      observed.apiEvaluationsAllPlasticityContributesFalse = allFalseInApi;
      assert.ok(allFalseInApi, 'expected /api/associative/evidence evaluations[].plasticity_contributes to be false for every entry');
    });

    await check('all four stage badge verdict states read Yes, Yes, Not established, No', async () => {
      const badges = page.locator('.learning-badge');
      await visible(badges.first());
      const states = await badges.locator('.learning-verdict').allInnerTexts();
      // The verdict pill is CSS text-transform:uppercase, and Playwright's innerText returns
      // the rendered (uppercased) text here, not the JSX source casing — compare case-insensitively,
      // matching the convention the application-badge check above already uses for this same element.
      observed.badgeStates = states.map(s => s.trim());
      assert.deepEqual(observed.badgeStates.map(s => s.toUpperCase()), ['YES', 'YES', 'NOT ESTABLISHED', 'NO']);
    });

    await check('navigating to overview and back to learning both work', async () => {
      await page.getByRole('link', { name: 'Overview', exact: true }).click();
      await visible(page.getByRole('heading', { name: 'A small circuit. A measured result.' }));
      assert.match(page.url(), /#overview$/);
      await page.getByRole('link', { name: 'Dopamine learning', exact: true }).click();
      await visible(page.getByRole('heading', { level: 1, name: 'Stage: dopamine-dependent learning on the MaleCNS circuit' }));
      assert.match(page.url(), /#learning$/);
    });

    await check('responsive width 390 shows no horizontal overflow', async () => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(base + '/#learning');
      await visible(page.getByRole('heading', { level: 1, name: 'Stage: dopamine-dependent learning on the MaleCNS circuit' }));
      // Screenshot first: capture the real rendered state regardless of the assertion below.
      await snap('learning-mobile');
      const overflow = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth }));
      observed.mobileOverflow = overflow;
      let culprit = null;
      if (overflow.scrollWidth > overflow.innerWidth + 1) {
        culprit = await page.evaluate(() => {
          let best = null;
          document.querySelectorAll('a,nav').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.right > window.innerWidth + 1 && (!best || r.right > best.right)) {
              best = { tag: el.tagName, text: (el.textContent || '').trim().slice(0, 40), right: Math.round(r.right) };
            }
          });
          return best;
        });
      }
      observed.mobileOverflowCulprit = culprit;
      assert.ok(overflow.scrollWidth <= overflow.innerWidth + 1,
        `scrollWidth ${overflow.scrollWidth} > innerWidth+1 ${overflow.innerWidth + 1}` +
        (culprit ? ` — likely cause: <${culprit.tag}> "${culprit.text}" right edge ${culprit.right}px (header nav overflow, present on every page, not specific to #learning)` : ''));
      await page.setViewportSize({ width: 1440, height: 1050 });
    });

    await check('responsive width 320 shows no horizontal overflow on learning and overview', async () => {
      const measure = async (hash, heading, snapName) => {
        await page.setViewportSize({ width: 320, height: 844 });
        await page.goto(base + hash);
        await visible(heading);
        // Screenshot first: capture the real rendered state regardless of the assertion below.
        await snap(snapName);
        const overflow = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth }));
        let culprit = null;
        if (overflow.scrollWidth > overflow.innerWidth + 1) {
          culprit = await page.evaluate(() => {
            let best = null;
            document.querySelectorAll('a,nav').forEach(el => {
              const r = el.getBoundingClientRect();
              if (r.right > window.innerWidth + 1 && (!best || r.right > best.right)) {
                best = { tag: el.tagName, text: (el.textContent || '').trim().slice(0, 40), right: Math.round(r.right) };
              }
            });
            return best;
          });
        }
        return { overflow, culprit };
      };
      const learning = await measure('/#learning',
        page.getByRole('heading', { level: 1, name: 'Stage: dopamine-dependent learning on the MaleCNS circuit' }),
        'learning-mobile-320');
      const overview = await measure('/#overview',
        page.getByRole('heading', { name: 'A small circuit. A measured result.' }),
        'overview-mobile-320');
      observed.overflow320 = { learning: learning.overflow, overview: overview.overflow };
      observed.overflow320Culprit = { learning: learning.culprit, overview: overview.culprit };
      await page.setViewportSize({ width: 1440, height: 1050 });
      assert.ok(learning.overflow.scrollWidth <= learning.overflow.innerWidth + 1,
        `learning at 320px: scrollWidth ${learning.overflow.scrollWidth} > innerWidth+1 ${learning.overflow.innerWidth + 1}` +
        (learning.culprit ? ` — likely cause: <${learning.culprit.tag}> "${learning.culprit.text}" right edge ${learning.culprit.right}px` : ''));
      assert.ok(overview.overflow.scrollWidth <= overview.overflow.innerWidth + 1,
        `overview at 320px: scrollWidth ${overview.overflow.scrollWidth} > innerWidth+1 ${overview.overflow.innerWidth + 1}` +
        (overview.culprit ? ` — likely cause: <${overview.culprit.tag}> "${overview.culprit.text}" right edge ${overview.culprit.right}px` : ''));
    });

    await check('no page errors and no unexpected console errors/warnings across the whole run', async () => {
      observed.pageErrors = errors;
      observed.consoleMessages = consoleMessages;
      assert.deepEqual(errors, []);
      // Two expected console entries come from the read-only 405 checks above (Chromium's
      // own resource-load failure log for each deliberately-rejected POST); anything else
      // must be genuinely empty.
      assert.deepEqual(consoleMessages.filter(m => !m.expected), []);
    });
  } finally {
    const failed = checks.filter(c => !c.pass);
    fs.writeFileSync(path.join(output, 'evidence.json'), JSON.stringify({
      base, guard, checks, observed,
      requests_summary: { total: requests.length, non_get: requests.filter(r => r.method !== 'GET').length },
      browser: 'Playwright Chromium (bundled)',
      screenshots: fs.readdirSync(output).filter(f => f.endsWith('.png')),
      all_passed: failed.length === 0,
    }, null, 2));
    await browser.close();
    if (failed.length) {
      console.error(`\n${failed.length} check(s) failed:`, failed.map(c => c.name));
      process.exitCode = 1;
    }
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
