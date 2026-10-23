/* Actual Chromium interactions against the running app; temporary profile only.
 * Run: node --experimental-websocket tests/assessment_report_browser.cjs
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");
const base = process.env.REPORT_TEST_BASE_URL || `https://${process.env.REPLIT_DEV_DOMAIN}`;
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "future-report-browser-"));
const browser = spawn("chromium", ["--headless", "--no-sandbox", "--disable-dev-shm-usage",
  "--no-first-run", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const pending = new Map(), requests = [], exceptions = [];
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
  for (let attempt = 0; attempt < 150; attempt++) {
    if (await evaluate(expression)) return;
    await pause(100);
  }
  throw Error(`Timed out: ${expression}`);
}
async function go(route) {
  await send("Page.navigate", { url: base + route });
  await wait("document.readyState==='complete' && typeof FutureSkillReport!=='undefined'");
  if (route.includes("report-demo=")) {
    await wait("!document.getElementById('reportDemoScenario').disabled && !!document.querySelector('#userProfile section')");
  }
}
async function metrics(width) {
  await send("Emulation.setDeviceMetricsOverride", { width, height: 1000, deviceScaleFactor: 1, mobile: width < 700 });
}
async function screenshot(name) {
  const result = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(`/tmp/future-report-${name}.png`, Buffer.from(result.data, "base64"));
}
async function contrast() {
  const measurements = await evaluate(`(() => {
    const luminance = color => {
      const values = color.match(/[\\d.]+/g).slice(0,3).map(Number).map(v => {
        v /= 255; return v <= .04045 ? v / 12.92 : ((v+.055)/1.055)**2.4;
      });
      return values[0]*.2126 + values[1]*.7152 + values[2]*.0722;
    };
    return [...document.querySelectorAll('#userProfile h2,#userProfile h3,.report-summary p,.report-meter-label,.report-meter-value,.report-activity,.report-citation,.report-question,.report-evidence,.report-details summary,.report-ai-notice,.report-actions a,.report-actions button')]
      .filter(el => el.getClientRects().length).map(el => {
        let parent=el,bg;
        while(parent) {
          bg=getComputedStyle(parent).backgroundColor;
          if(bg!=='rgba(0, 0, 0, 0)' && bg!=='transparent') break;
          parent=parent.parentElement;
        }
        const a=luminance(getComputedStyle(el).color), b=luminance(bg);
        return {text:el.textContent.slice(0,45),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
      });
  })()`);
  assert.ok(measurements.length > 40);
  assert.deepEqual(measurements.filter(item => item.ratio < 4.5), [], "report text contrast >=4.5:1");
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
      if (message.method === "Network.requestWillBeSent") {
        const request = message.params.request;
        requests.push({ id: message.params.requestId, url: request.url, method: request.method, body: request.postData });
      }
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
    await send("Page.bringToFront");
    await send("Emulation.setFocusEmulationEnabled", { enabled: true });
    await metrics(1440);
    await go("/");
    assert.equal(await evaluate("getComputedStyle(document.getElementById('reportDemoControl')).display"), "none");
    await evaluate("startAssessment();document.querySelector('input[name=\"0_0\"][value=\"4\"]').click();document.querySelector('input[name=\"0_1\"][value=\"2\"]').click()");
    const savedDraft = await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)");
    assert.ok(savedDraft);

    for (const scenario of ["equal-high", "equal-low", "differentiated", "leading-tie", "mixed"]) {
      await go(`/?report-demo=${scenario}`);
      const values = await evaluate("[...document.querySelectorAll('#userProfile [role=meter]')].map(el=>Number(el.getAttribute('aria-valuenow')))");
      assert.equal(values.length, 18);
      if (scenario.startsWith("equal-")) {
        const high = scenario === "equal-high";
        assert.deepEqual(values, [...Array(6).fill(high ? 100 : 20), ...Array(12).fill(high ? 5 : 1)]);
        assert.match(await evaluate("document.querySelector('.report-summary').textContent"),
          /Your answers do not identify a clear leading interest area\./);
        assert.equal(await evaluate("document.querySelector('.report-code strong').textContent"), "RIA");
        await evaluate("document.querySelector('#report-interests details summary').click()");
        assert.match(await evaluate("document.querySelector('#report-interests details').textContent"), /R–I–A–S–E–C/);
      }
      if (scenario === "leading-tie") assert.match(await evaluate("document.querySelector('.report-summary').textContent"), /tied: Realistic, Investigative/);
      assert.equal(await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)"), savedDraft);
      assert.equal(await evaluate("document.querySelectorAll('.report-interest .report-source-link').length"), 6);
      assert.equal(await evaluate("document.querySelectorAll('#report-subjects .report-question').length"), 6);
      assert.equal(await evaluate("document.querySelectorAll('#report-confidence .report-evidence').length"), 6);
      const recommendationRequest = requests.filter(req => req.url.endsWith("/api/recommend")).at(-1);
      const response = await send("Network.getResponseBody", { requestId: recommendationRequest.id });
      const actual = JSON.parse(response.body);
      const headings = await evaluate("[...document.querySelectorAll('#careerResults > .career-card > h3')].map(el=>el.textContent)");
      assert.deepEqual(headings, actual.recommendations.map((career, index) => `${index+1}. ${career.title}`));
      const cardValues = await evaluate("[...document.querySelectorAll('#careerResults .match-score')].map(el=>el.textContent)");
      assert.deepEqual(cardValues, actual.recommendations.map(career => `Match Index: ${career.match_index.toFixed(2)}`));
      assert.equal(await evaluate("[...document.querySelectorAll('#results a[href^=\"/reskilling\"]')].every(el=>el.href.includes('demo=1'))"), true);
      console.log(`PASS browser: ${scenario}, exact scores, real recommendation order, sources, activities, isolated drafts`);
    }

    const scoreBefore = await evaluate("[...document.querySelectorAll('#userProfile [role=meter]')].map(el=>el.getAttribute('aria-valuenow'))");
    await evaluate("document.querySelector('.report-details summary').focus()");
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
    assert.equal(await evaluate("document.querySelector('.report-details').open"), true);
    assert.notEqual(await evaluate("getComputedStyle(document.activeElement).outlineStyle"), "none");
    await evaluate("document.querySelector('.report-button').click()");
    assert.equal(await evaluate("Object.keys(answers).length"), 42);
    assert.equal(await evaluate("document.getElementById('clearAssessmentDraft').disabled"), true);
    await evaluate("document.querySelector('input[name=\"0_0\"][value=\"1\"]').click()");
    assert.equal(await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)"), savedDraft);
    await evaluate("closeAssessment()");
    assert.equal(await evaluate("document.getElementById('results').style.display"), "block");
    assert.deepEqual(await evaluate("[...document.querySelectorAll('#userProfile [role=meter]')].map(el=>el.getAttribute('aria-valuenow'))"), scoreBefore);
    console.log("PASS browser: keyboard accordion/focus, filled answer review, edits never overwrite learner draft or existing scores");

    const beforeInvalid = requests.filter(req => req.url.endsWith("/api/recommend")).length;
    await go("/?report-demo=invalid");
    assert.equal(await evaluate("document.querySelectorAll('#userProfile [role=meter]').length"), 0);
    assert.match(await evaluate("document.querySelector('#userProfile [role=alert]').textContent"), /incomplete|range/);
    assert.equal(requests.filter(req => req.url.endsWith("/api/recommend")).length, beforeInvalid);
    assert.match(await evaluate("document.getElementById('resultsPathwayLink').href"), /demo=1/);
    await go("/?report-demo=mixed");
    await evaluate("document.querySelector('.report-careers-link').click()");
    assert.equal(await evaluate("location.hash"), "#careerRecommendationsHeading");
    await wait("Math.abs(document.getElementById('careerRecommendationsHeading').getBoundingClientRect().top)<200");
    await evaluate("document.querySelector('#report-methodology details summary').click()");
    assert.match(await evaluate("document.querySelector('#report-methodology').textContent"), /Skills are not ranking inputs/);
    assert.match(await evaluate("document.querySelector('.report-ai-notice').textContent"), /unavailable/);
    assert.equal(requests.some(req => /openai|\/api\/.*explanation|\/api\/.*review/.test(req.url)), false);
    assert.equal(requests.filter(req => req.method !== "GET" && !req.url.endsWith("/api/recommend")).length, 0);
    console.log("PASS browser: invalid data fails explicitly, career anchor works, AI unavailable without calls or fake output");

    for (const width of [1440, 390]) {
      await metrics(width);
      await go("/?report-demo=equal-high");
      for (const theme of ["light", "dark"]) {
        await evaluate(`FutureSkillTheme.setPreference('${theme}')`);
        await pause(400);
        assert.equal(await evaluate("document.documentElement.scrollWidth<=innerWidth+2"), true);
        await contrast();
        await screenshot(`${width}-${theme}-overview`);
        await evaluate("document.getElementById('report-interests').scrollIntoView({behavior:'instant'})");
        await screenshot(`${width}-${theme}-interests`);
        await evaluate("document.getElementById('report-subjects').scrollIntoView({behavior:'instant'})");
        await screenshot(`${width}-${theme}-subjects`);
        await evaluate("document.getElementById('report-confidence').scrollIntoView({behavior:'instant'})");
        await screenshot(`${width}-${theme}-confidence`);
        console.log(`PASS browser: ${width}px ${theme}, no overflow, >=4.5:1 text contrast and report screenshots`);
      }
    }
    await go("/"); await evaluate("startAssessment()");
    assert.equal(await evaluate("Object.keys(answers).length"), 2);
    await evaluate(`for(let p=0;p<3;p++){assessmentProgress.goToPart(p);document.querySelectorAll('#questionContainer input[value=\"3\"]').forEach(input=>input.click())}document.getElementById('nextButton').click()`);
    await wait("document.getElementById('results').style.display==='block' && document.querySelectorAll('#userProfile [role=meter]').length===18");
    assert.equal(await evaluate("getComputedStyle(document.getElementById('reportDemoControl')).display"), "none");
    assert.equal(await evaluate("[...document.querySelectorAll('#results a[href^=\"/reskilling\"]')].every(el=>!el.href.includes('demo=1'))"), true);
    const normalDraft = await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)");
    await evaluate("document.querySelector('.report-button').click()");
    assert.equal(await evaluate("Object.keys(answers).length"), 42);
    assert.equal(await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)"), normalDraft);
    console.log("PASS browser: normal assessment submission and review preserve all answers; normal pathways are not demos");

    await go("/?report-demo=mixed");
    await evaluate("document.querySelector('#careerResults a[href^=\"/reskilling\"]').click()");
    await wait("location.pathname==='/reskilling' && typeof setSteps==='function'");
    assert.equal(await evaluate("new URLSearchParams(location.search).get('demo')"), "1");
    console.log("PASS browser: real recommendation opens isolated reskilling flow");
    assert.deepEqual(exceptions, [], "no uncaught browser exceptions");
    console.log("All results browser checks passed; screenshots in /tmp/future-report-*.png. No actual LLM calls made.");
  } finally {
    socket?.close();
    for (const entry of pending.values()) clearTimeout(entry.timer);
    if (browser.exitCode === null) {
      await new Promise(resolve => { browser.once("exit", resolve); browser.kill("SIGTERM"); });
    }
    // Chromium's child processes may still flush the profile after the parent exits.
    // Async cleanup lets those processes finish and must not mask a failed assertion.
    await pause(300);
    await fs.promises.rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 })
      .catch(error => console.warn(`Temporary browser profile cleanup: ${error.code}`));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
