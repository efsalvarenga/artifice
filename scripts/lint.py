#!/usr/bin/env python3
"""lint.py - Unified Static Governance & Anti-Bloat Linter for artifice.

Audits Markdown formatting cleanliness, link integrity, YAML frontmatter syntax,
and Core Diet line/word ceilings across skills, agents, and global AGENTS.md.
Strictly returns 0 on complete pass, non-zero on any failure.
"""

import argparse
import os
import re
import sys

BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
FENCED_CODE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

GLOBAL_AGENTS_MD = os.path.expanduser("~/.gemini/config/AGENTS.md")
GLOBAL_LINE_LIMIT = 140
GLOBAL_WORD_LIMIT = 1400
SKILL_LINE_LIMIT = 180


def find_markdown_files(root_dir: str) -> list:
    md_files = []
    for root, _, files in os.walk(root_dir):
        if (
            "/.git" in root
            or "/node_modules" in root
            or "/.system_generated" in root
        ):
            continue
        for f in sorted(files):
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))
    return sorted(md_files)


def check_markdown_cleanliness_and_links(
    target_dir: str, md_files: list
) -> tuple:
    heading_errors = 0
    link_errors = 0

    for file_path in md_files:
        rel_path = os.path.relpath(file_path, target_dir)
        file_dir = os.path.dirname(file_path)
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            print(f"  {RED}✗{NC} Could not read {rel_path}: {e}")
            heading_errors += 1
            link_errors += 1
            continue

        lines = content.splitlines()

        # 1. Heading Cleanliness Check
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
                        heading_errors += 1

        # 2. Link Resolution Check
        content_stripped = FENCED_CODE_PATTERN.sub("", content)
        content_stripped = INLINE_CODE_PATTERN.sub("", content_stripped)

        for match in LINK_PATTERN.finditer(content_stripped):
            link_target = match.group(2).strip()
            if link_target.startswith(
                ("http://", "https://", "mailto:", "#", "conversation://")
            ):
                continue

            clean_target = link_target.split("#")[0]
            if not clean_target:
                continue

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
                    f"    {RED}Broken link{NC} in {rel_path}: '{link_target}' (Resolved: {resolved_path})"
                )
                link_errors += 1

    return heading_errors, link_errors


def check_yaml_frontmatter(target_dir: str) -> int:
    targets = []
    skills_dir = os.path.join(target_dir, "skills")
    if os.path.isdir(skills_dir):
        for entry in sorted(os.listdir(skills_dir)):
            skill_md = os.path.join(skills_dir, entry, "SKILL.md")
            if os.path.isfile(skill_md):
                targets.append(skill_md)

    agents_dir = os.path.join(target_dir, "agents")
    if os.path.isdir(agents_dir):
        for entry in sorted(os.listdir(agents_dir)):
            agent_md = os.path.join(agents_dir, entry, "agent.md")
            if os.path.isfile(agent_md):
                targets.append(agent_md)

    if not targets:
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

    return errors


def check_core_diet(target_dir: str) -> int:
    diet_errors = 0

    # Ceiling A: Global AGENTS.md
    if os.path.isfile(GLOBAL_AGENTS_MD):
        with open(GLOBAL_AGENTS_MD, "r", encoding="utf-8") as f:
            text = f.read()
        lines = len(text.splitlines())
        words = len(text.split())

        if lines <= GLOBAL_LINE_LIMIT and words <= GLOBAL_WORD_LIMIT:
            print(
                f"  {GREEN}✓{NC} Global AGENTS.md is within budget ({lines}/{GLOBAL_LINE_LIMIT} lines, {words}/{GLOBAL_WORD_LIMIT} words)."
            )
        else:
            print(
                f"    {RED}Global AGENTS.md exceeded budget:{NC} {lines} lines (max {GLOBAL_LINE_LIMIT}), {words} words (max {GLOBAL_WORD_LIMIT})."
            )
            diet_errors += 1
    else:
        print(f"    {YELLOW}Warning: Global AGENTS.md not found at {GLOBAL_AGENTS_MD}.{NC}")

    # Ceiling B: Skills SKILL.md entrypoints
    skills_dir = os.path.join(target_dir, "skills")
    if os.path.isdir(skills_dir):
        for entry in sorted(os.listdir(skills_dir)):
            skill_file = os.path.join(skills_dir, entry, "SKILL.md")
            if os.path.isfile(skill_file):
                with open(skill_file, "r", encoding="utf-8") as f:
                    s_lines = len(f.read().splitlines())
                if s_lines <= SKILL_LINE_LIMIT:
                    print(
                        f"  {GREEN}✓{NC} Skill '{entry}' SKILL.md is within budget ({s_lines}/{SKILL_LINE_LIMIT} lines)."
                    )
                else:
                    print(
                        f"    {RED}Skill '{entry}' exceeded budget:{NC} {s_lines} lines (max {SKILL_LINE_LIMIT}). Offload large sections to references/."
                    )
                    diet_errors += 1

    return diet_errors


def lint_repository(target_dir: str) -> int:
    target_dir = os.path.abspath(target_dir)
    print(f"{BOLD}{BLUE}=== Running Static Governance Linters ==={NC}\n")
    print(f"Target directory: {target_dir}\n")

    total_errors = 0
    md_files = find_markdown_files(target_dir)

    # Gate 1 & 3: Markdown Cleanliness & Link Resolution
    heading_errors, link_errors = check_markdown_cleanliness_and_links(
        target_dir, md_files
    )

    print(f"{BOLD}1. Verifying Markdown Formatting Cleanliness...{NC}")
    if heading_errors == 0:
        print(f"  {GREEN}✓{NC} All markdown headings are followed by clean blank lines.")
    else:
        print(f"  {RED}✗{NC} {heading_errors} markdown heading violation(s) found.")
        total_errors += heading_errors

    print(f"\n{BOLD}2. Validating YAML Frontmatter (skills & agents)...{NC}")
    frontmatter_errors = check_yaml_frontmatter(target_dir)
    if frontmatter_errors == 0:
        print(f"  {GREEN}✓{NC} All skill and agent definitions have valid YAML frontmatter.")
    else:
        print(f"  {RED}✗{NC} YAML frontmatter validation failed on {frontmatter_errors} file(s).")
        total_errors += frontmatter_errors

    print(f"\n{BOLD}3. Resolving Markdown Relative & File Links...{NC}")
    if link_errors == 0:
        print(f"  {GREEN}✓{NC} All markdown cross-links resolve to existing local paths.")
    else:
        print(f"  {RED}✗{NC} {link_errors} broken markdown link(s) detected.")
        total_errors += link_errors

    print(f"\n{BOLD}4. Enforcing Core Diet Ceilings (Anti-Bloat)...{NC}")
    diet_errors = check_core_diet(target_dir)
    if diet_errors > 0:
        print(f"  {RED}✗{NC} Core Diet budget exceeded on {diet_errors} file(s).")
        total_errors += diet_errors

    # Gate 5: EGM Specification Contracts (if docs/designs exists)
    designs_dir = os.path.join(target_dir, "docs", "designs")
    if os.path.isdir(designs_dir):
        print(f"\n{BOLD}5. Validating EGM Specification Contracts...{NC}")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        try:
            import validate_egm
            egm_res = validate_egm.validate_repo(target_dir)
            if egm_res != 0:
                print(f"  {RED}✗{NC} EGM specification contract validation failed.")
                total_errors += 1
            else:
                print(f"  {GREEN}✓{NC} All active EGM specification contracts and Goldfish reviews pass.")
        except Exception as e:
            print(f"  {RED}✗{NC} Could not execute validate_egm: {e}")
            total_errors += 1

    # Gate 6: Native Automated Test Suite (if tests/ exists)
    tests_dir = os.path.join(target_dir, "tests")
    if os.path.isdir(tests_dir):
        print(f"\n{BOLD}6. Executing Automated Test Suite...{NC}")
        import unittest
        loader = unittest.defaultTestLoader
        suite = loader.discover(tests_dir)
        runner = unittest.TextTestRunner(verbosity=1)
        test_result = runner.run(suite)
        if not test_result.wasSuccessful():
            failure_count = len(test_result.failures) + len(test_result.errors)
            print(f"  {RED}✗{NC} {failure_count} test failure(s) detected.")
            total_errors += failure_count
        else:
            print(f"  {GREEN}✓{NC} All {test_result.testsRun} automated test(s) passed successfully.")

    print("\n========================================================")
    if total_errors == 0:
        print(f"{GREEN}{BOLD}✓ ALL STATIC GOVERNANCE LINTERS PASSED CLEANLY.{NC}")
        print("========================================================")
        return 0
    else:
        print(f"{RED}{BOLD}✗ STATIC LINTING FAILED WITH {total_errors} ERROR(S).{NC}")
        print("========================================================")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Unified Static Governance & Anti-Bloat Linter for artifice and sibling repositories."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Repository root or directory to inspect (default: current directory)",
    )

    args = parser.parse_args()
    sys.exit(lint_repository(args.target))


if __name__ == "__main__":
    main()
