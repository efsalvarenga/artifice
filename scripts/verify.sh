#!/usr/bin/env bash
# ==============================================================================
# verify.sh - Continuous Verification Orchestrator for artifice
# ==============================================================================
# Orchestrates static governance linting (scripts/lint.sh) and automated unit
# tests (tests/test_scripts.py).
# Strictly returns 0 on complete pass, non-zero on any failure.
# ==============================================================================

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BOLD}${BLUE}=== Running artifice Continuous Verification ===${NC}\n"

# Step 1: Static Governance Linters
if [ -f "${SCRIPT_DIR}/lint.sh" ]; then
  "${SCRIPT_DIR}/lint.sh"
  echo ""
fi

# Step 2: Automated Unit Test Suite
echo -e "${BOLD}Executing Automated Python Unit Test Suite...${NC}"
if [ -d "${REPO_ROOT}/tests" ]; then
  if ARTIFICE_IN_VERIFY=1 python3 -m unittest discover "${REPO_ROOT}/tests" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} All python unit tests passed."
  else
    echo -e "  ${RED}✗${NC} Python unit test suite failed."
    ARTIFICE_IN_VERIFY=1 python3 -m unittest discover "${REPO_ROOT}/tests" || true
    echo -e "\n========================================================"
    echo -e "${RED}${BOLD}✗ VERIFICATION FAILED: UNIT TESTS FAILED.${NC}"
    echo -e "========================================================"
    exit 1
  fi
fi

echo -e "\n========================================================"
echo -e "${GREEN}${BOLD}✓ ALL ARTIFICE VERIFICATION GATES PASSED CLEANLY.${NC}"
echo -e "========================================================"
exit 0
