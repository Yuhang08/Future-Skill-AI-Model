# FutureSkill AI: 923-career SDG goal suggestions

## Scope and honesty

The source catalogue in `src/career_profiles_clean.csv` has exactly 923
distinct O*NET data-level occupation rows. This release keeps those O*NET-SOC
identities, along with a few distinct namespaced demonstration-role identities.

**This is not a verified occupational SDG impact model.**
O*NET supplies occupation names and classifications. The official UN SDG pages
define goals and targets; neither independently establishes which goal a
particular career advances, or what impact is achieved.

## Decision method

1. A user selects an occupation ID from `GET /api/sdg/careers`; arbitrary
   input text cannot be treated as a career.
2. `sdg_occupation_rules.py` checks ordered title-based themes (for instance,
   "Environmental Engineers" → Goals 6, 9, 13; "Registered Nurses" → Goal 3).
3. Where there is no specific title rule, the first two O*NET-SOC digits
   identify an SOC major occupational group, which supplies a broad *topic*
   (for example, software and mathematical occupations → Goal 9).
4. A career is returned with at least one `mapping_kind=occupation_theme`
   suggestion; `review_status=rule_based_suggestion` identifies the method.
   Such suggestions use `target_id=null`, never manufactured target numbers.
5. Pre-existing **curated, illustrative pathway-preparation** links to UN
   targets 4.4 and 8.5 remain unchanged. Specialty-based *goal* suggestions
   may be displayed beside them, without repeating an SDG icon.
6. `/sdg-impact` shows the reason, classification trigger, external source
   scope and limitations, and highlights matching goals in its 17-goal graph.

SOC major-group fallback intentionally produces shared results across many
roles. The occupation-title rule takes precedence; these are still **candidate
connections, not bespoke expert assessments**. Users must check actual tasks
and collect role-specific outcome evidence before presenting a stronger claim.

## Examples

| Career | O*NET-SOC ID | Proposed goals | Kind |
| --- | --- | --- | --- |
| Environmental Engineers | 17-2081.00 | 6, 9, 13 | Rule-based occupation theme |
| Registered Nurses | 29-1141.00 | 3 | Rule-based occupation theme |
| Solar Energy Systems Engineers | 17-2199.11 | 7, 9, 13 | Rule-based occupation theme |
| Software Developers | 15-1252.00 | 4 and 8 (prior curated *learning* links); 9 (occupational theme) | Mixed |
| Data Analyst (prototype) | prototype:data-analyst | 4 and 8 (prior learning links); 9 (occupational theme) | Mixed |

## Technical contract

- Search `mapping_availability`: `curated` or `suggested`.
- Mindmap `status`: `curated` for original pathways, `suggested` for
  catalogue occupations without curated learning-pathway links.
- New mapping metadata includes `match_basis`,
  `mapping_kind=occupation_theme`, `review_status=rule_based_suggestion`,
  `target_id=null`, rationale, source scope and explicit limits.
- Do not use these thematic suggestions as verified performance claims or
  evidence that an employer will advance an SDG.

## Verification before merge

From the repository root:

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
python -m uvicorn main:app --app-dir src --port 5000
# In another terminal, where Chrome/Chromium is available:
node tests/sdg_browser.cjs
```

Windows PowerShell substitute: `$env:PYTHONPATH = "src"` before running
the unittest command.

## References

- Occupational identities and structure:
  https://www.onetcenter.org/taxonomy.html
- Official SDG list and descriptions:
  https://sdgs.un.org/goals
- Existing project-specific source and evidence disclosures:
  `docs/sdg-career-explorer.md`

Those pages define their respective systems. The rule connections are an
**authored FutureSkill prototype heuristic**, not authored by O*NET or UN.
