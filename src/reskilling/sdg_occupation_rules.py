"""Illustrative occupation-to-SDG thematic suggestions for the 923 O*NET careers.

This is a transparent, rule-based *prototype*. O*NET-SOC gives an occupation
identity, not evidence of measurable SDG contributions. No target-level claims
are made for these suggestions, and no LLM, probability, or impact score is used.
"""
import re

GOAL_NAMES = {
    1: "No Poverty", 2: "Zero Hunger", 3: "Good Health and Well-being",
    4: "Quality Education", 5: "Gender Equality",
    6: "Clean Water and Sanitation", 7: "Affordable and Clean Energy",
    8: "Decent Work and Economic Growth",
    9: "Industry, Innovation and Infrastructure", 10: "Reduced Inequalities",
    11: "Sustainable Cities and Communities",
    12: "Responsible Consumption and Production", 13: "Climate Action",
    14: "Life Below Water", 15: "Life on Land",
    16: "Peace, Justice and Strong Institutions",
    17: "Partnerships for the Goals",
}

# Standard Occupational Classification major groups: *theme*, not SDG evidence.
# NOT every SOC group is assigned an SDG. A broad job type is not evidence of
# actual SDG contribution; do NOT assign Goal 8 merely because a job exists.
MAJOR_GROUP_THEMES = {
    # These are broad DISCOVERY THEMES. They are not verified target links.
    "15": ((9,), "computer and mathematical occupations"),
    "17": ((9,), "architecture and engineering"),
    "19": ((9,), "scientific research and investigation"),
    "21": ((10,), "social and community support"),
    "23": ((16,), "legal services and justice institutions"),
    "25": ((4,), "education and instruction"),
    "29": ((3,), "healthcare practice"),
    "31": ((3,), "healthcare support"),
    "33": ((16,), "protective and public services"),
    "35": ((12,), "food preparation and consumption"),
    "37": ((11,), "building and grounds maintenance"),
    "45": ((2, 15), "farming, fisheries and natural resources"),
    "47": ((9, 11), "construction and the built environment"),
}

# No automatic SDG fallback for mixed fields SOC 27, 49, 51, 53.
# An interior designer is not automatically "Sustainable Cities"; a boiler
# operator is not inherently "Industry/Consumption"; a refuse collector
# is not automatically both "Industry" and "Sustainable Cities".
# Task/DWA evidence and clearly specialist titles remain available.
# More specific titles take priority over the broad occupational major group.
# Ordered from more specific to more general; return at most three theme goals.
TITLE_THEMES = (
    # Explicit specialist/industry titles are still only topic hypotheses.
    # Governance and renewable-energy managers should NOT inherit SDG 8.
    (r"\blegislators?\b", (16,), "legislative governance"),
    (r"\bcomputer and information systems managers?\b",
     (9,), "digital infrastructure and information systems"),
    (r"\b(?:biofuels? production|biomass power plant|hydroelectric production) managers?\b",
     (7,), "renewable power operations"),
    (r"\b(?:social and community service managers?)\b",
     (10,), "community and social inclusion services"),
    # Specific occupational specialties take precedence over SOC fallback.
    (r"\benvironmental engineers?\b", (6, 9, 13), "environmental engineering"),
    (r"\b(?:water/wastewater|wastewater|water treatment|sewage|sanitation|hydrolog(?:ist|y|ical))\b",
     (6,), "water resource protection and sanitation"),
    (r"\b(?:solar|wind energy|wind turbine|renewable energy|biofuels?)\b",
     (7, 9, 13), "renewable energy technologies"),
    (r"\b(?:climate change|climatolog(?:ist|y)|carbon emissions?|greenhouse gas)\b",
     (13,), "climate analysis or mitigation"),
    (r"\b(?:sustainability|sustainable development|pollution control|environmental protection)\b",
     (12, 13), "sustainability and pollution control"),
    (r"\b(?:marine biolog(?:ist|y)|oceanograph(?:er|y)|aquacultur(?:e|al)|fisheries)\b",
     (14,), "aquatic ecosystems and resources"),
    (r"\b(?:wildlife|forestry|forest conservation|ecolog(?:ist|y)|conservation scientist|botan(?:ist|y))\b",
     (15,), "terrestrial ecosystems and biodiversity"),
    (r"\b(?:agricultur(?:e|al)|farm(?:er|workers?|ing)|crop|livestock|horticultur(?:e|al))\b",
     (2, 15), "food systems and land stewardship"),
    (r"\b(?:equal opportunity|civil rights|disability services)\b",
     (10, 16), "inclusion and equal access"),
    (r"\b(?:gender equality|women's rights|women and girls)\b",
     (5, 10), "gender equality"),
    (r"\b(?:international development|international aid|foreign aid)\b",
     (17,), "international development partnerships"),
    (r"\b(?:social worker|social and human service|poverty reduction|housing assistance)\b",
     (1, 10), "social services and economic inclusion"),
    (r"\b(?:biomedical engineer|health informatics|medical equipment)\b",
     (3, 9), "healthcare technology"),
    (r"\b(?:registered nurses?|nurse practitioner|physician|dentist|therapist)\b",
     (3,), "clinical care and health services"),
    (r"\b(?:teachers?|instructors?|professors?|tutors?|education administrators?)\b",
     (4,), "teaching and learning"),
    (r"\b(?:cybersecurity|cyber security|information security)\b",
     (9, 16), "digital security and resilient information systems"),
    (r"\b(?:software develop\w*|computer programm\w*|data analysts?|data scientists?|database|artificial intelligence|machine learning)\b",
     (9,), "software, data and technological innovation"),
    (r"\b(?:user experience|ui/ux|web and digital interface)\b",
     (9,), "digital interface development"),
    (r"\b(?:digital marketing|advertising|marketing specialist)\b",
     (8,), "marketing and commercial activity"),
)

LIMITATIONS = (
    "Rule-based thematic suggestion from the occupation title or SOC major group. "
    "O*NET supplies occupational identity, and UN pages define goals; neither "
    "source establishes that this occupation achieves an SDG. No UN target, "
    "employment outcome or measured impact is verified. Expert review of job "
    "tasks and independent outcome evidence is needed for stronger claims."
)


def _suggestion(career_id, career_title):
    """Return (goal_ids, basis, specificity) without assuming SDG impact."""
    title = str(career_title or "").strip()
    for pattern, goals, theme in TITLE_THEMES:
        if re.search(pattern, title, flags=re.IGNORECASE):
            return goals, "occupation title: " + theme, "title_rule"
    major_group = str(career_id or "")[:2]
    if major_group in MAJOR_GROUP_THEMES:
        goals, theme = MAJOR_GROUP_THEMES[major_group]
        return goals, "broad SOC group: " + theme, "soc_group"
    # No arbitrary default Goal 8 for generic management/business roles.
    # The app may still show the real O*NET tasks without inventing a goal.
    return (), "no occupation-specific SDG rule", "unassessed"


def suggested_goal_ids(career_id, career_title):
    """Backwards-compatible (ids, basis) helper, not a causal impact estimator."""
    goals, basis, _ = _suggestion(career_id, career_title)
    return goals, basis


def infer_occupation_sdg_mappings(career_id, career_title):
    """Occupation *theme* suggestions, separate from FutureSkill training links."""
    ids, basis, specificity = _suggestion(career_id, career_title)
    mappings = []
    for goal_id in dict.fromkeys(ids):
        # A SOC-group fallback is deliberately weaker than a title-specific
        # specialty, and neither has been verified against actual job tasks.
        qualification = (
            "Occupation-title thematic suggestion; requires task-level verification."
            if specificity == "title_rule" else
            "Broad SOC-group exploration only; this occupation may not contribute "
            "directly to the goal. Requires task-level verification."
        )
        mappings.append({
            "sdg_id": goal_id,
            "sdg_name": GOAL_NAMES[goal_id],
            "target_id": None,
            "target_summary": "Possible theme only; no occupation-to-target verification.",
            "career_id": career_id,
            "review_status": "rule_based_suggestion",
            "mapping_kind": "occupation_theme",
            "specificity": specificity,
            "match_basis": basis,
            "relevance_reason": (
                f"{career_title} matches the {basis} classification. This gives a "
                f"possible connection to SDG {goal_id} ({GOAL_NAMES[goal_id]}). "
                + qualification
            ),
            # These are TRACEABILITY NOTES, not scientific proof of impact.
            "supporting_evidence": [
                f"Catalogued occupation: {career_title} (O*NET ID: {career_id}).",
                f"Rule used: {basis}.",
                qualification,
            ],
            "evidence_source": [
                {
                    "id": "onet-soc-taxonomy",
                    "label": "O*NET · Occupation classification",
                    "url": "https://www.onetcenter.org/taxonomy.html",
                    "scope": "Occupational classification, not evidence of SDG impacts.",
                },
                {
                    "id": f"un-sdg-goal-{goal_id}",
                    "label": f"United Nations · SDG {goal_id}",
                    "url": f"https://sdgs.un.org/goals/goal{goal_id}",
                    "scope": "Goal definition only, not proof of occupational contribution.",
                },
                {
                    "id": "onet-tasks-documentation",
                    "label": "O*NET · Task Statements (recommended verification data)",
                    "url": "https://www.onetcenter.org/dictionary/31.0/csv/task_statements.html",
                    "scope": "Official Task Statements documentation; task evidence is separately matched by exact O*NET code and Task ID.",
                },
            ],
            "supporting_source_ids": [
                "onet-soc-taxonomy", f"un-sdg-goal-{goal_id}",
                "onet-tasks-documentation",
            ],
            "user_action": (
                "Check this career's published O*NET tasks and the exact SDG "
                "target before treating this thematic suggestion as an alignment."
            ),
            "impact_limitations": LIMITATIONS,
        })
    return mappings
