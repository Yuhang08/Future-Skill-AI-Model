/* Pure report tests: no DOM, provider, storage, or learner data. */
const assert = require("node:assert/strict");
const { buildModel, SOURCES } = require("../src/static/assessment-report.js");
const order = ["R", "I", "A", "S", "E", "C"];
const subjects = ["IT", "Math", "Education", "Health", "Business", "Engineering"];
const skills = ["MathSkill", "CodingSkill", "DataSkill", "CommunicationSkill", "LeadershipSkill", "CreativeSkill"];
let checks = 0;
function check(name, action) { action(); checks++; console.log(`PASS: ${name}`); }
function result(interests = [100, 100, 100, 100, 100, 100], subject = [5, 5, 5, 5, 5, 5], confidence = [5, 5, 5, 5, 5, 5]) {
  const scores = Object.fromEntries(order.map((key, index) => [key, interests[index]]));
  return {
    top3: [...order].sort((a, b) => scores[b] - scores[a]).slice(0, 3).join(""),
    riasec_scores: scores,
    subject_preferences: Object.fromEntries(subjects.map((key, index) => [key, subject[index]])),
    skills: Object.fromEntries(skills.map((key, index) => [key, confidence[index]])),
    recommendations: [{
      title: "Software Developers", riasec: "ICR", match_index: 67.5,
      interest_index: 50, subject_index: 100, fields: "IT", explanation: "Test engine recommendation."
    }]
  };
}
check("equal high: no arbitrary leading area; ratings visible", () => {
  const model = buildModel(result());
  assert.equal(model.valid, true);
  assert.equal(model.allInterestsEqual, true);
  assert.deepEqual(model.leadingInterests, order);
  assert.match(model.interestSummary, /Your answers do not identify a clear leading interest area\./);
  assert.match(model.interestSummary, /100/);
  assert.match(model.subjectSummary, /equal at 5 \/ 5/);
  assert.match(model.confidenceSummary, /5 \/ 5/);
});
check("equal low: same tie treatment without claiming incapacity", () => {
  const model = buildModel(result(Array(6).fill(20), Array(6).fill(1), Array(6).fill(1)));
  assert.equal(model.valid, true);
  assert.match(model.interestSummary, /20 \/ 100/);
  assert.match(model.subjectSummary, /1 \/ 5/);
  assert.match(model.confidenceSummary, /1 \/ 5/);
  assert.doesNotMatch(model.interestSummary, /weak|unable|unfit|strength/);
});
check("differentiated scores support exploratory connections", () => {
  const model = buildModel(result([40, 100, 60, 80, 40, 20]));
  assert.deepEqual(model.leadingInterests, ["I"]);
  assert.match(model.interestSummary, /Investigative/);
  assert.deepEqual(model.combinedAreas.map(row => row.key), ["I", "S"]);
});
check("leading ties never choose a single winner", () => {
  const model = buildModel(result([60, 100, 40, 100, 80, 20]));
  assert.deepEqual(model.leadingInterests, ["I", "S"]);
  assert.equal(model.hasInterestTies, true);
  assert.match(model.interestSummary, /tied: Investigative, Social/);
});
check("cutoff and second-place ties are preserved", () => {
  const model = buildModel(result([100, 80, 60, 60, 60, 20]));
  assert.deepEqual(model.cutoffAreas, ["A", "S", "E"]);
  assert.equal(model.hasInterestTies, true);
  assert.equal(buildModel(result([100, 80, 80, 60, 40, 20])).hasInterestTies, true);
});
check("mixed preferences and confidence reflect actual ratings", () => {
  const model = buildModel(result([80, 60, 40, 100, 20, 60], [1, 5, 3, 2, 4, 5], [5, 1, 3, 2, 4, 1]));
  assert.equal(model.allSubjectsEqual, false);
  assert.deepEqual(model.subjectLeaders, ["Math", "Engineering"]);
  assert.match(model.subjectSummary, /tied/);
  assert.match(model.confidenceSummary, /5 \/ 5/);
  assert.match(model.confidenceSummary, /1 \/ 5/);
});
check("precision and input objects remain unchanged", () => {
  const data = result([97.5, 80, 72.5, 65, 52.5, 20], [4.5, 5, 3.5, 2, 1, 4], [5, 4, 3, 2, 1, 4]);
  const original = JSON.stringify(data);
  const model = buildModel(data);
  assert.equal(model.valid, true);
  assert.equal(model.ordered[0].score, 97.5);
  assert.equal(JSON.stringify(data), original);
});
check("no recommendations is explicit rather than fabricated", () => {
  const data = result(); data.recommendations = [];
  assert.equal(buildModel(data).valid, true);
});
check("missing, null, non-numeric, non-finite, or out-of-range inputs fail closed", () => {
  for (const data of [null, [], {}, undefined]) assert.equal(buildModel(data).valid, false);
  for (const [field, key, badValues] of [
    ["riasec_scores", "R", [null, "100", NaN, Infinity, 0, 19, 101, true]],
    ["subject_preferences", "IT", [null, "5", NaN, Infinity, 0, 6, true]],
    ["skills", "MathSkill", [null, "5", NaN, Infinity, 0, 6, true]],
  ]) {
    for (const value of badValues) {
      const data = result(); data[field][key] = value;
      assert.equal(buildModel(data).valid, false, `${field}=${value}`);
    }
    const data = result(); delete data[field][key];
    assert.equal(buildModel(data).valid, false);
    const extra = result(); extra[field].extra = 5;
    assert.equal(buildModel(extra).valid, false);
  }
});
check("incorrect code and malformed recommendations rejected", () => {
  for (const code of ["wrong", "SIE", "RRR", null]) {
    const data = result(); data.top3 = code;
    assert.equal(buildModel(data).valid, false);
  }
  for (const rec of [null, {}, { title: "Missing numbers" }]) {
    const data = result(); data.recommendations = [rec];
    assert.equal(buildModel(data).valid, false);
  }
});
check("untrusted AI output never substitutes for calculated observations", () => {
  const data = result(); const expected = buildModel(data).interestSummary;
  for (const review of ["Guaranteed job", "{broken JSON", { source_ids: ["invented"], score: 999 }]) {
    data.ai_review = review;
    assert.equal(buildModel(data).interestSummary, expected);
  }
});
check("registry exposes stable IDs, verified URLs, and bounded claims", () => {
  for (const [id, entry] of Object.entries(SOURCES)) {
    assert.equal(entry.id, id);
    for (const key of ["title", "publisher", "url", "claims"]) assert.ok(entry[key]);
  }
  assert.equal(SOURCES["onet-interest-types"].url, "https://www.onetonline.org/find/descriptor/browse/1.B.1");
  assert.equal(SOURCES["onet-interest-profiler"].url, "https://www.onetcenter.org/IP.html");
  assert.match(SOURCES["onet-interest-profiler"].claims, /not the official/);
});
console.log(`${checks} report-model checks passed.`);
