"""Tests for task-derived goal-level scoring.

The synthetic tasks below are fixtures, NOT original O*NET records.
Actual SDG impact accuracy requires a separately labelled human benchmark.
"""
import unittest
from unittest.mock import patch

from reskilling.sdg_task_goal_model import (
    _score_task, score_career_goals, _lexical_similarity,
)


def task(task_id, text, task_type="Core", rating=None, dwas=None):
    return {
        "id": str(task_id), "task": text, "type": task_type,
        "task_ratings": rating or {}, "dwa_activities": dwas or [],
    }


class TaskToGoalScoreTests(unittest.TestCase):
    def setUp(self):
        score_career_goals.cache_clear()
        self.addCleanup(score_career_goals.cache_clear)

    def run_synthetic(self, rows, code="17-2199.11"):
        def context(_code, task_id):
            item = next(row for row in rows if row["id"] == task_id)
            return {
                "task_ratings": item.get("task_ratings", {}),
                "dwas": item.get("dwa_activities", []),
            }
        with patch("reskilling.sdg_task_goal_model._task_rows",
                   return_value=(rows, "available")), patch(
            "reskilling.sdg_task_goal_model.get_context", side_effect=context
        ):
            return score_career_goals(code, ("synthetic", code))

    def test_seventeen_ranked_goals_and_task_ids(self):
        rows = [
            task("910001", "Design photovoltaic solar power systems."),
            task("910002", "Install renewable energy solar photovoltaic panels."),
            task("910003", "Maintain electrical components in power generation."),
        ]
        data = self.run_synthetic(rows)
        scores = data["goal_scores"]
        self.assertEqual(len(scores), 17)
        self.assertEqual({x["sdg_id"] for x in scores}, set(range(1, 18)))
        self.assertEqual([x["rank"] for x in scores], list(range(1, 18)))
        self.assertEqual(len(data["top_goal_scores"]), 3)
        self.assertEqual(data["top_goal_scores"][0]["sdg_id"], 7)
        self.assertTrue(data["top_goal_scores"][0]["task_evidence"])
        self.assertTrue(all(
            x["task_id"] in {"910001", "910002", "910003"}
            for goal in scores for x in goal["task_evidence"]
        ))

    def test_task_text_governs_ranking_not_occupation_code(self):
        codes = ("11-1011.00", "53-7081.00")
        rows = [
            task("911001", "Monitor wastewater treatment and sewage quality."),
            task("911002", "Improve drinking water treatment systems."),
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.run_synthetic(rows, code)
                self.assertEqual(result["top_goal_scores"][0]["sdg_id"], 6)

    def test_direct_task_signal_dominates_generic_word_similarity(self):
        t = task("912001", "Teach students in classroom and develop lesson plans.")
        goal4 = _score_task(t, 4)
        goal8 = _score_task(t, 8)
        self.assertGreater(goal4["raw"], goal8["raw"])
        self.assertIn("teach students", goal4["phrase_matches"])

    def test_core_task_and_source_importance_affect_weight_not_impact(self):
        sentence = "Install photovoltaic solar power arrays."
        core = _score_task(task("913001", sentence, "Core"), 7)
        supplemental = _score_task(task("913002", sentence, "Supplemental"), 7)
        weighted = _score_task(task(
            "913003", sentence, "Core",
            {"importance_1_to_5": 5, "relevance_pct": 100}
        ), 7)
        self.assertGreater(core["raw"], supplemental["raw"])
        self.assertGreater(weighted["raw"], core["raw"])
        self.assertNotIn("sdg_probability", weighted)

    def test_dwa_weakly_contributes_but_is_not_a_certified_mapping(self):
        row = task("914001", "Review equipment.", dwas=[
            {"id": "4.A", "name": "Inspect photovoltaic solar energy systems"}
        ])
        result = _score_task(row, 7)
        self.assertGreater(result["raw"], 0)
        self.assertEqual(result["phrase_matches"], [])
        self.assertTrue(result["dwa_phrase_matches"])

    def test_no_fabricated_task_ids_for_missing_source(self):
        with patch("reskilling.sdg_task_goal_model._task_rows",
                   return_value=([], "not_installed")):
            result = score_career_goals("11-1011.00", ("missing",))
        self.assertEqual(result["status"], "not_installed")
        self.assertEqual(result["goal_scores"], [])
        self.assertEqual(result["top_goal_scores"], [])

    def test_even_weak_task_overlap_gives_ranked_exploratory_goals(self):
        result = self.run_synthetic([
            task("915001", "Compile records and review documents."),
        ])
        self.assertEqual(len(result["goal_scores"]), 17)
        self.assertEqual(len(result["top_goal_scores"]), 3)
        self.assertTrue(all(x["task_evidence"] for x in result["top_goal_scores"]))
        self.assertTrue(all(
            x["review_status"] != "verified_impact"
            for x in result["goal_scores"]
        ))

    def test_similarity_is_bounded(self):
        for phrase in ("", "dance choreography", "clinical patient assessment"):
            for goal in range(1, 18):
                score = _lexical_similarity(phrase, goal)
                self.assertGreaterEqual(score, 0)
                self.assertLessEqual(score, 1)


if __name__ == "__main__":
    unittest.main()
