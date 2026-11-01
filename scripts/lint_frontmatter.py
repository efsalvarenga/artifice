#!/usr/bin/env python3
"""lint_frontmatter.py - YAML Frontmatter Validator for Skills and Agents.

Verifies that all skill definitions (SKILL.md) and agent definitions (agent.md)
contain valid opening/closing frontmatter delimiters (---) and required keys:
'name:' and 'description:'.
Returns 0 on success, 1 on any violation.
"""

import argparse
import os
import sys

BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
NC = "\033[0m"


def check_frontmatter(target_dir: str, verbose: bool = True) -> int:
    target_dir = os.path.abspath(target_dir)
    if not os.path.exists(target_dir):
        print(f"{RED}Error: Target path does not exist: {target_dir}{NC}")
        return 1

    targets = []

    # Collect skill files
    skills_dir = os.path.join(target_dir, "skills")
    if os.path.isdir(skills_dir):
        for entry in sorted(os.listdir(skills_dir)):
            skill_md = os.path.join(skills_dir, entry, "SKILL.md")
            if os.path.isfile(skill_md):
                targets.append(skill_md)

    # Collect agent files
    agents_dir = os.path.join(target_dir, "agents")
    if os.path.isdir(agents_dir):
        for entry in sorted(os.listdir(agents_dir)):
            agent_md = os.path.join(agents_dir, entry, "agent.md")
            if os.path.isfile(agent_md):
                targets.append(agent_md)

    # Also check if target_dir is itself a skill or agent file
    if os.path.isfile(target_dir) and (
        target_dir.endswith("SKILL.md") or target_dir.endswith("agent.md")
    ):
        targets.append(target_dir)

    if not targets:
        if verbose:
            print("No skill (SKILL.md) or agent (agent.md) definitions found.")
        return 0

    errors = 0
    for target in targets:
        rel_path = os.path.relpath(target, target_dir)
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"  {RED}✗{NC} Could not read {rel_path}: {e}")
            errors += 1
            continue

        if not lines or lines[0].strip() != "---":
            print(
                f"    {RED}Frontmatter error{NC}: Missing opening delimiter (---) in {rel_path}"
            )
            errors += 1
            continue

        closing_idx = -1
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                closing_idx = idx
                break

        if closing_idx == -1:
            print(
                f"    {RED}Frontmatter error{NC}: Missing closing delimiter (---) in {rel_path}"
            )
            errors += 1
            continue

        has_name = any(
            line.strip().startswith("name:") for line in lines[1:closing_idx]
        )
        has_desc = any(
            line.strip().startswith("description:")
            for line in lines[1:closing_idx]
        )

        if not has_name:
            print(
                f"    {RED}Frontmatter error{NC}: Missing 'name:' field in {rel_path}"
            )
            errors += 1
        if not has_desc:
            print(
                f"    {RED}Frontmatter error{NC}: Missing 'description:' field in {rel_path}"
            )
            errors += 1

    return 1 if errors > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate YAML frontmatter in skill (SKILL.md) and agent (agent.md) definitions."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Repository root or directory to inspect (default: current directory)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-error output",
    )

    args = parser.parse_args()
    sys.exit(check_frontmatter(args.target, verbose=not args.quiet))


if __name__ == "__main__":
    main()
