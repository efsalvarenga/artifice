"""Model selection contracts use mocked rosters, never the host daemon."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_ollama


CODE_TASKS = ("code", "logic", "fim", "tdd")
PROSE_TASKS = ("prose", "docs", "adr", "architecture")


class ModelSelectionTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        requests = patch.object(
            check_ollama, "request_json", side_effect=AssertionError("Unexpected daemon query")
        )
        self.request = requests.start()
        self.addCleanup(requests.stop)
        status = patch.object(check_ollama, "get_status")
        self.status = status.start()
        self.addCleanup(status.stop)
        self.status.return_value = {
            "online": True,
            "available": [
                "mistral-nemo:12b", "qwen2.5:14b",
                "vendor/qwen2.5-coder:14b-instruct", "qwen2.5-coder:14b",
                "mistral-nemo:latest", "qwen3.8:27b-mlx",
            ],
            "resident": [{"name": "qwen3.8:27b-mlx"}],
        }

    def success(self, result, model, resident=False):
        self.assertEqual(result, {"model": model, "resident": resident, "fallback": None})
        self.assertIs(type(result["model"]), str)
        self.assertIs(type(result["resident"]), bool)

    def failure(self, result, fallback, reason):
        self.assertEqual(set(result), {"model", "fallback", "reason"})
        self.assertIsNone(result["model"])
        self.assertEqual(result["fallback"], fallback)
        self.assertIsInstance(result["reason"], str)
        self.assertTrue(result["reason"].strip())
        self.assertIn(reason, result["reason"].lower())

    def cli(self, *arguments, expected):
        output = io.StringIO()
        with patch.object(sys, "argv", ["check_ollama.py", *arguments]), redirect_stdout(output):
            with self.assertRaises(SystemExit) as stopped:
                check_ollama.main()
        self.assertEqual(stopped.exception.code, expected)
        return json.loads(output.getvalue())

    def test_unset_defaults_preserve_preference_and_installed_order(self):
        for task in CODE_TASKS:
            with self.subTest(task=task):
                self.success(
                    check_ollama.select_best_model(task),
                    "vendor/qwen2.5-coder:14b-instruct",
                )
        for task in PROSE_TASKS:
            with self.subTest(task=task):
                self.success(check_ollama.select_best_model(task), "mistral-nemo:12b")

    def test_unset_coding_default_retains_secondary_family(self):
        self.status.return_value["available"] = ["other", "custom/qwen2.5:14b-v2", "qwen2.5:14b"]
        self.success(check_ollama.select_best_model("code"), "custom/qwen2.5:14b-v2")

    def test_selected_override_is_exact_and_residency_is_typed(self):
        for tasks, variable in (
            (CODE_TASKS, "ARTIFICE_CODE_MODEL"), (PROSE_TASKS, "ARTIFICE_PROSE_MODEL")
        ):
            for task in tasks:
                with self.subTest(task=task), patch.dict(os.environ, {variable: "qwen3.8:27b-mlx"}):
                    self.success(check_ollama.select_best_model(task), "qwen3.8:27b-mlx", True)

    def test_selected_nonresident_override(self):
        os.environ["ARTIFICE_CODE_MODEL"] = "mistral-nemo:latest"
        self.success(check_ollama.select_best_model("code"), "mistral-nemo:latest")

    def test_both_task_groups_may_share_the_same_exact_tag(self):
        os.environ.update(
            ARTIFICE_CODE_MODEL="qwen3.8:27b-mlx", ARTIFICE_PROSE_MODEL="qwen3.8:27b-mlx"
        )
        for task in (*CODE_TASKS, *PROSE_TASKS):
            with self.subTest(task=task):
                self.success(self.cli("select", "--task", task, expected=0), "qwen3.8:27b-mlx", True)

    def test_empty_selected_override_fails_before_daemon_query(self):
        for task, variable in (("code", "ARTIFICE_CODE_MODEL"), ("prose", "ARTIFICE_PROSE_MODEL")):
            with self.subTest(task=task), patch.dict(os.environ, {variable: ""}, clear=True):
                self.status.reset_mock()
                self.failure(self.cli("select", "--task", task, expected=2), None, "empty")
                self.status.assert_not_called()

    def test_invalid_other_group_is_ignored(self):
        for task, other, expected in (
            ("code", "ARTIFICE_PROSE_MODEL", "vendor/qwen2.5-coder:14b-instruct"),
            ("prose", "ARTIFICE_CODE_MODEL", "mistral-nemo:12b"),
        ):
            for invalid in ("", "not-installed"):
                with self.subTest(task=task, invalid=invalid), patch.dict(os.environ, {other: invalid}):
                    self.success(check_ollama.select_best_model(task), expected)
                selected = "ARTIFICE_CODE_MODEL" if task == "code" else "ARTIFICE_PROSE_MODEL"
                with self.subTest(task=task, override=True, invalid=invalid), patch.dict(
                    os.environ, {other: invalid, selected: "qwen3.8:27b-mlx"}
                ):
                    self.success(check_ollama.select_best_model(task), "qwen3.8:27b-mlx", True)

    def test_override_requires_exact_installed_tag_without_normalisation(self):
        for variable, task in (("ARTIFICE_CODE_MODEL", "code"), ("ARTIFICE_PROSE_MODEL", "docs")):
            for tag in ("qwen3.8", "qwen3.8:27b-mlx ", "QWEN3.8:27b-mlx", "missing:latest"):
                with self.subTest(task=task, tag=tag), patch.dict(os.environ, {variable: tag}):
                    self.failure(self.cli("select", "--task", task, expected=2), None, "installed")

    def test_offline_failure_fallback_depends_only_on_selected_override(self):
        self.status.return_value["online"] = False
        for task, selected, other in (
            ("code", "ARTIFICE_CODE_MODEL", "ARTIFICE_PROSE_MODEL"),
            ("prose", "ARTIFICE_PROSE_MODEL", "ARTIFICE_CODE_MODEL"),
        ):
            for environment, fallback in (
                ({}, "cloud-flash"), ({other: ""}, "cloud-flash"),
                ({selected: "qwen3.8:27b-mlx"}, None),
                ({selected: "missing:tag"}, None),
            ):
                with self.subTest(task=task, environment=environment), patch.dict(os.environ, environment, clear=True):
                    self.failure(self.cli("select", "--task", task, expected=2), fallback, "offline")

    def test_no_default_model_retains_advisory_cloud_hint(self):
        for task in (*CODE_TASKS, *PROSE_TASKS):
            with self.subTest(task=task):
                self.status.return_value["available"] = ["qwen3.8:27b-mlx"]
                self.failure(self.cli("select", "--task", task, expected=2), "cloud-flash", "suitable")

    def test_empty_roster_and_uninstalled_override_have_closed_failure_shapes(self):
        self.status.return_value["available"] = []
        self.failure(check_ollama.select_best_model("code"), "cloud-flash", "suitable")
        os.environ["ARTIFICE_CODE_MODEL"] = "qwen3.8:27b-mlx"
        self.failure(check_ollama.select_best_model("code"), None, "installed")

    def test_residency_matches_the_full_selected_tag(self):
        self.status.return_value["resident"] = [{"name": "vendor/qwen2.5-coder:14b"}]
        self.success(check_ollama.select_best_model("code"), "vendor/qwen2.5-coder:14b-instruct")
        self.status.return_value["resident"] = [{"name": "vendor/qwen2.5-coder:14b-instruct"}]
        self.success(check_ollama.select_best_model("code"), "vendor/qwen2.5-coder:14b-instruct", True)

    def test_cli_choices_are_unchanged(self):
        with patch.object(sys, "argv", ["check_ollama.py", "select", "--task", "unknown"]), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                check_ollama.main()
        self.assertEqual(stopped.exception.code, 2)
        self.status.assert_not_called()


class LifecycleInterfaceTests(unittest.TestCase):
    def test_status_preserves_roster_order_and_residency_interface(self):
        with patch.object(check_ollama, "request_json", side_effect=[
            (200, {"models": [{"name": "b:2"}, {"name": "a:1"}]}, 0.01),
            (200, {"models": [{"name": "a:1", "size_vram": 1024**3, "expires_at": "later"}]}, 0.01),
        ]) as request:
            result = check_ollama.get_status()
        self.assertEqual(result, {
            "online": True, "ping_ms": 10.0, "available": ["b:2", "a:1"],
            "resident": [{"name": "a:1", "size_vram_gb": 1.0, "expires_at": "later"}],
        })
        self.assertEqual([call.args[0] for call in request.call_args_list], ["/api/tags", "/api/ps"])

    def test_daemon_error_does_not_query_residency(self):
        with patch.object(check_ollama, "request_json", return_value=(0, {"error": "offline"}, 0.01)) as request:
            self.assertEqual(check_ollama.get_status(), {
                "online": False, "ping_ms": 10.0, "resident": [], "available": [], "error": "offline",
            })
        self.assertEqual(request.call_count, 1)

    def test_failed_residency_query_keeps_installed_roster(self):
        with patch.object(check_ollama, "request_json", side_effect=[
            (200, {"models": [{"name": "chosen:tag"}]}, 0.01), (0, {}, 0.01),
        ]):
            result = check_ollama.get_status()
        self.assertTrue(result["online"])
        self.assertEqual(result["available"], ["chosen:tag"])
        self.assertEqual(result["resident"], [])

    def test_warm_and_unload_preserve_exact_supplied_tags(self):
        tag = "qwen3.8:27b-mlx"
        with patch.object(check_ollama, "request_json", return_value=(200, {}, 0.02)) as request:
            self.assertEqual(check_ollama.warm_model(tag)["model"], tag)
            self.assertEqual(request.call_args.kwargs["data"], {"model": tag, "keep_alive": "5m"})
            self.assertEqual(check_ollama.unload_model(tag)["model"], tag)
            self.assertEqual(request.call_args.kwargs["data"], {"model": tag, "keep_alive": 0})


if __name__ == "__main__":
    unittest.main()
