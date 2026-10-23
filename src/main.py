
from pathlib import Path
from functools import lru_cache
import math
import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from assessment_scoring import calculate_assessment
from career_engine import load_careers, match_careers
from reskilling.sdg_alignment import (
    get_sdg_alignment,
    get_sdg_alignment_by_id,
)


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


CAREER_WORKSPACE_ROUTES = (
    "/career-overview",
    "/careers",
    "/my-profile",
    "/compare",
)
CAREER_ID_PATTERN = re.compile(r"^\d{2}-\d{4}\.\d{2}$")


def career_workspace_page():
    return FileResponse(BASE_DIR / "static" / "career-workspace.html")


for _route in CAREER_WORKSPACE_ROUTES:
    app.add_api_route(
        _route,
        career_workspace_page,
        methods=["GET"],
        include_in_schema=False,
    )


@app.get("/career/{career_id}", include_in_schema=False)
def career_detail_page(career_id: str):
    return career_workspace_page()


def _career_catalog_item(row):
    raw_id = row.get("O*NET-SOC Code")
    career_id = "" if raw_id is None else str(raw_id).strip()
    raw_top3 = row.get("RIASEC_Top3")
    scores = {}
    for dimension in ("R", "I", "A", "S", "E", "C"):
        try:
            value = float(row[dimension])
        except (TypeError, ValueError, KeyError):
            value = None
        scores[dimension] = value if value is not None and math.isfinite(value) else None
    return {
        "id": career_id,
        "title": str(row["Title"]).strip(),
        "riasec": scores,
        "riasec_top3": "" if raw_top3 is None else str(raw_top3).strip(),
    }


@app.get("/api/careers")
def career_catalog(
    q: str = Query(default="", max_length=100),
    limit: int = Query(default=24, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    """Search/browse canonical occupation records without making a selection."""
    careers = get_careers()
    records = [
        _career_catalog_item(row)
        for _, row in careers.iterrows()
        if CAREER_ID_PATTERN.fullmatch(
            "" if row.get("O*NET-SOC Code") is None else str(row.get("O*NET-SOC Code")).strip()
        )
    ]
    query = q.strip().casefold()
    if query:
        records = [item for item in records if query in item["title"].casefold()]
    records.sort(key=lambda item: item["title"].casefold())
    return {
        "results": records[offset:offset + limit],
        "total": len(records),
        "limit": limit,
        "offset": offset,
        "search_basis": "canonical occupation title",
    }


@app.get("/api/careers/{career_id}")
def career_detail(career_id: str):
    """Return only validated catalogue facts and explicit evidence availability."""
    if not CAREER_ID_PATTERN.fullmatch(career_id):
        raise HTTPException(status_code=404, detail="Career not found in the catalogue.")
    careers = get_careers()
    matching = careers.loc[
        careers["O*NET-SOC Code"].astype(str).str.strip() == career_id
    ]
    if matching.empty:
        raise HTTPException(status_code=404, detail="Career not found in the catalogue.")
    row = matching.iloc[0]
    item = _career_catalog_item(row)
    alignment = get_sdg_alignment_by_id(career_id)
    return {
        **item,
        "profile_url": f"https://www.onetonline.org/link/summary/{career_id}",
        "profile_source": "O*NET OnLine occupation profile",
        "pathway": {
            "available": bool(alignment.get("pathway_career")),
            "template": alignment.get("pathway_career"),
            "status": "illustrative_template" if alignment.get("pathway_career") else "not_available",
        },
        "sdg_status": alignment.get("status", "unknown"),
    }


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
            sdg_alignment = get_sdg_alignment(str(career["Title"]))

            career_results.append({
                "id": str(career.get("O*NET-SOC Code", "")).strip(),

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

                "pathway_career": sdg_alignment.get("pathway_career"),
                "pathway_status": (
                    "illustrative_template"
                    if sdg_alignment.get("pathway_career")
                    else "not_available"
                ),
                "sdg_alignment": sdg_alignment,
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
