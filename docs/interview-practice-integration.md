# Interview practice integration

## Source and scope

- Upstream repository: [`Yuhang08/Future-Skill-AI-Model`](https://github.com/Yuhang08/Future-Skill-AI-Model)
- Upstream feature branch: `feature/integrate-hr-reskilling` at `b05d89c1ba5657a3c3f6683b839a3880e02baa21`
- Verified upstream `main` merge: `353469f93b475a8c9376ae22d915c5e43ce80ce0`
- The feature branch is an ancestor of that upstream `main` commit. Its files were integrated selectively into FutureSkill's current FastAPI application; upstream `main.py`, database, routes, and assessment results were not copied over.
- Local implementation branch: `feature/interview-practice-integration`. Changes are committed locally only; they are not pushed or merged to `main`.

## Reused and adapted files

The interview feature's question generation, coaching dimensions and weights, adaptive question policy, report calculations, and duplicate-question rules come from the upstream feature:

- `src/hr_interview/interview_engine.py`
- `src/hr_interview/question_policy.py`
- `src/hr_interview/semantic_validator.py`
- `src/hr_interview/speech_service.py`

The Flask route layer and browser page are adapted from the same source:

- `src/hr_interview/app.py`
- `src/hr_interview/career_data.py`
- `src/hr_interview/history_store.py`
- `src/hr_interview/templates/interview.html`
- `src/hr_interview/static/interview.js`
- `src/hr_interview/static/interview.css`

The Flask app is mounted at `/interview-practice/` using `a2wsgi`. It does not replace or shadow the FutureSkill root page, existing `/api/careers`, assessment, reskilling, or recommendation routes. The feature now looks up titles and IDs in the canonical 923-row FutureSkill CSV and does not fall back to the upstream demo-career list. Each selected title is checked against the same canonical ID.

The existing career detail page links to general title-based practice for the explicitly viewed career. The reskilling workspace has one Interview practice route and a dashboard entry that appears only for a saved target. Opening either route does not change that target. Its History link opens reports saved by the existing feature in the current browser. The entry, app mount, and dependency changes are in `src/main.py`, `src/static/career-workspace.js`, `src/reskilling/index.html`, `src/reskilling/static/app.js`, `src/reskilling/static/style.css`, and `requirements.txt`.

## Provider, input, and storage boundaries

- `GET /interview-practice/api/interview/availability` checks server-side provider configuration only; it does not make a provider request. Without configuration, the screen and history remain available and a start attempt returns the explicit message “AI interview practice is temporarily unavailable.” No simulated review is shown.
- The existing `ProviderSettings` configuration from the pathway explanation service supplies credentials. No secret is rendered to the browser, included in error messages, or logged.
- Real question generation, feedback, transcription, model availability and timeout behavior were not live-tested because no provider credentials are configured in this workspace. Automated success-path tests use local mocks and do not contact an LLM.
- The CSV has occupation titles and RIASEC values, but no sourced role skills, duties or descriptions. The feature therefore labels practice as general career-title practice; it does not invent occupation requirements.
- Interview answers and generated feedback are held temporarily in server memory for the active interview (one-hour session expiry) and are not inserted into the interview SQLite database. The database stores pseudonymous guest IDs, career titles and question text for repeat-question checks. Audio is processed only after the learner chooses voice input and requests transcription; it is not retained by this feature.
- Completed reports, including the learner's answer text, are saved in browser `localStorage` under the feature's existing report key. Learners can delete those reports from the history screen or clear browser site data.
- The existing feature has no account authentication, request quotas or rate limiting. Before public exposure, add abuse controls, account/data-retention decisions and deployment-appropriate secure cookie handling.

## Language and report copy

Static interface copy uses FutureSkill's shared English, Chinese and Malay language packs and preference in Settings. On initial load, the interview feedback language follows that preference; learners can choose a different language for the interview session without changing the global preference. Generated feedback remains in the chosen session language. Canonical career titles and generated learner/model text are not rewritten by the UI translator.

The upstream coaching score formula and report calculations are unchanged. The UI presents the report as subjective practice feedback and converts its threshold status into neutral reflection copy instead of showing job-readiness or application advice. Numerical scores, dimensions, and answer feedback remain the source values.

## Verification

Focused API tests cover page/static mounting, the full career catalogue, explicit provider unavailability, invalid inputs, provider exceptions, malformed provider JSON, a mocked three-question start/feedback/next/report flow, and the server-side answer-storage boundary. Language-pack tests check matching keys and interpolation slots in all three packs.

These tests do not establish model quality, source-question performance with a real provider, or public-launch readiness.
