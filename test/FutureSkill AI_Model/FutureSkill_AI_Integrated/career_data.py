"""Loads ALL titles from the existing FutureSkill CSV without hardcoded role limits."""
import csv
import os
from pathlib import Path
BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / os.getenv("CAREER_CSV", "career_profiles_clean.csv")
DEMO_PATH = BASE / "careers_demo.csv"

def get_careers():
    path = CSV_PATH if CSV_PATH.is_file() else DEMO_PATH
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "Title" not in reader.fieldnames:
            raise ValueError("Career CSV must have a Title column")
        careers = {}
        for row in reader:
            title = (row.get("Title") or "").strip()
            if title:
                careers[title.casefold()] = {"title": title,
                    "skills": (row.get("Skills") or "").strip(),
                    "description": (row.get("Description") or "").strip(),
                    "source": (row.get("Source") or "").strip()}
    return sorted(careers.values(), key=lambda d: (d["title"].casefold(), d["title"]))

def find_career(title):
    return next((x for x in get_careers() if x["title"] == title), None)
