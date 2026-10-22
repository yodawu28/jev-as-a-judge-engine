import json
from pathlib import Path

from jev_as_jungle_engine.contracts import DecisionInput, DecisionOutput

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_FIXTURE_DIR = REPO_ROOT / "artifacts" / "golden" / "faithfulness-v0.1.0"

EXPECTED_CASES = {
    "pass_supported.json": {
        "case_id": "pass_supported",
        "verdict": "PASS",
        "failure_type": "NONE",
        "suggested_action": "ALLOW",
        "evidence_relationship": "SUPPORTS",
    },
    "contradicts_context.json": {
        "case_id": "contradicts_context",
        "verdict": "FAIL",
        "failure_type": "CONTRADICTS_CONTEXT",
        "suggested_action": "FLAG_HALLUCINATION",
        "evidence_relationship": "CONTRADICTS",
    },
    "unsupported_by_context.json": {
        "case_id": "unsupported_by_context",
        "verdict": "FAIL",
        "failure_type": "UNSUPPORTED_BY_CONTEXT",
        "suggested_action": "FLAG_HALLUCINATION",
        "evidence_relationship": "INSUFFICIENT",
    },
    "missing_answer.json": {
        "case_id": "missing_answer",
        "verdict": "FAIL",
        "failure_type": "MISSING_ANSWER",
        "suggested_action": "RETRY_WITH_CONTEXT",
        "evidence_relationship": "RELATED",
    },
    "insufficient_context.json": {
        "case_id": "insufficient_context",
        "verdict": "FAIL",
        "failure_type": "INSUFFICIENT_CONTEXT",
        "suggested_action": "SEND_TO_HUMAN_REVIEW",
        "evidence_relationship": "INSUFFICIENT",
    },
}


def load_fixture(path: Path) -> tuple[str, DecisionInput, DecisionOutput]:
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert set(payload) == {"case_id", "input", "expected_output"}

    case_id = payload["case_id"]
    assert isinstance(case_id, str)

    return (
        case_id,
        DecisionInput.model_validate(payload["input"]),
        DecisionOutput.model_validate(payload["expected_output"]),
    )


def test_golden_faithfulness_fixture_set_is_complete() -> None:
    fixture_names = {path.name for path in GOLDEN_FIXTURE_DIR.glob("*.json")}

    assert fixture_names == set(EXPECTED_CASES)


def test_golden_faithfulness_fixtures_validate_expected_behavior() -> None:
    for fixture_name, expected in EXPECTED_CASES.items():
        case_id, decision_input, decision_output = load_fixture(
            GOLDEN_FIXTURE_DIR / fixture_name
        )
        context_chunk_ids = {
            chunk.chunk_id for chunk in decision_input.provided_context
        }
        evidence_relationships = {
            evidence.relationship for evidence in decision_output.evidence
        }

        assert case_id == expected["case_id"]
        assert decision_input.task_type == "RAG_QUESTION_ANSWERING"
        assert decision_output.trace_id == decision_input.trace_id
        assert decision_output.artifact_id == "faithfulness-v0.1.0"
        assert decision_output.verdict == expected["verdict"]
        assert decision_output.failure_type == expected["failure_type"]
        assert decision_output.suggested_action == expected["suggested_action"]
        assert evidence_relationships == {expected["evidence_relationship"]}
        assert {evidence.chunk_id for evidence in decision_output.evidence}.issubset(
            context_chunk_ids
        )
        assert all(
            chunk.source is not None and chunk.source.startswith("synthetic://")
            for chunk in decision_input.provided_context
        )
