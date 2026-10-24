"""Download genuine O*NET 31.0 Task Statements for the SDG evidence engine.

Run from the repository root:
  python scripts/import_onet_sdg_tasks.py

The official raw CSV (~18,838 task statements) is retained verbatim under
src/data/onet_task_statements.csv. The O*NET database is licensed CC BY 4.0.
This utility NEVER substitutes made-up data if the download fails.
"""
import csv
import io
import sys
import urllib.request
from pathlib import Path

URL = "https://www.onetcenter.org/dl_files/database/db_31_0_csv/task_statements.csv"
EXPECTED_COLUMNS = {"O*NET-SOC Code", "Title", "Task ID", "Task", "Task Type", "Date"}
DEST = Path(__file__).resolve().parent.parent / "src" / "data" / "onet_task_statements.csv"


def main():
    print("Official source:", URL)
    print("O*NET 31.0 (USDOL/ETA), CC BY 4.0")
    try:
        request = urllib.request.Request(URL, headers={"User-Agent": "FutureSkillAI-Research/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read(15 * 1024 * 1024 + 1)
    except Exception as exc:
        sys.exit(
            f"Could not fetch official O*NET source: {exc}\n"
            "Download task_statements.csv from "
            "https://www.onetcenter.org/dictionary/31.0/csv/task_statements.html "
            f"and put it at {DEST}"
        )
    if len(raw) > 15 * 1024 * 1024:
        sys.exit("Unexpectedly large O*NET file; refusing to save.")
    try:
        data = raw.decode("utf-8-sig")
        rows = csv.DictReader(io.StringIO(data))
        if not EXPECTED_COLUMNS.issubset(rows.fieldnames or []):
            sys.exit(f"Unexpected CSV headers: {rows.fieldnames!r}")
        count = 0
        for row in rows:
            if not row["Task ID"].strip().isdigit() or not row["Task"].strip():
                sys.exit("Invalid task row encountered; refusing to save.")
            count += 1
        if count < 15000:
            sys.exit(f"File has only {count} tasks; expected >=15,000 for version 31.0.")
    except UnicodeError as exc:
        sys.exit(f"Not a valid UTF-8 O*NET CSV: {exc}")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_bytes(raw)
    print(f"Saved {count:,} official task statements to {DEST}")
    print("To include this evidence in a Render deployment, commit this CSV to Git.")
    print("Source attribution: O*NET 31.0 (USDOL/ETA), CC BY 4.0.")
    print("FutureSkill's rule mappings are not endorsed by USDOL/ETA or the UN.")


if __name__ == "__main__":
    main()
