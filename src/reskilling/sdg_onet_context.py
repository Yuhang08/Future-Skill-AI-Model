"""O*NET 31.0 supporting context for SDG research (not SDG validation).

Join genuine Tasks-to-DWAs and Task Ratings by BOTH O*NET-SOC Code and Task ID.
Importance (IM 1..5) and relevance (RT 0..100) describe occupational
importance/relevance, NOT the probability of SDG impact or match accuracy.
Missing or 'Recommend Suppress=Y' ratings are never imputed.
"""
import csv
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"
DWA_CSV = ROOT / "onet_tasks_to_dwas.csv"
RATINGS_CSV = ROOT / "onet_task_ratings.csv"
DWA_DOC = "https://www.onetcenter.org/dictionary/31.0/csv/tasks_to_dwas.html"
RATINGS_DOC = "https://www.onetcenter.org/dictionary/31.0/csv/task_ratings.html"


def _stamp(path):
    return (str(path), path.stat().st_mtime_ns) if path.is_file() else None


@lru_cache(maxsize=2)
def _read_dwas(path, timestamp):
    del timestamp
    result = {}
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"O*NET-SOC Code", "Task ID", "DWA Element ID", "DWA Element Name"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Invalid O*NET 31.0 Tasks to DWAs CSV")
        for row in reader:
            key = (row["O*NET-SOC Code"].strip(), row["Task ID"].strip())
            entry = {
                "id": row["DWA Element ID"].strip(),
                "name": row["DWA Element Name"].strip(),
            }
            if entry["id"] and entry["name"]:
                existing = result.setdefault(key, [])
                if entry not in existing:
                    existing.append(entry)
    return result


@lru_cache(maxsize=2)
def _read_ratings(path, timestamp):
    del timestamp
    result = {}
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"O*NET-SOC Code", "Task ID", "Scale ID", "Data Value", "Recommend Suppress"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Invalid O*NET 31.0 Task Ratings CSV")
        for row in reader:
            scale = row["Scale ID"].strip()
            if scale not in ("IM", "RT"):
                continue
            if row["Recommend Suppress"].strip().upper() == "Y":
                continue
            try:
                number = float(row["Data Value"])
            except (TypeError, ValueError):
                continue
            if scale == "IM" and not 1 <= number <= 5:
                continue
            if scale == "RT" and not 0 <= number <= 100:
                continue
            key = (row["O*NET-SOC Code"].strip(), row["Task ID"].strip())
            rating = result.setdefault(key, {})
            rating["importance_1_to_5" if scale == "IM" else "relevance_pct"] = round(number, 2)
            # This is source-rating metadata, not an SDG validation statistic.
            if row.get("Domain Source"):
                rating["domain_source"] = row["Domain Source"].strip()
    return result


def _available_index(path, loader):
    stamp = _stamp(path)
    if stamp is None:
        return None
    try:
        return loader(*stamp)
    except (OSError, ValueError, UnicodeError):
        return None


def sources_available():
    return {
        "tasks_to_dwas": _available_index(DWA_CSV, _read_dwas) is not None,
        "task_ratings": _available_index(RATINGS_CSV, _read_ratings) is not None,
    }


def get_context(code, task_id):
    """Return only data tied to this exact occupation/task pair."""
    key = (str(code), str(task_id))
    dwas = _available_index(DWA_CSV, _read_dwas)
    ratings = _available_index(RATINGS_CSV, _read_ratings)
    return {
        "dwas": (dwas.get(key, [])[:5] if dwas is not None else []),
        "task_ratings": (dict(ratings.get(key, {})) if ratings is not None else {}),
    }


def importance_sort_key(code, row):
    """Sort Core tasks first, then valid occupational importance, never SDG impact."""
    ratings = get_context(code, row["id"])["task_ratings"]
    importance = ratings.get("importance_1_to_5")
    relevance = ratings.get("relevance_pct")
    return (
        row.get("type", "").lower() != "core",
        importance is None,
        -(importance or 0),
        relevance is None,
        -(relevance or 0),
        int(row["id"]) if str(row["id"]).isdigit() else 999999999,
    )
