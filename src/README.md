# FutureSkill AI — Integrated Website

This is the **merged** version of the user's existing FastAPI RIASEC website and the separate personalised reskilling module. They now run under **one server / one URL**.

## Start from the repository root

The website is in `src/`; the older prototypes under `test/` are preserved
without modification. Open the repository root in your editor and run:

   ```bash
   python -m pip install -r requirements.txt
   python -m uvicorn main:app --app-dir src --host 0.0.0.0 --port 5000
   ```

Open **http://127.0.0.1:5000/** or **http://127.0.0.1:5000/reskilling**.
No provider credential is required for the rule-based prototype pages.
The optional LLM explanation endpoint requires a separately configured supported
server-side provider; missing credentials return an explicit failure.

`FUTURESKILL_DATA_DIR` selects the private learner-storage directory; by default
it is `src/instance/`. Keep that directory, uploads, credentials and database
files out of Git. Use a separate writable data directory for testing.

## How to use

- The home page retains the **42-question RIASEC + subject + skills** assessment.
- Learners can either take the assessment or browse careers without answering it.
- Assessment results show the overview first, then the engine’s first three recommendations with the rest expandable, followed by interests, subject preferences and self-reported confidence.
- Career browsing supports search, details, and comparison of up to two roles. Selecting a role is separate from the learner’s saved pathway.
- After completing the assessment, each recommendation includes an **Explore reskilling options** link.
- The link takes you to `/reskilling?career=...` and selects a supported reskilling template **only when an explicit mapping exists** (the five prototype template titles plus Software Developers and Information Security Analysts). Other occupations receive an honest message and a choice of 5 prototype roles; **the app does not fake occupation-specific skill requirements**.
- Replacing an existing target or unfinished learning tasks requires explicit confirmation; cancelled changes are not submitted.
- Complete the 3-step skills/timetable form and select **Generate my pathway** to view your skill-gap scores, weekly tasks, objectives, progress bars and learning tree.
- Mark tasks done to gain cumulative XP; upload a photo (5 MB JPG/PNG/WEBP) as evidence; change timetable to reschedule unfinished tasks.

## Career report evidence boundaries

- Career matching inputs are the learner’s RIASEC answers and subject preferences. The six broad confidence ratings are not ranking inputs.
- The imported career CSV contains titles and RIASEC profile values. The engine labels its title-derived field taxonomy as a starter taxonomy, not official O*NET data. The UI does not treat those values as O*NET-validated occupational requirements.
- Recommendations show the engine’s existing interest and subject indices, ordering, and title-based field tags. They are not employment probabilities, percentile ranks, or measures of proficiency.
- The custom questionnaire is not the official O*NET Interest Profiler. The report links to official O*NET pages only for general RIASEC explanations and for optional exploration of an occupation profile; those sources do not validate this questionnaire or the imported local values.
- O*NET sources: [Interest Types](https://www.onetonline.org/find/descriptor/browse/1.B.1) supports general RIASEC descriptions; [O*NET Interest Profiler](https://www.onetcenter.org/IP.html) describes the official instrument and its own validation; [O*NET OnLine](https://www.onetonline.org/) provides the linked occupation profiles.
- The local results report is deterministic. The existing optional LLM service explains pathway skill gaps; it is not an assessment-review service. No LLM call is required by the report.

## Replit development review

- Open the running app in **Preview**. The development-only **Open screen inventory** link appears on the homepage and reskilling page when the Replit workflow starts with `FUTURESKILL_DEV_INVENTORY=1`.
- The inventory is at `/__dev/screens`. It contains stable IDs and direct demonstrations for the assessment, reskilling wizard, dashboard components, returning learners, and edge states.
- Demo learners use separate scenario-specific browser sessions and visibly labeled sample data. Changes in those sessions do not modify a normal learner session.
- The inventory distinguishes working screens, development simulations, limited prototypes, and proposed features. Inventory routes are disabled when the development flag is off.

## Exploratory features imported from GitHub

- `/ai-trend` displays ten qualitative category scenarios. The upstream data cites the World Economic Forum Future of Jobs Report 2025 without page-level citations; the page labels the scenario data as unvalidated.
- `/uncertainty` runs the upstream hand-set scenario formula. Its starting value and coefficients are illustrative assumptions, not labor-market forecasts.
- `/sdg-impact` shows limited potential alignments to UN SDG targets 4.4 and 8.5 for five explicitly mapped reskilling pathways. The role skills and practice activities come from FutureSkill's illustrative catalogue; unsupported roles remain unreviewed, and no employment or measured SDG impact is claimed.
- All three are linked from the homepage under **Explore More Features**. No RunPod model or external API key is required for these prototype pages.

## Technical layout

```
src/
  main.py                    FastAPI /api/recommend + integrated routers
  assessment_scoring.py      Original assessment algorithm
  career_engine.py           Original career matching algorithm (923-row dataset)
  career_profiles_clean.csv  Original provided career database
  static/index.html          Assessment, results and direct-entry choices
  static/career-workspace.*  Career overview, search, profile and comparison
  static/assessment-report.* Results report and visualizations
  static/career-ui.js        Shared engine recommendation cards
  reskilling/api.py          Integrated FastAPI endpoints, session, photo uploads
  reskilling/engine.py       Skill-gap calculations, priorities, scheduling, XP
  reskilling/catalog.py      5 illustrative skill-template careers
  reskilling/storage.py      SQLite persistence
  reskilling/index.html      Learning pathway UI
  reskilling/static/         Separate CSS/JS for pathway UI
  instance/                  Created on run (private data — never commit)
```

## Important notes

- The original career matching formula and 42 questions are unchanged.
- The existing 6 skill self-reports are broad skills **not** the occupational competencies used for each pathway. Pathway users are asked to self-rate specific skills; we do not falsely equate interest scores with mastery.
- Career selection and assessment context used by the career workspace are browser-session context; browsing a role does not overwrite a saved pathway.
- Sample skill demands, scheduling time estimates and learning resources are a **rule-based prototype**, not trained AI or verified forecasts.
- This demo uses an anonymous signed browser cookie, not a real account. Clear cookies and you may lose access to earlier tasks. Photos and SQLite remain locally under `instance/`.
- **Do not deploy as-is to public production**. Add individual user accounts, real auth, HTTPS, secure cookies, consent/data retention, image transcoding and rate limiting before allowing public photo uploads.

## Run automated checks

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
node tests/assessment_progress.test.cjs
node tests/assessment_report.test.cjs
node tests/language_packs.test.cjs
node tests/pathway_confirmation.test.cjs
# Requires a running app, Chromium and Node with built-in WebSocket support.
node --experimental-websocket tests/assessment_report_browser.cjs
```

On PowerShell, set `$env:PYTHONPATH = "src"` before running the Python checks.

## Assessment navigation and drafts

The existing 42-question assessment keeps its original questions, ratings and
scoring. Part buttons allow non-linear review; numbered question controls are
inside a compact **Quiz navigation** disclosure, collapsed by default. Next and
submission scroll to the first missing answer and mark unanswered cards with
an inline required-answer message. The marking clears when that question is
answered. Overall and per-part progress are separate from the answer controls.

Answers and the current position are saved in browser-local storage, with a
30-day restoration window and a question-version compatibility check. They are
not account-based or synced between devices. Use **Clear saved draft** on shared
devices; confirmation is required and existing results/learning plans are not
deleted. If storage is blocked, an explicit message explains that answers last
only for the current page. Development screen samples never overwrite drafts.

The browser checks exercise refresh recovery, preview isolation, final-submit
validation, reset confirmation, storage failures, and measured text contrast in
both themes at desktop/mobile widths. Their screenshots are written to `/tmp`,
not committed or published.

## One-server architecture

For the second-pass UI, screen IDs, isolated review links, original logo assets,
before/after captures and check boundaries, see
[`docs/ui-refinement-review.md`](../docs/ui-refinement-review.md).
Start at `/__dev/screens` in development Preview. Brand alternatives are at
`/__dev/brand`; sample overview/profile pages do not replace learner data.

- `GET /`  → old Career Assessment
- `POST /api/recommend` → old career assessment and career matching
- `GET /reskilling` → new skills and timetable questionnaire/dashboard
- `GET /api/state` → anonymous user's learning data
- `POST /api/plan`, `POST /api/replan` → personalised timetable generator
- `POST /api/tasks/{id}/status` → to-do completion and growth points
- `POST /api/tasks/{id}/proof` → attached learning photograph
