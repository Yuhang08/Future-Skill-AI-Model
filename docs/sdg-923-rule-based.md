# Task-based SDG relevance: method and evidence boundaries

## Four separate outputs

1. **Goal rankings** compare genuine occupation tasks with FutureSkill-authored
   themes for all 17 Goals. The top three are exploratory rankings, including
   weak results; they are not three established connections.
2. **Task-to-Target candidates** require narrower task-rule matches. Their
   `task_signal_unreviewed` status is not human review or verified impact.
3. **Other suggestions** distinguish task-topic, linked-DWA-topic and
   classification-only guesses. Title/SOC resemblance is not task evidence.
4. **Learning-preparation examples** describe FutureSkill practice activities
   under Targets 4.4 and 8.5, not occupational SDG contributions.

The diagram preserves these distinctions. Solid edges are unreviewed narrow
Target hypotheses; dashed edges are exploratory rankings or tentative ideas.
Displaying an index for every Goal does not assign every occupation to it.

## Reproducible heuristic

For each actual O*NET task and Goal:

```text
TextSignal =
    1.00 × min(2, direct task phrase hits)
  + 0.42 × min(2, officially linked DWA phrase hits)
  + 0.45 × bounded lexical similarity

TaskWeight =
    (1.00 for Core tasks, otherwise 0.70)
  × (0.70 + 0.30 × importance / 5)
  × (0.80 + 0.20 × relevance / 100)

TaskEvidence = TaskWeight × TextSignal

CareerRaw =
    sum of up to three highest positive TaskEvidence values / 3
  + 0.035 × ln(1 + number of task scores >= 0.08)

RelevanceIndex = round(100 × CareerRaw / (1.50 + CareerRaw), 1)
```

Missing top-task slots contribute zero. Lexical similarity combines bounded
word overlap (0.85) and character-gram overlap (0.15).
If occupational importance/relevance metadata is absent, the model uses neutral
ordering assumptions of 0.6 and 0.7 respectively; these are not displayed as
observed O*NET ratings. Optional DWA and Task Ratings files are **not installed
in this integration**.

Phrase banks, weights and index scaling are FutureSkill assumptions, not
empirically calibrated probabilities. Ties use Goal ID ordering. A high index
does not demonstrate an outcome; a low index does not prove no possible role
connection. The model is deterministic and calls no LLM.

## API and interface

`POST /api/sdg/mindmap` accepts a selected canonical identity:

```json
{"career_id":"17-2199.11"}
```

Real O*NET occupations return 17 `goal_scores`, three `top_goal_scores`,
`goal_scoring_method`, and separate `mappings`, `candidate_mappings` and
`learning_pathway_mappings`. Scores expose Task IDs/text, match phrases,
individual contributions, evidence basis, review status and source URLs.
Prototype roles have explicit IDs and do not receive invented occupation tasks.
Unknown IDs return 404; arbitrary free text is not a selected career.

The page keeps comparison indices concise. “Why this ranking?” disclosures,
Goal dialogs and Target drawers provide the task wording, sources, rationale
and limitations. Existing learning pathways remain available independently
of whether an occupation has a narrow task-to-Target match.

## Official source records

| Source ID | Publisher / version | Supports |
|---|---|---|
| `onet-task-statements` | USDOL/ETA, O*NET 31.0 | Occupation-specific task wording, IDs and task type only |
| `un-sdg-target-{target}` / `un-sdg-goal-{goal}` | United Nations | Official Goal/Target definitions, not the FutureSkill occupational interpretation |
| `onet-task-dwa` (optional) | USDOL/ETA, O*NET 31.0 | A detailed work activity linked to an actual Task ID |
| `onet-task-ratings` (optional) | USDOL/ETA, O*NET 31.0 | Occupational task importance/relevance, not SDG likelihood |
| `futureskill-reskilling-catalogue` | FutureSkill | Illustrative pathway skills and practice only |

- [O*NET 31.0 Task Statements documentation](https://www.onetcenter.org/dictionary/31.0/csv/task_statements.html)
- [Official versioned CSV](https://www.onetcenter.org/dl_files/database/db_31_0_csv/task_statements.csv)
- [O*NET database license](https://www.onetcenter.org/license_db.html):
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- [United Nations Goals and Targets](https://sdgs.un.org/goals)
- [O*NET Tasks-to-DWAs documentation](https://www.onetcenter.org/dictionary/31.0/csv/tasks_to_dwas.html)
- [O*NET Task Ratings documentation](https://www.onetcenter.org/dictionary/31.0/csv/task_ratings.html)

The included CSV contains 18,838 source records. During integration, every
header and record matched the official 31.0 CSV; Git-normalized line endings
explain the byte difference. Local SHA-256:
`782681605b008ad2727f7ca954bf5216dfdad56097f5d3d07d1e3455e2abc134`.
O*NET® is a trademark of USDOL/ETA. FutureSkill is not endorsed by USDOL/ETA or
the UN. O*NET describes U.S. occupations, not Malaysian-specific job outcomes.

## Audits and exports

`PYTHONPATH=src python scripts/audit_sdg_task_evidence.py` is read-only.
The export scripts create files under `reports/`; inspect their destinations
before running them. They were not run during this integration, and no existing
evidence export was overwritten. The full score matrix has 923 × 17 = 15,691
indices, not 15,691 substantiated occupational relationships.

See [integration verification](sdg-integration-verification.md) for observed
coverage, tests, preserved functionality and missing evidence. Human semantic
review and an independent benchmark are still needed before making claims
about occupational mapping accuracy or real SDG impact.
