/* Real Chromium checks for local language packs, Settings and learner-state preservation.
 * node --experimental-websocket tests/language_browser.cjs
 */
const assert = require("node:assert/strict"), fs = require("node:fs");
const os = require("node:os"), path = require("node:path"), { spawn } = require("node:child_process");
const base = process.env.LANGUAGE_TEST_BASE_URL || `https://${process.env.REPLIT_DEV_DOMAIN}`;
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "future-language-"));
const browser = spawn("chromium", ["--headless", "--no-sandbox", "--disable-dev-shm-usage",
  "--no-first-run", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const pending = new Map(), exceptions = [], requests = [];
let socket, serial = 0;
function send(method, params = {}) {
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(Error(`CDP timeout: ${method}`)); }, 20000);
    pending.set(id, { resolve, reject, timer }); socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const response = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true, userGesture: true });
  if (response.exceptionDetails) throw Error(JSON.stringify(response.exceptionDetails));
  return response.result.value;
}
async function wait(expression) {
  for (let attempt = 0; attempt < 150; attempt++) {
    if (await evaluate(expression)) return;
    await pause(100);
  }
  throw Error(`Timed out: ${expression}`);
}
async function go(route) {
  await send("Page.navigate", { url: base + route });
  await wait("document.readyState==='complete' && !!window.FutureSkillI18n && !!document.getElementById('fsSettingsButton')");
  await evaluate("FutureSkillI18n.ready");
  if (route.includes("report-demo")) await wait("!!document.querySelector('.report-summary') && !document.getElementById('reportDemoScenario').disabled");
}
async function language(code) {
  await evaluate(`FutureSkillI18n.setLanguage(${JSON.stringify(code)})`);
  await wait(`document.documentElement.lang===${JSON.stringify(code)} && FutureSkillI18n.getLanguage()===${JSON.stringify(code)}`);
  await pause(80);
}
async function settings() {
  await evaluate("document.getElementById('fsSettingsButton').click()");
  await wait("document.getElementById('fsSettingsDialog').open");
}
async function picture(name) {
  const image = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(`/tmp/future-language-${name}.png`, Buffer.from(image.data, "base64"));
}
(async () => {
  try {
    const active = path.join(profile, "DevToolsActivePort");
    for (let attempt = 0; !fs.existsSync(active); attempt++) {
      if (attempt > 150 || browser.exitCode !== null) throw Error("Chromium did not start");
      await pause(100);
    }
    const port = fs.readFileSync(active, "utf8").split("\n")[0];
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
    socket = new WebSocket(target.webSocketDebuggerUrl);
    socket.addEventListener("message", event => {
      const message = JSON.parse(event.data);
      if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails);
      if (message.method === "Network.requestWillBeSent") requests.push(message.params.request);
      const callback = pending.get(message.id);
      if (!callback) return;
      clearTimeout(callback.timer); pending.delete(message.id);
      if (message.error) callback.reject(Error(JSON.stringify(message.error)));
      else callback.resolve(message.result);
    });
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true }); socket.addEventListener("error", reject, { once: true });
    });
    await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");
    await send("Page.bringToFront"); await send("Emulation.setFocusEmulationEnabled", { enabled: true });
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await go("/"); assert.equal(await evaluate("FutureSkillI18n.getLanguage()"), "en");
    const englishHome = await evaluate("document.querySelector('#homePage h1').textContent");
    await settings();
    assert.deepEqual(await evaluate("[...document.querySelectorAll('#fsLanguageSelect option')].map(el=>el.value)"), ["en", "zh-CN", "ms"]);
    await evaluate("document.getElementById('fsLanguageSelect').value='zh-CN';document.getElementById('fsLanguageSelect').dispatchEvent(new Event('change',{bubbles:true}))");
    await wait("FutureSkillI18n.getLanguage()==='zh-CN'");
    assert.notEqual(await evaluate("document.querySelector('#homePage h1').textContent"), englishHome);
    assert.equal(await evaluate("localStorage.getItem('futureskill-language-preference')"), "zh-CN");
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await wait("!document.getElementById('fsSettingsDialog').open");
    assert.equal(await evaluate("document.activeElement.id"), "fsSettingsButton");
    await language("ms"); await language("en");
    assert.equal(await evaluate("document.querySelector('#homePage h1').textContent"), englishHome);
    console.log("PASS browser: Settings, Chinese/Malay/English switching, persistence, Escape and restored focus");

    await evaluate("startAssessment();document.querySelector('input[name=\"0_0\"][value=\"4\"]').click()");
    const answersBefore = await evaluate("JSON.stringify(answers)");
    let draftBefore = await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)");
    const questionBefore = await evaluate("document.querySelector('.question-title').textContent");
    for (const code of ["zh-CN", "ms", "en"]) {
      const beforeSwitchDraft = await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)");
      await language(code);
      assert.equal(await evaluate("JSON.stringify(answers)"), answersBefore);
      assert.equal(await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)"), beforeSwitchDraft);
      assert.equal(await evaluate("document.querySelector('input[name=\"0_0\"][value=\"4\"]').checked"), true);
      const questionNow = await evaluate("document.querySelector('.question-title').textContent");
      if (code === "en") assert.equal(questionNow, questionBefore);
      else assert.notEqual(questionNow, questionBefore);
      await evaluate("assessmentProgress.goToPart(1)");
      if (code !== "en") assert.doesNotMatch(await evaluate("document.querySelector('.question-title').textContent"), /Developing software/);
      await evaluate("assessmentProgress.goToPart(0)");
    }
    await evaluate("closeAssessment()");
    draftBefore = await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)");
    console.log("PASS browser: all locales on an open assessment and dynamically rerendered questions preserve answers/drafts/values");

    await go("/?report-demo=equal-high");
    const reportValues = await evaluate("[...document.querySelectorAll('#userProfile [role=meter]')].map(el=>el.getAttribute('aria-valuenow'))");
    const originalSummary = await evaluate("document.querySelector('.report-summary').textContent");
    const paths = await evaluate("[...document.querySelectorAll('#careerResults a')].map(el=>el.getAttribute('href'))");
    for (const code of ["zh-CN", "ms", "en"]) {
      await language(code);
      assert.deepEqual(await evaluate("[...document.querySelectorAll('#userProfile [role=meter]')].map(el=>el.getAttribute('aria-valuenow'))"), reportValues);
      assert.deepEqual(await evaluate("[...document.querySelectorAll('#careerResults a')].map(el=>el.getAttribute('href'))"), paths);
      const summary = await evaluate("document.querySelector('.report-summary').textContent");
      if (code === "en") assert.equal(summary, originalSummary);
      else assert.notEqual(summary, originalSummary);
      assert.equal(await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)"), draftBefore);
    }
    console.log("PASS browser: dynamic results translate reversibly while scores, ranking links and saved learner draft stay unchanged");

    await language("ms");
    for (const route of ["/ai-trend", "/uncertainty", "/sdg-impact", "/reskilling"]) {
      await go(route);
      assert.equal(await evaluate("FutureSkillI18n.getLanguage()"), "ms");
      assert.notEqual(await evaluate("document.querySelector('.fs-site-links a').textContent"), "Career assessment");
      if (route === "/ai-trend") assert.notEqual(await evaluate("document.querySelector('h1').textContent"), "AI Career Trend Explorer");
      if (route === "/uncertainty") assert.notEqual(await evaluate("document.querySelector('h1').textContent"), "AI Uncertainty Lab");
    }
    await wait("!!document.getElementById('fsWorkspaceLanguageSelect')");
    await evaluate("document.querySelector('[data-workspace-action=\"settings\"]').click()");
    assert.equal(await evaluate("document.getElementById('settingsDialog').open"), true);
    await evaluate("document.getElementById('fsWorkspaceLanguageSelect').value='zh-CN';document.getElementById('fsWorkspaceLanguageSelect').dispatchEvent(new Event('change',{bubbles:true}))");
    await wait("FutureSkillI18n.getLanguage()==='zh-CN'");
    assert.equal(await evaluate("document.getElementById('fsLanguageSelect').value"), "zh-CN");
    await go("/"); assert.equal(await evaluate("FutureSkillI18n.getLanguage()"), "zh-CN");
    console.log("PASS browser: preference survives page navigation/reload and existing reskilling Settings uses the same language preference");

    for (const width of [1440, 390]) {
      await send("Emulation.setDeviceMetricsOverride", { width, height: 1000, deviceScaleFactor: 1, mobile: width < 700 });
      for (const theme of ["light", "dark"]) {
        await evaluate(`FutureSkillTheme.setPreference('${theme}')`);
        for (const code of ["en", "zh-CN", "ms"]) {
          await language(code); await settings(); await pause(180);
          assert.equal(await evaluate("document.documentElement.scrollWidth<=innerWidth+2"), true);
          assert.equal(await evaluate("document.getElementById('fsSettingsDialog').scrollWidth<=document.getElementById('fsSettingsDialog').clientWidth+2"), true);
          assert.equal(await evaluate("Math.abs(document.getElementById('fsSettingsButton').getBoundingClientRect().top-document.querySelector('[data-theme-toggle]').getBoundingClientRect().top)<5"), true,
            "Settings and theme controls stay in the same navigation row");
          await picture(`${width}-${theme}-${code}`);
          await evaluate("document.getElementById('fsSettingsDialog').close()");
        }
      }
    }
    console.log("PASS browser: all three language Settings layouts at desktop/mobile widths in both themes without horizontal overflow");

    await evaluate("localStorage.setItem('futureskill-language-preference','unsupported')");
    await go("/"); assert.equal(await evaluate("FutureSkillI18n.getLanguage()"), "en");
    const override = await send("Page.addScriptToEvaluateOnNewDocument", { source:
      "Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}})" });
    await go("/"); await settings();
    await evaluate("document.getElementById('fsLanguageSelect').value='ms';document.getElementById('fsLanguageSelect').dispatchEvent(new Event('change',{bubbles:true}))");
    await wait("FutureSkillI18n.getLanguage()==='ms'");
    await wait("document.getElementById('fsLanguageStatus').textContent.length>0");
    assert.equal(await evaluate("FutureSkillI18n.getState().persistence"), "blocked");
    await send("Page.removeScriptToEvaluateOnNewDocument", { identifier: override.identifier });
    assert.deepEqual(exceptions, []);
    console.log("PASS browser: invalid saved preference defaults to English; blocked storage gives explicit notice without breaking switching");
    console.log("All language browser checks passed. Screenshots: /tmp/future-language-*.png");
  } finally {
    socket?.close(); for (const item of pending.values()) clearTimeout(item.timer);
    if (browser.exitCode === null) await new Promise(resolve => { browser.once("exit", resolve); browser.kill("SIGTERM"); });
    await pause(300);
    await fs.promises.rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 }).catch(error => console.warn(error.code));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
