"""Unit and black-box contract tests for Artifice scripts, adapters, and installer."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install_copilot.sh"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_ollama  # noqa: E402
import lint  # noqa: E402
import validate_egm  # noqa: E402


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home dir"
        self.home.mkdir()

    def run_installer(self, *args, home=None, copilot_home=None, extra_env=None):
        env = {"PATH": os.environ["PATH"], "HOME": str(home if home is not None else self.home)}
        if copilot_home is not None:
            env["COPILOT_HOME"] = str(copilot_home)
        env.update(extra_env or {})
        return subprocess.run(
            ["bash", str(INSTALLER), *args],
            cwd=self.tmp.name, env=env, text=True, capture_output=True,
        )

    def test_cli_help_and_invalid_args(self):
        self.assertEqual(self.run_installer("--help").returncode, 0)
        self.assertEqual(self.run_installer("--unknown").returncode, 2)
        self.assertFalse((self.home / ".copilot").exists())

    def test_invalid_paths_rejected_without_writes(self):
        self.assertEqual(self.run_installer(home="relative/home").returncode, 1)
        self.assertEqual(self.run_installer(copilot_home="relative/copilot").returncode, 1)
        self.assertEqual(self.run_installer(copilot_home=self.home / ".local/share/artifice/sub").returncode, 1)
        self.assertEqual(self.run_installer(copilot_home=REPO_ROOT / "sub").returncode, 1)

    def test_check_install_and_idempotence(self):
        self.assertEqual(self.run_installer("--check").returncode, 1)
        self.assertFalse((self.home / ".local").exists())

        res = self.run_installer()
        self.assertEqual(res.returncode, 0, res.stderr)
        anchor = self.home / ".local/share/artifice"
        self.assertEqual(anchor.resolve(), REPO_ROOT.resolve())
        self.assertEqual((self.home / ".copilot/agents").resolve(), (REPO_ROOT / "integrations/copilot/agents").resolve())
        self.assertEqual((self.home / ".copilot/skills").resolve(), (REPO_ROOT / "skills").resolve())

        agents = self.home / ".copilot/agents"
        agents.unlink()
        agents.symlink_to(REPO_ROOT / "integrations/copilot/agents")
        self.assertEqual(self.run_installer("--check").returncode, 0)
        self.assertEqual(self.run_installer().returncode, 0)
        alias = self.home / "copilot alias"
        alias.symlink_to(self.home / ".copilot")
        self.assertEqual(self.run_installer("--check", copilot_home=alias).returncode, 0)

    def test_unresolvable_parent_fails_before_mutation(self):
        root = Path(self.tmp.name).resolve()
        denied = root / "denied parent"
        denied.mkdir()
        requested = denied / root.relative_to("/") / "misregistered copilot"
        bash_env = root / "bash_env"
        # Stub writes so even the regressed installer cannot touch the host.
        bash_env.write_text(
            'cd() {\n'
            '    if [[ "$1" == "$DENIED_PARENT" ]]; then\n'
            '        printf "Permission denied (simulated): %s\\n" "$1" >&2\n'
            '        return 1\n'
            '    fi\n'
            '    builtin cd "$@"\n'
            '}\n'
            'mkdir() { printf "unexpected mutation: mkdir\\n" >&2; }\n'
            'ln() { printf "unexpected mutation: ln\\n" >&2; }\n',
            encoding="utf-8",
        )
        for args in (("--check",), ()):
            with self.subTest(args=args):
                result = self.run_installer(
                    *args, copilot_home=requested,
                    extra_env={"BASH_ENV": str(bash_env), "DENIED_PARENT": str(denied)},
                )
                self.assertIn("Permission denied (simulated)", result.stderr)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn("unexpected mutation:", result.stderr)
                self.assertNotIn("missing:", result.stdout)
                self.assertNotIn("PASS:", result.stdout)
        self.assertFalse((self.home / ".local").exists())
        self.assertFalse((root / "misregistered copilot").exists())

    def test_conflicts_and_bad_parents_never_overwritten(self):
        existing = self.home / ".copilot/agents"
        existing.mkdir(parents=True)
        marker = existing / "keep.md"
        marker.write_text("user file\n", encoding="utf-8")

        res = self.run_installer()
        self.assertEqual(res.returncode, 1)
        self.assertIn("conflict:", res.stdout)
        self.assertTrue(marker.is_file())
        self.assertFalse((self.home / ".local/share/artifice").exists())

        bad_home = Path(self.tmp.name) / "bad_home"
        bad_home.mkdir()
        (bad_home / ".copilot").write_text("file not dir\n", encoding="utf-8")
        self.assertEqual(self.run_installer(home=bad_home).returncode, 1)

        broken_home = Path(self.tmp.name) / "broken_home"
        (broken_home / ".copilot").mkdir(parents=True)
        (broken_home / ".copilot/skills").symlink_to("/nonexistent/artifice/skills")
        self.assertEqual(self.run_installer(home=broken_home).returncode, 1)


class ModelSelectionTests(unittest.TestCase):
    def setUp(self):
        env_patch = patch.dict(os.environ, {}, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        status_patch = patch.object(check_ollama, "get_status", return_value={
            "online": True,
            "available": ["mistral-nemo:latest", "qwen2.5:14b", "qwen2.5-coder:14b"],
            "resident": [{"name": "qwen2.5-coder:14b"}],
        })
        self.status = status_patch.start()
        self.addCleanup(status_patch.stop)

    def test_defaults_and_task_overrides(self):
        self.assertEqual(
            check_ollama.select_best_model("code"),
            {"model": "qwen2.5-coder:14b", "resident": True, "fallback": None},
        )
        self.assertEqual(
            check_ollama.select_best_model("prose"),
            {"model": "mistral-nemo:latest", "resident": False, "fallback": None},
        )
        with patch.dict(os.environ, {"ARTIFICE_CODE_MODEL": "qwen2.5:14b", "ARTIFICE_PROSE_MODEL": ""}):
            self.assertEqual(check_ollama.select_best_model("code")["model"], "qwen2.5:14b")
            empty_prose = check_ollama.select_best_model("prose")
            self.assertIsNone(empty_prose["model"])
            self.assertIsNone(empty_prose["fallback"])

    def test_uninstalled_and_offline_fallbacks_and_cli_exit_codes(self):
        with patch.dict(os.environ, {"ARTIFICE_CODE_MODEL": "missing:tag"}):
            res = check_ollama.select_best_model("code")
            self.assertEqual((res["model"], res["fallback"]), (None, None))

        self.status.return_value = {"online": False, "available": [], "resident": []}
        self.assertEqual(check_ollama.select_best_model("code")["fallback"], "cloud-flash")
        with patch.dict(os.environ, {"ARTIFICE_CODE_MODEL": "qwen2.5:14b"}):
            self.assertIsNone(check_ollama.select_best_model("code")["fallback"])

        buf = io.StringIO()
        with patch.object(sys, "argv", ["check_ollama.py", "select", "--task", "code"]), redirect_stdout(buf):
            with self.assertRaises(SystemExit) as exc:
                check_ollama.main()
        self.assertEqual(exc.exception.code, 2)
        self.assertIsNone(json.loads(buf.getvalue())["model"])


class LintAndContractTests(unittest.TestCase):
    def test_adapter_scalars_frontmatter_and_cli(self):
        cases = (
            ("name", 0, ("code-author", "'code-author'", '"code-author"')),
            ("name", 1, ('"code-author', "'code-author\"", '""code-author""', '" code-author "')),
            ("description", 0, (
                "Review code.", '"Review code."', "'Review code.'",
                '"[Beta] Review code."', "'[Beta] Review code.'",
                '"# Review code."', "'# Review code.'", '"null"', "'null'",
                "'It''s valid.'", '"Say \\"review\\"."', "'\\n'",
            )),
            ("description", 1, (
                "", "null", "Null", "NULL", "~", '""', "''", '"   "', '"\\n"',
                '"Review code.', "'Review code.\"", '""Review code.""', '"\\q"',
                "[Beta]", "{review: code}", "# comment",
            )),
            ("tools", 0, ('["read", \'search\', edit, execute, agent]',)),
            ("tools", 1, (
                '[read, search, edit, execute, "agent]',
                '[read, search, edit, execute, "agent\']',
                "[read, search, edit, execute, agent, agent]",
                "[read, search, edit, execute, web]",
            )),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = root / "integrations/copilot/agents/code-author.agent.md"
            adapter.parent.mkdir(parents=True)
            env = {"PATH": os.environ["PATH"], "HOME": tmp, "PYTHONDONTWRITEBYTECODE": "1"}
            for field, expected, values in cases:
                for value in values:
                    fields = {
                        "name": "code-author", "description": "Review code.",
                        "tools": "[read, search, edit, execute, agent]",
                    }
                    fields[field] = value
                    adapter.write_text(
                        "---\n" + "\n".join(f"{key}: {scalar}" for key, scalar in fields.items())
                        + "\n---\n\nRead `agents/code-author/agent.md`.\n", encoding="utf-8",
                    )
                    with redirect_stdout(io.StringIO()):
                        frontmatter = lint.check_yaml_frontmatter(tmp)
                    cli = subprocess.run(
                        [sys.executable, str(REPO_ROOT / "scripts/lint.py"), tmp],
                        env=env, text=True, capture_output=True,
                    )
                    for interface, actual in (("frontmatter", frontmatter), ("cli", cli.returncode)):
                        with self.subTest(field=field, value=value, interface=interface):
                            self.assertEqual(actual, expected, cli.stderr)

    def test_wrapper_uses_effective_target_for_unit_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tooling = root / "tooling checkout"
            consumer = root / "consumer project"
            consumer.mkdir()
            scripts = tooling / "scripts"
            scripts.mkdir(parents=True)
            for name in ("lint.sh", "lint.py"):
                shutil.copyfile(REPO_ROOT / "scripts" / name, scripts / name)
            tests = tooling / "tests"
            tests.mkdir()
            (tests / "test_sentinel.py").write_text(
                "import pathlib, sys, unittest\n"
                "ROOT = pathlib.Path(__file__).resolve().parents[1]\n"
                "sys.path.insert(0, str(ROOT / 'scripts'))\n"
                "import lint\n"
                "class Sentinel(unittest.TestCase):\n"
                "    def test_tooling_budget(self):\n"
                "        print('TOOLING_SENTINEL')\n"
                "        self.assertEqual(lint.check_core_diet(str(ROOT)), 0)\n",
                encoding="utf-8",
            )
            skill = tooling / "skills/fixture/SKILL.md"
            skill.parent.mkdir(parents=True)
            header = "---\nname: fixture\ndescription: Fixture\n---\n\n"
            skill.write_text(header + "word " * 1001, encoding="utf-8")
            env = {"PATH": os.environ["PATH"], "HOME": tmp, "PYTHONDONTWRITEBYTECODE": "1"}

            def run(cwd, *args):
                return subprocess.run(
                    ["bash", str(scripts / "lint.sh"), *args], cwd=cwd,
                    env=env, text=True, capture_output=True,
                )

            omitted, explicit = run(consumer), run(consumer, ".")
            self.assertEqual(omitted.returncode, 0, omitted.stdout + omitted.stderr)
            self.assertEqual(
                (omitted.returncode, omitted.stdout, omitted.stderr),
                (explicit.returncode, explicit.stdout, explicit.stderr),
            )
            self.assertNotIn("TOOLING_SENTINEL", omitted.stdout)

            skill.write_text(header + "Within budget.\n", encoding="utf-8")
            alias = root / "tooling alias"
            alias.symlink_to(tooling)
            for cwd, args in (
                (consumer, (str(tooling),)), (consumer, (str(alias),)),
                (tooling, ()), (tooling, (".",)),
            ):
                with self.subTest(cwd=cwd, args=args):
                    result = run(cwd, *args)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("TOOLING_SENTINEL", result.stdout)
            for flag, expected in (("--help", 0), ("-h", 0), ("--unknown", 2)):
                with self.subTest(flag=flag):
                    result = run(tooling, flag)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                    self.assertIn("usage:", result.stdout + result.stderr)
                    self.assertNotIn("TOOLING_SENTINEL", result.stdout)

    def test_live_repository_and_canonical_word_budget(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(lint.lint_repository(str(REPO_ROOT)), 0)

        canonical = [
            *(REPO_ROOT / "agents" / r / "agent.md" for r in ("code-author", "code-reviewer", "developer-coach")),
            *(REPO_ROOT / "skills" / s / "SKILL.md" for s in ("spec-egm", "review", "coach-frameworks", "local-code")),
        ]
        total_words = sum(len(p.read_text(encoding="utf-8").split()) for p in canonical)
        self.assertLessEqual(total_words, 4158)
        for path in canonical:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("/Users/", text)
            if "/scripts/" in text:
                self.assertIn("${ARTIFICE_ROOT:-$HOME/Repos/artifice}", text)

    def test_adapter_diet_and_bash_validation(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(lint.check_copilot_adapter(
                "integrations/copilot/agents/code-author.agent.md",
                ["name: code-author", "description: Valid", "tools: [read, search, edit, execute, agent]", "model: gpt-5"],
                "Read `agents/code-author/agent.md`.",
            ), 1)
            self.assertEqual(lint.check_copilot_adapter(
                "integrations/copilot/agents/code-author.agent.md",
                ["name: code-author", "description: Valid", "tools: [read, search, edit, execute, agent]"],
                "Read `agents/code-reviewer/agent.md`.",
            ), 1)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills/demo/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("word " * 1001, encoding="utf-8")
            bad_sh = root / "scripts/broken.sh"
            bad_sh.parent.mkdir(parents=True)
            bad_sh.write_text("#!/usr/bin/env bash\nif [\n", encoding="utf-8")
            with patch.object(lint, "GLOBAL_AGENTS_MD", str(root / "none.md")), redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_core_diet(str(root)), 1)
                self.assertEqual(lint.check_bash_syntax(str(root)), 1)


class PathTraversalTests(unittest.TestCase):
    """Tests for path traversal vulnerability fixes."""

    def test_sanitise_spec_path_rejects_traversal_sequences(self):
        designs_dir = "/tmp/docs/designs"
        with self.assertRaises(ValueError) as ctx:
            validate_egm.sanitise_spec_path("../../../etc/passwd", designs_dir)
        self.assertIn("path traversal", str(ctx.exception))
        
        with self.assertRaises(ValueError) as ctx:
            validate_egm.sanitise_spec_path("..", designs_dir)
        self.assertIn("path traversal", str(ctx.exception))
        
        with self.assertRaises(ValueError) as ctx:
            validate_egm.sanitise_spec_path("./test", designs_dir)
        self.assertIn("path traversal", str(ctx.exception))
        
        with self.assertRaises(ValueError) as ctx:
            validate_egm.sanitise_spec_path("test\\..\\test", designs_dir)
        self.assertIn("path traversal", str(ctx.exception))

    def test_sanitise_spec_path_accepts_valid_names(self):
        designs_dir = "/tmp/docs/designs"
        self.assertEqual(validate_egm.sanitise_spec_path("123-spec.md", designs_dir), "123-spec.md")
        self.assertEqual(validate_egm.sanitise_spec_path("spec-001", designs_dir), "spec-001")
        self.assertEqual(validate_egm.sanitise_spec_path("  spec-001  ", designs_dir), "spec-001")
        self.assertEqual(validate_egm.sanitise_spec_path("123", designs_dir), "123")
        self.assertIsNone(validate_egm.sanitise_spec_path(None, designs_dir))

    def test_validate_repo_rejects_traversal_in_spec_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            designs_dir = Path(tmp) / "docs" / "designs"
            designs_dir.mkdir(parents=True)
            spec_file = designs_dir / "001-test.md"
            spec_file.write_text("# 1. Overview & Objectives\n\n# 3. State Schema\n\n# 4. Invariants & Rules\n\n# 7. Verification\n\n---\nStatus: Approved\n", encoding="utf-8")
            
            with redirect_stdout(io.StringIO()):
                result = validate_egm.validate_repo(str(Path(tmp).resolve()), "../../../etc/passwd")
            self.assertEqual(result, 1)


class GlobalAgentsPathTests(unittest.TestCase):
    """Tests for GLOBAL_AGENTS_PATH environment variable configuration."""

    def test_global_agents_path_env_var_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom_path = Path(tmp) / "custom" / "AGENTS.md"
            custom_path.parent.mkdir(parents=True)
            custom_path.write_text("word " * 100, encoding="utf-8")
            
            with patch.dict(os.environ, {"GLOBAL_AGENTS_PATH": str(custom_path)}):
                with patch.object(lint, "GLOBAL_AGENTS_MD", str(custom_path)):
                    with redirect_stdout(io.StringIO()):
                        result = lint.check_core_diet(tmp)
                    self.assertEqual(result, 0)

    def test_default_global_agents_path_used_when_env_not_set(self):
        default_path = os.path.expanduser("~/.gemini/config/AGENTS.md")
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(lint, "GLOBAL_AGENTS_MD", default_path):
                with redirect_stdout(io.StringIO()):
                    lint.check_core_diet("/tmp")


class BashSyntaxRecursiveTests(unittest.TestCase):
    """Tests for recursive bash syntax checking across repository."""

    def test_check_bash_syntax_recursive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            
            # Create valid .sh files in various locations
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "valid.sh").write_text("#!/usr/bin/env bash\necho 'hello'\n", encoding="utf-8")
            
            (root / "tests").mkdir(parents=True)
            (root / "tests" / "test.sh").write_text("#!/usr/bin/env bash\necho 'test'\n", encoding="utf-8")
            
            # Create valid .sh file in subdirectory
            (root / "subdir" / "nested.sh").parent.mkdir(parents=True)
            (root / "subdir" / "nested.sh").write_text("#!/usr/bin/env bash\necho 'nested'\n", encoding="utf-8")
            
            # Create invalid .sh file
            (root / "scripts" / "invalid.sh").write_text("#!/usr/bin/env bash\nif [\n", encoding="utf-8")
            
            with redirect_stdout(io.StringIO()):
                errors = lint.check_bash_syntax(str(root))
            self.assertEqual(errors, 1)

    def test_check_bash_syntax_skips_forbidden_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            
            # Create .sh files in forbidden directories
            (root / ".git").mkdir(parents=True)
            (root / ".git" / "hooks" / "pre-commit.sh").parent.mkdir(parents=True)
            (root / ".git" / "hooks" / "pre-commit.sh").write_text("#!/usr/bin/env bash\nif [\n", encoding="utf-8")
            
            (root / "node_modules").mkdir(parents=True)
            (root / "node_modules" / "package" / "script.sh").parent.mkdir(parents=True)
            (root / "node_modules" / "package" / "script.sh").write_text("#!/usr/bin/env bash\nif [\n", encoding="utf-8")
            
            (root / ".system_generated").mkdir(parents=True)
            (root / ".system_generated" / "generated.sh").write_text("#!/usr/bin/env bash\nif [\n", encoding="utf-8")
            
            # Create valid .sh file outside forbidden dirs
            (root / "scripts" / "valid.sh").parent.mkdir(parents=True)
            (root / "scripts" / "valid.sh").write_text("#!/usr/bin/env bash\necho 'valid'\n", encoding="utf-8")
            
            with redirect_stdout(io.StringIO()):
                errors = lint.check_bash_syntax(str(root))
            # All .sh files in forbidden dirs should be skipped, so no errors
            self.assertEqual(errors, 0)


if __name__ == "__main__":
    unittest.main()
