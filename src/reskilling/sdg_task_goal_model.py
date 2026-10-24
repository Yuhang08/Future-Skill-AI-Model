"""Task-to-SDG goal-level RELEVANCE RANKING (not verified UN impacts).

For each O*NET occupation, rank all 17 UN Goals using every official Task
Statement and any linked DWAs / unsuppressed occupational task ratings.

The model is explainable, offline, dependency-free and intentionally
conservative.  It measures thematic *text similarity* and characteristic
task-phrases, not outcome achievement, target certification, job quality,
a probability, or model validation.  A "Top 3" is returned even for weak
matching occupations, but a weak result is explicitly identified as such.
This module NEVER fabricates occupation task records or Task IDs.
"""
from collections import Counter
from functools import lru_cache
from math import log1p, sqrt
import re

from .sdg_candidate_ranker import _task_rows
from .sdg_occupation_rules import GOAL_NAMES
from .sdg_onet_context import get_context

MODEL_VERSION = "task-goal-lexical-v1"
# Short, deliberately distinct domain vocabulary for each official Goal.
# Unlike the *specific UN targets*, these are broad GOAL-level topic clues.
GOAL_CONTEXT = {
    1: "poverty alleviation welfare public benefits social protection income support low income housing homeless assistance hardship social work aid financial security",
    2: "hunger food security nutrition agricultural farming crops livestock cultivation harvest irrigation fisheries sustainable agriculture food production malnutrition",
    3: "health medicine patient nursing clinical medical diagnostics disease disease prevention mental health treatment pharmacy hospital rehabilitation healthcare",
    4: "education teaching classroom school students instruction learning curriculum tutoring assessment vocational learning university literacy educational access",
    5: "gender equality women girls maternity discrimination reproductive rights equitable workplaces violence against women equal opportunities",
    6: "clean water drinking water sanitation wastewater sewage treatment water pollution water quality filtration reservoirs water resources contamination",
    7: "clean renewable energy solar photovoltaic wind turbines power generation electricity geothermal hydropower energy efficiency energy conservation",
    8: "employment worker rights decent working conditions wages occupational safety workplace worker protections labor standards vocational jobs",
    9: "industry technology infrastructure engineering research innovation manufacturing machinery production systems industrial processes software development digital technology",
    10: "reduced inequalities accessibility disability inclusion equal rights discrimination inclusive services immigrant inclusion equitable access social integration",
    11: "sustainable cities urban planning transportation public transit affordable housing infrastructure communities heritage disaster resilient buildings architecture",
    12: "responsible consumption sustainable production recycling reusable materials waste prevention circular economy material efficiency product sustainability procurement",
    13: "climate action carbon emissions climate change greenhouse gas adaptation mitigation energy emissions resilience atmosphere decarbonization",
    14: "life below water marine sea ocean fisheries coastal ecosystems coral reef aquatic habitats marine conservation fish biodiversity",
    15: "life on land forest wildlife conservation biodiversity ecosystems land restoration endangered species soil ecology sustainable forestry natural habitats",
    16: "peace justice institutions judiciary courts public law legal rights anti corruption public governance crime prevention legal enforcement",
    17: "partnership international cooperation sustainable development coordination cross border international aid public private joint programs collaborative partnerships",
}
# Strong, inspectable task terms. Generic verbs ("work", "manage",
# "support") deliberately do not trigger SDG 8 or any other goal.
PHRASES = {
    1: ("poverty", "social protection", "welfare benefits", "unemployment benefits",
        "low-income housing", "homelessness", "public assistance"),
    2: ("food security", "crop production", "nutrition", "farming", "harvest",
        "agriculture", "malnutrition", "livestock"),
    3: ("patients", "medical treatment", "diagnos", "clinical", "healthcare",
        "nursing care", "mental health", "disease prevention", "medicine"),
    4: ("teach students", "classroom", "curriculum", "school children",
        "student learning", "lesson plan", "educational software", "literacy"),
    5: ("gender equality", "women's rights", "sexual harassment",
        "gender discrimination", "equal pay for women"),
    6: ("wastewater", "sewage treatment", "water pollution",
        "water quality", "drinking water", "water sanitation"),
    7: ("solar power", "solar energy", "photovoltaic", "wind turbine",
        "renewable energy", "hydroelectric", "power generation", "energy efficiency"),
    8: ("worker safety", "occupational safety", "employee rights",
        "workplace conditions", "labor standards", "labour standards", "job training"),
    9: ("software development", "software applications", "industrial",
        "research and development", "infrastructure", "engineering design",
        "design systems", "manufacturing", "technology", "prototype", "machines"),
    10: ("accessibility", "disability", "equal opportunity", "discrimination",
         "social inclusion", "inclusive access", "equitable services"),
    11: ("urban planning", "public transportation", "public transit", "buildings",
         "housing", "disaster recovery", "city planning", "architecture"),
    12: ("recycling", "recycled materials", "reuse materials", "reduce waste",
         "food waste", "scrap for recycling", "waste prevention", "resource efficiency"),
    13: ("climate change", "greenhouse gas", "carbon emissions",
         "energy conservation", "emission reductions", "climate adaptation"),
    14: ("marine", "ocean", "coastal", "coral", "aquatic habitat",
         "fisheries management", "seawater"),
    15: ("forestry", "wildlife", "forest", "ecosystem", "biodiversity",
         "soil conservation", "habitat restoration", "protected land"),
    16: ("law enforcement", "court proceedings", "judicial", "crime prevention",
         "civil rights", "public governance", "legal representation"),
    17: ("international partnership", "international cooperation",
         "cross-border", "development partnership", "public-private partnership"),
}
STOP_WORDS = frozenset(
    "about above across after again against all also among and are around as "
    "at back based before between both by can check could does doing each "
    "ensure every for from have having into in is its make may more must "
    "not of on or other our over per provide related services such than "
    "that the their them these this those through to under using use via "
    "was were what when where which while who with within would your"
    .split()
)
WORD_RE = re.compile(r"[a-z]{4,}")
PHRASE_REGEX = {
    goal: tuple(
        (phrase, re.compile(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])"))
        for phrase in phrases
    )
    for goal, phrases in PHRASES.items()
}


def _stem(word):
    """Small deterministic normalization; not an English semantic model."""
    word = word.lower()
    if word.endswith("ies") and len(word) > 6:
        return word[:-3] + "y"
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) > len(suffix) + 4:
            return word[:-len(suffix)]
    return word


def _word_set(text):
    return {
        _stem(word) for word in WORD_RE.findall(str(text).lower())
        if word not in STOP_WORDS
    }


@lru_cache(maxsize=17)
def _goal_terms(goal):
    return _word_set(GOAL_CONTEXT[goal])


@lru_cache(maxsize=17)
def _goal_char_grams(goal):
    return {
        word[i:i+4]
        for word in _goal_terms(goal)
        if len(word) >= 5
        for i in range(len(word)-3)
    }


def _lexical_similarity(task, goal):
    """Transparent sparse word and within-word character overlap, 0..1."""
    terms = _word_set(task)
    if not terms:
        return 0.0
    reference = _goal_terms(goal)
    exact = len(terms & reference) / max(1, sqrt(len(terms) * len(reference)))
    grams = {
        word[i:i+4] for word in terms if len(word) >= 5
        for i in range(len(word)-3)
    }
    goal_grams = _goal_char_grams(goal)
    fuzzy = len(grams & goal_grams) / max(1, sqrt(len(grams) * len(goal_grams)))
    # Fuzzy overlap is only a WEAK exploratory tiebreaker.
    return min(1.0, 0.85 * exact + 0.15 * fuzzy)


def _phrase_hits(text, goal):
    lowered = str(text).lower()
    return [name for name, pattern in PHRASE_REGEX[goal] if pattern.search(lowered)]


def _rating_factor(task):
    """Only occupational task importance/relevance; NOT SDG impact."""
    rating = task.get("task_ratings") or {}
    importance = rating.get("importance_1_to_5")
    relevance = rating.get("relevance_pct")
    im = (float(importance) / 5.0) if isinstance(importance, (int, float)) else 0.6
    rt = (float(relevance) / 100.0) if isinstance(relevance, (int, float)) else 0.7
    return (0.7 + 0.3 * im) * (0.8 + 0.2 * rt)


def _score_task(task, goal):
    actual = task["task"]
    dwas = task.get("dwa_activities") or []
    hits = _phrase_hits(actual, goal)
    dwa_hits = sorted({
        label for dwa in dwas
        for label in _phrase_hits(dwa["name"], goal)
    })
    lexical = _lexical_similarity(actual, goal)
    # Direct, identified duty phrases have more weight than linked DWAs.
    # Lexical similarity retains a small exploratory signal when exact
    # phrase rules miss relevant duties.  All weights are model assumptions.
    raw = (
        min(2, len(hits)) * 1.0
        + min(2, len(dwa_hits)) * 0.42
        + lexical * 0.45
    )
    core = 1.0 if str(task.get("type", "")).lower() == "core" else 0.7
    total = core * _rating_factor(task) * raw
    return {
        "raw": total,
        "task_id": str(task["id"]),
        "task": actual,
        "task_type": task.get("type", ""),
        "task_ratings": task.get("task_ratings", {}),
        "dwa_activities": dwas[:4],
        "phrase_matches": hits,
        "dwa_phrase_matches": dwa_hits,
        "task_score": round(total, 5),
    }


def _score_rows(career_id):
    rows, status = _task_rows(career_id)
    if not rows:
        return [], status
    enriched = []
    for row in rows:
        context = get_context(career_id, row["id"])
        enriched.append({**row, "task_ratings": context["task_ratings"],
                         "dwa_activities": context["dwas"]})
    scored = []
    for goal in range(1, 18):
        matches = [_score_task(task, goal) for task in enriched]
        matches.sort(key=lambda item: (-item["raw"], item["task_id"]))
        positive = [item for item in matches if item["raw"] > 0]
        # Average of the three most relevant *actual tasks*, with a small
        # diversity bonus; this avoids large task lists dominating the rank.
        top = positive[:3]
        raw = sum(item["raw"] for item in top) / 3.0
        raw += 0.035 * log1p(len([item for item in matches if item["raw"] >= 0.08]))
        index = round(100 * raw / (raw + 1.5), 1) if raw else 0.0
        direct = sum(bool(item["phrase_matches"]) for item in top)
        dwa = sum(bool(item["dwa_phrase_matches"]) for item in top)
        basis = ("direct_task_topic" if direct else
                 "linked_dwa_topic" if dwa else "lexical_similarity_only")
        evidence = top if top else matches[:1]
        scored.append({
            "sdg_id": goal,
            "sdg_name": GOAL_NAMES[goal],
            "relevance_index": index,
            "raw_score": round(raw, 6),
            "task_count": len(rows),
            "related_task_count": len([item for item in matches if item["raw"] >= 0.08]),
            "task_evidence": [
                {key: value for key, value in task.items() if key != "raw"}
                for task in evidence
            ],
            "evidence_basis": basis if positive else "no_detected_overlap",
            "explanation": (
                f"Compared {len(rows)} real O*NET Task Statements and available "
                "linked DWAs to Goal-level task themes; the relevance index "
                "comes from the three strongest occupational tasks. "
                "Scores are descriptive model estimates, NOT SDG success, "
                "probabilities, official alignments or target certifications."
            ),
            "goal_source": f"https://sdgs.un.org/goals/goal{goal}",
            "occupation_source": f"https://www.onetonline.org/link/details/{career_id}",
        })
    scored.sort(key=lambda item: (-item["raw_score"], item["sdg_id"]))
    for rank, item in enumerate(scored, start=1):
        item["rank"] = rank
        item["review_status"] = (
            "task_text_candidate" if item["evidence_basis"] == "direct_task_topic"
            else "dwa_candidate" if item["evidence_basis"] == "linked_dwa_topic"
            else "weak_exploratory_ranking"
        )
    return scored, status


@lru_cache(maxsize=1024)
def score_career_goals(career_id, source_stamp=None):
    """Return ALL 17 scores and TOP 3 for a real occupation; no fake tasks.

    Pass source_stamp from the caller to refresh results if official CSV
    contents change on disk while the process is running.
    """
    del source_stamp
    ranked, status = _score_rows(career_id)
    return {
        "status": status,
        "model": MODEL_VERSION,
        "goal_scores": ranked,
        "top_goal_scores": ranked[:3],
        "method": (
            "Task-level phrase and lexical overlap (Core tasks weighted 1.0, "
            "Supplemental 0.7; available O*NET IM/RT rating weights). "
            "Linked DWA phrases count less than direct Task phrases. "
            "Top-three task aggregation uses fixed saturating scale 0–100. "
            "Rankings are exploratory and NOT probabilities or UN certifications."
        ),
    }
