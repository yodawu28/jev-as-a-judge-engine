import json
from typing import Any, cast

import pytest
from pydantic import ValidationError

from jev_as_jungle_engine.contracts import DecisionOutput, DecisionScores, EvidenceReference


def valid_decision_output_payload() -> dict[str, object]:
    return {
        "schema_version": "decision-output/v0",
        "trace_id": "tr-001",
        "artifact_id": "faithfulness-v0.1.0",
        "verdict": "FAIL",
        "failure_type": "CONTRADICTS_CONTEXT",
        "confidence": 0.92,
        "scores": {"faithfulness": 0.0},
        "suggested_action": "FLAG_HALLUCINATION",
        "evidence": [
            {
                "chunk_id": "ctx-001",
                "relationship": "CONTRADICTS",
                "note": "The response conflicts with the referenced context.",
            }
        ],
        "reasoning": "The response says 30 days while the referenced context says 7 days.",
        "extensions": {"fixture": "contradiction"},
    }


def test_decision_output_accepts_structured_faithfulness_verdict() -> None:
    decision_output = DecisionOutput.model_validate(valid_decision_output_payload())

    assert decision_output.schema_version == "decision-output/v0"
    assert decision_output.trace_id == "tr-001"
    assert decision_output.artifact_id == "faithfulness-v0.1.0"
    assert decision_output.verdict == "FAIL"
    assert decision_output.failure_type == "CONTRADICTS_CONTEXT"
    assert decision_output.confidence == 0.92
    assert decision_output.scores == DecisionScores(faithfulness=0.0)
    assert decision_output.suggested_action == "FLAG_HALLUCINATION"
    assert decision_output.evidence == (
        EvidenceReference(
            chunk_id="ctx-001",
            relationship="CONTRADICTS",
            note="The response conflicts with the referenced context.",
        ),
    )


def test_decision_output_accepts_additional_bounded_scores() -> None:
    payload = valid_decision_output_payload()
    payload["scores"] = {"faithfulness": 1.0, "correctness": 0.75, "safety": 1.0}

    decision_output = DecisionOutput.model_validate(payload)
    serialized = json.loads(decision_output.model_dump_json())

    assert serialized["scores"] == {"faithfulness": 1.0, "correctness": 0.75, "safety": 1.0}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "decision-output/v1"),
        ("verdict", "MAYBE"),
        ("failure_type", "BAD_CONTEXT"),
        ("suggested_action", "DELETE_USER"),
    ],
)
def test_decision_output_rejects_unsupported_contract_values(field: str, value: str) -> None:
    payload = valid_decision_output_payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        DecisionOutput.model_validate(payload)


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_decision_output_rejects_out_of_range_confidence(confidence: float) -> None:
    payload = valid_decision_output_payload()
    payload["confidence"] = confidence

    with pytest.raises(ValidationError):
        DecisionOutput.model_validate(payload)


@pytest.mark.parametrize("faithfulness", [-0.01, 1.01])
def test_decision_output_rejects_out_of_range_faithfulness_score(
    faithfulness: float,
) -> None:
    payload = valid_decision_output_payload()
    payload["scores"] = {"faithfulness": faithfulness}

    with pytest.raises(ValidationError):
        DecisionOutput.model_validate(payload)


@pytest.mark.parametrize(
    "scores",
    [
        {},
        {"correctness": 1.0},
        {"faithfulness": 1.0, "correctness": 1.01},
        {"faithfulness": 1.0, "safety": -0.01},
    ],
)
def test_decision_output_rejects_malformed_scores(scores: dict[str, float]) -> None:
    payload = valid_decision_output_payload()
    payload["scores"] = scores

    with pytest.raises(ValidationError):
        DecisionOutput.model_validate(payload)


@pytest.mark.parametrize(
    "evidence",
    [
        [],
        [{"relationship": "SUPPORTS"}],
        [{"chunk_id": "ctx-001"}],
        [{"chunk_id": "", "relationship": "SUPPORTS"}],
        [{"chunk_id": "ctx-001", "relationship": "UNKNOWN"}],
        [{"chunk_id": "ctx-001", "relationship": "SUPPORTS", "extra": "nope"}],
    ],
)
def test_decision_output_rejects_missing_or_malformed_evidence(
    evidence: list[dict[str, str]],
) -> None:
    payload = valid_decision_output_payload()
    payload["evidence"] = evidence

    with pytest.raises(ValidationError):
        DecisionOutput.model_validate(payload)


@pytest.mark.parametrize("field", ["trace_id", "artifact_id", "reasoning"])
def test_decision_output_rejects_missing_required_text_fields(field: str) -> None:
    payload = valid_decision_output_payload()
    del payload[field]

    with pytest.raises(ValidationError):
        DecisionOutput.model_validate(payload)


def test_decision_output_rejects_extra_fields_and_is_immutable() -> None:
    payload = valid_decision_output_payload()
    payload["unexpected"] = "fail closed"

    with pytest.raises(ValidationError):
        DecisionOutput.model_validate(payload)

    decision_output = DecisionOutput.model_validate(valid_decision_output_payload())

    with pytest.raises(ValidationError):
        decision_output.trace_id = "tr-mutated"

    with pytest.raises(AttributeError):
        cast(Any, decision_output.evidence).append(
            EvidenceReference(chunk_id="ctx-002", relationship="RELATED")
        )

    with pytest.raises(TypeError):
        cast(Any, decision_output.extensions)["fixture"] = "mutated"


def test_decision_output_serializes_extensions_after_freezing() -> None:
    decision_output = DecisionOutput.model_validate(valid_decision_output_payload())

    serialized = json.loads(decision_output.model_dump_json())

    assert serialized["extensions"] == {"fixture": "contradiction"}
