from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_readme_documents_contract_foundation_without_raw_trace_content() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for required_text in [
        "Decision Contract v0",
        "DecisionInput v0",
        "DecisionOutput v0",
        "DecisionArtifact v0",
        "src/jev_as_jungle_engine/contracts.py",
        "artifacts/faithfulness-v0.1.0.json",
        "Deferred on purpose",
    ]:
        assert required_text in readme

    for raw_trace_text in [
        "What is the refund policy?",
        "Refunds are available within 7 days of signup.",
        "The response is grounded in the referenced context.",
    ]:
        assert raw_trace_text not in readme


def test_changelog_records_sprint_1_contract_foundation() -> None:
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    for required_text in [
        "Sprint 1.0 Contract Foundation",
        "DecisionInput v0",
        "DecisionOutput v0",
        "DecisionArtifact v0",
        "faithfulness-v0.1.0",
        "public facade",
        "deferred",
    ]:
        assert required_text in changelog
