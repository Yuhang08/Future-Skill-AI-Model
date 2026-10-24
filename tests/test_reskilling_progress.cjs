'use strict';
// Check pure progress behavior without browser dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'reskilling', 'static', 'app.js'),
  'utf8'
);
const start = source.indexOf('function completedPracticeLevels(');
const end = source.indexOf('\nfunction renderGaps(', start);
assert.ok(start >= 0 && end > start, 'level-progress helper must exist');
const sandbox = Object.create(null);
vm.runInNewContext(source.slice(start, end), sandbox, {timeout:1000});
const progress = sandbox.completedPracticeLevels;
function done(hours, skill='Python', kind='learning', completed=true) {
  return {hours, skill, kind, completed};
}
const g = {current:2, required:5, gap:3, estimated_hours:12};
const cases = [
  [[], 0, 'initial progress must be zero despite self-rating 2'],
  [[done(3)], 0, 'partial work must not fill a level'],
  [[done(4)], 1, 'one completed estimated level'],
  [[done(9)], 2, 'two completed estimated levels'],
  [[done(12)], 3, 'all planned levels'],
  [[done(30)], 3, 'capped at planned levels'],
  [[done(5,'Python','review')], 0, 'review does not count'],
  [[done(5,'Other')], 0, 'other skill does not count'],
  [[done(5,'Python','learning',false)], 0, 'not checked off does not count'],
  [[done(4),done(4,'Python','learning',false)], 1, 'reopened task no longer counts'],
  [[done(1.5),done(2.5)], 1, 'multiple completed tasks add together'],
];
for (const [tasks, expected, explanation] of cases) {
  assert.equal(progress('Python',g,tasks).completed, expected, explanation);
}
assert.equal(progress('Python',{...g,gap:0,estimated_hours:0},[]).completed,0);
assert.match(source, /renderGaps\(state\.gaps,\s*state\.tasks\)/);
console.log('OK: ' + (cases.length + 2) + ' learning progress assertions');
