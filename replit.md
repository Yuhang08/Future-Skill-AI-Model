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
