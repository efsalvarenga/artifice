#!/usr/bin/env bash
# ==============================================================================
# lint.sh - Static Governance Harness for artifice
# ==============================================================================
# Thin execution wrapper delegating to scripts/lint.py.
# Strictly returns 0 on complete pass, non-zero on any failure.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/lint.py" "$@"
