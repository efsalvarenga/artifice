#!/usr/bin/env python3
"""lint_headings.py - Markdown Heading Cleanliness Validator.

Enforces that every Markdown heading (#, ##, etc.) is immediately followed
by an empty blank line, preventing collapsed text blocks under headings.
Returns 0 on success, 1 on any violation.
"""

import argparse
import os
import re
import sys

BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
NC = "\033[0m"

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")


def find_markdown_files(root_dir: str) -> list:
    md_files = []
    for root, _, files in os.walk(root_dir):
        if "/.git" in root or "/node_modules" in root or "/.system_generated" in root:
            continue
        for f in files:
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))
    return sorted(md_files)


def check_headings(target_dir: str, verbose: bool = True) -> int:
    target_dir = os.path.abspath(target_dir)
    if not os.path.exists(target_dir):
        print(f"{RED}Error: Target path does not exist: {target_dir}{NC}")
        return 1

    if os.path.isfile(target_dir):
        md_files = [target_dir]
        base_dir = os.path.dirname(target_dir)
    else:
        md_files = find_markdown_files(target_dir)
        base_dir = target_dir

    if not md_files:
        if verbose:
            print("No markdown files found to check.")
        return 0

    violations = 0
    for file_path in md_files:
        rel_path = os.path.relpath(file_path, base_dir)
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"  {RED}✗{NC} Could not read {rel_path}: {e}")
            violations += 1
            continue

        in_code_block = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            if HEADING_PATTERN.match(line):
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() != "":
                        print(
                            f"    {RED}Heading violation{NC} in {rel_path}:{i+1} -> '{line.strip()}' followed by non-blank: '{next_line.strip()}'"
                        )
                        violations += 1

    return 1 if violations > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate that Markdown headings are immediately followed by blank lines."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Directory or file to validate (default: current directory)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-error output",
    )

    args = parser.parse_args()
    sys.exit(check_headings(args.target, verbose=not args.quiet))


if __name__ == "__main__":
    main()
