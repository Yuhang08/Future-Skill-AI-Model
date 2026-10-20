
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CAREER_FILE = BASE_DIR / "career_profiles_clean.csv"

careers_df = pd.read_csv(CAREER_FILE)

print("Career dataset loaded!")
print("Number of careers:", len(careers_df))


import math

# Six RIASEC dimensions
RIASEC = ["R", "I", "A", "S", "E", "C"]


def get_top_three(scores):
    """Return the user's or career's top three RIASEC types."""
    return sorted(
        RIASEC,
        key=lambda dimension: scores[dimension],
        reverse=True
    )[:3]


def recommend_careers(user_scores, careers_df, top_n=10):
    results = []

    # Identify the user's strongest three interest types
    user_types = get_top_three(user_scores)

    for _, career in careers_df.iterrows():

        # Get the six interest scores for this career
        career_scores = {
            dimension: float(career[dimension])
            for dimension in RIASEC
        }

        career_types = get_top_three(career_scores)

        # Rule 1: Keep careers sharing at least two top-three types
        shared_types = set(user_types) & set(career_types)

        if len(shared_types) < 2:
            continue

        # Rule 2: Calculate Euclidean distance
        distance = math.sqrt(
            sum(
                (user_scores[d] - career_scores[d]) ** 2
                for d in RIASEC
            )
        )

        results.append({
            "Title": career["Title"],
            "Career_Top3": "".join(career_types),
            "Shared_Types": "".join(
                d for d in RIASEC if d in shared_types
            ),
            "Distance": distance
        })

    # Smaller distance = more similar profiles
    results.sort(key=lambda item: item["Distance"])

    return user_types, results[:top_n]


# ==========================================
# TEST USER — replace with questionnaire data later
# ==========================================

user_scores_original = {
    "R": 50,
    "I": 100,
    "A": 30,
    "S": 80,
    "E": 80,
    "C": 60
}

# Temporary scale conversion:
# Map the user's 20–100 scale to the O*NET 0–7 range.
# This is a prototype assumption, not a validated equivalence.
user_scores = {
    d: (user_scores_original[d] - 20) / 80 * 7
    for d in RIASEC
}

user_types, recommendations = recommend_careers(
    user_scores,
    careers_df,
    top_n=10
)

print("\nUser's RIASEC Top 3:", "".join(user_types))
print("\nRecommended careers:")

if recommendations:
    for rank, item in enumerate(recommendations, start=1):
        print(f"\n{rank}. {item['Title']}")
        print("Career types:", item["Career_Top3"])
        print("Shared types:", item["Shared_Types"])
        print(f"Distance: {item['Distance']:.3f}")
else:
    print("No careers passed the filtering rule.")
    print("Consider reviewing the threshold.")

















































































