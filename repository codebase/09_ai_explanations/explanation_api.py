"""Anonymous-session scoped, CSRF-protected explanation request handling."""
import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import Field, ValidationError

from .explanation_provider import ExplanationFailure
from .explanation_service import get_gap_explanation_service, request_from_profile
from .gap_explanations import ContractModel, ExplainGapsResponse

router = APIRouter()
MAX_BODY_BYTES = 1024
REQUEST_BODY_TIMEOUT_SECONDS = 5


class ExplainSavedGapsRequest(ContractModel):
    schema_version: str = Field(pattern=r"^1\.0$", strict=True)
    consent_to_model: bool = Field(strict=True)


def failure_response(error):
    headers = {"Cache-Control": "no-store"}
    if error.retry_after:
        headers["Retry-After"] = str(error.retry_after)
    return JSONResponse(
        status_code=error.status,
        content={"error": {
            "code": error.code, "message": error.message, "retryable": error.retryable,
        }, "explanation_origin": "unavailable"},
        headers=headers,
    )


async def read_explanation_request(request):
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        raise ExplanationFailure("unsupported_media_type")
    body = bytearray()
    try:
        async with asyncio.timeout(REQUEST_BODY_TIMEOUT_SECONDS):
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_BODY_BYTES:
                    raise ExplanationFailure("request_too_large")
                body.extend(chunk)
    except TimeoutError:
        raise ExplanationFailure("request_timeout") from None
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError, RecursionError):
        raise ExplanationFailure("invalid_json") from None
    try:
        parsed = ExplainSavedGapsRequest.model_validate(data)
    except ValidationError:
        raise ExplanationFailure("invalid_request") from None
    if not parsed.consent_to_model:
        raise ExplanationFailure("consent_required")
    return parsed


@router.post(
    "/api/skill-gaps/explain", response_model=ExplainGapsResponse,
    openapi_extra={"requestBody": {
        "required": True,
        "content": {"application/json": {"schema": ExplainSavedGapsRequest.model_json_schema()}},
    }},
)
async def explain_saved_skill_gaps(
    request: Request, service=Depends(get_gap_explanation_service),
):
    # Import lazily to retain the existing single source of session/store behavior.
    from .api import STORE, require_csrf, uid

    require_csrf(request)
    try:
        await read_explanation_request(request)
        subject = uid(request)
        profile = STORE.get_profile(subject)
        snapshot = request_from_profile(profile)
        result = await service.explain(profile, subject)
        # Do not return an explanation for a skill profile changed during inference.
        current = request_from_profile(STORE.get_profile(subject))
        if current != snapshot:
            raise ExplanationFailure("profile_changed")
        return JSONResponse(
            content=result.model_dump(mode="json"),
            headers={"Cache-Control": "no-store"},
        )
    except ExplanationFailure as error:
        return failure_response(error)
