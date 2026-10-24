"""Carefully labeled prototypes imported from the latest GitHub project state."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .sdg_alignment import (
    get_sdg_alignment_by_id,
    get_sdg_careers,
    search_sdg_careers,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
router = APIRouter()


CAREER_TRENDS = [
    {
        "category": "AI & Data Science",
        "historical_trend": "Growing",
        "future_trend": "Strong Growth",
        "direction": "Increase",
        "drivers": ["AI adoption", "Big data demand", "Digital transformation"],
        "impact": "More demand for AI and data skills",
        "skills": ["Python", "Machine Learning", "Statistics", "Data Analysis"],
        "careers": ["AI Engineer", "Data Scientist"],
    },
    {
        "category": "Software & IT",
        "historical_trend": "Growing",
        "future_trend": "Growing",
        "direction": "Increase",
        "drivers": ["Digital transformation", "AI-assisted development", "Cloud computing"],
        "impact": "Routine coding changes; system skills grow",
        "skills": ["Programming", "Cloud", "System Design", "AI Tools"],
        "careers": ["Software Developer", "Cloud Engineer"],
    },
    {
        "category": "Cybersecurity",
        "historical_trend": "Growing",
        "future_trend": "Strong Growth",
        "direction": "Increase",
        "drivers": ["Cyber threats", "Data protection", "AI security risks"],
        "impact": "Greater demand for security expertise",
        "skills": ["Cybersecurity", "Networking", "Risk Analysis", "AI Security"],
        "careers": ["Security Analyst", "Security Engineer"],
    },
    {
        "category": "Healthcare",
        "historical_trend": "Growing",
        "future_trend": "Growing",
        "direction": "Increase",
        "drivers": ["Population ageing", "Healthcare demand", "Medical technology"],
        "impact": "More care demand and AI-assisted tasks",
        "skills": ["Clinical Knowledge", "Communication", "AI Literacy"],
        "careers": ["Nurse", "Healthcare Specialist"],
    },
    {
        "category": "Education",
        "historical_trend": "Transforming",
        "future_trend": "Growing",
        "direction": "Increase",
        "drivers": ["Education demand", "Digital learning", "AI-assisted teaching"],
        "impact": "Teaching roles increasingly use AI",
        "skills": ["Teaching", "Digital Literacy", "Critical Thinking"],
        "careers": ["Teacher", "Education Specialist"],
    },
    {
        "category": "Engineering & Green Energy",
        "historical_trend": "Growing",
        "future_trend": "Strong Growth",
        "direction": "Increase",
        "drivers": ["Green transition", "Renewable energy investment", "Infrastructure demand"],
        "impact": "More opportunities in energy engineering",
        "skills": ["Engineering", "Sustainability", "Energy Systems"],
        "careers": ["Environmental Engineer", "Renewable Energy Engineer"],
    },
    {
        "category": "Business & Finance",
        "historical_trend": "Transforming",
        "future_trend": "Mixed",
        "direction": "Mixed / Uncertain",
        "drivers": ["Fintech innovation", "Process automation", "Economic change"],
        "impact": "Routine finance tasks change",
        "skills": ["Financial Analysis", "Fintech", "Risk Management"],
        "careers": ["Financial Analyst", "Bank Teller"],
    },
    {
        "category": "Sales & Customer Service",
        "historical_trend": "Transforming",
        "future_trend": "Mixed",
        "direction": "Mixed / Uncertain",
        "drivers": ["E-commerce", "AI customer service", "Consumer demand"],
        "impact": "Routine service tasks become automated",
        "skills": ["Communication", "Digital Marketing", "CRM"],
        "careers": ["Salesperson", "Customer Service Agent"],
    },
    {
        "category": "Manufacturing & Logistics",
        "historical_trend": "Transforming",
        "future_trend": "Mixed",
        "direction": "Mixed / Uncertain",
        "drivers": ["Robotics", "Supply chain restructuring", "Delivery demand"],
        "impact": "Some routine tasks automated",
        "skills": ["Automation", "Logistics", "Technical Maintenance"],
        "careers": ["Factory Worker", "Delivery Driver"],
    },
    {
        "category": "Administrative & Clerical",
        "historical_trend": "Automation Pressure",
        "future_trend": "Declining",
        "direction": "Decrease",
        "drivers": ["AI automation", "Digital documents", "Workflow software"],
        "impact": "Lower demand for repetitive clerical tasks",
        "skills": ["Digital Tools", "Coordination", "Communication"],
        "careers": ["Data Entry Clerk", "Administrative Assistant"],
    },
]

TREND_METADATA = {
    "historical_period": "2021–2025",
    "scenario_period": "2026–2030",
    "model_type": "Qualitative rule-based scenario",
    "geographic_scope": "Global",
    "quantitative_employment_forecast": False,
    "source": (
        "The imported GitHub dataset lists the World Economic Forum Future of Jobs "
        "Report 2025. It does not specify the exact table or page for each category."
    ),
    "limitations": [
        "Historical labels are qualitative, not annual job counts.",
        "Future labels are scenario assumptions, not a validated forecast.",
        "Country-specific results may differ.",
        "The listed source requires citation-level review before external claims.",
    ],
}


@router.get("/ai-trend", include_in_schema=False)
def ai_trend_page():
    return FileResponse(PROJECT_ROOT / "static" / "ai-trend.html")


@router.get("/uncertainty", include_in_schema=False)
def uncertainty_page():
    return FileResponse(PROJECT_ROOT / "static" / "uncertainty.html")


@router.get("/sdg-impact", include_in_schema=False)
def sdg_impact_page():
    return FileResponse(PROJECT_ROOT / "static" / "sdg-impact.html")


@router.get("/api/ai-trends")
def get_ai_trends():
    return {**TREND_METADATA, "categories": CAREER_TRENDS}


YEARS = tuple(range(2026, 2032))
BASE_EMPLOYMENT_RATE = 68.9


@dataclass(frozen=True)
class Scenario:
    name: str
    ai_growth: float
    automation: float
    adaptation: float
    economy: float
    alignment: float
    other_factors: float = 50


SCENARIOS = {
    "A": Scenario("Balanced Growth", 85, 65, 85, 85, 10, 60),
    "B": Scenario("AI Fast, Economy Slow", 85, 80, 35, 25, 15, 45),
    "C": Scenario("Traditional Economic Boom", 25, 30, 65, 85, 10, 60),
    "D": Scenario("Dual Stagnation", 20, 25, 30, 20, 10, 40),
    "E": Scenario("Over-Automation", 95, 95, 20, 70, 20, 50),
    "F": Scenario("Goal Misalignment", 85, 75, 50, 60, 90, 50),
}

JOBS = {
    "AI Engineer": (0.40, 0.90, 0.10, 0.40),
    "Software Developer": (0.55, 0.50, 0.35, 0.35),
    "Nurse": (0.40, 0.08, 0.08, 0.12),
    "Construction Worker": (0.85, 0.05, 0.30, 0.08),
    "Factory Assembly Worker": (0.70, 0.05, 0.90, 0.20),
    "Administrative Clerk": (0.45, 0.02, 0.95, 0.10),
    "Cybersecurity Specialist": (0.55, 0.65, 0.10, -0.20),
    "Electrician": (0.65, 0.15, 0.15, 0.06),
    "Cleaner": (0.40, 0.02, 0.55, 0.08),
    "Teacher": (0.38, 0.08, 0.20, 0.12),
}

MODEL_WARNING = (
    "Illustrative rule-based outputs only. The coefficients and 68.9% starting value "
    "are assumptions from the imported prototype, not calibrated or validated labour data."
)


def annual_rate_change(scenario: Scenario) -> float:
    economic_effect = 0.018 * (scenario.economy - 50)
    general_effect = 0.005 * (scenario.other_factors - 50)
    transition_gap = max(0, scenario.automation - scenario.adaptation)
    displacement_effect = -0.012 * transition_gap
    alignment_effect = -0.003 * scenario.alignment
    tech_opportunity = 0.003 * scenario.ai_growth * scenario.adaptation / 100
    return (
        economic_effect
        + general_effect
        + displacement_effect
        + alignment_effect
        + tech_opportunity
    )


def employment_scenario(scenario: Scenario, base_rate: float = BASE_EMPLOYMENT_RATE):
    rate = base_rate
    result = {YEARS[0]: round(rate, 2)}
    for year in YEARS[1:]:
        rate = max(0.0, min(100.0, rate + annual_rate_change(scenario)))
        result[year] = round(rate, 2)
    return result


def occupational_growth(scenario: Scenario):
    results = {}
    for job, (economy_weight, ai_weight, automation_weight, alignment_weight) in JOBS.items():
        growth = (
            0.06 * economy_weight * (scenario.economy - 50)
            + 0.035 * ai_weight * scenario.ai_growth
            - 0.045 * automation_weight * max(0, scenario.automation - 0.4 * scenario.adaptation)
            - 0.02 * alignment_weight * scenario.alignment
            + 0.008 * (scenario.other_factors - 50)
        )
        results[job] = round(growth, 2)
    return results


def scenario_result(scenario: Scenario, base_rate: float = BASE_EMPLOYMENT_RATE):
    return {
        "employment_rate": employment_scenario(scenario, base_rate),
        "occupational_growth": occupational_growth(scenario),
    }


def scenario_payload(key: str, scenario: Scenario):
    return {
        "id": key,
        "name": scenario.name,
        "inputs": {
            "ai_growth": scenario.ai_growth,
            "automation": scenario.automation,
            "adaptation": scenario.adaptation,
            "economy": scenario.economy,
            "alignment": scenario.alignment,
            "other_factors": scenario.other_factors,
        },
        **scenario_result(scenario),
    }


class ScenarioRequest(BaseModel):
    ai_growth: float = Field(ge=0, le=100)
    automation: float = Field(ge=0, le=100)
    adaptation: float = Field(ge=0, le=100)
    economy: float = Field(ge=0, le=100)
    alignment: float = Field(ge=0, le=100)
    other_factors: float = Field(default=50, ge=0, le=100)
    base_rate: float = Field(default=BASE_EMPLOYMENT_RATE, ge=0, le=100)


@router.get("/api/uncertainty/scenarios")
def get_uncertainty_scenarios():
    return {
        "years": YEARS,
        "base_rate": BASE_EMPLOYMENT_RATE,
        "warning": MODEL_WARNING,
        "scenarios": [
            scenario_payload(key, scenario)
            for key, scenario in SCENARIOS.items()
        ],
    }


@router.post("/api/uncertainty/simulate")
def simulate_uncertainty(request: ScenarioRequest):
    scenario = Scenario(
        "Custom",
        request.ai_growth,
        request.automation,
        request.adaptation,
        request.economy,
        request.alignment,
        request.other_factors,
    )
    return {
        **scenario_result(scenario, request.base_rate),
        "warning": MODEL_WARNING,
    }


class MindmapRequest(BaseModel):
    model_config = {"extra": "forbid"}
    career_id: str = Field(min_length=1, max_length=100)


@router.get("/api/sdg/careers")
def search_careers(q: str = Query(default="", max_length=100)):
    """Search catalogue entries; results are suggestions, never implicit selections."""
    return {"results": search_sdg_careers(q)}


@router.post("/api/sdg/mindmap")
def create_sdg_mindmap(request: MindmapRequest):
    career_id = request.career_id.strip()
    career = get_sdg_careers().get(career_id)
    if career is None:
        raise HTTPException(status_code=404, detail="Select a supported career from the catalogue.")
    # The mindmap actively requests task-derived scores for all 17 goals.
    # Legacy assessments/audit exports retain the older optional API fields.
    return get_sdg_alignment_by_id(career_id, include_goal_scores=True)
