#!/usr/bin/env python3
"""build_review_dossier.py - Repository Invariant & Decision Dossier Generator.

Compiles a compact markdown digest (<= 40 lines / <= 600 tokens) of repository
governance, architectural boundaries, active rulings, and specification invariants
to inject into local/cross-family review models (Qwen 2.5 14B / Mistral NeMo 12B).
"""

import argparse
import os
import re
import sys


def find_repo_agents_md(repo_root: str) -> str:
    candidates = [
        os.path.join(repo_root, "AGENTS.md"),
        os.path.join(repo_root, ".agents", "AGENTS.md"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return ""


def find_decisions_file(repo_root: str) -> str:
    candidates = [
        os.path.join(repo_root, "docs", "decisions", "pending-decisions.md"),
        os.path.join(repo_root, ".agents", "context", "decisions.md"),
        os.path.join(repo_root, "templates", "decisions.md.template"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return ""


def extract_invariants(agents_file: str) -> list:
    if not agents_file or not os.path.isfile(agents_file):
        return []

    with open(agents_file, "r", encoding="utf-8") as f:
        content = f.read()

    extracted = []
    # Extract specific known rule bullets or headings
    lines = content.splitlines()
    for line in lines:
        s = line.strip()
        if s.startswith("- **") and len(s) < 160:
            extracted.append(s)
        elif s.startswith("* **") and len(s) < 160:
            extracted.append(s)
        elif s.startswith("## ") and any(
            kw in s.lower()
            for kw in [
                "git",
                "boundary",
                "integrity",
                "lore",
                "sovereignty",
                "language",
            ]
        ):
            extracted.append(f"Constraint: {s[3:].strip()}")

    return extracted[:8]


def extract_spec_invariants(repo_root: str, changed_files: list) -> list:
    designs_dir = os.path.join(repo_root, "docs", "designs")
    if not os.path.isdir(designs_dir):
        return []

    spec_invariants = []
    for sf in os.listdir(designs_dir):
        if sf.endswith(".md") and sf != "TEMPLATE.md":
            with open(
                os.path.join(designs_dir, sf), "r", encoding="utf-8"
            ) as f:
                content = f.read()
            match = re.search(
                r"## 4\. Invariants & Rules\s*\n(.*?)(?=\n##|\Z)",
                content,
                re.DOTALL,
            )
            if match:
                inv_lines = [
                    l.strip()
                    for l in match.group(1).splitlines()
                    if l.strip().startswith(("*", "-"))
                ]
                for il in inv_lines[:3]:
                    spec_invariants.append(f"Spec ({sf[:7]}): {il}")
    return spec_invariants[:4]


def build_dossier(repo_root: str, changed_files: list) -> str:
    repo_name = os.path.basename(os.path.abspath(repo_root))
    agents_file = find_repo_agents_md(repo_root)
    repo_invariants = extract_invariants(agents_file)
    spec_invariants = extract_spec_invariants(repo_root, changed_files)

    # Core global invariants
    dossier_lines = [
        f"### Repository Invariant Dossier: {repo_name}",
        "",
        "> Directives: The following constraints represent intentional architectural and governance invariants for this repository. Do NOT flag adherence to these rules as defects or anti-patterns.",
        "",
        "* **Language:** 100% British English required across code, docstrings, commits, and comments.",
        "* **Markdown Cleanliness:** Mandatory blank line beneath every markdown heading.",
        "* **Narrative Sovereignty:** AI agents must never autonomously invent world lore or character backstory.",
    ]

    # Specific repo rules
    if "arete" in repo_name.lower():
        dossier_lines.append(
            "* **Git Boundary (arete):** Strictly prohibited from running `git commit`; leave files unstaged/staged."
        )
        dossier_lines.append(
            "* **Data Integrity (arete):** Return `None` on missing data; never inject synthetic or interpolated figures."
        )
    elif "emergent" in repo_name.lower():
        dossier_lines.append(
            "* **Simulation Decoupling (emergent):** `engine/` is strictly headless, pure, and decoupled from client."
        )
        dossier_lines.append(
            "* **Lore Placeholders (emergent):** Neutral technical terms (e.g. 'Traveller') are intentional pending human lore."
        )
    else:
        dossier_lines.append(
            f"* **Git Operations ({repo_name}):** Atomic commits to feature branches; direct pushes to main prohibited."
        )

    for ri in repo_invariants[:4]:
        dossier_lines.append(f"* {ri}")

    for si in spec_invariants[:3]:
        dossier_lines.append(f"* {si}")

    # Enforce <= 40 lines
    dossier_lines = dossier_lines[:38]
    return "\n".join(dossier_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compile Repository Invariant Dossier for Local/Cross-Model Review"
    )
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=".",
        help="Path to repository root (default: current directory)",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=[],
        help="List of changed file paths in diff",
    )

    args = parser.parse_args()
    dossier = build_dossier(os.path.abspath(args.repo_root), args.files)
    print(dossier)


if __name__ == "__main__":
    main()
