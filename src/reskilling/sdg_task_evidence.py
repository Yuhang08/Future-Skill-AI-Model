"""Evidence-limited mapping from REAL O*NET 31.0 Task Statements to UN targets.

The 923-row interest CSV does NOT contain job tasks. An external, official O*NET
31.0 CSV must be installed under src/data/onet_task_statements.csv. Without it,
no task-backed goal is displayed. A task match is a hypothesis, NEVER proof of
a sustainable-development outcome.
"""
import csv
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from .sdg_occupation_rules import GOAL_NAMES
from .sdg_onet_context import get_context, importance_sort_key, DWA_DOC, RATINGS_DOC

TASK_DATA = Path(__file__).resolve().parent.parent / "data" / "onet_task_statements.csv"
ONET_DOWNLOAD = "https://www.onetcenter.org/dl_files/database/db_31_0_csv/task_statements.csv"
ONET_DOC = "https://www.onetcenter.org/dictionary/31.0/csv/task_statements.html"

# These rules are deliberately restrictive. Only occupation-specific tasks
# with clear action + topic are promoted to *task-supported candidate* links.
# A keyword alone, or a role/industry name alone, does not qualify.
TARGET_RULES = (
    {
        "target": "12.3", "goal": 12,
        "topic": r"\b(?:food|ingredients?|meals?|perishable)\b",
        "action": r"\b(?:reduc\w*|prevent\w*|minimi[sz]\w*|avoid\w*|divert\w*|donat\w*|reus\w*|recycl\w*)\b",
        "object": r"\b(?:wast\w*|spoil\w*|discard\w*|leftovers?|surplus)\b",
        "note": "Food-waste prevention may relate to Target 12.3; measured food waste reduction is not established.",
    },
    {
        "target": "12.5", "goal": 12,
        "topic": r"\b(?:material|solid waste|recycl\w*|plastic|scrap|industrial waste)\b",
        "action": r"\b(?:reduc\w*|recycl\w*|reus\w*|recover\w*|prevent\w*)\b",
        "object": r"\b(?:wast\w*|recycl\w*|scrap|refuse|dispos\w*)\b",
        "note": "Waste prevention/recycling tasks may connect to Target 12.5.",
    },
    {
        "target": "1.3", "goal": 1,
        "topic": r"\b(?:social security|income support|financial assistance|welfare benefits|public assistance)\b",
        "action": r"\b(?:administer|deliver|provide|distribut|determin|enrol|assist|process|coordinate|evaluat)\w*\b",
        "note": "Administration of social-protection benefits may connect to Target 1.3.",
    },
    {
        "target": "2.1", "goal": 2,
        "topic": r"\b(?:food insecurity|food assistance|food bank|hunger relief|emergency food|school meals)\b",
        "action": r"\b(?:provid|deliver|distribut|organis|organiz|coordinat|manage|administer)\w*\b",
        "note": "Direct food-assistance tasks may connect to Target 2.1.",
    },
    {
        "target": "3.8", "goal": 3,
        "groups": ("29", "31", "21"),
        "topic": r"\b(?:patient|clinical|medical care|healthcare|health care)\b",
        "action": r"\b(?:diagnos|treat|provid|administer|monitor|care for|rehabilitat)\w*\b",
        "note": "Providing clinical care may connect to Target 3.8; health outcomes are not measured.",
    },
    {
        "target": "4.1", "goal": 4,
        "groups": ("25",),
        "topic": r"\b(?:students?|pupils?|classroom|school children|school students)\b",
        "action": r"\b(?:teach|instruct|tutor|educat|assess|develop lesson)\w*\b",
        "note": "Teaching school students may connect to Target 4.1.",
    },
    {
        "target": "6.3", "goal": 6,
        "topic": r"\b(?:wastewater|sewage|water pollution|water treatment|water quality)\b",
        "action": r"\b(?:treat|purif|test|monitor|remov|control|assess|improv|operat|design)\w*\b",
        "note": "Water treatment and pollution management may connect to Target 6.3.",
    },
    {
        "target": "7.2", "goal": 7,
        "groups": ("11", "17", "19", "47", "49"),
        "topic": r"\b(?:solar (?:power|energy|panels?|photovoltaic)|wind (?:energy|power|turbines?)|renewable energy|geothermal energy)\b",
        "action": r"\b(?:install|maintain|operat|design|develop|engineer|plan|repair|test|construct)\w*\b",
        "note": "Tasks directly supporting renewable-energy systems may connect to Target 7.2.",
    },
    {
        "target": "8.8", "goal": 8,
        "topic": r"\b(?:worker rights|labor rights|labour rights|occupational health and safety|workplace safety)\b",
        "action": r"\b(?:enforc|protect|inspect|monitor|improv|investigat|assess)\w*\b",
        "note": "Worker-rights / workplace-protection tasks may connect to Target 8.8.",
    },
    {
        "target": "9.5", "goal": 9,
        "groups": ("15", "17", "19"),
        "topic": r"\b(?:research|scientific|technolog\w*|engineer\w*|prototype|software)\b",
        "action": r"\b(?:conduct research|design|develop|experiment|investigat|test|invent|research)\w*\b",
        "note": "Research and development tasks may connect to Target 9.5; innovation impact is not proven.",
    },
    {
        "target": "10.2", "goal": 10,
        "topic": r"\b(?:persons with disabilities|people with disabilities|disability access|social inclusion|accessibility barriers)\b",
        "action": r"\b(?:provid|improv|facilitat|develop|assess|assist|support|design|remov)\w*\b",
        "note": "Disability inclusion/accessibility services may connect to Target 10.2.",
    },
    {
        "target": "11.2", "goal": 11,
        "topic": r"\b(?:public transit|public transport|mass transit|bus routes?|rail transit)\b",
        "action": r"\b(?:plan|design|improv|develop|operat|manag|coordinat)\w*\b",
        "note": "Public-transport development may connect to Target 11.2.",
    },
    {
        "target": "13.2", "goal": 13,
        "topic": r"\b(?:climate chang\w*|greenhouse gas|carbon emissions?|climate adaptation)\b",
        "action": r"\b(?:assess|reduc|mitigat|develop|model|plan|monitor|analys|analyz|control)\w*\b",
        "note": "Explicit climate mitigation/adaptation tasks may connect to Target 13.2.",
    },
    {
        "target": "14.2", "goal": 14,
        "topic": r"\b(?:marine habitats?|marine ecosystems?|coral reefs?|coastal ecosystems?|ocean biodiversity)\b",
        "action": r"\b(?:conserv|restor|protect|monitor|rehabilitat|preserv|manag)\w*\b",
        "note": "Protection of marine ecosystems may connect to Target 14.2.",
    },
    {
        "target": "15.1", "goal": 15,
        "topic": r"\b(?:wildlife habitats?|forest ecosystems?|wetlands?|terrestrial ecosystems?|biodiversity)\b",
        "action": r"\b(?:conserv|restor|protect|preserv|manag|rehabilitat|monitor)\w*\b",
        "note": "Protection/restoration of terrestrial habitats may connect to Target 15.1.",
    },
    {
        "target": "16.3", "goal": 16,
        "groups": ("23",),
        "topic": r"\b(?:legal aid|legal representation|access to justice|court proceedings|clients? in court)\b",
        "action": r"\b(?:represent|provid|assist|defend|advoc|prepar|support)\w*\b",
        "note": "Legal assistance may connect to Target 16.3.",
    },
)


def _match_rule(task, code, rule):
    if rule.get("groups") and code[:2] not in rule["groups"]:
        return False
    for key in ("topic", "action", "object"):
        if rule.get(key) and not re.search(rule[key], task, re.IGNORECASE):
            return False
    return True


@lru_cache(maxsize=4)
def _read_index(path_text, modified_ns):
    del modified_ns
    indexed = defaultdict(list)
    with Path(path_text).open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        needed = {"O*NET-SOC Code", "Task ID", "Task", "Task Type"}
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError("Not an official O*NET Task Statements CSV: incorrect columns")
        for row in reader:
            code = (row.get("O*NET-SOC Code") or "").strip()
            task = (row.get("Task") or "").strip()
            task_id = (row.get("Task ID") or "").strip()
            if not re.fullmatch(r"\d{2}-\d{4}\.\d{2}", code) or not task or not task_id.isdigit():
                continue
            indexed[code].append({
                "id": task_id,
                "task": task,
                "type": (row.get("Task Type") or "").strip(),
                "date": (row.get("Date") or "").strip(),
            })
    return indexed


def source_status():
    if not TASK_DATA.is_file():
        return "not_installed"
    try:
        index = _read_index(str(TASK_DATA), TASK_DATA.stat().st_mtime_ns)
    except (OSError, ValueError, UnicodeError):
        return "invalid_file"
    return "available" if index else "invalid_file"


def task_supported_mappings(career_id, title):
    """Return (matching proposals, data status); never fabricate task evidence."""
    status = source_status()
    if status != "available":
        return [], status
    tasks = _read_index(str(TASK_DATA), TASK_DATA.stat().st_mtime_ns).get(career_id, [])
    if not tasks:
        return [], "occupation_tasks_missing"
    matched = defaultdict(list)
    for row in tasks:
        for rule in TARGET_RULES:
            if _match_rule(row["task"], career_id, rule):
                matched[rule["target"]].append((row, rule))
    # Require an explicitly matching CORE task, if present; otherwise label
    # supplemental findings as weaker signals (not automatically endorsed).
    mappings = []
    for target, found in sorted(matched.items()):
        core = [(task, rule) for task, rule in found if task["type"].lower() == "core"]
        # Relative role-task importance affects the order of displayed
        # evidence only. It is NOT an SDG impact probability.
        selected = sorted(core or found,
                          key=lambda item: importance_sort_key(career_id, item[0]))[:3]
        task, rule = selected[0]
        goal = rule["goal"]
        evidence = [
            {
                "task_id": item["id"],
                "task": item["task"],
                "task_type": item["type"],
                "date": item["date"],
                "source_url": f"https://www.onetonline.org/link/details/{career_id}",
                "dwa_activities": get_context(career_id, item["id"])["dwas"],
                "task_ratings": get_context(career_id, item["id"])["task_ratings"],
            }
            for item, _ in selected
        ]
        actual_sources = [
            {"id": "onet-task-statements",
             "label": "O*NET 31.0 · Occupation-specific Task Statements",
             "url": ONET_DOC,
             "scope": "Original task text and ID; no demonstrated SDG outcome."},
            {"id": f"un-sdg-target-{target}",
             "label": f"United Nations · SDG Target {target}",
             "url": f"https://sdgs.un.org/goals/goal{goal}",
             "scope": "Official target definition; mapping is a FutureSkill heuristic."},
        ]
        if any(row["task_ratings"] for row in evidence):
            actual_sources.append({
                "id": "onet-task-ratings",
                "label": "O*NET 31.0 Task Ratings",
                "url": RATINGS_DOC,
                "scope": "Importance/relevance of actual job tasks; not SDG confidence.",
            })
        if any(row["dwa_activities"] for row in evidence):
            actual_sources.append({
                "id": "onet-task-dwa",
                "label": "O*NET 31.0 Tasks to DWAs",
                "url": DWA_DOC,
                "scope": "Actual detailed work activity linked by job code and Task ID.",
            })
        mappings.append({
            "career_id": career_id,
            "sdg_id": goal,
            "sdg_name": GOAL_NAMES[goal],
            "target_id": target,
            "target_summary": rule["note"],
            "mapping_kind": "task_based_candidate",
            "review_status": "task_signal_unreviewed",
            "specificity": "onet_task",
            "match_basis": f"O*NET 31.0 Task Statements: {len(found)} rule-matched task(s)",
            "relevance_reason": (
                f"O*NET 31.0 lists {len(found)} occupation-specific task(s) for {title} "
                f"that match a narrow proposed connection to UN Target {target}. "
                "This shows relevant duties, not that SDG progress occurred."
            ),
            "task_evidence": evidence,
            "supporting_evidence": [
                f"Official O*NET 31.0 Task ID {x['task_id']} ({x['task_type'] or 'unclassified'}): {x['task']}"
                for x in evidence
            ],
            "evidence_source": actual_sources,
            "supporting_source_ids": [row["id"] for row in actual_sources],
            "user_action": (
                "Check the O*NET Task ID and UN target. Human review and evidence "
                "of actual outcomes are required before claiming SDG impact."
            ),
            "impact_limitations": (
                "Task-to-target matching is a transparent keyword rule on genuine "
                "O*NET 31.0 tasks, not a validated causal model. It does not "
                "show any measurable SDG outcome or UN endorsement."
            ),
        })
    return mappings, "available"
