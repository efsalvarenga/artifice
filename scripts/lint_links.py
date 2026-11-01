#!/usr/bin/env python3
"""lint_links.py - Markdown Relative & File Link Resolver.

Validates that all local relative links, file:// URI links, and absolute paths
referenced in Markdown documents resolve to actual existing files or directories.
Ignores web URLs, mailto, anchor-only links, and code blocks.
Returns 0 on success, 1 on any broken link.
"""

import argparse
import os
import re
import sys

BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
NC = "\033[0m"

FENCED_CODE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def find_markdown_files(root_dir: str) -> list:
    md_files = []
    for root, _, files in os.walk(root_dir):
        if "/.git" in root or "/node_modules" in root or "/.system_generated" in root:
            continue
        for f in files:
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))
    return sorted(md_files)


def check_links(target_dir: str, verbose: bool = True) -> int:
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

    broken_count = 0
    for file_path in md_files:
        rel_file = os.path.relpath(file_path, base_dir)
        file_dir = os.path.dirname(file_path)
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            print(f"  {RED}✗{NC} Could not read {rel_file}: {e}")
            broken_count += 1
            continue

        # Strip code blocks before checking links
        content_stripped = FENCED_CODE_PATTERN.sub("", content)
        content_stripped = INLINE_CODE_PATTERN.sub("", content_stripped)

        for match in LINK_PATTERN.finditer(content_stripped):
            link_target = match.group(2).strip()
            # Skip web urls, mailto, anchor only links, conversation references
            if link_target.startswith(
                ("http://", "https://", "mailto:", "#", "conversation://")
            ):
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
                resolved_path = os.path.normpath(
                    os.path.join(file_dir, clean_target)
                )

            if not os.path.exists(resolved_path):
                print(
                    f"    {RED}Broken link{NC} in {rel_file}: '{link_target}' (Resolved: {resolved_path})"
                )
                broken_count += 1

    return 1 if broken_count > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate that Markdown cross-links resolve to existing local paths."
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
    sys.exit(check_links(args.target, verbose=not args.quiet))


if __name__ == "__main__":
    main()
