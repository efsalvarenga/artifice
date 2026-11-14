#!/usr/bin/env python3
"""Validate explicit commit-message provenance without changing Git or messages."""

import argparse
from contextlib import nullcontext
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Optional

REQUIRED = ("Model-Author", "Agent-Role", "Co-authored-by")
CONTROLS = re.compile(r"[\x00-\x1f\x7f\x85\u2028\u2029]")
PLACEHOLDERS = re.compile(
    r"\$\{[A-Za-z_][A-Za-z0-9_]*\}|\{\{[A-Za-z_][A-Za-z0-9_]*\}\}|<[A-Z][A-Z0-9_]*>"
)
ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
ADDRESS = re.compile(rf"{ATOM}(?:\.{ATOM})*@{LABEL}(?:\.{LABEL})*")
COAUTHOR = re.compile(r"([^<>]+) +<([^<>]+)>")


def git(arguments: list[str], repo: Optional[Path] = None, message: Optional[str] = None) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_TERMINAL_PROMPT": "0",
    })
    # Even --parse rewrites configured aliases; parse outside every repository.
    location = tempfile.TemporaryDirectory(prefix="artifice-provenance-") if repo is None else nullcontext(str(repo))
    with location as directory:
        if repo is None:
            env["GIT_CEILING_DIRECTORIES"] = os.path.realpath(directory)
        result = subprocess.run(
            ["git", "--no-pager", "--no-replace-objects", "-C", directory, *arguments],
            input=message.encode("utf-8") if message is not None else None,
            env=env, capture_output=True,
        )
    if result.returncode:
        detail = result.stderr.decode("utf-8").strip() or f"exit {result.returncode}"
        raise ValueError(f"Git {arguments[0]} failed: {detail}")
    return result.stdout.decode("utf-8")


def validate_message(message: str) -> list[str]:
    if "\x00" in message:
        return ["Commit messages must not contain NUL bytes."]
    parsed = git(
        ["-c", "trailer.separators=:", "interpret-trailers", "--parse", "--no-divider"],
        message=message,
    )
    values: dict[str, list[str]] = {name.lower(): [] for name in REQUIRED}
    for line in parsed.split("\n"):
        key, separator, value = line.partition(":")
        if separator and key.isascii() and key.lower() in values:
            values[key.lower()].append(value.strip(" \t"))

    errors = []
    for name in REQUIRED:
        entries = values[name.lower()]
        if not entries:
            errors.append(f"Missing {name} trailer.")
            continue
        if name != "Co-authored-by" and len(entries) != 1:
            errors.append(f"{name} must appear exactly once.")
        for value in entries:
            if not value or CONTROLS.search(value):
                errors.append(f"{name} must be non-empty and contain no control characters or line breaks.")
            elif PLACEHOLDERS.search(value):
                errors.append(f"{name} contains an unexpanded template token.")
            elif name == "Co-authored-by":
                author = COAUTHOR.fullmatch(value)
                if not author or not author[1].strip() or not ADDRESS.fullmatch(author[2]):
                    errors.append("Co-authored-by must contain a name and a supported unquoted ASCII email address.")
    return errors


def resolve_commit(repo: Path, revision: str) -> str:
    return git(["rev-parse", "--verify", "--end-of-options", revision + "^{commit}"], repo).strip()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--message-file", help="Prepared UTF-8 commit-message file")
    mode.add_argument("--commit", help="Exactly one commit revision")
    mode.add_argument("--range", dest="revision_range", help="Explicit BASE..HEAD commit range")
    parser.add_argument("--repo", help="Repository to inspect; required for history modes")
    args = parser.parse_args(argv)
    if args.message_file is not None and args.repo is not None:
        parser.error("--repo is only valid with --commit or --range")
    if args.message_file is None and not args.repo:
        parser.error("--repo is required with --commit or --range")
    if args.commit is not None and not args.commit:
        parser.error("--commit requires an explicit revision")
    endpoints = []
    if args.revision_range is not None:
        endpoints = args.revision_range.split("..")
        if len(endpoints) != 2 or not all(endpoints) or "..." in args.revision_range:
            parser.error("--range requires two explicit endpoints in BASE..HEAD form")

    label = args.message_file or f"{args.repo}: {args.commit or args.revision_range}"
    try:
        if args.message_file is not None:
            messages = [(label, Path(args.message_file).read_bytes().decode("utf-8"))]
        else:
            repo = Path(args.repo)
            if args.commit is not None:
                commits = [resolve_commit(repo, args.commit)]
            else:
                base, head = (resolve_commit(repo, revision) for revision in endpoints)
                commits = git(["rev-list", f"{base}..{head}"], repo).splitlines()
                if not commits:
                    raise ValueError("Selected commit range is empty.")
            messages = []
            for commit in commits:
                label = commit
                raw = git(["cat-file", "commit", commit], repo)
                _, separator, body = raw.partition("\n\n")
                if not separator:
                    raise ValueError("Commit object has no message separator.")
                messages.append((commit, body))

        errors = 0
        for label, message in messages:
            for error in validate_message(message):
                print(f"Error: {label}: {error}", file=sys.stderr)
                errors += 1
        if errors:
            return 1
        print(f"PASS: {len(messages)} commit message(s) have valid provenance structure.")
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {label}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
