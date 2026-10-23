"""Saved-profile explanation orchestration, without persistence or scheduling."""
import asyncio
from collections import deque
from functools import lru_cache
import math
import time

from pydantic import ValidationError

from .explanation_provider import ExplanationFailure, OpenAIExplanationProvider
from .gap_explanations import (
    ExplainGapsRequest, assemble_explanation, prepare_explanation_input,
)

TOTAL_TIMEOUT_SECONDS = 20
MAX_FINAL_BYTES = 65_536
NUMERIC_FIELDS = ("current", "required", "gap", "importance", "priority", "estimated_hours")


def request_from_profile(profile):
    if profile is None:
        raise ExplanationFailure("missing_profile")
    if not isinstance(profile, dict):
        raise ExplanationFailure("profile_invalid")
    try:
        return ExplainGapsRequest(
            schema_version="1.0", target_career=profile.get("target_career"),
            rating_basis="self_reported", skills=profile.get("skills"),
        )
    except ValidationError:
        raise ExplanationFailure("profile_invalid") from None


def minimal_model_context(prepared):
    """No user ID, CV, goal, industry, experience, interest scores or raw ratings."""
    return {
        "target_career": prepared.target_career,
        "rating_basis": prepared.rating_basis,
        "skills": [{
            "skill": gap.skill, "objective": gap.objective,
            "project": gap.project, "needs_practice": gap.gap > 0,
            "requirement_status": gap.requirement_status,
            "allowed_source_ids": gap.requirement_source_ids + gap.learning_source_ids,
        } for gap in prepared.calculated_gaps],
        "sources": [{
            "id": source.id, "kind": source.kind, "title": source.title,
            "supports": source.supports, "limitations": source.limitations,
        } for source in prepared.approved_sources],
        "limitations": prepared.limitations,
    }


class UsageLimiter:
    """Single-process prototype limits, not durable account/billing quotas."""
    def __init__(self, *, clock=time.monotonic):
        self.clock = clock
        self.events = deque()
        self.active = set()

    def acquire(self, subject):
        now = self.clock()
        while self.events and self.events[0][0] <= now - 86_400:
            self.events.popleft()
        if len(self.events) >= 60:
            delay = math.ceil(86_400 - (now - self.events[0][0]))
            raise ExplanationFailure("local_rate_limited", retry_after=delay)
        recent = [(when, key) for when, key in self.events if when > now - 60]
        own = [when for when, key in recent if key == subject]
        if len(recent) >= 12 or len(own) >= 3:
            oldest = own[0] if len(own) >= 3 else recent[0][0]
            raise ExplanationFailure("local_rate_limited", retry_after=math.ceil(60 - (now - oldest)))
        if subject in self.active or len(self.active) >= 2:
            raise ExplanationFailure("provider_busy", retry_after=2)
        self.events.append((now, subject))
        self.active.add(subject)

    def release(self, subject):
        self.active.discard(subject)


class GapExplanationService:
    def __init__(self, provider_factory=OpenAIExplanationProvider.from_environment, *, limiter=None):
        self.provider_factory = provider_factory
        self.limiter = limiter or UsageLimiter()

    async def explain(self, profile, subject):
        request = request_from_profile(profile)
        prepared = prepare_explanation_input(request)
        provider = self.provider_factory()  # Missing configuration consumes no call budget.
        self.limiter.acquire(subject)
        try:
            try:
                async with asyncio.timeout(TOTAL_TIMEOUT_SECONDS):
                    draft = await provider.generate(minimal_model_context(prepared))
                # Recompute, validate all skill/citation scopes and merge server-owned numbers.
                response = assemble_explanation(request, draft, origin="hosted_model")
                for expected, actual in zip(prepared.calculated_gaps, response.gaps, strict=True):
                    if expected.skill != actual.skill or any(
                        getattr(expected, key) != getattr(actual, key) for key in NUMERIC_FIELDS
                    ):
                        raise ExplanationFailure("invalid_response")
                encoded = response.model_dump_json().encode("utf-8")
                if len(encoded) > MAX_FINAL_BYTES:
                    raise ExplanationFailure("response_too_large")
                return response
            except TimeoutError:
                raise ExplanationFailure("provider_timeout") from None
            except (ValidationError, ValueError, TypeError, UnicodeError, RecursionError):
                raise ExplanationFailure("invalid_response") from None
            except ExplanationFailure:
                raise
            except Exception:
                # Unexpected provider failures must not print SDK exceptions or data.
                raise ExplanationFailure("provider_unavailable") from None
        finally:
            self.limiter.release(subject)


@lru_cache(maxsize=1)
def get_gap_explanation_service():
    return GapExplanationService()
