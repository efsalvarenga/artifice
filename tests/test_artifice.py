"""Unit and black-box contract tests for Artifice scripts, adapters, and installer."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install_copilot.sh"
ANTIGRAVITY_INSTALLER = REPO_ROOT / "scripts" / "install_antigravity.sh"
OMP_INSTALLER = REPO_ROOT / "scripts" / "install_omp.sh"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_review_dossier  # noqa: E402
import lint  # noqa: E402
import pr_checklist  # noqa: E402


class PrChecklistTests(unittest.TestCase):
    DESIGN = (
        "# Design\n\n## Technical Plan (Architecture)\n\n"
        "- glossary bullet that must NOT appear\n\n"
        "## Detailed Implementation Plan\n\n### Target Files\n\n"
        "1. `a.py` — **[Modify]**\n"
        "   - nested detail that must NOT appear\n"
        "2. `b.py` — **[Delete]**\n\n"
        "### Verification Plan\n\n* `./scripts/lint.sh`\n\n## Risks & Mitigations\n\n- none\n"
    )

    def test_generate_and_drift_check(self):
        items = pr_checklist.plan_items(self.DESIGN)
        self.assertEqual(items, ["`a.py` — **[Modify]**", "`b.py` — **[Delete]**"])
        markdown = pr_checklist.checklist_markdown(items)
        self.assertTrue(markdown.startswith("## Implementation Checklist\n\n- [ ] `a.py`"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            design = root / "design.md"
            design.write_text(self.DESIGN, encoding="utf-8")
            pr = root / "pr.md"
            pr.write_text("## Description\n\nx\n\n" + markdown + "\n## Verification\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pr_checklist.main([str(design), "--check", str(pr)]), 0)
            pr.write_text("## Implementation Checklist\n\n- [x] `a.py` — **[Modify]**\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pr_checklist.main([str(design), "--check", str(pr)]), 1)
            pr.write_text("## Implementation Checklist\n\n- [ ] `a.py` — **[Modify]**\n- [ ] extra step\n- [ ] `b.py` — **[Delete]**\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pr_checklist.main([str(design), "--check", str(pr)]), 1)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pr_checklist.main([str(root / "missing.md")]), 2)
            empty = root / "empty.md"
            empty.write_text("# No plan here\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pr_checklist.main([str(empty)]), 2)
            bad = root / "bad.md"
            bad.write_bytes(b"# \xff\xfe not utf-8\n")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pr_checklist.main([str(bad)]), 2)
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(pr_checklist.main([str(design)]), 0)
            self.assertIn("- [ ] `b.py`", out.getvalue())


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

    def test_installed_skills_use_canonical_resource_bases(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        for registered in sorted((self.home / ".copilot/skills").iterdir()):
            entrypoint = registered / "SKILL.md"
            if not entrypoint.is_file():
                continue
            with self.subTest(skill=registered.name):
                canonical = registered.resolve()
                self.assertEqual(canonical, (REPO_ROOT / "skills" / registered.name).resolve())
                text = entrypoint.read_text(encoding="utf-8")
                self.assertIn(f"resolve links from `ARTIFICE_ROOT/skills/{registered.name}/`", text)
                for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                    if not target.startswith("../"):
                        continue
                    resource = Path(os.path.normpath(canonical / target.split("#")[0]))
                    self.assertTrue(resource.is_file(), f"{registered.name}: {target}")

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


class AntigravityInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home dir"
        self.home.mkdir()

    def run_installer(self, *args, home=None, gemini_home=None, extra_env=None):
        env = {"PATH": os.environ["PATH"], "HOME": str(home if home is not None else self.home)}
        if gemini_home is not None:
            env["GEMINI_HOME"] = str(gemini_home)
        env.update(extra_env or {})
        return subprocess.run(
            ["bash", str(ANTIGRAVITY_INSTALLER), *args],
            cwd=self.tmp.name, env=env, text=True, capture_output=True,
        )

    def test_cli_help_and_invalid_args(self):
        self.assertEqual(self.run_installer("--help").returncode, 0)
        self.assertEqual(self.run_installer("--unknown").returncode, 2)
        self.assertFalse((self.home / ".gemini").exists())

    def test_check_install_and_idempotence(self):
        self.assertEqual(self.run_installer("--check").returncode, 1)
        res = self.run_installer()
        self.assertEqual(res.returncode, 0, res.stderr)
        anchor = self.home / ".local/share/artifice"
        self.assertEqual(anchor.resolve(), REPO_ROOT.resolve())
        self.assertEqual((self.home / ".gemini/config/agents").resolve(), (REPO_ROOT / "agents").resolve())
        self.assertEqual((self.home / ".gemini/config/skills").resolve(), (REPO_ROOT / "skills").resolve())
        self.assertTrue((self.home / ".gemini/config/skills.json").is_file())
        # Idempotence: check should now pass
        self.assertEqual(self.run_installer("--check").returncode, 0)
        self.assertEqual(self.run_installer().returncode, 0)

    def test_conflicts_and_bad_parents_never_overwritten(self):
        existing = self.home / ".gemini/config/agents"
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
        (bad_home / ".gemini").write_text("file not dir\n", encoding="utf-8")
        self.assertEqual(self.run_installer(home=bad_home).returncode, 1)

    def test_tilde_in_skills_json_triggers_conflict(self):
        self.assertEqual(self.run_installer().returncode, 0)
        skills_json = self.home / ".gemini/config/skills.json"
        skills_json.write_text('{"entries": [{"path": "~/.local/share/artifice/skills"}]}\n', encoding="utf-8")
        res = self.run_installer("--check")
        self.assertEqual(res.returncode, 1)
        self.assertIn("unresolved tilde", res.stdout)



class OmpInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home dir"
        self.home.mkdir()

    def run_installer(self, *args, home=None, agent_dir=None, profile=None, extra_env=None):
        env = {"PATH": os.environ["PATH"], "HOME": str(home if home is not None else self.home)}
        if agent_dir is not None:
            env["PI_CODING_AGENT_DIR"] = str(agent_dir)
        if profile is not None:
            env["OMP_PROFILE"] = profile
        env.update(extra_env or {})
        return subprocess.run(
            ["bash", str(OMP_INSTALLER), *args],
            cwd=self.tmp.name, env=env, text=True, capture_output=True,
        )

    def test_cli_help_and_invalid_args(self):
        self.assertEqual(self.run_installer("--help").returncode, 0)
        self.assertEqual(self.run_installer("--unknown").returncode, 2)
        self.assertFalse((self.home / ".omp").exists())

    def test_invalid_paths_rejected_without_writes(self):
        self.assertEqual(self.run_installer(agent_dir="relative/agent").returncode, 1)
        self.assertEqual(self.run_installer(agent_dir=self.home / ".local/share/artifice/sub").returncode, 1)
        self.assertEqual(self.run_installer(agent_dir=REPO_ROOT / "sub").returncode, 1)
        self.assertFalse((self.home / ".local").exists())

    def test_profile_resolution_uses_profile_agent_dir(self):
        res = self.run_installer(profile="work")
        self.assertEqual(res.returncode, 0, res.stderr)
        policy = self.home / ".omp/profiles/work/agent/AGENTS.md"
        self.assertTrue(policy.is_symlink())
        self.assertEqual(policy.resolve(), (REPO_ROOT / "rules/global-agents.md").resolve())
        self.assertFalse((self.home / ".omp/agent").exists())

    def test_check_install_and_idempotence(self):
        self.assertEqual(self.run_installer("--check").returncode, 1)
        self.assertFalse((self.home / ".local").exists())
        res = self.run_installer()
        self.assertEqual(res.returncode, 0, res.stderr)
        anchor = self.home / ".local/share/artifice"
        self.assertEqual(anchor.resolve(), REPO_ROOT.resolve())
        self.assertEqual((self.home / ".omp/agent/AGENTS.md").resolve(), (REPO_ROOT / "rules/global-agents.md").resolve())
        self.assertEqual((self.home / ".omp/agent/agents").resolve(), (REPO_ROOT / "integrations/omp/agents").resolve())
        config = self.home / ".omp/agent/config.yml"
        self.assertTrue(config.is_file())
        self.assertIn(str(anchor / "skills"), config.read_text(encoding="utf-8"))
        self.assertEqual(self.run_installer("--check").returncode, 0)
        before = config.read_text(encoding="utf-8")
        self.assertEqual(self.run_installer().returncode, 0)
        self.assertEqual(config.read_text(encoding="utf-8"), before)

    def test_config_conflict_snippet_and_no_writes(self):
        agent = self.home / ".omp/agent"
        agent.mkdir(parents=True)
        anchor_skills = str(self.home / ".local/share/artifice/skills")
        fixtures = (
            "skills:\n  customDirectories:\n    - /other/skills\n",
            "skills:\n  customDirectories: [/other/skills]\n",
            "modelRoles:\n  default: x\nskills:\n  hide: []\n",
            "other:\n  - %s\n" % anchor_skills,
            "skills:\n  customDirectories:\n    - /other/skills\n  hide:\n    - %s\n" % anchor_skills,
            "skills:\n  customDirectories: |\n    - %s\n" % anchor_skills,
        )
        for original in fixtures:
            with self.subTest(original=original):
                (agent / "config.yml").write_text(original, encoding="utf-8")
                res = self.run_installer()
                self.assertEqual(res.returncode, 1)
                self.assertIn("conflict:", res.stdout)
                self.assertIn(
                    f"  skills:\n    customDirectories:\n      - {anchor_skills}",
                    res.stdout,
                )
                self.assertEqual((agent / "config.yml").read_text(encoding="utf-8"), original)
                self.assertFalse((self.home / ".local/share/artifice").exists())

    def test_config_not_regular_file_conflicts(self):
        agent = self.home / ".omp/agent"
        agent.mkdir(parents=True)
        (agent / "config.yml").symlink_to("/nonexistent/config.yml")
        res = self.run_installer("--check")
        self.assertEqual(res.returncode, 1)
        self.assertIn("conflict:", res.stdout)
        (agent / "config.yml").unlink()
        (agent / "config.yml").mkdir()
        res = self.run_installer("--check")
        self.assertEqual(res.returncode, 1)
        self.assertIn("conflict:", res.stdout)

    def test_agent_dir_override_beats_profile(self):
        res = self.run_installer(profile="work", agent_dir=self.home / "custom agent")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue((self.home / "custom agent/AGENTS.md").is_symlink())
        self.assertFalse((self.home / ".omp").exists())

    def test_profile_with_slash_rejected(self):
        res = self.run_installer(profile="a/b")
        self.assertEqual(res.returncode, 1)
        self.assertIn("single path segment", res.stderr)
        self.assertFalse((self.home / ".omp").exists())

    def test_conflicts_and_bad_parents_never_overwritten(self):
        existing = self.home / ".omp/agent/agents"
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
        (bad_home / ".omp").write_text("file not dir\n", encoding="utf-8")
        self.assertEqual(self.run_installer(home=bad_home).returncode, 1)


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
                '"Review: code"', "'true'", '"42"', "Read https://example.com.",
            )),
            ("description", 1, (
                "", "null", "Null", "NULL", "~", '""', "''", '"   "', '"\\n"',
                '"Review code.', "'Review code.\"", '""Review code.""', '"\\q"',
                "[Beta]", "{review: code}", "# comment",
                "Review: code", "Review:", "*missing_alias", "&anchor Review",
                "!tag Review", "- Review", "? Review", "@Review", "`Review",
                "true", "false", "yes", "off", '"Review\x01code"',
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
            policy = tooling / "rules/global-agents.md"
            policy.parent.mkdir()
            policy.write_text("# Shared rules\n\nFixture policy.\n", encoding="utf-8")
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
            *(REPO_ROOT / "skills" / s / "SKILL.md" for s in ("review", "coach-frameworks")),
        ]
        total_words = sum(len(p.read_text(encoding="utf-8").split()) for p in canonical)
        self.assertLessEqual(total_words, 3300)
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
            self.assertEqual(lint.check_copilot_adapter(
                "integrations/copilot/agents/code-author.agent.md",
                ["name: code-author", "  description: Invalid indentation", "tools: [read, search, edit, execute, agent]"],
                "Read `agents/code-author/agent.md`.",
            ), 1)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills/demo/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("word " * 1001, encoding="utf-8")
            bad_sh = root / "scripts/broken.sh"
            bad_sh.parent.mkdir(parents=True)
            bad_sh.write_text("#!/usr/bin/env bash\nif [\n", encoding="utf-8")
            with patch.object(lint, "GLOBAL_AGENTS_MD", None), redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_core_diet(str(root)), 1)
                self.assertEqual(lint.check_bash_syntax(str(root)), 1)

    def test_omp_adapter_validation(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(lint.check_omp_adapter(
                "integrations/omp/agents/code-author.md",
                ["name: code-author", "description: Valid", "tools: [read, grep, glob, edit, write, bash, send_message, task, wait, todo]"],
                "Read `agents/code-author/agent.md`.",
            ), 0)
            self.assertEqual(lint.check_omp_adapter(
                "integrations/omp/agents/code-author.md",
                ["name: code-author", "description: Valid", "tools: [read, search, edit, execute, agent]"],
                "Read `agents/code-author/agent.md`.",
            ), 1)
            self.assertEqual(lint.check_omp_adapter(
                "integrations/omp/agents/code-author.md",
                ["name: code-author", "description: Valid", "tools: [read, grep, glob, edit, write, bash, send_message, task, wait, todo]"],
                "Read `agents/code-reviewer/agent.md`.",
            ), 1)

    def test_agent_frontmatter_rejects_duplicate_aliased_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "agents/demo/agent.md"
            agent.parent.mkdir(parents=True)
            header = "---\nname: demo\ndescription: Demo.\ntools:\n"
            body = "---\n\n# Demo\n"
            agent.write_text(
                header + "    - read_file\n    - grep_search\n" + body, encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 0)
            agent.write_text(
                header + "    - view_file\n    - read_file\n" + body, encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                header + "    - read_file\n    - read_file\n" + body, encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools: [view_file, read_file]\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools: [view_file, read_file] # main tools\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools: [view_file,\n  read_file]\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: >-\n  tools: [view_file, read_file]\ntools:\n    - read_file\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 0)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools: [\"x]\", view_file, read_file]\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools: [view_file, read_file\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools:\n  [view_file, read_file]\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools:\n-\n- view_file\n- read_file\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools: [\"a\\\"]\", view_file, read_file]\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\n\"tools\": [view_file, read_file]\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools : [view_file, read_file]\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)
            agent.write_text(
                "---\nname: demo\ndescription: Demo.\ntools: [view_file, # note\n  read_file]\n---\n\n# Demo\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_yaml_frontmatter(tmp), 1)

    def test_adapter_line_ceiling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok = root / "integrations/omp/agents/ok.md"
            ok.parent.mkdir(parents=True)
            ok.write_text("---\nname: ok\n---\n" + "line\n" * 50, encoding="utf-8")
            big = root / "integrations/copilot/agents/big.agent.md"
            big.parent.mkdir(parents=True)
            big.write_text("---\nname: big\n---\n" + "line\n" * 61, encoding="utf-8")
            with patch.object(lint, "GLOBAL_AGENTS_MD", None), redirect_stdout(io.StringIO()):
                self.assertEqual(lint.check_core_diet(str(root)), 1)


    def test_lint_allows_upstream_egm_design_doc_without_legacy_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            designs = root / "docs" / "designs"
            designs.mkdir(parents=True)
            (designs / "001_sample.md").write_text(
                "# Sample Upstream EGM Design\n"
                "\n"
                "## Overview\n"
                "\n"
                "Upstream-formatted design document without legacy numbered sections.\n"
                "\n"
                "## Goals\n"
                "\n"
                "* Deliver the feature.\n",
                encoding="utf-8",
            )
            with patch.object(lint, "GLOBAL_AGENTS_MD", None):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(lint.lint_repository(str(root)), 0)

    def test_build_review_dossier_omits_spec_invariant_scraper(self):
        self.assertFalse(hasattr(build_review_dossier, "extract_spec_invariants"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text(
                "# Rules\n"
                "\n"
                "* **Rule one:** Be deterministic.\n"
                "* **Rule two:** Be lean.\n",
                encoding="utf-8",
            )
            designs = root / "docs" / "designs"
            designs.mkdir(parents=True)
            (designs / "001_legacy.md").write_text(
                "# Legacy Spec\n"
                "\n"
                "## 4. Invariants & Rules\n"
                "\n"
                "* legacy scraper bait invariant\n",
                encoding="utf-8",
            )
            dossier = build_review_dossier.build_dossier(str(root), [])
            self.assertIn("Rule one", dossier)
            self.assertNotIn("legacy scraper bait invariant", dossier)
            self.assertNotIn("Spec (", dossier)

    def test_find_markdown_files_includes_github_and_skips_forbidden_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kept = (
                root / ".github" / "PULL_REQUEST_TEMPLATE.md",
                root / "node_modules_docs" / "valid.md",
            )
            skipped = root / ".git" / "bad.md"
            for path in kept:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# Heading\n\nValid.\n", encoding="utf-8")
            skipped.parent.mkdir(parents=True, exist_ok=True)
            skipped.write_text("# Heading\n\nSkipped.\n", encoding="utf-8")
            files = lint.find_markdown_files(str(root))
            for path in kept:
                self.assertIn(str(path), files)
            self.assertNotIn(str(skipped), files)

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

    def test_canonical_policy_used_without_a_personal_file(self):
        with tempfile.TemporaryDirectory() as consumer, patch.dict(os.environ, {}, clear=True):
            with patch.object(lint, "GLOBAL_AGENTS_MD", None):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(lint.check_core_diet(consumer), 0)


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
