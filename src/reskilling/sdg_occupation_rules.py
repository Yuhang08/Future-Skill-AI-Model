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
# Every SOC major group present in career_profiles_clean.csv is included.
MAJOR_GROUP_THEMES = {
    "11": ((8,), "management and organisational activity"),
    "13": ((8,), "business and financial operations"),
    "15": ((9,), "computing, mathematical methods and innovation"),
    "17": ((9,), "engineering and infrastructure"),
    "19": ((9,), "research, science and technical innovation"),
    "21": ((10,), "community and social services"),
    "23": ((16,), "law and access to justice"),
    "25": ((4,), "teaching and education"),
    "27": ((11,), "arts, cultural communication and communities"),
    "29": ((3,), "healthcare practice"),
    "31": ((3,), "healthcare support"),
    "33": ((16,), "public and protective services"),
    "35": ((12,), "food preparation and responsible resource use"),
    "37": ((11,), "building and grounds services"),
    "39": ((8,), "personal and client-facing services"),
    "41": ((8,), "sales and commercial activity"),
    "43": ((8,), "administrative and office operations"),
    "45": ((2, 15), "food systems and land-based resources"),
    "47": ((9, 11), "construction and the built environment"),
    "49": ((9, 12), "equipment maintenance and resource efficiency"),
    "51": ((9, 12), "manufacturing and production"),
    "53": ((9, 11), "transportation and infrastructure"),
    "55": ((16,), "public institutions and security"),
}

# More specific titles take priority over the broad occupational major group.
# Ordered from more specific to more general; return at most three theme goals.
TITLE_THEMES = (
    (r"\benvironmental engineer(?:ing|s)?\b", (6, 9, 13), "environmental engineering"),
    (r"\b(?:water|wastewater|sanitation|hydrolog(?:y|ist|ical)|sewage)\b", (6, 9), "water systems and sanitation"),
    (r"\b(?:solar|wind energy|wind turbine|renewable energy|biofuels?)\b", (7, 9, 13), "renewable energy"),
    (r"\b(?:climate|global warming|carbon emission)\b", (13, 9), "climate-related work"),
    (r"\b(?:sustainab(?:ility|le)|environmental protection|pollution control)\b", (12, 13), "sustainability and pollution prevention"),
    (r"\b(?:marine biology|oceanograph(?:y|er)|fishery|fisheries|aquacultur(?:e|al))\b", (14, 15), "aquatic ecosystems"),
    (r"\b(?:marine|ocean|seafar|sailor)\b", (14, 9), "marine systems"),
    (r"\b(?:forestry|forest|wildlife|ecolog(?:y|ist)|conservation|botan(?:y|ist))\b", (15, 13), "land ecosystems and biodiversity"),
    (r"\b(?:agricultur(?:e|al)|farm(?:er|ing|worker)?s?|crop|livestock|soil|horticultur(?:e|al))\b", (2, 15), "agriculture and food production"),
    (r"\b(?:equal opportunity|disability support|rehabilitation counselor)\b", (10, 16), "inclusion and equal access"),
    (r"\b(?:women's|gender equality|women and girls)\b", (5, 10), "gender equality"),
    (r"\b(?:international development|international relations|foreign aid)\b", (17, 16), "international partnerships"),
    (r"\b(?:social worker|social and human service|poverty|housing assistance)\b", (1, 10), "social support and economic inclusion"),
    (r"\b(?:biomedical|medical equipment|health informatics)\b", (3, 9), "medical and healthcare technology"),
    (r"\b(?:teacher|instructor|professor|tutor|educat(?:or|ion))\b", (4,), "education and skills development"),
    (r"\b(?:cybersecurity|cyber security|information security|security analyst)\b", (9, 16), "digital infrastructure and information security"),
    (r"\b(?:software|computer programmer|data analyst|data scientist|database|artificial intelligence|machine learning)\b", (9,), "digital systems and technical innovation"),
    (r"\b(?:user experience|ui\/ux|web and digital interface|graphic design)\b", (9, 10), "digital design and access"),
    (r"\b(?:digital marketing|advertising|marketing specialist)\b", (8, 12), "commercial communication and consumer choices"),
)

LIMITATIONS = (
    "Rule-based thematic suggestion from the occupation title or SOC major group. "
    "O*NET supplies occupational identity, and UN pages define goals; neither "
    "source establishes that this occupation achieves an SDG. No UN target, "
    "employment outcome or measured impact is verified. Expert review of job "
    "tasks and independent outcome evidence is needed for stronger claims."
)


def suggested_goal_ids(career_id, career_title):
    """Return (goal IDs, explicit classification basis) for a known catalogue role."""
    title = str(career_title or "")
    for pattern, goals, theme in TITLE_THEMES:
        if re.search(pattern, title, flags=re.IGNORECASE):
            return goals, "title theme: " + theme
    major_group = str(career_id or "")[:2]
    if major_group in MAJOR_GROUP_THEMES:
        goals, theme = MAJOR_GROUP_THEMES[major_group]
        return goals, "SOC major group: " + theme
    # Namespaced prototype titles without a recognisable specialist title.
    return (8,), "general career-preparation theme (no SOC classification)"


def infer_occupation_sdg_mappings(career_id, career_title):
    """Create explainable *goal-level suggestions*, never reviewed target links."""
    goal_ids, basis = suggested_goal_ids(career_id, career_title)
    mappings = []
    for goal_id in dict.fromkeys(goal_ids):
        mappings.append({
            "sdg_id": goal_id,
            "sdg_name": GOAL_NAMES[goal_id],
            "target_id": None,  # No invented target-level occupational evidence.
            "target_summary": (
                "Possible occupational theme; no specific UN target has been "
                "validated for this career."
            ),
            "career_id": career_id,
            "review_status": "rule_based_suggestion",
            "mapping_kind": "occupation_theme",
            "match_basis": basis,
            "relevance_reason": (
                f"The occupation '{career_title}' is grouped under {basis}. "
                f"This suggests a possible thematic connection to SDG {goal_id} "
                f"({GOAL_NAMES[goal_id]}), not proof of SDG impact."
            ),
            "supporting_evidence": [
                f"Occupation in the FutureSkill catalogue: {career_title} "
                f"(ID: {career_id}).",
                f"Transparent classification rule: {basis}.",
            ],
            "evidence_source": [
                {
                    "id": "onet-soc-taxonomy",
                    "label": "O*NET · Occupational taxonomy",
                    "url": "https://www.onetcenter.org/taxonomy.html",
                    "scope": "Occupation identity and taxonomy only; not SDG evidence.",
                },
                {
                    "id": f"un-sdg-goal-{goal_id}",
                    "label": f"United Nations · SDG {goal_id}",
                    "url": f"https://sdgs.un.org/goals/goal{goal_id}",
                    "scope": "Official definition of the goal, not a verified occupation link.",
                },
            ],
            "supporting_source_ids": [
                "onet-soc-taxonomy", f"un-sdg-goal-{goal_id}",
            ],
            "user_action": (
                "Check this occupation's actual tasks, identify an SDG-relevant "
                "activity and verify its possible outcomes using independent sources."
            ),
            "impact_limitations": LIMITATIONS,
        })
    return mappings
