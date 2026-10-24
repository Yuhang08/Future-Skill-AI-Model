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
  await waitFor(`document.getElementById('mapCareerName')?.textContent === ${JSON.stringify(canonicalTitle)} &&
    !document.getElementById('submitButton').disabled &&
    document.querySelectorAll('.goal-node').length === 17`, `career refreshed: ${title}`);
}

async function typeSearch(title) {
  await evaluate(`document.getElementById('career').focus();document.getElementById('career').value=${JSON.stringify(title)};document.getElementById('career').dispatchEvent(new Event('input',{bubbles:true}))`);
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
    assert.equal(await evaluate(`document.getElementById('submitButton').disabled`), true);
    assert.equal(await evaluate(`document.querySelectorAll('.mapping').length`), 0);
    await evaluate(`document.getElementById('career').focus()`);
    await waitFor(`document.querySelector('#careerOptions [role=option]')`, 'initial exact suggestion');
    await key('ArrowDown', 'ArrowDown', 40);
    assert.equal(await evaluate(`document.getElementById('career').getAttribute('aria-activedescendant')`), 'career-option-0');
    await key('Enter', 'Enter', 13, '\r');
    assert.equal(await evaluate(`careerSearch.selection().id`), 'prototype:data-analyst');
    await evaluate(`document.getElementById('careerForm').requestSubmit()`);
    await waitFor(`document.getElementById('reviewStatus').textContent.includes('NO TASK-BACKED MATCH') &&
      !document.getElementById('results').hidden &&
      !document.getElementById('submitButton').disabled`, 'prototype role without official O*NET task ID');
    assert.deepEqual(mindmapRequests.at(-1), { career_id: 'prototype:data-analyst' });
    assert.equal(await evaluate(`document.querySelectorAll('.mapping').length`), 0);
    assert.equal(await evaluate(`document.querySelectorAll('.goal-node.linked').length`), 0);
    assert.equal(await evaluate(`document.querySelectorAll('#mapLines line').length`), 0);
    assert.equal(await evaluate(`document.querySelector('#candidateSuggestions').hidden`), false);
    assert.equal(await evaluate(`document.querySelector('#learningContribution').hidden`), false);
    assert.match(await evaluate(`document.getElementById('candidateList').textContent`), /Goal 9/);
    assert.match(await evaluate(`document.getElementById('learningContributionList').textContent`), /Target 4\.4/);
    assert.match(await evaluate(`document.getElementById('learningContributionList').textContent`), /Target 8\.5/);
    await waitFor(`Array.from(document.querySelectorAll('.goal-node img')).every(img => img.complete && img.naturalWidth > 0)`, 'all 17 official goal icons');
    assert.equal(await evaluate(`document.querySelector('details.about').open`), false);
    console.log('PASS: prototype has no fabricated O*NET evidence; broad guess and training outcomes are separate');

    await activate('.goal-node[data-sdg-id="9"]');
    await waitFor(`document.getElementById('goalInfoDialog').open`, 'goal is not misleadingly highlighted');
    assert.match(await evaluate(`document.getElementById('goalInfoCopy').textContent`), /No reviewed career-to-target link/);
    await escapeDialog();
    assert.equal(await evaluate(`document.activeElement.dataset.sdgId`), '9');
    await send('Emulation.setDeviceMetricsOverride', {
      width: 390, height: 844, deviceScaleFactor: 1, mobile: true,
    });
    await sleep(200);
    assert.equal(await evaluate(`document.documentElement.scrollWidth <= window.innerWidth + 1`), true);
    await capture('sdg-no-task-evidence-mobile');
    console.log('PASS: no-evidence mobile layout');

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
    assert.equal(await evaluate(`document.getElementById('mapCareerName').textContent`), 'Choose a supported career');
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
    assert.equal(await evaluate(`document.getElementById('mapCareerName').textContent`), 'Environmental Engineers');
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
        await checkTextContrast('.career-option-title, .career-option-status, #mapCareerName');
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
    browser.kill('SIGTERM');
    for (const item of pending.values()) clearTimeout(item.timer);
    await sleep(250);
    fs.rmSync(profile, { recursive: true, force: true, maxRetries: 3 });
  }
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
