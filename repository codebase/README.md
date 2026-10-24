# FutureSkill AI — Repository Codebase

## Important: Render-safe source of truth

**The complete running application is the original repository structure, particularly `src/` and the root deployment/dependency files.** This submission directory is *documentation and supplementary grouped source snapshots only*. The snapshots are **not** intended to be deployed or used as an alternate application root.

Do not delete, move, rename or replace files under `src/`, or change `requirements.txt`, production start command, environment variables, runtime data paths, or the Render deployment branch just to make the submission folders look cleaner.

### Canonical code links

- [Production project source (main/src)](../../src)
- [Root dependency and deployment configuration](../../)
- [Original tests](../../tests)

### Snapshots by function (not exhaustive)

- `00_application/`: app entrypoint and requirements copy
- `01_career_assessment/`: career matching snapshot
- `02_future_job_trend/`: trend page snapshot
- `04_reskilling/`: selected reskilling modules, pages and JS
- `05_sdg_mapping/`: SDG page snapshot
- `06_frontend/`: selected frontend files
- `07_multilingual/`: selected language scripts and locale data
- `08_interview/`: interview HTML snapshot
- `09_tests/`: selected tests

**These are not every dependency.** Actual backend functionality includes additional modules in `src/reskilling/`, `src/hr_interview/`, data files and assets. Shared modules (including `src/main.py`) cannot be independently run from feature folders without preserving dependencies and relative paths.

### Submission guidance

To cite a feature in paperwork, always link to the **real source file under `src/`**, not just its duplicate in this folder. This ensures reviewers inspect exactly what is deployed. Use the feature folders for navigation and illustrative grouped copies only.

### Archive completeness

Until the full Git tree and the precise Render deployment branch are verified, **do not claim that this archive contains every source or asset**. Preserve the original file tree as the authoritative, complete runnable project.

- `03_employability_predictor/`: employability predictor archived page
- `10_ai_explanations/`: AI explanation API, provider and service snapshots
