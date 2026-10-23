/* End-to-end checks for the interview screen and its contextual FutureSkill links.
 * Uses an isolated Chromium profile and an isolated development demo scenario.
 * No provider calls, saved learner pathways, or real browser histories are touched.
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");
const base = process.env.INTERVIEW_TEST_BASE_URL
  || (process.env.REPLIT_DEV_DOMAIN
    ? `https://${process.env.REPLIT_DEV_DOMAIN}`
    : "http://127.0.0.1:5000");
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "future-interview-ui-"));
const browser = spawn("chromium", [
  "--headless", "--no-sandbox", "--disable-dev-shm-usage", "--no-first-run",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
], { stdio: "ignore" });
const pending = new Map(), errors = [], failedLocalRequests = [];
let socket, serial = 0;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function send(method, params = {}) {
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(Error(`CDP timeout: ${method}`));
    }, 20000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await send("Runtime.evaluate", {
    expression, returnByValue: true, awaitPromise: true, userGesture: true,
  });
  if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function wait(expression, label = expression) {
  for (let count = 0; count < 180; count++) {
    if (await evaluate(expression)) return;
    await sleep(100);
  }
  throw Error(`Timed out waiting for ${label}`);
}

async function go(route, page) {
  await send("Page.navigate", { url: base + route });
  await wait(`document.readyState === "complete" &&
    document.documentElement.dataset.futureskillPage === ${JSON.stringify(page)} &&
    !!document.querySelector(".fs-site-nav")`, route);
}

async function noOverflow(label) {
  const sizes = await evaluate("({width:innerWidth,scrollWidth:document.documentElement.scrollWidth})");
  assert.ok(sizes.scrollWidth <= sizes.width + 2, `${label}: horizontal overflow ${JSON.stringify(sizes)}`);
}

async function checkTheme(theme) {
  await evaluate(`FutureSkillTheme.setPreference(${JSON.stringify(theme)})`);
  await wait(`document.documentElement.dataset.futureTheme === ${JSON.stringify(theme)}`, `${theme} theme`);
  const colors = await evaluate(`({
    canvas:getComputedStyle(document.documentElement).getPropertyValue('--fs-canvas').trim(),
    surface:getComputedStyle(document.querySelector('.interview-panel')).backgroundColor,
    text:getComputedStyle(document.querySelector('.interview-panel')).color
  })`);
  assert.ok(colors.canvas && colors.surface && colors.text, `${theme}: FutureSkill theme tokens applied`);
  return colors;
}

(async () => {
  try {
    const activePort = path.join(profile, "DevToolsActivePort");
    for (let count = 0; !fs.existsSync(activePort); count++) {
      if (count > 150 || browser.exitCode !== null) throw Error("Chromium did not start");
      await sleep(100);
    }
    const port = fs.readFileSync(activePort, "utf8").split("\n")[0];
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {
      method: "PUT",
    })).json();
    socket = new WebSocket(target.webSocketDebuggerUrl);
    socket.addEventListener("message", event => {
      const message = JSON.parse(event.data);
      if (message.method === "Runtime.exceptionThrown") {
        errors.push(message.params.exceptionDetails.text);
      }
      if (message.method === "Network.responseReceived") {
        const response = message.params.response;
        if (response.status >= 400 && response.url.startsWith(base)) {
          failedLocalRequests.push(`${response.status} ${response.url}`);
        }
      }
      if (message.id && pending.has(message.id)) {
        const callback = pending.get(message.id);
        pending.delete(message.id);
        clearTimeout(callback.timer);
        message.error ? callback.reject(Error(JSON.stringify(message.error))) : callback.resolve(message.result);
      }
    });
    await new Promise(resolve => socket.addEventListener("open", resolve, { once: true }));
    await send("Page.enable");
    await send("Runtime.enable");
    await send("Network.enable");
    await send("Emulation.setFocusEmulationEnabled", { enabled: true });

    await send("Emulation.setDeviceMetricsOverride", {
      width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false,
    });
    await go("/interview-practice/", "interview");
    await wait("window.FutureSkillI18n && document.querySelector('#careerCount').textContent.includes('923 careers total')",
      "canonical occupation list");
    assert.equal(await evaluate("document.querySelector('#role').value"), "",
      "no career is auto-selected from alphabetical order");
    assert.equal(await evaluate("document.querySelector('#careerId').value"), "");
    assert.equal(await evaluate("document.querySelector('#start').disabled"), true,
      "practice cannot start without provider configuration");
    assert.equal(await evaluate("document.querySelector('#availabilityNotice').hidden"), false);
    assert.equal(await evaluate("document.querySelector('#availabilityNotice').textContent.trim()"),
      "AI interview practice is temporarily unavailable.");
    assert.equal(await evaluate("document.querySelectorAll('.fs-site-nav').length"), 1,
      "shared FutureSkill navigation is retained");

    const themeLight = await checkTheme("light");
    const themeDark = await checkTheme("dark");
    assert.notEqual(themeLight.canvas, themeDark.canvas, "light and dark canvas tokens differ");
    await checkTheme("light");

    await evaluate(`(() => {
      const input = document.querySelector('#careerSearch');
      input.value = 'Software Developers';
      input.dispatchEvent(new Event('input', {bubbles:true}));
    })()`);
    await wait("document.querySelector('#careerCount').textContent.startsWith('1 matching')");
    assert.equal(await evaluate("document.querySelector('#careerOptions button').textContent"),
      "Software Developers", "search is backed by the canonical catalogue");

    await go("/interview-practice/?career_id=15-1252.00&career=Software%20Developers", "interview");
    await wait("document.querySelector('#careerId').value === '15-1252.00'");
    assert.equal(await evaluate("document.querySelector('#role').value"), "Software Developers");
    assert.equal(await evaluate("document.querySelector('#start').disabled"), true);
    await noOverflow("interview desktop");

    await evaluate(`(() => {
      const dummy = {
        role: 'Browser-only sample',
        overall: 72,
        readiness: {status:'practice_reflection',message:'Test-only copy',evidence_count:1},
        history: [{
          question:'Browser-only sample question',
          answer:'Synthetic answer in a temporary Chromium profile.',
          feedback:{total:72,improvements:['Test only']}
        }]
      };
      localStorage.setItem('futureskill_hr_reports_v2', JSON.stringify([{
        id:'isolated-browser-sample',saved_at:new Date().toISOString(),report:dummy
      }]));
    })()`);
    await go("/interview-practice/?view=history", "interview");
    assert.equal(await evaluate("document.querySelector('#historyPage').classList.contains('hidden')"), false);
    assert.equal(await evaluate("document.querySelector('#savedInterviews').textContent.includes('Browser-only sample')"), true);
    assert.equal(await evaluate("document.querySelector('#savedInterviews').textContent.includes('Synthetic answer')"), true);

    await evaluate(`FutureSkillI18n.setLanguage('zh-CN')`);
    await wait("document.documentElement.lang === 'zh-CN' && document.querySelector('h1').textContent.trim() === '面试练习'");
    assert.equal(await evaluate("document.querySelector('#language').value"), "中文",
      "session feedback language follows saved global preference");
    await evaluate("FutureSkillI18n.setLanguage('ms')");
    await wait("document.documentElement.lang === 'ms'");
    assert.equal(await evaluate("document.querySelector('#language').value"), "Bahasa Melayu");
    await evaluate(`(() => {
      const select=document.querySelector('#language');
      select.value='English';
      select.dispatchEvent(new Event('change',{bubbles:true}));
    })()`);
    await evaluate("FutureSkillI18n.setLanguage('en')");
    await wait("document.documentElement.lang === 'en'");
    assert.equal(await evaluate("document.querySelector('#language').value"), "English",
      "session override does not change with the global language preference");
    assert.equal(await evaluate("document.querySelector('#savedInterviews').textContent.includes('Browser-only sample')"), true,
      "canonical and user-entered report content is not rewritten by the UI translator");

    await send("Emulation.setDeviceMetricsOverride", {
      width: 390, height: 844, deviceScaleFactor: 1, mobile: true,
    });
    await go("/interview-practice/", "interview");
    await wait("document.querySelector('#careerCount').textContent.includes('923 careers total')");
    await noOverflow("interview mobile");
    assert.equal(await evaluate("getComputedStyle(document.querySelector('.interview-fields')).gridTemplateColumns.split(' ').length"), 1,
      "mobile form fields stack into one column");

    await go("/career/15-1252.00", "career-workspace");
    await wait("[...document.querySelectorAll('a')].some(link => link.textContent.includes('Practise for this career'))");
    assert.equal(await evaluate(`(() => {
      const link=[...document.querySelectorAll('a')].find(a=>a.textContent.includes('Practise for this career'));
      const url=new URL(link.href);
      return url.pathname === '/interview-practice/' &&
        url.searchParams.get('career_id') === '15-1252.00' &&
        url.searchParams.get('career') === 'Software Developers';
    })()`), true, "career detail opens practice for the explicit career without altering a pathway");

    await go("/reskilling?demo=1&demo_scenario=dashboard", "reskilling");
    await wait("!!document.querySelector('#interviewPracticeLink') && !document.querySelector('#interviewPracticeCard').hidden",
      "saved-target practice card in isolated demo");
    assert.equal(await evaluate(`(() => {
      const target=appState.profile.target_career;
      const link=new URL(document.querySelector('#interviewPracticeLink').href);
      return target && link.searchParams.get('career') === target;
    })()`), true, "dashboard practice link uses only the saved target");
    assert.equal(await evaluate(`new URL(document.querySelector('.interview-history-link').href).searchParams.get('view')`),
      "history", "history link opens existing browser reports");

    await go("/reskilling?demo=1&demo_scenario=fresh", "reskilling");
    await wait("appState !== null");
    assert.equal(await evaluate("document.querySelector('#interviewPracticeCard').hidden"), true,
      "no saved learner pathway means no target-specific dashboard card");

    assert.deepEqual(errors, [], "no browser JavaScript exceptions");
    assert.deepEqual(failedLocalRequests, [], "no failed local app requests");
    console.log("PASS: interview route, canonical selection, local history, unavailable provider state, bilingual settings, both themes, mobile layout, career-detail entry, and isolated reskilling navigation");
  } finally {
    if (socket?.readyState === WebSocket.OPEN) socket.close();
    browser.kill("SIGTERM");
    fs.rmSync(profile, { recursive: true, force: true });
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
