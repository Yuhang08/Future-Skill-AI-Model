# Current Replit source snapshot for GitHub

## Repository and branch policy

- Repository: `Yuhang08/Future-Skill-AI-Model`.
- Review branch: `feature/replit-current-update`.
- Source application baseline: Replit commit `a91cf66`.
- Compared feature branch: `feature/career-catalogue-sdg-search`, commit `7a81a6d`.
- Fetched GitHub main: `7b040cb`.
- No merge into main, production change, deployment, or auto-deploy branch push
  is authorized by this handoff.

The Replit and GitHub histories have no common ancestor. GitHub also keeps its
application under `test/FutureSkill AI_Model/FutureSkill_AI_Integrated/`, whereas
this snapshot keeps the working application at repository root.

The review branch is an isolated source-snapshot commit, without checkpoint or
legacy repository ancestry. It is not intended for an automatic whole-branch
merge. Existing local files and history are preserved separately and are not
deleted to construct this snapshot.

## What is included

The current application, assessment and reskilling services, deterministic
matching/scoring/scheduling, bounded skill-gap explanation service, tests,
documentation, and the design-preview source are preserved.

The newer UI includes shared light/dark styling, assessment question navigation,
draft recovery and unanswered-question guidance, an uncertainty chart, and the
SDG explorer with horizontal summaries, evidence drawers, attributed photography,
official icons, and canonical career selection.

LLM provider configuration is not changed. Mocked provider tests do not establish
that real inference is configured or available.

## Privacy and packaging audit

The export uses a tracked-source allowlist plus explicit exclusions and a text
credential-pattern scan. It does not copy arbitrary untracked workspace files.

Excluded from the snapshot:

- `.env` files, private keys, secret files and credential files.
- `instance/`, upload directories, learner SQLite databases and database journals.
- Uploaded reference assets and the original import archive.
- Virtual environments, dependencies, caches, browser profiles, generated build
  output, Replit-internal metadata and agent memory.
- Checkpoint history containing older versions of excluded files.

Official, source-attributed SDG icons and stock photographs used by the app are
application assets, not learner-uploaded photos. They remain included.

Design fixtures are generated in isolated temporary data directories using
synthetic demo profiles. Their preview CSRF values are replaced with a public
preview-only placeholder in this snapshot; no live session token is exported.

The credential URL found in `tests/test_explanation_service.py` is an intentional
invalid `.test` URL fixture, not a real account credential. No credential values
are printed in audit output.

**Existing remote exposure:** fetched GitHub main already tracks
`test/FutureSkill AI_Model/FutureSkill_AI_Integrated/instance/futureskill.sqlite3`.
Its contents were not opened. It is excluded from this snapshot. No existing
remote history has been rewritten; review of that pre-existing file is separate.

Pattern scans cannot guarantee absence of every possible secret. The staged
file paths, binary asset locations and synthetic-fixture provenance are also
checked before the snapshot is committed.

## Combining with the catalogue/search branch

Keep this version's SDG UI and curated illustrative evidence as the application
baseline. Do not overwrite the page with the older radial-map implementation.

Potential selective reuse:

- A separately maintained catalogue module.
- A declarative mapping registry with strict source, target and review metadata
  validation.
- Multi-word search, configurable result limits and catalogue counts.
- Additional reviewed-record fixture tests.

Resolve these differences explicitly before porting:

1. **IDs:** this version uses occupational IDs such as `17-2081.00`; the other
   branch prefixes them with `onet:`. Its UI/UX prototype also contains a slash
   rather than this version's `prototype:ui-ux-designer`. It adds a separate
   Software Developer prototype where this version uses an occupational record.
2. **Search:** this version uses `/api/sdg/careers`; the other uses `/api/careers`.
   Preserve the current frontend contract or implement an explicit adapter.
3. **Mapping responses:** this version returns `status`, `mappings`, and
   `pathway_skills`; the other returns `mapping_status`, `goals`, `suggestions`,
   `skills`, and `all_goals`.
4. **Requests:** retain this version's selected-ID-only validation. Do not
   reintroduce arbitrary title submission or caller-supplied skill ratings.
5. **Data:** the other branch's reviewed-mappings JSON is empty. Preserve all
   current role associations, target text, source IDs, evidence and limitations;
   an empty registry must not replace them.
6. **Evidence strength:** retain `curated_illustrative` labels. Migrating a record
   does not turn it into independently validated occupational impact evidence.
7. **Environmental Engineers:** the other branch suggests SDGs 13 and 9 through
   keyword rules. Those are not reviewed target-level evidence. Keep the current
   `not_reviewed` result unless genuine evidence is reviewed separately.
8. **UI:** retain shared navigation, light/dark mode, horizontal summaries,
   evidence drawers, official images, all-goal browsing without career selection,
   canonical selection, stale-response protection and saved-profile handling.

The occupational CSV is byte-for-byte identical. No replacement is needed.

## Verification performed on the source application

- `python -B -m unittest discover -s tests -p 'test_*.py' -q`:
  **42 tests passed**.
- `node --test tests/assessment_progress.test.cjs`:
  passed, including **22 invalid/expired/incompatible draft cases**.
- `node tests/sdg_browser.cjs`: all **11 check groups passed**.
- `node tests/theme_browser.cjs`: all checks passed across **6 routes** in
  desktop/mobile and light/dark modes.
- `node tests/assessment_browser.cjs`: all **7 check groups passed**, including
  the real 42-answer recommendation flow and required-question navigation.
- `PORT=22117 BASE_PATH=/__mockup/ npm --prefix artifacts/mockup-sandbox-preview run build`:
  production build passed. This design-preview build requires both non-secret
  configuration variables; invoking it without them fails during config loading.

The source application remains running in Preview. No real-model smoke test was
run as part of this GitHub preparation.
