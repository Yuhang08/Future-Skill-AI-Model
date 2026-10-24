"""Auditable, preliminary SDG themes for ALL catalogue occupations.

Never asserts that occupations *achieve* a UN SDG target. Genuine O*NET task
texts supply role-specific context. Strict task-to-target mappings remain
separate and higher priority in sdg_task_evidence.py.
"""
import re

from . import sdg_task_evidence as evidence
from .sdg_occupation_rules import GOAL_NAMES, infer_occupation_sdg_mappings
from .sdg_onet_context import get_context, importance_sort_key, sources_available, DWA_DOC, RATINGS_DOC

# Distinctive multiword task themes. Matching means "possible topic", not
# target achievement. Avoid misleading generic tokens: jobs, food, education
# through learning to program, "security", sustainability or "work".
TASK_TOPICS = {
    1: (r"\b(?:poverty alleviation|homelessness services?|public assistance benefits|"
        r"income support|welfare benefits|social security benefits)\b",),
    2: (r"\b(?:food insecurity|hunger relief|food bank|nutritional assistance|"
        r"crop yield|agricultural production)\b",),
    3: (r"\b(?:patient care|patient treatment|treat patients|clinical care|"
        r"diagnose diseases?|medical services?|community health services?)\b",),
    # Education-related TRAINING for unrelated jobs is not automatically a
    # career contribution to UN SDG 4. Require a learning-specific context.
    4: (r"\b(?:teach students?|tutor pupils?|develop curricul\w*|"
        r"classroom instruction|student learning|educational software|"
        r"school learning|university teaching|college instruction)\b",),
    5: (r"\b(?:gender equality|gender-based discrimination|women's rights|"
        r"equal pay for women|sexual harassment prevention)\b",),
    6: (r"\b(?:wastewater treatment|sewage treatment|drinking water supply|"
        r"water quality monitoring|water pollution|sanitation systems?)\b",),
    7: (r"\b(?:solar (?:power|panels?|energy)|wind (?:turbines?|energy|power)|"
        r"renewable energy|photovoltaic systems?|geothermal power)\b",),
    8: (r"\b(?:worker rights|workers' rights|occupational health and safety|"
        r"workplace safety|fair employment|labor protections?|labour protections?)\b",),
    9: (r"\b(?:develop software|software systems? design|technological research|"
        r"engineering research|research and development|prototype development|"
        r"design infrastructure|develop prototypes?)\b",),
    10: (r"\b(?:disability inclusion|accessible services?|equal opportunity|"
         r"disability access|reduce discrimination|accessibility barriers?)\b",),
    11: (r"\b(?:urban planning|affordable housing|public (?:transit|transport)|"
         r"urban resilience|community infrastructure|disaster-resilient buildings?)\b",),
    12: (r"\b(?:food waste|reduce waste|waste reduction|recycl(?:ing|able)|"
         r"material recovery|resource efficiency|sustainable procurement)\b",),
    13: (r"\b(?:climate change|greenhouse gas|carbon emissions?|"
         r"climate mitigation|climate adaptation)\b",),
    14: (r"\b(?:marine ecosystems?|coral reefs?|ocean conservation|"
         r"marine biodiversity|coastal habitat restoration)\b",),
    15: (r"\b(?:wildlife habitats?|forest conservation|wetland restoration|"
         r"terrestrial biodiversity|endangered species conservation)\b",),
    16: (r"\b(?:access to justice|legal representation|court proceedings|"
         r"crime prevention|human rights enforcement|judicial proceedings)\b",),
    17: (r"\b(?:international development partnerships?|international cooperation|"
         r"cross-border partnership|public-private partnerships?|"
         r"development cooperation)\b",),
}


def _task_rows(career_id):
    """Only actual occupation-coded Task Statements. Empty if unavailable."""
    if evidence.source_status() != "available":
        return [], evidence.source_status()
    table = evidence._read_index(
        str(evidence.TASK_DATA), evidence.TASK_DATA.stat().st_mtime_ns
    )
    rows = table.get(str(career_id), [])
    return sorted(rows, key=lambda row: importance_sort_key(career_id, row)), (
        "available" if rows else "occupation_tasks_missing"
    )


def _evidence(row, career_id):
    context = get_context(career_id, row["id"])
    return {
        "task_id": row["id"],
        "task": row["task"],
        "task_type": row["type"],
        "date": row.get("date", ""),
        "dwa_activities": context["dwas"],
        "task_ratings": context["task_ratings"],
    }


def occupation_task_profile(career_id):
    """Ground EVERY occupation's analysis in its own Task IDs when available."""
    rows, status = _task_rows(career_id)
    return {
        "source_status": status,
        "occupation_task_count": len(rows),
        "core_task_count": sum(row["type"].lower() == "core" for row in rows),
        "representative_tasks": [_evidence(row, career_id) for row in rows[:3]],
        "supporting_data_available": sources_available(),
        "source_url": f"https://www.onetonline.org/link/details/{career_id}"
            if rows else evidence.ONET_DOC,
        "evidence_scope": (
            "Official O*NET duty descriptions, not proof of actual SDG impact. "
            "A role may have tasks with no sufficient SDG-target connection."
        ),
    }


def _topic_candidates(career_id, title, rows):
    """Use task phrases first; matching DWA names is explicitly weaker.

    DWAs and O*NET ratings are occupational evidence, NOT validated SDG
    crosswalks. A general activity must never be presented as a proven target.
    """
    grouped = {}
    for row in rows:
        dwas = get_context(career_id, row["id"])["dwas"]
        for goal_id, expressions in TASK_TOPICS.items():
            task_match = any(re.search(pattern, row["task"], re.IGNORECASE)
                             for pattern in expressions)
            dwa_match = not task_match and any(
                re.search(pattern, dwa["name"], re.IGNORECASE)
                for dwa in dwas for pattern in expressions
            )
            if task_match or dwa_match:
                grouped.setdefault(goal_id, []).append(
                    (row, "task_topic" if task_match else "dwa_topic")
                )
    ranked = sorted(grouped.items(), key=lambda pair: (
        -sum(row["type"].lower() == "core" for row, _ in pair[1]),
        -sum(kind == "task_topic" for _, kind in pair[1]),
        -len(pair[1]), pair[0]
    ))
    suggestions = []
    for goal_id, matched_rows in ranked[:3]:
        task_hits = [row for row, kind in matched_rows if kind == "task_topic"]
        dwa_only = not task_hits
        selected = (task_hits or [row for row, _ in matched_rows])[:2]
        candidate_tier = "dwa_topic" if dwa_only else "task_topic"
        evidence_rows = [_evidence(row, career_id) for row in selected]
        explanation = (
            f"O*NET 31.0 lists occupation-specific duties for {title}. "
            + (
                f"A linked Detailed Work Activity (DWA) names a theme related "
                f"to SDG {goal_id}; the original task may not mention the theme."
                if dwa_only else
                f"The actual Task Statement text includes a phrase potentially "
                f"related to SDG {goal_id}."
            ) +
            " This is a goal-level research hypothesis, NOT an established "
            "UN Target alignment or evidence of measurable SDG impact."
        )
        sources = [
            {"id": "onet-task-statements", "label": "O*NET 31.0 Task Statements",
             "url": evidence.ONET_DOC,
             "scope": "Occupation task wording and ID only."},
            {"id": f"un-sdg-goal-{goal_id}", "label": f"UN SDG {goal_id}",
             "url": f"https://sdgs.un.org/goals/goal{goal_id}",
             "scope": "UN goal definition; no occupational impact claim."},
        ]
        if dwa_only:
            sources.append({
                "id": "onet-task-dwa", "label": "O*NET 31.0 Tasks to DWAs",
                "url": DWA_DOC,
                "scope": "The DWA activity is joined using the exact occupation and Task ID."
            })
        suggestions.append({
            "career_id": career_id,
            "sdg_id": goal_id,
            "sdg_name": GOAL_NAMES[goal_id],
            "target_id": None,
            "mapping_kind": "task_context_candidate",
            "review_status": "human_review_required",
            "specificity": "onet_dwa_topic" if dwa_only else "onet_task_topic",
            "candidate_tier": candidate_tier,
            "match_basis": (
                "Official O*NET DWA linked to occupation Task ID" if dwa_only
                else "Phrase found in occupation's official Task Statement"
            ),
            "relevance_reason": explanation,
            "task_evidence": evidence_rows,
            "supporting_evidence": [
                f"O*NET Task ID {e['task_id']}: {e['task']}"
                for e in evidence_rows
            ],
            "evidence_source": sources,
            "supporting_source_ids": [item["id"] for item in sources],
            "impact_limitations": (
                "Preliminary thematic candidate using genuine O*NET duties or "
                "linked work activities. NOT a validated UN target link, "
                "impact assessment or probability estimate."
            ),
            "user_action": (
                "Inspect the exact O*NET Task and DWA IDs, compare the actual "
                "UN target wording, and seek independent outcome evidence."
            ),
        })
    return suggestions


def candidate_mappings_for_occupation(career_id, title, confirmed_task_goals=()):
    """Return ranked, auditable ideas for each of 923 occupations.

    Tier 1: distinctive task-topic phrases; linked DWA-topic clues are weaker.
    Tier 2: broad title/SOC classification ONLY, with task profile as context.
    No tier measures verified SDG impact or an objective match probability.
    """
    rows, _ = _task_rows(career_id)
    strict_goals = set(confirmed_task_goals)
    task_topics = [
        item for item in _topic_candidates(career_id, title, rows)
        if item["sdg_id"] not in strict_goals
    ]
    existing = set(strict_goals)
    existing.update(item["sdg_id"] for item in task_topics)

    fallbacks = []
    for suggestion in infer_occupation_sdg_mappings(career_id, title):
        if suggestion["sdg_id"] in existing:
            continue
        suggestion = dict(suggestion)
        suggestion["candidate_tier"] = "classification_only"
        suggestion["task_evidence"] = []  # no target-specific evidence
        suggestion["review_status"] = "classification_unverified"
        suggestion["supporting_evidence"] = [
            f"Title/SOC classification: {suggestion['match_basis']}.",
            "No matching Task ID establishes an occupation-to-goal relation.",
        ]
        suggestion["relevance_reason"] = (
            f"Broad occupational-topic idea from {suggestion['match_basis']}. "
            "This is NOT supported by a task-to-target match. The occupation "
            "task profile is supplied separately for manual review."
        )
        fallbacks.append(suggestion)
    # At most three goal ideas; strongest task-related topics first.
    return (task_topics + fallbacks)[:3]
