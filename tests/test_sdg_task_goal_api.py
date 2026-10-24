"""Smoke tests of the task-to-SDG scores returned by the existing mindmap API."""
import unittest

from fastapi.testclient import TestClient
from main import app
from reskilling.sdg_task_evidence import source_status

# The test never downloads anything and never invents original occupation IDs.


class TaskGoalAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if source_status() != "available":
            raise unittest.SkipTest("Official O*NET Task Statements CSV not installed")
        cls.client = TestClient(app)

    def test_task_based_ranking_for_different_real_careers(self):
        samples = {
            "17-2199.11": "Solar Energy Systems Engineers",
            "51-8031.00": "Water and Wastewater Treatment Plant and System Operators",
            "25-2021.00": "Elementary School Teachers, Except Special Education",
            "11-1011.00": "Chief Executives",
        }
        for code, title in samples.items():
            with self.subTest(code=code):
                response = self.client.post(
                    "/api/sdg/mindmap", json={"career_id": code}
                )
                self.assertEqual(response.status_code, 200, response.text)
                data = response.json()
                self.assertEqual(data["career_id"], code)
                self.assertEqual(data["career"], title)
                self.assertEqual(len(data["goal_scores"]), 17)
                self.assertEqual(len(data["top_goal_scores"]), 3)
                self.assertEqual(
                    {g["sdg_id"] for g in data["goal_scores"]}, set(range(1, 18))
                )
                self.assertEqual(
                    [g["rank"] for g in data["top_goal_scores"]], [1, 2, 3]
                )
                self.assertGreater(data["task_profile"]["occupation_task_count"], 0)
                original_ids = {
                    row["task_id"]
                    for goal in data["goal_scores"]
                    for row in goal["task_evidence"]
                }
                self.assertTrue(original_ids)
                self.assertTrue(all(identifier.isdigit() for identifier in original_ids))
                self.assertIn("NOT probabilities", data["goal_scoring_method"])
                # Goal-level scoring NEVER upgrades a weak suggestion to an
                # existing strict Target-evidence mapping.
                self.assertIsInstance(data["mappings"], list)


if __name__ == "__main__":
    unittest.main()
