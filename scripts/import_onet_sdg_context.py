"""Download original O*NET 31.0 supporting CSVs; do not synthesize data.

Run from repository root:
  python scripts/import_onet_sdg_context.py

These public source files supplement the already committed Task Statements.
They are not themselves evidence that an SDG outcome has occurred.
"""
import csv
import io
import sys
import urllib.request
from pathlib import Path

BASE = "https://www.onetcenter.org/dl_files/database/db_31_0_csv/"
DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "data"
FILES = {
    "tasks_to_dwas.csv": (
        {"O*NET-SOC Code", "Task ID", "DWA Element ID", "DWA Element Name"},
        20_000,
    ),
    "task_ratings.csv": (
        {"O*NET-SOC Code", "Task ID", "Scale ID", "Data Value",
         "Recommend Suppress"},
        150_000,
    ),
}


def validated_content(raw, name, required, min_rows):
    if len(raw) > 150 * 1024 * 1024:
        raise ValueError(f"{name}: unexpectedly large download")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError(
            f"{name}: unexpected columns; received {reader.fieldnames!r}"
        )
    rows = 0
    for row in reader:
        if not row["Task ID"].strip().isdigit():
            raise ValueError(f"{name}: invalid Task ID on row {rows + 2}")
        rows += 1
    if rows < min_rows:
        raise ValueError(
            f"{name}: incomplete download ({rows} rows; expected >= {min_rows})"
        )
    return rows


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, (required, minimum) in FILES.items():
        url = BASE + name
        path = DATA_DIR / ("onet_" + name)
        print(f"Downloading official O*NET 31.0 source: {url}", flush=True)
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "FutureSkillAI-SDG-Research/1.0"}
            )
            with urllib.request.urlopen(req, timeout=90) as response:
                raw = response.read(150 * 1024 * 1024 + 1)
            count = validated_content(raw, name, required, minimum)
        except (OSError, ValueError, UnicodeError) as exc:
            print(f"FAILED for {name}: {exc}")
            print(f"Manual fallback: download '{name}' at")
            print(f"  https://www.onetcenter.org/dictionary/31.0/csv/{name[:-4]}.html")
            print(f"  and save it at {path}")
            sys.exit(1)
        path.write_bytes(raw)
        print(f"Saved {count:,} original rows to {path}")
    print("Official data downloaded. O*NET 31.0 (USDOL/ETA), CC BY 4.0.")
    print("These task/activity statistics are NOT verified UN SDG outcomes.")
    print("Review provenance/license before committing the two CSVs to GitHub.")


if __name__ == "__main__":
    main()
