"""FutureSkill AI — 17 SDG Mapping Engine (standalone, standard library only).

Run: python sdg_mapping.py
This is an explainable prototype: associations indicate potential contributions,
not UN endorsements or measured social impact.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Official UN goal numbers, English names and standard SDG brand colours.
SDG_DATA = {
    1: {"name": "No Poverty", "color": "#E5243B", "short": "End poverty"},
    2: {"name": "Zero Hunger", "color": "#DDA63A", "short": "Food security"},
    3: {"name": "Good Health and Well-being", "color": "#4C9F38", "short": "Better health"},
    4: {"name": "Quality Education", "color": "#C5192D", "short": "Better learning"},
    5: {"name": "Gender Equality", "color": "#FF3A21", "short": "Equal opportunity"},
    6: {"name": "Clean Water and Sanitation", "color": "#26BDE2", "short": "Clean water"},
    7: {"name": "Affordable and Clean Energy", "color": "#FCC30B", "short": "Clean energy"},
    8: {"name": "Decent Work and Economic Growth", "color": "#A21942", "short": "Decent work"},
    9: {"name": "Industry, Innovation and Infrastructure", "color": "#FD6925", "short": "Innovation"},
    10: {"name": "Reduced Inequalities", "color": "#DD1367", "short": "Inclusion"},
    11: {"name": "Sustainable Cities and Communities", "color": "#FD9D24", "short": "Better cities"},
    12: {"name": "Responsible Consumption and Production", "color": "#BF8B2E", "short": "Resource efficiency"},
    13: {"name": "Climate Action", "color": "#3F7E44", "short": "Climate solutions"},
    14: {"name": "Life Below Water", "color": "#0A97D9", "short": "Ocean protection"},
    15: {"name": "Life on Land", "color": "#56C02B", "short": "Nature protection"},
    16: {"name": "Peace, Justice and Strong Institutions", "color": "#00689D", "short": "Justice"},
    17: {"name": "Partnerships for the Goals", "color": "#19486A", "short": "Partnerships"},
}

# Specific job-title matches are checked first, before general occupational matches.
# Patterns include word boundaries to avoid e.g. 'AI' matching inside 'marine'.
SPECIFIC_CAREER_PATTERNS = {
    1: [r"\bpoverty\b", r"\bpoverty reduction\b", r"\bsocial welfare\b"],
    2: [r"\bagricultur\w*\b", r"\bfarm\w*\b", r"\bnutritionist\b", r"\bfood security\b"],
    3: [r"\bnurs\w*\b", r"\bdoctor\b", r"\bphysician\b", r"\bmedical\b", r"\bhealth\w*\b", r"\btherap\w*\b",
        r"\bpharmac\w*\b"],
    4: [r"\bteach\w*\b", r"\btutor\b", r"\bprofessor\b", r"\beducat\w*\b", r"\bschool counselor\b"],
    5: [r"\bgender equality\b", r"\bwomen'?s? rights\b", r"\bgender policy\b"],
    6: [r"\bwater treatment\b", r"\bwastewater\b", r"\bsanitation\b", r"\bwater quality\b"],
    7: [r"\bsolar\b", r"\brenewable energy\b", r"\bwind energy\b", r"\bclean energy\b"],
    8: [r"\bhuman resources\b", r"\blabou?r economist\b", r"\bemployment\b", r"\bworkforce development\b"],
    9: [r"\bartificial intelligence\b", r"\bAI engineer\b", r"\bmachine learning\b", r"\bsoftware\b",
        r"\bdata scientist\b", r"\brobot\w*\b"],
    10: [r"\bsocial worker\b", r"\bdisability\b", r"\binclusion\b", r"\baccessibility\b"],
    11: [r"\burban plan\w*\b", r"\barchitect\w*\b", r"\bpublic transport\b", r"\bcity plan\w*\b"],
    12: [r"\brecycl\w*\b", r"\bwaste management\b", r"\bcircular economy\b", r"\bresource efficiency\b"],
    13: [r"\bclimat\w*\b", r"\benvironment\w*\b", r"\bcarbon\b", r"\bsustainab\w*\b"],
    14: [r"\bmarine\b", r"\bocean\w*\b", r"\bfisher\w*\b", r"\baquatic\b"],
    15: [r"\bforest\w*\b", r"\bwildlife\b", r"\bbiodivers\w*\b", r"\becolog\w*\b"],
    16: [r"\bhuman rights\b", r"\blawyer\b", r"\bjudg\w*\b", r"\bjustice\b", r"\banti.?corruption\b"],
    17: [r"\bdiplomat\w*\b", r"\binternational cooperation\b", r"\bpartnership\w*\b"],
}

GENERAL_CAREER_PATTERNS = {
    8: [r"\baccountant\b", r"\beconomist\b", r"\bentrepreneur\w*\b", r"\bchef\b", r"\bbusiness\b"],
    9: [r"\bengineer\w*\b", r"\bscientist\b", r"\btechnolog\w*\b", r"\bprogrammer\b", r"\bstatistician\b"],
    11: [r"\bcommunity designer\b", r"\bmunicipal\b"],
}

CAREER_IMPACT = {
    1: "Support poverty reduction",
    2: "Improve food security",
    3: "Improve healthcare and well-being",
    4: "Expand access to education",
    5: "Promote equal opportunities",
    6: "Improve water and sanitation systems",
    7: "Develop clean energy solutions",
    8: "Support decent jobs and livelihoods",
    9: "Build innovative technologies and infrastructure",
    10: "Reduce barriers and exclusion",
    11: "Make communities more sustainable",
    12: "Reduce waste and resource use",
    13: "Develop climate solutions",
    14: "Protect oceans and marine life",
    15: "Protect ecosystems and biodiversity",
    16: "Advance justice and effective institutions",
    17: "Build partnerships for shared goals",
}

# Names match the six skill keys in the FutureSkill AI assessment.
SKILL_RULES = {
    "MathSkill": [9],
    "CodingSkill": [9],
    "DataSkill": [9, 13],
    "CommunicationSkill": [4, 16],
    "LeadershipSkill": [8, 17],
    "CreativeSkill": [11, 12],
}


def _goal(sdg_id, *, provisional=False):
    """Return one UI-ready SDG node."""
    data = SDG_DATA[sdg_id]
    return {
        "id": sdg_id,
        "name": data["name"],
        "short": data["short"],
        "color": data["color"],
        "reason": CAREER_IMPACT[sdg_id],
        "url": f"https://sdgs.un.org/goals/goal{sdg_id}",
        "provisional": provisional,
    }


def get_all_sdgs():
    """Return all 17 SDGs (including ones not matched by a particular career)."""
    return [_goal(sdg_id) for sdg_id in range(1, 18)]


def _pattern_hits(title, patterns):
    return any(re.search(pattern, title, flags=re.IGNORECASE) for pattern in patterns)


def map_career(title, max_sdgs=4):
    """Map a job title to 1-4 possible SDGs; specific rules take priority."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Career title must be non-empty text")
    if not isinstance(max_sdgs, int) or max_sdgs < 1:
        raise ValueError("max_sdgs must be a positive integer")

    matches = []
    for sdg_id, patterns in SPECIFIC_CAREER_PATTERNS.items():
        if _pattern_hits(title, patterns):
            matches.append(sdg_id)
    for sdg_id, patterns in GENERAL_CAREER_PATTERNS.items():
        if sdg_id not in matches and _pattern_hits(title, patterns):
            matches.append(sdg_id)

    if not matches:
        # A placeholder, NOT a confident classification; must be reviewed.
        return [_goal(8, provisional=True)]
    return [_goal(sdg_id) for sdg_id in matches[:max_sdgs]]


def map_skills(skill_scores):
    """Map the six questionnaire skills to possible SDGs."""
    if not isinstance(skill_scores, dict):
        raise ValueError("skill_scores must be a dictionary")

    results = []
    for skill, rating in skill_scores.items():
        if skill not in SKILL_RULES:
            raise ValueError(f"Unknown skill: {skill}")
        if isinstance(rating, bool) or not isinstance(rating, (int, float)) or not 1 <= rating <= 5:
            raise ValueError(f"{skill}: self-rating must be 1 to 5")
        results.append({
            "skill": skill,
            "self_rating": rating,
            "sdgs": [_goal(sdg_id) for sdg_id in SKILL_RULES[skill]],
        })
    return results


def build_mindmap(career_title, skill_scores=None):
    """Generate nodes and links for a future interactive mind map."""
    goals = map_career(career_title)
    skills = map_skills(skill_scores or {})

    nodes = [{"id": "career", "type": "career", "label": career_title}]
    links = []
    for goal in goals:
        nodes.append({
            "id": f"sdg-{goal['id']}", "type": "sdg",
            "label": f"SDG {goal['id']}", "name": goal["name"],
            "color": goal["color"], "short": goal["short"],
        })
        links.append({"from": "career", "to": f"sdg-{goal['id']}"})

    goal_ids = {goal["id"] for goal in goals}
    for skill in skills:
        relevant = [goal["id"] for goal in skill["sdgs"] if goal["id"] in goal_ids]
        if not relevant:
            continue
        skill_id = f"skill-{skill['skill']}"
        nodes.append({"id": skill_id, "type": "skill", "label": skill["skill"],
                      "rating": skill["self_rating"]})
        for sdg_id in relevant:
            links.append({"from": f"sdg-{sdg_id}", "to": skill_id})

    return {
        "career": career_title, "goals": goals, "skills": skills,
        "nodes": nodes, "links": links,
        "note": "Possible SDG associations only; not verified impact or UN endorsement.",
    }


if __name__ == "__main__":
    print("=== ALL 17 SDGs ===")
    for goal in get_all_sdgs():
        print(f"SDG {goal['id']:2}: {goal['name']}")

    careers = [
        "AI Engineer", "Environmental Engineer", "Teacher", "Nurse",
        "Gender Equality Officer", "Poverty Reduction Specialist", "Marine Biologist",
        "Water Treatment Engineer", "Solar Energy Engineer", "Unknown Job Title",
    ]
    print("\n=== CAREER -> SDG TEST ===")
    for career in careers:
        print(f"{career:30} -> {[g['id'] for g in map_career(career)]}")

    demo_skills = {
        "MathSkill": 5, "CodingSkill": 4, "DataSkill": 5,
        "CommunicationSkill": 3, "LeadershipSkill": 4, "CreativeSkill": 4,
    }
    print("\n=== SKILLS -> SDG TEST ===")
    for skill in map_skills(demo_skills):
        print(f"{skill['skill']:21} -> {[g['id'] for g in skill['sdgs']]}")

    preview = build_mindmap("Environmental Engineer", demo_skills)
    output = Path(__file__).with_name("sdg_mindmap_demo.json")
    output.write_text(json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nMind map JSON saved: {output.name}")
    print(f"Nodes: {len(preview['nodes'])}; Links: {len(preview['links'])}")
    print("\nAll tests completed.")
