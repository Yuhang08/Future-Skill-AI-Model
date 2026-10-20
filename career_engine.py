
from pathlib import Path
import re
import numpy as np
import pandas as pd

RIASEC = ("R", "I", "A", "S", "E", "C")

FIELDS = (
    "it", "math", "education", "health",
    "business", "creative", "engineering",
    "science", "public_service"
)

FIELD_LABELS = {
    "it": "IT / Computing",
    "math": "Mathematics / Statistics",
    "education": "Education",
    "health": "Healthcare",
    "business": "Business",
    "creative": "Creative Arts",
    "engineering": "Engineering",
    "science": "Natural Sciences",
    "public_service": "Public Service"
}

# Starter taxonomy from career titles.
# This is NOT official O*NET Knowledge data.
FIELD_PATTERNS = {
    "it": [
        r"\bsoftware\b", r"\bcomputer\b",
        r"\bdata\b", r"\bcyber",
        r"\binformation technology\b",
        r"\bweb\b", r"\bdatabase\b",
        r"\bnetwork\b", r"\bprogrammer",
        r"\bmachine learning\b",
        r"\binformatics\b"
    ],
    "math": [
        r"\bmathematic", r"\bstatistic",
        r"\bactuar", r"\boperations research\b",
        r"\bdata scientist", r"\bquantitative\b"
    ],
    "education": [
        r"\bteacher", r"\bprofessor",
        r"\btutor", r"\binstructor",
        r"\beducation", r"\bschool counselor",
        r"\blecturer"
    ],
    "health": [
        r"\bmedical", r"\bhealth",
        r"\bnurs", r"\bphysician",
        r"\bpatient", r"\bgenetic counselor",
        r"\btherap", r"\bdent",
        r"\bpharmac", r"\bsurgeon",
        r"\bclinical", r"\bepidemiolog"
    ],
    "business": [
        r"\bmanager", r"\bmarket",
        r"\bbusiness", r"\bsales",
        r"\bexecutive", r"\bentrepreneur",
        r"\bfinance", r"\baccountant",
        r"\badvertis"
    ],
    "creative": [
        r"\bartist", r"\bdesign",
        r"\bwriter", r"\bmusic",
        r"\bactor", r"\bfilm",
        r"\banimat", r"\bphotograph"
    ],
    "engineering": [
        r"\bengineer", r"\barchitect",
        r"\brobot", r"\bmechanic",
        r"\belectric", r"\bcivil engineering"
    ],
    "science": [
        r"\bscientist", r"\bchemist",
        r"\bphysic", r"\bbiolog",
        r"\bresearch", r"\bastronom",
        r"\bgeolog"
    ],
    "public_service": [
        r"\bpublic", r"\bgovernment",
        r"\bsocial worker", r"\bpolicy",
        r"\bcommunity", r"\bpolice",
        r"\bfirefighter"
    ]
}

COMPILED = {
    key: [re.compile(p, re.I) for p in patterns]
    for key, patterns in FIELD_PATTERNS.items()
}


# ==========================================
# 1. LOAD CAREER DATASET
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

def load_careers(path=None):

    if path is None:
        path = BASE_DIR / "career_profiles_clean.csv"

    if not Path(path).is_file():
        raise FileNotFoundError(
            f"Career dataset not found: {path}"
        )

    df = pd.read_csv(
        path,
        dtype={"O*NET-SOC Code": "string"}
    )

    required = {"Title", *RIASEC}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {sorted(missing)}"
        )

    for dimension in RIASEC:
        df[dimension] = pd.to_numeric(
            df[dimension],
            errors="coerce"
        )

    df = df.dropna(
        subset=["Title", *RIASEC]
    ).copy()

    valid = (
        df[list(RIASEC)].ge(1).all(axis=1)
        & df[list(RIASEC)].le(7).all(axis=1)
    )

    df = df[valid].copy()

    if "O*NET-SOC Code" in df.columns:
        df = df.drop_duplicates(
            subset="O*NET-SOC Code"
        )

    if df.empty:
        raise ValueError("No valid career data")

    return df.reset_index(drop=True)


# ==========================================
# 2. VALIDATE USER SCORES
# ==========================================

def validate_user_scores(scores):

    if set(scores) != set(RIASEC):
        raise ValueError(
            "Scores must contain R, I, A, S, E, C"
        )

    values = np.array(
        [scores[d] for d in RIASEC],
        dtype=float
    )

    if not np.isfinite(values).all():
        raise ValueError("Invalid RIASEC scores")

    if np.any(values < 20) or np.any(values > 100):
        raise ValueError(
            "RIASEC scores must be between 20 and 100"
        )

    return values


# ==========================================
# 3. CAREER FIELD CLASSIFICATION
# ==========================================

def field_tags(title):

    return {
        field: int(
            any(
                pattern.search(str(title))
                for pattern in patterns
            )
        )
        for field, patterns in COMPILED.items()
    }


# ==========================================
# 4. CAREER MATCHING ALGORITHM
# ==========================================

def match_careers(
    df,
    user_scores,
    subject_preferences=None,
    top_n=10,
    subject_weight=0.35
):

    if not 0 <= subject_weight <= 1:
        raise ValueError(
            "subject_weight must be between 0 and 1"
        )

    if top_n < 1:
        raise ValueError("top_n must be positive")

    # User vector
    u = validate_user_scores(user_scores)

    # Career matrix
    c = df[list(RIASEC)].to_numpy(
        dtype=float
    )

    # ======================================
    # MODEL A: PEARSON CORRELATION
    # ======================================

    user_centered = u - u.mean()

    career_centered = (
        c - c.mean(axis=1, keepdims=True)
    )

    numerator = career_centered @ user_centered

    denominator = (
        np.linalg.norm(career_centered, axis=1)
        * np.linalg.norm(user_centered)
    )

    pearson = np.divide(
        numerator,
        denominator,
        out=np.zeros(len(c)),
        where=denominator > 1e-9
    )

    pearson = np.clip(pearson, -1, 1)

    # Convert [-1,1] into [0,1]
    shape_score = (pearson + 1) / 2

    # ======================================
    # MODEL B: SOFT RANK SIMILARITY
    # ======================================

    # Positive deviations represent
    # relatively strong interest dimensions.

    user_positive = np.maximum(
        user_centered, 0
    )

    career_positive = np.maximum(
        career_centered, 0
    )

    if user_positive.sum() > 1e-9:

        user_weights = (
            user_positive
            / user_positive.sum()
        )

        relative_score = (
            career_positive @ user_weights
        ) / np.maximum(
            career_positive.max(axis=1),
            1e-9
        )

        relative_score = np.clip(
            relative_score, 0, 1
        )

    else:
        relative_score = np.full(
            len(c), 0.5
        )

    # ======================================
    # MODEL C: COMBINED RIASEC
    # ======================================

    interest_score = (
        0.85 * shape_score
        + 0.15 * relative_score
    )

    # Neutral fallback for a flat user profile
    if np.linalg.norm(user_centered) < 1e-9:
        interest_score = np.full(
            len(c), 0.5
        )

    # ======================================
    # MODEL D: SUBJECT MATCHING
    # ======================================

    preferences = {}

    if subject_preferences is not None:

        if not set(subject_preferences).issubset(FIELDS):
            raise ValueError(
                "Unknown subject preference"
            )

        preferences = {
            k: float(v)
            for k, v in subject_preferences.items()
        }

        if any(
            not np.isfinite(v) or not 1 <= v <= 5
            for v in preferences.values()
        ):
            raise ValueError(
                "Subject preferences must be 1-5"
            )

    tags = [
        field_tags(title)
        for title in df["Title"]
    ]

    # Unknown career field = neutral estimate
    subject_score = np.full(
        len(c), 0.5
    )

    if preferences:

        for i, tag in enumerate(tags):

            active_fields = [
                k for k in preferences
                if tag[k] == 1
            ]

            if active_fields:

                values = [
                    (preferences[k] - 1) / 4
                    for k in active_fields
                ]

                subject_score[i] = np.mean(
                    values
                )

        final_score = (
            (1 - subject_weight) * interest_score
            + subject_weight * subject_score
        )

    else:
        final_score = interest_score

    # ======================================
    # 5. PREPARE RESULTS
    # ======================================

    results = df.copy()

    results["Interest_Index"] = np.round(
        interest_score * 100, 2
    )

    results["Subject_Index"] = (
        np.round(subject_score * 100, 2)
        if preferences else np.nan
    )

    results["Match_Index"] = np.round(
        final_score * 100, 2
    )

    results["Career_Top3"] = [
        "".join(
            RIASEC[j]
            for j in np.argsort(
                -row, kind="stable"
            )[:3]
        )
        for row in c
    ]

    results["Fields"] = [
        ", ".join(
            FIELD_LABELS[k]
            for k in FIELDS
            if tag[k]
        ) or "Unclassified"
        for tag in tags
    ]

    explanations = []

    for i, row in enumerate(c):

        career_top = np.argsort(
            -row, kind="stable"
        )[:3]

        shared = [
            RIASEC[j]
            for j in career_top
            if u[j] > u.mean()
        ]

        shared_text = (
            ", ".join(shared)
            if shared else "limited overlap"
        )

        explanation = (
            f"Shared interest strengths: {shared_text}. "
            f"Detected career fields: "
            f"{results.iloc[i]['Fields']}."
        )

        explanations.append(explanation)

    results["Explanation"] = explanations

    results = results.sort_values(
        ["Match_Index", "Interest_Index", "Title"],
        ascending=[False, False, True]
    )

    # ======================================
    # 6. RESULT DIVERSIFICATION
    # ======================================

    if preferences and top_n >= 5:

        selected = []
        counts = {}

        # Maximum approximate number of
        # careers per primary detected field
        limit = max(
            2, int(np.ceil(top_n * 0.3))
        )

        for index, row in results.iterrows():

            primary_field = row["Fields"].split(
                ", "
            )[0]

            if counts.get(primary_field, 0) < limit:

                selected.append(index)

                counts[primary_field] = (
                    counts.get(primary_field, 0) + 1
                )

                if len(selected) >= top_n:
                    break

        if len(selected) < top_n:

            remaining = [
                i for i in results.index
                if i not in selected
            ]

            selected.extend(
                remaining[:top_n - len(selected)]
            )

        return results.loc[
            selected
        ].reset_index(drop=True)

    return results.head(
        top_n
    ).reset_index(drop=True)


# ==========================================
# 7. LOCAL TEST
# ==========================================

if __name__ == "__main__":

    careers_df = load_careers()

    print("Career dataset loaded!")
    print("Number of careers:", len(careers_df))

    user_scores = {
        "R": 50,
        "I": 97.5,
        "A": 50,
        "S": 97.5,
        "E": 80,
        "C": 75
    }

    preferences = {
        "it": 4.5,
        "math": 5,
        "education": 4.5,
        "health": 2,
        "business": 2,
        "engineering": 4.5
    }

    recommendations = match_careers(
        careers_df,
        user_scores,
        preferences,
        top_n=10
    )

    print("\nRECOMMENDED CAREERS:")

    for rank, (_, career) in enumerate(
        recommendations.iterrows(), 1
    ):

        print(
            f"\n{rank}. {career['Title']}"
        )

        print(
            f"RIASEC: {career['Career_Top3']}"
        )

        print(
            f"Match Index: {career['Match_Index']:.2f}"
        )

        print(
            f"Fields: {career['Fields']}"
        )

        print(
            f"Reason: {career['Explanation']}"
        )
