# Glossary

## Deterministic Faithfulness Rule
A simple, fully deterministic Sprint 2.0 rule for classifying whether an agent
response is grounded in provided context. It is a test oracle for the runtime
contract, not a replacement for a future model-backed judge.

## Failure Precedence
The order used when more than one faithfulness failure could apply:
`CONTRADICTS_CONTEXT`, `UNSUPPORTED_BY_CONTEXT`, `MISSING_ANSWER`, then
`INSUFFICIENT_CONTEXT`.

## Insufficient Context
A faithfulness failure where the provided context is not enough to answer the
user prompt. Empty context is not part of this state because `DecisionInput v0`
rejects empty context before evaluation.

## Unsupported By Context
A faithfulness failure where the context does not support the agent response.
When no supporting chunk exists, Sprint 2.0 evidence should point to the most
relevant available chunk using the `INSUFFICIENT` relationship.
