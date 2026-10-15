#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT_DIR"

fail() {
  printf 'VERIFY_FAIL: %s\n' "$1" >&2
  exit 1
}

info() {
  printf 'VERIFY: %s\n' "$1"
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "missing required file: $path"
}

require_file "scripts/verify.sh"

if [[ -f AGENTS.md ]]; then
  agent_lines="$(wc -l < AGENTS.md | tr -d ' ')"
  [[ "$agent_lines" -le 150 ]] || fail "AGENTS.md must stay under 150 lines; found $agent_lines"
  grep -q './scripts/verify.sh' AGENTS.md || fail "AGENTS.md must reference canonical verification"
fi

if [[ -f PROGRESS.md ]]; then
  grep -q 'Current Goal' PROGRESS.md || fail "PROGRESS.md must record the current goal"
fi

if [[ -f DECISIONS.md ]]; then
  grep -q 'ADR-001' DECISIONS.md || fail "DECISIONS.md must contain ADR-001"
fi

bash -n scripts/verify.sh || fail "scripts/verify.sh has invalid shell syntax"

if [[ -f pyproject.toml ]]; then
  command -v uv >/dev/null 2>&1 || fail "pyproject.toml present but uv is unavailable"
  [[ -d src ]] || fail "pyproject.toml present but src/ is missing"
  [[ -d tests || -d harness ]] || fail "pyproject.toml present but tests/ or harness/ is missing"
  uv run ruff check .
  if [[ -d tests ]]; then
    uv run mypy src tests
  else
    uv run mypy src
  fi
  uv run pytest
fi

if [[ -f package.json ]]; then
  command -v npm >/dev/null 2>&1 || fail "package.json present but npm is unavailable"
  npm run lint --if-present
  npm run typecheck --if-present
  npm test --if-present
fi

info "bootstrap verification passed"
