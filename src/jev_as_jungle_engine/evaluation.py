"""Core evaluation orchestration for decision backends."""

from typing import Protocol

from .contracts import DecisionArtifact, DecisionInput, DecisionOutput


class DecisionBackend(Protocol):
    """Backend contract consumed by CLI, workers, and future adapters."""

    backend_id: str
    backend_type: str

    def evaluate(
        self, decision_input: DecisionInput, artifact: DecisionArtifact
    ) -> object:
        """Evaluate one decision input against one decision artifact."""


def evaluate_decision(
    decision_input: DecisionInput,
    artifact: DecisionArtifact,
    backend: DecisionBackend,
) -> DecisionOutput:
    """Validate runtime boundaries, call a backend, and validate its output."""

    _validate_runtime_contract(decision_input, artifact, backend)
    decision_output = DecisionOutput.model_validate(
        backend.evaluate(decision_input, artifact)
    )
    _validate_output_correlation(decision_input, artifact, decision_output)
    return decision_output


def _validate_output_correlation(
    decision_input: DecisionInput,
    artifact: DecisionArtifact,
    decision_output: DecisionOutput,
) -> None:
    if decision_output.trace_id != decision_input.trace_id:
        msg = (
            "trace_id mismatch: backend returned "
            f"{decision_output.trace_id!r} for input {decision_input.trace_id!r}"
        )
        raise ValueError(msg)

    if decision_output.artifact_id != artifact.artifact_id:
        msg = (
            "artifact_id mismatch: backend returned "
            f"{decision_output.artifact_id!r} for artifact {artifact.artifact_id!r}"
        )
        raise ValueError(msg)


def _validate_runtime_contract(
    decision_input: DecisionInput,
    artifact: DecisionArtifact,
    backend: DecisionBackend,
) -> None:
    if artifact.metric != "context_grounded_faithfulness":
        msg = f"unsupported artifact metric: {artifact.metric}"
        raise ValueError(msg)

    if artifact.input_schema_version != "decision-input/v0":
        msg = f"unsupported input_schema_version: {artifact.input_schema_version}"
        raise ValueError(msg)

    if artifact.output_schema_version != "decision-output/v0":
        msg = f"unsupported output_schema_version: {artifact.output_schema_version}"
        raise ValueError(msg)

    if artifact.combiner != "faithfulness_v0_rule":
        msg = f"unsupported combiner: {artifact.combiner}"
        raise ValueError(msg)

    if decision_input.task_type not in artifact.supported_task_types:
        msg = f"unsupported task_type: {decision_input.task_type}"
        raise ValueError(msg)

    if (
        backend.backend_id != artifact.backend_binding.backend_id
        or backend.backend_type != artifact.backend_binding.backend_type
    ):
        msg = (
            "backend_binding mismatch: artifact requires "
            f"{artifact.backend_binding.backend_id}/"
            f"{artifact.backend_binding.backend_type}"
        )
        raise ValueError(msg)
