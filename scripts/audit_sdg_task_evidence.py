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
    print("Examples of task-derived candidates (not measured SDG impact):")
    for career in occupations:
        code, title = career["O*NET-SOC Code"], career["Title"]
        matches, task_status = task_supported_mappings(code, title)
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
    print(f"Occupations with no task-rule match: {len(occupations)-supported}")
    print("By proposed UN target (counts of occupational candidates):")
    for target, count in sorted(counts.items()):
        print(f"  {target}: {count}")
    print("WARNING: Task matches describe duties only; they do not measure SDG impact.")


if __name__ == "__main__":
    main()
