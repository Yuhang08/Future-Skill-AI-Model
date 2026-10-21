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
```

## One-server architecture

- `GET /`  → old Career Assessment
- `POST /api/recommend` → old career assessment and career matching
- `GET /reskilling` → new skills and timetable questionnaire/dashboard
- `GET /api/state` → anonymous user's learning data
- `POST /api/plan`, `POST /api/replan` → personalised timetable generator
- `POST /api/tasks/{id}/status` → to-do completion and growth points
- `POST /api/tasks/{id}/proof` → attached learning photograph
