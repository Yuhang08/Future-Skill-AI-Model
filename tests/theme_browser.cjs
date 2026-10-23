/* Real-app light/dark regression checks. No preview fixtures or npm dependency. */
const assert = require("node:assert/strict");
const fs = require("node:fs"), os = require("node:os"), path = require("node:path");
const { spawn } = require("node:child_process");
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const base = process.env.THEME_TEST_BASE_URL || `https://${process.env.REPLIT_DEV_DOMAIN}`;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "future-live-theme-"));
const browser = spawn("chromium", ["--headless", "--no-sandbox", "--disable-dev-shm-usage",
  "--no-first-run", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const pending = new Map(), exceptions = [];
let socket, serial = 0;
function connect(url) {
  const peer = new WebSocket(url);
  peer.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails);
    const callback = pending.get(message.id);
    if (!callback) return;
    clearTimeout(callback.timer); pending.delete(message.id);
    if (message.error) callback.reject(Error(JSON.stringify(message.error)));
    else callback.resolve(message.result);
  });
  return new Promise((resolve, reject) => {
    peer.addEventListener("open", () => resolve(peer), { once: true });
    peer.addEventListener("error", reject, { once: true });
  });
}
function send(method, params = {}) {
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(Error(`CDP timeout: ${method}`)); }, 20000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true, userGesture: true });
  if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function wait(expression, label) {
  for (let i = 0; i < 200; i++) {
    if (await evaluate(`(()=>{try{return (${expression})}catch(e){if(e instanceof TypeError)return false;throw e}})()`)) return;
    await sleep(100);
  }
  throw Error(`Timed out: ${label || expression}`);
}
async function go(route, page) {
  await send("Page.navigate", { url: base + route });
  await wait(`document.readyState==='complete' && document.documentElement.dataset.futureskillPage===${JSON.stringify(page)} &&
    !!document.querySelector('.fs-site-nav')`, page);
  await evaluate("document.fonts.ready.then(()=>true)");
}
async function capture(name) {
  const image = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(`/tmp/future-live-${name}.png`, Buffer.from(image.data, "base64"));
}
async function checkLayout() {
  assert.equal(await evaluate("!!document.querySelector('.fs-site-brand img[src^=\"/static/futureskill-atom.svg\"]').naturalWidth"), true, "shared atom logo loads");
  assert.equal(await evaluate("[...document.querySelectorAll('.brand-icon img, .brand-mark img, .footer-brand img')].every(img => img.complete && img.naturalWidth > 0 && new URL(img.src).pathname === '/static/futureskill-atom.svg')"), true, "page logos use loaded shared asset");
  assert.equal(await evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), true, "no document overflow");
  assert.equal(await evaluate("document.querySelectorAll('.fs-site-nav').length"), 1);
  assert.equal(await evaluate("document.querySelectorAll('.fs-site-links a[aria-current=page]').length"), 1);
  assert.equal(await evaluate("document.querySelectorAll('.fs-theme-toggle svg:not([hidden])').length"), 1);
  assert.equal(await evaluate("!document.querySelector('.dev-demo-banner') || document.querySelector('.dev-demo-banner').getBoundingClientRect().top >= document.querySelector('.fs-site-nav').getBoundingClientRect().bottom - 1"), true, "development warning must not obscure navigation");
}
async function toggle(expected) {
  await evaluate("document.querySelector('[data-theme-toggle]').click()");
  await wait(`document.documentElement.dataset.futureTheme===${JSON.stringify(expected)}`);
  assert.equal(await evaluate("localStorage.getItem('futureskill-theme-preference')"), expected);
}

(async () => {
  try {
    const active = path.join(profile, "DevToolsActivePort");
    for (let i = 0; !fs.existsSync(active); i++) {
      if (i > 150 || browser.exitCode !== null) throw Error("Chromium did not start");
      await sleep(100);
    }
    const port = fs.readFileSync(active, "utf8").split("\n")[0];
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
    socket = await connect(target.webSocketDebuggerUrl);
    await send("Page.enable"); await send("Runtime.enable");
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
    await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: "dark" }] });
    await go("/", "home");
    assert.equal(await evaluate("FutureSkillTheme.getState().preference"), "system");
    assert.equal(await evaluate("document.documentElement.dataset.futureTheme"), "dark");
    await evaluate("FutureSkillTheme.setPreference('dark')");
    const pages = [
      ["/", "home"],
      ["/__dev/demo/open?demo=1&demo_scenario=dashboard&scenario=dashboard&screen=S10", "reskilling"],
      ["/ai-trend", "trends"], ["/uncertainty", "uncertainty"],
      ["/sdg-impact?career=Data%20Analyst", "sdg"], ["/__dev/screens", "inventory"],
    ];
    for (const [route, page] of pages) {
      await go(route, page);
      assert.equal(await evaluate("document.documentElement.dataset.futureTheme"), "dark", "preference survives navigation");
      if (page === "reskilling") await wait("document.getElementById('dashboard').hidden===false");
      if (page === "sdg") await wait("document.querySelectorAll('.goal-node').length===17");
      if (page === "uncertainty") await wait("document.getElementById('lastValue').textContent==='73.23%'");
      await checkLayout(); await capture(`${page}-dark`);
      await toggle("light"); await checkLayout(); await capture(`${page}-light`);
      await toggle("dark");
      console.log(`PASS: ${page}, real page, both modes, persisted preference and desktop layout`);
    }
    await go("/reskilling?demo=1&demo_scenario=dashboard", "reskilling");
    await wait("!document.getElementById('dashboard').hidden");
    await evaluate("document.querySelector('[data-workspace-action=settings]').click();document.querySelector('#themePreference input[value=light]').click()");
    assert.equal(await evaluate("document.documentElement.dataset.futureTheme"), "light");
    assert.equal(await evaluate("localStorage.getItem('futureskill-theme-preference')"), "light");
    assert.equal(await evaluate("document.getElementById('settingsDialog').open"), true);
    await evaluate("document.querySelector('#themePreference input[value=system]').click()");
    assert.equal(await evaluate("document.documentElement.dataset.futureTheme"), "dark");
    await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: "light" }] });
    await wait("document.documentElement.dataset.futureTheme==='light'");
    assert.equal(await evaluate("localStorage.getItem('futureskill-theme-preference')"), "system");
    assert.equal(await evaluate("document.querySelector('#themePreference input[value=system]').checked"), true);
    await evaluate("document.getElementById('settingsDialog').close();FutureSkillTheme.setPreference('dark')");
    console.log("PASS: existing appearance settings, system theme changes, dialog state");

    // A real second tab must update the first through the browser storage event.
    const original = socket;
    const peerTarget = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
    const peer = await connect(peerTarget.webSocketDebuggerUrl);
    socket = peer;
    await send("Page.enable"); await send("Runtime.enable"); await go("/", "home");
    await evaluate("FutureSkillTheme.setPreference('light')");
    socket = original;
    await wait("document.documentElement.dataset.futureTheme==='light'");
    assert.equal(await evaluate("document.querySelector('#themePreference input[value=light]').checked"), true);
    await send("Target.closeTarget", { targetId: peerTarget.id }); peer.close();
    console.log("PASS: real cross-tab synchronization");

    await go("/uncertainty", "uncertainty");
    await wait("document.getElementById('lastValue').textContent==='73.23%'");
    await wait("!!window.echarts?.getInstanceByDom(document.getElementById('employmentChart'))");
    await evaluate("document.getElementById('preset').value='C';document.getElementById('preset').dispatchEvent(new Event('change'))");
    await wait("document.getElementById('lastValue').textContent==='72.39%'");
    await wait("echarts.getInstanceByDom(document.getElementById('employmentChart')).getOption().series[0].name==='Traditional Economic Boom'");
    assert.deepEqual(await evaluate("echarts.getInstanceByDom(document.getElementById('employmentChart')).getOption().series[0].data.map(point=>[new Date(point[0]).getUTCFullYear(),point[1]])"),
      [[2026,68.9],[2027,69.6],[2028,70.3],[2029,71],[2030,71.7],[2031,72.39]]);
    assert.equal(await evaluate("document.querySelector('.year-values').open"), false);
    await evaluate("FutureSkillTheme.setPreference('dark');document.querySelector('.employment-output').scrollIntoView({block:'center'})");
    await sleep(300); await capture("uncertainty-chart-C-dark");
    await toggle("light"); await sleep(300); await capture("uncertainty-chart-C-light");
    assert.equal(await evaluate("echarts.getInstanceByDom(document.getElementById('employmentChart')).getOption().series[0].data.at(-1)[1]"), 72.39);
    await evaluate("document.querySelector('.year-values').open=true");
    assert.equal(await evaluate("document.querySelectorAll('#yearTable tbody tr').length"), 6);
    assert.match(await evaluate("document.querySelector('#yearTable tbody tr:last-child').textContent"), /72.39/);
    await evaluate("document.getElementById('ai_growth').value='35';document.getElementById('run').click()");
    await wait("document.getElementById('lastValue').textContent!=='72.39%'");
    assert.equal(await evaluate("document.getElementById('chartScenarioName').textContent"), "Traditional Economic Boom · adjusted assumptions");
    await evaluate("document.getElementById('compare').click()");
    await wait("document.querySelectorAll('#compareTable tbody tr').length===6");
    console.log("PASS: chart uses real six-year C series, 72.39%, theme updates, custom inputs and original tables");
    await go("/sdg-impact?career=Data%20Analyst", "sdg");
    await wait("!!document.querySelector('#careerOptions [data-career-id=\"prototype:data-analyst\"]')");
    await evaluate("document.querySelector('#careerOptions [data-career-id=\"prototype:data-analyst\"]').click();document.getElementById('careerForm').requestSubmit()");
    await wait("document.querySelectorAll('.mapping').length===2");
    await evaluate("document.querySelector('.mapping-details-trigger').click();FutureSkillTheme.setPreference('dark')");
    assert.equal(await evaluate("!!document.querySelector('.mapping-drawer[open]')"), true);
    assert.equal(await evaluate("document.querySelector('.mapping-drawer[open] details.evidence-full').open"), false);
    await evaluate("document.querySelector('.mapping-drawer[open] .evidence-node').click()");
    assert.match(await evaluate("document.querySelector('.mapping-drawer[open] .evidence-detail').textContent"), /Illustrative pathway requirement/);
    await capture("sdg-drawer");
    await evaluate("document.querySelector('.mapping-drawer[open]').close()");
    console.log("PASS: real scenario requests, comparisons, SDG drawer and evidence preserved");

    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    for (const [route, page] of pages) {
      await go(route, page); await checkLayout();
      await evaluate("FutureSkillTheme.setPreference('dark')"); await capture(`${page}-mobile-dark`);
      await toggle("light"); await checkLayout(); await capture(`${page}-mobile-light`);
      if (page === "uncertainty") {
        await wait("!!window.echarts?.getInstanceByDom(document.getElementById('employmentChart'))");
        await evaluate("document.querySelector('.employment-output').scrollIntoView({block:'center'})");
        await sleep(300); await capture("uncertainty-chart-mobile");
        assert.equal(await evaluate("document.getElementById('employmentChart').getBoundingClientRect().width <= innerWidth"), true);
      }
      console.log(`PASS: ${page}, mobile dark/light without overflow`);
    }
    // Blocking the CDN must leave the real data table and simulation usable.
    await send("Network.enable");
    await send("Network.setCacheDisabled", { cacheDisabled: true });
    await send("Network.setBlockedURLs", { urls: ["*cdn.jsdelivr.net/npm/echarts*"] });
    await go("/uncertainty", "uncertainty");
    await wait("!document.getElementById('employmentChartStatus').hidden && document.getElementById('employmentChart').hidden");
    await wait("document.querySelectorAll('#yearTable tbody tr').length===6");
    assert.equal(await evaluate("document.querySelector('.year-values').open"), true);
    await evaluate("document.getElementById('preset').value='C';document.getElementById('preset').dispatchEvent(new Event('change'))");
    await wait("document.getElementById('lastValue').textContent==='72.39%'");
    assert.match(await evaluate("document.getElementById('employmentChartStatus').textContent"), /could not be loaded/);
    await send("Network.setBlockedURLs", { urls: [] });
    console.log("PASS: blocked chart library falls back to actual year-by-year model values");
    // Simulate a browser that blocks persistent storage; appearance must still work.
    const override = await send("Page.addScriptToEvaluateOnNewDocument", { source:
      "Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}})" });
    await go("/", "home");
    await evaluate("document.querySelector('[data-theme-toggle]').click()");
    assert.equal(await evaluate("['light','dark'].includes(document.documentElement.dataset.futureTheme)"), true);
    await send("Page.removeScriptToEvaluateOnNewDocument", { identifier: override.identifier });
    assert.deepEqual(exceptions, [], "no uncaught browser errors");
    console.log("PASS: storage-blocked browser remains usable");
    console.log("All real-app theme browser checks passed. Screenshots: /tmp/future-live-*.png");
  } finally {
    socket?.close(); browser.kill("SIGTERM");
    for (const item of pending.values()) clearTimeout(item.timer);
    await sleep(100); fs.rmSync(profile, { recursive: true, force: true, maxRetries: 3 });
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
