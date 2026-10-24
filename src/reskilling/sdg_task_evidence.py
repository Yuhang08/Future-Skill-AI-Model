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
        # Target 12.3 is about *preventing/reducing* food loss and waste;
        # collecting or recycling already-discarded food is not by itself
        # the same outcome. Require an explicit prevention/reduction action.
        "topic": r"\b(?:food|ingredients?|meals?|perishable|edible)\b",
        "action": r"\b(?:reduc\w*|prevent\w*|minimi[sz]\w*|avoid\w*|"
                  r"donat\w*)\b",
        "object": r"\b(?:wast\w*|spoil\w*|discard\w*|leftovers?|surplus|"
                  r"food loss(?:es)?)\b",
        "exclude": r"\b(?:curricul\w*|train\w*|teach\w*|"
                   r"educat\w*|workshops?|seminars?)\b",
        "core_only": True,
        "note": "Explicit Core duties preventing/reducing food loss or food "
                "waste may relate to 12.3. Collecting food waste alone does not.",
    },
    {
        "target": "12.5", "goal": 12,
        # A recycling/reuse or real waste-prevention operation is required.
        # Disposing of waste, removing waste from a body, or mere handling of
        # hazardous materials does not prove waste generation is reduced.
        "topic": r"\b(?:wast\w*|recycl\w*|reus\w*|scrap|"
                 r"reclaim\w*|recover\w*)\b",
        "action": r"\b(?:reduc\w*|prevent\w*|recycl\w*|reus\w*|"
                  r"recover\w*|reclaim\w*|collect\w*|sort\w*|"
                  r"implement\w*|manag\w*|process\w*|coordinat\w*)\b",
        "operational_pattern": (
            r"\b(?:reduc\w*|prevent\w*|minimi[sz]\w*)\b.{0,110}"
            r"\b(?:wast\w*|scrap|discards?)\b|"
            r"\b(?:recycl\w*|reus\w*|reclaim\w*|recover\w*)\b"
            r".{0,110}\b(?:wast\w*|scrap|materials?|products?)\b|"
            r"\b(?:collect\w*|sort\w*|process\w*|manag\w*|"
            r"coordinat\w*|implement\w*)\b.{0,110}"
            r"\b(?:recycl\w*|reus\w*|reclaim\w*|scrap (?:metal|materials?))\b"
        ),
        "exclude": r"\b(?:teach\w*|train\w*|educat\w*|instruct\w*|"
                   r"curricul\w*|workshops?|seminars?|"
                   r"awareness presentations?)\b",
        "core_only": True,
        "note": "Only a Core waste-prevention/reuse/recycling operation suggests "
                "12.5. Generic waste disposal and training do not establish it.",
    },
    {
        "target": "1.3", "goal": 1,
        # UN 1.3 is about SOCIAL PROTECTION systems. A commercial loan,
        # student scholarship or generic financial assistance is not 1.3.
        "topic": r"\b(?:social (?:security|protection) (?:benefits?|programs?|systems?)|"
                 r"(?:government|public) assistance (?:benefits?|programs?)|"
                 r"(?:unemployment|disability|welfare|child|maternity|pension) benefits?|"
                 r"(?:income support|social welfare) (?:benefits?|programs?))\b",
        "action": r"\b(?:administer|deliver|provid|distribut|determin|enrol|"
                  r"assist|process|coordinat|evaluat|approv|assess|manag)\w*\b",
        "exclude": r"\b(?:student loans?|college loans?|scholarships?|"
                   r"tuition (?:loans?|grants?)|commercial loans?|"
                   r"mortgage loans?|credit applications?)\b",
        "core_only": True,
        "note": "A core duty delivering/administering a social-protection program "
                "may relate to Target 1.3; benefit coverage has not been measured.",
    },
    {
        "target": "2.1", "goal": 2,
        "topic": r"\b(?:food insecurity|food assistance|food bank|hunger relief|emergency food|school meals)\b",
        "action": r"\b(?:provid|deliver|distribut|organis|organiz|coordinat|manage|administer)\w*\b",
        "note": "Direct food-assistance tasks may connect to Target 2.1.",
    },
    {
        "target": "3.8", "goal": 3,
        # UN Target 3.8 concerns health-service ACCESS/COVERAGE, not the
        # mere existence of a clinical job. Patient care is a weaker
        # goal-level SDG 3 topic in sdg_candidate_ranker.py.
        "topic": r"\b(?:universal health coverage|health(?:care)? access|"
                 r"access to (?:essential|primary) (?:health|medical|clinical) "
                 r"(?:care|services)|health services? coverage|"
                 r"access to healthcare services|patient access to care)\b",
        "action": r"\b(?:expand|improv|ensur|facilitat|provid|increas|"
                  r"coordinat|extend|manag|develop)\w*\b",
        "core_only": True,
        "note": "Work explicitly improving access to essential healthcare "
                "may relate to Target 3.8; providing clinical care alone is not UHC.",
    },
    {
        "target": "4.1", "goal": 4,
        # Target 4.1 refers specifically to PRIMARY and SECONDARY
        # education, not postsecondary, preschool or adult classes.
        "codes": (
            # Kindergarten/pre-primary education is target 4.2, not 4.1.
            "25-2021.00", "25-2022.00", "25-2023.00",
            "25-2031.00", "25-2032.00",
            "25-2056.00", "25-2057.00", "25-2058.00",
            # Grade-unspecified substitute teaching cannot establish 4.1.
        ),
        "topic": r"\b(?:students?|pupils?|kindergartners?|"
                 r"classrooms?|school children|school students)\b",
        "action": r"\b(?:teach|instruct|tutor|educat|assess|"
                  r"develop lesson|prepar\w* lessons?)\w*\b",
        "core_only": True,
        "note": "Core teaching duties in K-12 schooling may relate to "
                "Target 4.1; preschool, university and adult instruction are different targets.",
    },
    {
        "target": "4.2", "goal": 4,
        # Target 4.2 is early childhood care and pre-primary education.
        # Only explicit preschool/kindergarten educator occupation codes,
        # not all other teaching positions.
        "codes": (
            "25-2011.00",  # Preschool Teachers, Except Special Education
            "25-2012.00",  # Kindergarten Teachers, Except Special Education
            "25-2051.00",  # Special Education Teachers, Preschool
            "25-2055.00",  # Special Education Teachers, Kindergarten
        ),
        "topic": r"\b(?:preschool|pre-school|kindergarten|"
                 r"children|young learners?|students?|pupils?)\b",
        "action": r"\b(?:teach|instruct|tutor|educat|"
                  r"assess|develop lesson|prepar\w* lessons?)\w*\b",
        "core_only": True,
        "note": "A Core preschool/kindergarten educational duty may "
                "relate to Target 4.2, not Target 4.1. Pre-primary access "
                "and early childhood outcomes are not measured.",
    },
    {
        "target": "6.3", "goal": 6,
        "topic": r"\b(?:wastewater|sewage|water pollution|water treatment|"
                 r"water quality|water contamination)\b",
        "action": r"\b(?:treat|purif|test|monitor|remov|control|assess|"
                  r"improv|operat|design|remediat|filter)\w*\b",
        # Training the public about sewage risks is not directly improving
        # wastewater treatment or water quality.
        "exclude": r"\b(?:public health education|health education programs?|"
                   r"train\w*|teach\w*|educat\w*|lectur\w*|"
                   r"public presentations?|workshops?)\b",
        "core_only": True,
        "note": "Core water-quality or wastewater intervention may suggest 6.3; "
                "public-health lectures mentioning sewage do not prove it.",
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
        # UN 9.5 emphasises scientific research and R&D capacity. General
        # software installation, technical support, ordinary maintenance,
        # website design or product testing alone do NOT establish 9.5.
        "topic": r"\b(?:research and development|scientific research|"
                 r"(?:basic|applied|experimental) research|"
                 r"conduct (?:scientific|applied|experimental) research|"
                 r"(?:develop|design|research|investigat)\w* (?:novel|"
                 r"innovative|experimental|new) (?:technolog\w*|materials?|"
                 r"products?|methods?|processes?|prototypes?)|"
                 r"(?:develop|design|test) experimental prototypes?|"
                 r"laboratory research)\b",
        "core_only": True,
        "note": "An explicit core research/development duty may relate to "
                "Target 9.5. Routine IT work is not R&D, and no SDG result is measured.",
    },
    {
        "target": "10.2", "goal": 10,
        # Target 10.2 is promoting inclusion. One-off customer assistance
        # (including passengers with disabilities) does not establish this.
        "topic": r"\b(?:disability inclusion|social inclusion|"
                 r"accessibility barriers?|inclusive services?|"
                 r"equitable access|social integration|"
                 r"disability rights|equal access to (?:services?|employment|education))\b",
        "action": r"\b(?:improv|facilitat|develop|implement|"
                  r"remov|promot|expand|increas|design|advoc)\w*\b",
        "core_only": True,
        "note": "Explicit Core activities promoting systematic social/economic "
                "inclusion may suggest 10.2. Routine passenger assistance does not.",
    },
    {
        "target": "11.2", "goal": 11,
        "topic": r"\b(?:public transit|public transport|mass transit|bus routes?|rail transit)\b",
        "action": r"\b(?:plan|design|improv|develop|operat|manag|coordinat)\w*\b",
        "note": "Public-transport development may connect to Target 11.2.",
    },
    {
        "target": "13.2", "goal": 13,
        "topic": r"\b(?:climate chang\w*|greenhouse gas|"
                 r"carbon emissions?|climate adaptation|climate mitigation)\b",
        "action": r"\b(?:integrat|formulat|develop|implement|"
                  r"coordinat|draft|revis|design|plan)\w*\b",
        # UN 13.2 specifically concerns integrating measures into policies,
        # strategies and planning. Driver route planning is NOT climate policy.
        "policy_scope": r"\b(?:climate polic(?:y|ies)|"
                        r"national (?:climate |environmental )?strateg(?:y|ies)|"
                        r"(?:national|public|government) polic(?:y|ies)|"
                        r"climate action plans?|climate strateg(?:y|ies)|"
                        r"(?:adaptation|mitigation) strateg(?:y|ies)|"
                        r"climate-related (?:strategic|land-use) planning)\b",
        "core_only": True,
        "note": "Core climate policy/strategy integration duties may suggest "
                "Target 13.2. Fuel-efficient route planning is a different scope.",
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


def _match_rule(task, code, rule, task_type=None):
    """Propose target only when wording, career scope and evidence tier agree."""
    if rule.get("groups") and code[:2] not in rule["groups"]:
        return False
    if rule.get("codes") and code not in rule["codes"]:
        return False
    if rule.get("core_only") and task_type is not None:
        if str(task_type).strip().lower() != "core":
            return False
    if rule.get("exclude") and re.search(rule["exclude"], task, re.IGNORECASE):
        return False
    for key in ("policy_scope", "operational_pattern"):
        if rule.get(key) and not re.search(rule[key], task, re.IGNORECASE):
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
            if _match_rule(row["task"], career_id, rule, row["type"]):
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
