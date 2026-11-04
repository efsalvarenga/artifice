#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

python3 "${SCRIPT_DIR}/lint.py" "$@"

if [[ $# -eq 0 ]] || [[ "$(cd "${1}" 2>/dev/null && pwd -P)" == "${REPO_ROOT}" ]]; then
    printf '\n=== Running Unit & Contract Tests ===\n\n'
    python3 -m unittest discover -s "${REPO_ROOT}/tests" -p 'test_*.py'
fi
