"""Strict v0 decision contracts for Jev-as-Jungle Engine."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Annotated, Literal, Self, overload

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    field_serializer,
    field_validator,
    model_validator,
)

type NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
type ArtifactIdStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[a-z][a-z0-9-]*-v\d+\.\d+\.\d+$",
    ),
]
type SemanticVersionStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^\d+\.\d+\.\d+$"),
]
type BoundedScore = Annotated[float, Field(ge=0.0, le=1.0)]

_BOUNDED_SCORE_ADAPTER = TypeAdapter(BoundedScore)

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


class _StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ContextChunk(_StrictFrozenModel):
    chunk_id: NonEmptyStr
    text: NonEmptyStr
    source: NonEmptyStr | None = None


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

_DECISION_INPUT_JSON_ADAPTER: TypeAdapter[DecisionInput] = TypeAdapter(DecisionInput)
_DECISION_OUTPUT_JSON_ADAPTER: TypeAdapter[DecisionOutput] = TypeAdapter(DecisionOutput)
_DECISION_ARTIFACT_JSON_ADAPTER: TypeAdapter[DecisionArtifact] = TypeAdapter(
    DecisionArtifact
)


def parse_decision_input_json(json_text: str) -> DecisionInput:
    return _DECISION_INPUT_JSON_ADAPTER.validate_json(json_text)


def parse_decision_output_json(json_text: str) -> DecisionOutput:
    return _DECISION_OUTPUT_JSON_ADAPTER.validate_json(json_text)


def parse_decision_artifact_json(json_text: str) -> DecisionArtifact:
    return _DECISION_ARTIFACT_JSON_ADAPTER.validate_json(json_text)


@overload
def serialize_contract(contract: DecisionInput) -> dict[str, object]: ...


@overload
def serialize_contract(contract: DecisionOutput) -> dict[str, object]: ...


@overload
def serialize_contract(contract: DecisionArtifact) -> dict[str, object]: ...


def serialize_contract(contract: BaseModel) -> dict[str, object]:
    return contract.model_dump(mode="json")
