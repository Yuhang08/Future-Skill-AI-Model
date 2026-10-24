/* Local translation-pack and engine checks. No real browser or learner data. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const packs = Object.fromEntries(["en", "zh-CN", "ms"].map(code =>
  [code, JSON.parse(fs.readFileSync(`src/static/locales/${code}.json`, "utf8"))]));
const names = text => [...text.matchAll(/\{([a-zA-Z][a-zA-Z0-9]*)\}/g)].map(match => match[1]).sort();
const keySet = Object.keys(packs.en).sort();
for (const [code, pack] of Object.entries(packs)) {
  assert.deepEqual(Object.keys(pack).sort(), keySet, `${code}: matching language-pack keys`);
  for (const key of keySet) {
    assert.equal(typeof pack[key], "string");
    assert.ok(pack[key].trim(), `${code}: nonempty ${key}`);
    assert.deepEqual(names(pack[key]), names(key), `${code}: preserve interpolation slots for ${key}`);
  }
}
console.log(`PASS: ${keySet.length} matching, nonempty language-pack entries with consistent placeholders`);

const source = fs.readFileSync("src/static/index.html", "utf8");
const match = source.match(/const assessmentParts = (\[[\s\S]*?\n\]);/);
assert.ok(match, "existing assessment question data found");
const parts = vm.runInNewContext(match[1]);
assert.equal(parts.reduce((sum, part) => sum + part.questions.length, 0), 42);
for (const code of ["zh-CN", "ms"]) {
  for (const part of parts) {
    for (const [, question] of part.questions) {
      assert.ok(packs[code][question], `${code}: question has a local translation: ${question}`);
      assert.notEqual(packs[code][question], question);
    }
  }
}
console.log("PASS: all 42 original assessment questions have Chinese and Malay translations");

function engine({ blocked = false, fail = false, delayed, saved = {}, start = false } = {}) {
  const stored = new Map(Object.entries(saved));
  const element = { nodeType: 1, childNodes: [], hasAttribute: () => false, closest: () => null };
  const document = {
    readyState: start ? "complete" : "loading", body: element, documentElement: {},
    addEventListener() {}, getElementById: () => null, querySelectorAll: () => [],
  };
  const window = { dispatchEvent() {}, addEventListener() {} };
  const localStorage = {
    getItem: key => { if (blocked) throw Error("blocked"); return stored.get(key) || null; },
    setItem: (key, value) => { if (blocked) throw Error("blocked"); stored.set(key, value); },
  };
  const fetch = async url => {
    const code = url.match(/\/([^/]+)\.json/)[1];
    if (delayed && code === "zh-CN") await delayed;
    return { ok: !fail, json: async () => packs[code] };
  };
  const context = { window, document, localStorage, fetch, console, setTimeout, clearTimeout,
    MutationObserver: class { observe() {} },
    CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options?.detail; } } };
  vm.runInNewContext(fs.readFileSync("src/static/future-i18n.js", "utf8"), context);
  return { api: window.FutureSkillI18n, document, stored };
}
(async () => {
  const migrated = engine({ saved: { futureskill_language: "zh" }, start: true });
  await migrated.api.ready;
  assert.equal(migrated.api.getLanguage(), "zh-CN");
  assert.equal(migrated.stored.get("futureskill-language-preference"), "zh-CN");
  const preferred = engine({ saved: { "futureskill-language-preference": "ms", futureskill_language: "zh" }, start: true });
  await preferred.api.ready;
  assert.equal(preferred.api.getLanguage(), "ms", "existing Settings preference takes priority over legacy storage");
  const invalid = engine({ saved: { "futureskill-language-preference": "unsupported", futureskill_language: "zh" }, start: true });
  await invalid.api.ready;
  assert.equal(invalid.api.getLanguage(), "en", "invalid canonical preference retains its English fallback");
  const alias = engine();
  await alias.api.setLanguage("zh");
  assert.equal(alias.api.getLanguage(), "zh-CN");
  assert.equal(alias.stored.get("futureskill-language-preference"), "zh-CN");
  assert.equal(alias.stored.get("futureskill_language"), "zh");
  console.log("PASS: legacy preference migration, canonical precedence and zh alias share one language state");

  const { api, document, stored } = engine();
  for (const code of ["zh-CN", "ms", "en", "zh-CN", "en"]) {
    await api.setLanguage(code);
    assert.equal(api.getLanguage(), code);
    assert.equal(document.documentElement.lang, code);
    assert.equal(api.translateText("Career assessment"), packs[code]["Career assessment"]);
    const phrase = "Part 2 of 3";
    const expected = code === "en" ? phrase : packs[code]["Part {n} of 3"].replace("{n}", "2");
    assert.equal(api.translateText(phrase), expected, `${code}: whole-phrase interpolation works`);
    const question = "Question 3 of 5";
    const expectedQuestion = code === "en" ? question
      : packs[code]["Question {questionNumber} of {questionCount}"]
        .replace("{questionNumber}", "3").replace("{questionCount}", "5");
    assert.equal(api.translateText(question), expectedQuestion, `${code}: interview question count translates`);
    assert.equal(api.translateText("Interview practice"), packs[code]["Interview practice"]);
    const countPhrase = "Practice answers in this summary: 3.";
    const expectedCount = code === "en" ? countPhrase
      : packs[code]["Practice answers in this summary: {count}."].replace("{count}", "3");
    assert.equal(api.translateText(countPhrase), expectedCount);
    assert.equal(api.translateText("97.5 / 100"), "97.5 / 100");
    assert.equal(api.translateText("Software Developers"), "Software Developers");
  }
  assert.equal(stored.get("futureskill-language-preference"), "en");
  console.log("PASS: repeated language changes, template interpolation, numbers and canonical career names");

  const unavailable = engine({ fail: true }).api;
  await assert.rejects(unavailable.setLanguage("zh-CN"));
  assert.equal(unavailable.getLanguage(), "en");
  assert.equal(unavailable.translateText("Career assessment"), "Career assessment");
  console.log("PASS: unavailable language pack retains the previously working language");

  const blocked = engine({ blocked: true }).api;
  await blocked.setLanguage("ms");
  assert.equal(blocked.getLanguage(), "ms");
  assert.equal(blocked.getState().persistence, "blocked");
  console.log("PASS: blocked storage does not prevent changing language for the visit");

  let resolve;
  const delayed = new Promise(done => { resolve = done; });
  const raced = engine({ delayed }).api;
  const earlier = raced.setLanguage("zh-CN");
  await raced.setLanguage("ms");
  resolve(); await earlier;
  assert.equal(raced.getLanguage(), "ms", "slow earlier load must not overwrite the latest choice");
  console.log("PASS: out-of-order pack requests retain the latest language selection");
})().catch(error => { console.error(error); process.exitCode = 1; });
