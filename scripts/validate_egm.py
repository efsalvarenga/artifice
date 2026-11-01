#!/usr/bin/env python3
"""validate_egm.py - Portable Elephant-Goldfish Model (EGM) Contract Validator.

Validates that design specifications in docs/designs/ comply with EGM section
requirements, possess a corresponding zero-context Goldfish review in
docs/reviews/, and have achieved an Approved verdict.
"""

import os
import re
import sys

BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"

REQUIRED_SECTIONS = [
    "1. Overview & Objectives",
    "3. State Schema",
    "4. Invariants & Rules",
    "7. Verification",
]


def validate_repo(repo_root: str) -> int:
    designs_dir = os.path.join(repo_root, "docs", "designs")
    reviews_dir = os.path.join(repo_root, "docs", "reviews")

    if not os.path.isdir(designs_dir):
        print(f"{RED}Error: 'docs/designs' directory not found in {repo_root}{NC}")
        return 1

    print(f"{BOLD}{BLUE}=== Validating EGM Specification Contracts ==={NC}\n")
    print(f"Target repository: {repo_root}")

    spec_files = [
        f
        for f in os.listdir(designs_dir)
        if f.endswith(".md") and f != "TEMPLATE.md"
    ]

    if not spec_files:
        print(f"No active specifications found in {designs_dir}.")
        return 0

    errors = 0
    num_pattern = re.compile(r"^(\d+)")

    for spec_name in sorted(spec_files):
        spec_path = os.path.join(designs_dir, spec_name)
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"\nChecking specification: {BOLD}{spec_name}{NC}")

        # Check required sections
        for section in REQUIRED_SECTIONS:
            if section.lower() not in content.lower():
                print(f"  {RED}✗{NC} Missing section matching: '{section}'")
                errors += 1
            else:
                print(f"  {GREEN}✓{NC} Found section: {section}")

        # Check matching review if spec has numeric prefix
        match = num_pattern.match(spec_name)
        if match:
            spec_num = match.group(1)
            review_match = None
            if os.path.isdir(reviews_dir):
                for rf in os.listdir(reviews_dir):
                    if (
                        rf.startswith(f"{spec_num}_")
                        and rf.endswith(".md")
                        and not rf.startswith("pr_")
                        and rf != "TEMPLATE.md"
                    ):
                        review_match = rf
                        break

            if not review_match:
                print(
                    f"  {RED}✗{NC} Missing matching Goldfish review in docs/reviews/ for prefix {spec_num}"
                )
                errors += 1
            else:
                review_path = os.path.join(reviews_dir, review_match)
                with open(review_path, "r", encoding="utf-8") as rf_obj:
                    r_content = rf_obj.read()

                verdict_match = re.search(
                    r"(?:\*\*)?Verdict:(?:\*\*)?\s*([A-Za-z\s]+)",
                    r_content,
                    re.IGNORECASE,
                )
                review_approved = verdict_match and "approved" in verdict_match.group(1).lower()

                spec_status_match = re.search(
                    r"(?:\*\*)?Status:(?:\*\*)?\s*([A-Za-z\s]+)",
                    content,
                    re.IGNORECASE,
                )
                spec_approved = spec_status_match and "approved" in spec_status_match.group(1).lower()

                if review_approved or spec_approved:
                    status_note = "Review Approved" if review_approved else f"Spec Status: {spec_status_match.group(1).strip()}"
                    print(
                        f"  {GREEN}✓{NC} Review '{review_match}' verified ({status_note})."
                    )
                else:
                    verdict_str = (
                        verdict_match.group(1).strip()
                        if verdict_match
                        else "Unknown"
                    )
                    print(
                        f"  {RED}✗{NC} Specification is not approved (Review: {verdict_str}, Spec Status: {spec_status_match.group(1).strip() if spec_status_match else 'Unknown'})"
                    )
                    errors += 1

    print("\n========================================================")
    if errors == 0:
        print(f"{GREEN}{BOLD}✓ ALL EGM CONTRACTS VALIDATED SUCCESSFULLY.{NC}")
        print("========================================================")
        return 0
    else:
        print(f"{RED}{BOLD}✗ EGM VALIDATION FAILED WITH {errors} ERROR(S).{NC}")
        print("========================================================")
        return 1


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    abs_target = os.path.abspath(target)
    sys.exit(validate_repo(abs_target))


if __name__ == "__main__":
    main()
