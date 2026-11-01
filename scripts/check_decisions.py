#!/usr/bin/env python3
"""check_decisions.py - Linter for Asynchronous Decision Ledgers.

Validates section ordering (D -> P -> C), numbering integrity, adequate
context length for coordinator rulings, presence of response prompts, and
enforces active-only hygiene (flagging lingering answered items).
"""

import os
import re
import sys

BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def lint_decision_ledger(file_path: str) -> int:
    if not os.path.isfile(file_path):
        print(f"{RED}Error: File '{file_path}' does not exist.{NC}")
        return 1

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    errors = 0
    warnings = 0

    print(f"{BOLD}=== Checking Decision Ledger: {os.path.basename(file_path)} ==={NC}\n")

    # 1. Section Ordering Check
    expected_sections = [
        "## 0. Opening Roster",
        "## 1. Open Human Decisions",
        "## 2. Actions for Developer",
        "## 3. Coordinator Reversible Decisions",
    ]

    section_positions = {}
    for sec in expected_sections:
        for idx, line in enumerate(lines):
            if sec.lower() in line.lower():
                section_positions[sec] = idx
                break

    last_pos = -1
    for sec in expected_sections:
        if sec in section_positions:
            pos = section_positions[sec]
            if pos < last_pos:
                print(f"  {RED}✗{NC} Section out of order: '{sec}' appears before earlier sections.")
                errors += 1
            else:
                last_pos = pos
                print(f"  {GREEN}✓{NC} Found section in order: '{sec}'")
        else:
            # Section 0 is optional, but 1, 2, 3 are recommended
            if sec != "## 0. Opening Roster":
                print(f"  {YELLOW}⚠{NC} Section missing or heading modified: '{sec}'")
                warnings += 1

    # 2. Check D items (Open Human Decisions)
    d_headings = re.findall(r"^###\s+(D\d+):?\s*(.*)$", content, re.MULTILINE)
    for d_id, title in d_headings:
        # Find item block
        item_match = re.search(
            rf"^###\s+{d_id}.*?\n(.*?)(?=\n###|\n##|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
        if item_match:
            item_body = item_match.group(1)
            if "response:" not in item_body.lower():
                print(f"  {RED}✗{NC} Item {d_id} ('{title}') missing 'Response:' line.")
                errors += 1
            if "recommended" not in item_body.lower():
                print(f"  {YELLOW}⚠{NC} Item {d_id} ('{title}') missing explicit recommended option.")
                warnings += 1

    # 3. Check C items (Coordinator Reversible Decisions)
    c_headings = re.findall(r"^###\s+(C\d+):?\s*(.*)$", content, re.MULTILINE)
    for c_id, title in c_headings:
        item_match = re.search(
            rf"^###\s+{c_id}.*?\n(.*?)(?=\n###|\n##|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
        if item_match:
            item_body = item_match.group(1)
            words = len(item_body.split())
            if words < 25:
                print(
                    f"  {RED}✗{NC} Item {c_id} ('{title}') context is too short ({words} words; minimum 25 required for clear rationale)."
                )
                errors += 1
            if "revert" not in item_body.lower():
                print(
                    f"  {RED}✗{NC} Item {c_id} ('{title}') missing explicit revert instruction or trigger."
                )
                errors += 1

    # 4. Check for Lingering Answered Items (Active-Only Hygiene)
    # Match Response: or **Response:** followed by text, ignoring empty prompts or underscore blanks
    raw_responses = re.findall(r"(?:\*\*)?Response:(?:\*\*)?\s*(.*)$", content, re.MULTILINE)
    answered_responses = [
        r.strip() for r in raw_responses 
        if r.strip() and not re.match(r"^[_ \t\-\.]+$", r.strip())
    ]
    if answered_responses:
        print(
            f"  {YELLOW}⚠{NC} Active ledger contains {len(answered_responses)} answered item(s). Move resolved items to archive."
        )
        warnings += 1

    print("\n========================================================")
    if errors == 0:
        print(f"{GREEN}{BOLD}✓ Decision ledger format valid ({warnings} warning(s)).{NC}")
        print("========================================================")
        return 0
    else:
        print(f"{RED}{BOLD}✗ Decision ledger lint failed with {errors} error(s).{NC}")
        print("========================================================")
        return 1


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "docs/decisions/pending-decisions.md"
    sys.exit(lint_decision_ledger(target))


if __name__ == "__main__":
    main()
