import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from jev_as_jungle_engine.contracts import DecisionArtifact

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "faithfulness-v0.1.0.json"


def load_artifact_file(path: Path) -> DecisionArtifact:
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    return DecisionArtifact.model_validate(payload)


def test_canonical_faithfulness_artifact_fixture_validates() -> None:
    artifact = load_artifact_file(CANONICAL_ARTIFACT_PATH)

    assert artifact.artifact_id == "faithfulness-v0.1.0"
    assert artifact.artifact_version == "0.1.0"
    assert artifact.description == (
        "Context-grounded faithfulness artifact for RAG question answering."
    )
    assert artifact.metric == "context_grounded_faithfulness"
    assert artifact.input_schema_version == "decision-input/v0"
    assert artifact.output_schema_version == "decision-output/v0"
    assert artifact.supported_task_types == ("RAG_QUESTION_ANSWERING",)
    assert artifact.backend_binding.backend_id == "deterministic-rules-v0"
    assert artifact.backend_binding.backend_type == "DETERMINISTIC_RULES"
    assert tuple(question.question_id for question in artifact.questions) == (
        "faithfulness.support",
        "faithfulness.contradiction",
        "faithfulness.insufficient_context",
    )
    assert artifact.combiner == "faithfulness_v0_rule"
    assert artifact.actions == (
        "ALLOW",
        "FLAG_HALLUCINATION",
        "RETRY_WITH_CONTEXT",
        "SEND_TO_HUMAN_REVIEW",
    )
    assert artifact.evaluation_report_ref == "reports/faithfulness-v0.1.0.json"


def test_malformed_faithfulness_artifact_fixture_fails_closed(tmp_path: Path) -> None:
    malformed_artifact_path = tmp_path / "faithfulness-v0.1.0.json"
    malformed_artifact_path.write_text(
        json.dumps(
            {
                "artifact_id": "faithfulness-v0.1.0",
                "artifact_version": "0.1.0",
                "description": (
                    "Context-grounded faithfulness artifact for RAG question answering."
                ),
                "metric": "context_grounded_faithfulness",
                "input_schema_version": "decision-input/v0",
                "output_schema_version": "decision-output/v0",
                "supported_task_types": ["RAG_QUESTION_ANSWERING"],
                "backend_binding": {
                    "backend_id": "deterministic-rules-v0",
                    "backend_type": "DETERMINISTIC_RULES",
                },
                "questions": [],
                "combiner": "faithfulness_v0_rule",
                "actions": [
                    "ALLOW",
                    "FLAG_HALLUCINATION",
                    "RETRY_WITH_CONTEXT",
                    "SEND_TO_HUMAN_REVIEW",
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_artifact_file(malformed_artifact_path)
