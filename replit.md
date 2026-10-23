# Running FutureSkill AI on Replit

The existing Python 3.12 / FastAPI application serves both its web pages and API.
Keep the imported structure and stack; no frontend build or separate server is needed.

## Start

Use **Run** to start the `Start application` workflow:

```bash
python -m uvicorn main:app --app-dir src --host 0.0.0.0 --port 5000
```

Open Preview at `/` for the career assessment, or `/reskilling` for learning
pathways. Other pages include `/ai-trend`, `/uncertainty`, `/sdg-impact` and API
documentation at `/docs`.

## Dependencies

Dependencies are declared in `requirements.txt`. This environment uses the
ignored `.pythonlibs` package directory. If dependencies need to be restored and
the standard installer fails with a disabled user-site error, run:

```bash
python -m pip install --no-user --target .pythonlibs/lib/python3.12/site-packages -r requirements.txt
```

No virtual environment is needed.

## Data and optional services

- The core rule-based prototype needs no external services or API keys.
- Optional AI-generated explanations require a supported server-side provider.
  Without it, that endpoint returns an explicit configuration failure; the rest
  of the app works. Do not add invented credentials.
- Learner data, uploads and the app-generated cookie-signing key live in
  `src/instance/` by default, which is ignored by Git.
- The existing application is a development prototype using anonymous browser
  sessions, not real user accounts. Follow the public-launch warnings in
  `src/README.md` before publishing, especially for photo uploads and learner data.
- The development screen inventory stays disabled by default.

## Checks

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
node tests/assessment_progress.test.cjs
```

Additional browser checks and architecture notes are in `src/README.md`.

## Career-assessment results report

The report adds interpretation and accessible comparison bars around the existing
`/api/recommend` response. It does not change assessment scoring or career ranking.
Self-reported broad skill confidence is displayed separately and is not a ranking
input. General interest descriptions cite official O*NET pages; FutureSkill's
questionnaire is custom, not the official Interest Profiler.

Open `/?report-demo=equal-high` in Preview for an explicitly labeled sample report.
The selector also supports equal-low, differentiated, leading-tie, mixed, and
invalid data. Valid demonstrations call the real recommendations API, keep
answers in memory, and never overwrite the learner's saved draft. Their
reskilling links use the existing isolated demo sessions.

Additional checks:

```bash
node tests/assessment_report.test.cjs
node --experimental-websocket tests/assessment_report_browser.cjs
node --experimental-websocket tests/assessment_browser.cjs
```

The browser checks require the available Chromium binary and a running workflow.
They use a temporary browser profile and save screenshots under `/tmp`, not Git.
The API regression checks are included in Python test discovery and compare full
responses against pre-report-refinement baselines.

No assessment LLM review is implemented or represented as successful AI output.
The existing pathway-only provider reports missing credentials in this setup.
The deterministic report remains available and sends no answers to an LLM.

## Interface languages

The shared navigation Settings button offers English (`en`), Simplified Chinese
(`zh-CN`) and Bahasa Melayu (`ms`). One shared Settings dialog now includes
learning-profile access, Light/Dark/System appearance, language, privacy
information, and clearly unavailable workspace options. It is opened by the
top-right gear-and-Settings button; there is no separate sidebar Settings panel.
Preferences are local to the current browser, not account settings or
cross-device synchronization.

The reskilling sidebar contains only Overview, My Reskilling Plan, and Progress
Tracking. Global page navigation stays in the top bar. The Profile action opens
the existing profile editor in reskilling, or navigates there using
`/reskilling?editProfile=1` from other pages. New learners see the real setup
form; existing learners retain their saved values until they submit an edit.

The language packs are editable local JSON files under `src/static/locales/`.
Keep their English phrase keys and named interpolation slots synchronized.
`src/static/future-i18n.js` applies the selected pack to static and dynamically
rendered interface text without changing questionnaire data, input values,
recommendation identifiers, scores or URLs. Imported occupational titles and
external source material may retain their original English.

Language-specific checks:

```bash
node tests/language_packs.test.cjs
node --experimental-websocket tests/language_browser.cjs
```

The browser checks also cover unified Settings, internal sidebar navigation,
and profile-entry links. Returning-learner UI checks use an explicitly labeled
in-memory fixture; it is never submitted or stored as a learner record.
