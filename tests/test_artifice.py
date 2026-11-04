"""Unit and black-box contract tests for Artifice scripts, adapters, and installer."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
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


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home dir"
        self.home.mkdir()

    def run_installer(self, *args, home=None, copilot_home=None):
        env = {"PATH": os.environ["PATH"], "HOME": str(home if home is not None else self.home)}
        if copilot_home is not None:
            env["COPILOT_HOME"] = str(copilot_home)
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

        self.assertEqual(self.run_installer("--check").returncode, 0)
        self.assertEqual(self.run_installer().returncode, 0)

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


if __name__ == "__main__":
    unittest.main()
