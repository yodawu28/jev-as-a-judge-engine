import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from jev_as_jungle_engine import contracts

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "faithfulness-v0.1.0.json"


def valid_decision_input_payload() -> dict[str, object]:
    return {
        "schema_version": "decision-input/v0",
        "trace_id": "tr-round-trip-input",
        "task_type": "RAG_QUESTION_ANSWERING",
        "user_prompt": "What is the refund policy?",
        "provided_context": [
            {
                "chunk_id": "ctx-001",
                "text": "Refunds are available within 7 days of signup.",
                "source": "policy.md",
            }
        ],
        "agent_response": "Refunds are available within 7 days of signup.",
        "extensions": {"fixture": "round-trip-input"},
    }


def valid_decision_output_payload() -> dict[str, object]:
    return {
        "schema_version": "decision-output/v0",
        "trace_id": "tr-round-trip-output",
        "artifact_id": "faithfulness-v0.1.0",
        "verdict": "PASS",
        "failure_type": "NONE",
        "confidence": 0.97,
        "scores": {"faithfulness": 1.0, "correctness": 0.9},
        "suggested_action": "ALLOW",
        "evidence": [
            {
                "chunk_id": "ctx-001",
                "relationship": "SUPPORTS",
                "note": "The response matches the referenced context.",
            }
        ],
        "reasoning": "The response is grounded in the referenced context.",
        "extensions": {"fixture": "round-trip-output"},
    }


def test_parse_and_serialize_decision_input_json_round_trip() -> None:
    payload = valid_decision_input_payload()

    decision_input = contracts.parse_decision_input_json(json.dumps(payload))

    assert isinstance(decision_input, contracts.DecisionInput)
    assert contracts.serialize_contract(decision_input) == payload


def test_parse_and_serialize_decision_output_json_round_trip() -> None:
    payload = valid_decision_output_payload()

    decision_output = contracts.parse_decision_output_json(json.dumps(payload))

    assert isinstance(decision_output, contracts.DecisionOutput)
    assert contracts.serialize_contract(decision_output) == payload


def test_parse_and_serialize_decision_artifact_json_round_trip() -> None:
    payload: dict[str, object] = json.loads(CANONICAL_ARTIFACT_PATH.read_text(encoding="utf-8"))

    decision_artifact = contracts.parse_decision_artifact_json(json.dumps(payload))

    assert isinstance(decision_artifact, contracts.DecisionArtifact)
    assert contracts.serialize_contract(decision_artifact) == payload


@pytest.mark.parametrize(
    "parser_name",
    [
        "parse_decision_input_json",
        "parse_decision_output_json",
        "parse_decision_artifact_json",
    ],
)
def test_contract_json_parsers_fail_closed_on_invalid_json(parser_name: str) -> None:
    parser = getattr(contracts, parser_name)

    with pytest.raises(ValidationError):
        parser("{")


def test_contract_json_parser_fails_closed_on_schema_mismatch() -> None:
    output_json = json.dumps(valid_decision_output_payload())

    with pytest.raises(ValidationError):
        contracts.parse_decision_input_json(output_json)


def test_contract_helpers_avoid_static_analyzer_hostile_pydantic_patterns() -> None:
    source = inspect.getsource(contracts)

    assert "type DecisionContract =" not in source
    assert "model_validate_json" not in source
