# Replit upload review

Upload branch: `feature/replit-sdg-current-update`.
Target repository: `Yuhang08/Future-Skill-AI-Model`.
PR target: `main`.

## Preserved application

The branch preserves the complete local integration history, including
`3cd7e18` (task-based SDG integration) and `70fe1a8` (goal-list and unified
evidence-drawer refinement). It shares history with remote main at
`a4e53e4beb538bc1e6c9d545362e421193499f6c`. No main merge, reset, source
re-import, scoring change or history rewrite was needed.

Application code, O*NET source data, licensed graphics, tests, configuration
templates and documentation are retained. Existing unrelated main files
are not replaced with a duplicate application.

## Upload exclusions

Twelve previously tracked legacy runtime files are removed from this branch's
current tree only: eleven compiled Python cache files and
`test/FutureSkill AI_Model/FutureSkill_AI_Integrated/instance/futureskill.sqlite3`.
Their local copies remain intact and ignored.

The database also exists in remote main's older history. This change does not
purge historical copies. A history purge would require separately approved,
coordinated history rewriting, contrary to this upload's instructions.

Existing ignore rules exclude environment secrets, learner databases,
uploads, CVs, session data, dependencies, caches, attached files and generated
screenshots/reports. The tracked `.env.example` has an empty provider-key
field and is retained as a configuration template. No real credential was
found in the tracked-tree checks or high-confidence credential-pattern scan
of the 240 unique blobs in local-only history. A credential-bearing URL
pattern in a security test is synthetic test data, not a working credential.
Pattern scanning cannot guarantee the absence of every possible secret.

## Validation

Run for this upload:

- Full Python test discovery: **93 tests passed**.
- Preview `/sdg-impact`: **HTTP 200**.
- Tracked-file and ignore-rule review; excluded files remain on disk.
- Common-ancestor and commit-preservation checks.

Previously run on the unchanged application at `70fe1a8`:

- SDG browser suite: **16 check groups passed**.
- Shared-theme browser suite: **18 check groups passed**.
- Four complete SDG API responses matched their pre-refinement snapshots.

Browser checks are prior results, not new runs for this upload. No application
code changed during upload preparation. No actual LLM inference was run.
Main, Replit publishing and external deployment settings are unchanged.
