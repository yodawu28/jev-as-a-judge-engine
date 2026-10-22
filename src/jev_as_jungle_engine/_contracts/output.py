"""Decision output contract models."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal, Self

from pydantic import (
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    field_serializer,
    field_validator,
    model_validator,
)

from .base import BoundedScore, NonEmptyStr, _StrictFrozenModel

_BOUNDED_SCORE_ADAPTER = TypeAdapter(BoundedScore)


class DecisionScores(_StrictFrozenModel):
    model_config = ConfigDict(extra="allow", frozen=True, strict=True)

    faithfulness: BoundedScore

    @model_validator(mode="after")
    def _validate_extra_scores(self) -> Self:
        for name, value in (self.model_extra or {}).items():
            try:
                _BOUNDED_SCORE_ADAPTER.validate_python(value, strict=True)
            except ValidationError as exc:
                msg = f"extra score {name!r} must be between 0.0 and 1.0"
                raise ValueError(msg) from exc
        return self


class EvidenceReference(_StrictFrozenModel):
    chunk_id: NonEmptyStr
    relationship: Literal["SUPPORTS", "CONTRADICTS", "RELATED", "INSUFFICIENT"]
    note: NonEmptyStr | None = None


class DecisionOutput(_StrictFrozenModel):
    schema_version: Literal["decision-output/v0"]
    trace_id: NonEmptyStr
    artifact_id: NonEmptyStr
    verdict: Literal["PASS", "FAIL", "NEEDS_REVIEW"]
    failure_type: Literal[
        "NONE",
        "CONTRADICTS_CONTEXT",
        "UNSUPPORTED_BY_CONTEXT",
        "MISSING_ANSWER",
        "INSUFFICIENT_CONTEXT",
    ]
    confidence: BoundedScore
    scores: DecisionScores
    suggested_action: Literal[
        "ALLOW",
        "FLAG_HALLUCINATION",
        "RETRY_WITH_CONTEXT",
        "SEND_TO_HUMAN_REVIEW",
    ]
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1)
    reasoning: NonEmptyStr
    extensions: Mapping[str, object] = Field(default_factory=dict)

    @field_validator("evidence", mode="before")
    @classmethod
    def _freeze_evidence(cls, value: object) -> object:
        if isinstance(value, list):
            return tuple(value)
        return value

    @field_validator("extensions", mode="after")
    @classmethod
    def _freeze_extensions(cls, value: Mapping[str, object]) -> Mapping[str, object]:
        return MappingProxyType(dict(value))

    @field_serializer("extensions")
    def _serialize_extensions(self, value: Mapping[str, object]) -> dict[str, object]:
        return dict(value)
