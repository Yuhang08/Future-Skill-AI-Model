# FutureSkill AI — HR Interview (Modules 1–10)

## Important career data
Place your **existing** `career_profiles_clean.csv` next to `app.py`. Its `Title` column drives the **complete** searchable A–Z target career list. Search is case-insensitive, all matches appear with a 7-row scroll window. No careers are manually capped.

Without that file, the app loads `careers_demo.csv` (seven illustrative careers). The full 293 titles cannot be guaranteed unless you provide the original CSV, which was not attached to this conversation.

If your file has another name set `CAREER_CSV=your_filename.csv` in `.env`.

## Run
1. Python 3.10+ recommended.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and enter `OPENAI_API_KEY`.
4. `python app.py` and open http://127.0.0.1:5000

## Features (1–10)
1. Career selection
2. Personal facts: optional skills/description from CSV; no invented experience
3. Searchable A-Z dropdown, seven visible options, scroll for all
4. LLM question generation
5. Career CSV grounding (NOT independently fact checked)
6. Mic → submit recording → transcribe → evaluate; browser speech synthesis for interviewer
7. Per-question weighted score and coaching
8. Adaptive prompts based on weakest dimension
9. Readiness, proficiency, strengths/weaknesses with evidence counts
10. Persistent browser personal interview reports and server question history
Plus semantic embeddings with <150 / >=150 / recent100 policy

## Limitations and safety
- The example CSV is **illustrative**, not a verified occupational source. Full source checking and curated fallbacks remain to be added.
- Real API key and network are needed. API calls cost money; set account budgets and rate limits.
- Browser report history is local; it may be deleted by clearing site data. Server stores question text associated with an anonymous opaque cookie. SQLite may be ephemeral on Render; use managed PostgreSQL for deployment.
- Cookie uses HttpOnly SameSite Lax; add CSRF protections, stronger privacy policy, request rate limiting, durable session storage, GDPR-style deletion hooks and production authentication/abuse controls before public release.
- Embedding uses one API request per comparison for previous questions in this MVP: cache/persist vectors before a large deployment. It is expensive for long histories.
- Scores are subjective practice indicators; not hiring decisions.
- Your original FastAPI website cannot simply replace its app.py with this Flask example; mount equivalent endpoints or migrate the module.

## Section 6 — Text and Voice Answer
- Choose **Text Answer** to type into an expanded, editable answer area.
- Choose **Voice Answer** to record and transcribe your speech. The transcript is editable before submission.
- Both modes share the same AI feedback, scoring, and interview report.
- A word and character counter appears beneath the input.
