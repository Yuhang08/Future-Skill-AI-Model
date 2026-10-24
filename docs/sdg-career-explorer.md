> **Current implementation:** The explorer distinguishes task-derived Goal
> rankings, narrow task-to-Target rule candidates, weaker exploratory
> suggestions, and FutureSkill learning-preparation examples. None is a
> reviewed or measured SDG outcome. See
> [sdg-923-rule-based.md](sdg-923-rule-based.md) for the ranking method.

# SDG career explorer: diagnosis and selection contract

## Workspace diagnosis

- `static/sdg-impact.html` is the current page; it renders the 17 Goal scores,
  task evidence, evidence drawers and the separate learning pathway.
- `reskilling/extra_features.py` serves `POST /api/sdg/mindmap`.
- `reskilling/sdg_alignment.py` keeps task-to-Target rule candidates,
  exploratory occupation suggestions and learning-pathway examples separate.
  The ranking is deterministic; it does not call an LLM.
- `career_profiles_clean.csv` supplies 923 occupational names and O*NET-SOC
  identifiers. Its interest ratings are not occupational requirement evidence.
- `reskilling/catalog.py` supplies the existing illustrative pathway skills
  and practice activities. This change does not alter targets, scoring,
  saved profiles or scheduling.
- `data/onet_task_statements.csv` supplies O*NET 31.0 task statements. These
  describe occupation duties; the Goal-ranking and matching rules are
  FutureSkill-created and are not endorsed by O*NET or the UN.

The previous UI accepted arbitrary nonempty text as a displayed career. The
mapping service already avoided a default SDG 8 link, but did not distinguish
an unknown phrase from a supported career without a reviewed mapping.

Learning-preparation links that existed before the task model remain under
`learning_pathway_mappings`; they are not occupation mappings. A task-derived
score does not upgrade a pathway example or weak suggestion into a verified
relationship.

## Canonical selection

`GET /api/sdg/careers?q=...` returns up to 12 suggestions containing:

- `id`, `title`, `kind` (`occupation` or `prototype`)
- `mapping_availability: suggested` (a search suggestion, not a reviewed
  relationship)
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

- Unknown text cannot become a selected career or obtain a mapping. Requests
  accept a canonical catalogue ID; unsupported IDs return 404.
- For a real occupation, `goal_scores` contains all 17 deterministic,
  task-derived thematic indices (0–100); `top_goal_scores` is the top three.
  An index is not a probability, percentage, impact measure, certification or
  official UN mapping. Weak exploratory rankings are labeled as such.
- `mappings` contains narrow O*NET task-to-Target rule candidates only. Each
  includes original Task IDs and wording, the matching rationale, source IDs
  and limitations. `task_signal_unreviewed` means candidate, not human-verified
  relationship.
- `candidate_mappings` distinguishes task-topic, DWA-topic and
  classification-only suggestions. These are weaker than a strict task rule;
  title/SOC similarity alone is not task evidence.
- `learning_pathway_mappings` is a separate FutureSkill learning-preparation
  example, retaining its target, rationale and source links. Its
  `curated_illustrative` label does not mean independent occupational or
  impact review.
- `task_data_status` describes data availability; `status` distinguishes a
  task-supported candidate, no task-to-Target candidate, and unknown career.
  No match does not prove that a career has no possible connection.
- O*NET records describe duties; UN Goal pages define goals/targets. Neither
  source independently supports the FutureSkill matching rules or proves an
  occupational outcome. The ranking runs only for real O*NET occupations;
  catalogue prototypes do not receive invented task scores.

The reskilling page also displays completed practice milestones derived from
completed learning-task hours. The count is capped by the existing self-rating
gap and estimated practice hours. It does not change skill ratings, targets,
gaps, saved task records or XP, and it is not evidence of proficiency.

## Remaining evidence gap

The strict task rules and broad scoring vocabulary are heuristic and have not
been independently benchmarked or human-reviewed as occupation-to-Target
relationships. Do not present candidates as curated or verified. Future review
requires documented criteria and evidence of what was and was not established.
Existing pathway links remain illustrative.

## Verification

Automated checks cover career selection/API states, task score output, source
IDs, strict Target precision and completed-practice-level calculation. Record
their latest results separately from browser screenshots and any provider
inference; the deterministic SDG endpoints do not call an LLM.
