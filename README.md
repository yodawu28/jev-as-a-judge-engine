# Jev-as-Judge Engine

Event-driven LLM evaluation and observability experiments for judging agent
outputs in near real time.

The project explores a narrow but useful first artifact:
**Context-Grounded Faithfulness**. Given a user prompt, context chunks, and an
agent response, the engine will decide whether the response is grounded in the
provided context and emit a structured verdict for telemetry or guardrail
actions.

## Project Status

| Area | Status |
| --- | --- |
| Maturity | Experimental Engineering PoC |
| Active sprint | Sprint 1.0: Python Foundation & Decision Contracts |
| First artifact | Context-Grounded Faithfulness |
| Runtime target | Local Event Bus Worker built from core function and CLI first |
| Verification | `./scripts/verify.sh` |
| Python | `>=3.12` |

## Why This Exists

LLM-as-a-Judge systems are usually run offline against datasets. This project
investigates a more reactive shape: publish prompt/response/context events,
evaluate them asynchronously, and emit typed decisions without adding latency to
the primary application path.

The long-term goal is to understand how a JEV-style event-driven runtime can
apply versioned decision artifacts produced by a separate model-training or
evaluation workflow.

## Architecture Snapshot

```mermaid
flowchart LR
    subgraph Lab["Train Decision Model"]
        Dataset["Synthetic / Labelled Dataset"]
        Metrics["Metric Definition"]
        Artifact["Decision Artifact"]
        Report["Evaluation Report"]
        Dataset --> Metrics --> Artifact --> Report
    end

    subgraph Runtime["Jev-as-Jungle Runtime"]
        Bus["Local Event Bus"]
        Worker["Async Judge Worker"]
        Backend["DecisionBackend"]
        Action["Guardrail Action"]
        Telemetry["Telemetry"]
        Bus --> Worker --> Backend --> Action
        Worker --> Telemetry
    end

    Artifact --> Worker
```

## Current Scope

In scope for the first implementation path:

- Strict `DecisionInput`, `DecisionOutput`, and `DecisionArtifact` contracts.
- `ContextChunk[]` support for RAG-style context.
- Fail-closed validation for unsupported task types.
- Deterministic and fixture-backed decision backends before local model calls.
- CLI trace evaluation before the local event bus demo.

Deferred on purpose:

- Ollama or other local model adapter.
- Real fine-tuning workflow.
- Dashboard UI.
- Safety and schema-compliance decision artifacts.
- Production event bus, telemetry database, and artifact registry.

## Development

Install dependencies and run the canonical verification gate:

```bash
uv sync
./scripts/verify.sh
```

The verification script runs:

- `ruff check .`
- `mypy src tests`
- `pytest`

## Repository Layout

```text
docs/proposals/   Technical proposal and project narrative
scripts/          Local verification and automation scripts
src/              Python package source
tests/            Unit and harness tests
```

Agent-local harness files such as `AGENTS.md`, `PROGRESS.md`,
`DECISIONS.md`, and `.agents/` are intentionally ignored by git. They are local
execution memory, not public product artifacts.

## More Detail

See [`docs/proposals/jev_as_judge_proposal.md`](docs/proposals/jev_as_judge_proposal.md)
for the technical design proposal and roadmap.
