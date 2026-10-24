# SDG task evidence and learning-progress integration

## Source and strategy

- Repository: `Yuhang08/Future-Skill-AI-Model`
- Source: `a4e53e4beb538bc1e6c9d545362e421193499f6c`
- First parent: `353469f93b475a8c9376ae22d915c5e43ce80ce0`
- Second parent: `b9b8cf7ad9686dec7be892bbca854cfe2f3da602`
- Integration branch: `feature/sdg-task-mapping-integration`

The workspace started clean. The source was absent from the local ancestry.
References were fetched first, then the actual merge commit was merged into a
separate branch. This was not a reset or an arbitrary mainline cherry-pick.

Conflicts in the shared application mount, requirements, ignore rules, interview
implementation and reskilling frontend were resolved in favor of the newer
local application. The new SDG engine/data were reused; the progress helper was
adapted into the existing dashboard.

## Reused, adapted and excluded

**Reused:** O*NET Task Statements, narrow task-to-Target matching, tiered
suggestions, 17-Goal scoring, source import/audit/export utilities, relevant
tests and test-only GitHub CI.

**Adapted:** the current SDG page, not the older upstream visual system.
Task evidence is behind concise disclosures and the existing detail drawers.
The shared header, logo, Settings, themes and canonical career selection remain.
The old illustrative learning-preparation links are displayed separately and
their pathways remain available even without a narrow occupational match.

**Preserved:** assessment algorithms and answers, recommendation scores/order,
five existing illustrative pathway templates, self-ratings, skill targets/gap
arithmetic, storage implementation, completed records, uploads and XP. No
database was replaced or migrated. Data-changing API regression checks use
temporary storage; browser sample plans use clearly isolated demo sessions.

**Intentionally not imported:** unrelated interview file replacements,
duplicate interview datasets, dependency changes, shared app-mount changes and
upstream catalog expansion/derived skill-profile modules. Those would replace
the current approved pathway targets and navigation rather than merely add
task evidence and progress. Existing interview code remains unchanged.

## Observed coverage

| Item | Count |
|---|---:|
| Real O*NET occupations | 923 |
| Separate explicit prototype identities | 4 |
| Occupations with source task records | 923 |
| Source task records | 18,838 |
| Occupations with a narrow task-to-Target rule candidate | 59 |
| Occupations without a narrow task-to-Target match | 864 |
| Additional occupations with task-topic suggestions | 92 |
| Additional DWA-only suggestions | 0 |
| Occupations with classification-only guesses | 374 |
| Occupations with no justified candidate | 398 |
| Documented human-reviewed occupation mappings | 0 |
| Goal indices checked across real occupations | 15,691 |

The final score-coverage test checks 923 × 17 outputs and confirms every
displayed task identifier belongs to that occupation in the source CSV.
Indices are comparisons, not 15,691 established relationships. Weak indices
and classification-only guesses must not be described as supported Targets.

The narrow rule audit covers Targets 4.1, 4.2, 6.3, 7.2, 8.8, 9.5, 11.2,
12.3, 12.5, 15.1 and 16.3. No missing Target relationship is invented.
Environmental Engineers and its singular alias resolve to `17-2081.00`; its
exploratory Goal ranking is not promoted into a narrow Target mapping.

## Source verification

The included task CSV was compared directly with the versioned official
O*NET 31.0 CSV. All headers and all 18,838 records match. The official raw file
uses CRLF and the Git copy LF; normalized text is identical.

The official database license page links CC BY 4.0. Attribution is visible in
the application. O*NET describes U.S. occupations and does not validate
FutureSkill's SDG interpretation. UN pages define Goals/Targets, not occupation
relationships. Source URLs and the exact model formula are documented in
[the method note](sdg-923-rule-based.md).

Optional Tasks-to-DWAs and Task Ratings files are not installed. Their import
utilities are available but were not run. No existing evidence export was
overwritten. The source import scripts were inspected before use; source
verification read the public file without replacing the workspace CSV.

## Progress meaning

For each skill, completed learning-task hours are divided by the existing
estimated hours per gap level. Only whole estimated practice milestones count,
capped at the planned gap. Review tasks and reopened/unfinished tasks do not
count. Partial practice remains visible in the overall completed-hours total.

The UI keeps current self-rating, example target, estimated remaining hours,
activity completion and XP distinct. No completion silently increases a
verified or self-reported skill level. There is no actual proficiency assessment.

## Final verification

| Check | Final result |
|---|---|
| Python suite | 93 passed, 0 failed, 0 skipped |
| Full-catalogue scoring | All 923 occupations × 17 Goals; genuine occupation Task IDs |
| Practice-level JavaScript | 16 assertions passed |
| Report-model JavaScript | 12 check groups passed |
| Assessment draft, language packs, pathway confirmation | Passed |
| JavaScript syntax | Passed for modified standalone scripts |
| SDG browser suite | 11 groups passed |
| Theme browser suite | 18 groups passed across six routes |
| Interview browser suite | Passed its route/history/unavailable-provider/language/theme/mobile matrix |
| UI refinement browser suite | Seven screens passed desktop/tablet/mobile, both themes and reflow checks |
| Preview screenshot | Current `/sdg-impact` rendered successfully |
| Live LLM/provider inference | Not performed; SDG calculations require none |
| GitHub-hosted CI / production / Render | Not run or changed |

Browser tests use real Chromium and app/API requests. They check native
keyboard selection, focus restoration, stale searches, errors/retry, exact
task/source parity in drawers, all 17 indices, mobile layout and both themes.
Interview provider failures are explicit; mocked unit responses are not
reported as successful live inference.

Initial regression failures were resolved rather than ignored. An upstream
test assumed a different pathway catalog; it now exercises the preserved local
catalog. Original complete-response hashes included old SDG metadata: replacing
only that metadata with the pre-integration helper reproduced all five frozen
hashes. All remaining assessment/recommendation content was identical; new
core baselines exclude only the intentionally replaced SDG metadata.
The old theme test was updated to the current logo and gear/Settings UI, and its
Chromium cleanup no longer masks an assertion failure.

## Changed files

- `.github/workflows/futureskill-integration.yml`, `.replitignore`
- `docs/sdg-923-rule-based.md`, `docs/sdg-career-explorer.md`, this report
- `scripts/audit_sdg_task_evidence.py`
- `scripts/export_923_sdg_review.py`, `scripts/export_923_task_goal_rankings.py`
- `scripts/import_onet_sdg_context.py`, `scripts/import_onet_sdg_tasks.py`
- `src/README.md`, `src/data/onet_task_statements.csv`
- `src/reskilling/extra_features.py`, `src/reskilling/index.html`
- `src/reskilling/sdg_alignment.py`, `src/reskilling/sdg_candidate_ranker.py`
- `src/reskilling/sdg_occupation_rules.py`, `src/reskilling/sdg_onet_context.py`
- `src/reskilling/sdg_task_evidence.py`, `src/reskilling/sdg_task_goal_model.py`
- `src/reskilling/static/app.js`
- `src/static/future-pages.css`, `src/static/index.html`
- `src/static/sdg-career-search.js`, `src/static/sdg-impact.html`
- `tests/sdg_browser.cjs`, `tests/theme_browser.cjs`
- `tests/test_assessment_report_regression.py`, `tests/test_integration.py`
- `tests/test_reskilling_progress.cjs`, `tests/test_sdg_careers.py`
- `tests/test_sdg_onet_context.py`, `tests/test_sdg_target_precision.py`
- `tests/test_sdg_task_goal_api.py`, `tests/test_sdg_task_goal_model.py`

Generated browser captures are under ignored `generated-artifacts/`; they are
not application assets or learner records. The integration is committed locally
only. No push, merge into main, publication or Render change is authorized.
