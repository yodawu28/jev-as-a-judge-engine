"""Public facade for strict v0 decision contracts."""

from ._contracts.artifact import (
    FAITHFULNESS_ANSWER_OPTIONS,
    SUPPORTED_DECISION_ACTIONS,
    ArtifactQuestion,
    BackendBinding,
    DecisionArtifact,
)
from ._contracts.base import ArtifactIdStr, BoundedScore, NonEmptyStr, SemanticVersionStr
from ._contracts.input import ContextChunk, DecisionInput
from ._contracts.output import DecisionOutput, DecisionScores, EvidenceReference
from ._contracts.serialization import (
    parse_decision_artifact_json,
    parse_decision_input_json,
    parse_decision_output_json,
    serialize_contract,
)

__all__ = (
    "FAITHFULNESS_ANSWER_OPTIONS",
    "SUPPORTED_DECISION_ACTIONS",
    "ArtifactIdStr",
    "ArtifactQuestion",
    "BackendBinding",
    "BoundedScore",
    "ContextChunk",
    "DecisionArtifact",
    "DecisionInput",
    "DecisionOutput",
    "DecisionScores",
    "EvidenceReference",
    "NonEmptyStr",
    "SemanticVersionStr",
    "parse_decision_artifact_json",
    "parse_decision_input_json",
    "parse_decision_output_json",
    "serialize_contract",
)
