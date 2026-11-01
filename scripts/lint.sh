#!/usr/bin/env bash
# ==============================================================================
# lint.sh - Static Governance & Linter Harness for artifice
# ==============================================================================
# Audits Markdown formatting cleanliness, YAML frontmatter validity, link
# integrity, and Core Diet ceilings across skills, agents, and global AGENTS.md.
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
MD_HEADING_VIOLATIONS=0

python3 - << 'EOF' || MD_HEADING_VIOLATIONS=1
import os
import re
import sys

repo_root = os.getcwd()
md_files = []
for root, _, files in os.walk(repo_root):
    if "/.git" in root or "/node_modules" in root:
        continue
    for f in files:
        if f.endswith(".md"):
            md_files.append(os.path.join(root, f))

heading_pattern = re.compile(r'^(#{1,6})\s+(.*)$')
errors = 0

for file_path in md_files:
    rel_path = os.path.relpath(file_path, repo_root)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    in_code_block = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
            
        if heading_pattern.match(line):
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() != "" and not heading_pattern.match(next_line):
                    print(f"    Heading violation in {rel_path}:{i+1} -> '{line.strip()}' followed by non-blank: '{next_line.strip()}'")
                    errors += 1

if errors > 0:
    sys.exit(1)
EOF

if [ "$MD_HEADING_VIOLATIONS" -eq 0 ]; then
  pass "All markdown headings are followed by clean blank lines."
else
  fail "${MD_HEADING_VIOLATIONS} markdown file(s) violate blank-line heading constraints."
fi

# ------------------------------------------------------------------------------
# Gate 2: YAML Frontmatter Validation
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}2. Validating YAML Frontmatter (skills & agents)...${NC}"
FRONTMATTER_ERRORS=0

python3 - << 'EOF' || FRONTMATTER_ERRORS=1
import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "..")) if sys.argv[0] else os.getcwd()
targets = []

# Collect skill files
skills_dir = os.path.join(repo_root, "skills")
if os.path.isdir(skills_dir):
    for entry in os.listdir(skills_dir):
        skill_md = os.path.join(skills_dir, entry, "SKILL.md")
        if os.path.isfile(skill_md):
            targets.append(skill_md)

# Collect agent files
agents_dir = os.path.join(repo_root, "agents")
if os.path.isdir(agents_dir):
    for entry in os.listdir(agents_dir):
        agent_md = os.path.join(agents_dir, entry, "agent.md")
        if os.path.isfile(agent_md):
            targets.append(agent_md)

errors = 0
for target in targets:
    rel_path = os.path.relpath(target, repo_root)
    with open(target, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines or lines[0].strip() != "---":
        print(f"    Missing opening frontmatter delimiter (---) in {rel_path}")
        errors += 1
        continue
    
    closing_idx = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            closing_idx = idx
            break
            
    if closing_idx == -1:
        print(f"    Missing closing frontmatter delimiter (---) in {rel_path}")
        errors += 1
        continue
        
    frontmatter_text = "".join(lines[1:closing_idx])
    has_name = any(line.strip().startswith("name:") for line in lines[1:closing_idx])
    has_desc = any(line.strip().startswith("description:") for line in lines[1:closing_idx])
    
    if not has_name:
        print(f"    Missing 'name:' in frontmatter: {rel_path}")
        errors += 1
    if not has_desc:
        print(f"    Missing 'description:' in frontmatter: {rel_path}")
        errors += 1

if errors > 0:
    sys.exit(1)
EOF

if [ "$FRONTMATTER_ERRORS" -eq 0 ]; then
  pass "All skill and agent definitions have valid YAML frontmatter."
else
  fail "YAML frontmatter validation failed on one or more files."
fi

# ------------------------------------------------------------------------------
# Gate 3: Markdown Relative Link Resolver
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}3. Resolving Markdown Relative & File Links...${NC}"
LINK_ERRORS=0

python3 - << 'EOF' || LINK_ERRORS=1
import os
import re
import sys

repo_root = os.getcwd()
md_files = []
for root, _, files in os.walk(repo_root):
    if "/.git" in root or "/node_modules" in root:
        continue
    for f in files:
        if f.endswith(".md"):
            md_files.append(os.path.join(root, f))

# Strip code blocks (fenced ```...``` and inline `...`) before parsing links
fenced_code_pattern = re.compile(r'```.*?```', re.DOTALL)
inline_code_pattern = re.compile(r'`[^`\n]+`')
link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
errors = 0

for file_path in md_files:
    rel_file = os.path.relpath(file_path, repo_root)
    file_dir = os.path.dirname(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip code blocks
    content_stripped = fenced_code_pattern.sub('', content)
    content_stripped = inline_code_pattern.sub('', content_stripped)

    for match in link_pattern.finditer(content_stripped):
        link_target = match.group(2).strip()
        # Skip web urls, mailto, anchor only links
        if link_target.startswith(("http://", "https://", "mailto:", "#", "conversation://")):
            continue
        
        # Remove anchor if present
        clean_target = link_target.split("#")[0]
        if not clean_target:
            continue
            
        # Handle file:// scheme
        if clean_target.startswith("file://"):
            resolved_path = clean_target[7:]
        elif os.path.isabs(clean_target):
            resolved_path = clean_target
        else:
            resolved_path = os.path.normpath(os.path.join(file_dir, clean_target))
            
        if not os.path.exists(resolved_path):
            print(f"    Broken link in {rel_file}: '{link_target}' (Resolved: {resolved_path})")
            errors += 1

if errors > 0:
    sys.exit(1)
EOF

if [ "$LINK_ERRORS" -eq 0 ]; then
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
SKILL_DIR="${REPO_ROOT}/skills"

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
