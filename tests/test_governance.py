"""Contract tests for shared policy registration and portable linting."""

from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lint  # noqa: E402


class GovernanceInstallerTests(unittest.TestCase):
    clients = ("copilot", "antigravity")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def home(self, name):
        home = self.root / name / "home dir"
        home.mkdir(parents=True)
        return home

    def policy(self, client, home):
        relative = ".copilot/copilot-instructions.md" if client == "copilot" else ".gemini/config/AGENTS.md"
        return home / relative

    def run_installer(self, client, home, *args, checkout=ROOT, extra_env=None):
        env = {"PATH": os.environ["PATH"], "HOME": str(home)}
        env.update(extra_env or {})
        return subprocess.run(
            ["bash", str(checkout / "scripts" / f"install_{client}.sh"), *args],
            cwd=self.root, env=env, text=True, capture_output=True,
        )

    def checkout(self, name):
        checkout = self.root / name
        checkout.mkdir()
        for directory in ("agents", "integrations", "skills", "scripts", "rules"):
            source = ROOT / directory
            if source.is_dir():
                shutil.copytree(source, checkout / directory, ignore=shutil.ignore_patterns("__pycache__"))
        return checkout

    def test_installs_global_policy_and_checks_without_writes(self):
        for client in self.clients:
            with self.subTest(client=client):
                home = self.home(client)
                result = self.run_installer(client, home, "--check")
                self.assertEqual(result.returncode, 1)
                self.assertFalse((home / ".local").exists())
                result = self.run_installer(client, home)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                policy = self.policy(client, home)
                self.assertTrue(policy.is_symlink())
                self.assertEqual(policy.resolve(), ROOT / "rules/global-agents.md")
                before = os.readlink(policy)
                for args in (("--check",), ()):
                    result = self.run_installer(client, home, *args)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(os.readlink(policy), before)

    def test_both_installation_orders_share_one_live_policy(self):
        checkout = self.checkout("live checkout")
        source = checkout / "rules/global-agents.md"
        source.parent.mkdir(exist_ok=True)
        source.write_text("# Shared rules\n\nFirst.\n", encoding="utf-8")
        for order in (self.clients, tuple(reversed(self.clients))):
            with self.subTest(order=order):
                home = self.home("-".join(order))
                for client in order:
                    result = self.run_installer(client, home, checkout=checkout)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                source.write_text(f"# Shared rules\n\nChanged with {order[0]} first.\n", encoding="utf-8")
                for client in order:
                    policy = self.policy(client, home)
                    self.assertTrue(policy.is_symlink())
                    self.assertEqual(policy.resolve(), source)
                    self.assertEqual(policy.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

    def test_existing_policy_entries_abort_before_any_registration(self):
        for client in self.clients:
            for kind in ("file", "identical", "directory", "wrong-link", "broken-link"):
                with self.subTest(client=client, kind=kind):
                    home = self.home(f"{client}-{kind}")
                    policy = self.policy(client, home)
                    policy.parent.mkdir(parents=True)
                    content = "# Personal policy\n\nKeep me.\n"
                    if kind == "identical":
                        source = ROOT / "rules/global-agents.md"
                        content = source.read_text(encoding="utf-8") if source.is_file() else content
                    if kind in ("file", "identical"):
                        policy.write_text(content, encoding="utf-8")
                    elif kind == "directory":
                        policy.mkdir()
                        (policy / "keep").write_text(content, encoding="utf-8")
                    else:
                        target = home / "other.md"
                        if kind == "wrong-link":
                            target.write_text(content, encoding="utf-8")
                        policy.symlink_to(target)
                    for args in ((), ("--check",)):
                        result = self.run_installer(client, home, *args)
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        self.assertIn("conflict", result.stdout + result.stderr)
                        self.assertIn("manual", (result.stdout + result.stderr).lower())
                        self.assertFalse((home / ".local").exists())
                        self.assertFalse((policy.parent / "agents").exists())
                    if kind in ("file", "identical"):
                        self.assertEqual(policy.read_text(encoding="utf-8"), content)
                    elif kind == "directory":
                        self.assertEqual(list(policy.iterdir()), [policy / "keep"])
                    else:
                        self.assertEqual(os.readlink(policy), str(target))

    def test_equivalent_policy_link_and_client_root_aliases(self):
        for client in self.clients:
            with self.subTest(client=client):
                home = self.home(client)
                self.assertEqual(self.run_installer(client, home).returncode, 0)
                policy = self.policy(client, home)
                self.assertTrue(policy.is_symlink())
                policy.unlink()
                policy.symlink_to(ROOT / "rules/global-agents.md")
                client_root = home / (".copilot" if client == "copilot" else ".gemini")
                alias = home / "client alias"
                alias.symlink_to(client_root)
                variable = "COPILOT_HOME" if client == "copilot" else "GEMINI_HOME"
                result = self.run_installer(client, home, "--check", extra_env={variable: str(alias)})
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_policy_sources_abort_without_writes(self):
        for client in self.clients:
            for kind in ("missing", "directory", "unreadable"):
                with self.subTest(client=client, kind=kind):
                    checkout = self.checkout(f"checkout-{client}-{kind}")
                    source = checkout / "rules/global-agents.md"
                    if source.exists():
                        source.unlink()
                    if kind == "directory":
                        source.mkdir(parents=True)
                    elif kind == "unreadable":
                        source.parent.mkdir(parents=True, exist_ok=True)
                        source.write_text("# Rules\n\nFixture.\n", encoding="utf-8")
                        source.chmod(0)
                        self.addCleanup(source.chmod, 0o644)
                        if os.access(source, os.R_OK):
                            self.skipTest("This runner can read chmod-protected files.")
                    home = self.home(f"home-{client}-{kind}")
                    result = self.run_installer(client, home, checkout=checkout)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("source", (result.stdout + result.stderr).lower())
                    self.assertFalse((home / ".local").exists())

    def test_overridden_client_roots_receive_the_same_policy(self):
        for client in self.clients:
            with self.subTest(client=client):
                home = self.home(client)
                custom = self.root / f"{client} custom profile"
                variable = "COPILOT_HOME" if client == "copilot" else "GEMINI_HOME"
                result = self.run_installer(client, home, extra_env={variable: str(custom)})
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                policy = custom / ("copilot-instructions.md" if client == "copilot" else "config/AGENTS.md")
                self.assertTrue(policy.is_symlink())
                self.assertEqual(policy.resolve(), ROOT / "rules/global-agents.md")
                self.assertFalse((home / (".copilot" if client == "copilot" else ".gemini")).exists())

    def test_missing_provenance_tool_aborts_before_registration(self):
        for client in self.clients:
            with self.subTest(client=client):
                checkout = self.checkout(f"incomplete-{client}")
                (checkout / "scripts/validate_provenance.py").unlink()
                home = self.home(client)
                result = self.run_installer(client, home, checkout=checkout)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("validate_provenance.py", result.stderr)
                self.assertFalse((home / ".local").exists())

    def test_symlinked_client_parents_cannot_register_inside_the_checkout(self):
        for client in self.clients:
            with self.subTest(client=client):
                checkout = self.checkout(f"escaped-{client}")
                settings = checkout / "settings"
                settings.mkdir()
                home = self.home(client)
                if client == "copilot":
                    (home / ".copilot").symlink_to(settings)
                else:
                    (home / ".gemini").mkdir()
                    (home / ".gemini/config").symlink_to(settings)
                result = self.run_installer(client, home, checkout=checkout)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("checkout", result.stderr)
                self.assertFalse((home / ".local").exists())
                self.assertEqual(list(settings.iterdir()), [])

    def test_non_normalised_override_cannot_escape_through_the_pending_anchor(self):
        for client in self.clients:
            with self.subTest(client=client):
                checkout = self.checkout(f"non-normalised-{client}")
                home = self.home(client)
                variable = "COPILOT_HOME" if client == "copilot" else "GEMINI_HOME"
                override = str(home) + "/.local//share/artifice/client-profile"
                result = self.run_installer(client, home, checkout=checkout, extra_env={variable: override})
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertFalse((home / ".local").exists())
                self.assertFalse((checkout / "client-profile").exists())

    def test_destination_created_after_preflight_is_not_followed(self):
        bash_env = self.root / "race.bash"
        bash_env.write_text(
            'mkdir() {\n'
            '  command mkdir "$@" || return\n'
            '  if [[ ! -e "$RACE_DEST" && ! -L "$RACE_DEST" ]]; then\n'
            '    command mkdir -p "${RACE_DEST%/*}"\n'
            '    if [[ "$RACE_KIND" == directory ]]; then\n'
            '      command mkdir "$RACE_DEST"\n'
            '      printf "keep\\n" > "$RACE_DEST/keep"\n'
            '    else\n'
            '      printf "keep\\n" > "$RACE_DEST"\n'
            '    fi\n'
            '  fi\n'
            '}\n',
            encoding="utf-8",
        )
        for client in self.clients:
            for kind in ("file", "directory"):
                with self.subTest(client=client, kind=kind):
                    home = self.home(f"{client}-{kind}")
                    policy = self.policy(client, home)
                    result = self.run_installer(client, home, extra_env={
                        "BASH_ENV": str(bash_env), "RACE_DEST": str(policy), "RACE_KIND": kind,
                    })
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertNotIn("PASS:", result.stdout)
                    if kind == "directory":
                        self.assertEqual(list(policy.iterdir()), [policy / "keep"])
                    else:
                        self.assertEqual(policy.read_text(encoding="utf-8"), "keep\n")

    def test_non_writable_client_parent_fails_before_registration(self):
        for client in self.clients:
            with self.subTest(client=client):
                home = self.home(client)
                parent = self.policy(client, home).parent
                parent.mkdir(parents=True)
                parent.chmod(0o555)
                self.addCleanup(parent.chmod, 0o755)
                if os.access(parent, os.W_OK):
                    self.skipTest("This runner bypasses directory write permissions.")
                result = self.run_installer(client, home)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("writable", result.stderr)
                self.assertFalse((home / ".local").exists())

    def test_read_only_registered_policy_can_be_checked_without_writes(self):
        for client in self.clients:
            with self.subTest(client=client):
                home = self.home(client)
                self.assertEqual(self.run_installer(client, home).returncode, 0)
                parent = self.policy(client, home).parent
                parent.chmod(0o555)
                self.addCleanup(parent.chmod, 0o755)
                result = self.run_installer(client, home, "--check")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_later_runtime_failure_leaves_observable_partial_state(self):
        bash_env = self.root / "fail.bash"
        bash_env.write_text(
            'mkdir() {\n'
            '  if [[ "$1" == -p && "$2" == "$FAIL_PARENT" ]]; then\n'
            '    printf "simulated later failure\\n" >&2\n'
            '    return 1\n'
            '  fi\n'
            '  command mkdir "$@"\n'
            '}\n',
            encoding="utf-8",
        )
        for client in self.clients:
            with self.subTest(client=client):
                home = self.home(client)
                parent = self.policy(client, home).parent
                result = self.run_installer(client, home, extra_env={
                    "BASH_ENV": str(bash_env), "FAIL_PARENT": str(parent),
                })
                self.assertEqual(result.returncode, 1)
                self.assertIn("simulated later failure", result.stderr)
                self.assertNotIn("PASS:", result.stdout)
                self.assertTrue((home / ".local/share/artifice").is_symlink())
                result = self.run_installer(client, home, "--check")
                self.assertEqual(result.returncode, 1)
                self.assertIn("missing:", result.stdout)
                self.assertFalse(parent.exists())


class GlobalPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.policy = self.root / "canonical.md"
        self.policy.write_text("# Shared rules\n\nFixture.\n", encoding="utf-8")

    def diet(self, override=None):
        with patch.object(lint, "CANONICAL_GLOBAL_AGENTS_MD", str(self.policy), create=True), \
             patch.object(lint, "GLOBAL_AGENTS_MD", override), redirect_stdout(io.StringIO()):
            return lint.check_core_diet(str(self.root))

    def test_canonical_policy_exact_budgets_are_mandatory(self):
        for content, expected in (
            ("line\n" * 140, 0), ("line\n" * 141, 1),
            ("word " * 1400 + "\n", 0), ("word " * 1401 + "\n", 1),
        ):
            with self.subTest(lines=len(content.splitlines()), words=len(content.split())):
                self.policy.write_text(content, encoding="utf-8")
                self.assertEqual(self.diet(), expected)

    def test_external_override_cannot_hide_a_bad_canonical_policy(self):
        external = self.root / "personal.md"
        external.write_text("# Personal rules\n\nFixture.\n", encoding="utf-8")
        self.policy.write_text("word " * 1401, encoding="utf-8")
        self.assertEqual(self.diet(str(external)), 1)

    def test_missing_invalid_or_explicitly_unreadable_policies_fail(self):
        self.policy.unlink()
        self.assertEqual(self.diet(), 1)
        self.policy.write_bytes(b"\xff")
        self.assertEqual(self.diet(), 1)
        self.policy.write_text("# Rules\n\nFixture.\n", encoding="utf-8")
        self.assertEqual(self.diet(str(self.root / "missing.md")), 1)
        self.assertEqual(self.diet(""), 1)
        with patch("builtins.open", side_effect=PermissionError("unreadable policy")):
            self.assertEqual(self.diet(), 1)

    def test_portable_lint_reads_physical_checkout_policy_and_its_links(self):
        tooling = self.root / "tooling"
        scripts = tooling / "scripts"
        scripts.mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts/lint.py", scripts / "lint.py")
        policy = tooling / "rules/global-agents.md"
        policy.parent.mkdir()
        consumer = self.root / "consumer"
        consumer.mkdir()
        env = {"PATH": os.environ["PATH"], "HOME": str(self.root), "PYTHONDONTWRITEBYTECODE": "1"}
        cases = (
            ("# Rules\n\nWithin budget.\n", 0),
            ("# Rules\nNo blank line.\n", 1),
            ("# Rules\n\n[Missing](missing.md)\n", 1),
            ("word " * 1401, 1),
        )
        alias = self.root / "tooling alias"
        alias.symlink_to(tooling)
        for content, expected in cases:
            with self.subTest(content=content[:40]):
                policy.write_text(content, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(alias / "scripts/lint.py"), str(consumer)],
                    cwd=consumer, env=env, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        policy.unlink()
        result = subprocess.run(
            [sys.executable, str(scripts / "lint.py"), str(consumer)],
            env=env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_installed_policy_symlinks_resolve_links_from_the_canonical_directory(self):
        tooling = self.root / "tooling"
        script = tooling / "scripts/lint.py"
        script.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts/lint.py", script)
        policy = tooling / "rules/global-agents.md"
        policy.parent.mkdir()
        policy.write_text("# Rules\n\n[Tool](../scripts/lint.py)\n", encoding="utf-8")
        consumer = self.root / "consumer"
        consumer.mkdir()
        for placement in ("personal", "consumer"):
            with self.subTest(placement=placement):
                base = consumer if placement == "consumer" else self.root / "personal"
                installed = base / ".copilot/copilot-instructions.md"
                installed.parent.mkdir(parents=True)
                installed.symlink_to(policy)
                result = subprocess.run(
                    [sys.executable, str(script), str(consumer)],
                    env={
                        "PATH": os.environ["PATH"], "HOME": str(self.root),
                        "GLOBAL_AGENTS_PATH": str(installed), "PYTHONDONTWRITEBYTECODE": "1",
                    },
                    text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_empty_external_policy_is_reported_by_the_cli(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/lint.py"), str(self.root)],
            env={"PATH": os.environ["PATH"], "HOME": str(self.root), "GLOBAL_AGENTS_PATH": ""},
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Global policy error", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
