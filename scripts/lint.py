#!/usr/bin/env python3
"""lint.py - Unified Static Governance & Anti-Bloat Linter for artifice.

Audits Markdown formatting cleanliness, link integrity, YAML frontmatter syntax,
and Core Diet line/word ceilings across skills, agents, and global AGENTS.md.
Strictly returns 0 on complete pass, non-zero on any failure.
"""

import argparse
import os
import re
import subprocess
import sys

BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
FENCED_CODE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

CANONICAL_GLOBAL_AGENTS_MD = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "rules", "global-agents.md"
)
GLOBAL_AGENTS_MD = os.environ.get("GLOBAL_AGENTS_PATH")
GLOBAL_LINE_LIMIT = 140
GLOBAL_WORD_LIMIT = 1400
SKILL_LINE_LIMIT = 180
SKILL_WORD_LIMIT = 1000
AGENT_WORD_LIMIT = 900
COPILOT_TOOLS = {
    "code-author": {"read", "search", "edit", "execute", "agent"},
    "code-reviewer": {"read", "search", "execute", "agent"},
    "developer-coach": {"read", "search", "edit", "execute", "web"},
}

OMP_TOOLS = {
    "code-author": {"read", "grep", "glob", "edit", "write", "bash", "send_message", "task", "wait", "todo"},
    "code-reviewer": {"read", "grep", "glob", "bash", "send_message", "task", "wait", "todo"},
    "developer-coach": {"read", "grep", "glob", "bash", "web_search", "send_message"},
}
ADAPTER_LINE_LIMIT = 60

ADAPTER_SPECS = {
    "copilot": {"suffix": ".agent.md", "tools": COPILOT_TOOLS, "label": "Copilot"},
    "omp": {"suffix": ".md", "tools": OMP_TOOLS, "label": "omp"},
}


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


def _adapter_string(value: str):
    """Read the adapter's narrow single-line YAML strings, or return None."""
    if re.search(r"[\x00-\x08\x0b-\x1f\x7f]", value):
        return None
    if value.startswith("'"):
        return value[1:-1].replace("''", "'") if re.fullmatch(r"'(?:[^']|'')*'", value) else None
    if value.startswith('"'):
        if not re.fullmatch(r'"(?:[^"\\]|\\.)*"', value):
            return None
        escapes = {
            "0": "\0", "a": "\a", "b": "\b", "t": "\t", "n": "\n",
            "v": "\v", "f": "\f", "r": "\r", "e": "\x1b", " ": " ",
            '"': '"', "/": "/", "\\": "\\", "N": "\x85", "_": "\xa0",
            "L": "\u2028", "P": "\u2029",
        }
        try:
            return re.sub(
                r"\\(x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|.)",
                lambda m: chr(int(m[1][1:], 16)) if m[1][0] in "xuU" else escapes[m[1]],
                value[1:-1],
            )
        except (KeyError, ValueError, OverflowError):
            return None
    plain = re.split(r"[ \t]+#", value, maxsplit=1)[0].rstrip()
    if (
        not plain
        or plain.lower() in ("null", "~", "true", "false", "yes", "no", "on", "off")
        or re.match(r"[,{}\[\]#&*!|>%@`]|[-?:](?:\s|$)", plain)
        or re.search(r":(?:\s|$)", plain)
    ):
        return None
    return plain


def _check_adapter(path: str, header: list, body: str, spec: dict) -> int:
    """Validate a harness adapter's frontmatter, tool allowlist, and canonical role target."""
    suffix, expected_tools, label = spec["suffix"], spec["tools"], spec["label"]
    base = os.path.basename(path)
    role = base[: -len(suffix)] if base.endswith(suffix) else base
    fields = {}
    valid = base == f"{role}{suffix}" and role in expected_tools
    for line in header:
        match = re.fullmatch(r"([a-z-]+):[ \t]*(.+)", line.rstrip("\r\n"))
        if not match or match[1] in fields:
            valid = False
        else:
            fields[match[1]] = match[2].strip()

    desc = _adapter_string(fields.get("description", ""))
    inline_tools = re.fullmatch(r"\[([^\]]+)\]", fields.get("tools", ""))
    tools = [_adapter_string(t.strip()) for t in inline_tools[1].split(",")] if inline_tools else []
    targets = re.findall(r"agents/([^/\s`]+)/agent\.md", body)
    valid = (
        valid
        and set(fields) == {"name", "description", "tools"}
        and _adapter_string(fields.get("name", "")) == role
        and bool(desc and desc.strip())
        and len(tools) == len(set(tools)) and set(tools) == expected_tools.get(role)
        and bool(targets) and all(t == role for t in targets)
    )
    if not valid:
        print(f"    {RED}{label} adapter error{NC}: Invalid metadata or canonical target in {path}")
    return 0 if valid else 1


def check_copilot_adapter(path: str, header: list, body: str) -> int:
    return _check_adapter(path, header, body, ADAPTER_SPECS["copilot"])


def check_omp_adapter(path: str, header: list, body: str) -> int:
    return _check_adapter(path, header, body, ADAPTER_SPECS["omp"])


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

    adapters = {}
    integrations_dir = os.path.join(target_dir, "integrations")
    if os.path.isdir(integrations_dir):
        for harness in sorted(os.listdir(integrations_dir)):
            agents_subdir = os.path.join(integrations_dir, harness, "agents")
            if os.path.isdir(agents_subdir):
                adapters[agents_subdir] = harness
                targets.extend(
                    os.path.join(agents_subdir, entry)
                    for entry in sorted(os.listdir(agents_subdir))
                    if entry.endswith(".md") and os.path.isfile(os.path.join(agents_subdir, entry))
                )

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
        harness = adapters.get(os.path.dirname(target))
        if harness in ADAPTER_SPECS:
            errors += _check_adapter(
                rel_path, lines[1:closing_idx], "".join(lines[closing_idx + 1:]), ADAPTER_SPECS[harness],
            )

    return errors


def policy_paths() -> list:
    paths = [CANONICAL_GLOBAL_AGENTS_MD]
    if GLOBAL_AGENTS_MD is not None:
        paths.append(GLOBAL_AGENTS_MD)
    return list(dict.fromkeys(paths))


def check_core_diet(target_dir: str) -> int:
    diet_errors = 0
    for path in policy_paths():
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeError) as error:
            print(f"    {RED}Global policy error{NC}: {path}: {error}")
            diet_errors += 1
            continue
        lines = len(text.splitlines())
        words = len(text.split())

        if lines <= GLOBAL_LINE_LIMIT and words <= GLOBAL_WORD_LIMIT:
            print(
                f"  {GREEN}✓{NC} Global policy {path} is within budget ({lines}/{GLOBAL_LINE_LIMIT} lines, {words}/{GLOBAL_WORD_LIMIT} words)."
            )
        else:
            print(
                f"    {RED}Global policy exceeded budget{NC}: {path}: {lines} lines (max {GLOBAL_LINE_LIMIT}), {words} words (max {GLOBAL_WORD_LIMIT})."
            )
            diet_errors += 1

    for directory, filename, word_limit, line_limit in (
        ("skills", "SKILL.md", SKILL_WORD_LIMIT, SKILL_LINE_LIMIT),
        ("agents", "agent.md", AGENT_WORD_LIMIT, None),
    ):
        base = os.path.join(target_dir, directory)
        if not os.path.isdir(base):
            continue
        for entry in sorted(os.listdir(base)):
            path = os.path.join(base, entry, filename)
            if not os.path.isfile(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            lines, words = len(text.splitlines()), len(text.split())
            measurement = f"{words}/{word_limit} words"
            if line_limit is not None:
                measurement += f", {lines}/{line_limit} lines"
            if words <= word_limit and (line_limit is None or lines <= line_limit):
                print(f"  {GREEN}✓{NC} {directory}/{entry}/{filename} is within budget ({measurement}).")
            else:
                print(f"    {RED}Core Diet exceeded{NC}: {directory}/{entry}/{filename} ({measurement}).")
                diet_errors += 1

    integrations_dir = os.path.join(target_dir, "integrations")
    if os.path.isdir(integrations_dir):
        for harness in sorted(os.listdir(integrations_dir)):
            agents_subdir = os.path.join(integrations_dir, harness, "agents")
            if not os.path.isdir(agents_subdir):
                continue
            for entry in sorted(os.listdir(agents_subdir)):
                path = os.path.join(agents_subdir, entry)
                if not entry.endswith(".md") or not os.path.isfile(path):
                    continue
                with open(path, "r", encoding="utf-8") as f:
                    lines = len(f.read().splitlines())
                rel = os.path.relpath(path, target_dir)
                if lines <= ADAPTER_LINE_LIMIT:
                    print(f"  {GREEN}✓{NC} adapter {rel} is within budget ({lines}/{ADAPTER_LINE_LIMIT} lines).")
                else:
                    print(f"    {RED}Adapter diet exceeded{NC}: {rel}: {lines} lines (max {ADAPTER_LINE_LIMIT}).")
                    diet_errors += 1

    return diet_errors


def check_bash_syntax(target_dir: str) -> int:
    """Check native syntax only; disposable runtime tests are separately runnable."""
    errors = 0
    for root, dirs, files in os.walk(target_dir):
        # Skip forbidden directories
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".system_generated")]

        for filename in sorted(files):
            if not filename.endswith(".sh"):
                continue
            path = os.path.join(root, filename)
            try:
                result = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
                if result.returncode == 0:
                    continue
                detail = result.stderr.strip()
            except OSError as error:
                detail = str(error)
            print(f"    {RED}Bash syntax error{NC}: {path}: {detail}")
            errors += 1
    return errors


def lint_repository(target_dir: str) -> int:
    target_dir = os.path.abspath(target_dir)
    print(f"{BOLD}{BLUE}=== Running Static Governance Linters ==={NC}\n")
    print(f"Target directory: {target_dir}\n")

    total_errors = 0
    policies = policy_paths()
    physical_policies = {os.path.realpath(path) for path in policies if path}
    md_files = sorted({
        os.path.realpath(path) if os.path.realpath(path) in physical_policies else path
        for path in find_markdown_files(target_dir) + policies if path
    })

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

    print(f"\n{BOLD}2. Validating YAML Frontmatter (skills, agents & harness adapters)...{NC}")
    frontmatter_errors = check_yaml_frontmatter(target_dir)
    if frontmatter_errors == 0:
        print(f"  {GREEN}✓{NC} All entry points have valid frontmatter and adapter loading directives.")
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

    print(f"\n{BOLD}5. Checking Native Bash Syntax (not runtime tests)...{NC}")
    syntax_errors = check_bash_syntax(target_dir)
    total_errors += syntax_errors
    if syntax_errors == 0:
        print(f"  {GREEN}✓{NC} All Bash scripts pass native syntax checks.")

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
