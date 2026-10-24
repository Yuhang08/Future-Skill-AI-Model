# FutureSkill AI: 923 careers and evidence-limited SDG suggestions

## What changed

The 923 O*NET-SOC occupational entries from `src/career_profiles_clean.csv`
have searchable identifiers. **The occupation mind map no longer inherits SDG 4
or SDG 8 from FutureSkill's training programme.** These links are separate.

The occupation map is **NOT a verified SDG contribution or target-impact
model**. Our source CSV contains occupation names, O*NET-SOC codes and RIASEC
interest dimensions — not occupational Task Statements or measured impacts.

## Two deliberately separate outputs

`POST /api/sdg/mindmap`, with a canonical `career_id`:

- `mappings`: possible goal-level occupational themes based on **specific
  phrases** in titles, otherwise broad SOC-major-group classifications.
  Each has `target_id: null`, `mapping_kind: occupation_theme`,
  `review_status: rule_based_suggestion`, and `specificity` of
  `title_rule` or `soc_group`. Neither has been validated as an
  occupation-to-target impact claim.
- `learning_pathway_mappings`: original limited, illustrative FutureSkill
  training links to Targets 4.4 and 8.5, **only where that learning
  pathway exists**. Shown in a separate disclosure, never as career map nodes.
- `pathway_skills`: existing illustrative learning requirements, unaffected.
- `status: suggested`: the career map is not independently reviewed.

A SOC-group link is deliberately **broad** and explicitly identified as such.
Do not present 923 available suggestions as 923 validated occupational
contribution judgments.

## Illustrative examples (not externally verified)

| Occupation | Career map | Separate FutureSkill learning links |
| --- | --- | --- |
| Data Analyst (prototype, not O*NET CSV identity) | Goal 9 | 4.4, 8.5 |
| Software Developers (15-1252.00) | Goal 9 | 4.4, 8.5 |
| Information Security Analysts (15-1212.00) | Goals 9 and 16 | 4.4, 8.5 |
| Environmental Engineers (17-2081.00) | Goals 6, 9, 13 | none |
| Registered Nurses (29-1141.00) | Goal 3 | none |
| Solar Energy Systems Engineers (17-2199.11) | Goals 7, 9, 13 | none |
| Marine Engineers and Naval Architects (17-2121.00) | Goal 9, broad occupational-group suggestion | none |

SDG 4 can be relevant for a teacher or a software developer **specifically**
working on a documented education intervention; it is not a default for
a general software job. SDG 8 is not automatic simply because a job exists.

## Inputs and verification

O*NET 31.0 publishes **Task Statements** associated with occupation codes.
This prototype does not fetch, bundle or evaluate those statements. A stronger
future version can assess the actual occupational tasks against carefully
selected UN SDG targets and retain the Task IDs as auditable evidence.

* Official O*NET 31.0 Task Statements:
  https://www.onetcenter.org/dictionary/31.0/csv/task_statements.html
* O*NET taxonomy: https://www.onetcenter.org/taxonomy.html
* UN SDGs: https://sdgs.un.org/goals
* O*NET license/attribution: https://www.onetcenter.org/database.html

O*NET task and occupation data is not proof of SDG impact. The final connection
still requires human target review and outcome evidence. This project's
rule-to-goal mappings are authored FutureSkill heuristics, not UN or O*NET
endorsements.

## Running the checks

From the repository root (Windows PowerShell):

```powershell
git switch feature/all-923-career-sdg-mapping
git pull --ff-only origin feature/all-923-career-sdg-mapping
$env:PYTHONPATH="src"
python -m unittest discover -s tests -p "test_sdg_careers.py" -v
python -m unittest discover -s tests -p "test_integration.py" -v
python -m uvicorn main:app --app-dir src --reload --port 5000
```

Open `http://127.0.0.1:5000/sdg-impact` and compare Data Analyst
and Software Developers. The central map should show Goal 9 only for
those career-specific examples, with Goals 4/8 accessible solely in the
distinct FutureSkill learning section.
