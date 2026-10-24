"""FutureSkill AI: targeted Reskilling skill-profile corrections.

These are expert-authored, illustrative learning templates informed by the
O*NET tasks/skills for Mathematicians (15-2021.00) and Actuaries (15-2011.00).
The required levels, importance weights, estimated hours and project tasks are
NOT official O*NET measurements or validated hiring requirements.

To integrate, copy this file to reskilling/occupation_skill_overrides.py and
put the following two lines AT THE END of reskilling/catalog.py:

from .occupation_skill_overrides import apply_overrides
apply_overrides(CAREERS)

These overrides are deliberately limited to two identified mismatches.
"""
from copy import deepcopy


def _skill(level, weight, hours, objective, project, prerequisites=()):
    return {
        "required": level,
        "importance": weight,
        "hours_per_level": hours,
        "objective": objective,
        "project": project,
        "prerequisites": list(prerequisites),
    }


# Editable demonstration learning profiles, not a replacement for an occupation-
# matched and validated dataset of all 923 careers.
OCCUPATION_OVERRIDES = {
    "Mathematicians": {
        "Mathematical Reasoning & Proof": _skill(
            4, 1.00, 6,
            "Form precise mathematical arguments and justify each inference",
            "Write and explain a rigorous proof of a chosen theorem"),
        "Calculus & Linear Algebra": _skill(
            4, 0.95, 6,
            "Apply multivariable calculus, eigenvalues and vector spaces",
            "Solve a small modelling problem using calculus and matrices"),
        "Abstract Mathematics": _skill(
            3, 0.90, 6,
            "Explore definitions, assumptions and abstract structures",
            "Investigate a theorem in algebra or discrete mathematics"),
        "Mathematical Modelling": _skill(
            4, 0.95, 6,
            "Translate a real problem into equations, assumptions and testable predictions",
            "Build and explain a simple differential-equation model",
            ["Calculus & Linear Algebra"]),
        "Numerical Methods": _skill(
            3, 0.75, 5,
            "Approximate solutions and evaluate errors and stability",
            "Compare exact and numerical solutions to an equation",
            ["Calculus & Linear Algebra"]),
        "Mathematical Research Communication": _skill(
            3, 0.85, 4,
            "Read mathematical literature and explain results clearly",
            "Write a short research-style note with references"),
    },
    "Actuaries": {
        "Probability & Statistics": _skill(
            4, 1.00, 6,
            "Apply probability distributions and statistical inference to uncertain outcomes",
            "Estimate event probabilities from a sample risk dataset"),
        "Financial Mathematics": _skill(
            4, 0.95, 6,
            "Apply interest, discounting and present-value calculations",
            "Calculate present values for example cash-flow scenarios"),
        "Insurance & Pension Fundamentals": _skill(
            3, 0.95, 5,
            "Explain insurance premiums, reserves and pension obligations",
            "Compare the assumptions of two hypothetical insurance products"),
        "Actuarial Risk Modelling": _skill(
            4, 1.00, 6,
            "Model uncertain losses and quantify potential liabilities",
            "Create an illustrative loss model and explain its assumptions",
            ["Probability & Statistics"]),
        "Statistical Data Tools": _skill(
            3, 0.80, 5,
            "Analyze risk-related data using a spreadsheet or statistical software",
            "Prepare a reproducible analysis of anonymized claims data"),
        "Risk Reporting & Communication": _skill(
            3, 0.85, 4,
            "Present uncertainty, limitations and results to nontechnical audiences",
            "Write a concise risk report with an understandable chart"),
    },
}


def apply_overrides(careers):
    """Mutate an existing CAREERS mapping, preserving unrelated occupations.

    Returns a list of occupation names actually corrected.
    """
    updated = []
    for title, skills in OCCUPATION_OVERRIDES.items():
        if title not in careers:
            continue
        if not isinstance(careers[title], dict):
            raise TypeError(f"Unexpected career schema for {title}")
        careers[title]["skills"] = deepcopy(skills)
        updated.append(title)
    return updated
