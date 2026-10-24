"""Audit coverage of real O*NET 31.0 tasks and conservative SDG candidates.

Run after downloading official CSV:
  $env:PYTHONPATH="src"
  python scripts/audit_sdg_task_evidence.py
"""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from reskilling.sdg_task_evidence import source_status, task_supported_mappings
from reskilling.sdg_candidate_ranker import (
    candidate_mappings_for_occupation, occupation_task_profile,
)
from reskilling.sdg_onet_context import sources_available

OCCUPATIONS = ROOT / "src" / "career_profiles_clean.csv"


def main():
    status = source_status()
    print("O*NET 31.0 Task Statements source status:", status)
    if status != "available":
        raise SystemExit(
            "No verified O*NET Task Statements CSV was found. Run "
            "'python scripts/import_onet_sdg_tasks.py' first. "
            "Title/SOC guesses are NOT task-backed data."
        )
    occupations = list(csv.DictReader(OCCUPATIONS.open(encoding="utf-8-sig", newline="")))
    counts = Counter()
    supported = 0
    task_topic_count = 0
    dwa_topic_count = 0
    weak_only_count = 0
    missing_task_profiles = 0
    print("Examples of task-derived candidates (not measured SDG impact):")
    for career in occupations:
        code, title = career["O*NET-SOC Code"], career["Title"]
        matches, task_status = task_supported_mappings(code, title)
        candidates = candidate_mappings_for_occupation(code, title, {x["sdg_id"] for x in matches})
        profile = occupation_task_profile(code)
        if not profile["occupation_task_count"]:
            missing_task_profiles += 1
        if not matches:
            tiers = {x["candidate_tier"] for x in candidates}
            if "task_topic" in tiers:
                task_topic_count += 1
            elif "dwa_topic" in tiers:
                dwa_topic_count += 1
            else:
                weak_only_count += 1
        if matches:
            supported += 1
            counts.update(str(m["target_id"]) for m in matches)
            if title in ("Chefs and Head Cooks", "Software Developers",
                         "Registered Nurses", "Environmental Engineers"):
                print(f" {code} {title}: " + ", ".join(
                    f"Target {m['target_id']} via Task ID {m['task_evidence'][0]['task_id']}"
                    for m in matches))
        elif title in ("Chefs and Head Cooks", "Software Developers"):
            print(f" {code} {title}: no explicit task rule match (not automatically SDG mapped)")
    print(f"Catalogue occupational records: {len(occupations)}")
    print(f"Occupations with at least one O*NET task-rule candidate: {supported}")
    print(f"Occupations with no strict task-target match: {len(occupations)-supported}")
    print(f"Additional occupations with task-text topic suggestions: {task_topic_count}")
    print(f"Additional occupations with DWA-topic-only suggestions: {dwa_topic_count}")
    print(f"Occupations with classification-only (weakest) suggestions: {weak_only_count}")
    print(f"Occupations with no O*NET Task Statements: {missing_task_profiles}")
    print(f"Total occupations with some analysis: {supported + task_topic_count + dwa_topic_count + weak_only_count}")
    print("Supporting O*NET datasets installed:", sources_available())
    print("Classification-only is NOT SDG evidence; each suggestion still needs expert review.")
    print("By proposed UN target (counts of occupational candidates):")
    for target, count in sorted(counts.items()):
        print(f"  {target}: {count}")
    print("WARNING: Task matches describe duties only; they do not measure SDG impact.")


if __name__ == "__main__":
    main()
