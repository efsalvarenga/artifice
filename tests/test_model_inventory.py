"""Contract tests for metadata-only model discovery and exact selection."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import model_inventory as inventory  # noqa: E402
import vibe_execute  # noqa: E402


TAG = "qwen3.8:27b-mlx"


def installed(name=TAG, **extra):
    return {"name": name, "model": name, "digest": "digest-" + name, "size": 1024, **extra}


def details(**extra):
    return {
        "capabilities": ["completion", "tools", "vision"],
        "model_info": {"example.context_length": 32768},
        "details": {"parameter_size": "3B", "quantization_level": "Q4"},
        **extra,
    }


class InventoryTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        resolver = patch.object(inventory, "find_vibe", return_value="")
        self.find_vibe = resolver.start()
        self.addCleanup(resolver.stop)
        self.tags = [installed()]
        self.detail_bodies = {}
        self.ps = (200, {"models": []}, 0.01)
        self.calls = []
        transport = patch.object(inventory, "request_json", side_effect=self.request)
        self.transport = transport.start()
        self.addCleanup(transport.stop)

    def request(self, path, data=None, timeout=3.0, host=None):
        self.calls.append((path, deepcopy(data), timeout, host))
        if path == "/api/tags":
            return 200, {"models": deepcopy(self.tags)}, 0.01
        if path == "/api/ps":
            return deepcopy(self.ps)
        if path == "/api/show":
            body = self.detail_bodies.get(data["model"], details())
            if isinstance(body, tuple):
                return deepcopy(body)
            return 200, deepcopy(body), 0.01
        self.fail("Discovery attempted a non-metadata endpoint: " + path)

    def discover(self, **kwargs):
        return inventory.discover(**kwargs)

    def test_unfamiliar_installed_model_has_evidence_not_a_quality_rank(self):
        snapshot = self.discover()
        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(snapshot["status"], "complete")
        self.assertEqual(len(snapshot["models"]), 1)
        model = snapshot["models"][0]
        self.assertEqual(model["model_id"], TAG)
        self.assertEqual(model["reference"], "ollama/default/" + TAG)
        self.assertEqual(model["execution_ref"], TAG)
        self.assertEqual(model["execution_locality"], "on_device")
        self.assertEqual(model["capabilities"]["chat"], True)
        self.assertEqual(model["context_tokens"], 32768)
        self.assertEqual(model["evidence"], ["installed"])
        self.assertEqual(len(model["identity_fingerprint"]), 64)
        self.assertNotIn("score", model)
        self.assertNotIn("recommended_model", snapshot)

    def test_all_models_are_sorted_deduplicated_and_namespaces_survive(self):
        self.tags = [installed("team/local-special:Case"), installed("a:1"), installed("a:1")]
        snapshot = self.discover()
        self.assertEqual([m["model_id"] for m in snapshot["models"]], ["a:1", "team/local-special:Case"])
        chosen = inventory.select_candidate(snapshot, provider="ollama", model="team/local-special:Case")
        self.assertEqual(chosen["reference"].split("/", 2)[2], "team/local-special:Case")
        self.tags.reverse()
        other = self.discover()
        self.assertEqual(snapshot["models"], other["models"])

    def test_empty_roster_is_complete_but_not_a_successful_selection(self):
        self.tags = []
        snapshot = self.discover()
        self.assertEqual(snapshot["status"], "complete")
        self.assertEqual(snapshot["models"], [])
        with self.assertRaises(inventory.SelectionError):
            inventory.select_candidate(snapshot, provider="ollama")

    def test_metadata_failure_keeps_identity_and_unknowns(self):
        self.ps = (503, {"error": "unavailable"}, 0.01)
        self.detail_bodies[TAG] = (404, {"error": "unsupported"}, 0.01)
        snapshot = self.discover()
        self.assertEqual(snapshot["status"], "partial")
        model = snapshot["models"][0]
        self.assertEqual(model["model_id"], TAG)
        self.assertIsNone(model["resident"])
        self.assertIsNone(model["capabilities"]["chat"])
        self.assertTrue(snapshot["diagnostics"])
        with self.assertRaises(inventory.SelectionError):
            inventory.select_candidate(snapshot, provider="ollama")
        chosen = inventory.select_candidate(
            snapshot, provider="ollama", model=TAG,
            task_requirements=inventory.requirements(accept_unknown=True),
        )
        self.assertEqual(chosen["model_id"], TAG)
        with self.assertRaises(inventory.SelectionError):
            inventory.select_candidate(
                snapshot, provider="ollama",
                task_requirements=inventory.requirements(accept_unknown=True),
            )

    def test_known_incompatibilities_cannot_be_waived(self):
        self.detail_bodies[TAG] = details(capabilities=["embedding"])
        snapshot = self.discover()
        for accept in (False, True):
            with self.subTest(accept=accept), self.assertRaises(inventory.SelectionError):
                inventory.select_candidate(
                    snapshot, provider="ollama", model=TAG,
                    task_requirements=inventory.requirements(accept_unknown=accept),
                )

    def test_context_limit_and_execution_mode_are_enforced(self):
        snapshot = self.discover()
        for requirements in (
            inventory.requirements(min_context=65536),
            inventory.requirements(mode="cli_agent"),
        ):
            with self.subTest(requirements=requirements), self.assertRaises(inventory.SelectionError):
                inventory.select_candidate(snapshot, provider="ollama", model=TAG, task_requirements=requirements)
        self.detail_bodies[TAG] = details(parameters="num_ctx 4096\n")
        snapshot = self.discover()
        self.assertEqual(snapshot["models"][0]["context_tokens"], 4096)
        with self.assertRaises(inventory.SelectionError):
            inventory.select_candidate(
                snapshot, provider="ollama", model=TAG,
                task_requirements=inventory.requirements(min_context=8192),
            )

    def test_conflicting_context_metadata_remains_unknown(self):
        self.detail_bodies[TAG] = details(model_info={
            "first.context_length": 32768, "second.context_length": 4096,
        })
        snapshot = self.discover()
        self.assertIsNone(snapshot["models"][0]["context_tokens"])
        self.assertIn("CONFLICTING_CONTEXT_METADATA", [item["code"] for item in snapshot["diagnostics"]])

    def test_ambiguous_selection_never_uses_list_order(self):
        self.tags.append(installed("another:latest"))
        snapshot = self.discover()
        with self.assertRaisesRegex(inventory.SelectionError, "multiple|Several|ambiguous"):
            inventory.select_candidate(snapshot, provider="ollama")
        self.assertEqual(inventory.select_candidate(snapshot, provider="ollama", model=TAG)["model_id"], TAG)

    def test_fingerprint_binds_digest_and_endpoint(self):
        snapshot = self.discover()
        expected = snapshot["models"][0]["identity_fingerprint"]
        self.tags[0]["digest"] = "new-digest"
        changed = self.discover()
        with self.assertRaises(inventory.SelectionError):
            inventory.select_candidate(changed, provider="ollama", model=TAG, expect_identity=expected)
        self.tags[0]["digest"] = "digest-" + TAG
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://127.0.0.1:11435"}):
            changed = self.discover()
        self.assertNotEqual(changed["models"][0]["identity_fingerprint"], expected)

    def test_conflicting_tag_identity_remains_unavailable_after_enrichment(self):
        self.tags.append(installed(digest="different-digest"))
        snapshot = self.discover()
        self.assertEqual(snapshot["status"], "partial")
        self.assertEqual(snapshot["models"][0]["dispatch_state"], "unavailable")
        with self.assertRaises(inventory.SelectionError):
            inventory.select_candidate(snapshot, provider="ollama", model=TAG)

    def test_duplicate_locality_conflicts_fail_closed_in_both_orders(self):
        for restricted, expected_locality in (
            (installed(remote_model="remote", remote_host="https://example.invalid"), "hosted"),
            (installed(size=0), "unknown"),
        ):
            local = installed()
            for order, tags in (("local-first", [local, restricted]), ("restricted-first", [restricted, local])):
                with self.subTest(locality=expected_locality, order=order):
                    self.tags = tags
                    self.calls.clear()
                    snapshot = self.discover(local_only=True)
                    self.assertEqual(snapshot["status"], "partial")
                    self.assertEqual(len(snapshot["models"]), 1)
                    model = snapshot["models"][0]
                    self.assertEqual(model["execution_locality"], expected_locality)
                    self.assertEqual(model["dispatch_state"], "unavailable")
                    self.assertTrue(model["identity_conflict"])
                    self.assertEqual(model["evidence"], ["configured"])
                    self.assertIn("MODEL_LOCALITY_CONFLICT", [item["code"] for item in snapshot["diagnostics"]])
                    self.assertNotIn("/api/show", [call[0] for call in self.calls])
                    for accept_unknown in (False, True):
                        with self.assertRaises(inventory.SelectionError):
                            inventory.select_candidate(
                                snapshot, provider="ollama", model=TAG,
                                task_requirements=inventory.requirements(
                                    local_only=True, accept_unknown=accept_unknown,
                                ),
                            )

    def test_invalid_configured_context_is_not_replaced_by_advertised_capacity(self):
        self.detail_bodies[TAG] = details(parameters="num_ctx -1\n")
        snapshot = self.discover()
        self.assertEqual(snapshot["status"], "partial")
        self.assertIsNone(snapshot["models"][0]["context_tokens"])
        self.assertIn("INVALID_CONTEXT_LIMIT", [item["code"] for item in snapshot["diagnostics"]])

    def test_cloud_backing_or_missing_weight_evidence_is_not_local(self):
        for tag, expected in (
            (installed(remote_model="remote", remote_host="https://example.invalid"), "hosted"),
            ({"name": TAG}, "unknown"),
        ):
            with self.subTest(tag=tag):
                self.tags = [tag]
                snapshot = self.discover(local_only=True)
                self.assertEqual(snapshot["models"][0]["execution_locality"], expected)
                with self.assertRaises(inventory.SelectionError):
                    inventory.select_candidate(
                        snapshot, provider="ollama", model=TAG,
                        task_requirements=inventory.requirements(local_only=True, accept_unknown=True),
                    )
        self.assertNotIn("/api/show", [call[0] for call in self.calls])

    def test_local_policy_disables_hosted_resolver_and_remote_endpoint(self):
        self.find_vibe.side_effect = AssertionError("Hosted resolver must not run")
        snapshot = self.discover(local_only=True)
        self.assertEqual(snapshot["providers"][1]["state"], "disabled")
        with patch.dict(os.environ, {"OLLAMA_HOST": "https://example.invalid"}):
            self.transport.reset_mock()
            with self.assertRaises(ValueError):
                self.discover(local_only=True)
            self.transport.assert_not_called()

    def test_repository_privacy_directive_is_applied_before_discovery(self):
        for text in ("Privacy: on-device\n", "* **Review:** `local-only`\n"):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                Path(tmp, "AGENTS.md").write_text(text, encoding="utf-8")
                self.find_vibe.side_effect = AssertionError("Hosted resolver must not run")
                snapshot = self.discover(workdir=tmp)
            self.assertTrue(snapshot["policy"]["local_only"])

    def test_hosted_cli_presence_is_explicitly_deferred(self):
        self.find_vibe.return_value = "/not-executed/vibe"
        snapshot = self.discover()
        hosted = next(p for p in snapshot["providers"] if p["provider"] == "mistral")
        self.assertEqual(hosted["state"], "unsupported_version")
        self.assertIn("HOSTED_DISCOVERY_DEFERRED", [d["code"] for d in snapshot["diagnostics"]])
        self.assertTrue(all(m["identity"][0] == "ollama" for m in snapshot["models"]))
        self.assertTrue(all(call[0] in ("/api/tags", "/api/ps", "/api/show") for call in self.calls))

    def test_malformed_entries_are_diagnosed_without_losing_valid_models(self):
        self.tags.extend([None, {}, {"name": ""}])
        snapshot = self.discover()
        self.assertEqual(snapshot["status"], "partial")
        self.assertEqual([m["model_id"] for m in snapshot["models"]], [TAG])

    def test_deadline_preserves_roster_and_bounds_operation_timeouts(self):
        self.tags = [installed("model:" + str(n)) for n in range(20)]
        clock = [0.0]
        original = self.request
        lock = threading.Lock()

        def delayed(*args, **kwargs):
            with lock:
                clock[0] += 1.0
                return original(*args, **kwargs)

        self.transport.side_effect = delayed
        with patch.object(inventory, "monotonic", side_effect=lambda: clock[0]):
            snapshot = self.discover(timeout_sec=3.0)
        self.assertEqual(len(snapshot["models"]), 20)
        self.assertEqual(snapshot["status"], "partial")
        self.assertTrue(all(0 < call[2] <= 3.0 for call in self.calls))
        self.assertLessEqual(clock[0], 3.0)

    def test_detail_concurrency_never_exceeds_four(self):
        self.tags = [installed("model:" + str(n)) for n in range(12)]
        original = self.request
        counts = {"active": 0, "max": 0}
        lock = threading.Lock()

        def concurrent(path, **kwargs):
            if path != "/api/show":
                return original(path, **kwargs)
            with lock:
                counts["active"] += 1
                counts["max"] = max(counts["max"], counts["active"])
            try:
                time.sleep(0.01)
                return original(path, **kwargs)
            finally:
                with lock:
                    counts["active"] -= 1

        self.transport.side_effect = concurrent
        snapshot = self.discover()
        self.assertEqual(snapshot["status"], "complete")
        self.assertEqual(len(snapshot["models"]), 12)
        self.assertLessEqual(counts["max"], 4)

    def test_invalid_requirements_are_errors_not_default_values(self):
        for kwargs in ({"task": "invalid"}, {"min_context": 0}, {"min_context": True},
                       {"mode": "invalid"}, {"required_capabilities": ["invalid"]}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                inventory.requirements(**kwargs)
        for kwargs in ({"workdir": ""}, {"local_only": 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.discover(**kwargs)

    def test_failed_run_surfaces_underlying_discovery_diagnostics(self):
        self.detail_bodies[TAG] = (503, {}, 0.01)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [
            "vibe_execute.py", "run", "Synthetic task", "--provider", "ollama", "--model", TAG, "--json",
        ]), redirect_stdout(stdout), redirect_stderr(stderr):
            code = vibe_execute.main()
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(stdout.getvalue())["success"])
        self.assertIn("MODEL_METADATA_UNAVAILABLE", stderr.getvalue())

    def test_discover_cli_json_and_exit_codes(self):
        for partial, expected in ((False, 0), (True, 1)):
            self.detail_bodies[TAG] = (500, {}, 0.01) if partial else details()
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, "argv", ["vibe_execute.py", "discover", "--local"]), \
                    redirect_stdout(stdout), redirect_stderr(stderr):
                code = vibe_execute.main()
            self.assertEqual(code, expected)
            self.assertEqual(json.loads(stdout.getvalue())["models"][0]["model_id"], TAG)
            if partial:
                self.assertTrue(stderr.getvalue())


class MetadataTransportTests(unittest.TestCase):
    def setUp(self):
        self.paths = []
        paths = self.paths

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                paths.append(self.path)
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/secret-target")
                    self.end_headers()
                    return
                if self.path == "/slow":
                    time.sleep(0.3)
                body = b'{"ok": true}' if self.path != "/invalid" else b"not-json"
                self.send_response(200)
                self.end_headers()
                try:
                    if self.path == "/drip":
                        for byte in body:
                            self.wfile.write(bytes([byte]))
                            self.wfile.flush()
                            time.sleep(0.02)
                    else:
                        self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.host = "http://127.0.0.1:" + str(self.server.server_port)

    def test_redirects_and_environment_proxies_are_not_used(self):
        with patch.dict(os.environ, {
            "HTTP_PROXY": "http://127.0.0.1:1", "http_proxy": "http://127.0.0.1:1",
            "NO_PROXY": "", "no_proxy": "",
        }):
            code, _, _ = inventory.request_json("/ok", host=self.host)
            self.assertEqual(code, 200)
            code, _, _ = inventory.request_json("/redirect", host=self.host)
        self.assertEqual(code, 302)
        self.assertEqual(self.paths, ["/ok", "/redirect"])

    def test_invalid_json_and_deadlines_return_explicit_errors(self):
        code, result, _ = inventory.request_json("/invalid", host=self.host)
        self.assertNotEqual(code, 200)
        self.assertTrue(result["error"])
        for path in ("/slow", "/drip"):
            start = time.monotonic()
            code, result, _ = inventory.request_json(path, host=self.host, timeout=0.05)
            self.assertEqual(code, 0)
            self.assertTrue(result["error"])
            self.assertLess(time.monotonic() - start, 0.2)

    def test_timeout_cannot_reopen_a_closed_connection_and_send_late(self):
        original = inventory.http.client.HTTPConnection
        connections = []

        class DelayedRequest(original):
            def connect(self):
                connections.append(True)
                return super().connect()

            def request(self, *args, **kwargs):
                time.sleep(0.08)
                return super().request(*args, **kwargs)

        with patch.object(inventory.http.client, "HTTPConnection", DelayedRequest):
            code, result, _ = inventory.request_json("/ok", host=self.host, timeout=0.03)
        self.assertEqual(code, 0)
        self.assertTrue(result["error"])
        self.assertEqual(len(connections), 1)
        self.assertEqual(self.paths, [])


if __name__ == "__main__":
    unittest.main()
