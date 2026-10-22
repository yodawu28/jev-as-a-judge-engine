"""Decision input contract models."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

from pydantic import Field, field_serializer, field_validator

from .base import NonEmptyStr, _StrictFrozenModel


class ContextChunk(_StrictFrozenModel):
    chunk_id: NonEmptyStr
    text: NonEmptyStr
    source: NonEmptyStr | None = None


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
