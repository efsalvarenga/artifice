#!/usr/bin/env python3
"""test_validate_egm.py - Unit tests for validate_egm.py targeted spec validation."""

import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VALIDATE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "validate_egm.py")


class TestValidateEgm(unittest.TestCase):
    """Test suite asserting CLI contracts and validation logic of validate_egm.py."""

    def run_validator(self, *args):
        """Helper to run validate_egm.py via subprocess and return (exit_code, stdout, stderr)."""
        cmd = [sys.executable, VALIDATE_SCRIPT] + list(args)
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def test_validate_all_specs_in_repo(self):
        """Assert validating all specs in artifice succeeds."""
        code, stdout, _ = self.run_validator(REPO_ROOT)
        self.assertEqual(code, 0)
        self.assertIn("ALL EGM CONTRACTS VALIDATED SUCCESSFULLY", stdout)

    def test_validate_target_spec_by_prefix(self):
        """Assert validating spec by numeric prefix succeeds."""
        code, stdout, _ = self.run_validator(REPO_ROOT, "--spec", "001")
        self.assertEqual(code, 0)
        self.assertIn("001_sovereign_quota_fortress.md", stdout)
        self.assertIn("ALL EGM CONTRACTS VALIDATED SUCCESSFULLY", stdout)

    def test_validate_target_spec_by_filename(self):
        """Assert validating spec by exact filename succeeds."""
        code, stdout, _ = self.run_validator(
            REPO_ROOT, "--spec", "002_craftsman_tdd_pipeline.md"
        )
        self.assertEqual(code, 0)
        self.assertIn("002_craftsman_tdd_pipeline.md", stdout)
        self.assertIn("ALL EGM CONTRACTS VALIDATED SUCCESSFULLY", stdout)

    def test_validate_target_spec_not_found(self):
        """Assert validating non-existent spec returns exit code 1 with error."""
        code, stdout, _ = self.run_validator(REPO_ROOT, "--spec", "999")
        self.assertEqual(code, 1)
        self.assertIn("not found", stdout.lower())

    def test_validate_target_spec_unapproved(self):
        """Assert spec lacking Approved review fails validation with exit code 1."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            designs = os.path.join(tmp_dir, "docs", "designs")
            reviews = os.path.join(tmp_dir, "docs", "reviews")
            os.makedirs(designs)
            os.makedirs(reviews)

            spec_path = os.path.join(designs, "100_unapproved_spec.md")
            with open(spec_path, "w", encoding="utf-8") as f:
                f.write(
                    "# Design Spec\n\n"
                    "Status: Draft\n\n"
                    "## 1. Overview & Objectives\n\nOverview\n\n"
                    "## 3. State Schema\n\nSchema\n\n"
                    "## 4. Invariants & Rules\n\nInvariants\n\n"
                    "## 7. Verification\n\nVerification\n"
                )

            review_path = os.path.join(reviews, "100_unapproved_spec_review.md")
            with open(review_path, "w", encoding="utf-8") as f:
                f.write(
                    "# Goldfish Review\n\n"
                    "Verdict: Revisions Required\n\n"
                    "## 1. Executive Summary\n\nNeeds work\n"
                )

            code, stdout, _ = self.run_validator(tmp_dir, "--spec", "100")
            self.assertEqual(code, 1)
            self.assertIn("not approved", stdout.lower())


if __name__ == "__main__":
    unittest.main()
