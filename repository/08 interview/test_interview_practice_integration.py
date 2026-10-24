"""Contract and lifecycle checks for the mounted interview practice feature."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import hr_interview.app as interview_module
import hr_interview.interview_engine as interview_engine
import hr_interview.history_store as history_store
from main import app as fastapi_app


TEST_PROVIDER_ENV = {
    "AI_INTEGRATIONS_OPENAI_API_KEY": "",
    "AI_INTEGRATIONS_OPENAI_BASE_URL": "",
    "OPENAI_API_KEY": "synthetic-test-only-not-a-provider-key",
}


def feedback_result():
    return {
        "total": 72,
        "summary": "A short, specific practice observation.",
        "scores": {
            "relevance": 74,
            "clarity": 71,
            "evidence": 69,
            "depth": 73,
            "language": 73,
        },
        "strengths": ["The answer included a clear action."],
        "improvements": ["Add a concrete outcome."],
        "example_answer": "A fictional example, not a claim about the learner.",
    }


class InterviewPracticeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="futureskill_interview_")
        self.addCleanup(self.directory.cleanup)
        self.db_patch = patch.object(
            history_store, "DB_PATH", Path(self.directory.name) / "history.sqlite3"
        )
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        history_store.init()
        interview_module.sessions.clear()
        self.client = TestClient(fastapi_app)

    def catalogue_item(self):
        response = self.client.get("/interview-practice/api/careers")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 923)
        self.assertEqual(len(payload["career_options"]), 923)
        return payload["career_options"][0]

    def test_mounted_page_assets_and_canonical_catalogue(self):
        page = self.client.get("/interview-practice/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Interview practice", page.text)
        self.assertIn("Answers, audio and history", page.text)
        self.assertIn("Text answer", page.text)
        self.assertEqual(
            self.client.get("/interview-practice/static/interview.js").status_code, 200
        )
        self.assertEqual(
            self.client.get("/interview-practice/static/interview.css").status_code, 200
        )
        item = self.catalogue_item()
        self.assertTrue(item["id"])
        self.assertTrue(item["title"])
        self.assertFalse(item["supported_context"])

    def test_missing_provider_is_explicit_without_running_question_generation(self):
        empty = {
            "AI_INTEGRATIONS_OPENAI_API_KEY": "",
            "AI_INTEGRATIONS_OPENAI_BASE_URL": "",
            "OPENAI_API_KEY": "",
        }
        with patch.dict(os.environ, empty):
            self.assertFalse(
                self.client.get("/interview-practice/api/interview/availability").json()["available"]
            )
            with patch.object(interview_module, "pick", side_effect=AssertionError("must not run")):
                item = self.catalogue_item()
                response = self.client.post(
                    "/interview-practice/api/interview/start",
                    json={"role": item["title"], "career_id": item["id"]},
                )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["error"], "AI interview practice is temporarily unavailable."
        )
        self.assertNotIn("OPENAI_API_KEY", response.text)

    def test_mocked_interview_lifecycle_and_answer_storage_boundary(self):
        questions = [
            {"question": "Describe how you would approach a new project.", "focus": "Planning"},
            {"question": "Tell me about a problem you solved.", "focus": "Evidence"},
            {"question": "How would you explain a complex idea?", "focus": "Communication"},
        ]
        with patch.dict(os.environ, TEST_PROVIDER_ENV):
            with patch.object(interview_module, "pick", side_effect=questions):
                with patch.object(interview_module, "feedback_for", side_effect=lambda *_: feedback_result()):
                    career = self.catalogue_item()
                    started = self.client.post(
                        "/interview-practice/api/interview/start",
                        json={
                            "role": career["title"],
                            "career_id": career["id"],
                            "mode": "Mixed",
                            "language": "English",
                            "question_count": 3,
                        },
                    )
                    self.assertEqual(started.status_code, 200, started.text)
                    first = started.json()
                    self.assertEqual(first["question_number"], 1)
                    self.assertEqual(first["practice_scope"], "general")
                    self.assertIn("fs_guest", self.client.cookies)

                    answer_texts = [
                        "I planned the work and reviewed the result.",
                        "I found the problem, tested an approach, and explained the outcome.",
                        "I used a simple example and checked that it was clear.",
                    ]
                    session_id = first["session_id"]
                    for index, answer in enumerate(answer_texts):
                        bad = self.client.post(
                            "/interview-practice/api/interview/feedback",
                            json={"session_id": session_id, "answer": "x"},
                        )
                        self.assertEqual(bad.status_code, 400)
                        submitted = self.client.post(
                            "/interview-practice/api/interview/feedback",
                            json={"session_id": session_id, "answer": answer},
                        )
                        self.assertEqual(submitted.status_code, 200, submitted.text)
                        self.assertEqual(
                            submitted.json()["finished"], index == len(answer_texts) - 1
                        )
                        if index < len(answer_texts) - 1:
                            next_response = self.client.post(
                                "/interview-practice/api/interview/next",
                                json={"session_id": session_id},
                            )
                            self.assertEqual(next_response.status_code, 200)
                            self.assertEqual(next_response.json()["question_number"], index + 2)

                    completed = self.client.post(
                        "/interview-practice/api/interview/next",
                        json={"session_id": session_id},
                    )
                    self.assertEqual(completed.status_code, 200, completed.text)
                    report = completed.json()["report"]
                    self.assertEqual(report["questions_completed"], 3)
                    self.assertEqual(len(report["history"]), 3)
                    self.assertEqual(
                        self.client.post(
                            "/interview-practice/api/interview/next",
                            json={"session_id": session_id},
                        ).status_code,
                        404,
                    )

        guest = self.client.cookies.get("fs_guest")
        self.assertEqual(
            history_store.all_text(guest),
            [question["question"] for question in questions],
        )
        with sqlite3.connect(history_store.DB_PATH) as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(questions)")}
            self.assertNotIn("answer", columns)
        for answer in answer_texts:
            self.assertNotIn(answer, history_store.DB_PATH.read_bytes().decode("latin-1"))

    def test_invalid_role_id_mode_and_question_count_are_rejected(self):
        career = self.catalogue_item()
        with patch.dict(os.environ, TEST_PROVIDER_ENV):
            mismatch = self.client.post(
                "/interview-practice/api/interview/start",
                json={"role": career["title"], "career_id": "not-a-canonical-id"},
            )
            self.assertEqual(mismatch.status_code, 400)
            invalid_mode = self.client.post(
                "/interview-practice/api/interview/start",
                json={"role": career["title"], "mode": "Invented"},
            )
            self.assertEqual(invalid_mode.status_code, 400)
            invalid_count = self.client.post(
                "/interview-practice/api/interview/start",
                json={"role": career["title"], "question_count": 4},
            )
            self.assertEqual(invalid_count.status_code, 400)

    def test_provider_error_is_generic_and_does_not_leak_exception(self):
        item = self.catalogue_item()
        with patch.dict(os.environ, TEST_PROVIDER_ENV):
            with patch.object(interview_module, "pick", side_effect=RuntimeError("sensitive-provider-error")):
                response = self.client.post(
                    "/interview-practice/api/interview/start",
                    json={"role": item["title"], "career_id": item["id"]},
                )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "AI interview practice is temporarily unavailable.")
        self.assertNotIn("sensitive-provider-error", response.text)

    def test_malformed_provider_json_is_generic_without_a_live_call(self):
        career = self.catalogue_item()

        class FakeResponses:
            @staticmethod
            def create(**_kwargs):
                from types import SimpleNamespace
                return SimpleNamespace(output_text='{"question": "incomplete-provider-json"')

        fake_client = type("FakeClient", (), {"responses": FakeResponses()})()
        with patch.dict(os.environ, TEST_PROVIDER_ENV):
            with patch.object(interview_engine, "_client", fake_client):
                response = self.client.post(
                    "/interview-practice/api/interview/start",
                    json={"role": career["title"], "career_id": career["id"]},
                )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "AI interview practice is temporarily unavailable.")
        self.assertNotIn("incomplete-provider-json", response.text)


if __name__ == "__main__":
    unittest.main()
