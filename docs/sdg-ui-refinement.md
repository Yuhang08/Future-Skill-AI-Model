# SDG goal-list and shared-drawer refinement

Implemented on `feature/sdg-task-mapping-integration` after the completed
integration. No source re-import, backend/scoring change or data migration.

## Interface

- Top-three ranking cards and their numerical values are preserved.
- The perimeter/SVG diagram is replaced by a native expandable 17-Goal list.
  It starts collapsed and becomes a single readable column on phones.
- Every Goal, including before career selection, opens the same native
  evidence drawer. Narrow Target cards use this drawer too.
- Each drawer shows the official Goal definition/source, available
  occupational rationale and original task wording/IDs, source links, review
  status, limitations and an exploration action. Additional Target hypotheses
  for the same Goal are retained.
- Goal 4/8 learning-preparation explanations retain their exact API-provided
  rationale, skill/practice statements, sources, limitations and actions.
  They remain separate from occupational evidence and appear early in the
  drawer when available.
- Unselected careers, prototype roles, classification-only guesses, weak
  rankings, missing task data and missing pathway examples have explicit
  states. Prototype IDs never become invented O*NET occupation URLs.
- Career invalidation closes stale evidence. Escape, close/backdrop, native
  modal focus, focus return, mobile scrolling and reduced motion are supported.
- Contrast checks cover themed list text and text over all 17 Goal colors.

## Verification

- Final complete Python suite: **93 passed**, no failures or skips.
- SDG browser suite: **16 check groups passed**, including every Goal in
  unselected and occupational contexts; exact Goal 4/8 pathway evidence;
  task/source parity; missing-source fixture; keyboard/focus; stale searches;
  errors/retry; desktop/mobile; light/dark; computed text contrast.
- Shared-theme browser suite also passed across six routes.
- Complete API responses for Environmental Engineers, Solar Energy Systems
  Engineers, Data Analyst and Software Developers matched their
  pre-refinement snapshots exactly.
- No backend, assessment scoring, career ranking, task data or stored learner
  data files changed. Browser missing-source data is an in-page test fixture,
  never written to application storage.
- Main Preview remains on port 5000. No publishing, remote push, main-branch
  merge or deployment change.

Changed implementation: `src/static/sdg-impact.html`,
`src/static/future-pages.css`.
Changed checks: `tests/sdg_browser.cjs`, `tests/test_integration.py`.
Documentation: this note and `docs/sdg-923-rule-based.md`.
Generated screenshots are under ignored `generated-artifacts/sdg-ui-refinement/`.
