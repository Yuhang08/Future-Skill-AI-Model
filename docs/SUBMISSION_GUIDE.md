# FutureSkill AI — Submission Code Guide

This branch is a **non-deploying submission workspace** created to organize judging documentation without changing the website's interface, algorithms, data, or deployment.

## Feature directory plan (not yet migrated)

| Feature | Proposed folder | Code to inventory |
|---|---|---|
| Career assessment | `modules/career_assessment/` | Questionnaire, RIASEC scoring, matching/ranking |
| AI trends | `modules/ai_trend/` | Historical series, projections, explanations |
| Personalized reskilling | `modules/reskilling/` | Skill gaps, learning pathway, progress |
| SDG mapping | `modules/sdg_mapping/` | Task-to-SDG relevance and scoring |
| Chat / AI explanations (if present) | `modules/ai_chatbot/` | API integrations, prompts, explanations |
| Web frontend | Existing templates/static locations | UI, language selection, graphics |

**Important:** These paths are *proposed*, not verified locations of currently running code. Do not move executable files until real import paths, dataset paths, and production entrypoint have been traced.

## Paperwork mapping

For each function record:
1. User-facing feature and example usage.
2. Exact source code path, class/function name and inputs/outputs.
3. Formula, model and data sources actually used.
4. API/service disclosure and limitations.
5. Evidence of tests and a link to the live feature.

## Safety checklist before restructuring

- Identify the actual Render production branch and application entrypoint.
- Create a commit/tag of the working version.
- Preserve every original function, endpoint and frontend asset.
- Confirm imports, template/static paths and relative CSV paths.
- Verify full 923-career coverage where implemented.
- Run all key features locally or in staging.
- Merge only after working output matches the deployed version.

Do not commit .env, access tokens, API keys, cached credentials, or user data.
