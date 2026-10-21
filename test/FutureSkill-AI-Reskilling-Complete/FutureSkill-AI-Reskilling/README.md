# 🌱 FutureSkill AI — Personalised Reskilling Website

A **working, local, zero-third-party-dependency Python demo**. It uses the Python standard library (HTTP server, SQLite, scheduling) and plain HTML/CSS/JavaScript.

## 1. How to run (Windows / Mac / Linux)

1. Install Python 3.10+ from https://www.python.org/downloads/ (on Windows, tick **Add Python to PATH**).
2. Extract this ZIP. Open a terminal in the `FutureSkill-AI-Reskilling` folder.
3. Run `python app.py` (Windows may use `py app.py`); alternatively double-click `start_windows.bat` on Windows, or run `sh start_mac_linux.sh` on Mac/Linux.
4. Open **http://localhost:8000** in your browser.
5. Complete the questionnaire to create your learning pathway.
6. Press **Ctrl + C** in the terminal to stop the website.

No `pip install` is required. The app binds to `127.0.0.1` and runs on **your computer only**, not a public URL.

## 2. Features

- Questionnaire: career background, target role, current skill levels, experience, goal, weekly study hours, available days, duration, learning style.
- Explainable skill gap analysis: `gap = max(0, required - current)` and `priority = gap / 5 × importance`.
- Estimates study time as `gap × hours_per_level` (illustrative assumptions).
- Schedules **80% learning / 20% review** on selected weekdays, respecting skill prerequisites.
- Actionable learning objectives, to-do list, optional mobile-camera/photo uploads (JPG/PNG/WEBP, max 5 MB).
- Completed-task persistence in SQLite, study-hours progress bar, cumulative XP, six stages of a growing tree.
- Positive feedback without streak punishments; changing the timetable keeps completed tasks and XP.
- Stores data in `instance/futureskill.sqlite3` and photos in `instance/uploads/`. This folder is created on first run.

## 3. Directory guide

```text
FutureSkill-AI-Reskilling/
├── app.py              HTTP routes and photo uploads
├── engine.py           Skill gaps, scheduling, trees, feedback
├── catalog.py          Five example careers and skills
├── storage.py          SQLite database
├── index.html          Web interface
├── static/
│   ├── app.js          Interactive questionnaire and dashboard
│   └── style.css       Website styling
├── tests/
│   └── test_engine.py  Algorithm tests
└── instance/           Automatically created local data (not commit to Git)
```

## 4. How the model works

1. User completes a skill self-rating (0 to 5).
2. Compare each skill against a role target in `catalog.py`.
3. Rank gaps by `gap/5 × importance`; choose highest-priority *eligible* skill (after prerequisites).
4. Allocate study tasks on preferred dates with a fixed 20% review buffer.
5. Save tasks, optional task photos and completed status in SQLite.
6. When a schedule changes, **completed tasks are retained**. Remaining *practice* hours are rescheduled.
7. Gain effort-weighted XP for completed tasks (learning: approximately 10 XP/hour; review: approximately 4 XP/hour), and the tree grows at thresholds 10, 35, 80, 150 and 250 XP.

**Important:** completion of practice hours and photos **does not prove skill mastery**. The app never automatically raises a self-rated skill level; retake the questionnaire after a real assessment to update those ratings. XP is a motivational feature, not a scientific score.

## 5. Technical notes and boundaries

- This is **an explainable, rule-based recommendation/scheduling engine**, not a trained AI/ML model. It is an appropriate functional prototype for a hackathon. An LLM can be added later for natural-language explanations; an ML model requires actual learning outcome data and validation.
- Role proficiency targets, learning-hour estimates, priority weights and learning projects are **demonstration data**, not validated job-market forecasts. Improve with curated O*NET/ESCO data and local review.
- Study time is a flexible estimate, not a promise of employment or immunity from AI-driven changes.
- No real accounts: one anonymous session per browser. Clearing session cookies can make old data inaccessible. Different browsers are isolated. For public deployment add authentication and account recovery.
- Uploaded photos are only displayed to the browser session that uploaded them; images are **not analysed or automatically graded**. Avoid uploading personal documents, IDs or sensitive information to the demo.
- For a public website add authenticated users, HTTPS, secure cookies, consent/privacy policy, upload rewriting with a trusted image library, server-side rate limits, backups, and a production-grade server and hosting. Do not deploy this local HTTP server unchanged to the public internet.
- SQLite and images persist when the server restarts on the same computer. `instance/.session_secret` is necessary for existing sessions and must remain private.

## 6. Connecting to existing FutureSkill AI work

`career_engine.py` (RIASEC matching) and `career_trend.py` are **not overwritten**. A future integration can accept their selected `target_career` as the questionnaire default. Do **not** interpret an RIASEC interest score as a verified technical skill level.

To add more careers: edit `CAREERS` in `catalog.py`, supplying a required level, importance, hours-per-level, objective, project and zero-or-more prerequisites for each skill. Make sure prerequisites name actual skills and do not form loops.

## 7. Testing

Run: `python -m unittest discover -s tests -v`

The tests check skill gaps, input validation, prerequisites, schedule capacity, XP levels, flexible replanning and more. For the full HTTP/API integration tests, run with the project files available and use the same command.

**Team roles idea:** Mathematical engine + database/career research + UI/API integration.
