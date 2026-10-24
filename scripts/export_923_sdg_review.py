"""Export one auditable SDG evaluation row for every career in the 923-row CSV.

Windows PowerShell, from repository root:
  $env:PYTHONPATH="src"
  python scripts/export_923_sdg_review.py

No false guarantee of accuracy: recorded suggestions remain candidates for
expert review, and NO impact percentage or success claim is fabricated.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from reskilling.sdg_alignment import get_sdg_alignment_by_id
from reskilling.sdg_task_evidence import source_status

SOURCE = ROOT / "src" / "career_profiles_clean.csv"
DEST = ROOT / "reports" / "sdg_mapping_923_review.csv"
COLUMNS = [
    "onet_soc", "occupation", "onet_task_data_status",
    "onet_task_count", "core_task_count", "sample_task_ids",
    "task_based_goals", "task_based_targets", "task_based_ids",
    "task_topic_goals", "task_topic_ids",
    "dwa_topic_goals", "dwa_topic_task_ids",
    "classification_only_goals", "all_candidate_goals",
    "rating_data_available", "dwa_data_available",
    "sample_task_importance", "sample_task_dwa_ids",
    "review_status", "sdg_evidence_disclaimer",
]


def csv_ids(items):
    return "; ".join(str(x) for x in items)


def unique_goal_ids(items):
    return csv_ids(sorted({int(x["sdg_id"]) for x in items}))


def main():
    status = source_status()
    if status != "available":
        raise SystemExit(
            "Official O*NET Task Statements CSV missing or invalid. "
            "Run: python scripts/import_onet_sdg_tasks.py"
        )
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        occupations = list(csv.DictReader(stream))
    if len(occupations) != 923:
        raise SystemExit(f"Unexpected occupation count: {len(occupations)}; expected 923.")
    output = []
    classified = {
        "task_supported": 0, "task_topic_only": 0,
        "dwa_topic_only": 0, "classification_only": 0,
        "no_sdg_suggestion": 0
    }
    for role in occupations:
        code = role["O*NET-SOC Code"]
        data = get_sdg_alignment_by_id(code)
        if data["status"] == "unknown":
            raise SystemExit(f"Missing registered O*NET occupation: {code}")
        strict = data["mappings"]
        candidates = data["candidate_mappings"]
        profile = data["task_profile"] or {}
        topics = [x for x in candidates if x.get("candidate_tier") == "task_topic"]
        dwa_topics = [x for x in candidates if x.get("candidate_tier") == "dwa_topic"]
        fallback = [x for x in candidates
                    if x.get("candidate_tier") == "classification_only"]
        # No specific SDG suggestion is an honest possible outcome.
        # The task_profile still provides an independently auditable
        # occupational analysis; never fabricate a Goal 8 fallback.
        tier = (
            "task_supported" if strict else
            "task_topic_only" if topics else
            "dwa_topic_only" if dwa_topics else
            "classification_only" if fallback else "no_sdg_suggestion"
        )
        classified[tier] += 1
        strict_tasks = [
            task["task_id"] for m in strict for task in m.get("task_evidence", [])
        ]
        topic_tasks = [
            task["task_id"] for m in topics for task in m.get("task_evidence", [])
        ]
        dwa_task_ids = [
            task["task_id"] for m in dwa_topics for task in m.get("task_evidence", [])
        ]
        sample = profile.get("representative_tasks", [])
        output.append({
            "onet_soc": code,
            "occupation": role["Title"],
            "onet_task_data_status": data["task_data_status"],
            "onet_task_count": profile.get("occupation_task_count", 0),
            "core_task_count": profile.get("core_task_count", 0),
            "sample_task_ids": csv_ids(
                task["task_id"] for task in profile.get("representative_tasks", [])
            ),
            "task_based_goals": unique_goal_ids(strict),
            "task_based_targets": csv_ids(sorted({m["target_id"] for m in strict})),
            "task_based_ids": csv_ids(sorted(set(strict_tasks))),
            "task_topic_goals": unique_goal_ids(topics),
            "task_topic_ids": csv_ids(sorted(set(topic_tasks))),
            "dwa_topic_goals": unique_goal_ids(dwa_topics),
            "dwa_topic_task_ids": csv_ids(sorted(set(dwa_task_ids))),
            "classification_only_goals": unique_goal_ids(fallback),
            "rating_data_available": (profile.get("supporting_data_available") or {}).get("task_ratings", False),
            "dwa_data_available": (profile.get("supporting_data_available") or {}).get("tasks_to_dwas", False),
            "sample_task_importance": csv_ids(
                str(task.get("task_ratings", {}).get("importance_1_to_5", ""))
                for task in sample
            ),
            "sample_task_dwa_ids": csv_ids(sorted({
                item.get("id", "")
                for task in sample for item in task.get("dwa_activities", [])
                if item.get("id")
            })),
            "all_candidate_goals": unique_goal_ids(strict + candidates),
            "review_status": tier,
            "sdg_evidence_disclaimer": (
                "All SDG mappings are preliminary research hypotheses, "
                "not independently reviewed or demonstrated SDG impacts."
            ),
        })
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(output)
    print(f"Exported {len(output)} O*NET career-specific analyses: {DEST}")
    print("Evidence tiers:")
    for key, number in classified.items():
        print(f"  {key}: {number}")
    print("CAUTION: 923/923 coverage means analysis availability, NOT mapping accuracy.")


if __name__ == "__main__":
    main()
