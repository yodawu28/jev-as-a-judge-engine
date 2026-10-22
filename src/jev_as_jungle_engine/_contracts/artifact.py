"""Decision artifact contract models."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal, Self

from pydantic import Field, field_serializer, field_validator, model_validator

from .base import ArtifactIdStr, NonEmptyStr, SemanticVersionStr, _StrictFrozenModel

FAITHFULNESS_ANSWER_OPTIONS = (
    "SUPPORTED",
    "UNSUPPORTED",
    "CONTRADICTS",
    "INSUFFICIENT_CONTEXT",
)
SUPPORTED_DECISION_ACTIONS = (
    "ALLOW",
    "FLAG_HALLUCINATION",
    "RETRY_WITH_CONTEXT",
    "SEND_TO_HUMAN_REVIEW",
)


class BackendBinding(_StrictFrozenModel):
    backend_id: NonEmptyStr
    backend_type: Literal["DETERMINISTIC_RULES", "FIXTURE_REPLAY"]


class ArtifactQuestion(_StrictFrozenModel):
    question_id: NonEmptyStr
    question_type: Literal["SINGLE_CHOICE"]
    prompt: NonEmptyStr
    answer_options: tuple[
        Literal[
            "SUPPORTED",
            "UNSUPPORTED",
            "CONTRADICTS",
            "INSUFFICIENT_CONTEXT",
        ],
        ...,
    ] = Field(min_length=1)

    @field_validator("answer_options", mode="before")
    @classmethod
    def _freeze_answer_options(cls, value: object) -> object:
        if isinstance(value, list):
            return tuple(value)
        return value

    @field_validator("answer_options", mode="after")
    @classmethod
    def _require_fixed_answer_options(
        cls,
        value: tuple[
            Literal[
                "SUPPORTED",
                "UNSUPPORTED",
                "CONTRADICTS",
                "INSUFFICIENT_CONTEXT",
            ],
            ...,
        ],
    ) -> tuple[
        Literal[
            "SUPPORTED",
            "UNSUPPORTED",
            "CONTRADICTS",
            "INSUFFICIENT_CONTEXT",
        ],
        ...,
    ]:
        if value != FAITHFULNESS_ANSWER_OPTIONS:
            msg = "answer_options must match the fixed faithfulness v0 option set"
            raise ValueError(msg)
        return value


class DecisionArtifact(_StrictFrozenModel):
    artifact_id: ArtifactIdStr
    artifact_version: SemanticVersionStr
    description: NonEmptyStr
    metric: Literal["context_grounded_faithfulness"]
    input_schema_version: Literal["decision-input/v0"]
    output_schema_version: Literal["decision-output/v0"]
    supported_task_types: tuple[Literal["RAG_QUESTION_ANSWERING"], ...] = Field(
        min_length=1
    )
    backend_binding: BackendBinding
    questions: tuple[ArtifactQuestion, ...] = Field(min_length=1)
    combiner: Literal["faithfulness_v0_rule"]
    actions: tuple[
        Literal[
            "ALLOW",
            "FLAG_HALLUCINATION",
            "RETRY_WITH_CONTEXT",
            "SEND_TO_HUMAN_REVIEW",
        ],
        ...,
    ] = Field(min_length=1)
    evaluation_report_ref: NonEmptyStr | None = None
    extensions: Mapping[str, object] = Field(default_factory=dict)

    @field_validator("supported_task_types", "questions", "actions", mode="before")
    @classmethod
    def _freeze_sequence_fields(cls, value: object) -> object:
        if isinstance(value, list):
            return tuple(value)
        return value

    @field_validator("supported_task_types", mode="after")
    @classmethod
    def _require_supported_task_types(
        cls, value: tuple[Literal["RAG_QUESTION_ANSWERING"], ...]
    ) -> tuple[Literal["RAG_QUESTION_ANSWERING"], ...]:
        if value != ("RAG_QUESTION_ANSWERING",):
            msg = "supported_task_types must only contain RAG_QUESTION_ANSWERING"
            raise ValueError(msg)
        return value

    @field_validator("actions", mode="after")
    @classmethod
    def _require_supported_actions(
        cls,
        value: tuple[
            Literal[
                "ALLOW",
                "FLAG_HALLUCINATION",
                "RETRY_WITH_CONTEXT",
                "SEND_TO_HUMAN_REVIEW",
            ],
            ...,
        ],
    ) -> tuple[
        Literal[
            "ALLOW",
            "FLAG_HALLUCINATION",
            "RETRY_WITH_CONTEXT",
            "SEND_TO_HUMAN_REVIEW",
        ],
        ...,
    ]:
        if value != SUPPORTED_DECISION_ACTIONS:
            msg = "actions must match the fixed decision output action set"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _require_consistent_artifact_contract(self) -> Self:
        if not self.artifact_id.endswith(f"-v{self.artifact_version}"):
            msg = "artifact_id version suffix must match artifact_version"
            raise ValueError(msg)

        question_ids = [question.question_id for question in self.questions]
        if len(question_ids) != len(set(question_ids)):
            msg = "question_id values must be unique"
            raise ValueError(msg)

        return self

    @field_validator("extensions", mode="after")
    @classmethod
    def _freeze_extensions(cls, value: Mapping[str, object]) -> Mapping[str, object]:
        return MappingProxyType(dict(value))

    @field_serializer("extensions")
    def _serialize_extensions(self, value: Mapping[str, object]) -> dict[str, object]:
        return dict(value)
