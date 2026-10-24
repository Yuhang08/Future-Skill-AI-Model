"""Frozen API baselines captured before the results-only UI refinement.

The original complete-response digests included the old SDG metadata. During the
task-SDG integration, the original helper reproduced every stored digest; removing
only that intentionally replaced metadata produced the core baselines below.
Scores and recommendation order/content must continue to match those baselines.
"""
import hashlib
import json
import os
import tempfile
import unittest
from copy import deepcopy

# Match the existing integration-suite import preconditions and never use learner data.
TEST_DATA = tempfile.TemporaryDirectory(prefix="futureskill-report-test-")
os.environ["FUTURESKILL_DATA_DIR"] = TEST_DATA.name
os.environ["FUTURESKILL_DEV_INVENTORY"] = "1"

from fastapi.testclient import TestClient
from main import app
from assessment_scoring import RIASEC, SUBJECTS, SKILLS


PROFILES = {
    "equal-high": ([5] * 6, [5] * 6, [5] * 6),
    "equal-low": ([1] * 6, [1] * 6, [1] * 6),
    "differentiated": ([2, 5, 3, 4, 2, 1], [5, 4, 3, 2, 1, 4], [2, 5, 4, 3, 1, 4]),
    "leading-tie": ([3, 5, 2, 5, 4, 1], [4, 5, 2, 3, 1, 4], [4, 2, 5, 3, 1, 4]),
    "mixed": ([4, 3, 2, 5, 1, 3], [1, 5, 3, 2, 4, 5], [5, 1, 3, 2, 4, 1]),
}

BASELINES = {
    "equal-high": "b654d3784a91857c1be24601c2c656c090b53767ec1a7b58084b37316e5650e1",
    "equal-low": "fb0686606a00de4386e3ae11f79d011c99eeb6cdb615804101b396a6c3a56b36",
    "differentiated": "1e80952e9de4e89ad283944535ad33c70cee1041f933434a022350ee190652c2",
    "leading-tie": "1561dfcdac3d32e89e9810e8fa63fccb5051bdc43124722f998fd668901e82c9",
    "mixed": "53caf0807a4d94c9a08c2bdba5772c41dc906ae3035ea36e492ca6b9ad78c1ed",
}

CORE_BASELINES = {
    "equal-high": "f3141b4f6f7ba6f3b8eb84456c97de785fcb5217192f9d80352a2beff4b590ff",
    "equal-low": "1374871e3138e202e090c606e3620a7f4f55ece82f05f398e37d2f58317535fa",
    "differentiated": "3eee2b9b6d30cd47c0afcd61d413a12efb820ca218d77382d91e365a414a2086",
    "leading-tie": "8f716f0818e69f8bc81032ecdfde9aa5d03db8bce6285fd44d1dda2289577d77",
    "mixed": "f6c613f6dceba475e353dce2781dac6a03a3456df43f58fa0d7dfb9156ae1d72",
}


def payload_for(name):
    interests, subjects, skills = PROFILES[name]
    return {
        "answers": {key: [value] * 4 for key, value in zip(RIASEC, interests)},
        "subject_answers": {key: [value] * 2 for key, value in zip(SUBJECTS, subjects)},
        "skill_answers": dict(zip(SKILLS, skills)),
    }


class AssessmentReportRegressionTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_scores_and_recommendations_match_pre_refinement_baselines(self):
        for name, expected in CORE_BASELINES.items():
            with self.subTest(profile=name):
                response = self.client.post("/api/recommend", json=payload_for(name))
                self.assertEqual(response.status_code, 200)
                legacy_contract = response.json()
                for career in legacy_contract["recommendations"]:
                    for additive_key in ("id", "pathway_career", "pathway_status", "sdg_alignment"):
                        career.pop(additive_key, None)
                canonical = json.dumps(legacy_contract, sort_keys=True, separators=(",", ":"))
                self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), expected)

    def test_broad_confidence_is_not_a_career_ranking_input(self):
        payload = payload_for("differentiated")
        original = self.client.post("/api/recommend", json=payload).json()
        payload["skill_answers"] = {key: 1 for key in SKILLS}
        changed = self.client.post("/api/recommend", json=payload).json()
        self.assertNotEqual(original["skills"], changed["skills"])
        for key in ("riasec_scores", "top3", "subject_preferences", "recommendations"):
            self.assertEqual(original[key], changed[key])

    def test_flat_interest_uses_neutral_index_and_stable_code(self):
        for name in ("equal-high", "equal-low"):
            result = self.client.post("/api/recommend", json=payload_for(name)).json()
            self.assertEqual(result["top3"], "RIA")
            self.assertEqual({row["interest_index"] for row in result["recommendations"]}, {50.0})
            self.assertEqual(len(set(result["riasec_scores"].values())), 1)

    def test_catalogue_ids_are_additive_and_resolve_to_canonical_profiles(self):
        catalogue = self.client.get("/api/careers", params={"q": "software", "limit": 5})
        self.assertEqual(catalogue.status_code, 200)
        self.assertGreater(catalogue.json()["total"], 0)
        career = catalogue.json()["results"][0]
        self.assertRegex(career["id"], r"^\d{2}-\d{4}\.\d{2}$")
        detail = self.client.get(f"/api/careers/{career['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["title"], career["title"])
        self.assertEqual(detail.json()["pathway"], career["pathway"])
        self.assertTrue(detail.json()["profile_url"].startswith("https://www.onetonline.org/"))
        self.assertIsInstance(detail.json()["pathway"]["available"], bool)
        self.assertTrue(detail.json()["pathway"]["status"])
        self.assertEqual(self.client.get("/api/careers/invalid").status_code, 404)
        for route in (
            "/career-overview",
            "/careers",
            "/my-profile",
            "/compare?ids=15-1252.00,15-1253.00",
            f"/career/{career['id']}",
        ):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 200)

    def test_recommendation_order_and_titles_resolve_through_additive_catalogue_ids(self):
        result = self.client.post("/api/recommend", json=payload_for("differentiated")).json()
        self.assertGreater(len(result["recommendations"]), 0)
        first = result["recommendations"][0]
        self.assertRegex(first["id"], r"^\d{2}-\d{4}\.\d{2}$")
        detail = self.client.get(f"/api/careers/{first['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["title"], first["title"])

    def test_invalid_assessment_still_rejected(self):
        base = payload_for("equal-high")
        missing = deepcopy(base)
        del missing["answers"]["R"]
        short = deepcopy(base)
        short["answers"]["R"] = [5]
        out_of_range = deepcopy(base)
        out_of_range["subject_answers"]["IT"] = [0, 6]
        null = deepcopy(base)
        null["skill_answers"]["MathSkill"] = None
        for payload in ({}, missing, short, out_of_range, null):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/recommend", json=payload).status_code, 422)


if __name__ == "__main__":
    unittest.main()
