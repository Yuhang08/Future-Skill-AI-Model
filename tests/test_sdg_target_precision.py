"""SDG semantic regression checks.

Synthetic task sentences below are controlled TEST CASES, not claims that the
official O*NET Task Statements dataset contains these exact sentences.
These tests prevent recurring false positives; they do not measure empirical
accuracy of all 923 occupation-to-SDG suggestions.
"""
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

    def test_target_3_8_access_not_generic_healthcare(self):
        self.assertFalse(matches(
            "3.8", "29-1141.00", "Provide clinical patient care and administer medications."
        ))
        self.assertTrue(matches(
            "3.8", "29-1141.00", "Improve patient access to healthcare services."
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
