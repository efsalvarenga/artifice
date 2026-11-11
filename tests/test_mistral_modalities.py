"""Tests for mistral_ocr.py specialised modality script."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import mistral_ocr  # noqa: E402


class MistralOCRTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_get_api_key_from_env(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "secret-test-key"}):
            self.assertEqual(mistral_ocr.get_api_key(), "secret-test-key")

    def test_get_api_key_from_vibe_env(self):
        vibe_dir = Path(self.tmp.name) / ".vibe"
        vibe_dir.mkdir(parents=True)
        env_file = vibe_dir / ".env"
        env_file.write_text('MISTRAL_API_KEY="vibe-secret-key"\n', encoding="utf-8")

        with patch.dict(os.environ, {}, clear=True), patch("pathlib.Path.home", return_value=Path(self.tmp.name)):
            self.assertEqual(mistral_ocr.get_api_key(), "vibe-secret-key")

    def test_ocr_process_document_url(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"pages": [{"markdown": "# Sample Heading"}]}).encode("utf-8")
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            res = mistral_ocr.process_document("https://example.com/doc.pdf", api_key="test-key")
            self.assertIn("pages", res)
            req = mock_urlopen.call_args[0][0]
            body = json.loads(req.data.decode("utf-8"))
            self.assertEqual(body["document"]["type"], "document_url")
            self.assertEqual(body["document"]["document_url"], "https://example.com/doc.pdf")

    def test_ocr_process_document_local_file(self):
        test_file = Path(self.tmp.name) / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 mock content")

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"pages": [{"markdown": "Page 1"}]}).encode("utf-8")
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            res = mistral_ocr.process_document(str(test_file), api_key="test-key")
            self.assertEqual(res["pages"][0]["markdown"], "Page 1")
            req = mock_urlopen.call_args[0][0]
            body = json.loads(req.data.decode("utf-8"))
            self.assertEqual(body["document"]["type"], "document_url")
            self.assertTrue(body["document"]["document_url"].startswith("data:application/pdf;base64,"))


if __name__ == "__main__":
    unittest.main()
