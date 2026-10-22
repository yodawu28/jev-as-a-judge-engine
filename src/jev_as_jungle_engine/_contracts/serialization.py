"""JSON parsing and stable serialization helpers for decision contracts."""

from typing import overload

from pydantic import BaseModel, TypeAdapter

from .artifact import DecisionArtifact
from .input import DecisionInput
from .output import DecisionOutput

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
