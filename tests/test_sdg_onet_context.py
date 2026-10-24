"""Offline tests for real-format O*NET 31.0 supporting files.

The small CSV data below are deliberately SYNTHETIC fixtures. They test
correct joining, suppression and interpretation, not actual SDG accuracy.
"""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reskilling import sdg_onet_context as context
from reskilling import sdg_task_evidence as evidence
from reskilling.sdg_candidate_ranker import (
    candidate_mappings_for_occupation, occupation_task_profile,
)


def write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class ONetSDGContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.tasks = root / "task_statements.csv"
        self.dwas = root / "tasks_to_dwas.csv"
        self.ratings = root / "task_ratings.csv"
        write_csv(self.tasks,
                  ["O*NET-SOC Code", "Title", "Task ID", "Task",
                   "Task Type", "Date"],
                  [
                      {"O*NET-SOC Code": "15-1252.00", "Title": "Software Developers",
                       "Task ID": "123", "Task": "Build an application.",
                       "Task Type": "Core", "Date": "08/2026"},
                      {"O*NET-SOC Code": "15-1252.00", "Title": "Software Developers",
                       "Task ID": "124", "Task": "Maintain information systems.",
                       "Task Type": "Supplemental", "Date": "08/2026"},
                      {"O*NET-SOC Code": "19-1011.00", "Title": "Other Occupation",
                       "Task ID": "123", "Task": "Study crops.",
                       "Task Type": "Core", "Date": "08/2026"},
                  ])
        write_csv(self.dwas, ["O*NET-SOC Code", "Task ID", "DWA Element ID",
                               "DWA Element Name"],
                  [
                      {"O*NET-SOC Code": "15-1252.00", "Task ID": "123",
                       "DWA Element ID": "D01", "DWA Element Name": "Develop educational software"},
                      {"O*NET-SOC Code": "19-1011.00", "Task ID": "123",
                       "DWA Element ID": "D02", "DWA Element Name": "Study crop growth"},
                  ])
        write_csv(self.ratings, ["O*NET-SOC Code", "Task ID", "Scale ID",
                                 "Data Value", "Recommend Suppress", "Domain Source"],
                  [
                      {"O*NET-SOC Code": "15-1252.00", "Task ID": "123",
                       "Scale ID": "IM", "Data Value": "4.25",
                       "Recommend Suppress": "N", "Domain Source": "Incumbent"},
                      {"O*NET-SOC Code": "15-1252.00", "Task ID": "123",
                       "Scale ID": "RT", "Data Value": "88.2",
                       "Recommend Suppress": "N", "Domain Source": "Incumbent"},
                      {"O*NET-SOC Code": "15-1252.00", "Task ID": "124",
                       "Scale ID": "IM", "Data Value": "4.9",
                       "Recommend Suppress": "Y", "Domain Source": "Incumbent"},
                      {"O*NET-SOC Code": "19-1011.00", "Task ID": "123",
                       "Scale ID": "IM", "Data Value": "2.0",
                       "Recommend Suppress": "N", "Domain Source": "Incumbent"},
                  ])
        for target, path in (
            ("reskilling.sdg_onet_context.DWA_CSV", self.dwas),
            ("reskilling.sdg_onet_context.RATINGS_CSV", self.ratings),
            ("reskilling.sdg_task_evidence.TASK_DATA", self.tasks),
        ):
            p = patch(target, path)
            p.start()
            self.addCleanup(p.stop)
        context._read_dwas.cache_clear()
        context._read_ratings.cache_clear()

    def test_exact_soc_and_task_join_no_cross_career_data_leaks(self):
        result = context.get_context("15-1252.00", "123")
        self.assertEqual(result["dwas"], [
            {"id": "D01", "name": "Develop educational software"}])
        self.assertEqual(result["task_ratings"]["importance_1_to_5"], 4.25)
        self.assertEqual(result["task_ratings"]["relevance_pct"], 88.2)
        self.assertEqual(context.get_context("19-1011.00", "123")["dwas"][0]["id"], "D02")
        self.assertFalse(context.get_context("15-1252.00", "124")["task_ratings"])

    def test_dwa_is_an_unverified_goal_level_candidate_not_a_target(self):
        result = candidate_mappings_for_occupation(
            "15-1252.00", "Software Developers")
        guess = next(x for x in result if x["sdg_id"] == 4)
        self.assertEqual(guess["candidate_tier"], "dwa_topic")
        self.assertIsNone(guess["target_id"])
        self.assertEqual(guess["task_evidence"][0]["task_id"], "123")
        self.assertIn("D01", [d["id"] for d in
                             guess["task_evidence"][0]["dwa_activities"]])
        self.assertIn("NOT", guess["impact_limitations"])

    def test_official_task_profile_reports_ratings_without_false_sdg_probability(self):
        profile = occupation_task_profile("15-1252.00")
        self.assertEqual(profile["occupation_task_count"], 2)
        self.assertEqual(profile["core_task_count"], 1)
        self.assertTrue(profile["supporting_data_available"]["task_ratings"])
        core = profile["representative_tasks"][0]
        self.assertEqual(core["task_id"], "123")
        self.assertEqual(core["task_ratings"]["importance_1_to_5"], 4.25)
        self.assertNotIn("sdg_probability", core)


if __name__ == "__main__":
    unittest.main()
