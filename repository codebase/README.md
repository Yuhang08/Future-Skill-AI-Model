# Repository Codebase — FutureSkill AI

This directory contains **read-only organizational copies** of verified source files from the repository's `main` branch, copied for judging and paperwork review on `submission-structure-20261025`.

**The website does not run from this directory.** Do not deploy it as a standalone application. Executable files retain their original live locations under `src/`. No live routes, imports, styling, logic, or dataset paths were changed.

## Modules and original paths

| Folder | Function | Original code path |
|---|---|---|
| `00_application/` | App entrypoint, integrated services and routes | `src/main.py` |
| `01_career_assessment/` | Career matching / scoring engine | `src/career_engine.py` |
| `02_ai_trend/` | Trend feature page | `src/static/ai-trend.html` |
| `03_reskilling/` | Career catalog, occupation skills, reskilling frontend | `src/reskilling/` (selected files) |
| `04_sdg_mapping/` | SDG impact page | `src/static/sdg-impact.html` |
| `05_frontend/` | Homepage, workspace, styling, dynamic effects | `src/static/` (selected files) |
| `06_multilingual/` | Language translation code and locale packs | `src/static/future-i18n.js`, `src/static/js/`, `src/static/locales/` (selected files) |

## Important limitations of this snapshot

- This is a **partial verified code archive**, not yet every file used by the live site.
- Some Python backend functions for different features may still live together in `src/main.py`, and copying it does not separate their implementations.
- Large datasets, fonts, logos, binaries, further feature pages, extra modules and package/runtime dependencies have not all been inventoried or copied.
- Some front-end copies retain references to their **original** locations and are for inspection, not execution.
- `main` may not be the branch currently deployed to Render; live deployment branch has not been confirmed.
- Do not treat these copies as evidence that every module is independently runnable.

For functional verification, use the original application under `src/` until a separate full migration and regression test is completed.
