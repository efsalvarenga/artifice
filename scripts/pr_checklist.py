#!/usr/bin/env python3
"""pr_checklist.py - Project a design doc's implementation plan onto a PR checklist.

Usage:
  pr_checklist.py <design.md>                   print the checklist markdown to stdout
  pr_checklist.py <design.md> --check <pr-body.md>
        exit 0 iff the PR body's ## Implementation Checklist items match the design doc's plan

The design doc on the branch is the source of truth; the PR checklist is a projection
that reviewers re-generate to flag drift (see README.md, Task Tracking & Feedback).
"""

import argparse
import re
import sys
from pathlib import Path

PLAN_HEADING = re.compile(r"^## .*(Implementation Plan|Technical Plan)", re.IGNORECASE)
SECTION_HEADING = re.compile(r"^## ")
LIST_ITEM = re.compile(r"^\s*(?:\d+\.|[-*])\s+(.*)$")
CHECKBOX_ITEM = re.compile(r"^\s*- \[[ xX]\]\s+(.*)$")
CHECKLIST_HEADING = "## Implementation Checklist"

def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def plan_items(design_text: str) -> list:
    """Top-level list items of the design doc's implementation-plan section."""
    items = []
    in_plan = False
    for line in design_text.splitlines():
        if in_plan and re.match(r"^### .*Verification", line, re.IGNORECASE):
            break
        if SECTION_HEADING.match(line):
            if in_plan:
                break
            in_plan = bool(PLAN_HEADING.match(line))
            continue
        if in_plan:
            match = LIST_ITEM.match(line)
            if match:
                items.append(_normalise(match[1]))
    return items


def checklist_markdown(items: list) -> str:
    """Render the ## Implementation Checklist section."""
    lines = [CHECKLIST_HEADING, ""]
    lines.extend(f"- [ ] {item}" for item in items)
    return "\n".join(lines) + "\n"


def pr_checklist_items(pr_body: str) -> list:
    """Checkbox item texts of the PR body's checklist section."""
    items = []
    in_section = False
    for line in pr_body.splitlines():
        if SECTION_HEADING.match(line):
            if in_section:
                break
            in_section = line.strip() == CHECKLIST_HEADING
            continue
        if in_section:
            match = CHECKBOX_ITEM.match(line)
            if match:
                items.append(_normalise(match[1]))
    return items


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", help="Path to the branch's design doc (docs/designs/NNN_*.md)")
    parser.add_argument("--check", metavar="PR_BODY", help="Compare against a PR body file instead of printing")
    args = parser.parse_args(argv)

    items = plan_items(Path(args.design).read_text(encoding="utf-8"))
    if not items:
        print(f"error: no implementation-plan list items found in {args.design}", file=sys.stderr)
        return 2
    if args.check is None:
        sys.stdout.write(checklist_markdown(items))
        return 0

    pr_items = pr_checklist_items(Path(args.check).read_text(encoding="utf-8"))
    missing = [item for item in items if item not in pr_items]
    extra = [item for item in pr_items if item not in items]
    if not missing and not extra:
        print(f"OK: PR checklist matches {args.design} ({len(items)} items).")
        return 0
    for item in missing:
        print(f"MISSING from PR checklist: {item}")
    for item in extra:
        print(f"EXTRA in PR checklist: {item}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
