#!/bin/bash
set -euo pipefail

: "${CLAUDE_PROJECT_ROOT:=}"

if command -v jj >/dev/null 2>&1; then
  jj_status="$(jj status 2>/dev/null || true)"
  if [[ -n "${CLAUDE_PROJECT_ROOT}" ]] && [[ "${jj_status}" == 0 ]]; then
    cd "${CLAUDE_PROJECT_ROOT}" || exit 0
    prompt="$(cat | jq '.prompt' 2>/dev/null || true)"
    jj describe -m "${prompt}" 2>/dev/null || true
    jj new 2>/dev/null || true
  fi
fi

exit 0
