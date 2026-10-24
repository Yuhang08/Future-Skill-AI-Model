"""Curated, evidence-limited links between pathway skills and UN SDG targets."""

import re
from difflib import SequenceMatcher
from functools import lru_cache

from .catalog import CAREERS
from .sdg_candidate_ranker import candidate_mappings_for_occupation, occupation_task_profile
from .sdg_task_evidence import task_supported_mappings
from . import sdg_task_evidence as task_source
from .sdg_onet_context import DWA_CSV, RATINGS_CSV
from .sdg_task_goal_model import score_career_goals
from career_engine import load_careers


TARGETS = {
    "4.4": {
        "sdg_id": 4,
        "sdg_name": "Quality Education",
        "target_id": "4.4",
        "target_summary": (
            "Increase the number of youth and adults with relevant skills, "
            "including technical and vocational skills, for employment and decent jobs."
        ),
        "url": "https://sdgs.un.org/goals/goal4",
    },
    "8.5": {
        "sdg_id": 8,
        "sdg_name": "Decent Work and Economic Growth",
        "target_id": "8.5",
        "target_summary": (
            "Promote full and productive employment and decent work for all, "
            "including young people and persons with disabilities."
        ),
        "url": "https://sdgs.un.org/goals/goal8",
    },
}


# These are explicit title equivalences, not fuzzy matches. Roles outside this
# reviewed set remain unassigned until role-level evidence is added.
ROLE_CONFIG = {
    "Data Analyst": {
        "career_id": "prototype:data-analyst",
        "aliases": ("Data Analyst", "Data Analysts"),
        "evidence_skills": ("SQL", "Pandas", "Data Visualisation"),
        "user_action": (
            "Rate your SQL, Pandas, and data-visualisation skills in the "
            "reskilling pathway, then complete the practice project for each gap."
        ),
    },
    "Software Developer": {
        "career_id": "15-1252.00",
        "aliases": ("Software Developer", "Software Developers"),
        "evidence_skills": ("Python Basics", "Web Basics", "Testing"),
        "user_action": (
            "Rate your programming, web, and testing skills in the reskilling "
            "pathway, then complete the matching practice projects for any gaps."
        ),
    },
    "Cybersecurity Analyst": {
        "career_id": "prototype:cybersecurity-analyst",
        "aliases": ("Cybersecurity Analyst", "Cyber Security Analyst"),
        "occupational_aliases": {"15-1212.00": ("Information Security Analyst",)},
        "evidence_skills": ("Networking", "Security Fundamentals", "Log Analysis"),
        "user_action": (
            "Rate your networking, security, and log-analysis skills, then "
            "complete the associated safe practice activities for any gaps."
        ),
    },
    "UI/UX Designer": {
        "career_id": "prototype:ui-ux-designer",
        "aliases": ("UI/UX Designer", "UI UX Designer"),
        "occupational_aliases": {"15-1255.00": ()},
        "evidence_skills": ("Wireframing", "Accessibility", "Usability Testing"),
        "user_action": (
            "Rate your wireframing, accessibility, and usability-testing skills, "
            "then complete the matching design exercises for any gaps."
        ),
    },
    "Digital Marketing Specialist": {
        "career_id": "prototype:digital-marketing-specialist",
        "aliases": ("Digital Marketing Specialist",),
        "evidence_skills": ("Analytics", "Content Strategy", "Reporting"),
        "user_action": (
            "Rate your analytics, content-planning, and reporting skills, then "
            "complete a campaign analysis activity for any gaps."
        ),
    },
}

def _normalize_name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


@lru_cache(maxsize=1)
def get_sdg_careers():
    """Canonical occupational records plus explicitly namespaced prototypes."""
    occupations = load_careers()
    records = {}
    for _, row in occupations.iterrows():
        career_id = str(row.get("O*NET-SOC Code") or "").strip()
        title = str(row["Title"]).strip()
        if not re.fullmatch(r"\d{2}-\d{4}\.\d{2}", career_id):
            continue
        records[career_id] = {
            "id": career_id,
            "title": title,
            "kind": "occupation",
            "aliases": {title},
        }

    for name, config in ROLE_CONFIG.items():
        career_id = config["career_id"]
        if career_id in records:
            record = records[career_id]
        else:
            record = {
                "id": career_id,
                "title": name,
                "kind": "prototype",
                "aliases": {name},
            }
            records[career_id] = record
        record["aliases"].update(config["aliases"])

        # Preserve the existing curated occupational aliases without merging
        # prototype identities into the occupational CSV.
        for occupational_id, explicit_aliases in config.get("occupational_aliases", {}).items():
            if occupational_id in records:
                records[occupational_id]["aliases"].update(explicit_aliases)

    if "17-2081.00" in records:
        records["17-2081.00"]["aliases"].add("Environmental Engineer")
    return records


@lru_cache(maxsize=1)
def _career_aliases():
    aliases = {}
    for career_id, record in get_sdg_careers().items():
        for alias in record["aliases"]:
            aliases.setdefault(_normalize_name(alias), set()).add(career_id)
    return aliases


ROLE_BY_ID = {
    career_id: name
    for name, config in ROLE_CONFIG.items()
    for career_id in (config["career_id"], *config.get("occupational_aliases", {}))
}


def search_sdg_careers(query="", limit=12):
    """Return suggestions only; callers must require an explicit selected ID."""
    query = str(query or "").strip()
    if len(query) > 100:
        return []
    normalized = _normalize_name(query)
    records = get_sdg_careers()
    aliases = _career_aliases()
    pathway_ids = set(ROLE_BY_ID)

    def result(career_id, matched_by):
        career = records[career_id]
        return {
            "id": career_id,
            "title": career["title"],
            "kind": career["kind"],
            "mapping_availability": "suggested",
            "matched_by": matched_by,
        }

    if normalized:
        exact_ids = aliases.get(normalized, set())
        if exact_ids:
            return [result(career_id, "exact") for career_id in sorted(exact_ids)[:limit]]

        partial = []
        for career_id, career in records.items():
            if any(normalized in _normalize_name(alias) for alias in career["aliases"]):
                partial.append((career_id, min(
                    len(_normalize_name(alias)) for alias in career["aliases"]
                    if normalized in _normalize_name(alias)
                )))
        if partial:
            partial.sort(key=lambda pair: (pair[1], records[pair[0]]["title"].casefold()))
            return [result(career_id, "partial") for career_id, _ in partial[:limit]]

        suggestions = []
        for career_id, career in records.items():
            score = max(
                (SequenceMatcher(None, normalized, _normalize_name(alias)).ratio()
                 for alias in career["aliases"]),
                default=0,
            )
            if score >= 0.62:
                suggestions.append((career_id, score))
        suggestions.sort(key=lambda pair: (-pair[1], records[pair[0]]["title"].casefold()))
        return [result(career_id, "suggestion") for career_id, _ in suggestions[:limit]]

    featured = sorted(
        records,
        key=lambda career_id: (
            career_id not in pathway_ids,
            records[career_id]["title"].casefold(),
        ),
    )
    return [result(career_id, "featured") for career_id in featured[:limit]]


def resolve_sdg_career_id(title):
    matches = _career_aliases().get(_normalize_name(title), set())
    return next(iter(matches)) if len(matches) == 1 else None

REVIEWED_SCOPE = (
    "Potential alignment only. FutureSkill pathway skill requirements and "
    "practice activities are illustrative, not independently validated. This "
    "mapping does not establish employment, decent working conditions, fair "
    "access, or measurable progress on an SDG indicator. UN goal pages define "
    "the targets; they do not prove an occupational connection."
)


def _pathway_skills(career_name, current_skills=None):
    role_skills = CAREERS[career_name]["skills"]
    current_skills = current_skills if isinstance(current_skills, dict) else {}
    result = []
    for name, detail in role_skills.items():
        current = current_skills.get(name)
        if isinstance(current, bool) or not isinstance(current, (int, float)) or not 0 <= current <= 5:
            current = None
        result.append({
            "name": name,
            "required_level": detail["required"],
            "current_level": current,
            "gap_level": max(0, detail["required"] - current) if current is not None else None,
            "objective": detail["objective"],
            "project": detail["project"],
        })
    return result


def _unknown_alignment(title):
    return {
        "career": title,
        "career_id": None,
        "pathway_career": None,
        "status": "unknown",
        "task_data_status": "unknown",
        "task_profile": None,
        "goal_scores": [],
        "top_goal_scores": [],
        "goal_scoring_method": None,
        "mappings": [],
        "candidate_mappings": [],
        "learning_pathway_mappings": [],
        "pathway_skills": [],
        "evidence_scope": "This title is not in the supported career catalogue.",
    }


def _build_alignment(career_id, current_skills=None, include_goal_scores=False):
    career = get_sdg_careers().get(career_id)
    if career is None:
        return _unknown_alignment("")
    career_name = ROLE_BY_ID.get(career_id)
    # Real occupational task records, not job titles, drive highlighted nodes.
    task_mappings, task_data_status = task_supported_mappings(career_id, career["title"])
    # Each role has an independently inspectable O*NET task profile and up to
    # three ranked candidate goals. Never confuse them with verified impacts.
    task_profile = occupation_task_profile(career_id)
    # Ranking is an on-demand feature: the 923-row legacy audit/tests remain
    # fast and stable, while the website can show 17 scored goals per role.
    scored = {}
    if include_goal_scores and career["kind"] == "occupation":
        stamp = tuple(
            (str(p), p.stat().st_mtime_ns if p.is_file() else None)
            for p in (task_source.TASK_DATA, DWA_CSV, RATINGS_CSV)
        )
        scored = score_career_goals(career_id, stamp)
    candidate_mappings = candidate_mappings_for_occupation(
        career_id, career["title"], {m["sdg_id"] for m in task_mappings}
    )
    if career_name is None or career_name not in CAREERS:
        return {
            "career": career["title"],
            "career_id": career_id,
            "pathway_career": None,
            "status": "task_supported" if task_mappings else "no_task_evidence",
            "task_data_status": task_data_status,
            "task_profile": task_profile,
            "goal_scores": scored.get("goal_scores", []),
            "top_goal_scores": scored.get("top_goal_scores", []),
            "goal_scoring_method": scored.get("method"),
            "mappings": task_mappings,
            "candidate_mappings": candidate_mappings,
            "learning_pathway_mappings": [],
            "pathway_skills": [],
            "evidence_scope": (
                "Only explicit rule matches in genuine O*NET 31.0 task statements "
                "are shown on the career map. Title/SOC fallback is for browsing "
                "only; neither supplies verified SDG outcome evidence."
            ),
        }

    config = ROLE_CONFIG[career_name]
    skills = _pathway_skills(career_name, current_skills)
    skill_by_name = {item["name"]: item for item in skills}
    evidence = []
    for skill_name in config["evidence_skills"]:
        skill = skill_by_name[skill_name]
        evidence.append(
            f"Illustrative pathway requirement: {skill_name} "
            f"(self-rating target {skill['required_level']}/5)."
        )
        evidence.append(f"Practice activity: {skill['project']}.")

    learning_mappings = []
    for target_id in ("4.4", "8.5"):
        target = TARGETS[target_id]
        if target_id == "4.4":
            reason = (
                f"The {career_name} pathway links role-related skills to guided "
                "practice activities. That is a potential connection to Target 4.4's "
                "focus on relevant skills for employment."
            )
        else:
            reason = (
                f"The {career_name} pathway helps a learner practise skills associated "
                "with a potential occupation. This is a preparation link to Target 8.5, "
                "not evidence that the learner will obtain decent work."
            )
        learning_mappings.append({
            "sdg_id": target["sdg_id"],
            "sdg_name": target["sdg_name"],
            "target_id": target["target_id"],
            "target_summary": target["target_summary"],
            "career_id": career_id,
            "review_status": "curated_illustrative",
            "mapping_kind": "pathway_preparation",
            "relevance_reason": reason,
            "supporting_evidence": evidence,
            "evidence_source": [
                {
                    "id": f"un-sdg-goal-{target['sdg_id']}",
                    "label": f"United Nations · SDG {target['sdg_id']} targets",
                    "url": target["url"],
                    "scope": "Target definition only; not occupational evidence.",
                },
                {
                    "id": "futureskill-reskilling-catalogue",
                    "label": "FutureSkill reskilling catalogue (illustrative)",
                    "url": "/reskilling",
                    "scope": "Illustrative pathway requirements and practice, not validated occupational requirements.",
                },
            ],
            "supporting_source_ids": [
                f"un-sdg-goal-{target['sdg_id']}",
                "futureskill-reskilling-catalogue",
            ],
            "user_action": config["user_action"],
            "impact_limitations": REVIEWED_SCOPE,
        })

    # This distinction is essential: FutureSkill's training may relate to
    # UN 4.4 / 8.5, but it does not make every IT career an SDG 4/8 occupation.
    return {
        "career": career["title"],
        "career_id": career_id,
        "pathway_career": career_name,
        "status": "task_supported" if task_mappings else "no_task_evidence",
        "task_data_status": task_data_status,
        "task_profile": task_profile,
        "goal_scores": scored.get("goal_scores", []),
        "top_goal_scores": scored.get("top_goal_scores", []),
        "goal_scoring_method": scored.get("method"),
        "mappings": task_mappings,
        "candidate_mappings": candidate_mappings,
        "learning_pathway_mappings": learning_mappings,
        "pathway_skills": skills,
        "evidence_scope": (
            "Career graph: narrow rule matches in real O*NET 31.0 job tasks, "
            "not measured SDG impacts. Broad title and SOC themes are clearly "
            "separate. Training Targets 4.4 and 8.5 describe only FutureSkill."
        ),
    }


def get_sdg_alignment_by_id(career_id, current_skills=None, include_goal_scores=False):
    """Return a verified catalogue identity and optional task-derived ranking."""
    return _build_alignment(
        str(career_id or "").strip(), current_skills, include_goal_scores
    )


def get_sdg_alignment(career_title, current_skills=None):
    """Legacy recommendation helper using exact, unambiguous catalogue aliases only."""
    title = str(career_title or "").strip()
    career_id = resolve_sdg_career_id(title)
    return _build_alignment(career_id, current_skills) if career_id else _unknown_alignment(title)
