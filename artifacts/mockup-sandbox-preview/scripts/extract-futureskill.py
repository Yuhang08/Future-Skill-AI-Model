"""Refresh isolated, anonymous design-preview snapshots from the real app."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[3]
SANDBOX = ROOT / "artifacts/mockup-sandbox-preview"
GROUP = SANDBOX / "src/components/mockups/future-theme"
SOURCE = GROUP / "_source"
SOURCE.mkdir(parents=True, exist_ok=True)
for name, source in {
    "home.html": "static/index.html",
    "reskilling.html": "reskilling/index.html",
    "trends.html": "static/ai-trend.html",
    "uncertainty.html": "static/uncertainty.html",
    "sdg.html": "static/sdg-impact.html",
    "inventory.html": "static/dev-screens.html",
    "reskilling.css": "reskilling/static/style.css",
    "reskilling-dev.css": "reskilling/static/dev.css",
    "reskilling.js": "reskilling/static/app.js",
}.items():
    shutil.copyfile(ROOT / source, SOURCE / name)
assets = SANDBOX / "public/images/futureskill"
assets.mkdir(parents=True, exist_ok=True)
shutil.copytree(ROOT / "static/assets/sdg", assets / "sdg", dirs_exist_ok=True)
shutil.copyfile(ROOT / "static/favicon.svg", assets / "favicon.svg")

# No live learner session, session cookie, signed URL or token is exported.
sys.path.insert(0, str(ROOT))
with tempfile.TemporaryDirectory(prefix="future-theme-fixtures-") as data_dir:
    os.environ["FUTURESKILL_DATA_DIR"] = data_dir
    os.environ["FUTURESKILL_DEV_INVENTORY"] = "1"
    from fastapi.testclient import TestClient
    from app import app
    with TestClient(app) as client:
        def get(path):
            response = client.get(path)
            response.raise_for_status()
            return response.json()

        def post(path, payload):
            response = client.post(path, json=payload)
            response.raise_for_status()
            return response.json()

        state = get("/api/state?demo=1")
        state["csrf"] = "preview-only-not-a-token"
        fixtures = {
            "state": state,
            "states": {"fresh": state},
            "trends": get("/api/ai-trends"),
            "scenarios": get("/api/uncertainty/scenarios"),
            "sdg": {},
        }
        for scenario in ("dashboard", "returning", "partial", "no-gap", "edit"):
            opened = client.get(f"/__dev/demo/open?demo=1&demo_scenario={scenario}&scenario={scenario}")
            opened.raise_for_status()
            sample = get(f"/api/state?demo=1&demo_scenario={scenario}")
            sample["csrf"] = "preview-only-not-a-token"
            fixtures["states"][scenario] = sample
        from reskilling.extra_features import JOBS
        fixtures["occupational_weights"] = JOBS
        from reskilling.sdg_alignment import get_sdg_alignment
        for role in ("Data Analyst", "Software Developer", "Cybersecurity Analyst",
                     "UI/UX Designer", "Digital Marketing Specialist", "Unreviewed role"):
            # Static fixture extraction only; the live endpoint requires a selected ID.
            fixtures["sdg"][role] = get_sdg_alignment(role)
        fixtures["recommendations"] = post("/api/recommend", {
            "answers": {"R": [4,4,3,4], "I": [5,4,5,4], "A": [3,4,4,3],
                        "S": [4,5,4,4], "E": [4,4,5,4], "C": [3,4,4,5]},
            "subject_answers": {"IT": [5,4], "Math": [4,5], "Education": [4,4],
                               "Health": [3,3], "Business": [4,4], "Engineering": [4,5]},
            "skill_answers": {"MathSkill": 3, "CodingSkill": 3, "DataSkill": 4,
                             "CommunicationSkill": 4, "LeadershipSkill": 3, "CreativeSkill": 4},
        })
        (SOURCE / "fixtures.json").write_text(json.dumps(fixtures, ensure_ascii=False, indent=2))
print("Extracted six real pages, dependencies and anonymous preview fixtures.")
