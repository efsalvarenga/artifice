"""Native adapter, word/line boundary, Markdown and Bash governance contracts."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lint


TOOLS = {
    "code-author": "read, search, edit, execute, agent",
    "code-reviewer": "read, search, execute, agent",
    "developer-coach": "read, search, edit, execute, web",
}


class LintFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="artifice-lint-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        global_rules = patch.object(lint, "GLOBAL_AGENTS_MD", str(self.root / "no global rules"))
        global_rules.start()
        self.addCleanup(global_rules.stop)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def quiet(self, function, *arguments):
        with redirect_stdout(io.StringIO()):
            return function(*arguments)


class CoreDietTests(LintFixture):
    def payload(self, words):
        prefix = "---\nname: entry\ndescription: entry\n---\n\n```\n"
        suffix = "\n```\n"
        return prefix + " ".join(["word"] * (words - len((prefix + suffix).split()))) + suffix

    def test_skill_word_boundaries_include_frontmatter_and_code(self):
        for words, expected in ((1000, 0), (1001, 1)):
            with self.subTest(words=words):
                text = self.payload(words)
                self.assertEqual(len(text.split()), words)
                self.write("skills/entry/SKILL.md", text)
                self.assertEqual(self.quiet(lint.check_core_diet, str(self.root)), expected)

    def test_agent_word_boundaries_include_frontmatter_and_code(self):
        for words, expected in ((900, 0), (901, 1)):
            with self.subTest(words=words):
                text = self.payload(words)
                self.assertEqual(len(text.split()), words)
                self.write("agents/entry/agent.md", text)
                self.assertEqual(self.quiet(lint.check_core_diet, str(self.root)), expected)

    def test_skill_line_boundaries(self):
        for lines, expected in ((180, 0), (181, 1)):
            with self.subTest(lines=lines):
                text = "word\n" * lines
                self.assertEqual(len(text.splitlines()), lines)
                self.write("skills/entry/SKILL.md", text)
                self.assertEqual(self.quiet(lint.check_core_diet, str(self.root)), expected)

    def test_long_unwrapped_paragraphs_cannot_evade_word_budgets(self):
        for relative, words in (("skills/entry/SKILL.md", 1001), ("agents/entry/agent.md", 901)):
            with self.subTest(relative=relative):
                path = self.write(relative, " ".join(["word"] * words))
                self.assertEqual(len(path.read_text().splitlines()), 1)
                self.assertEqual(self.quiet(lint.check_core_diet, str(self.root)), 1)
                path.unlink()

    def test_global_line_and_word_limits_remain_enforced(self):
        path = self.root / "global rules.md"
        with patch.object(lint, "GLOBAL_AGENTS_MD", str(path)):
            for text, expected in (
                ("word\n" * 140, 0), ("word\n" * 141, 1),
                ("word " * 1400, 0), ("word " * 1401, 1),
            ):
                with self.subTest(lines=len(text.splitlines()), words=len(text.split())):
                    path.write_text(text)
                    self.assertEqual(self.quiet(lint.check_core_diet, str(self.root)), expected)


class AdapterTests(LintFixture):
    def adapter(self, role="code-author"):
        return (
            f"---\nname: {role}\ndescription: Useful role.\ntools: [{TOOLS[role]}]\n---\n\n"
            f"Before acting, read `agents/{role}/agent.md` under the validated root.\n"
            "Apply its Markdown body. Its YAML frontmatter is Antigravity metadata, not Copilot tools.\n"
            "Inherit the selected model. If loading fails, stop; no generic fallback.\n"
        )

    def setUp(self):
        super().setUp()
        for role in TOOLS:
            self.write(f"integrations/copilot/agents/{role}.agent.md", self.adapter(role))

    def check(self):
        return self.quiet(lint.check_yaml_frontmatter, str(self.root))

    def test_valid_inline_adapters_and_block_canonical_frontmatter(self):
        self.write("skills/entry/SKILL.md", "---\nname: entry\ndescription: >-\n  Multiline description.\n---\n")
        self.write("agents/entry/agent.md", "---\nname: entry\ndescription: >-\n  Role description.\ntools:\n    - read_file\n---\n")
        self.assertEqual(self.check(), 0)

    def test_malformed_adapter_metadata_is_rejected(self):
        valid = self.adapter()
        mutations = {
            "missing opener": valid.removeprefix("---\n"),
            "missing closer": valid.replace("\n---\n\n", "\n\n", 1),
            "wrong name": valid.replace("name: code-author", "name: code-reviewer"),
            "blank description": valid.replace("description: Useful role.", "description:   "),
            "quoted empty description": valid.replace("description: Useful role.", 'description: ""'),
            "null description": valid.replace("description: Useful role.", "description: null"),
            "comment-only description": valid.replace("description: Useful role.", "description: # only a comment"),
            "empty sequence description": valid.replace("description: Useful role.", "description: []"),
            "sequence description": valid.replace("description: Useful role.", "description: [Useful role.]"),
            "empty mapping description": valid.replace("description: Useful role.", "description: {}"),
            "mapping description": valid.replace("description: Useful role.", "description: {purpose: review}"),
            "unmatched sequence description": valid.replace("description: Useful role.", "description: ]"),
            "unmatched mapping description": valid.replace("description: Useful role.", "description: }"),
            "duplicate tools field": valid.replace("tools: [read", "tools: [read]\ntools: [read"),
            "block description": valid.replace("description: Useful role.", "description: >-\n  Useful role."),
            "block name": valid.replace("name: code-author", "name: >-\n  code-author"),
            "missing tools": valid.replace(f"tools: [{TOOLS['code-author']}]\n", ""),
            "block tools": valid.replace(f"tools: [{TOOLS['code-author']}]", "tools:\n  - read"),
            "duplicate tools": valid.replace("read, search", "read, read, search"),
            "wildcard tools": valid.replace("read, search", "*, search"),
            "extra tool": valid.replace("read, search", "web, read, search"),
            "missing tool": valid.replace("edit, ", ""),
            "model field": valid.replace("name: code-author", "name: code-author\nmodel: hidden"),
            "empty model field": valid.replace("name: code-author", "name: code-author\nmodel:"),
            "duplicate name": valid.replace("name: code-author", "name: code-author\nname: code-author"),
            "duplicate description": valid.replace("description: Useful role.", "description: Useful role.\ndescription: Again."),
        }
        for label, text in mutations.items():
            with self.subTest(label=label):
                self.write("integrations/copilot/agents/code-author.agent.md", text)
                self.assertGreater(self.check(), 0)

    def test_quoted_descriptions_preserve_literal_yaml_markers(self):
        for value in ("# only a comment", "[]", "{}", "]", "}"):
            for quote in ("'", '"'):
                with self.subTest(value=value, quote=quote):
                    description = f"{quote}{value}{quote}"
                    text = self.adapter().replace("description: Useful role.", f"description: {description}")
                    self.write("integrations/copilot/agents/code-author.agent.md", text)
                    self.assertEqual(self.check(), 0)

    def test_role_specific_tool_sets_are_exact(self):
        for role, forbidden in (("code-reviewer", "edit"), ("developer-coach", "agent")):
            with self.subTest(role=role):
                relative = f"integrations/copilot/agents/{role}.agent.md"
                try:
                    self.write(relative, self.adapter(role).replace("tools: [read", f"tools: [{forbidden}, read"))
                    self.assertGreater(self.check(), 0)
                finally:
                    self.write(relative, self.adapter(role))

    def test_unknown_or_mismatched_filenames_are_rejected(self):
        path = self.root / "integrations/copilot/agents/code-author.agent.md"
        for filename in ("unknown.agent.md", "code-author.md"):
            with self.subTest(filename=filename):
                renamed = path.with_name(filename)
                path.rename(renamed)
                try:
                    self.assertGreater(self.check(), 0)
                finally:
                    renamed.rename(path)

    def test_loading_target_and_fail_closed_directive_are_required(self):
        valid = self.adapter()
        for text in (
            valid.replace("agents/code-author/agent.md", "agents/code-reviewer/agent.md"),
            valid.replace("Before acting, read", "Eventually consider"),
            valid.replace("Apply its Markdown body.", "Use its tool header."),
            valid.replace("stop; no generic fallback", "continue with a generic role"),
            valid.replace("Inherit the selected model.", "Choose another model."),
        ):
            with self.subTest(body=text):
                self.write("integrations/copilot/agents/code-author.agent.md", text)
                self.assertGreater(self.check(), 0)

    def test_loading_must_use_the_validated_root_not_a_registration_or_target(self):
        valid = self.adapter()
        for text in (
            valid.replace("under the validated root", "under the consuming repository"),
            valid.replace(
                "`agents/code-author/agent.md` under the validated root",
                "`~/.local/share/artifice/agents/code-author/agent.md`",
            ),
        ):
            with self.subTest(body=text):
                self.write("integrations/copilot/agents/code-author.agent.md", text)
                self.assertGreater(self.check(), 0)


class NativeGovernanceTests(LintFixture):
    def test_relative_link_and_heading_checks_remain_active(self):
        self.write("scripts/utility.py", "# Utility.\n")
        document = self.write("skills/example.md", "# Example\n\n[Utility](../scripts/utility.py)\n")
        self.assertEqual(lint.check_markdown_cleanliness_and_links(str(self.root), [str(document)]), (0, 0))
        document.write_text("# Example\n[Missing](../scripts/missing.py)\n")
        self.assertEqual(
            self.quiet(lint.check_markdown_cleanliness_and_links, str(self.root), [str(document)]),
            (1, 1),
        )

    def test_bash_syntax_checks_every_script_without_executing_them(self):
        self.write("scripts/valid.sh", "#!/bin/bash\nexit 99\n")
        broken = self.write("tests/broken.sh", "#!/bin/bash\nif then\n")
        self.assertGreater(self.quiet(lint.check_bash_syntax, str(self.root)), 0)
        broken.write_text("#!/bin/bash\nexit 98\n")
        self.assertEqual(self.quiet(lint.check_bash_syntax, str(self.root)), 0)

    def test_bash_syntax_is_integrated_in_native_lint(self):
        with patch.object(lint, "check_bash_syntax", return_value=1) as syntax:
            self.assertEqual(self.quiet(lint.lint_repository, str(self.root)), 1)
        syntax.assert_called_once_with(str(self.root))

    def test_missing_bash_is_reported_as_a_lint_failure(self):
        self.write("scripts/valid.sh", "#!/bin/bash\nexit 99\n")
        with patch.object(lint.subprocess, "run", side_effect=OSError("Bash unavailable")):
            self.assertEqual(self.quiet(lint.check_bash_syntax, str(self.root)), 1)


if __name__ == "__main__":
    unittest.main()
