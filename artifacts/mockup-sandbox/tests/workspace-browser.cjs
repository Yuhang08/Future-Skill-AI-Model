/* Isolated canvas prototype checks. No learner sessions or records are used.
 * Run: node --experimental-websocket artifacts/mockup-sandbox/tests/workspace-browser.cjs
 */
const assert = require("node:assert/strict");
const fs = require("node:fs"), os = require("node:os"), path = require("node:path");
const { spawn } = require("node:child_process");
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "future-results-design-"));
const browser = spawn("chromium", ["--headless", "--no-sandbox", "--disable-dev-shm-usage",
  "--no-first-run", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const pending = new Map(), errors = [], requests = [];
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
  const response = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true, userGesture: true });
  if (response.exceptionDetails) throw Error(JSON.stringify(response.exceptionDetails));
  return response.result.value;
}
async function wait(expression) {
  for (let i = 0; i < 150; i++) {
    if (await evaluate(expression)) return;
    await pause(100);
  }
  throw Error(`Timed out: ${expression}`);
}
async function section(id) {
  await evaluate(`document.getElementById('rw-tab-${id}').click()`);
  await wait(`document.getElementById('rw-tab-${id}').getAttribute('aria-selected')==='true'`);
  await pause(320);
}
async function pattern(id) {
  await evaluate(`(()=>{const control=document.querySelector('select');control.value=${JSON.stringify(id)};control.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  await pause(150);
}
async function picture(name) {
  const image = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(`/tmp/future-results-design-${name}.png`, Buffer.from(image.data, "base64"));
}
(async () => {
  try {
    const active = path.join(profile, "DevToolsActivePort");
    for (let i = 0; !fs.existsSync(active); i++) {
      if (i > 150 || browser.exitCode !== null) throw Error("Chromium did not start");
      await pause(100);
    }
    const port = fs.readFileSync(active, "utf8").split("\n")[0];
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
    socket = new WebSocket(target.webSocketDebuggerUrl);
    socket.addEventListener("message", event => {
      const message = JSON.parse(event.data);
      if (message.method === "Runtime.exceptionThrown") errors.push(message.params.exceptionDetails);
      if (message.method === "Network.requestWillBeSent") requests.push(message.params.request);
      const callback = pending.get(message.id);
      if (!callback) return;
      clearTimeout(callback.timer); pending.delete(message.id);
      if (message.error) callback.reject(Error(JSON.stringify(message.error)));
      else callback.resolve(message.result);
    });
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", reject, { once: true });
    });
    await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");
    await send("Page.bringToFront"); await send("Emulation.setFocusEmulationEnabled", { enabled: true });
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: `https://${process.env.REPLIT_DEV_DOMAIN}/__mockup/preview/results-workspace/Workspace` });
    await wait("!!document.getElementById('rw-tab-overview')");
    const storage = await evaluate("JSON.stringify({...localStorage})");
    assert.equal(await evaluate("document.querySelectorAll('[role=tab]').length"), 5);
    await picture("overview-desktop");
    await section("interests");
    assert.equal(await evaluate("document.querySelectorAll('.rw-interest-card').length"), 6);
    assert.equal(await evaluate("document.querySelector('.rw-code').textContent"), "RIA");
    assert.match(await evaluate("document.querySelector('[role=tabpanel]').textContent"), /Your answers do not identify a clear leading interest area/);
    assert.equal(await evaluate("new Set([...document.querySelectorAll('.rw-interest-card')].map(el=>Math.round(el.getBoundingClientRect().y))).size"), 1);
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.rw-interest-card [role=meter]')].map(el=>+el.getAttribute('aria-valuenow'))"), Array(6).fill(100));
    await picture("interests-desktop");
    await pattern("equal-low");
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.rw-interest-card [role=meter]')].map(el=>+el.getAttribute('aria-valuenow'))"), Array(6).fill(20));
    for (const sample of ["differentiated", "leading-tie", "mixed"]) {
      await pattern(sample);
      assert.equal(await evaluate("[...document.querySelectorAll('.rw-interest-card [role=meter]')].every(el=>+el.getAttribute('aria-valuenow')%5===0)"), true);
      if (sample === "leading-tie") assert.match(await evaluate("document.querySelector('[role=tabpanel]').textContent"), /tie|tied/i);
    }
    await pattern("mixed");
    for (const id of ["subjects", "confidence"]) {
      await section(id);
      assert.equal(await evaluate("document.querySelectorAll('.rw-scale-card').length"), 6);
      assert.equal(await evaluate("document.querySelectorAll('.rw-scale-card [role=meter]').length"), 6);
      await evaluate("document.querySelector('.rw-mini-disclosure summary').click()");
      assert.equal(await evaluate("document.querySelector('.rw-mini-disclosure').open"), true);
      await picture(`${id}-desktop`);
    }
    await section("careers");
    assert.match(await evaluate("document.querySelector('[role=tabpanel]').textContent"), /no career results|no recommendations/i);
    assert.equal(requests.some(request => /\/api\//.test(request.url)), false);
    console.log("PASS: five sections, all five sample patterns, ties, exact scores, expanded details and honest career empty state");
    await section("overview");
    await evaluate("document.getElementById('rw-tab-overview').focus()");
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "ArrowDown", code: "ArrowDown" });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "ArrowDown", code: "ArrowDown" });
    await wait("document.activeElement.id==='rw-tab-interests'");
    for (const theme of ["dark", "light"]) {
      await evaluate("document.querySelector('.rw-settings').click()");
      await wait("!!document.querySelector('dialog[open]')");
      await evaluate(`[...document.querySelectorAll('dialog button')].find(button=>button.textContent.toLowerCase().includes('${theme} theme')).click()`);
      await wait(`document.documentElement.dataset.futureTheme==='${theme}'`);
      await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
      await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
      await wait("!document.querySelector('dialog[open]')");
      assert.equal(await evaluate("document.activeElement.classList.contains('rw-settings')"), true);
      for (const width of [1440, 1024, 390]) {
        await send("Emulation.setDeviceMetricsOverride", { width, height: 1000, deviceScaleFactor: 1, mobile: width === 390 });
        for (const id of ["overview", "interests", "subjects", "confidence", "careers"]) {
          await section(id);
          assert.equal(await evaluate("document.documentElement.scrollWidth<=innerWidth+1"), true, `${width}/${theme}/${id} overflow`);
          if (id === "interests" && width >= 1024)
            assert.equal(await evaluate("new Set([...document.querySelectorAll('.rw-interest-card')].map(el=>Math.round(el.getBoundingClientRect().y))).size"), 1);
          if (width === 390 && id === "subjects") await picture(`subjects-mobile-${theme}`);
        }
      }
    }
    assert.equal(await evaluate("JSON.stringify({...localStorage})"), storage);
    assert.deepEqual(errors, []);
    console.log("PASS: keyboard tabs, native settings Escape/focus, 1440/1024/390 layouts, light/dark themes, no storage/API writes or runtime errors");
  } finally {
    for (const callback of pending.values()) clearTimeout(callback.timer);
    pending.clear();
    if (socket) socket.close();
    const exited = browser.exitCode !== null ? Promise.resolve() : new Promise(resolve => browser.once("exit", resolve));
    browser.kill("SIGTERM"); await exited; await pause(300);
    await fs.promises.rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 }).catch(() => {});
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
