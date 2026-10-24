"""Interview career lookup backed by FutureSkill's canonical occupation catalogue."""
import csv
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
_csv_name = Path(os.getenv("CAREER_CSV", "career_profiles_clean.csv"))
if _csv_name.is_absolute():
    CSV_PATH = _csv_name
else:
    CSV_PATH = next(
        (path for path in (BASE.parent / _csv_name, BASE / _csv_name) if path.is_file()),
        BASE.parent / _csv_name,
    )


def get_careers():
    # Do not silently swap to the upstream illustrative demo list when the
    # canonical catalogue is missing.
    if not CSV_PATH.is_file():
        raise FileNotFoundError("The FutureSkill career catalogue is unavailable.")
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or "Title" not in reader.fieldnames:
            raise ValueError("Career CSV must have a Title column")
        careers = {}
        for row in reader:
            title = (row.get("Title") or "").strip()
            if not title:
                continue
            careers[title.casefold()] = {
                "title": title,
                "id": (row.get("O*NET-SOC Code") or "").strip(),
                "skills": (row.get("Skills") or "").strip(),
                "description": (row.get("Description") or "").strip(),
                "source": (row.get("Source") or "").strip(),
            }
    return sorted(careers.values(), key=lambda item: (item["title"].casefold(), item["title"]))


def find_career(title):
    if not isinstance(title, str):
        return None
    return next((item for item in get_careers() if item["title"] == title), None)


def find_career_id(career_id):
    if not isinstance(career_id, str) or not career_id:
        return None
    return next((item for item in get_careers() if item["id"] == career_id), None)
