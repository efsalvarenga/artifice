#!/usr/bin/env bash
# ==============================================================================
# lint.sh - Static Governance & Linter Harness for artifice
# ==============================================================================
# Orchestrates modular linters for Markdown formatting cleanliness, YAML
# frontmatter validity, link integrity, and Core Diet ceilings.
# Strictly returns 0 on complete pass, non-zero on any failure.
# ==============================================================================

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${1:-${REPO_ROOT}}"
GLOBAL_AGENTS_MD="${HOME}/.gemini/config/AGENTS.md"

echo -e "${BOLD}${BLUE}=== Running artifice Static Governance Linters ===${NC}\n"

ERRORS_FOUND=0

pass() {
  echo -e "  ${GREEN}✓${NC} $1"
}

fail() {
  echo -e "  ${RED}✗${NC} $1"
  ERRORS_FOUND=$((ERRORS_FOUND + 1))
}

# ------------------------------------------------------------------------------
# Gate 1: Markdown Formatting Cleanliness
# ------------------------------------------------------------------------------
echo -e "${BOLD}1. Verifying Markdown Formatting Cleanliness...${NC}"
if python3 "${SCRIPT_DIR}/lint_headings.py" "${TARGET_DIR}"; then
  pass "All markdown headings are followed by clean blank lines."
else
  fail "Markdown file(s) violate blank-line heading constraints."
fi

# ------------------------------------------------------------------------------
# Gate 2: YAML Frontmatter Validation
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}2. Validating YAML Frontmatter (skills & agents)...${NC}"
if python3 "${SCRIPT_DIR}/lint_frontmatter.py" "${TARGET_DIR}"; then
  pass "All skill and agent definitions have valid YAML frontmatter."
else
  fail "YAML frontmatter validation failed on one or more files."
fi

# ------------------------------------------------------------------------------
# Gate 3: Markdown Relative Link Resolver
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}3. Resolving Markdown Relative & File Links...${NC}"
if python3 "${SCRIPT_DIR}/lint_links.py" "${TARGET_DIR}"; then
  pass "All markdown cross-links resolve to existing local paths."
else
  fail "Broken markdown link(s) detected."
fi

# ------------------------------------------------------------------------------
# Gate 4: Core Diet Ceilings (Anti-Bloat Governance)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}4. Enforcing Core Diet Ceilings (Anti-Bloat)...${NC}"
DIET_ERRORS=0

# Ceiling A: Global AGENTS.md (Max 140 lines / 1,400 words)
GLOBAL_LINE_LIMIT=140
GLOBAL_WORD_LIMIT=1400

if [ -f "$GLOBAL_AGENTS_MD" ]; then
  GLOBAL_LINES=$(wc -l < "$GLOBAL_AGENTS_MD" | tr -d ' ')
  GLOBAL_WORDS=$(wc -w < "$GLOBAL_AGENTS_MD" | tr -d ' ')
  
  if [ "$GLOBAL_LINES" -le "$GLOBAL_LINE_LIMIT" ] && [ "$GLOBAL_WORDS" -le "$GLOBAL_WORD_LIMIT" ]; then
    pass "Global AGENTS.md is within budget (${GLOBAL_LINES}/${GLOBAL_LINE_LIMIT} lines, ${GLOBAL_WORDS}/${GLOBAL_WORD_LIMIT} words)."
  else
    echo -e "    ${RED}Global AGENTS.md exceeded budget:${NC} ${GLOBAL_LINES} lines (max ${GLOBAL_LINE_LIMIT}), ${GLOBAL_WORDS} words (max ${GLOBAL_WORD_LIMIT})."
    DIET_ERRORS=$((DIET_ERRORS + 1))
  fi
else
  echo -e "    ${YELLOW}Warning: Global AGENTS.md not found at ${GLOBAL_AGENTS_MD}.${NC}"
fi

# Ceiling B: Skills SKILL.md entrypoints (Max 180 lines each)
SKILL_LINE_LIMIT=180
SKILL_DIR="${TARGET_DIR}/skills"

if [ -d "$SKILL_DIR" ]; then
  for s_dir in "${SKILL_DIR}"/*; do
    [ -d "$s_dir" ] || continue
    skill_file="${s_dir}/SKILL.md"
    [ -f "$skill_file" ] || continue
    
    s_lines=$(wc -l < "$skill_file" | tr -d ' ')
    s_name=$(basename "$s_dir")
    
    if [ "$s_lines" -le "$SKILL_LINE_LIMIT" ]; then
      pass "Skill '${s_name}' SKILL.md is within budget (${s_lines}/${SKILL_LINE_LIMIT} lines)."
    else
      echo -e "    ${RED}Skill '${s_name}' exceeded budget:${NC} ${s_lines} lines (max ${SKILL_LINE_LIMIT}). Offload large sections to references/."
      DIET_ERRORS=$((DIET_ERRORS + 1))
    fi
  done
fi

if [ "$DIET_ERRORS" -gt 0 ]; then
  fail "Core Diet budget exceeded on ${DIET_ERRORS} file(s)."
fi

# ------------------------------------------------------------------------------
# Final Verdict
# ------------------------------------------------------------------------------
echo -e "\n========================================================"
if [ "$ERRORS_FOUND" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}✓ ALL STATIC GOVERNANCE LINTERS PASSED CLEANLY.${NC}"
  echo -e "========================================================"
  exit 0
else
  echo -e "${RED}${BOLD}✗ STATIC LINTING FAILED WITH ${ERRORS_FOUND} ERROR(S).${NC}"
  echo -e "========================================================"
  exit 1
fi
