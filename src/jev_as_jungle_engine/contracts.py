"""Strict v0 decision contracts for Jev-as-Jungle Engine."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
    field_validator,
)

type NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
type BoundedScore = Annotated[float, Field(ge=0.0, le=1.0)]


class _StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ContextChunk(_StrictFrozenModel):
    chunk_id: NonEmptyStr
    text: NonEmptyStr
    source: NonEmptyStr | None = None


class DecisionScores(_StrictFrozenModel):
    model_config = ConfigDict(extra="allow", frozen=True, strict=True)

    __pydantic_extra__: dict[str, BoundedScore] = Field(init=False)

    faithfulness: BoundedScore


class EvidenceReference(_StrictFrozenModel):
    chunk_id: NonEmptyStr
    relationship: Literal["SUPPORTS", "CONTRADICTS", "RELATED", "INSUFFICIENT"]
    note: NonEmptyStr | None = None


class DecisionInput(_StrictFrozenModel):
    schema_version: Literal["decision-input/v0"]
    trace_id: NonEmptyStr
    task_type: Literal["RAG_QUESTION_ANSWERING"]
    user_prompt: NonEmptyStr
    provided_context: tuple[ContextChunk, ...] = Field(min_length=1)
    agent_response: NonEmptyStr
    extensions: Mapping[str, object] = Field(default_factory=dict)

    @field_validator("provided_context", mode="before")
    @classmethod
    def _freeze_context(cls, value: object) -> object:
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
