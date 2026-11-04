"""Static workflow contracts across canonical agents, skills, and Copilot adapters."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import lint


AGENTS = sorted((ROOT / "agents").glob("*/agent.md"))
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))
ADAPTERS = sorted((ROOT / "integrations/copilot/agents").glob("*.agent.md"))


class EntryPointTests(unittest.TestCase):
    def test_entry_point_counts_and_core_diet_budgets(self):
        self.assertEqual((len(AGENTS), len(SKILLS), len(ADAPTERS)), (3, 4, 3))
        for path in AGENTS + SKILLS:
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text()
                self.assertLessEqual(len(text.split()), 900 if path in AGENTS else 1000)
                if path in SKILLS:
                    self.assertLessEqual(len(text.splitlines()), 180)

    def test_antigravity_agent_frontmatter_declares_explicit_tools(self):
        for path in AGENTS:
            with self.subTest(role=path.parent.name):
                header = path.read_text().split("---", 2)[1]
                self.assertIn(f"name: {path.parent.name}", header)
                self.assertIn("description:", header)
                self.assertIn("tools:", header)
                self.assertIn("- read_file", header)

    def test_relative_documentation_links_resolve(self):
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

    def test_dynamic_model_selection_replaces_hardcoded_warm_tags(self):
        for relative in (
            "agents/code-author/agent.md",
            "agents/code-reviewer/agent.md",
            "skills/local-code/SKILL.md",
            "skills/review/SKILL.md",
        ):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text()
                self.assertIn("ARTIFICE_CODE_MODEL", text)
                self.assertIn("code_model", text)
                self.assertNotRegex(text, r"warm\s+(?:qwen2\.5|mistral-nemo)")

    def test_copilot_adapters_pass_static_contract_validation(self):
        self.assertEqual(lint.check_yaml_frontmatter(str(ROOT)), 0)
        for path in ADAPTERS:
            with self.subTest(adapter=path.name):
                text = path.read_text()
                self.assertIn("Inherit the selected model", text)
                self.assertIn("no generic fallback", text)
                self.assertNotRegex(text, r"(?m)^model:")


if __name__ == "__main__":
    unittest.main()
