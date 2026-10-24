## Upgrade: 923 role-specific analyses (not 923 verified impacts)

The prior strict task rules matched 280 of 923 careers in the first local
audit; 643 had no *strict* task-to-target match. The newer analysis
**does not force those 643 occupations into a supposedly proven UN target**.

All 923 now receive a structured result:
- **Task-to-target hypotheses:** prior strict rules, with real O*NET Task IDs;
  mapped as main links. They remain unreviewed.
- **Task-topic suggestions:** broader but distinctive topics extracted from
  real job-task text, showing the source Task IDs. These are dashed,
  unverified **goal-level** possibilities — not verified targets.
- **Classification-only suggestions:** the weakest occupational title/SOC
  suggestions, marked as such. The profile lists genuine job tasks to inspect,
  but those tasks are **not cited as proof of the suggested SDG**.

In the interactive mind map, solid links denote strict task-to-target
hypotheses; dashed links require review. Different visual styles communicate
the evidence tier and do not imply causal impact.

`task_profile` reports each occupation's number of official tasks, number of
Core tasks, and up to three verbatim representative tasks with their IDs and
the official occupation link. This is role-specific context, not an impact
estimate.

### Export the complete 923-row review file

```powershell
$env:PYTHONPATH="src"
python scripts/audit_sdg_task_evidence.py
python scripts/export_923_sdg_review.py
```

This creates `reports/sdg_mapping_923_review.csv` with exactly one row
per occupation, official Task IDs, tiered goal suggestions and source status.
Rows labelled `classification_only` are NOT validated SDG mappings. Review
those rows, especially when considering an official submission.

The "923/923" count is **availability of an individualised analysis**, not
classification accuracy. No calibrated confidence probability is claimed.
Neither O*NET nor the UN independently approves these project-authored
occupational correspondences.

---

# FutureSkill AI — Evidence-based SDG candidate mapping (O*NET 31.0)

## Important conclusion

The original CSV of 923 occupations has **only O*NET-SOC codes, titles and
RIASEC interest measures**, not job duties. Assigning SDG 12 to all chefs or
SDG 4 to IT roles based only on occupation type is **not verified**. It is
incorrect to describe such suggestions as validated impacts.

Official sources checked:
- O*NET 31.0 [Task Statements](https://www.onetcenter.org/dictionary/31.0/csv/task_statements.html),
  published as `task_statements.csv`, contains **18,838 occupational task
  records** with the occupational code, task ID, full task text, Task Type and
  source date.
- UN [Goal 12 / Target 12.3](https://sdgs.un.org/goals/goal12) refers explicitly
  to reducing food waste and food losses.
- O*NET [Chefs and Head Cooks (35-1011.00)](https://www.onetonline.org/link/details/35-1011.00)
  lists tasks such as ordering supplies, estimating ingredient amounts,
  checking food quality and planning menus based on expected demand. **These
  do not establish that an individual chef has reduced food waste.**

## Latest website contract

The career explorer still searches **923 occupations**, but now returns:

1. `mappings` — **only** suggested UN-target links triggered by *real task
   statements*, with an actual O*NET Task ID, task text, Core/Supplemental
   label and official source URLs. Such links are named
   `task_based_candidate` and `task_signal_unreviewed` — NOT measured
   impacts or endorsement by the UN.
2. `candidate_mappings` — low-specificity career-name/SOC-group *guesses*.
   These are browsable in a separate disclosure, **not drawn as graph edges**.
3. `learning_pathway_mappings` — prior FutureSkill education / reskilling
   preparation links (UN 4.4, 8.5), separate from occupation contributions.
4. `task_data_status` — `available`, `not_installed`,
   `invalid_file`, or `occupation_tasks_missing`. When no source CSV is
   installed, the app does **not** invent task-backed mappings.

## Real-data installation (Windows PowerShell)

From the **repository root**, using your PyCharm virtual environment:

```powershell
git switch feature/all-923-career-sdg-mapping
git pull --ff-only origin feature/all-923-career-sdg-mapping
python scripts/import_onet_sdg_tasks.py
$env:PYTHONPATH="src"
python scripts/audit_sdg_task_evidence.py
python -m unittest discover -s tests -p "test_sdg_careers.py" -v
python -m uvicorn main:app --app-dir src --reload --port 5000
```

If the automatic download fails, open the official [O*NET Task Statements
page](https://www.onetcenter.org/dictionary/31.0/csv/task_statements.html)
and download `task_statements.csv` manually. Move that file to
`src/data/onet_task_statements.csv`. **Do not use an invented dataset.**

The official source is not automatically downloaded by the server at startup;
deployment with Render is deterministic and never calls the O*NET website
during an API request.

**To deploy the true task evidence on Render**, the downloaded CSV must be
checked into your GitHub branch and included in the merge to `main`:
```powershell
git add src/data/onet_task_statements.csv
git commit -m "data: add original O*NET 31.0 task statements for auditable SDG mapping"
git push origin feature/all-923-career-sdg-mapping
```

Review the dataset license and ensure the file is the official O*NET release
before publishing. Without that CSV on Render, the website will explicitly
state no real task records are installed; it will *not* draw the old Chef→12
line as if it had supporting duties.

## What evidence supports

A narrowly matched task such as explicit food-waste reduction may be
considered for UN Target 12.3. Simply ordering groceries or estimating
ingredient quantities **does not pass** this target rule. A job title or
industry classification never establishes an outcome.

The mapping rules are authored FutureSkill heuristics. A task statement and a
UN target may be directly relevant without verifying a benefit. Before
claiming real contribution, validate the rule manually against the UN target
and collect real outcome or programme evidence.

## License and attribution

> This page includes information from the O*NET 31.0 Database by the
> U.S. Department of Labor, Employment and Training Administration
> (USDOL/ETA). Used under the CC BY 4.0 license. O*NET® is a trademark
> of USDOL/ETA. FutureSkill AI has added its own UN SDG matching
> heuristics; USDOL/ETA has not approved, endorsed or tested them.

License: https://www.onetcenter.org/license_db.html

## Caveats

- O*NET is a U.S. occupational data source, not Malaysia-specific evidence.
- `task_supported` means **a rule found a matching real occupational duty**,
  not that SDG impact is measured or externally validated.
- Some of the 923 records may have no narrow task-rule match; these remain
  explicitly unassigned on the goal graph, not automatically assigned an SDG.
- Current target rules cover selected, carefully specified goals, not all
  169 UN SDG targets. The coverage audit reports the true count.
