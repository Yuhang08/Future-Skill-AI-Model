/* Source-based theme checks using Chromium CDP, with no npm test dependency. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const base = process.env.THEME_TEST_BASE_URL || `https://${process.env.REPLIT_DEV_DOMAIN}`;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "future-theme-browser-"));
const browser = spawn("chromium", ["--headless", "--no-sandbox", "--disable-dev-shm-usage",
  "--no-first-run", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"],
  { stdio: "ignore" });
const pending = new Map();
const exceptions = [], liveApiRequests = [];
let socket, serial = 0;
function send(method, params = {}) {
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(Error(`CDP timeout: ${method}`)); }, 20000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const value = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true, userGesture: true });
  if (value.exceptionDetails) throw Error(JSON.stringify(value.exceptionDetails));
  return value.result.value;
}
async function wait(expression, label) {
  for (let count = 0; count < 200; count++) {
    // An iframe briefly has an empty document during navigation. Retry read-only
    // selector predicates then; application exceptions are tracked separately.
    if (await evaluate(`(() => {try {return (${expression});} catch (error) {
      if (error instanceof TypeError) return false; throw error;
    }})()`)) return;
    await sleep(100);
  }
  throw Error(`Timed out: ${label || expression}`);
}
const D = "document.querySelector('.fs-source-frame').contentDocument";
const W = "document.querySelector('.fs-source-frame').contentWindow";
const inner = code => evaluate(`(() => {const d=${D};const w=${W}; ${code}})()`);
async function screenshot(name) {
  await sleep(150);
  const image = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(`/tmp/future-theme-${name}.png`, Buffer.from(image.data, "base64"));
}
async function navigate(page) {
  await send("Page.navigate", { url: `${base}/__mockup/preview/future-theme/${page}` });
  await wait(`document.querySelector('.fs-source-frame')?.contentDocument?.readyState === 'complete' &&
    document.querySelector('.fs-source-frame').contentDocument.documentElement.dataset.previewPage`, page);
  await inner("return d.fonts.ready.then(()=>true)");
  await sleep(180);
}
async function toggle() {
  await evaluate("document.querySelector('.fs-mode-toggle').click()");
  await wait(`${D}?.documentElement.dataset.futureTheme === document.querySelector('.fs-preview').dataset.mode`);
}
async function noOverflow() {
  assert.equal(await evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), true, "preview chrome overflow");
  assert.equal(await inner("return d.documentElement.scrollWidth <= d.documentElement.clientWidth + 2"), true, "page overflow");
  assert.equal(await evaluate("document.querySelector('.fs-source-frame').getBoundingClientRect().height > 250"), true);
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
    socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", reject, { once: true });
    });
    socket.addEventListener("message", event => {
      const item = JSON.parse(event.data);
      if (item.method === "Runtime.exceptionThrown") exceptions.push(item.params.exceptionDetails);
      if (item.method === "Network.requestWillBeSent" && new URL(item.params.request.url).pathname.startsWith("/api/")) {
        liveApiRequests.push(item.params.request.url);
      }
      const handler = pending.get(item.id);
      if (!handler) return;
      clearTimeout(handler.timer); pending.delete(item.id);
      if (item.error) handler.reject(Error(JSON.stringify(item.error)));
      else handler.resolve(item.result);
    });
    await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });

    const entries = ["Assessment", "Reskilling", "Trends", "Dark", "Sdg"];
    for (const entry of entries) {
      await navigate(entry);
      if (entry === "Reskilling") await wait(`${D}.getElementById('dashboard')?.hidden === false`, "sample dashboard");
      if (entry === "Dark") await wait(`${D}.getElementById('lastValue')?.textContent === '73.23%'`, "formula output");
      if (entry === "Sdg") await wait(`${D}.querySelectorAll('.goal-node').length === 17`, "17 goals");
      for (const mode of ["dark", "light"]) {
        if (await evaluate("document.querySelector('.fs-preview').dataset.mode") !== mode) await toggle();
        assert.equal(await inner(`return d.documentElement.dataset.futureTheme`), mode);
        await noOverflow();
        await screenshot(`${entry}-${mode}`);
      }
      console.log(`PASS: ${entry} desktop, dark/light, source content and no overflow`);
    }
    await inner("d.querySelector('.mapping-details-trigger').click();w.__themeSentinel='preserved';return true");
    await wait(`${D}.querySelector('.mapping-drawer[open]') !== null`, "SDG drawer");
    assert.equal(await inner("return Array.from(d.querySelectorAll('.mapping-drawer[open] .evidence-node')).every(b=>b.scrollWidth<=b.clientWidth+1)"), true, "evidence labels fit");
    await toggle();
    assert.equal(await inner("return w.__themeSentinel"), "preserved");
    assert.equal(await inner("return !!d.querySelector('.mapping-drawer[open]')"), true);
    assert.equal(await inner("return d.querySelector('.mapping-drawer[open] details.evidence-full').open"), false);
    assert.equal(await inner("return d.querySelectorAll('.goal-node.linked').length"), 2);
    await inner("d.querySelector('.mapping-drawer[open] .evidence-node').click();return true");
    assert.match(await inner("return d.querySelector('.mapping-drawer[open] .evidence-detail').textContent"), /Illustrative pathway requirement/);
    await screenshot("sdg-drawer");
    await inner("d.querySelector('.mapping-drawer[open]').close();d.getElementById('career').value='Environmental Engineer';d.getElementById('careerForm').requestSubmit();return true");
    await wait(`${D}.getElementById('mapCareerName')?.textContent === 'Environmental Engineer' && ${D}.querySelectorAll('.goal-node').length===17`);
    assert.equal(await inner("return d.querySelectorAll('.mapping').length"), 0);
    assert.equal(await inner("return d.querySelectorAll('.goal-node.linked').length"), 0);
    console.log("PASS: theme switch preserves drawer/state, full evidence stays collapsed, no invented links");

    await navigate("Dark");
    await wait(`${D}.getElementById('lastValue')?.textContent === '73.23%'`);
    await inner("d.getElementById('ai_growth').value='35';d.getElementById('run').click();return true");
    await wait(`${D}.getElementById('lastValue').textContent !== '73.23%'`);
    await inner("d.getElementById('compare').click();return true");
    await wait(`${D}.querySelectorAll('#compareTable tbody tr').length===6`);
    await inner("d.querySelector('header a').click();return true");
    await wait("document.querySelector('.fs-preview').dataset.page==='home'", "inner navigation");
    await wait(`${D}.documentElement.dataset.previewPage==='home' &&
      Array.from(${D}.querySelectorAll('button')).some(b=>b.textContent.includes('Start Career Assessment'))`, "assessment source ready");
    await inner("Array.from(d.querySelectorAll('button')).find(b=>b.textContent.includes('Start Career Assessment')).click();return true");
    await wait(`getComputedStyle(${D}.querySelector('.overlay')).display!=='none'`, "assessment modal");
    await toggle();
    assert.notEqual(await inner("return w.getComputedStyle(d.querySelector('.overlay')).display"), "none");
    console.log("PASS: scenario controls/comparison, source navigation and assessment modal");

    // Inspect real source inventory and its sample results route.
    await evaluate("Array.from(document.querySelectorAll('.fs-preview-nav button')).find(b=>b.textContent==='Screen inventory').click()");
    await wait(`${D}.querySelector('a[href="/?screen=S05"]') !== null`);
    await noOverflow(); await screenshot("inventory");
    await inner("d.querySelector('a[href=\"/?screen=S05\"]').click();return true");
    await wait(`${D}.getElementById('results')?.style.display==='block'`, "labeled sample results");
    assert.equal(await inner("return d.querySelectorAll('.dev-inventory-banner').length"), 1);
    await screenshot("sample-results");
    console.log("PASS: inventory review and labeled sample assessment results");

    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    for (const entry of entries) {
      await navigate(entry);
      if (entry === "Sdg") await wait(`${D}.querySelectorAll('.goal-node').length===17`);
      await noOverflow();
      assert.notEqual(await evaluate("getComputedStyle(document.querySelector('.fs-preview-status')).display"), "none", "preview status visible on mobile");
      await screenshot(`${entry}-mobile-dark`);
      await toggle(); await noOverflow();
      await screenshot(`${entry}-mobile-light`);
      console.log(`PASS: ${entry} mobile, both modes`);
    }
    await navigate("Current");
    assert.equal(await inner("return d.querySelectorAll('style').length > 0"), true);
    assert.equal(await inner("return d.documentElement.dataset.futureTheme"), "current");
    assert.equal(await evaluate("document.querySelector('.fs-mode-toggle') === null"), true);
    assert.deepEqual(liveApiRequests, [], "no requests reached real learner APIs");
    assert.deepEqual(exceptions, [], "no uncaught browser errors");
    console.log("All theme-preview checks passed. Screenshots: /tmp/future-theme-*.png");
  } finally {
    socket?.close(); browser.kill("SIGTERM");
    for (const item of pending.values()) clearTimeout(item.timer);
    await sleep(100);
    fs.rmSync(profile, { recursive: true, force: true, maxRetries: 3 });
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
