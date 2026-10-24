
# ==========================================
# FUTURESKILL AI - UNCERTAINTY LAB API
# FastAPI Integration
# ==========================================

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .uncertainty_engine import (
    SCENARIOS,
    Scenario,
    employment_forecast,
    occupational_growth
)

# ==========================================
# 1. CREATE ROUTER
# ==========================================

router = APIRouter(
    tags=["Uncertainty Lab"]
)

BASE_DIR = Path(__file__).resolve().parent


# ==========================================
# 2. USER INPUT FORMAT
# ==========================================

class SimulationRequest(BaseModel):

    ai_growth: float = Field(ge=0, le=100)

    automation: float = Field(ge=0, le=100)

    adaptation: float = Field(ge=0, le=100)

    economy: float = Field(ge=0, le=100)

    alignment: float = Field(ge=0, le=100)

    other_factors: float = Field(ge=0, le=100)

    base_rate: float = Field(
        default=68.9,
        ge=0,
        le=100
    )


# ==========================================
# 3. DISPLAY UNCERTAINTY WEBPAGE
# ==========================================

@router.get("/uncertainty", include_in_schema=False)
def uncertainty_home():

    page = BASE_DIR / "uncertainty.html"

    if not page.is_file():

        raise HTTPException(
            status_code=404,
            detail="Uncertainty webpage not found"
        )

    return FileResponse(page)


# ==========================================
# 4. PREDEFINED SCENARIOS API
# ==========================================

@router.get("/api/scenarios")
def get_scenarios():

    results = {}

    for key, scenario in SCENARIOS.items():

        results[key] = {

            "name": scenario.name,

            "employment_rate":
                employment_forecast(scenario),

            "occupational_growth":
                occupational_growth(scenario)

        }

    return results


# ==========================================
# 5. CUSTOM SIMULATION API
# ==========================================

@router.post("/api/simulate")
def simulate(request: SimulationRequest):

    scenario = Scenario(

        name="Custom",

        ai_growth=request.ai_growth,

        automation=request.automation,

        adaptation=request.adaptation,

        economy=request.economy,

        alignment=request.alignment,

        other_factors=request.other_factors
    )

    employment = employment_forecast(
        scenario,
        request.base_rate
    )

    jobs = occupational_growth(
        scenario
    )

    return {

        "employment_rate": employment,

        "occupational_growth": jobs
    }
