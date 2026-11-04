"""Black-box installer contracts; all mutations stay inside generated fixtures."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallerFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="artifice-installer-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.checkout = self.root / "checkout with spaces"
        self.checkout.mkdir()
        for directory in ("agents", "skills", "scripts", "integrations"):
            shutil.copytree(
                ROOT / directory, self.checkout / directory,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        self.home = self.root / "home with spaces"
        self.home.mkdir()
        self.copilot = self.home / ".copilot"
        self.anchor = self.home / ".local/share/artifice"
        self.consumer = self.root / "separate consuming repository"
        self.consumer.mkdir()
        self.shims = self.root / "shims"
        self.shims.mkdir()
        self.env = {
            "PATH": f"{self.shims}{os.pathsep}{os.defpath}",
            "HOME": str(self.home),
            "COPILOT_HOME": str(self.copilot),
            "ARTIFICE_TEST_ROOT": str(self.root),
            "ARTIFICE_TEST_PROBE": str(self.root / "unused probe"),
            "LC_ALL": "C",
        }

    def run_installer(self, *arguments, expected=0, environment=None):
        result = subprocess.run(
            ["bash", str(self.checkout / "scripts/install_copilot.sh"), *arguments],
            env=self.env if environment is None else environment,
            cwd=self.consumer, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def absent(self, path):
        self.assertFalse(path.exists() or path.is_symlink(), str(path))

    def links(self):
        for path, target in (
            (self.anchor, self.checkout),
            (self.copilot / "agents", self.anchor / "integrations/copilot/agents"),
            (self.copilot / "skills", self.anchor / "skills"),
        ):
            self.assertTrue(path.is_symlink(), str(path))
            self.assertEqual(os.readlink(path), str(target))

    def shim(self, command, action):
        self.assertIn(command, ("mkdir", "ln", "rm", "rmdir"))
        path = self.shims / command
        path.write_text(
            '#!/bin/bash\nset -eu\ndestination=${@: -1}\n'
            'case "$destination" in\n'
            '    "$ARTIFICE_TEST_ROOT"/*|"$ARTIFICE_TEST_PROBE") ;;\n'
            '    *) printf "UNSCOPED MUTATOR: %s\\n" "$destination" >&2; exit 99 ;;\n'
            'esac\n'
            f'printf "SHIM {command}: %s\\n" "$destination"\n' + action + "\n"
        )
        path.chmod(0o700)

    def fail_link(self):
        self.shim("ln", '''
if [[ "$destination" == "$COPILOT_HOME/skills" ]]; then exit 1; fi
/bin/ln "$@"
''')


class InstallerBaselineTests(InstallerFixture):
    """Freeze the expectations of the original 21 temporary-home cases."""

    def test_01_install_check_options_idempotence_and_source_visibility(self):
        self.run_installer("--check", expected=1)
        self.absent(self.home / ".local")
        self.absent(self.copilot)
        self.run_installer("--help")
        for arguments in (("--unknown",), ("--check", "unexpected"), ("--help", "extra"), ("extra",)):
            self.run_installer(*arguments, expected=2)
        self.absent(self.anchor)
        self.run_installer()
        self.links()
        self.run_installer()
        self.links()
        self.run_installer("--check")
        for path in (
            self.copilot / "agents/code-author.agent.md",
            self.copilot / "skills/spec-egm/references/design-spec-template.md",
            self.anchor / "scripts/validate_egm.py",
            self.anchor / "agents/code-author/agent.md",
        ):
            self.assertTrue(path.is_file(), str(path))
        (self.checkout / "skills/local-code/added-resource.md").write_text("new resource")
        self.assertEqual(
            (self.copilot / "skills/local-code/added-resource.md").read_text(),
            "new resource",
        )
        future = self.checkout / "skills/future-skill"
        future.mkdir()
        (future / "SKILL.md").write_text("future skill")
        self.assertEqual((self.copilot / "skills/future-skill/SKILL.md").read_text(), "future skill")
        for source, visible in (
            ("agents/code-author/agent.md", self.anchor / "agents/code-author/agent.md"),
            ("skills/local-code/SKILL.md", self.copilot / "skills/local-code/SKILL.md"),
        ):
            (self.checkout / source).write_text("changed source")
            self.assertEqual(visible.read_text(), "changed source")
        (future / "SKILL.md").unlink()
        self.absent(self.copilot / "skills/future-skill/SKILL.md")

    def test_02_custom_copilot_home(self):
        self.copilot = self.root / "custom copilot"
        self.env["COPILOT_HOME"] = str(self.copilot)
        self.run_installer()
        self.links()
        self.absent(self.home / ".copilot")

    def test_03_unset_copilot_home(self):
        del self.env["COPILOT_HOME"]
        self.run_installer()
        self.links()

    def test_04_equivalent_links_keep_their_literal_text(self):
        self.anchor.parent.mkdir(parents=True)
        self.copilot.mkdir()
        self.anchor.symlink_to(str(self.checkout) + "/.")
        (self.copilot / "agents").symlink_to(self.checkout / "integrations/copilot/agents")
        (self.copilot / "skills").symlink_to(str(self.checkout / "skills") + "/.")
        before = [os.readlink(p) for p in (self.anchor, self.copilot / "agents", self.copilot / "skills")]
        self.run_installer()
        self.run_installer("--check")
        self.assertEqual(before, [os.readlink(p) for p in (self.anchor, self.copilot / "agents", self.copilot / "skills")])

    def conflict(self, kind):
        self.copilot.mkdir()
        path = self.copilot / "skills"
        if kind == "directory":
            path.mkdir()
        elif kind == "file":
            path.write_text("prior content")
        else:
            path.symlink_to(self.home if kind == "wrong-link" else self.root / "missing")
        self.run_installer(expected=1)
        self.run_installer("--check", expected=1)
        self.absent(self.home / ".local")
        self.absent(self.copilot / "agents")
        self.assertTrue(path.exists() or path.is_symlink())
        if kind == "file":
            self.assertEqual(path.read_text(), "prior content")

    def test_05_directory_conflict(self):
        self.conflict("directory")

    def test_06_file_conflict(self):
        self.conflict("file")

    def test_07_wrong_link_conflict(self):
        self.conflict("wrong-link")

    def test_08_broken_link_conflict(self):
        self.conflict("broken-link")

    def test_09_non_directory_parent(self):
        (self.home / ".local").mkdir()
        (self.home / ".local/share").touch()
        self.run_installer(expected=1)
        self.absent(self.copilot)

    def test_10_missing_source_preflights_before_writing(self):
        (self.checkout / "agents/code-author/agent.md").unlink()
        self.run_installer(expected=1)
        self.absent(self.home / ".local")
        self.absent(self.copilot)

    def test_11_invalid_homes_and_resource_cycles(self):
        for key, value in (
            ("HOME", None), ("HOME", ""), ("HOME", "relative"),
            ("COPILOT_HOME", "relative"),
            ("COPILOT_HOME", str(self.checkout / "personal")),
            ("COPILOT_HOME", str(self.anchor / "personal")),
        ):
            with self.subTest(key=key, value=value):
                environment = dict(self.env)
                if value is None:
                    environment.pop(key)
                else:
                    environment[key] = value
                self.run_installer(expected=1, environment=environment)
                self.absent(self.home / ".local")
                self.absent(self.checkout / "personal")
                self.absent(self.copilot)

    def test_12_rollback_preserves_prior_anchor_and_retry_succeeds(self):
        self.anchor.parent.mkdir(parents=True)
        self.anchor.symlink_to(self.checkout)
        self.fail_link()
        self.run_installer(expected=1)
        self.assertTrue(self.anchor.is_symlink())
        self.absent(self.copilot)
        (self.shims / "ln").unlink()
        self.run_installer()
        self.links()

    def test_13_failed_link_rolls_back_all_new_paths(self):
        self.fail_link()
        self.run_installer(expected=1)
        self.absent(self.home / ".local")
        self.absent(self.copilot)

    def test_14_file_parent_cannot_be_cancelled_by_dot_dot(self):
        self.run_installer()
        self.env["COPILOT_HOME"] = str(self.copilot / "agents/code-reviewer.agent.md/../..")
        self.run_installer("--check", expected=1)
        self.links()

    def test_15_dot_dot_follows_physical_symlink_parent(self):
        target = self.root / "alias target"
        target.mkdir()
        (self.home / "alias").symlink_to(target)
        self.env["COPILOT_HOME"] = str(self.home / "alias/../physical copilot")
        self.run_installer()
        self.assertTrue((self.root / "physical copilot/skills").is_symlink())
        self.absent(self.home / "physical copilot")

    def test_16_interrupt_after_link_creation_before_bookkeeping(self):
        self.shim("ln", '''
/bin/ln "$@" || exit
if [[ "$destination" == "$COPILOT_HOME/skills" ]]; then kill -TERM "$PPID"; fi
''')
        self.run_installer(expected=1)
        self.absent(self.home / ".local")
        self.absent(self.copilot)

    def test_17_interrupt_after_directory_creation_before_bookkeeping(self):
        self.shim("mkdir", '/bin/mkdir "$@" || exit\nkill -TERM "$PPID"')
        self.run_installer(expected=1)
        self.absent(self.home / ".local")
        self.absent(self.copilot)

    def test_18_nonzero_after_successful_link_creation(self):
        self.shim("ln", '''
/bin/ln "$@" || exit
if [[ "$destination" == "$COPILOT_HOME/skills" ]]; then exit 143; fi
''')
        self.run_installer(expected=1)
        self.absent(self.home / ".local")
        self.absent(self.copilot)

    def test_19_nonzero_after_successful_directory_creation(self):
        self.shim("mkdir", '/bin/mkdir "$@" || exit\nexit 143')
        self.run_installer(expected=1)
        self.absent(self.home / ".local")
        self.absent(self.copilot)

    def test_20_any_working_directory_and_missing_anchor_check(self):
        self.run_installer()
        self.links()
        physical_root = (self.copilot / "skills/spec-egm/SKILL.md").resolve().parents[2]
        self.assertEqual(physical_root, self.checkout)
        self.anchor.unlink()
        self.assertTrue((physical_root / "scripts/validate_egm.py").is_file())
        self.run_installer("--check", expected=1)
        self.absent(self.anchor)

    def test_21_root_parent_probe_is_black_box_and_never_writes_to_root(self):
        probe = Path("/") / self.root.name
        self.absent(probe)
        self.env.update(COPILOT_HOME=str(probe), ARTIFICE_TEST_PROBE=str(probe))
        self.shim("mkdir", '''
if [[ "$destination" == "$ARTIFICE_TEST_PROBE" ]]; then
    printf 'ROOT-PARENT-PROBE\\n'
    exit 1
fi
/bin/mkdir "$@"
''')
        output = self.run_installer(expected=1)
        self.assertIn("ROOT-PARENT-PROBE", output)
        self.absent(probe)
        self.absent(self.home / ".local")


class InstallerContractTests(InstallerFixture):
    def test_empty_copilot_home_defaults(self):
        self.env["COPILOT_HOME"] = ""
        self.run_installer()
        self.links()

    def test_missing_home_fails_without_writes(self):
        self.env["HOME"] = str(self.root / "missing home")
        self.run_installer(expected=1)
        self.absent(self.root / "missing home")
        self.absent(self.copilot)

    def test_installer_root_comes_from_its_script_not_runtime_override(self):
        self.env["ARTIFICE_ROOT"] = str(self.consumer)
        self.run_installer()
        self.links()

    def test_unreadable_source_fails_before_writes(self):
        source = self.checkout / "agents/code-author/agent.md"
        previous_mode = source.stat().st_mode
        source.chmod(0)
        try:
            if os.access(source, os.R_OK):
                self.skipTest("Host privileges bypass fixture read permissions")
            self.run_installer(expected=1)
            self.absent(self.home / ".local")
            self.absent(self.copilot)
        finally:
            source.chmod(previous_mode)

    def test_all_required_sources_preflight(self):
        sources = (
            [f"agents/{r}/agent.md" for r in ("code-author", "code-reviewer", "developer-coach")]
            + [f"integrations/copilot/agents/{r}.agent.md" for r in ("code-author", "code-reviewer", "developer-coach")]
            + [f"skills/{s}/SKILL.md" for s in ("spec-egm", "review", "coach-frameworks", "local-code")]
            + [f"scripts/{s}.py" for s in ("validate_egm", "build_review_dossier", "check_ollama")]
        )
        for relative in sources:
            with self.subTest(source=relative):
                source = self.checkout / relative
                held = source.with_suffix(".held")
                source.rename(held)
                try:
                    self.run_installer(expected=1)
                    self.absent(self.home / ".local")
                    self.absent(self.copilot)
                finally:
                    held.rename(source)

    def test_check_never_calls_mutators(self):
        for command in ("mkdir", "ln", "rm", "rmdir"):
            self.shim(command, "exit 99")
        output = self.run_installer("--check", expected=1)
        self.assertNotIn("SHIM", output)
        self.absent(self.home / ".local")
        self.absent(self.copilot)
        for command in ("mkdir", "ln", "rm", "rmdir"):
            (self.shims / command).unlink()
        self.run_installer()
        for command in ("mkdir", "ln", "rm", "rmdir"):
            self.shim(command, "exit 99")
        self.assertNotIn("SHIM", self.run_installer("--check"))
        self.links()

    def test_relative_equivalent_links_are_preserved(self):
        self.anchor.parent.mkdir(parents=True)
        self.copilot.mkdir()
        self.anchor.symlink_to(os.path.relpath(self.checkout, self.anchor.parent))
        for name, source in (
            ("agents", self.checkout / "integrations/copilot/agents"),
            ("skills", self.checkout / "skills"),
        ):
            (self.copilot / name).symlink_to(os.path.relpath(source, self.copilot))
        before = os.readlink(self.anchor)
        self.run_installer()
        self.run_installer("--check")
        self.assertEqual(os.readlink(self.anchor), before)

    def test_symlinked_registration_parent_inside_checkout_is_rejected(self):
        (self.home / "alias").symlink_to(self.checkout)
        self.env["COPILOT_HOME"] = str(self.home / "alias/personal")
        self.run_installer(expected=1)
        self.absent(self.home / ".local")
        self.absent(self.checkout / "personal")

    def test_anchor_parent_resolving_inside_checkout_is_rejected(self):
        (self.home / ".local").symlink_to(self.checkout)
        self.run_installer(expected=1)
        self.absent(self.checkout / "share")
        self.absent(self.copilot)

    def test_missing_parent_before_dot_dot_is_not_lexically_cancelled(self):
        self.env["COPILOT_HOME"] = str(self.home / "missing/../copilot")
        self.run_installer(expected=1)
        self.absent(self.home / "missing")
        self.absent(self.home / ".local")

    def test_rollback_preserves_pre_existing_directories_and_links(self):
        self.anchor.parent.mkdir(parents=True)
        self.copilot.mkdir()
        self.anchor.symlink_to(self.checkout)
        (self.copilot / "agents").symlink_to(self.checkout / "integrations/copilot/agents")
        self.fail_link()
        self.run_installer(expected=1)
        self.assertTrue(self.anchor.parent.is_dir())
        self.assertTrue(self.copilot.is_dir())
        self.assertTrue(self.anchor.is_symlink())
        self.assertTrue((self.copilot / "agents").is_symlink())
        self.absent(self.copilot / "skills")

    def test_catchable_hangup_and_interrupt_roll_back(self):
        for signal in ("HUP", "INT"):
            with self.subTest(signal=signal):
                self.env["ARTIFICE_TEST_SIGNAL"] = signal
                self.shim("ln", '''
/bin/ln "$@" || exit
if [[ "$destination" == "$COPILOT_HOME/skills" ]]; then
    kill -"$ARTIFICE_TEST_SIGNAL" "$PPID"
fi
''')
                self.run_installer(expected=1)
                self.absent(self.home / ".local")
                self.absent(self.copilot)

    def test_cleanup_failures_are_reported(self):
        self.fail_link()
        self.shim("rm", "exit 1")
        output = self.run_installer(expected=1)
        self.assertIn("Rollback failed", output)
        self.assertTrue(self.anchor.is_symlink())
        self.assertTrue(self.checkout.is_dir())

    def test_changed_link_is_not_removed_by_rollback(self):
        self.shim("ln", '''
/bin/ln "$@" || exit
if [[ "$destination" == "$COPILOT_HOME/skills" ]]; then
    /bin/rm "$destination"
    /bin/ln -s "$HOME" "$destination"
    exit 143
fi
''')
        self.run_installer(expected=1)
        self.assertEqual(os.readlink(self.copilot / "skills"), str(self.home))
        self.assertTrue(self.home.is_dir())

    def test_moved_checkout_requires_explicit_anchor_repair(self):
        self.run_installer()
        old_checkout = self.checkout
        self.checkout = self.root / "moved checkout"
        old_checkout.rename(self.checkout)
        self.run_installer("--check", expected=1)
        self.run_installer(expected=1)
        self.assertEqual(os.readlink(self.anchor), str(old_checkout))
        self.assertTrue(self.anchor.is_symlink())
        self.assertFalse(self.anchor.exists())


if __name__ == "__main__":
    unittest.main()
