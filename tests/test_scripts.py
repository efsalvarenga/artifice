#!/usr/bin/env python3
"""Unit tests for artifice scripts."""

import os
import subprocess
import tempfile
import unittest


class TestArtificeScripts(unittest.TestCase):

    def setUp(self):
        self.artifice_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

    def test_verify_script(self):
        if os.environ.get("ARTIFICE_IN_VERIFY") == "1":
            return
        env = dict(os.environ, ARTIFICE_IN_VERIFY="1")
        res = subprocess.run(
            ["./scripts/verify.sh"], cwd=self.artifice_root, capture_output=True, env=env
        )
        self.assertEqual(
            res.returncode,
            0,
            f"verify.sh failed:\n{res.stdout.decode()}\n{res.stderr.decode()}",
        )

    def test_lint_script(self):
        res = subprocess.run(
            ["./scripts/lint.sh"], cwd=self.artifice_root, capture_output=True, text=True
        )
        self.assertEqual(
            res.returncode,
            0,
            f"lint.sh failed:\n{res.stdout}\n{res.stderr}",
        )

    def test_build_review_dossier(self):
        cmd = [
            "python3",
            "scripts/build_review_dossier.py",
            self.artifice_root,
        ]
        res = subprocess.run(
            cmd, cwd=self.artifice_root, capture_output=True, text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Repository Invariant Dossier", res.stdout)
        self.assertIn("100% British English", res.stdout)

    def test_check_decisions(self):
        template_path = os.path.join(
            self.artifice_root,
            "skills/coordinate-fronts/references/decision-ledger-template.md",
        )
        cmd = ["python3", "scripts/check_decisions.py", template_path]
        res = subprocess.run(
            cmd, cwd=self.artifice_root, capture_output=True, text=True
        )
        self.assertEqual(
            res.returncode,
            0,
            f"check_decisions failed:\n{res.stdout}\n{res.stderr}",
        )

    def test_sabotage_check_probe(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = os.path.join(tmpdir, "sample.py")
            with open(sample_file, "w") as f:
                f.write(
                    "def is_valid(x):\n    return x > 0\n\ndef test():\n    assert is_valid(1)\n    assert not is_valid(0)\n"
                )

            # Probe with a mutation that breaks the test (returns x < 0 instead of x > 0)
            # The test will fail, so mutant is KILLED (exit 0)
            cmd = [
                "python3",
                os.path.join(self.artifice_root, "scripts/sabotage_check.py"),
                "probe",
                "--repo",
                tmpdir,
                "--file",
                "sample.py",
                "--old",
                "x > 0",
                "--new",
                "x < 0",
                "--test-cmd",
                f"python3 -c 'import sys; sys.path.insert(0, \"{tmpdir}\"); import sample; sample.test()'",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(
                res.returncode,
                0,
                f"Sabotage probe should have caught mutant:\n{res.stdout}\n{res.stderr}",
            )
            self.assertIn("KILLED", res.stdout)


if __name__ == "__main__":
    unittest.main()
