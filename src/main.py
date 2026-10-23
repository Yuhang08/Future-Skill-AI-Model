
from pathlib import Path
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from assessment_scoring import calculate_assessment
from career_engine import load_careers, match_careers
from reskilling.sdg_alignment import get_sdg_alignment


# ======================================
# 1. CREATE WEBSITE SERVER
# ======================================

app = FastAPI(
    title="FutureSkill AI"
)

BASE_DIR = Path(__file__).resolve().parent


# ======================================
# 2. LOAD CAREER DATABASE
# ======================================

@lru_cache(maxsize=1)
def get_careers():

    return load_careers(
        BASE_DIR / "career_profiles_clean.csv"
    )


# ======================================
# 3. QUESTIONNAIRE INPUT FORMAT
# ======================================

class AssessmentRequest(BaseModel):

    answers: dict[str, list[int]]

    subject_answers: dict[str, list[int]]

    skill_answers: dict[str, int]


# ======================================
# 4. SUBJECT LABEL CONVERSION
# ======================================

SUBJECT_MAPPING = {
    "IT": "it",
    "Math": "math",
    "Education": "education",
    "Health": "health",
    "Business": "business",
    "Engineering": "engineering"
}


# ======================================
# 5. DISPLAY WEBSITE
# ======================================

@app.get("/")
def home():
    page = BASE_DIR / "static" / "index.html"
    if not DEV_INVENTORY_ENABLED:
        return FileResponse(page)
    html = page.read_text(encoding="utf-8").replace(
        "</header>",
        '<a href="/__dev/screens" style="display:block;text-align:center;padding:9px;background:#e8f4ee;color:#17483c;font:700 13px Arial,sans-serif">Development only · Open screen inventory</a></header>',
        1,
    )
    return HTMLResponse(html)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(
        BASE_DIR / "static" / "favicon.svg",
        media_type="image/svg+xml",
    )


# ======================================
# 6. CAREER RECOMMENDATION API
# ======================================

@app.post("/api/recommend")
def recommend(request: AssessmentRequest):

    try:

        # A. Calculate questionnaire scores
        assessment = calculate_assessment(
            riasec_answers=request.answers,
            subject_answers=request.subject_answers,
            skill_answers=request.skill_answers
        )

        # B. Get user RIASEC
        riasec_scores = assessment[
            "riasec_scores"
        ]

        # C. Convert subject preferences
        subject_preferences = {
            SUBJECT_MAPPING[k]: v
            for k, v in assessment[
                "subject_preferences"
            ].items()
        }

        # D. Call career matching engine
        careers = get_careers()

        recommendations = match_careers(
            df=careers,
            user_scores=riasec_scores,
            subject_preferences=subject_preferences,
            top_n=10
        )

        # E. Prepare career recommendations
        career_results = []

        for _, career in recommendations.iterrows():

            career_results.append({
                "title": str(career["Title"]),

                "riasec": str(
                    career["Career_Top3"]
                ),

                "match_index": float(
                    career["Match_Index"]
                ),

                "interest_index": float(
                    career["Interest_Index"]
                ),

                "subject_index": float(
                    career["Subject_Index"]
                ),

                "fields": str(
                    career["Fields"]
                ),

                "explanation": str(
                    career["Explanation"]
                ),

                "sdg_alignment": get_sdg_alignment(
                    str(career["Title"])
                ),
            })

        # F. Return results to website
        return {
            "top3": assessment["riasec_top3"],

            "riasec_scores": riasec_scores,

            "subject_preferences": assessment[
                "subject_preferences"
            ],

            "skills": assessment["skills"],

            "recommendations": career_results
        }

    except (ValueError, KeyError, TypeError) as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error


# One FastAPI application hosts both the original assessment and the reskilling studio.
from fastapi.staticfiles import StaticFiles
from reskilling.api import (
    DEV_INVENTORY_ENABLED,
    router as reskilling_router,
    session_cookie_middleware,
)
from reskilling.extra_features import router as exploration_router
from reskilling.explanation_api import router as explanation_router

app.mount("/reskill-static", StaticFiles(directory=BASE_DIR / "reskilling" / "static"), name="reskill-static")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.middleware("http")(session_cookie_middleware)
app.include_router(reskilling_router)
app.include_router(exploration_router)
app.include_router(explanation_router)
