"""Input/response contracts for 'Explain my skill gaps'.

The explanatory draft has no numeric result fields: those are copied from the
existing engine. Provider transport and orchestration live in separate modules.
"""

from copy import deepcopy
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .catalog import CAREERS
from .catalog_sources import CATALOG_SOURCE_ID, SOURCES
from .engine import skill_gaps

Rating = Annotated[float, Field(strict=True, ge=0, le=5, allow_inf_nan=False)]
Number = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]
Text = Annotated[str, Field(strict=True, min_length=1, max_length=1200)]
SourceIds = Annotated[list[Text], Field(min_length=1, max_length=4)]

LIMITATIONS = [
    "Skill ratings are self-reported, not verified proficiency.",
    "All target levels, importance weights, hour estimates and prerequisite choices remain illustrative catalogue assumptions.",
    "Technical learning references do not validate occupational requirements or job demand.",
    "A zero gap does not establish mastery; suggested actions do not change the schedule or award completion credit.",
    "Interest-profile CSV records are not occupational skill-requirement evidence and are excluded.",
    "Citation and schema validation do not prove textual entailment; explanations still require evidence review.",
]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ExplainGapsRequest(ContractModel):
    schema_version: Literal["1.0"]
    target_career: Text
    rating_basis: Literal["self_reported"]
    skills: dict[Text, Rating]

    @model_validator(mode="after")
    def supported_complete_profile(self):
        if self.target_career not in CAREERS:
            raise ValueError("An existing supported pathway is required.")
        if set(self.skills) != set(CAREERS[self.target_career]["skills"]):
            raise ValueError("Provide exactly the supported pathway's skill ratings.")
        return self


class ApprovedSource(ContractModel):
    id: Text
    title: Text
    kind: Literal["illustrative_catalog", "technical_learning_reference"]
    local_path: Text | None
    url: Text | None
    accessed_on: Text | None
    published_on: Text | None
    supports: Text
    limitations: Annotated[list[Text], Field(min_length=1)]


class CalculatedGap(ContractModel):
    skill: Text
    current: Rating
    required: Rating
    gap: Rating
    importance: Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]
    priority: Number
    estimated_hours: Number
    objective: Text
    project: Text
    prerequisites: list[Text]
    catalog_ref: Text
    requirement_status: Literal["illustrative"]
    requirement_source_ids: SourceIds
    learning_source_ids: list[Text]


class ExplanationInput(ContractModel):
    schema_version: Literal["1.0"]
    target_career: Text
    rating_basis: Literal["self_reported"]
    calculated_gaps: Annotated[list[CalculatedGap], Field(min_length=1, max_length=30)]
    approved_sources: Annotated[list[ApprovedSource], Field(min_length=1, max_length=4)]
    limitations: Annotated[list[Text], Field(min_length=1)]


class SourcedText(ContractModel):
    text: Text
    source_ids: SourceIds


class SkillExplanation(ContractModel):
    skill: Text
    why_skill_matters: SourcedText
    learning_actions: Annotated[list[SourcedText], Field(max_length=3)]
    limitations: Annotated[list[Text], Field(min_length=1, max_length=6)]


class ExplanationDraft(ContractModel):
    """Only these fields may be authored by a future model or human."""

    schema_version: Literal["1.0"]
    items: Annotated[list[SkillExplanation], Field(min_length=1, max_length=30)]


class ExplainedGap(CalculatedGap):
    why_skill_matters: SourcedText
    learning_actions: Annotated[list[SourcedText], Field(max_length=3)]
    limitations: Annotated[list[Text], Field(min_length=1, max_length=6)]


class ExplainGapsResponse(ContractModel):
    schema_version: Literal["1.0"]
    target_career: Text
    explanation_origin: Literal["authored_example", "rule_based", "hosted_model"]
    gaps: Annotated[list[ExplainedGap], Field(min_length=1, max_length=30)]
    approved_sources: Annotated[list[ApprovedSource], Field(min_length=1, max_length=4)]
    limitations: Annotated[list[Text], Field(min_length=1)]


def prepare_explanation_input(request: ExplainGapsRequest | dict) -> ExplanationInput:
    """Recompute all gaps; never accept client-authored targets or evidence."""
    request = ExplainGapsRequest.model_validate(request)
    calculated = skill_gaps({
        "target_career": request.target_career, "skills": request.skills,
    })
    role = CAREERS[request.target_career]["skills"]
    items = []
    used_ids = {CATALOG_SOURCE_ID}
    for name, gap in calculated.items():
        detail = role[name]
        used_ids.update(detail["learning_source_ids"])
        items.append({
            "skill": name, **gap,
            "catalog_ref": f"reskilling/catalog.py::CAREERS[{request.target_career!r}]['skills'][{name!r}]",
            "requirement_status": detail["requirement_status"],
            "requirement_source_ids": list(detail["requirement_source_ids"]),
            "learning_source_ids": list(detail["learning_source_ids"]),
        })
    return ExplanationInput(
        schema_version="1.0", target_career=request.target_career,
        rating_basis="self_reported", calculated_gaps=items,
        approved_sources=[deepcopy(SOURCES[key]) for key in sorted(used_ids)],
        limitations=list(LIMITATIONS),
    )


def assemble_explanation(
    request: ExplainGapsRequest | dict,
    draft: ExplanationDraft | dict,
    *,
    origin: Literal["authored_example", "rule_based", "hosted_model"] = "authored_example",
) -> ExplainGapsResponse:
    """Validate scope/citations and merge prose with freshly computed numbers.

    This is a local contract utility, NOT proof that cited prose is factual.
    URLs resolve from the registry; explanatory drafts must not supply URLs.
    """
    context = prepare_explanation_input(request)
    draft = ExplanationDraft.model_validate(draft)
    names = [item.skill for item in draft.items]
    expected = {gap.skill for gap in context.calculated_gaps}
    if len(names) != len(set(names)) or set(names) != expected:
        raise ValueError("Explain every calculated skill exactly once, including zero gaps.")
    by_skill = {item.skill: item for item in draft.items}
    explained = []
    for gap in context.calculated_gaps:
        item = by_skill[gap.skill]
        allowed = set(gap.requirement_source_ids + gap.learning_source_ids)
        if gap.gap > 0 and not item.learning_actions:
            raise ValueError("A positive gap requires at least one learning action.")
        texts = [
            item.why_skill_matters.text,
            *(action.text for action in item.learning_actions),
            *item.limitations,
        ]
        if any(
            marker in text.lower()
            for text in texts for marker in ("http://", "https://", "www.")
        ):
            raise ValueError("Use approved source IDs, not URLs in drafted text.")
        for passage in [item.why_skill_matters, *item.learning_actions]:
            if len(passage.source_ids) != len(set(passage.source_ids)):
                raise ValueError("Duplicate source IDs are not allowed.")
            if not set(passage.source_ids) <= allowed:
                raise ValueError(f"Source is not approved for {gap.skill}.")
        if CATALOG_SOURCE_ID not in item.why_skill_matters.source_ids:
            raise ValueError("Pathway relevance must cite its illustrative catalogue basis.")
        explained.append(ExplainedGap(
            **gap.model_dump(),
            **item.model_dump(exclude={"skill"}),
        ))
    return ExplainGapsResponse(
        schema_version="1.0", target_career=context.target_career,
        explanation_origin=origin, gaps=explained,
        approved_sources=context.approved_sources, limitations=context.limitations,
    )


def contract_schemas() -> dict:
    """Export standalone JSON Schemas without network or filesystem access."""
    return {
        "request": ExplainGapsRequest.model_json_schema(),
        "prepared_input": ExplanationInput.model_json_schema(),
        "explanation_draft": ExplanationDraft.model_json_schema(),
        "response": ExplainGapsResponse.model_json_schema(),
    }
