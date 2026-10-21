import json
from typing import Any, Literal, cast

import pytest
from pydantic import ValidationError

from jev_as_jungle_engine import contracts

AnswerOption = Literal[
    "SUPPORTED",
    "UNSUPPORTED",
    "CONTRADICTS",
    "INSUFFICIENT_CONTEXT",
]
SupportedAction = Literal[
    "ALLOW",
    "FLAG_HALLUCINATION",
    "RETRY_WITH_CONTEXT",
    "SEND_TO_HUMAN_REVIEW",
]

ANSWER_OPTIONS: tuple[AnswerOption, ...] = (
    "SUPPORTED",
    "UNSUPPORTED",
    "CONTRADICTS",
    "INSUFFICIENT_CONTEXT",
)

SUPPORTED_ACTIONS: tuple[SupportedAction, ...] = (
    "ALLOW",
    "FLAG_HALLUCINATION",
    "RETRY_WITH_CONTEXT",
    "SEND_TO_HUMAN_REVIEW",
)


def valid_decision_artifact_payload() -> dict[str, object]:
    return {
        "artifact_id": "faithfulness-v0.1.0",
        "artifact_version": "0.1.0",
        "description": "Context-grounded faithfulness artifact for RAG question answering.",
        "metric": "context_grounded_faithfulness",
        "input_schema_version": "decision-input/v0",
        "output_schema_version": "decision-output/v0",
        "supported_task_types": ["RAG_QUESTION_ANSWERING"],
        "backend_binding": {
            "backend_id": "deterministic-rules-v0",
            "backend_type": "DETERMINISTIC_RULES",
        },
        "questions": [
            {
                "question_id": "faithfulness.support",
                "question_type": "SINGLE_CHOICE",
                "prompt": "Is the response fully supported by the provided context?",
                "answer_options": list(ANSWER_OPTIONS),
            }
        ],
        "combiner": "faithfulness_v0_rule",
        "actions": list(SUPPORTED_ACTIONS),
        "evaluation_report_ref": "reports/faithfulness-v0.1.0.json",
        "extensions": {"fixture": "artifact-contract"},
    }


def test_decision_artifact_accepts_context_grounded_faithfulness_contract() -> None:
    decision_artifact = contracts.DecisionArtifact.model_validate(
        valid_decision_artifact_payload()
    )

    assert decision_artifact.artifact_id == "faithfulness-v0.1.0"
    assert decision_artifact.artifact_version == "0.1.0"
    assert decision_artifact.metric == "context_grounded_faithfulness"
    assert decision_artifact.input_schema_version == "decision-input/v0"
    assert decision_artifact.output_schema_version == "decision-output/v0"
    assert decision_artifact.supported_task_types == ("RAG_QUESTION_ANSWERING",)
    assert decision_artifact.backend_binding == contracts.BackendBinding(
        backend_id="deterministic-rules-v0",
        backend_type="DETERMINISTIC_RULES",
    )
    assert decision_artifact.questions == (
        contracts.ArtifactQuestion(
            question_id="faithfulness.support",
            question_type="SINGLE_CHOICE",
            prompt="Is the response fully supported by the provided context?",
            answer_options=ANSWER_OPTIONS,
        ),
    )
    assert decision_artifact.combiner == "faithfulness_v0_rule"
    assert decision_artifact.actions == SUPPORTED_ACTIONS
    assert decision_artifact.evaluation_report_ref == "reports/faithfulness-v0.1.0.json"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("artifact_id", "faithfulness"),
        ("artifact_id", "Faithfulness-v0.1.0"),
        ("artifact_version", "v0.1.0"),
        ("artifact_version", "0.1"),
        ("metric", "schema_compliance"),
        ("input_schema_version", "decision-input/v1"),
        ("output_schema_version", "decision-output/v1"),
        ("combiner", "custom_rule_dsl"),
    ],
)
def test_decision_artifact_rejects_unsupported_contract_values(
    field: str, value: str
) -> None:
    payload = valid_decision_artifact_payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)


def test_decision_artifact_rejects_artifact_id_version_mismatch() -> None:
    payload = valid_decision_artifact_payload()
    payload["artifact_id"] = "faithfulness-v0.2.0"

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)


@pytest.mark.parametrize(
    "task_types",
    [
        [],
        ["SUMMARIZATION"],
        ["RAG_QUESTION_ANSWERING", "SUMMARIZATION"],
        ["RAG_QUESTION_ANSWERING", "RAG_QUESTION_ANSWERING"],
    ],
)
def test_decision_artifact_rejects_unsupported_task_type_sets(
    task_types: list[str],
) -> None:
    payload = valid_decision_artifact_payload()
    payload["supported_task_types"] = task_types

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)


@pytest.mark.parametrize(
    "backend_binding",
    [
        {"backend_type": "DETERMINISTIC_RULES"},
        {"backend_id": "deterministic-rules-v0"},
        {"backend_id": "", "backend_type": "DETERMINISTIC_RULES"},
        {"backend_id": "deterministic-rules-v0", "backend_type": "REMOTE_MODEL"},
        {
            "backend_id": "deterministic-rules-v0",
            "backend_type": "DETERMINISTIC_RULES",
            "extra": "nope",
        },
    ],
)
def test_decision_artifact_rejects_malformed_backend_bindings(
    backend_binding: dict[str, str],
) -> None:
    payload = valid_decision_artifact_payload()
    payload["backend_binding"] = backend_binding

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)


@pytest.mark.parametrize(
    "question",
    [
        {
            "question_type": "SINGLE_CHOICE",
            "prompt": "Missing id.",
            "answer_options": list(ANSWER_OPTIONS),
        },
        {
            "question_id": "faithfulness.support",
            "prompt": "Missing type.",
            "answer_options": list(ANSWER_OPTIONS),
        },
        {
            "question_id": "faithfulness.support",
            "question_type": "FREE_TEXT",
            "prompt": "Unsupported type.",
            "answer_options": list(ANSWER_OPTIONS),
        },
        {
            "question_id": "faithfulness.support",
            "question_type": "SINGLE_CHOICE",
            "answer_options": list(ANSWER_OPTIONS),
        },
        {
            "question_id": "faithfulness.support",
            "question_type": "SINGLE_CHOICE",
            "prompt": "Missing options.",
        },
        {
            "question_id": "faithfulness.support",
            "question_type": "SINGLE_CHOICE",
            "prompt": "Wrong option set.",
            "answer_options": ["SUPPORTED"],
        },
        {
            "question_id": "faithfulness.support",
            "question_type": "SINGLE_CHOICE",
            "prompt": "Duplicate option.",
            "answer_options": [
                "SUPPORTED",
                "UNSUPPORTED",
                "CONTRADICTS",
                "CONTRADICTS",
            ],
        },
        {
            "question_id": "faithfulness.support",
            "question_type": "SINGLE_CHOICE",
            "prompt": "Has extra field.",
            "answer_options": list(ANSWER_OPTIONS),
            "extra": "nope",
        },
    ],
)
def test_decision_artifact_rejects_malformed_questions(
    question: dict[str, object],
) -> None:
    payload = valid_decision_artifact_payload()
    payload["questions"] = [question]

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)


def test_decision_artifact_rejects_empty_question_list() -> None:
    payload = valid_decision_artifact_payload()
    payload["questions"] = []

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)


def test_decision_artifact_rejects_duplicate_question_ids() -> None:
    payload = valid_decision_artifact_payload()
    payload["questions"] = [
        {
            "question_id": "faithfulness.support",
            "question_type": "SINGLE_CHOICE",
            "prompt": "Is the response fully supported by the provided context?",
            "answer_options": list(ANSWER_OPTIONS),
        },
        {
            "question_id": "faithfulness.support",
            "question_type": "SINGLE_CHOICE",
            "prompt": "Does the response contradict the provided context?",
            "answer_options": list(ANSWER_OPTIONS),
        },
    ]

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)


@pytest.mark.parametrize(
    "actions",
    [
        [],
        ["ALLOW"],
        ["ALLOW", "FLAG_HALLUCINATION", "RETRY_WITH_CONTEXT", "DELETE_USER"],
        [
            "ALLOW",
            "FLAG_HALLUCINATION",
            "RETRY_WITH_CONTEXT",
            "SEND_TO_HUMAN_REVIEW",
            "ALLOW",
        ],
    ],
)
def test_decision_artifact_rejects_malformed_action_sets(actions: list[str]) -> None:
    payload = valid_decision_artifact_payload()
    payload["actions"] = actions

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)


def test_decision_artifact_allows_omitted_evaluation_report_ref() -> None:
    payload = valid_decision_artifact_payload()
    del payload["evaluation_report_ref"]

    decision_artifact = contracts.DecisionArtifact.model_validate(payload)

    assert decision_artifact.evaluation_report_ref is None


def test_decision_artifact_rejects_extra_fields_and_is_immutable() -> None:
    payload = valid_decision_artifact_payload()
    payload["unexpected"] = "fail closed"

    with pytest.raises(ValidationError):
        contracts.DecisionArtifact.model_validate(payload)

    decision_artifact = contracts.DecisionArtifact.model_validate(
        valid_decision_artifact_payload()
    )

    with pytest.raises(ValidationError):
        decision_artifact.artifact_id = "faithfulness-v0.2.0"

    with pytest.raises(AttributeError):
        cast(Any, decision_artifact.questions).append(
            contracts.ArtifactQuestion(
                question_id="faithfulness.extra",
                question_type="SINGLE_CHOICE",
                prompt="This should not be mutable.",
                answer_options=ANSWER_OPTIONS,
            )
        )

    with pytest.raises(TypeError):
        cast(Any, decision_artifact.extensions)["fixture"] = "mutated"


def test_decision_artifact_serializes_extensions_after_freezing() -> None:
    decision_artifact = contracts.DecisionArtifact.model_validate(
        valid_decision_artifact_payload()
    )

    serialized = json.loads(decision_artifact.model_dump_json())

    assert serialized["extensions"] == {"fixture": "artifact-contract"}
