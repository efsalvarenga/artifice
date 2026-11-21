#!/usr/bin/env python3
"""pr_checklist.py - Project a design doc's implementation plan onto a PR checklist.

Usage:
  pr_checklist.py <design.md>                   print the checklist markdown to stdout
  pr_checklist.py <design.md> --check <pr-body.md>
        compare the PR body's ## Implementation Checklist against the design doc's plan

Exit codes: 0 = printed / checklist matches (in order, no missing or extra items);
1 = drift (MISSING/EXTRA lines printed); 2 = unreadable input or no plan items found.

The design doc on the branch is the source of truth; the PR checklist is a projection
that reviewers re-generate to flag drift (see README.md, Task Tracking & Feedback).
"""

import argparse
import re
import sys
from pathlib import Path

PLAN_HEADINGS = (
    re.compile(r"^## .*Implementation Plan", re.IGNORECASE),
    re.compile(r"^## .*Technical Plan", re.IGNORECASE),
    re.compile(r"^## .*Execution", re.IGNORECASE),
)
SECTION_HEADING = re.compile(r"^## ")
LIST_ITEM = re.compile(r"^(?:\d+\.|[-*])\s+(.*)$")
CHECKBOX_ITEM = re.compile(r"^\s*- \[[ xX]\]\s+(.*)$")
CHECKLIST_HEADING = "## Implementation Checklist"

def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def plan_items(design_text: str) -> list:
    """Column-0 list items of the design doc's plan section.

    Section preference: Implementation Plan, then Technical Plan, then Execution.
    Stops at the next ## section or a Verification subheading.
    """
    lines = design_text.splitlines()
    start = None
    for pattern in PLAN_HEADINGS:
        for idx, line in enumerate(lines):
            if SECTION_HEADING.match(line) and pattern.match(line):
                if start is None or idx < start:
                    start = idx
        if start is not None:
            break
    if start is None:
        return []
    items = []
    for line in lines[start + 1:]:
        if SECTION_HEADING.match(line):
            break
        if re.match(r"^### .*Verification", line, re.IGNORECASE):
            break
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
            in_section = line.strip().lower() == CHECKLIST_HEADING.lower()
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

    try:
        design_text = Path(args.design).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: cannot read {args.design}: {error}", file=sys.stderr)
        return 2
    items = plan_items(design_text)
    if not items:
        print(f"error: no implementation-plan list items found in {args.design}", file=sys.stderr)
        return 2
    if args.check is None:
        sys.stdout.write(checklist_markdown(items))
        return 0

    try:
        pr_items = pr_checklist_items(Path(args.check).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: cannot read {args.check}: {error}", file=sys.stderr)
        return 2
    if pr_items == items:
        print(f"OK: PR checklist matches {args.design} ({len(items)} items).")
        return 0
    missing = [item for item in items if item not in pr_items]
    extra = [item for item in pr_items if item not in items]
    if pr_items != items and not missing and not extra:
        print("ORDER differs from the design doc plan.")
    for item in missing:
        print(f"MISSING from PR checklist: {item}")
    for item in extra:
        print(f"EXTRA in PR checklist: {item}")
    return 1
if __name__ == "__main__":
    sys.exit(main())
