#!/usr/bin/env python3
"""sabotage_check.py - Targeted Mutation & Test Sabotage Verification Harness.

Verifies that unit test suites catch deliberate logic mutations in boundary
comparators, guard conditions, or state reducers ("o teste pega se eu sabotar?").
Executes in an isolated git worktree or safely restored sandbox.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def run_mutation(
    target_dir: str,
    rel_file: str,
    anchor_old: str,
    mutate_new: str,
    test_cmd: str,
) -> tuple[str, str]:
    abs_file = os.path.join(target_dir, rel_file)
    if not os.path.isfile(abs_file):
        return ("ERROR", f"File not found: {rel_file}")

    with open(abs_file, "r", encoding="utf-8") as f:
        original_content = f.read()

    # Check anchor occurrences
    count = original_content.count(anchor_old)
    if count == 0:
        return (
            "STALE",
            f"Anchor not found in {rel_file}: '{anchor_old[:40]}...'",
        )
    elif count > 1:
        return (
            "AMBIGUOUS",
            f"Anchor matched {count} times in {rel_file} (must match exactly once).",
        )

    # Apply mutation
    mutated_content = original_content.replace(anchor_old, mutate_new, 1)
    with open(abs_file, "w", encoding="utf-8") as f:
        f.write(mutated_content)

    try:
        # Run test command inside target_dir
        res = subprocess.run(
            test_cmd,
            shell=True,
            cwd=target_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if res.returncode != 0:
            return (
                "KILLED",
                "Test suite failed on sabotaged code (Invariant caught!).",
            )
        else:
            return (
                "SURVIVED",
                "Test suite stayed green on sabotaged code (Blind spot!).",
            )
    finally:
        # Guarantee restoration
        with open(abs_file, "w", encoding="utf-8") as f:
            f.write(original_content)


def run_cases(cases_path: str, repo_root: str, use_worktree: bool) -> int:
    if not os.path.isfile(cases_path):
        print(f"{RED}Error: Cases file '{cases_path}' not found.{NC}")
        return 1

    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print(
        f"{BOLD}=== Running Sabotage Mutation Suite ({len(cases)} cases) ==={NC}\n"
    )

    worktree_dir = None
    if use_worktree:
        try:
            worktree_dir = tempfile.mkdtemp(prefix="artifice-sabotage-")
            subprocess.check_call(
                ["git", "worktree", "add", "--detach", worktree_dir, "HEAD"],
                cwd=repo_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            target_dir = worktree_dir
            print(f"Using isolated worktree: {worktree_dir}")
        except Exception:
            print(
                f"{YELLOW}Warning: Git worktree creation failed; falling back to working directory with in-place restoration.{NC}"
            )
            target_dir = repo_root
    else:
        target_dir = repo_root

    killed = 0
    survived = 0
    errors = 0

    try:
        for idx, case in enumerate(cases, 1):
            name = case.get("name", f"Case {idx}")
            rel_file = case["file"]
            anchor_old = case["anchor_old"]
            mutate_new = case["mutate_new"]
            test_cmd = case["test_cmd"]

            status, msg = run_mutation(
                target_dir, rel_file, anchor_old, mutate_new, test_cmd
            )

            if status == "KILLED":
                print(f"  {GREEN}✓ KILLED{NC} [{name}] — {rel_file}")
                killed += 1
            elif status == "SURVIVED":
                print(f"  {RED}✗ SURVIVED{NC} [{name}] — {rel_file}")
                print(f"      {RED}Blind spot:{NC} {msg}")
                survived += 1
            else:
                print(f"  {YELLOW}⚠ {status}{NC} [{name}] — {msg}")
                errors += 1
    finally:
        if worktree_dir:
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", worktree_dir],
                    cwd=repo_root,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if os.path.exists(worktree_dir):
                    shutil.rmtree(worktree_dir, ignore_errors=True)
            except Exception:
                pass

    print("\n========================================================")
    print(
        f"Sabotage Results: {killed} killed, {survived} survived, {errors} errors."
    )
    if survived == 0 and errors == 0:
        print(f"{GREEN}{BOLD}✓ ALL MUTATIONS CAUGHT BY TEST SUITE.{NC}")
        print("========================================================")
        return 0
    elif errors > 0:
        print(f"{YELLOW}{BOLD}⚠ STALE OR AMBIGUOUS ANCHORS DETECTED.{NC}")
        print("========================================================")
        return 2
    else:
        print(
            f"{RED}{BOLD}✗ MUTATIONS SURVIVED — TEST STRENGTHENING REQUIRED.{NC}"
        )
        print("========================================================")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Targeted Test Sabotage Verification Harness"
    )
    subparsers = parser.add_subparsers(dest="action")

    # Run cases
    run_parser = subparsers.add_parser("run", help="Run a suite of mutation cases")
    run_parser.add_argument(
        "--cases", required=True, help="Path to JSON mutation cases file"
    )
    run_parser.add_argument(
        "--repo", default=".", help="Target repository root (default: current directory)"
    )
    run_parser.add_argument(
        "--no-worktree",
        action="store_true",
        help="Disable git worktree isolation (use in-place file restore)",
    )

    # Probe single
    probe_parser = subparsers.add_parser(
        "probe", help="Probe a single targeted mutation"
    )
    probe_parser.add_argument(
        "--file", required=True, help="Target file relative to repo"
    )
    probe_parser.add_argument(
        "--old", required=True, help="Original anchor string"
    )
    probe_parser.add_argument(
        "--new", required=True, help="Mutated replacement string"
    )
    probe_parser.add_argument(
        "--test-cmd", required=True, help="Test command to run"
    )
    probe_parser.add_argument(
        "--repo", default=".", help="Target repository root"
    )

    args = parser.parse_args()

    if args.action == "run":
        sys.exit(
            run_cases(
                args.cases,
                os.path.abspath(args.repo),
                not args.no_worktree,
            )
        )
    elif args.action == "probe":
        status, msg = run_mutation(
            os.path.abspath(args.repo),
            args.file,
            args.old,
            args.new,
            args.test_cmd,
        )
        if status == "KILLED":
            print(f"{GREEN}✓ KILLED: {msg}{NC}")
            sys.exit(0)
        elif status == "SURVIVED":
            print(f"{RED}✗ SURVIVED: {msg}{NC}")
            sys.exit(1)
        else:
            print(f"{YELLOW}⚠ {status}: {msg}{NC}")
            sys.exit(2)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
