# SDG career explorer: diagnosis and selection contract

## Workspace diagnosis

- `static/sdg-impact.html` is the current page; it renders all 17 goals, compact
  mapping cards, evidence drawers and the optional learning pathway.
- `reskilling/extra_features.py` serves `POST /api/sdg/mindmap`.
- `reskilling/sdg_alignment.py` contains the curated, illustrative target links.
  It does not use a keyword mapper or an LLM to generate target relationships.
- `career_profiles_clean.csv` supplies 923 occupational names and O*NET-SOC
  identifiers. Its interest ratings are not occupational requirement evidence.
- `reskilling/catalog.py` supplies the existing illustrative pathway skills
  and practice activities. This change does not alter targets, scoring,
  saved profiles or scheduling.

The previous UI accepted arbitrary nonempty text as a displayed career. The
mapping service already avoided a default SDG 8 link, but did not distinguish
an unknown phrase from a supported career without a reviewed mapping.

According to the supplied reference findings, the GitHub/older Render screenshots
represent a different implementation:
their Environmental Engineer links to SDGs 13 and 9 must not be treated as
evidence or copied into this workspace. Data Analyst here retains its existing
illustrative Target 4.4 and 8.5 preparation links.

## Canonical selection

`GET /api/sdg/careers?q=...` returns up to 12 suggestions containing:

- `id`, `title`, `kind` (`occupation` or `prototype`)
- `mapping_availability` (`curated` or `not_reviewed`)
- `matched_by` (`exact`, `partial`, `suggestion`, or `featured`)

Names normalize case, punctuation and whitespace. Singular Environmental
Engineer is an explicit alias of **Environmental Engineers, `17-2081.00`**.
Partial and spelling matches only produce suggestions and never select a role.
The UI requires an explicit choice; editing its text invalidates the choice.
An exact single match can be selected with Enter; ambiguous/fuzzy choices need
an explicit highlighted option or pointer selection.

Prototype titles missing from the occupational CSV retain separate IDs:
`prototype:data-analyst`, `prototype:cybersecurity-analyst`,
`prototype:ui-ux-designer`, and `prototype:digital-marketing-specialist`.
They are not silently assigned occupational codes. Existing curated links for
Software Developers and the prior Information Security Analysts / Web and
Digital Interface Designers aliases remain associated with their actual
occupational IDs, without merging their identities into the prototypes.

`POST /api/sdg/mindmap` accepts only:

```json
{"career_id":"17-2081.00"}
```

A missing/empty/oversized ID is rejected by request validation; an unsupported
ID returns 404. Free-text `title` and client-supplied `skills` are not accepted.
The page reads confirmed saved profile data through the existing state API
only for a matching pathway; no fabricated skill ratings are sent.

## Mapping and evidence states

- Unknown text cannot become a selected career or obtain a mapping.
- Known but unreviewed careers return `status: not_reviewed`, canonical title
  and ID, no target links and no pathway requirements.
- Curated links retain their original rationale, full evidence wording,
  target IDs, source URLs and limitations. Additional metadata records
  canonical `career_id`, `review_status: curated_illustrative`,
  `mapping_kind`, source IDs and each source's scope.
- UN goal pages define targets; they do not establish occupational links.
  The pathway catalogue remains explicitly illustrative.
- All 17 goals are independently browsable before selection and after a failed
  request. “Not reviewed” never means “no possible SDG connection.”

## Remaining evidence gap

This workspace has no reviewed, target-level occupational evidence supporting
Environmental Engineers → SDG 13/9. Its occupational CSV record proves catalogue
membership, not that relationship. It therefore remains explicitly unreviewed;
legacy keyword suggestions are not promoted to curated mappings.

Existing pathway-based links also remain illustrative, not independently
validated occupational or social-impact claims. No new external evidence is
invented by this repair.

## Verification

Run `python -B -m unittest discover -s tests -p 'test_*.py' -q`,
`node tests/sdg_browser.cjs`, and `node tests/theme_browser.cjs`.
The SDG browser suite checks real catalogue/API requests, keyboard selection,
editing, ambiguous/fuzzy choices, API errors, evidence drawers and mobile/theme
layout. Its stale-search race uses real API bodies with controlled delivery
order. Browser screenshots are kept in `/tmp`, not shipped with the app.

Completed verification:

- 42 Python tests passed, including 7 dedicated career identity/evidence tests.
- 11 SDG browser check groups passed, including native keyboard input, stale
  search responses, real network-error recovery and evidence-source parity.
- Shared theme regression checks passed across 6 routes in desktop/mobile,
  light/dark modes.
- Preview was visually checked, including the new search and dark mobile layout.
  Search labels and the career-center label are checked at >=4.5:1 contrast.

## Exact changed files

- `reskilling/extra_features.py`
- `reskilling/sdg_alignment.py`
- `static/sdg-impact.html`
- `static/sdg-career-search.js`
- `static/future-pages.css`
- `tests/test_sdg_careers.py`
- `tests/test_integration.py`
- `tests/sdg_browser.cjs`
- `tests/theme_browser.cjs`
- `artifacts/mockup-sandbox-preview/scripts/extract-futureskill.py`
- `docs/sdg-career-explorer.md`
- `.agents/memory/sdg-disclosure-scope.md` (durable evidence-policy context only)

No occupational CSV, assessment scoring, profile storage, scheduling, model
provider configuration or deployment files were changed. Preview remains
running; no publish or remote push was performed.
