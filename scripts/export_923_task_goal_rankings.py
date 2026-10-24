"""Export 923 occupations × 17 ranked SDG relevance scores (NOT impact).

Windows PowerShell from repository root:
  $env:PYTHONPATH="src"
  python scripts/export_923_task_goal_rankings.py

Requires the user's ORIGINAL O*NET 31.0 Task Statements CSV. The file is
never replaced or modified. No task/SDG evidence is fabricated.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from reskilling.sdg_task_evidence import source_status
from reskilling.sdg_task_goal_model import score_career_goals

SOURCE = ROOT / "src" / "career_profiles_clean.csv"
OUTPUT = ROOT / "reports" / "sdg_task_goal_rankings_923.csv"
FIELDS = [
    "onet_soc", "occupation", "goal", "sdg_name", "rank",
    "relevance_index_0_to_100", "evidence_basis", "related_task_count",
    "task_count", "task_ids", "task_sentences",
    "matched_phrases", "dwa_matched_phrases",
    "review_status", "model_version", "limitations",
]


def main():
    if source_status() != "available":
        raise SystemExit(
            "Official O*NET Task Statements CSV not available. "
            "Run python scripts/import_onet_sdg_tasks.py first."
        )
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        occupations = list(csv.DictReader(stream))
    if len(occupations) != 923:
        raise SystemExit(
            f"Occupation catalogue contains {len(occupations)} records; expected 923."
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    weak = 0
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for role in occupations:
            code = role["O*NET-SOC Code"]
            title = role["Title"]
            result = score_career_goals(code)
            goals = result["goal_scores"]
            if result["status"] != "available" or len(goals) != 17:
                raise SystemExit(
                    f"Missing official per-task evidence for {code} ({title}). "
                    "Do not fabricate SDG scores."
                )
            for item in goals:
                evidence = item["task_evidence"]
                if not evidence or any(not t.get("task_id") for t in evidence):
                    raise SystemExit(f"No original O*NET Task IDs for {code} goal {item['sdg_id']}")
                if item["review_status"] == "weak_exploratory_ranking":
                    weak += 1
                writer.writerow({
                    "onet_soc": code,
                    "occupation": title,
                    "goal": item["sdg_id"],
                    "sdg_name": item["sdg_name"],
                    "rank": item["rank"],
                    "relevance_index_0_to_100": item["relevance_index"],
                    "evidence_basis": item["evidence_basis"],
                    "related_task_count": item["related_task_count"],
                    "task_count": item["task_count"],
                    "task_ids": "; ".join(t["task_id"] for t in evidence),
                    "task_sentences": json.dumps(
                        [t["task"] for t in evidence], ensure_ascii=False
                    ),
                    "matched_phrases": "; ".join(
                        sorted({x for t in evidence for x in t["phrase_matches"]})
                    ),
                    "dwa_matched_phrases": "; ".join(
                        sorted({x for t in evidence for x in t["dwa_phrase_matches"]})
                    ),
                    "review_status": item["review_status"],
                    "model_version": result["model"],
                    "limitations": (
                        "Relative task-text similarity only, not certified "
                        "occupation-to-SDG alignment or verified SDG impact."
                    ),
                })
                count += 1
    assert count == 923 * 17, "Unexpected career-goal pair count"
    print(f"Exported {count:,} occupation×Goal rows ({len(occupations)} occupations × 17 goals).")
    print(f"CSV: {OUTPUT}")
    print(f"Rows with weak or no distinctive topic evidence: {weak:,}")
    print("Important: Scores are relative model indices, NOT probability or SDG impact.")


if __name__ == "__main__":
    main()
