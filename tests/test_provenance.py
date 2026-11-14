"""Black-box provenance contracts using native Git and disposable repositories."""

from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_provenance.py"
TRAILERS = (
    "Model-Author: unavailable",
    "Agent-Role: orchestrator",
    "Co-authored-by: Fixture <fixture@example.test>",
)
VALID = "Subject\n\n" + "\n".join(TRAILERS) + "\n"


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / "project"
        self.repo.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.message = self.root / "message.txt"
        self.env = {
            "PATH": os.environ["PATH"], "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.test")
        self.git("config", "commit.gpgsign", "false")
        hooks = self.root / "empty hooks"
        hooks.mkdir()
        self.git("config", "core.hooksPath", str(hooks))

    def git(self, *args, input_text=None):
        result = subprocess.run(
            ["git", "-C", str(self.repo), *args], input=input_text,
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def run_validator(self, *args, extra_env=None, cwd=None):
        env = dict(self.env)
        env.update(extra_env or {})
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *args], cwd=cwd or self.root,
            env=env, text=True, capture_output=True,
        )

    def check_message(self, message, expected=0, extra_env=None, cwd=None):
        self.message.write_text(message, encoding="utf-8")
        before = self.message.read_bytes()
        result = self.run_validator("--message-file", str(self.message), extra_env=extra_env, cwd=cwd)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertEqual(self.message.read_bytes(), before)
        if expected:
            self.assertIn(self.message.name, result.stderr)
            self.assertNotIn("PASS:", result.stdout)
        return result

    def commit(self, message=VALID):
        self.message.write_text(message, encoding="utf-8")
        self.git("commit", "--allow-empty", "--file", str(self.message))
        return self.git("rev-parse", "HEAD")

    def test_valid_messages_roles_case_folding_and_coauthor_repetition(self):
        variants = (
            VALID,
            VALID.replace("unavailable", "FixtureModel:1"),
            VALID.replace("orchestrator", "developer-coach"),
            VALID.replace("Model-Author:", "mOdEl-AuThOr:"),
            VALID + TRAILERS[2] + "\n",
            VALID + "Co-authored-by: Other Fixture <other+tag@example.test>\n",
            VALID.replace("Fixture <", "Ren\u00e9 Fixture <"),
            VALID + "Signed-off-by: Fixture <fixture@example.test>\n",
            VALID.replace("Subject\n", "Subject\n\n---\n\nContext\n"),
            VALID.replace("\n", "\r\n"),
            VALID.replace("unavailable", "Fixture\n Model").replace("orchestrator", "developer\n coach"),
        )
        for message in variants:
            with self.subTest(message=message):
                self.check_message(message)

    def test_embedded_carriage_returns_are_not_converted_to_continuations(self):
        messages = (
            VALID.replace("unavailable", "Fixture\r Model"),
            VALID.replace("orchestrator", "developer\r coach"),
            VALID.replace("Fixture <", "Fixture\r Name <"),
        )
        for message in messages:
            with self.subTest(message=message, mode="file"):
                self.check_message(message, 1)
            with self.subTest(message=message, mode="history"):
                commit = self.commit(message)
                raw = subprocess.run(
                    ["git", "-C", str(self.repo), "cat-file", "commit", commit],
                    env=self.env, capture_output=True, check=True,
                ).stdout
                self.assertIn(b"\r ", raw)
                result = self.run_validator("--repo", str(self.repo), "--commit", commit)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(commit, result.stderr)
                self.assertNotIn("PASS:", result.stdout)

    def test_missing_blank_duplicate_or_body_only_fields_fail(self):
        variants = [
            "Subject\n", VALID + "\nOrdinary trailing prose.\n",
        ]
        for trailer in TRAILERS:
            key = trailer.split(":")[0]
            variants.extend((
                VALID.replace(trailer + "\n", ""),
                VALID.replace(trailer, key + ": \t"),
            ))
        for key in ("Model-Author", "Agent-Role"):
            variants.extend((VALID + f"{key}: other\n", VALID + f"{key.lower()}: unavailable\n"))
        for message in variants:
            with self.subTest(message=message):
                self.check_message(message, 1)

    def test_reserved_template_tokens_and_controls_fail_without_guessing_names(self):
        for value in ("<MODEL_NAME>", "${MODEL_NAME}", "{{MODEL_NAME}}", "Fixture\x01Model", "Fixture\tModel", "Fixture\u2028Model", "Fixture\x00Model"):
            with self.subTest(value=value):
                self.check_message(VALID.replace("unavailable", value), 1)
        self.check_message(VALID.replace("unavailable", "MODEL_NAME"))
        self.check_message(VALID.replace("Fixture <", "${PERSON} <"), 1)

    def test_coauthor_address_subset_is_explicit(self):
        for address in ("name", "<fixture@example.test>", "Fixture <no-at>", "Fixture <a@@example.test>", "Fixture <a..b@example.test>", "Fixture <a@-example.test>", "Fixture <a@example..test>", 'Fixture <"a b"@example.test>', "Fixture <a@[127.0.0.1]>", "Fixture <a@ex\u00e4mple.test>", "Fixture <a@example.test> trailing", "   <a@example.test>"):
            with self.subTest(address=address):
                self.check_message(VALID.replace(TRAILERS[2], "Co-authored-by: " + address), 1)
        self.check_message(VALID.replace(TRAILERS[2], "Co-authored-by: Fixture <a+b_c.d@example-domain.test>"))

    def test_aliases_and_configured_separators_cannot_change_acceptance(self):
        self.git("config", "trailer.Alias.key", "Model-Author")
        self.git("config", "trailer.Model-Author.key", "Renamed")
        self.git("config", "trailer.separators", "=")
        self.git("config", "trailer.ifExists", "replace")
        self.check_message(VALID, cwd=self.repo, extra_env={"TMPDIR": str(self.repo)})
        self.check_message(VALID.replace("Model-Author:", "Alias:"), 1, cwd=self.repo)
        self.check_message(VALID.replace("Model-Author:", "Model-Author="), 1, cwd=self.repo)
        self.check_message(VALID + "model-author: duplicate\n", 1, cwd=self.repo)

    def test_global_system_environment_configuration_and_commands_are_ignored(self):
        marker = self.root / "command-ran"
        config = self.root / "hostile.gitconfig"
        config.write_text(
            '[trailer "Alias"]\n\tkey = Model-Author\n'
            '[trailer "Model-Author"]\n\tkey = Renamed\n'
            f'\tcmd = "touch \\"{marker}\\""\n'
            '[trailer]\n\tseparators = =\n',
            encoding="utf-8",
        )
        extra = {
            "GIT_CONFIG_GLOBAL": str(config), "GIT_CONFIG_SYSTEM": str(config),
            "GIT_CONFIG_NOSYSTEM": "0", "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "trailer.separators", "GIT_CONFIG_VALUE_0": "=",
            "GIT_CONFIG_KEY_1": "trailer.Alias.key", "GIT_CONFIG_VALUE_1": "Model-Author",
            "GIT_CONFIG_PARAMETERS": "'trailer.Model-Author.key'='Renamed'",
        }
        self.check_message(VALID, extra_env=extra)
        self.check_message(VALID.replace("Model-Author:", "Alias:"), 1, extra_env=extra)
        self.assertFalse(marker.exists())

    def test_selected_commits_and_ranges_report_each_failure_without_mutation(self):
        base = self.commit("Unattributed base\n")
        good = self.commit()
        bad = self.commit("Unattributed selected commit\n")
        last = self.commit("Another unattributed commit\n")
        (self.repo / "keep.txt").write_text("untracked\n", encoding="utf-8")
        before = {str(path.relative_to(self.repo)): sha256(path.read_bytes()).hexdigest() for path in self.repo.rglob("*") if path.is_file()}
        result = self.run_validator("--repo", str(self.repo), "--commit", good)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_validator("--repo", str(self.repo), "--range", f"{base}..{last}")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(bad, result.stderr)
        self.assertIn(last, result.stderr)
        self.assertNotIn(base, result.stderr)
        self.assertNotIn("PASS:", result.stdout)
        after = {str(path.relative_to(self.repo)): sha256(path.read_bytes()).hexdigest() for path in self.repo.rglob("*") if path.is_file()}
        self.assertEqual(after, before)

    def test_merge_commits_are_not_silently_exempted(self):
        base = self.commit()
        self.git("checkout", "-q", "-b", "side")
        self.commit(VALID.replace("Subject", "Side"))
        self.git("checkout", "-q", "--detach", base)
        self.commit(VALID.replace("Subject", "Main"))
        self.git("merge", "--no-ff", "side", "-m", "Unattributed merge")
        merge = self.git("rev-parse", "HEAD")
        result = self.run_validator("--repo", str(self.repo), "--range", f"{base}..{merge}")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(merge, result.stderr)

    def test_unknown_noncommit_and_empty_selections_fail(self):
        commit = self.commit()
        blob = self.git("hash-object", "-w", "--stdin", input_text="fixture blob")
        for mode, value in (("--commit", "missing-ref"), ("--commit", blob), ("--range", f"{commit}..{commit}"), ("--range", "missing..HEAD")):
            with self.subTest(mode=mode, value=value):
                result = self.run_validator("--repo", str(self.repo), mode, value)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertTrue(result.stderr)
                self.assertNotIn("PASS:", result.stdout)
        result = self.run_validator("--repo", str(self.root / "missing"), "--commit", "HEAD")
        self.assertEqual(result.returncode, 1)

    def test_explicit_repository_cannot_be_replaced_by_git_environment(self):
        self.commit()
        empty = self.root / "empty repository"
        empty.mkdir()
        result = self.run_validator("--repo", str(empty), "--commit", "HEAD", extra_env={
            "GIT_DIR": str(self.repo / ".git"), "GIT_WORK_TREE": str(self.repo),
        })
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_selected_object_is_not_substituted_by_replace_refs(self):
        original = self.commit()
        replacement = self.commit("Unattributed replacement\n")
        self.git("replace", original, replacement)
        result = self.run_validator("--repo", str(self.repo), "--commit", original)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_git_is_an_explicit_failure_without_fallback(self):
        self.check_message(VALID, 1, extra_env={"PATH": str(self.root / "no executables")})

    def test_cli_usage_requires_one_explicit_input_and_repository_for_history(self):
        self.message.write_text(VALID, encoding="utf-8")
        cases = (
            (), ("--commit", "HEAD"), ("--range", "HEAD~1..HEAD"),
            ("--message-file", str(self.message), "--commit", "HEAD"),
            ("--repo", str(self.repo), "--message-file", str(self.message)),
            ("--repo", str(self.repo), "--range", "..HEAD"),
            ("--repo", str(self.repo), "--range", "HEAD.."),
            ("--repo", str(self.repo), "--range", "HEAD...HEAD"),
            ("--repo", str(self.repo), "--commit", ""),
        )
        for args in cases:
            with self.subTest(args=args):
                result = self.run_validator(*args)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("usage:", result.stderr)

    def test_missing_directory_and_invalid_utf8_message_inputs_fail(self):
        for path in (self.root / "missing.txt", self.repo):
            result = self.run_validator("--message-file", str(path))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(path.name, result.stderr)
        self.message.write_bytes(b"\xff")
        result = self.run_validator("--message-file", str(self.message))
        self.assertEqual(result.returncode, 1)
        self.assertIn(self.message.name, result.stderr)
