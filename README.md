# FutureSkill AI — Integrated Website

This is the **merged** version of the user's existing FastAPI RIASEC website and the separate personalised reskilling module. They now run under **one server / one URL**.

## Start on Windows (PyCharm)

1. **Back up your old PyCharm project first**. Extract this ZIP as its own folder to avoid overwriting your previous work.
2. In PyCharm, select **File → Open** and choose the extracted `FutureSkill_AI_Integrated` folder.
3. Open PyCharm Terminal (bottom panel) and enter:

   ```bash
   python -m pip install -r requirements.txt
   python -m uvicorn app:app --host 127.0.0.1 --port 8000
   ```

   You can alternatively double-click `start_windows.bat` after installing requirements.
4. Open **http://127.0.0.1:8000/** (original assessment) or **http://127.0.0.1:8000/reskilling** (new pathway).
5. If port 8000 is already in use, stop the old website's PyCharm Run process first.

## How to use

- The home page retains the **42-question RIASEC + subject + skills** assessment.
- After completing the assessment, browse career recommendations. Each recommendation now includes an **Explore reskilling options** link.
- The link takes you to `/reskilling?career=...` and selects a supported reskilling template **only when an explicit mapping exists** (the five prototype template titles plus Software Developers and Information Security Analysts). Other occupations receive an honest message and a choice of 5 prototype roles; **the app does not fake occupation-specific skill requirements**.
- Complete the 3-step skills/timetable form and select **Generate my pathway** to view your skill-gap scores, weekly tasks, objectives, progress bars and learning tree.
- Mark tasks done to gain cumulative XP; upload a photo (5 MB JPG/PNG/WEBP) as evidence; change timetable to reschedule unfinished tasks.

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
FutureSkill_AI_Integrated/
  app.py                     Original FastAPI /api/recommend + integrated router
  assessment_scoring.py      Original assessment algorithm
  career_engine.py           Original career matching algorithm (923-row dataset)
  career_profiles_clean.csv  Original provided career database
  static/index.html          Original 42-question frontend, with new links
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
- Sample skill demands, scheduling time estimates and learning resources are a **rule-based prototype**, not trained AI or verified forecasts.
- This demo uses an anonymous signed browser cookie, not a real account. Clear cookies and you may lose access to earlier tasks. Photos and SQLite remain locally under `instance/`.
- **Do not deploy as-is to public production**. Add individual user accounts, real auth, HTTPS, secure cookies, consent/data retention, image transcoding and rate limiting before allowing public photo uploads.

## Run automated checks

```bash
python -m unittest discover -s tests -v
node tests/assessment_progress.test.cjs
# Requires a running app, Chromium and Node with built-in WebSocket support.
node tests/assessment_browser.cjs
```

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

- `GET /`  → old Career Assessment
- `POST /api/recommend` → old career assessment and career matching
- `GET /reskilling` → new skills and timetable questionnaire/dashboard
- `GET /api/state` → anonymous user's learning data
- `POST /api/plan`, `POST /api/replan` → personalised timetable generator
- `POST /api/tasks/{id}/status` → to-do completion and growth points
- `POST /api/tasks/{id}/proof` → attached learning photograph
