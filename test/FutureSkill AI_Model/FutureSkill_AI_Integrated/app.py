
from pathlib import Path
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from assessment_scoring import calculate_assessment
from career_engine import load_careers, match_careers


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

    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )

# ======================================
# INDEPENDENT FEATURE PAGES
# ======================================

@app.get("/ai-trend", include_in_schema=False)
def ai_trend_page():
    return FileResponse(
        BASE_DIR / "static" / "ai-trend.html"
    )


@app.get("/sdg-impact", include_in_schema=False)
def sdg_impact_page():
    return FileResponse(
        BASE_DIR / "static" / "sdg-impact.html"
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
                )
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
from reskilling.api import router as reskilling_router, session_cookie_middleware

app.mount("/reskill-static", StaticFiles(directory=BASE_DIR / "reskilling" / "static"), name="reskill-static")
app.middleware("http")(session_cookie_middleware)
app.include_router(reskilling_router)

# ======================================
# CONNECT UNCERTAINTY LAB
# ======================================

from uncertainty.api import router as uncertainty_router

app.include_router(uncertainty_router)


# ==========================================
# SDG IMPACT MAP API
# ==========================================

from sdg_mapping import build_mindmap


class MindmapRequest(BaseModel):
    title: str
    skills: dict[str, int] | None = None


@app.post("/api/sdg/mindmap")
def create_sdg_mindmap(request: MindmapRequest):

    try:
        return build_mindmap(
            request.title,
            request.skills or {}
        )

    except (ValueError, TypeError, KeyError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error


# ==========================================
# AI TREND DATA API
# ==========================================

@app.get("/api/ai-trends")
def get_ai_trends():

    import json
    import csv

    folder = BASE_DIR.parent / "AI-development-trend"

    report_path = folder / "ai_trend_report.json"
    table_path = folder / "ai_trend_table.csv"

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="AI trend report not found"
        )

    with open(report_path, encoding="utf-8-sig") as file:
        report = json.load(file)

    columns = []
    rows = []

    if table_path.exists():

        with open(
            table_path,
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)
            columns = reader.fieldnames or []
            rows = list(reader)

    return {
        "report": report,
        "columns": columns,
        "rows": rows
    }
