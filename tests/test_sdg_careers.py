"""SDG API regressions. Synthetic task fixtures are NOT claimed to be O*NET data."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app
from reskilling.sdg_alignment import (
    get_sdg_alignment, get_sdg_careers, get_sdg_alignment_by_id,
)
from reskilling.sdg_task_evidence import TASK_DATA as OFFICIAL_TASK_DATA


class SDGCareerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # No downloaded official dataset is assumed in CI. Even when the
        # developer imports it locally, these baseline tests stay deterministic.
        self.missing = patch(
            "reskilling.sdg_task_evidence.TASK_DATA",
            Path("/this/path/intentionally/does/not/exist/onet_tasks.csv"),
        )
        self.missing.start()
        self.addCleanup(self.missing.stop)

    def search(self, query):
        result = self.client.get("/api/sdg/careers", params={"q": query})
        self.assertEqual(result.status_code, 200)
        return result.json()["results"]

    def sdg(self, career_id):
        response = self.client.post("/api/sdg/mindmap", json={"career_id": career_id})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_environmental_engineer_identity(self):
        for alias in ("Environmental Engineer", "environmental engineer",
                      " ENVIRONMENTAL   ENGINEERS "):
            result = self.search(alias)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], "17-2081.00")

    def test_chef_has_unverified_but_explicitly_lower_tier_suggestion(self):
        data = self.sdg("35-1011.00")  # Chefs and Head Cooks
        self.assertEqual(data["task_data_status"], "not_installed")
        self.assertEqual(data["status"], "no_task_evidence")
        self.assertEqual(data["mappings"], [])
        self.assertTrue(any(x["sdg_id"] == 12 for x in data["candidate_mappings"]))
        self.assertTrue(all(x["candidate_tier"] == "classification_only"
                            for x in data["candidate_mappings"]))
        self.assertEqual(data["task_profile"]["occupation_task_count"], 0)
        self.assertEqual(data["learning_pathway_mappings"], [])

    def test_training_goal_4_and_8_are_separate_from_occupation(self):
        for career_id in (
            "15-1252.00", "15-1212.00", "15-1255.00",
            "prototype:data-analyst", "prototype:cybersecurity-analyst",
            "prototype:ui-ux-designer",
        ):
            with self.subTest(career_id=career_id):
                data = self.sdg(career_id)
                self.assertEqual(data["mappings"], [])
                self.assertEqual(
                    {m["target_id"] for m in data["learning_pathway_mappings"]},
                    {"4.4", "8.5"},
                )
                self.assertTrue(all(
                    m["mapping_kind"] == "pathway_preparation"
                    for m in data["learning_pathway_mappings"]
                ))

    def test_923_occupation_catalogue_coverage_without_faked_evidence(self):
        occupations = {
            code: value for code, value in get_sdg_careers().items()
            if value["kind"] == "occupation"
        }
        self.assertEqual(len(occupations), 923)
        for code, career in occupations.items():
            with self.subTest(code=code):
                data = get_sdg_alignment_by_id(code)
                self.assertEqual(data["career"], career["title"])
                self.assertEqual(data["mappings"], [])
                self.assertEqual(data["task_data_status"], "not_installed")
                self.assertTrue(data["candidate_mappings"])
                self.assertEqual(data["task_profile"]["source_status"], "not_installed")
                self.assertEqual(data["task_profile"]["representative_tasks"], [])
                self.assertLessEqual(len(data["candidate_mappings"]), 3)

    def test_923_analyses_with_official_task_data_when_installed(self):
        # Genuine imported CSV is checked for role-by-role provenance. Missing
        # official data skips the test; fabricated fixtures never pass as real.
        if not OFFICIAL_TASK_DATA.is_file():
            self.skipTest("Official O*NET 31.0 Task Statements CSV not installed")
        with patch("reskilling.sdg_task_evidence.TASK_DATA", OFFICIAL_TASK_DATA):
            records = {
                code: rec for code, rec in get_sdg_careers().items()
                if rec["kind"] == "occupation"
            }
            self.assertEqual(len(records), 923)
            for code, record in records.items():
                with self.subTest(code=code):
                    result = get_sdg_alignment_by_id(code)
                    self.assertEqual(result["career"], record["title"])
                    self.assertTrue(result["mappings"] or result["candidate_mappings"])
                    self.assertIn(result["task_data_status"],
                                  ("available", "occupation_tasks_missing"))
                    self.assertIsNotNone(result["task_profile"])
                    profile = result["task_profile"]
                    if profile["occupation_task_count"]:
                        self.assertTrue(profile["representative_tasks"])
                        self.assertTrue(all(task["task_id"].isdigit() for task
                                            in profile["representative_tasks"]))
                    else:
                        self.assertEqual(result["task_data_status"],
                                         "occupation_tasks_missing")
                    for suggestion in result["candidate_mappings"]:
                        tier = suggestion["candidate_tier"]
                        self.assertIn(tier, (
                            "task_topic", "dwa_topic", "classification_only"))
                        if tier == "classification_only":
                            # Broad classification guesses must NOT fabricate
                            # occupation-specific task evidence.
                            self.assertEqual(suggestion["task_evidence"], [])
                        else:
                            # Both text-topic and DWA-topic candidates must
                            # reference genuine O*NET occupation task IDs.
                            self.assertTrue(suggestion["task_evidence"])
                            self.assertTrue(all(
                                item["task_id"].isdigit()
                                for item in suggestion["task_evidence"]
                            ))
                            if tier == "dwa_topic":
                                # The DWA association must come from the
                                # exact occupational task, not a job-title guess.
                                self.assertTrue(any(
                                    item.get("dwa_activities")
                                    for item in suggestion["task_evidence"]
                                ))

    def test_unknown_and_malformed_career_ids(self):
        self.assertEqual(self.search("the invalid"), [])
        self.assertEqual(get_sdg_alignment("the invalid")["status"], "unknown")
        for payload, expected in (
            ({}, 422), ({"career_id": ""}, 422),
            ({"career_id": "unknown"}, 404),
            ({"title": "Chefs and Head Cooks"}, 422),
            ({"career_id": "x" * 101}, 422),
            ({"career_id": "15-1252.00", "skills": {"Python": 5}}, 422),
        ):
            self.assertEqual(self.client.post("/api/sdg/mindmap", json=payload).status_code, expected)

    def test_fuzzy_search_does_not_auto_select_role(self):
        results = self.search("enviromental engineer")
        self.assertEqual(results[0]["id"], "17-2081.00")
        self.assertEqual(results[0]["matched_by"], "suggestion")
        self.assertEqual(get_sdg_alignment("enviromental engineer")["status"], "unknown")

    def test_real_data_parser_with_explicitly_synthetic_test_fixture(self):
        # These strings are TEST FIXTURES written here, not real O*NET tasks.
        # Verify that generic chef shopping does not imply reduced food waste,
        # whereas an explicit, task-identified waste-prevention duty can form
        # an unreviewed task-level candidate connection.
        with tempfile.TemporaryDirectory() as directory:
            taskfile = Path(directory) / "task_statements.csv"
            with taskfile.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=[
                    "O*NET-SOC Code", "Title", "Task ID", "Task",
                    "Task Type", "Date"
                ])
                writer.writeheader()
                writer.writerow({
                    "O*NET-SOC Code": "35-1011.00",
                    "Title": "Chefs and Head Cooks",
                    "Task ID": "900001",
                    "Task": "Order food and kitchen supplies.",
                    "Task Type": "Core", "Date": "10/2026",
                })
                writer.writerow({
                    "O*NET-SOC Code": "35-1011.00",
                    "Title": "Chefs and Head Cooks",
                    "Task ID": "900002",
                    "Task": "Reduce food waste by tracking spoiled ingredients.",
                    "Task Type": "Core", "Date": "10/2026",
                })
            with patch("reskilling.sdg_task_evidence.TASK_DATA", taskfile):
                data = self.sdg("35-1011.00")
                self.assertEqual(data["task_data_status"], "available")
                mapping = next(m for m in data["mappings"] if m["target_id"] == "12.3")
                self.assertEqual(mapping["specificity"], "onet_task")
                self.assertEqual(mapping["review_status"], "task_signal_unreviewed")
                self.assertEqual(mapping["task_evidence"][0]["task_id"], "900002")
                self.assertNotIn("900001", [task["task_id"] for task in mapping["task_evidence"]])
                self.assertIn("onet-task-statements", mapping["supporting_source_ids"])
                self.assertEqual(data["task_profile"]["occupation_task_count"], 2)
                self.assertEqual({x["task_id"] for x in
                                  data["task_profile"]["representative_tasks"]},
                                 {"900001", "900002"})
                self.assertTrue(all(x["sdg_id"] != 12 for x in
                                    data["candidate_mappings"]))

    def test_task_topic_is_not_promoted_to_a_verified_target(self):
        # Synthetic test ONLY. An IT role describing educational software can
        # have a lower-tier SDG 4 suggestion without inventing Target 4.1.
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "task_statements.csv"
            with p.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=[
                    "O*NET-SOC Code", "Title", "Task ID", "Task", "Task Type", "Date"])
                writer.writeheader()
                writer.writerow({
                    "O*NET-SOC Code": "15-1252.00",
                    "Title": "Software Developers",
                    "Task ID": "990011",
                    "Task": "Design educational software for students.",
                    "Task Type": "Core", "Date": "10/2026",
                })
            with patch("reskilling.sdg_task_evidence.TASK_DATA", p):
                response = self.sdg("15-1252.00")
                self.assertFalse(any(x["target_id"] == "4.1"
                                     for x in response["mappings"]))
                candidate = next(x for x in response["candidate_mappings"]
                                 if x["sdg_id"] == 4)
                self.assertEqual(candidate["candidate_tier"], "task_topic")
                self.assertIsNone(candidate["target_id"])
                self.assertEqual(candidate["task_evidence"][0]["task_id"], "990011")
                self.assertEqual(response["task_profile"]["core_task_count"], 1)

    def test_generic_synthetic_food_inventory_is_not_target_12_3(self):
        from reskilling.sdg_task_evidence import TARGET_RULES, _match_rule
        waste = next(r for r in TARGET_RULES if r["target"] == "12.3")
        self.assertFalse(_match_rule(
            "Estimate amounts and costs of food and ingredients.", "35-1011.00", waste))
        self.assertFalse(_match_rule(
            "Order or requisition food supplies.", "35-1011.00", waste))
        self.assertTrue(_match_rule(
            "Reduce food waste by tracking spoiled ingredients.", "35-1011.00", waste))


if __name__ == "__main__":
    unittest.main()
