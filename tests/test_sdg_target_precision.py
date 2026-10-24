"""SDG semantic regression checks.

Synthetic task sentences below are controlled TEST CASES, not claims that the
official O*NET Task Statements dataset contains these exact sentences.
These tests prevent recurring false positives; they do not measure empirical
accuracy of all 923 occupation-to-SDG suggestions.
"""
import ast
import csv
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reskilling.sdg_candidate_ranker import TASK_TOPICS
from reskilling.sdg_task_evidence import (
    TARGET_RULES, TASK_DATA, _match_rule, task_supported_mappings,
)


RULES = {rule["target"]: rule for rule in TARGET_RULES}


def matches(target, code, sentence, task_type="Core"):
    return _match_rule(sentence, code, RULES[target], task_type)


class SDGTargetPrecisionTests(unittest.TestCase):
    def test_no_duplicate_keys_in_sdg_target_rules(self):
        # A duplicate dictionary key is accepted by Python, but the second
        # value silently replaces the first (the cause of the 12.5 bug).
        import reskilling.sdg_task_evidence as module
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        variables = (
            stmt.value for stmt in tree.body
            if isinstance(stmt, ast.Assign)
            and any(isinstance(name, ast.Name) and name.id == "TARGET_RULES"
                    for name in stmt.targets)
        )
        definitions = next(variables)
        self.assertIsInstance(definitions, ast.Tuple)
        for rule in definitions.elts:
            self.assertIsInstance(rule, ast.Dict)
            keys = [key.value for key in rule.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)]
            self.assertEqual(len(keys), len(set(keys)),
                             "Duplicate key in an SDG Target rule: " + repr(keys))

    def test_target_1_3_social_protection_not_bank_loans(self):
        self.assertFalse(matches(
            "1.3", "13-2072.00",
            "Assist students in obtaining college financial assistance and loans."
        ))
        self.assertFalse(matches(
            "1.3", "13-2072.00",
            "Provide financial assistance for educational scholarships."
        ))
        self.assertTrue(matches(
            "1.3", "43-4061.00",
            "Determine eligibility for government assistance benefits."
        ))
        self.assertFalse(matches(
            "1.3", "43-4061.00",
            "Determine eligibility for government assistance benefits.",
            "Supplemental"
        ))

    def test_target_9_5_research_not_generic_it_support(self):
        self.assertFalse(matches(
            "9.5", "15-1232.00",
            "Test software and provide computer technical support to users."
        ))
        self.assertFalse(matches(
            "9.5", "15-1252.00",
            "Design, develop, and maintain software applications."
        ))
        self.assertTrue(matches(
            "9.5", "15-1221.00",
            "Conduct scientific research to develop innovative technologies."
        ))
        self.assertFalse(matches(
            "9.5", "15-1221.00",
            "Conduct scientific research to develop innovative technologies.",
            "Supplemental"
        ))

    def test_target_12_5_operations_not_recycling_training(self):
        self.assertFalse(matches(
            "12.5", "13-1151.00",
            "Train staff in recycling techniques and reducing waste."
        ))
        self.assertFalse(matches(
            "12.5", "13-1151.00",
            "Develop recycling curriculum and educational workshops."
        ))
        self.assertTrue(matches(
            "12.5", "53-7062.04",
            "Collect and sort recyclable materials for reuse."
        ))
        self.assertFalse(matches(
            "12.5", "53-7062.04",
            "Collect and sort recyclable materials for reuse.",
            "Supplemental"
        ))

    def test_target_4_1_k12_not_preschool_university_or_adults(self):
        sentence = "Teach students mathematics in their classrooms."
        self.assertTrue(matches("4.1", "25-2021.00", sentence))
        for code in ("25-1021.00", "25-2011.00",
                     "25-3011.00", "25-9044.00"):
            with self.subTest(code=code):
                self.assertFalse(matches("4.1", code, sentence))
        self.assertFalse(matches("4.1", "25-2021.00",
                                 sentence, "Supplemental"))

    def test_kindergarten_goes_to_4_2_not_primary_secondary_4_1(self):
        sentence = "Teach students reading and writing in kindergarten classrooms."
        self.assertFalse(matches("4.1", "25-2012.00", sentence))
        self.assertFalse(matches("4.1", "25-2055.00", sentence))
        self.assertTrue(matches("4.2", "25-2012.00", sentence))
        self.assertTrue(matches("4.2", "25-2055.00", sentence))
        self.assertFalse(matches("4.2", "25-2031.00", sentence))
        self.assertFalse(matches("4.1", "25-3031.00", sentence))
        self.assertTrue(matches("4.1", "25-2021.00", sentence))

    def test_target_3_8_access_not_generic_healthcare(self):
        self.assertFalse(matches(
            "3.8", "29-1141.00", "Provide clinical patient care and administer medications."
        ))
        self.assertTrue(matches(
            "3.8", "29-1141.00", "Improve patient access to healthcare services."
        ))

    def test_target_10_2_inclusion_not_one_off_passenger_help(self):
        self.assertFalse(matches(
            "10.2", "53-2031.00",
            "Determine special assistance needs of passengers, such as "
            "small children, the elderly, or persons with disabilities."
        ))
        self.assertTrue(matches(
            "10.2", "21-1093.00",
            "Develop social inclusion programs and remove accessibility barriers."
        ))

    def test_target_13_2_policy_not_truck_fuel_efficiency(self):
        # Based on the meaning of official O*NET Task ID 19923,
        # not proof of an implemented climate policy.
        self.assertFalse(matches(
            "13.2", "53-3032.00",
            "Plan or adjust routes to minimize fuel consumption and carbon emissions."
        ))
        self.assertTrue(matches(
            "13.2", "19-2041.00",
            "Develop national climate policies to integrate climate change measures."
        ))

    def test_target_6_3_direct_water_quality_not_health_lectures(self):
        # Task ID 17219 mentions "sewage" but is PUBLIC HEALTH EDUCATION.
        self.assertFalse(matches(
            "6.3", "29-1229.05",
            "Direct public health education programs dealing with water supply "
            "safety, sewage and waste disposal, and insect control."
        ))
        self.assertTrue(matches(
            "6.3", "51-8031.00",
            "Monitor wastewater treatment to improve water quality."
        ))

    def test_target_12_3_prevent_food_loss_not_collect_food_waste(self):
        self.assertFalse(matches(
            "12.3", "53-7081.00",
            "Collect and recycle food waste from collection sites."
        ))
        self.assertFalse(matches(
            "12.3", "29-1229.05",
            "Teach public health education classes about nutrition and food waste."
        ))
        self.assertTrue(matches(
            "12.3", "35-2021.00",
            "Reduce food waste by preventing spoilage of ingredients."
        ))

    def test_target_12_5_waste_prevention_not_generic_disposal(self):
        self.assertFalse(matches(
            "12.5", "39-4011.00",
            "Collect waste matter from organs and process bodily waste for disposal."
        ))
        self.assertFalse(matches(
            "12.5", "47-4041.00",
            "Collect hazardous waste material for disposal."
        ))
        self.assertTrue(matches(
            "12.5", "53-7062.04",
            "Collect and sort recyclable materials for reuse."
        ))
        self.assertTrue(matches(
            "12.5", "53-1042.01",
            "Coordinate recycling collection for reusable materials."
        ))

    def test_embalmer_containment_is_not_waste_reduction(self):
        # O*NET task 4504 is about professional containment, not SDG 12.5.
        self.assertFalse(matches(
            "12.5", "39-4011.00",
            "Pack body orifices to prevent escape of waste matter."
        ))

    def test_boiler_internal_water_is_not_water_pollution_control(self):
        # O*NET task 10470 protects boiler machinery from corrosion.
        self.assertFalse(matches(
            "6.3", "51-8021.00",
            "Test boiler water quality and take corrective action to prevent corrosion."
        ))
        self.assertTrue(matches(
            "6.3", "51-8031.00",
            "Monitor wastewater treatment to improve water quality."
        ))

    def test_recyclable_adjective_not_actual_recycling(self):
        # O*NET task 20313 sends materials to disposal sites, not an
        # explicitly recycling or waste-prevention operation.
        self.assertFalse(matches(
            "12.5", "53-7081.00",
            "Dump refuse or recyclable materials at disposal sites."
        ))
        # These original O*NET task themes DO refer to using recycled
        # materials and collecting metal scrap for actual recycling.
        self.assertTrue(matches(
            "12.5", "27-1025.00",
            "Design spaces using sustainable, recycled materials when feasible."
        ))
        self.assertTrue(matches(
            "12.5", "51-4052.00",
            "Skim slag and collect scrap for recycling."
        ))

    def test_core_scope_no_automatic_13_2_from_emissions(self):
        self.assertFalse(matches(
            "13.2", "49-9021.00",
            "Implement techniques that reduce greenhouse gas emissions."
        ))
        self.assertFalse(matches(
            "13.2", "53-3032.00",
            "Develop routes to minimize carbon emissions.", "Core"
        ))

    def test_staff_training_not_sdq4_career_theme(self):
        pattern = TASK_TOPICS[4][0]
        self.assertFalse(re.search(pattern,
                                   "Develop educational programs to train medical staff.",
                                   re.IGNORECASE))
        self.assertFalse(re.search(pattern,
                                   "Produce instructional materials for business staff.",
                                   re.IGNORECASE))
        self.assertTrue(re.search(pattern,
                                  "Design educational software for students.",
                                  re.IGNORECASE))

    def test_strict_mapping_uses_core_task_and_exact_code(self):
        with tempfile.TemporaryDirectory() as folder:
            task_csv = Path(folder) / "task_statements.csv"
            fieldnames = ["O*NET-SOC Code", "Title", "Task ID",
                          "Task", "Task Type", "Date"]
            records = [
                ("13-2072.00", "Loan Officers", "900001",
                 "Assist students in obtaining college financial assistance and loans.", "Core"),
                ("13-1151.00", "Training and Development Specialists", "900002",
                 "Train staff in recycling techniques and reducing waste.", "Core"),
                ("15-1232.00", "Computer User Support Specialists", "900003",
                 "Test software and provide computer technical support to users.", "Core"),
                ("25-1021.00", "Computer Science Teachers, Postsecondary", "900004",
                 "Teach students mathematics in their classrooms.", "Core"),
                ("53-7062.04", "Recycling and Reclamation Workers", "900005",
                 "Collect and sort recyclable materials for reuse.", "Core"),
                ("53-7062.04", "Recycling and Reclamation Workers", "900006",
                 "Collect and sort recyclable materials for reuse.", "Supplemental"),
            ]
            with task_csv.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fieldnames)
                writer.writeheader()
                for code, title, identifier, task, task_type in records:
                    writer.writerow({
                        "O*NET-SOC Code": code, "Title": title,
                        "Task ID": identifier, "Task": task,
                        "Task Type": task_type, "Date": "10/2026"
                    })
            with patch("reskilling.sdg_task_evidence.TASK_DATA", task_csv):
                for code, title, excluded in (
                    ("13-2072.00", "Loan Officers", "1.3"),
                    ("13-1151.00", "Training and Development Specialists", "12.5"),
                    ("15-1232.00", "Computer User Support Specialists", "9.5"),
                    ("25-1021.00", "Computer Science Teachers, Postsecondary", "4.1"),
                ):
                    with self.subTest(code=code):
                        result, _ = task_supported_mappings(code, title)
                        self.assertNotIn(excluded, [m["target_id"] for m in result])
                result, _ = task_supported_mappings(
                    "53-7062.04", "Recycling and Reclamation Workers")
                match = next(m for m in result if m["target_id"] == "12.5")
                self.assertEqual([t["task_id"] for t in match["task_evidence"]],
                                 ["900005"])

    def test_task_ids_from_report_not_wrong_target_if_official_csv_installed(self):
        # These task IDs appeared in the user's 83-record audit.
        # Exact original texts are loaded from O*NET, never invented.
        if not TASK_DATA.is_file():
            self.skipTest("Official O*NET 31.0 task data not installed")
        from reskilling.sdg_task_evidence import _read_index
        index = _read_index(str(TASK_DATA), TASK_DATA.stat().st_mtime_ns)
        suspicious = (
            ("53-2031.00", "9643", "10.2"),   # One-off passenger assistance
            ("53-3032.00", "19923", "13.2"),  # Lower-carbon route planning
            ("29-1229.05", "17219", "6.3"),  # Public health education
            ("29-1229.05", "17219", "12.3"), # Food sanitation lectures
            ("39-4011.00", "4504", "12.5"),    # Containing bodily waste matter
            ("51-8021.00", "10470", "6.3"),    # Internal boiler water testing
            ("53-7081.00", "20313", "12.5"),  # Disposal site != recycling
        )
        for career_id, task_id, target in suspicious:
            with self.subTest(task_id=task_id, target=target):
                tasks = [row for row in index.get(career_id, [])
                         if row["id"] == task_id]
                self.assertEqual(len(tasks), 1,
                                 f"Expected exactly one original O*NET Task ID {task_id}")
                task = tasks[0]
                self.assertFalse(_match_rule(task["task"], career_id,
                                             RULES[target], task["type"]))

    def test_real_onet_regressions_if_installed(self):
        # This catches regressions against the repository's *real* O*NET data.
        if not TASK_DATA.is_file():
            self.skipTest("Official O*NET 31.0 task data is not installed")
        for code, title, forbidden_target in (
            ("13-2072.00", "Loan Officers", "1.3"),
            ("15-1232.00", "Computer User Support Specialists", "9.5"),
            ("25-1021.00", "Computer Science Teachers, Postsecondary", "4.1"),
            ("13-1151.00", "Training and Development Specialists", "12.5"),
        ):
            with self.subTest(code=code):
                mappings, status = task_supported_mappings(code, title)
                self.assertEqual(status, "available")
                self.assertNotIn(forbidden_target,
                                 [m["target_id"] for m in mappings])


if __name__ == "__main__":
    unittest.main()
