"""Provider-free evidence, contract and unchanged-planner checks."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from reskilling.catalog import CAREERS, public_catalog
from reskilling.catalog_sources import CATALOG_SOURCE_ID, SOURCES
from reskilling.engine import generate_schedule, skill_gaps
from reskilling.gap_explanations import (
    ExplainGapsRequest, ExplainGapsResponse, ExplanationDraft,
    assemble_explanation, contract_schemas, prepare_explanation_input,
)

ROOT = Path(__file__).resolve().parents[1]


class GapExplanationTests(unittest.TestCase):
    def setUp(self):
        examples = ROOT / "docs" / "examples"
        self.request = json.loads((examples / "explain-skill-gaps-request.json").read_text())
        self.response = json.loads((examples / "explain-skill-gaps-response.json").read_text())
        self.draft = {
            "schema_version": "1.0",
            "items": [
                {key: item[key] for key in (
                    "skill", "why_skill_matters", "learning_actions", "limitations",
                )}
                for item in self.response["gaps"]
            ],
        }

    def test_full_example_matches_current_engine_and_sources(self):
        ExplainGapsRequest.model_validate(self.request)
        ExplainGapsResponse.model_validate(self.response)
        actual = assemble_explanation(self.request, self.draft).model_dump()
        self.assertEqual(actual, self.response)
        sql = next(gap for gap in actual["gaps"] if gap["skill"] == "SQL")
        self.assertEqual((sql["gap"], sql["priority"], sql["estimated_hours"]), (2, .4, 10))
        self.assertEqual(len(actual["gaps"]), 6)
        self.assertEqual(actual["explanation_origin"], "authored_example")

    def test_all_thirty_requirements_remain_illustrative(self):
        count = 0
        for role in CAREERS.values():
            for detail in role["skills"].values():
                count += 1
                self.assertEqual(detail["requirement_status"], "illustrative")
                self.assertEqual(detail["requirement_source_ids"], [CATALOG_SOURCE_ID])
                for source_id in detail["learning_source_ids"]:
                    self.assertEqual(SOURCES[source_id]["kind"], "technical_learning_reference")
        self.assertEqual(count, 30)

    def test_invalid_requests_are_rejected(self):
        for value in (True, "2", -1, 6, float("nan"), float("inf")):
            with self.subTest(value=value):
                request = deepcopy(self.request)
                request["skills"]["SQL"] = value
                with self.assertRaises(ValidationError):
                    prepare_explanation_input(request)
        for mutate in (
            lambda r: r.update(target_career="Unsupported occupation"),
            lambda r: r["skills"].pop("SQL"),
            lambda r: r["skills"].update({"Unreviewed skill": 2}),
            lambda r: r.update(riasec_scores={"I": 80}),
            lambda r: r.update(required={"SQL": 1}),
            lambda r: r.update(approved_sources=[]),
        ):
            request = deepcopy(self.request)
            mutate(request)
            with self.assertRaises(ValidationError):
                prepare_explanation_input(request)

    def test_each_skill_is_explained_exactly_once(self):
        for change in ("missing", "duplicate", "unknown"):
            draft = deepcopy(self.draft)
            if change == "missing":
                draft["items"].pop()
            elif change == "duplicate":
                draft["items"].append(deepcopy(draft["items"][0]))
            else:
                draft["items"][0]["skill"] = "Invented skill"
            with self.subTest(change=change), self.assertRaises(ValueError):
                assemble_explanation(self.request, draft)

    def test_draft_cannot_supply_numeric_results_or_sources(self):
        for key, value in (
            ("required", 1), ("gap", 0), ("priority", 1), ("estimated_hours", 1),
            ("requirement_status", "validated"), ("schedule", []),
            ("approved_sources", [{"id": "invented"}]),
        ):
            draft = deepcopy(self.draft)
            draft["items"][2][key] = value
            with self.subTest(key=key), self.assertRaises(ValidationError):
                assemble_explanation(self.request, draft)

    def test_unknown_unrelated_and_unsupported_citations_are_rejected(self):
        for source_id in ("made-up-course", "python-tutorial-3.12"):
            draft = deepcopy(self.draft)
            draft["items"][2]["learning_actions"][0]["source_ids"] = [source_id]
            with self.subTest(source_id=source_id), self.assertRaises(ValueError):
                assemble_explanation(self.request, draft)
        draft = deepcopy(self.draft)
        draft["items"][2]["why_skill_matters"]["source_ids"] = ["postgresql-sql-tutorial-18"]
        with self.assertRaises(ValueError):
            assemble_explanation(self.request, draft)
        draft = deepcopy(self.draft)
        draft["items"][2]["learning_actions"][0]["source_ids"] = [CATALOG_SOURCE_ID] * 2
        with self.assertRaises(ValueError):
            assemble_explanation(self.request, draft)

    def test_positive_gap_requires_action_and_draft_urls_are_rejected(self):
        draft = deepcopy(self.draft)
        draft["items"][2]["learning_actions"] = []
        with self.assertRaises(ValueError):
            assemble_explanation(self.request, draft)
        for url in ("https://invented.example/course", "HTTP://invented.example", "www.invented.example"):
            draft = deepcopy(self.draft)
            draft["items"][2]["learning_actions"][0]["text"] = f"Visit {url}"
            with self.subTest(url=url), self.assertRaises(ValueError):
                assemble_explanation(self.request, draft)
        draft = deepcopy(self.draft)
        draft["items"][2]["limitations"] = ["See https://invented.example"]
        with self.assertRaises(ValueError):
            assemble_explanation(self.request, draft)
        draft = deepcopy(self.draft)
        draft["items"][2]["why_skill_matters"]["text"] = "   "
        with self.assertRaises(ValidationError):
            assemble_explanation(self.request, draft)
        with self.assertRaises(ValidationError):
            assemble_explanation(self.request, self.draft, origin="llm")

    def test_prepared_evidence_is_minimal_and_independent(self):
        request = {
            "schema_version": "1.0", "target_career": "UI/UX Designer",
            "rating_basis": "self_reported",
            "skills": {name: 0 for name in CAREERS["UI/UX Designer"]["skills"]},
        }
        context = prepare_explanation_input(request)
        self.assertEqual([s.id for s in context.approved_sources], [CATALOG_SOURCE_ID])
        for item in context.calculated_gaps:
            self.assertEqual(item.learning_source_ids, [])
            self.assertIn("UI/UX Designer", item.catalog_ref)
        context.approved_sources[0].limitations.append("Not persisted")
        self.assertNotIn("Not persisted", SOURCES[CATALOG_SOURCE_ID]["limitations"])
        self.assertNotIn("riasec", context.model_dump_json().lower())

    def test_metadata_does_not_change_gap_or_schedule_results(self):
        stripped = deepcopy(CAREERS)
        for role in stripped.values():
            for detail in role["skills"].values():
                for key in ("requirement_status", "requirement_source_ids", "learning_source_ids"):
                    detail.pop(key)
        before_public = public_catalog()
        for career, role in CAREERS.items():
            profile = {
                "target_career": career, "skills": {name: 0 for name in role["skills"]},
                "weekly_hours": 6, "target_weeks": 8,
                "preferred_days": ["Tuesday", "Thursday", "Saturday"],
                "learning_style": "project", "experience": "beginner",
            }
            gaps = skill_gaps(profile)
            schedule = generate_schedule(profile, start_day=date(2026, 10, 22))
            with patch("reskilling.engine.CAREERS", stripped):
                self.assertEqual(gaps, skill_gaps(profile))
                self.assertEqual(schedule, generate_schedule(profile, start_day=date(2026, 10, 22)))
        with patch("reskilling.catalog.CAREERS", stripped):
            self.assertEqual(before_public, public_catalog())

    def test_schemas_export_without_provider_or_network(self):
        schemas = contract_schemas()
        self.assertEqual(set(schemas), {"request", "prepared_input", "explanation_draft", "response"})
        for schema in schemas.values():
            self.assertFalse(schema["additionalProperties"])
        properties = ExplanationDraft.model_json_schema()["$defs"]["SkillExplanation"]["properties"]
        self.assertNotIn("required", properties)
        self.assertNotIn("estimated_hours", properties)
        self.assertNotIn("approved_sources", properties)


if __name__ == "__main__":
    unittest.main()
