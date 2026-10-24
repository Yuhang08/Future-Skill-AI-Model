const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("src/reskilling/static/app.js", "utf8");
const handler = source.slice(source.indexOf("async function submitPlan(event)"), source.indexOf("async function toggleTask("));

async function run({ target = "Data Analyst", tasks = [], approve = false }) {
  const state = { profile: { target_career: "Software Developer" }, tasks };
  const before = JSON.stringify(state);
  const nodes = { submitPlan: { disabled: false }, formError: { textContent: "" } };
  const calls = [], prompts = [];
  const context = vm.createContext({
    appState: state, $: id => nodes[id],
    readForm: () => ({ target_career: target }),
    window: { confirm: text => { prompts.push(text); return approve; }, scrollTo() {} },
    api: async (...args) => { calls.push(args); return { state }; },
    showApp() {}, toast() {}
  });
  vm.runInContext(handler, context);
  await context.submitPlan({ preventDefault() {} });
  assert.equal(JSON.stringify(state), before, "confirmation does not mutate existing learner state");
  assert.equal(nodes.submitPlan.disabled, false);
  return { calls, prompts };
}

(async () => {
  const canceled = await run({ tasks: [{ completed: false, proof_url: "/private-proof" }, { completed: true }] });
  assert.equal(canceled.calls.length, 0);
  assert.match(canceled.prompts[0], /unfinished task/);
  assert.match(canceled.prompts[0], /Photos attached to unfinished tasks will also be removed/);
  assert.match(canceled.prompts[0], /Completed tasks, their uploaded evidence, and learning-tree points will remain/);
  const sameTarget = await run({ target: "Software Developer", tasks: [{ completed: false }] });
  assert.equal(sameTarget.calls.length, 0);
  assert.equal(sameTarget.prompts.length, 1);
  const approved = await run({ approve: true });
  assert.equal(approved.calls.length, 1);
  assert.equal(approved.calls[0][0], "/api/plan");
  assert.equal(approved.calls[0][2].target_career, "Data Analyst");
  console.log("PASS: cancelled target/unfinished-task replacement makes no save request; informed approval submits once");
})().catch(error => { console.error(error); process.exitCode = 1; });
