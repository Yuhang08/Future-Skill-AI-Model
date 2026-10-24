/**
 * Interactive SDG regressions using Chromium's native DevTools protocol.
 * Run with the app workflow serving: node tests/sdg_browser.cjs
 * No npm dependencies. Screenshots and browser profiles stay under /tmp.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const base = process.env.SDG_TEST_BASE_URL ||
  (process.env.REPLIT_DEV_DOMAIN ? `https://${process.env.REPLIT_DEV_DOMAIN}` : 'http://127.0.0.1:5000');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'sdg-browser-'));
const browser = spawn(process.env.CHROMIUM_BIN || 'chromium', [
  '--headless', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
  '--no-first-run', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
  'about:blank',
], { stdio: ['ignore', 'ignore', 'pipe'] });
let browserLog = '';
browser.stderr.on('data', data => { browserLog = (browserLog + data).slice(-4000); });
let socket;
let serial = 0;
const pending = new Map();
const exceptions = [];
const mindmapRequests = [];

function send(method, params = {}) {
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`CDP timeout: ${method}`));
    }, 20000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await send('Runtime.evaluate', {
    expression, awaitPromise: true, returnByValue: true, userGesture: true,
  });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function waitFor(expression, label = expression) {
  for (let i = 0; i < 200; i++) {
    if (await evaluate(expression)) return;
    await sleep(100);
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function activate(selector) {
  await evaluate(`(() => {
    const element = document.querySelector(${JSON.stringify(selector)});
    if (!element) throw new Error('Missing interactive element');
    element.focus(); element.click();
  })()`);
}

async function escapeDialog() {
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await waitFor(`!document.querySelector('dialog[open]')`, 'dialog closed with Escape');
}

async function career(title) {
  await evaluate(`(() => {
    document.getElementById('career').value = ${JSON.stringify(title)};
    document.getElementById('career').dispatchEvent(new Event('input', {bubbles:true}));
  })()`);
  await waitFor(`document.querySelectorAll('#careerOptions [role=option]').length > 0`, `career choices: ${title}`);
  const canonicalTitle = await evaluate(`document.querySelector('#careerOptions .career-option-title').textContent`);
  await activate('#careerOptions [role=option]');
  await evaluate(`document.getElementById('careerForm').requestSubmit()`);
  await waitFor(`document.getElementById('roleTitle')?.textContent === ${JSON.stringify(canonicalTitle)} &&
    !document.getElementById('submitButton').disabled &&
    document.querySelectorAll('.goal-node').length === 17`, `career refreshed: ${title}`);
}

async function typeSearch(title) {
  await evaluate(`document.getElementById('career').focus();document.getElementById('career').value=${JSON.stringify(title)};document.getElementById('career').dispatchEvent(new Event('input',{bubbles:true}))`);
}

async function openGoal(id) {
  await evaluate(`document.getElementById('allGoals').open=true`);
  await activate(`.goal-node[data-sdg-id="${id}"]`);
  await waitFor(`document.getElementById('goalInfoDialog').open`, `shared evidence drawer for goal ${id}`);
  assert.equal(await evaluate(`document.querySelector('dialog[open]').id`), 'goalInfoDialog');
  assert.equal(await evaluate(`document.querySelectorAll('dialog.mapping-drawer').length`), 1,
    'all goals and target cards reuse one native evidence drawer');
  assert.equal(await evaluate(`!!document.querySelector('#goalInfoDialog .drawer-visual') &&
    !!document.querySelector('#goalInfoDialog .mapping-content') &&
    !!document.querySelector('#goalInfoDialog .limit-box') &&
    !!document.querySelector('#goalInfoDialog .action-box')`), true);
  assert.equal(await evaluate(`document.querySelector('#goalInfoDialog .goal-definition').textContent.includes(goals[${id - 1}][2])`), true);
}

async function key(key, code, virtualKey, text) {
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key, code, windowsVirtualKeyCode: virtualKey,
    nativeVirtualKeyCode: virtualKey, ...(text ? { text, unmodifiedText: text } : {}) });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key, code, windowsVirtualKeyCode: virtualKey,
    nativeVirtualKeyCode: virtualKey });
}

async function checkTextContrast(selector) {
  const ratios = await evaluate(`(()=>{
    const luminance=color=>{const rgb=color.match(/[\\d.]+/g).slice(0,3).map(Number).map(v=>{
      v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});
      return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722};
    return [...document.querySelectorAll(${JSON.stringify(selector)})].map(el=>{
      let parent=el,bg;
      while(parent){bg=getComputedStyle(parent).backgroundColor;if(bg!=='rgba(0, 0, 0, 0)'&&bg!=='transparent')break;parent=parent.parentElement}
      const a=luminance(getComputedStyle(el).color),b=luminance(bg);
      return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    });
  })()`);
  assert.ok(ratios.length > 0 && ratios.every(ratio => ratio >= 4.5),
    `readable text contrast for ${selector}: ${ratios}`);
}

async function capture(name) {
  await sleep(250);
  const image = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(`/tmp/${name}.png`, Buffer.from(image.data, 'base64'));
}

(async () => {
  try {
    const activePort = path.join(profile, 'DevToolsActivePort');
    for (let i = 0; !fs.existsSync(activePort); i++) {
      if (i >= 150 || browser.exitCode !== null) throw new Error(`Chromium did not start: ${browserLog}`);
      await sleep(100);
    }
    const port = fs.readFileSync(activePort, 'utf8').split('\n')[0];
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
    socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', reject, { once: true });
    });
    socket.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
      if (message.method === 'Network.requestWillBeSent' &&
          message.params.request.url.endsWith('/api/sdg/mindmap') &&
          message.params.request.method === 'POST') {
        mindmapRequests.push(JSON.parse(message.params.request.postData));
      }
      const item = pending.get(message.id);
      if (!item) return;
      clearTimeout(item.timer);
      pending.delete(message.id);
      if (message.error) item.reject(new Error(JSON.stringify(message.error)));
      else item.resolve(message.result);
    });
    await send('Page.enable');
    await send('Runtime.enable');
    await send('Network.enable');
    await send('Page.bringToFront');
    await send('Emulation.setFocusEmulationEnabled', { enabled: true });
    await send('Emulation.setDeviceMetricsOverride', {
      width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false,
    });
    await send('Page.navigate', { url: `${base}/sdg-impact?career=Data%20Analyst` });
    await waitFor(`document.querySelectorAll('.goal-node').length === 17 &&
      document.querySelector('#careerOptions [role=option]')`, 'initial independent goals and career suggestion');
    assert.equal(await evaluate(`document.getElementById('allGoals').open`), false);
    await evaluate(`document.querySelector('#allGoals > summary').focus()`);
    await key('Enter', 'Enter', 13, '\r');
    assert.equal(await evaluate(`document.getElementById('allGoals').open`), true,
      'the complete list expands with native keyboard activation');
    assert.equal(await evaluate(`!!document.querySelector('#mapLines, .mindmap-stage')`), false);
    assert.equal(await evaluate(`document.querySelectorAll('#goalGrid [role=listitem]').length`), 17);
    for (let id=1; id<=17; id++) {
      await openGoal(id);
      assert.match(await evaluate(`document.querySelector('#goalInfoDialog .goal-evidence-status').textContent`), /No career selected/);
      assert.equal(await evaluate(`!!document.querySelector('#goalInfoDialog a[href*="onetonline.org"]')`), false);
      await escapeDialog();
      assert.equal(await evaluate(`document.activeElement.dataset.sdgId`), String(id));
    }
    console.log('PASS: collapsed list expands by keyboard; all 17 unselected goals share the rich drawer and restore focus');
    assert.equal(await evaluate(`document.getElementById('submitButton').disabled`), true);
    assert.equal(await evaluate(`document.querySelectorAll('.mapping').length`), 0);
    await evaluate(`document.getElementById('career').focus()`);
    await waitFor(`document.querySelector('#careerOptions [role=option]')`, 'initial exact suggestion');
    await key('ArrowDown', 'ArrowDown', 40);
    assert.equal(await evaluate(`document.getElementById('career').getAttribute('aria-activedescendant')`), 'career-option-0');
    await key('Enter', 'Enter', 13, '\r');
    assert.equal(await evaluate(`careerSearch.selection().id`), 'prototype:data-analyst');
    await evaluate(`document.getElementById('careerForm').requestSubmit()`);
    await waitFor(`document.getElementById('reviewStatus').textContent.includes('0 task-target') &&
      !document.getElementById('results').hidden &&
      !document.getElementById('submitButton').disabled`, 'prototype role without official O*NET task ID');
    assert.deepEqual(mindmapRequests.at(-1), { career_id: 'prototype:data-analyst' });
    assert.equal(await evaluate(`document.querySelectorAll('.mapping').length`), 0);
    assert.equal(await evaluate(`document.querySelectorAll('.goal-node.linked').length`), 0);
    assert.equal(await evaluate(`document.querySelector('.goal-node[data-sdg-id="9"]').classList.contains('tentative')`), true);
    assert.equal(await evaluate(`document.querySelector('#candidateSuggestions').hidden`), false);
    assert.equal(await evaluate(`document.querySelector('#learningContribution').hidden`), false);
    assert.match(await evaluate(`document.getElementById('candidateList').textContent`), /Goal 9/);
    assert.match(await evaluate(`document.getElementById('candidateList').textContent`), /CLASSIFICATION-ONLY GUESS/);
    assert.match(await evaluate(`document.getElementById('learningContributionList').textContent`), /Target 4\.4/);
    assert.match(await evaluate(`document.getElementById('learningContributionList').textContent`), /Target 8\.5/);
    assert.equal(await evaluate(`document.getElementById('pathway').hidden`), false,
      'the existing pathway must remain available without an occupational target match');
    assert.equal(await evaluate(`document.querySelectorAll('#skillsList .skill-row').length`), 6);
    assert.match(await evaluate(`document.querySelector('#assessmentStatus a').getAttribute('href')`), /career=Data%20Analyst/);
    await waitFor(`Array.from(document.querySelectorAll('.goal-node img')).every(img => img.complete && img.naturalWidth > 0)`, 'all 17 official goal icons');
    assert.equal(await evaluate(`document.querySelector('details.about').open`), false);
    console.log('PASS: prototype has a classification-only suggestion, never a task-backed claim');

    await openGoal(9);
    assert.match(await evaluate(`document.querySelector('#goalInfoDialog .goal-evidence-status').textContent`), /Classification-only guess/);
    assert.equal(await evaluate(`!!document.querySelector('#goalInfoDialog a[href*="/prototype"]')`), false,
      'a prototype ID must not become an invented O*NET occupation URL');
    await escapeDialog();
    assert.equal(await evaluate(`document.activeElement.dataset.sdgId`), '9');
    const analyst = await evaluate(`fetch('/api/sdg/mindmap',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({career_id:'prototype:data-analyst'})}).then(r=>r.json())`);
    for (const mapping of analyst.learning_pathway_mappings) {
      await openGoal(mapping.sdg_id);
      const copy = await evaluate(`document.querySelector('#goalInfoDialog .pathway-evidence').textContent`);
      for (const statement of mapping.supporting_evidence) assert.ok(copy.includes(statement));
      assert.ok(copy.includes(mapping.relevance_reason));
      assert.ok(copy.includes(mapping.impact_limitations));
      assert.ok(copy.includes(mapping.user_action));
      const ids = await evaluate(`[...document.querySelectorAll('#goalInfoDialog .pathway-evidence [data-source-id]')].map(a=>a.dataset.sourceId)`);
      assert.deepEqual(ids, mapping.evidence_source.map(source=>source.id));
      assert.match(await evaluate(`document.querySelector('#goalInfoDialog .goal-evidence-status').textContent`), /missing evidence|No occupational Target/);
      await capture(`sdg-pathway-evidence-${mapping.sdg_id}-desktop`);
      if (mapping.sdg_id===4) {
        await send('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:true});
        assert.equal(await evaluate(`document.getElementById('goalInfoDialog').scrollWidth<=document.getElementById('goalInfoDialog').clientWidth+1`),true);
        await capture('sdg-pathway-evidence-4-mobile');
        await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
      }
      await escapeDialog();
    }
    console.log('PASS: Goal 4/8 drawers retain exact separate pathway rationale, skills/practice, sources, limitations and actions');
    await send('Emulation.setDeviceMetricsOverride', {
      width: 390, height: 844, deviceScaleFactor: 1, mobile: true,
    });
    await sleep(200);
    assert.equal(await evaluate(`document.documentElement.scrollWidth <= window.innerWidth + 1`), true);
    assert.equal(await evaluate(`getComputedStyle(document.getElementById('goalGrid')).gridTemplateColumns.split(' ').length`), 1);
    await capture('sdg-no-task-evidence-mobile');
    console.log('PASS: no-evidence mobile layout');

    await career('Environmental Engineer');
    const environment = await evaluate(`fetch('/api/sdg/mindmap',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({career_id:'17-2081.00'})}).then(r=>r.json())`);
    assert.equal(environment.career_id, '17-2081.00');
    assert.equal(environment.goal_scores.length, 17);
    assert.equal(await evaluate(`document.querySelectorAll('.goal-rank-card').length`), 3);
    assert.deepEqual(await evaluate(`[...document.querySelectorAll('.rank-number')].map(x=>x.textContent)`),
      environment.top_goal_scores.map(score=>`${score.relevance_index}/100`));
    assert.equal(await evaluate(`document.querySelectorAll('.goal-rank-evidence[open]').length`), 0);
    await activate('.goal-rank-evidence summary');
    const firstScore = environment.top_goal_scores[0];
    for (const task of firstScore.task_evidence)
      assert.ok((await evaluate(`document.querySelector('.goal-rank-evidence').textContent`)).includes(task.task));
    assert.equal(await evaluate(`document.querySelector('.goal-rank-evidence .sources a').href`), firstScore.occupation_source);
    await activate('.all-goal-scores summary');
    assert.equal(await evaluate(`document.querySelectorAll('.goal-score-line').length`), 17);
    assert.equal(await evaluate(`document.querySelectorAll('.goal-score-line [role=meter]').length`), 17);
    for (const width of [1440,390]) {
      await send('Emulation.setDeviceMetricsOverride', {width,height:1000,deviceScaleFactor:1,mobile:width<600});
      const backgrounds = [];
      for (const theme of ['light','dark']) {
        await evaluate(`FutureSkillTheme.setPreference(${JSON.stringify(theme)});document.getElementById('taskGoalRankings').scrollIntoView({behavior:'instant',block:'start'})`);
        assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth+1`), true);
        await checkTextContrast('.goal-rank-card h3, .score-review-status');
        backgrounds.push(await evaluate(`getComputedStyle(document.querySelector('.goal-rank-card')).backgroundColor`));
        await capture(`sdg-task-ranking-${width}-${theme}`);
        await evaluate(`document.getElementById('allGoals').open=true;document.getElementById('allGoals').scrollIntoView({behavior:'instant',block:'start'})`);
        await checkTextContrast('.goal-name, .goal-node-status');
        assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth+1`), true);
        await capture(`sdg-goals-list-${width}-${theme}`);
      }
      assert.notEqual(backgrounds[0],backgrounds[1],'new ranking cards follow the shared theme');
    }
    console.log('PASS: real task-based Top 3 and all 17 indices match the API; source tasks, disclosure, mobile and both themes');

    await career('Solar Energy Systems Engineers');
    const solar = await evaluate(`fetch('/api/sdg/mindmap',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({career_id:'17-2199.11'})}).then(r=>r.json())`);
    assert.ok(solar.mappings.length>0,'use a genuine strict task-rule candidate for drawer checks');
    assert.equal(await evaluate(`document.querySelectorAll('.mapping').length`),solar.mappings.length);
    await activate('.mapping-details-trigger');
    await waitFor(`!!document.querySelector('.mapping-drawer[open]')`,'task evidence drawer');
    await activate('.mapping-drawer[open] .evidence-node');
    assert.equal(await evaluate(`document.querySelector('.mapping-drawer[open] .evidence-detail').textContent`),solar.mappings[0].supporting_evidence[0]);
    const sourceLinks = await evaluate(`[...document.querySelectorAll('.mapping-drawer[open] [data-source-id]')].map(x=>({id:x.dataset.sourceId,url:x.getAttribute('href')}))`);
    for (const source of solar.mappings[0].evidence_source)
      assert.ok(sourceLinks.some(link=>link.id===source.id && link.url===source.url));
    assert.match(await evaluate(`document.querySelector('.mapping-drawer[open]').textContent`),/human review|Human review/);
    for (const [width,label] of [[1440,'desktop'],[390,'mobile']]) {
      await send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<600});
      assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth+1`),true);
      await capture(`sdg-drawer-${label}`);
    }
    await escapeDialog();
    assert.equal(await evaluate(`document.activeElement.classList.contains('mapping-details-trigger')`),true);
    console.log('PASS: target drawer wording, task IDs, source IDs and focus restoration match real API records');
    for (let id=1; id<=17; id++) {
      await openGoal(id);
      const score = solar.goal_scores.find(entry=>entry.sdg_id===id);
      const copy = await evaluate(`document.querySelector('#goalInfoDialog .goal-ranking-evidence:not(.goal-definition)').textContent`);
      assert.ok(copy.includes(`${score.relevance_index}/100`));
      for (const task of score.task_evidence) {
        assert.ok(copy.includes(`Task ID ${task.task_id}`));
        assert.ok(copy.includes(task.task));
      }
      await checkTextContrast('#goalInfoDialog .drawer-visual-copy h3, #goalInfoDialog .drawer-visual-copy p');
      assert.equal(await evaluate(`document.getElementById('goalInfoDialog').scrollWidth <= document.getElementById('goalInfoDialog').clientWidth+1`), true);
      await escapeDialog();
      assert.equal(await evaluate(`document.activeElement.dataset.sdgId`), String(id));
    }
    console.log('PASS: every occupational Goal opens the same drawer with exact API task evidence and unchanged numeric values');
    for (const width of [1440,390]) {
      await send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<600});
      for (const theme of ['light','dark']) {
        await evaluate(`FutureSkillTheme.setPreference(${JSON.stringify(theme)})`);
        await openGoal(7);
        assert.equal(await evaluate(`document.getElementById('goalInfoDialog').scrollWidth<=document.getElementById('goalInfoDialog').clientWidth+1`),true);
        await checkTextContrast('#goalInfoDialog .goal-evidence-status, #goalInfoDialog .pathway-evidence p');
        await key('Tab','Tab',9);
        assert.equal(await evaluate(`!!document.activeElement.closest('#goalInfoDialog')`),true);
        await capture(`sdg-unified-evidence-${width}-${theme}`);
        await escapeDialog();
      }
    }
    console.log('PASS: shared occupational evidence drawer is responsive in both themes and retains modal keyboard focus');

    // Browser-only missing-source fixture; no application data or source CSV is changed.
    const missing = {...solar, goal_scores:[],top_goal_scores:[],mappings:[],candidate_mappings:[],
      task_data_status:'not_installed',task_profile:{representative_tasks:[],occupation_task_count:0}};
    await evaluate(`window.__sdgOriginalFetch=window.fetch;
      window.fetch=(url,options)=>String(url)==='/api/sdg/mindmap'
        ? Promise.resolve(new Response(${JSON.stringify(JSON.stringify(missing))},{status:200,headers:{'Content-Type':'application/json'}}))
        : window.__sdgOriginalFetch(url,options);
      document.getElementById('careerForm').requestSubmit()`);
    await waitFor(`!document.getElementById('submitButton').disabled && document.getElementById('taskGoalRankings').hidden`, 'explicit missing-source state');
    await openGoal(1);
    assert.match(await evaluate(`document.querySelector('#goalInfoDialog .goal-evidence-status').textContent`), /not installed/);
    assert.equal(await evaluate(`document.querySelectorAll('#goalInfoDialog .task-score-evidence').length`), 0);
    await escapeDialog();
    await evaluate(`window.fetch=window.__sdgOriginalFetch;delete window.__sdgOriginalFetch`);
    console.log('PASS: missing occupational source is explicit, with no invented task evidence or ranking');
    await career('Environmental Engineer');
    assert.match(await evaluate(`document.getElementById('candidateList').textContent`), /Goal 13/);
    assert.equal(await evaluate(`document.getElementById('pathway').hidden`), true);
    await career('Software Developer');
    assert.equal(await evaluate(`document.querySelector('.goal-node[data-sdg-id="4"]').classList.contains('linked')`), false);
    assert.equal(await evaluate(`document.querySelector('.goal-node[data-sdg-id="8"]').classList.contains('linked')`), false);
    assert.match(await evaluate(`document.getElementById('learningContributionList').textContent`), /Target 4\.4/);
    console.log('PASS: career switching never turns FutureSkill learning links into occupation evidence');

    await send('Network.setBlockedURLs', { urls: ['*/api/sdg/mindmap'] });
    await evaluate(`document.getElementById('careerForm').requestSubmit()`);
    await waitFor(`document.querySelectorAll('.retry').length === 1 &&
      !document.getElementById('submitButton').disabled`, 'API failure state');
    assert.equal(await evaluate(`document.getElementById('results').hidden`), false);
    assert.equal(await evaluate(`document.querySelectorAll('.goal-node').length`), 17);
    await send('Network.setBlockedURLs', { urls: [] });
    await activate('.retry');
    await waitFor(`document.querySelectorAll('.goal-node').length === 17 &&
      !document.getElementById('submitButton').disabled`, 'successful retry');
    await typeSearch('the invalid');
    await waitFor(`document.getElementById('careerOptions').textContent.includes('No matching careers')`, 'unknown career no-results state');
    const attemptsBeforeInvalid = mindmapRequests.length;
    await evaluate(`document.getElementById('careerForm').requestSubmit()`);
    assert.match(await evaluate(`document.getElementById('message').textContent`), /Select a supported career/);
    assert.equal(await evaluate(`document.getElementById('submitButton').disabled`), true);
    assert.equal(await evaluate(`document.getElementById('roleTitle').textContent`), 'Explore all 17 goals');
    assert.equal(mindmapRequests.length, attemptsBeforeInvalid);
    assert.equal(await evaluate(`document.querySelectorAll('.goal-node.linked').length`), 0);
    console.log('PASS: arbitrary text cannot select a career, make a model request, or receive fallback links');

    await typeSearch('analyst');
    await waitFor(`document.querySelectorAll('#careerOptions [role=option]').length > 1`, 'ambiguous search choices');
    await key('Enter', 'Enter', 13, '\r');
    assert.equal(await evaluate(`careerSearch.selection()`), null);
    assert.equal(await evaluate(`document.getElementById('submitButton').disabled`), true);
    await key('Escape', 'Escape', 27);
    assert.equal(await evaluate(`document.getElementById('careerOptions').hidden`), true);
    assert.equal(await evaluate(`document.activeElement.id`), 'career');
    await key('ArrowDown', 'ArrowDown', 40);
    await waitFor(`!document.getElementById('careerOptions').hidden && !!document.querySelector('#careerOptions [role=option]')`, 'reopened search options');
    await key('ArrowDown', 'ArrowDown', 40);
    await key('Enter', 'Enter', 13, '\r');
    assert.equal(await evaluate(`!!careerSearch.selection()`), true);
    await typeSearch('enviromental engineer');
    assert.equal(await evaluate(`careerSearch.selection()`), null);
    await waitFor(`document.querySelector('#careerOptions [data-career-id="17-2081.00"]')`, 'fuzzy suggestion');
    await key('Enter', 'Enter', 13, '\r');
    assert.equal(await evaluate(`careerSearch.selection()`), null, 'a spelling suggestion is not silently selected');
    console.log('PASS: native keyboard selection, Escape, ambiguous/fuzzy choices and edit invalidation');

    await send('Network.setBlockedURLs', { urls: ['*/api/sdg/careers?*'] });
    await typeSearch('environmental');
    await waitFor(`document.getElementById('careerOptions').textContent.includes('Career search failed')`, 'career-search network failure');
    assert.equal(await evaluate(`document.getElementById('submitButton').disabled`), true);
    await send('Network.setBlockedURLs', { urls: [] });
    await career('Environmental Engineer');
    assert.equal(await evaluate(`document.getElementById('roleTitle').textContent`), 'Environmental Engineers');
    await openGoal(1);
    await typeSearch('Data Analyst');
    assert.equal(await evaluate(`document.getElementById('goalInfoDialog').open`), false,
      'invalidating a career closes stale occupational evidence');
    console.log('PASS: search network failure is explicit and a later real search recovers');

    // Deliberately reverse two search responses. The response bodies come from
    // the real API; only the delivery order is controlled in this race check.
    const searchBodies = await evaluate(`Promise.all(['Environmental Engineer','Data Analyst'].map(q=>fetch('/api/sdg/careers?q='+encodeURIComponent(q)).then(r=>r.json())))`);
    await evaluate(`window.__sdgOriginalFetch=window.fetch;window.__sdgDelayed={};
      window.fetch=(url,options)=>String(url).startsWith('/api/sdg/careers?')
        ?new Promise(resolve=>{window.__sdgDelayed[new URL(url,location.href).searchParams.get('q')]=resolve})
        :window.__sdgOriginalFetch(url,options)`);
    await typeSearch('Environmental Engineer');
    await typeSearch('Data Analyst');
    await evaluate(`window.__sdgDelayed['Data Analyst'](new Response(${JSON.stringify(JSON.stringify(searchBodies[1]))},{status:200,headers:{'Content-Type':'application/json'}}))`);
    await waitFor(`!!document.querySelector('#careerOptions [data-career-id="prototype:data-analyst"]')`, 'latest search response');
    await evaluate(`window.__sdgDelayed['Environmental Engineer'](new Response(${JSON.stringify(JSON.stringify(searchBodies[0]))},{status:200,headers:{'Content-Type':'application/json'}}))`);
    await sleep(150);
    assert.equal(await evaluate(`!!document.querySelector('#careerOptions [data-career-id="prototype:data-analyst"]')`), true);
    assert.equal(await evaluate(`!!document.querySelector('#careerOptions [data-career-id="17-2081.00"]')`), false);
    await evaluate(`window.fetch=window.__sdgOriginalFetch;delete window.__sdgOriginalFetch;delete window.__sdgDelayed`);
    console.log('PASS: stale search responses cannot replace newer choices');

    for (const width of [1280, 390]) {
      await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
      for (const theme of ['light', 'dark']) {
        await evaluate(`FutureSkillTheme.setPreference(${JSON.stringify(theme)})`);
        await typeSearch('environmental engineering');
        await waitFor(`!!document.querySelector('#careerOptions [role=option]')`, 'long occupational title');
        await sleep(250);
        await checkTextContrast('.career-option-title, .career-option-status, #roleTitle');
        assert.equal(await evaluate(`document.documentElement.scrollWidth <= innerWidth + 1`), true);
        assert.equal(await evaluate(`[...document.querySelectorAll('#careerOptions [role=option]')].every(el=>el.getBoundingClientRect().height>=44)`), true);
        await capture(`sdg-search-${width}-${theme}`);
      }
    }
    console.log('PASS: long titles, mapping-status labels and dropdown layout in both themes on desktop/mobile');
    assert.deepEqual(exceptions, []);
    console.log('PASS: network failure, retry, input validation, and no uncaught browser errors');
    console.log('All SDG browser checks passed. Open-state screenshots: /tmp/sdg-drawer-{desktop,mobile}.png');
  } finally {
    if (socket) socket.close();
    const exited = browser.exitCode === null
      ? new Promise(resolve=>browser.once('exit',resolve)) : Promise.resolve();
    browser.kill('SIGTERM');
    for (const item of pending.values()) clearTimeout(item.timer);
    await exited;
    try {
      await fs.promises.rm(profile, {recursive:true,force:true,maxRetries:5,retryDelay:100});
    } catch (error) {
      console.warn('Temporary Chromium profile cleanup:',error.code);
    }
  }
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
