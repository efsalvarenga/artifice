"""Static workflow contracts, not live client, model or privacy acceptance."""

import hashlib
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import lint


AGENTS = sorted((ROOT / "agents").glob("*/agent.md"))
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))
ADAPTERS = sorted((ROOT / "integrations/copilot/agents").glob("*.agent.md"))


class EntryPointTests(unittest.TestCase):
    def test_seven_entry_point_budgets_and_aggregate_target(self):
        self.assertEqual((len(AGENTS), len(SKILLS)), (3, 4))
        for path in AGENTS + SKILLS:
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text()
                self.assertLessEqual(len(text.split()), 900 if path in AGENTS else 1000)
                if path in SKILLS:
                    self.assertLessEqual(len(text.splitlines()), 180)
        self.assertLessEqual(sum(len(p.read_text().split()) for p in AGENTS + SKILLS), 4158)

    def test_original_antigravity_headers_are_unchanged(self):
        fingerprints = {
            "code-author": "98bed386296b309bb657f7f26dfcd9e0d4514d04b773e89779835910031f3569",
            "code-reviewer": "846fa92b4cef3d7fca7a145fa773b389a6fde21e6bc4a0cef89971f21e19881b",
            "developer-coach": "6a1917ccbb6f861aad1e264a92f2fb683c6a29c9840e30388021879c17a57717",
        }
        for path in AGENTS:
            with self.subTest(role=path.parent.name):
                header = path.read_text().split("---", 2)[1]
                self.assertEqual(hashlib.sha256(header.encode()).hexdigest(), fingerprints[path.parent.name])

    def test_selected_source_policy_is_present_in_every_entry_point(self):
        for path in AGENTS + SKILLS + ADAPTERS:
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text()
                policy = re.search(r"Select Artifice.*?(?=\n\n|\Z)", text, re.DOTALL)
                self.assertIsNotNone(policy, "Text-only discovery needs a self-contained policy")
                policy = policy.group()
                sources = ("`ARTIFICE_ROOT`", "`$HOME/.local/share/artifice`", "`$HOME/Repos/artifice`")
                positions = [policy.index(source) for source in sources]
                self.assertEqual(positions, sorted(positions))
                for phrase in (
                    "explicitly supplied", "present", "only the selected source",
                    "empty/invalid overrides", "broken/invalid selected anchors",
                    "without fallback", "unused lower-priority anchors",
                    "absolute", "physically", "readable `agents`, `skills`, `scripts`",
                    "requested asset", "No physical definition path is required",
                    "per command", "target repository is separate",
                ):
                    self.assertIn(phrase, policy)
                self.assertNotIn("definition's containing directory", text)

    def test_relative_documentation_links_are_restored_and_resolve(self):
        required = {
            "agents/code-author/agent.md": "../../skills/spec-egm/SKILL.md",
            "agents/code-reviewer/agent.md": "../../skills/review/SKILL.md",
            "agents/developer-coach/agent.md": "../../skills/coach-frameworks/SKILL.md",
            "skills/spec-egm/SKILL.md": "../../scripts/validate_egm.py",
            "skills/review/SKILL.md": "../../agents/code-reviewer/agent.md",
            "skills/coach-frameworks/SKILL.md": "../../agents/developer-coach/agent.md",
            "skills/local-code/SKILL.md": "../../agents/code-author/agent.md",
        }
        for relative, target in required.items():
            with self.subTest(path=relative):
                self.assertIn(f"]({target})", (ROOT / relative).read_text())
        self.assertEqual(
            lint.check_markdown_cleanliness_and_links(str(ROOT), [str(p) for p in AGENTS + SKILLS + ADAPTERS]),
            (0, 0),
        )

    def test_privacy_boundary_precedes_protected_reads_in_instructions(self):
        for relative in (
            "agents/code-author/agent.md", "agents/code-reviewer/agent.md",
            "skills/local-code/SKILL.md", "skills/review/SKILL.md",
        ):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text()
                self.assertIn("genuinely local session", text)
                self.assertRegex(text, r"before protected[- ](?:content )?(?:reads|ingestion)")
                self.assertIn("no cloud fallback", text)
                self.assertIn("hybrid", text.lower())
        reference = (ROOT / "skills/review/references/review-framework.md").read_text()
        self.assertNotIn("Security Guarantee", reference)
        self.assertIn("genuinely local session", reference)

    def test_selected_tags_reach_inference_review_and_provenance_examples(self):
        code_surfaces = (
            "agents/code-author/agent.md", "agents/code-reviewer/agent.md",
            "skills/local-code/SKILL.md", "skills/review/SKILL.md", "README.md",
        )
        prose_surfaces = ("agents/code-reviewer/agent.md", "skills/review/SKILL.md", "README.md")
        for relative in code_surfaces:
            with self.subTest(code_surface=relative):
                text = (ROOT / relative).read_text()
                self.assertIn("ARTIFICE_CODE_MODEL", text)
                self.assertIn("code_model", text)
        for relative in prose_surfaces:
            with self.subTest(prose_surface=relative):
                text = (ROOT / relative).read_text()
                self.assertIn("ARTIFICE_PROSE_MODEL", text)
                self.assertIn("prose_model", text)
        local = (ROOT / "skills/local-code/SKILL.md").read_text()
        self.assertRegex(local, r'["\']model["\']\s*:\s*code_model')
        self.assertIn("provenance", local.lower())
        for path in AGENTS + SKILLS + [ROOT / "skills/review/references/review-framework.md"]:
            with self.subTest(no_fixed_execution_tag=str(path.relative_to(ROOT))):
                self.assertNotRegex(
                    path.read_text(),
                    r'(?:warm |"model": |Co-authored-by: )[^\n]*(?:qwen2\.5|mistral-nemo)',
                )
                self.assertNotIn("100% On-Device Audit via Ollama (qwen", path.read_text())

    def test_authorisation_and_design_approval_are_not_granted_by_roles(self):
        for path in AGENTS + SKILLS:
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text()
                self.assertIn("preauthorisation", text)
                self.assertIn("Git", text)
                self.assertIn("approval", text)
        for path in ADAPTERS:
            with self.subTest(adapter=path.name):
                text = path.read_text()
                self.assertIn("Inherit the selected model", text)
                self.assertIn("no generic fallback", text)
                self.assertNotRegex(text, r"(?m)^model:")

    def test_copilot_quick_start_is_short_and_links_operational_details(self):
        text = (ROOT / "README.md").read_text()
        quick_start = text.split("## Integration with Copilot\n", 1)[1].split("### Verification", 1)[0].strip()
        self.assertLessEqual(len(quick_start.splitlines()), 22)
        for phrase in (
            "COPILOT_HOME", "$HOME/.local/share/artifice", "/agents", "/skills",
            "--check", "fresh", "#conflicts--recovery", "#workflow-boundaries",
        ):
            self.assertIn(phrase, quick_start)


if __name__ == "__main__":
    unittest.main()
