/* Real Chromium checks against the running app. No extra npm dependency. */
const assert = require("node:assert/strict");
const fs = require("node:fs"), os = require("node:os"), path = require("node:path");
const { spawn } = require("node:child_process");
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const base = process.env.THEME_TEST_BASE_URL || `https://${process.env.REPLIT_DEV_DOMAIN}`;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "future-assessment-"));
const browser = spawn("chromium", ["--headless", "--no-sandbox", "--disable-dev-shm-usage",
  "--no-first-run", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const pending = new Map(), exceptions = [], submitted = [];
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
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true, userGesture: true });
  if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function wait(expression) {
  for (let i = 0; i < 150; i++) {
    if (await evaluate(expression)) return;
    await sleep(100);
  }
  throw Error(`Timed out: ${expression}`);
}
async function go(route = "/") {
  await send("Page.navigate", { url: base + route });
  await wait("document.readyState==='complete' && !!document.querySelector('.fs-site-nav')");
  if (route.startsWith("/reskilling")) await wait("typeof setSteps==='function'");
  else await wait("typeof assessmentProgress!=='undefined'");
}
async function screenshot(name) {
  const image = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(`/tmp/future-assessment-${name}.png`, Buffer.from(image.data, "base64"));
}
async function checkContrast(selector) {
  const ratios = await evaluate(`(()=>{
    const luminance=color=>{const c=color.match(/[\\d.]+/g).slice(0,3).map(Number).map(v=>{
      v/=255;return v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4});
      return c[0]*.2126+c[1]*.7152+c[2]*.0722};
    return [...document.querySelectorAll(${JSON.stringify(selector)})].map(el=>{
      let parent=el,bg;
      while(parent){bg=getComputedStyle(parent).backgroundColor;if(bg!=='rgba(0, 0, 0, 0)'&&bg!=='transparent')break;parent=parent.parentElement}
      const a=luminance(getComputedStyle(el).color), b=luminance(bg);
      return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    });
  })()`);
  assert.ok(ratios.length > 0, `elements exist: ${selector}`);
  assert.ok(ratios.every(ratio => ratio >= 4.5), `contrast >=4.5 for ${selector}: ${ratios}`);
}
async function checkStepInteractionContrast() {
  const { root } = await send("DOM.getDocument");
  const { nodeId } = await send("DOM.querySelector", {
    nodeId: root.nodeId, selector: ".steps .step-label:not(.active)",
  });
  for (const state of ["hover", "focus-visible"]) {
    await send("CSS.forcePseudoState", { nodeId, forcedPseudoClasses: [state] });
    await sleep(250);
    await checkContrast(".steps .step-label, .steps .step-label span");
  }
  await send("CSS.forcePseudoState", { nodeId, forcedPseudoClasses: [] });
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
    socket.addEventListener("message", event => {
      const message = JSON.parse(event.data);
      if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails);
      if (message.method === "Network.requestWillBeSent" &&
          message.params.request.url.endsWith("/api/recommend")) submitted.push(JSON.parse(message.params.request.postData));
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
    await send("DOM.enable"); await send("CSS.enable");
    await send("Page.bringToFront");
    await send("Emulation.setFocusEmulationEnabled", { enabled: true });
    await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
    await go();
    await evaluate("startAssessment()");
    assert.equal(await evaluate("document.querySelectorAll('.question-jump').length"), 24);
    assert.equal(await evaluate("document.getElementById('assessmentQuestionNav').open"), false,
      "numbered navigation is collapsed by default");
    assert.equal(await evaluate("document.getElementById('assessmentQuestionNav').getBoundingClientRect().height < 80"), true,
      "collapsed navigation uses one compact row");
    await evaluate("document.querySelector('#assessmentQuestionNav summary').click()");
    await evaluate("document.querySelector('[data-question-index=\"1\"].question-jump').focus()");
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter",
      windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: "\r", unmodifiedText: "\r" });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter",
      windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 });
    assert.equal(await evaluate("document.activeElement.id"), "assessment-question-0-1",
      JSON.stringify(await evaluate("({focused:document.hasFocus(),tag:document.activeElement.tagName,index:document.activeElement.dataset.questionIndex,current:document.querySelector('.question-jump[aria-current]').dataset.questionIndex})")));
    await evaluate("document.querySelector('input[name=\"0_1\"][value=\"4\"]').click()");
    assert.equal(await evaluate("document.querySelector('.question-jump[data-question-index=\"1\"]').dataset.questionState"), "answered");
    assert.equal(await evaluate("document.getElementById('progressBar').getAttribute('aria-valuenow')"), "1");
    await evaluate("document.querySelector('[data-assessment-part=\"1\"]').click();document.querySelector('input[name=\"1_0\"][value=\"2\"]').click()");
    assert.equal(await evaluate("document.querySelectorAll('.question-jump').length"), 12);
    await go(); await evaluate("startAssessment()");
    assert.equal(await evaluate("currentPart"), 1);
    assert.equal(await evaluate("answers['0_1']"), 4);
    assert.equal(await evaluate("document.querySelector('input[name=\"1_0\"][value=\"2\"]').checked"), true);
    assert.match(await evaluate("document.getElementById('assessmentSaveStatus').textContent"), /restored/);
    console.log("PASS: numbered question jumps, answered states, per-part counts and refresh recovery");

    const saved = await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)");
    await go("/?screen=S02");
    assert.equal(await evaluate("Object.keys(answers).length"), 42);
    await evaluate("document.querySelector('input[name=\"0_0\"][value=\"5\"]').click()");
    assert.equal(await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)"), saved);
    assert.equal(await evaluate("document.getElementById('clearAssessmentDraft').disabled"), true);
    await go(); await evaluate("startAssessment()");
    assert.equal(await evaluate("Object.keys(answers).length"), 2);
    console.log("PASS: development samples cannot overwrite learner drafts");

    await evaluate("document.querySelector('[data-assessment-part=\"2\"]').click();document.querySelectorAll('#questionContainer input[value=\"3\"]').forEach(input=>input.click());document.getElementById('nextButton').click()");
    assert.equal(await evaluate("currentPart"), 0);
    assert.match(await evaluate("document.getElementById('errorMessage').textContent"), /Parts A, B and C/);
    assert.equal(await evaluate("document.activeElement.id"), "assessment-question-0-0");
    assert.equal(await evaluate("document.querySelector('#assessment-question-0-0 [role=radiogroup]').getAttribute('aria-invalid')"), "true");
    assert.match(await evaluate("document.querySelector('#assessment-question-0-0 .question-validation-error').textContent"), /needs an answer/);
    assert.equal(submitted.length, 0);
    await evaluate(`for(let p=0;p<3;p++){assessmentProgress.goToPart(p);document.querySelectorAll('#questionContainer input[value="3"]').forEach(input=>input.click())}`);
    const expected = await evaluate("prepareAssessmentData()");
    await evaluate("document.getElementById('nextButton').click()");
    await wait("document.getElementById('results').style.display==='block'");
    assert.equal(submitted.length, 1);
    assert.deepEqual(submitted[0], expected);
    assert.deepEqual(Object.keys(submitted[0]).sort(), ["answers", "skill_answers", "subject_answers"]);
    console.log("PASS: incomplete sections cannot submit; all 42 answers use the unchanged real recommendation API");

    await go(); await evaluate("startAssessment();currentPart=0;delete answers['0_18'];displayQuestions();document.getElementById('assessmentModal').scrollTop=99999;document.getElementById('nextButton').click()");
    assert.equal(await evaluate("document.activeElement.id"), "assessment-question-0-18",
      "skip in the middle scrolls back to that question, not just the section heading");
    assert.equal(await evaluate("document.querySelector('#assessment-question-0-18').dataset.invalid"), "true");
    assert.equal(await evaluate("document.querySelector('.question-jump[data-question-index=\"18\"] .question-nav-mark').textContent"), "!");
    await evaluate("document.querySelector('input[name=\"0_18\"][value=\"3\"]').click()");
    assert.equal(await evaluate("document.querySelector('#assessment-question-0-18 .question-validation-error')"), null);
    assert.equal(await evaluate("document.querySelector('#assessment-question-0-18 [role=radiogroup]').hasAttribute('aria-invalid')"), false);
    console.log("PASS: skipped middle question is focused and marked; answering clears its error");

    for (const width of [1280, 390]) {
      await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
      await go(); await evaluate("startAssessment();currentPart=0;delete answers['0_0'];displayQuestions()");
      for (const theme of ["light", "dark"]) {
        await evaluate(`FutureSkillTheme.setPreference('${theme}');document.getElementById('assessmentModal').scrollTop=0`);
        await sleep(250); // Allow existing theme colour transitions to settle.
        await checkContrast(".question-jump, [data-assessment-part], .question-state");
        assert.equal(await evaluate("document.getElementById('assessmentQuestionNav').getBoundingClientRect().height < 80"), true);
        assert.equal(await evaluate("document.getElementById('assessmentModal').scrollWidth<=document.getElementById('assessmentModal').clientWidth+1"), true);
        assert.equal(await evaluate("document.getElementById('assessmentModal').getBoundingClientRect().width<=Math.min(780,innerWidth-32)+1"), true,
          "retain the existing modal width rather than redesigning the assessment");
        await screenshot(`home-${width}-${theme}`);
        await evaluate("document.getElementById('assessmentModal').scrollTop=99999;document.getElementById('nextButton').click()");
        assert.equal(await evaluate("document.activeElement.id"), "assessment-question-0-0");
        assert.equal(await evaluate(`(()=>{
          const q=document.getElementById('assessment-question-0-0').getBoundingClientRect();
          const m=document.getElementById('assessmentModal').getBoundingClientRect();
          return q.top>=m.top-1 && q.bottom<=m.bottom+1;
        })()`), true, "first unanswered card is scrolled into the visible modal");
        await checkContrast(".question-validation-error");
        await screenshot(`required-${width}-${theme}`);
        await evaluate("document.querySelector('#assessmentQuestionNav summary').click()");
        assert.equal(await evaluate("document.getElementById('assessmentQuestionNav').open"), true);
        await checkContrast(".question-jump");
        await evaluate("document.querySelector('#assessmentQuestionNav summary').click()");
      }
      await go("/reskilling");
      await wait("!!appState");
      await evaluate("document.getElementById('dashboard').hidden=true;document.getElementById('questionnaire').hidden=false;setSteps(0)");
      for (const theme of ["light", "dark"]) {
        await evaluate(`FutureSkillTheme.setPreference('${theme}');document.getElementById('questionnaire').scrollIntoView({block:'start'})`);
        await sleep(250);
        await checkContrast(".steps .step-label, .steps .step-label span");
        await checkStepInteractionContrast();
        assert.equal(await evaluate("[...document.querySelectorAll('.step-label span')].every(el=>getComputedStyle(el).display!=='none')"), true);
        assert.equal(await evaluate("document.documentElement.scrollWidth<=innerWidth+2"), true);
        await screenshot(`steps-${width}-${theme}`);
      }
    }
    console.log("PASS: compact navigation, required-question auto-scroll, desktop/mobile, light/dark and >=4.5:1 text contrast");

    await go(); await evaluate("startAssessment()");
    const beforeReset = await evaluate("JSON.stringify(answers)");
    const draftBeforeReset = await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)");
    assert.ok(Object.keys(JSON.parse(beforeReset)).length > 0);
    await evaluate("window.confirm=()=>false;document.getElementById('clearAssessmentDraft').click()");
    assert.equal(await evaluate("JSON.stringify(answers)"), beforeReset);
    assert.equal(await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)"), draftBeforeReset);
    await evaluate("window.confirm=()=>true;document.getElementById('clearAssessmentDraft').click()");
    assert.equal(await evaluate("Object.keys(answers).length"), 0);
    assert.equal(await evaluate("localStorage.getItem(FutureSkillAssessmentProgress.DRAFT_KEY)"), null);
    await go(); await evaluate("startAssessment()");
    assert.equal(await evaluate("Object.keys(answers).length"), 0);
    console.log("PASS: cancelled reset preserves answers; confirmed reset removes the saved draft");

    await evaluate("localStorage.setItem(FutureSkillAssessmentProgress.DRAFT_KEY,'{invalid')");
    await go(); await evaluate("startAssessment()");
    assert.equal(await evaluate("Object.keys(answers).length"), 0);
    assert.match(await evaluate("document.getElementById('assessmentSaveStatus').textContent"), /incompatible/);
    const override = await send("Page.addScriptToEvaluateOnNewDocument", { source:
      "Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}})" });
    await go(); await evaluate("startAssessment();document.querySelector('input[name=\"0_0\"][value=\"3\"]').click()");
    assert.equal(await evaluate("answers['0_0']"), 3);
    assert.match(await evaluate("document.getElementById('assessmentSaveStatus').textContent"), /unavailable/);
    await send("Page.removeScriptToEvaluateOnNewDocument", { identifier: override.identifier });
    assert.deepEqual(exceptions, [], "no uncaught browser exceptions");
    console.log("PASS: corrupted drafts and blocked browser storage leave the assessment usable");
    console.log("All assessment browser checks passed. Screenshots: /tmp/future-assessment-*.png");
  } finally {
    socket?.close();
    for (const item of pending.values()) clearTimeout(item.timer);
    if (browser.exitCode === null) {
      await new Promise(resolve => { browser.once("exit", resolve); browser.kill("SIGTERM"); });
    }
    await sleep(300);
    await fs.promises.rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 })
      .catch(error => console.warn(`Temporary browser profile cleanup: ${error.code}`));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
