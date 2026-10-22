from jev_as_jungle_engine import contracts

PUBLIC_CONTRACT_SYMBOLS = {
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
    "FAITHFULNESS_ANSWER_OPTIONS",
    "NonEmptyStr",
    "SUPPORTED_DECISION_ACTIONS",
    "SemanticVersionStr",
    "parse_decision_artifact_json",
    "parse_decision_input_json",
    "parse_decision_output_json",
    "serialize_contract",
}


def test_contracts_facade_exports_complete_public_contract_api() -> None:
    assert set(contracts.__all__) == PUBLIC_CONTRACT_SYMBOLS

    for symbol in PUBLIC_CONTRACT_SYMBOLS:
        assert getattr(contracts, symbol) is not None


def test_contract_model_implementations_live_in_private_domain_modules() -> None:
    assert contracts.ContextChunk.__module__ == "jev_as_jungle_engine._contracts.input"
    assert contracts.DecisionInput.__module__ == "jev_as_jungle_engine._contracts.input"

    assert contracts.DecisionScores.__module__ == "jev_as_jungle_engine._contracts.output"
    assert contracts.EvidenceReference.__module__ == "jev_as_jungle_engine._contracts.output"
    assert contracts.DecisionOutput.__module__ == "jev_as_jungle_engine._contracts.output"

    assert contracts.BackendBinding.__module__ == "jev_as_jungle_engine._contracts.artifact"
    assert contracts.ArtifactQuestion.__module__ == "jev_as_jungle_engine._contracts.artifact"
    assert contracts.DecisionArtifact.__module__ == "jev_as_jungle_engine._contracts.artifact"


def test_contract_json_helpers_live_in_private_serialization_module() -> None:
    assert (
        contracts.parse_decision_input_json.__module__
        == "jev_as_jungle_engine._contracts.serialization"
    )
    assert (
        contracts.parse_decision_output_json.__module__
        == "jev_as_jungle_engine._contracts.serialization"
    )
    assert (
        contracts.parse_decision_artifact_json.__module__
        == "jev_as_jungle_engine._contracts.serialization"
    )
    assert contracts.serialize_contract.__module__ == "jev_as_jungle_engine._contracts.serialization"
