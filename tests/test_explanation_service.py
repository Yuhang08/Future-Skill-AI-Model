"""Mocked HTTP transport and saved-profile endpoint tests; never real inference."""
import asyncio
from copy import deepcopy
import json
import logging
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

# Protect the real workspace before importing the application (Store has startup writes).
IMPORT_DATA = tempfile.TemporaryDirectory(prefix="gap_explanation_import_")
os.environ["FUTURESKILL_DATA_DIR"] = IMPORT_DATA.name
os.environ["FUTURESKILL_DEV_INVENTORY"] = "1"
from app import app
from reskilling import api as saved_api
from reskilling.explanation_provider import (
    ExplanationFailure, MAX_COMPLETION_TOKENS, MAX_PROVIDER_BYTES,
    OpenAIExplanationProvider, ProviderSettings,
)
from reskilling.explanation_service import (
    GapExplanationService, UsageLimiter, get_gap_explanation_service,
)
from reskilling.explanation_api import read_explanation_request
from reskilling.gap_explanations import assemble_explanation
from reskilling.storage import Store

ROOT = Path(__file__).resolve().parents[1]


class ExplanationEndpointTests(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.TemporaryDirectory(prefix="gap_explanation_test_")
        self.store = Store(Path(self.data.name) / "test.sqlite3")
        self.store_patch = patch.object(saved_api, "STORE", self.store)
        self.store_patch.start()
        self.client = TestClient(app)
        self.csrf = self.client.get("/api/state").json()["csrf"]
        self.subject = self.client.cookies["FS_SESSION"].split(".")[0]
        examples = ROOT / "docs" / "examples"
        self.ratings = json.loads((examples / "explain-skill-gaps-request.json").read_text())["skills"]
        full = json.loads((examples / "explain-skill-gaps-response.json").read_text())
        self.draft = {"schema_version": "1.0", "items": [
            {k: item[k] for k in ("skill", "why_skill_matters", "learning_actions", "limitations")}
            for item in full["gaps"]
        ]}
        self.profile = {
            "target_career": "Data Analyst", "skills": self.ratings,
            "weekly_hours": 6, "target_weeks": 8,
            "preferred_days": ["Tuesday", "Thursday"],
            "experience": "some", "learning_style": "project",
            "personal_goal": "PRIVATE_GOAL_NOT_FOR_PROVIDER",
            "current_industry": "PRIVATE_INDUSTRY_NOT_FOR_PROVIDER",
        }
        self.calls = []
        self.set_scenario("ok")

    def tearDown(self):
        app.dependency_overrides.pop(get_gap_explanation_service, None)
        self.client.close()
        self.store_patch.stop()
        self.data.cleanup()

    def save_profile(self):
        response = self.client.post("/api/plan", json=self.profile,
                                    headers={"X-CSRF-Token": self.csrf})
        self.assertEqual(response.status_code, 200)

    def set_scenario(self, scenario):
        async def handle(request):
            self.calls.append(json.loads(request.content))
            if scenario == "timeout":
                raise httpx.ReadTimeout("UPSTREAM_PRIVATE_MARKER", request=request)
            if scenario == "slow":
                await asyncio.sleep(.05)
            if scenario in ("auth", "rate", "server"):
                code = {"auth": 401, "rate": 429, "server": 503}[scenario]
                return httpx.Response(code, text="UPSTREAM_PRIVATE_MARKER")
            if scenario == "bad_envelope":
                return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": []}]})
            if scenario == "bad_json":
                return httpx.Response(200, text="UPSTREAM_PRIVATE_MARKER")
            if scenario == "large":
                return httpx.Response(200, content=b"x" * (MAX_PROVIDER_BYTES + 1))
            draft = deepcopy(self.draft)
            if scenario == "numbers":
                draft["items"][2]["required"] = 1
            if scenario == "citation":
                draft["items"][2]["learning_actions"][0]["source_ids"] = ["invented-source"]
            if scenario == "missing_skill":
                draft["items"].pop()
            if scenario == "changed":
                changed = deepcopy(self.profile)
                changed["skills"]["SQL"] = 1
                self.store.save_profile(self.subject, changed)
            message = {"content": json.dumps(draft)}
            if scenario == "refusal":
                message = {"content": None, "refusal": "UPSTREAM_PRIVATE_MARKER"}
            return httpx.Response(200, json={"choices": [{
                "finish_reason": "length" if scenario == "truncated" else "stop",
                "message": message,
            }]})

        transport = httpx.MockTransport(handle)
        factory = lambda: OpenAIExplanationProvider(
            ProviderSettings("https://api.openai.com/v1", "SYNTHETIC_TEST_CREDENTIAL", "test"),
            transport=transport,
        )
        self.service = GapExplanationService(factory)
        app.dependency_overrides[get_gap_explanation_service] = lambda: self.service

    def explain(self, body=None, **kwargs):
        return self.client.post(
            "/api/skill-gaps/explain",
            json=body if body is not None else {
                "schema_version": "1.0", "consent_to_model": True,
            },
            headers={"X-CSRF-Token": self.csrf}, **kwargs,
        )

    def test_saved_profile_success_numbers_sources_and_no_writes(self):
        self.save_profile()
        before = self.client.get("/api/state").json()
        response = self.explain()
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["explanation_origin"], "hosted_model")
        sql = next(item for item in result["gaps"] if item["skill"] == "SQL")
        self.assertEqual((sql["current"], sql["required"], sql["gap"],
                          sql["priority"], sql["estimated_hours"]), (2, 4, 2, .4, 10))
        self.assertEqual(len(result["gaps"]), 6)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.client.get("/api/state").json(), before)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0]["max_completion_tokens"], MAX_COMPLETION_TOKENS)
        self.assertFalse(self.calls[0]["store"])
        self.assertTrue(self.calls[0]["response_format"]["json_schema"]["strict"])

    def test_model_receives_minimal_validated_context_only(self):
        self.save_profile()
        self.assertEqual(self.explain().status_code, 200)
        payload = json.dumps(self.calls[0])
        for private in (
            "PRIVATE_GOAL_NOT_FOR_PROVIDER", "PRIVATE_INDUSTRY_NOT_FOR_PROVIDER",
            self.subject, "riasec", "weekly_hours", "current_industry",
            "catalog_ref", "current_level", "estimated_hours",
        ):
            self.assertNotIn(private, payload)
        context = json.loads(self.calls[0]["messages"][1]["content"])
        self.assertEqual(set(context), {"target_career", "rating_basis", "skills", "sources", "limitations"})
        self.assertNotIn("current", context["skills"][0])
        self.assertNotIn("required", context["skills"][0])
        self.assertTrue(next(item for item in context["skills"] if item["skill"] == "SQL")["needs_practice"])

    def test_missing_profile_and_corrupted_profile_make_no_call(self):
        response = self.explain()
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (409, "missing_profile"))
        self.store.save_profile(self.subject, {"target_career": "Data Analyst", "skills": {"SQL": True}})
        response = self.explain()
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (422, "profile_invalid"))
        self.assertEqual(self.calls, [])

    def test_another_session_cannot_use_the_saved_profile(self):
        self.save_profile()
        with TestClient(app) as other:
            csrf = other.get("/api/state").json()["csrf"]
            response = other.post("/api/skill-gaps/explain", json={
                "schema_version": "1.0", "consent_to_model": True,
            }, headers={"X-CSRF-Token": csrf})
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (409, "missing_profile"))
        self.assertEqual(self.calls, [])

    def test_final_numerical_snapshot_is_checked_independently(self):
        self.save_profile()
        request = {
            "schema_version": "1.0", "target_career": "Data Analyst",
            "rating_basis": "self_reported", "skills": self.ratings,
        }
        forged = assemble_explanation(request, self.draft, origin="hosted_model")
        forged.gaps[2].required = 1
        with patch("reskilling.explanation_service.assemble_explanation", return_value=forged):
            response = self.explain()
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (502, "invalid_response"))

    def test_csrf_consent_and_client_overrides_are_rejected(self):
        self.save_profile()
        response = self.client.post("/api/skill-gaps/explain", json={
            "schema_version": "1.0", "consent_to_model": True,
        })
        self.assertEqual(response.status_code, 403)
        for body, status in (
            ({}, 422),
            ({"schema_version": "1.0", "consent_to_model": False}, 400),
            ({"schema_version": "1.0", "consent_to_model": "true"}, 422),
            ({"schema_version": "1.0", "consent_to_model": 1}, 422),
            ({"schema_version": "1.0", "consent_to_model": True, "skills": self.ratings}, 422),
            ({"schema_version": "1.0", "consent_to_model": True, "target_career": "Data Analyst"}, 422),
        ):
            with self.subTest(body=body):
                self.assertEqual(self.explain(body).status_code, status)
        self.assertEqual(self.calls, [])

    def test_bad_json_media_type_and_request_size(self):
        for content, media_type, status in (
            (b"{", "application/json", 400),
            (b"x" * 1025, "application/json", 413),
            (b"{}", "text/plain", 415),
        ):
            with self.subTest(status=status):
                response = self.client.post(
                    "/api/skill-gaps/explain", content=content,
                    headers={"X-CSRF-Token": self.csrf, "Content-Type": media_type},
                )
                self.assertEqual(response.status_code, status)
        self.assertEqual(self.calls, [])

    def test_missing_credentials_is_explicit_and_does_not_call_provider(self):
        self.save_profile()
        self.service = GapExplanationService()
        app.dependency_overrides[get_gap_explanation_service] = lambda: self.service
        with patch.dict(os.environ, {}, clear=True):
            response = self.explain()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "missing_credentials")
        self.assertEqual(response.json()["explanation_origin"], "unavailable")
        self.assertEqual(self.calls, [])

    def test_provider_errors_are_sanitized_without_retries(self):
        self.save_profile()
        for scenario, status, code in (
            ("timeout", 504, "provider_timeout"),
            ("auth", 503, "credentials_rejected"),
            ("rate", 429, "provider_rate_limited"),
            ("server", 502, "provider_unavailable"),
            ("bad_json", 502, "invalid_response"),
            ("bad_envelope", 502, "invalid_response"),
            ("refusal", 502, "invalid_response"),
            ("truncated", 502, "invalid_response"),
            ("large", 502, "response_too_large"),
            ("numbers", 502, "invalid_response"),
            ("citation", 502, "invalid_response"),
            ("missing_skill", 502, "invalid_response"),
        ):
            with self.subTest(scenario=scenario):
                self.set_scenario(scenario)
                before = len(self.calls)
                response = self.explain()
                self.assertEqual((response.status_code, response.json()["error"]["code"]), (status, code))
                self.assertNotIn("UPSTREAM_PRIVATE_MARKER", response.text)
                self.assertNotIn("SYNTHETIC_TEST_CREDENTIAL", response.text)
                self.assertEqual(len(self.calls), before + 1)
                self.assertEqual(self.service.limiter.active, set())
                if status == 429:
                    self.assertIn("retry-after", response.headers)

    def test_total_timeout_and_input_output_bounds(self):
        self.save_profile()
        self.set_scenario("slow")
        with patch("reskilling.explanation_service.TOTAL_TIMEOUT_SECONDS", .001):
            self.assertEqual(self.explain().json()["error"]["code"], "provider_timeout")
        self.assertEqual(self.service.limiter.active, set())
        self.set_scenario("ok")
        count = len(self.calls)
        with patch("reskilling.explanation_provider.MAX_REQUEST_BYTES", 1):
            self.assertEqual(self.explain().json()["error"]["code"], "input_too_large")
        self.assertEqual(len(self.calls), count)
        with patch("reskilling.explanation_service.MAX_FINAL_BYTES", 1):
            self.assertEqual(self.explain().json()["error"]["code"], "response_too_large")

    def test_profile_change_during_inference_withholds_stale_explanation(self):
        self.save_profile()
        self.set_scenario("changed")
        response = self.explain()
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (409, "profile_changed"))
        self.assertNotIn("gaps", response.json())

    def test_fourth_request_is_locally_rate_limited(self):
        self.save_profile()
        for _ in range(3):
            self.assertEqual(self.explain().status_code, 200)
        response = self.explain()
        self.assertEqual((response.status_code, response.json()["error"]["code"]), (429, "local_rate_limited"))
        self.assertEqual(len(self.calls), 3)

    def test_provider_and_personal_data_do_not_appear_in_logs(self):
        self.save_profile()
        records = []

        class Capture(logging.Handler):
            def emit(self, record):
                records.append(record.getMessage())

        logger = logging.getLogger()
        handler = Capture()
        level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            self.assertEqual(self.explain().status_code, 200)
        finally:
            logger.setLevel(level)
            logger.removeHandler(handler)
        text = "\n".join(records)
        for private in ("SYNTHETIC_TEST_CREDENTIAL", "PRIVATE_GOAL_NOT_FOR_PROVIDER",
                        "PRIVATE_INDUSTRY_NOT_FOR_PROVIDER", self.subject):
            self.assertNotIn(private, text)


class ProviderConfigurationAndLimitsTests(unittest.TestCase):
    def test_managed_credentials_take_priority_and_incomplete_config_fails_closed(self):
        with patch.dict(os.environ, {
            "AI_INTEGRATIONS_OPENAI_BASE_URL": "http://localhost:1106/openai/v1",
            "AI_INTEGRATIONS_OPENAI_API_KEY": "SYNTHETIC_MANAGED",
            "OPENAI_API_KEY": "SYNTHETIC_DIRECT",
        }, clear=True):
            settings = ProviderSettings.from_environment()
            self.assertEqual(settings.credential_mode, "replit_managed")
            self.assertNotIn("SYNTHETIC", repr(settings))
        with patch.dict(os.environ, {"OPENAI_API_KEY": "SYNTHETIC_DIRECT"}, clear=True):
            self.assertEqual(ProviderSettings.from_environment().credential_mode, "replit_secret")
        for values in (
            {},
            {"AI_INTEGRATIONS_OPENAI_API_KEY": "SYNTHETIC"},
            {"AI_INTEGRATIONS_OPENAI_BASE_URL": "https://example.test"},
            {"AI_INTEGRATIONS_OPENAI_BASE_URL": "http://public.example",
             "AI_INTEGRATIONS_OPENAI_API_KEY": "SYNTHETIC"},
            {"AI_INTEGRATIONS_OPENAI_BASE_URL": "https://user:password@example.test",
             "AI_INTEGRATIONS_OPENAI_API_KEY": "SYNTHETIC"},
        ):
            with patch.dict(os.environ, values, clear=True), self.assertRaises(ExplanationFailure):
                ProviderSettings.from_environment()

    def test_concurrency_and_minute_limits(self):
        now = [0.]
        limiter = UsageLimiter(clock=lambda: now[0])
        limiter.acquire("a")
        with self.assertRaises(ExplanationFailure) as error:
            limiter.acquire("a")
        self.assertEqual(error.exception.code, "provider_busy")
        limiter.acquire("b")
        with self.assertRaises(ExplanationFailure):
            limiter.acquire("c")
        limiter.release("a")
        limiter.release("b")
        for _ in range(2):
            limiter.acquire("a")
            limiter.release("a")
        with self.assertRaises(ExplanationFailure) as error:
            limiter.acquire("a")
        self.assertEqual(error.exception.code, "local_rate_limited")
        now[0] = 61.
        limiter.acquire("a")
        limiter.release("a")
        limiter = UsageLimiter(clock=lambda: now[0])
        for i in range(12):
            limiter.acquire(str(i))
            limiter.release(str(i))
        with self.assertRaises(ExplanationFailure):
            limiter.acquire("new-session")

    def test_daily_limit_is_bounded_and_expires(self):
        now = [0.]
        limiter = UsageLimiter(clock=lambda: now[0])
        for i in range(60):
            if i % 12 == 0:
                now[0] += 61
            limiter.acquire(str(i))
            limiter.release(str(i))
        self.assertEqual(len(limiter.events), 60)
        with self.assertRaises(ExplanationFailure):
            limiter.acquire("over-budget")
        now[0] += 86_401
        limiter.acquire("after-expiry")
        self.assertEqual(len(limiter.events), 1)


class SlowRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_request_body_has_a_total_timeout(self):
        class SlowRequest:
            headers = {"content-type": "application/json"}

            async def stream(self):
                await asyncio.sleep(.05)
                yield b"{}"

        with patch("reskilling.explanation_api.REQUEST_BODY_TIMEOUT_SECONDS", .001):
            with self.assertRaises(ExplanationFailure) as error:
                await read_explanation_request(SlowRequest())
        self.assertEqual(error.exception.code, "request_timeout")
