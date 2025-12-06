#!/bin/bash

if [[ $(jj status) == 0 ]]; then
  cd "${CLAUDE_PROJECT_ROOT}" || exit 0
  jj describe -m "$(cat | jq '.prompt')" 2>/dev/null
  jj new 2>/dev/null
fi

exit 0
