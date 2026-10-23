# FutureSkill second-pass UI review

## Review in running Preview

Open `/__dev/screens` for the complete inventory. Development previews are enabled
only by the development-scoped `FUTURESKILL_DEV_INVENTORY=1` setting. No deployment
configuration or production environment setting was changed.

| Screen IDs | Route | What changed |
| --- | --- | --- |
| S05, S30 | `/?report-demo=differentiated` or `/?report-demo=equal-high` | Original scores; selective emphasis; larger occupation titles; compact matching reasons and separate disclosures |
| S25, S33 | `/career-overview` or `/__dev/career-preview?view=overview&profile=mixed` | Short overview with structured values, recommendations and next steps |
| S26 | `/careers` | Title-led catalogue, labeled search, suggestions, accurate count, load more, secondary metadata and actual pathway coverage |
| S27 | `/career/15-1252.00` | Shorter evidence/readiness text and collapsed catalogue profile; explicit target-review action |
| S28 | `/compare?ids=15-1252.00,15-1253.00` | Existing comparison retained; shared navigation and identity |
| S29, S34 | `/my-profile` or `/__dev/career-preview?view=profile&profile=mixed` | Complete charts; concise emphasized summary; Interests/Subjects/Confidence navigation; no repeated career cards |
| S06–S08 | `/reskilling?demo=1&demo_scenario=fresh` | Compact setup introduction, contextual steps/current/completed indicators, return to career exploration |
| S10 | `/__dev/demo/open?demo=1&demo_scenario=dashboard&scenario=dashboard&screen=S10` | Isolated saved-plan sample, real next unfinished activity and progress summary |
| S32 | `/__dev/brand` | Three original directions, selected Forward F, light/dark/monochrome and small-size previews |

The two new career-preview pages call the real recommendation API with labeled
sample answers held only in page memory. They do not write sessionStorage, drafts
or real learner records. Their pathway handoff uses the isolated sample session.
The ordinary overview/profile pages continue to use the learner's actual
browser-session result. Review/retake does not recalculate until resubmission.

## Visual decisions

- One application header/wordmark. The selected original **Forward F** symbol is
  in `src/static/brand-forward.svg`; dark and monochrome variants have matching
  suffixes. `brand-steps.svg` and `brand-branch.svg` are alternatives, not learner
  settings. The favicon endpoint and small navigation mark use the selected SVG.
- Shared type scale and primary accent; neutral cards and readable metadata.
- Occupation titles dominate recommendation-position labels. Cards show actual
  interest overlap and detected subject tags, visible pathway coverage, Explore
  and Compare actions, then closed **Why this match?**, **Sources** and
  **Limitations** disclosures. Existing engine indices remain available inside
  methodology, not replaced with a new score.
- Profile names/values use semantic strong elements built with DOM APIs.
  Translation stays separate from canonical occupation names and learner data.
- The learning-pathway sidebar action has a steps icon, arrow and restrained
  accent. Active navigation uses a separate inset indicator.
- Setup-step completion means the form step was continued with valid controls,
  not skill proficiency or a saved plan. Changing a step clears its completion;
  changing the target also clears skill-step completion.
- Returning learners see their saved target and earliest unfinished learning
  activity, then real stored progress. Exploration never silently changes that
  target. Progress navigation now reaches actual completed-task history.

## Files changed

- `src/static/ui-refinement.css`: shared second-pass hierarchy and responsive rules.
- `src/static/assessment-report.js`: structured emphasis, compact summary and
  profile-only report mode.
- `src/static/career-ui.js`: shared recommendation card hierarchy/disclosures.
- `src/static/career-workspace.js`, `career-workspace.html`: overview, catalogue,
  details/profile refinement and safe development sample routing.
- `src/reskilling/index.html`, `src/reskilling/static/app.js`: setup/saved-plan
  sidebar state, next activity, form-step status, typography and header cleanup.
- `src/static/future-theme.js`: shared identity, favicon and refinement stylesheet.
- `src/static/index.html`, `ai-trend.html`, `sdg-impact.html`, `uncertainty.html`:
  shared-header asset updates; no existing page algorithm changes.
- `src/static/locales/en.json`, `zh-CN.json`, `ms.json`: matching new UI phrases.
- `src/static/brand-*.svg`, `src/brand-preview.html`: original identity assets and
  development-only preview.
- `src/main.py`: selected favicon and additive catalogue pathway-coverage metadata
  using the existing reviewed mapping; scoring and ranking untouched.
- `src/reskilling/api.py`: development-only brand/sample-preview page endpoints.
- `src/static/dev-screens.html`: screen inventory/review links.
- `tests/ui_refinement_browser.cjs`: new isolated Chromium visual/interaction matrix.
- `tests/assessment_report_browser.cjs`, `tests/language_browser.cjs`,
  `tests/test_integration.py`, `tests/test_assessment_report_regression.py`:
  assertions updated for intentionally changed UI/navigation, plus source/pathway
  alignment checks; frozen scoring/ranking baselines unchanged.
- `.replit`: development-only inventory flag; workflows/ports/deployment unchanged.
- `src/README.md`, this document: review instructions and verification boundaries.

## Checks completed

### Automated regression checks

- 48 Python tests passed: frozen complete legacy recommendation-response digests
  for equal-high, equal-low, differentiated, leading-tie and mixed patterns;
  confidence excluded from ranking; invalid input; catalogue IDs/pathway coverage;
  reskilling data/progress and reviewed SDG mappings; mocked LLM error/timeout and
  structured-output validation.
- 12 report-model checks passed.
- Language-pack key/placeholder parity and all 42 question translations.
- Assessment draft restoration plus 22 invalid/expired/incompatible draft cases.
- Pathway replacement confirmation: cancellation sends no save; explicit approval
  submits once; completed records/evidence warning remains accurate.
- JavaScript syntax and whitespace checks.

### Real Chromium checks

- Seven affected screens at 390, 768 and 1440 CSS pixels in both themes.
- Reflow at a 720×500 CSS-pixel viewport with device scale factor 2, representing
  the layout area available at 200% zoom on a 1440px-wide display. This is
  zoom-equivalent reflow, not a claim of driving browser chrome zoom controls.
- Key text contrast measured at least 4.5:1; titles, ratings and emphasis checked.
- Keyboard disclosure activation, visible focus, Settings Escape/focus return.
- Search suggestions, no results, simulated catalogue failure and successful retry.
- Original exact scores/order, ties, invalid report, answer review and draft
  isolation; actual recommendation → detail → isolated pathway handoff.
- New sample previews do not replace the real stored session result.
- Selected Software Developers exploration does not replace the saved Data
  Analyst sample plan.
- Chinese/Malay/English switching on report, setup and shared Settings; values,
  IDs, canonical titles and existing saved profile remain intact.
- No uncaught browser errors, missing assets or page-level horizontal overflow
  in the final matrix.

### Visual captures

`generated-artifacts/ui-refinement/` contains before/after desktop captures,
responsive light/dark captures and a self-contained `review.html` gallery.
Before images were captured from an isolated copy of the pre-refinement commit,
using synthetic browser context/sample plans rather than real learner records.
Generated captures are ignored by Git and deployment.

### Actual model calls

**None.** Existing LLM behavior/provider configuration is unchanged. Provider and
malformed-output checks above use mocks; this work does not claim live inference.

## Remaining limitations and source boundaries

- No invented occupational descriptions: unsupported duties/requirements remain
  unavailable locally, with direct official O*NET occupation-profile links.
- Sources remain distinct from deterministic ranking methodology. O*NET interest
  definitions support general activity descriptions only; the official Interest
  Profiler's validation does not apply to FutureSkill's custom questionnaire.
- Pathway templates, reviewed SDG connections and trend mappings retain their
  existing limited coverage. Illustrative pathway requirements are labeled before
  the learner chooses a pathway. No new occupational or market facts were added.
- Career context remains browser-session based, not cross-device account sync.
- Brand concepts are original proposals, not a trademark-clearance opinion.
- No new placeholder UI, fabricated progress, generated AI review, or unavailable
  feature button was introduced.
