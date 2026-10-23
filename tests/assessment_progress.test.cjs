const assert = require("node:assert/strict");
require("../src/static/assessment-progress.js");
const { validateDraft, fingerprint } = globalThis.FutureSkillAssessmentProgress;
const parts = [{ questions: [["R", "Question one"], ["I", "Question two"]] },
  { questions: [["Math", "Question three"]] }];
const now = 1900000000000;
const good = {
  version: 1, questionnaire: fingerprint(parts), savedAt: now,
  currentPart: 1, currentQuestion: 0, answers: { "0_0": 4, "1_0": 2 },
};
assert.deepEqual(validateDraft(JSON.stringify(good), parts, now), good);
const invalid = [
  null, "", "{", "x".repeat(16385),
  ...[
    { version: 2 }, { questionnaire: "old-questions" },
    { savedAt: now - 31 * 86400000 }, { savedAt: now + 60001 },
    { savedAt: null }, { currentPart: -1 }, { currentPart: 10 },
    { currentQuestion: 10 }, { currentQuestion: 0.5 },
    { answers: [] }, { answers: null }, { answers: { "9_0": 3 } },
    { answers: { "0_0": 6 } }, { answers: { "0_0": 0 } },
    { answers: { "0_0": "3" } }, { answers: { "0_0": 3.5 } },
  ].map(patch => JSON.stringify({ ...good, ...patch })),
];
for (const raw of invalid) assert.equal(validateDraft(raw, parts, now), null);
assert.equal(validateDraft(JSON.stringify(good), [
  { questions: [["R", "Changed question"], ["I", "Question two"]] }, parts[1],
], now), null);
assert.equal(validateDraft(JSON.stringify({ ...good, answers: JSON.parse('{"__proto__":3}') }), parts, now), null);
console.log(`PASS: valid draft restoration and ${invalid.length + 2} malformed/expired/incompatible draft checks`);
