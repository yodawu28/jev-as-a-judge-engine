import json
from typing import Any, cast

import pytest
from pydantic import ValidationError

from jev_as_jungle_engine.contracts import ContextChunk, DecisionInput


def valid_decision_input_payload() -> dict[str, object]:
    return {
        "schema_version": "decision-input/v0",
        "trace_id": "tr-001",
        "task_type": "RAG_QUESTION_ANSWERING",
        "user_prompt": "What is the refund policy?",
        "provided_context": [
            {
                "chunk_id": "ctx-001",
                "text": "Refunds are available within 7 days of signup.",
                "source": "policy.md",
            },
            {
                "chunk_id": "ctx-002",
                "text": "Refund requests must include the account email.",
            },
        ],
        "agent_response": "Refunds are available within 7 days of signup.",
        "extensions": {"fixture": "happy-path"},
    }


def test_decision_input_accepts_chunked_rag_question_answering_context() -> None:
    decision_input = DecisionInput.model_validate(valid_decision_input_payload())

    assert decision_input.schema_version == "decision-input/v0"
    assert decision_input.task_type == "RAG_QUESTION_ANSWERING"
    assert decision_input.provided_context == (
        ContextChunk(
            chunk_id="ctx-001",
            text="Refunds are available within 7 days of signup.",
            source="policy.md",
        ),
        ContextChunk(
            chunk_id="ctx-002",
            text="Refund requests must include the account email.",
        ),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "decision-input/v1"),
        ("task_type", "SUMMARIZATION"),
    ],
)
def test_decision_input_rejects_unsupported_contract_values(field: str, value: str) -> None:
    payload = valid_decision_input_payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        DecisionInput.model_validate(payload)


def test_decision_input_rejects_missing_required_fields() -> None:
    payload = valid_decision_input_payload()
    del payload["agent_response"]

    with pytest.raises(ValidationError):
        DecisionInput.model_validate(payload)


def test_decision_input_rejects_empty_context_list() -> None:
    payload = valid_decision_input_payload()
    payload["provided_context"] = []

    with pytest.raises(ValidationError):
        DecisionInput.model_validate(payload)


@pytest.mark.parametrize(
    "chunk",
    [
        {"text": "Missing chunk id."},
        {"chunk_id": "ctx-missing-text"},
        {"chunk_id": "", "text": "Empty chunk id."},
        {"chunk_id": "ctx-empty-text", "text": "   "},
        {"chunk_id": "ctx-extra", "text": "Has extra field.", "extra": "nope"},
    ],
)
def test_decision_input_rejects_malformed_context_chunks(chunk: dict[str, str]) -> None:
    payload = valid_decision_input_payload()
    payload["provided_context"] = [chunk]

    with pytest.raises(ValidationError):
        DecisionInput.model_validate(payload)


def test_decision_input_rejects_extra_fields_and_is_immutable() -> None:
    payload = valid_decision_input_payload()
    payload["unexpected"] = "fail closed"

    with pytest.raises(ValidationError):
        DecisionInput.model_validate(payload)

    decision_input = DecisionInput.model_validate(valid_decision_input_payload())

    with pytest.raises(ValidationError):
        decision_input.trace_id = "tr-mutated"

    with pytest.raises(AttributeError):
        cast(Any, decision_input.provided_context).append(
            ContextChunk(chunk_id="ctx-003", text="This should not be mutable.")
        )

    with pytest.raises(TypeError):
        cast(Any, decision_input.extensions)["fixture"] = "mutated"


def test_decision_input_serializes_extensions_after_freezing() -> None:
    decision_input = DecisionInput.model_validate(valid_decision_input_payload())

    serialized = json.loads(decision_input.model_dump_json())

    assert serialized["extensions"] == {"fixture": "happy-path"}
