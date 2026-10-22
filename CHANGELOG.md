# Changelog

All notable product-facing changes to this project will be documented here.

This project follows a lightweight changelog style inspired by Keep a Changelog, with entries grouped under `Added`, `Changed`, `Fixed`, and `Removed` when useful.

## Unreleased

### Added
- Documented Sprint 1.0 Contract Foundation in the public README.
- Added strict `DecisionInput v0`, `DecisionOutput v0`, and `DecisionArtifact v0` contracts.
- Added canonical `faithfulness-v0.1.0` artifact fixture for context-grounded faithfulness.
- Added JSON parse and stable serialization helpers behind the `contracts.py` public facade.
- Added private `_contracts/` modules for base primitives, input models, output models, artifact models, and serialization helpers.
- Recorded deferred scope for schema compliance, safety, model adapters, event-bus workers, dashboards, telemetry databases, artifact registries, automatic retries, and human-review workflows.
- Initialized project changelog.
- Added public README with project status, scope, architecture snapshot, and development commands.
- Added MIT license and truthful README badges for current project status, Python, uv, verification, and agent readiness.
