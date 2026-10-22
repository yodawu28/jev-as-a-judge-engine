import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import jev_as_jungle_engine as engine
from jev_as_jungle_engine.contracts import (
    DecisionArtifact,
    DecisionInput,
    DecisionOutput,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "faithfulness-v0.1.0.json"


def valid_decision_input() -> DecisionInput:
    return DecisionInput.model_validate(
        {
            "schema_version": "decision-input/v0",
            "trace_id": "tr-core-001",
            "task_type": "RAG_QUESTION_ANSWERING",
            "user_prompt": "Which refund window applies?",
            "provided_context": [
                {
                    "chunk_id": "ctx-policy",
                    "text": "Refunds are available within 7 days of signup.",
                    "source": "policy.md",
                }
            ],
            "agent_response": "Refunds are available within 7 days of signup.",
        }
    )


def canonical_artifact() -> DecisionArtifact:
    payload: object = json.loads(CANONICAL_ARTIFACT_PATH.read_text(encoding="utf-8"))
    return DecisionArtifact.model_validate(payload)


def valid_decision_output_payload() -> dict[str, object]:
    return {
        "schema_version": "decision-output/v0",
        "trace_id": "tr-core-001",
        "artifact_id": "faithfulness-v0.1.0",
        "verdict": "PASS",
        "failure_type": "NONE",
        "confidence": 1.0,
        "scores": {"faithfulness": 1.0},
        "suggested_action": "ALLOW",
        "evidence": [
            {
                "chunk_id": "ctx-policy",
                "relationship": "SUPPORTS",
                "note": "The response is directly supported by the policy chunk.",
            }
        ],
        "reasoning": "The response repeats the supported refund window.",
    }


class RecordingBackend:
    backend_id = "deterministic-rules-v0"
    backend_type = "DETERMINISTIC_RULES"

    def __init__(self, output: object | None = None) -> None:
        self.calls: list[tuple[DecisionInput, DecisionArtifact]] = []
        self.output = output or DecisionOutput.model_validate(valid_decision_output_payload())

    def evaluate(
        self, decision_input: DecisionInput, artifact: DecisionArtifact
    ) -> object:
        self.calls.append((decision_input, artifact))
        return self.output


def test_evaluation_core_exports_backend_contract_surface() -> None:
    assert getattr(engine, "DecisionBackend", None) is not None
    assert callable(getattr(engine, "evaluate_decision", None))


def test_evaluate_decision_invokes_backend_once_and_returns_valid_output() -> None:
    decision_input = valid_decision_input()
    artifact = canonical_artifact()
    backend = RecordingBackend()

    decision = engine.evaluate_decision(decision_input, artifact, backend)

    assert decision == DecisionOutput.model_validate(valid_decision_output_payload())
    assert backend.calls == [(decision_input, artifact)]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("metric", "schema_compliance"),
        ("input_schema_version", "decision-input/v1"),
        ("output_schema_version", "decision-output/v1"),
        ("combiner", "unknown_rule"),
    ],
)
def test_evaluate_decision_rejects_unsupported_artifact_contract_before_backend_call(
    field: str, value: str
) -> None:
    artifact = canonical_artifact().model_copy(update={field: value})
    backend = RecordingBackend()

    with pytest.raises(ValueError, match=field):
        engine.evaluate_decision(valid_decision_input(), artifact, backend)

    assert backend.calls == []


def test_evaluate_decision_rejects_unsupported_task_type_before_backend_call() -> None:
    decision_input = valid_decision_input().model_copy(update={"task_type": "CHAT"})
    backend = RecordingBackend()

    with pytest.raises(ValueError, match="task_type"):
        engine.evaluate_decision(decision_input, canonical_artifact(), backend)

    assert backend.calls == []


def test_evaluate_decision_rejects_backend_binding_mismatch_before_backend_call() -> None:
    backend = RecordingBackend()
    backend.backend_id = "fixture-replay-v0"

    with pytest.raises(ValueError, match="backend_binding"):
        engine.evaluate_decision(valid_decision_input(), canonical_artifact(), backend)

    assert backend.calls == []


def test_evaluate_decision_rejects_malformed_backend_output() -> None:
    malformed_output: dict[str, Any] = valid_decision_output_payload()
    del malformed_output["evidence"]
    backend = RecordingBackend(output=malformed_output)

    with pytest.raises(ValidationError):
        engine.evaluate_decision(valid_decision_input(), canonical_artifact(), backend)

    assert len(backend.calls) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("trace_id", "tr-other"),
        ("artifact_id", "faithfulness-v9.9.9"),
    ],
)
def test_evaluate_decision_rejects_backend_output_correlation_mismatch(
    field: str, value: str
) -> None:
    mismatched_output = valid_decision_output_payload()
    mismatched_output[field] = value
    backend = RecordingBackend(output=DecisionOutput.model_validate(mismatched_output))

    with pytest.raises(ValueError, match=field):
        engine.evaluate_decision(valid_decision_input(), canonical_artifact(), backend)

    assert len(backend.calls) == 1
