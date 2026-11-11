#!/usr/bin/env python3
"""mistral_ocr.py - Extract structured Markdown and formulas from documents using mistral-ocr-latest.

Part of the Artifice harness for Mistral AI specialised modalities.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def get_api_key() -> str:
    """Resolve Mistral API key from environment or ~/.vibe/.env."""
    key = os.environ.get("MISTRAL_API_KEY")
    if key:
        return key.strip()

    vibe_env = Path.home() / ".vibe" / ".env"
    if vibe_env.is_file():
        try:
            for line in vibe_env.read_text(encoding="utf-8").splitlines():
                if line.startswith("MISTRAL_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
        except OSError:
            pass

    print("Error: MISTRAL_API_KEY not found in environment or ~/.vibe/.env", file=sys.stderr)
    sys.exit(1)


def process_document(
    source_path_or_url: str,
    model: str = "mistral-ocr-latest",
    api_key: str = None,
    include_images: bool = False,
) -> dict:
    """Send document to Mistral OCR endpoint."""
    api_key = api_key or get_api_key()
    endpoint = "https://api.mistral.ai/v1/ocr"

    if source_path_or_url.startswith(("http://", "https://")):
        doc_payload = {
            "type": "document_url",
            "document_url": source_path_or_url,
        }
    else:
        path = Path(source_path_or_url).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {source_path_or_url}")

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/pdf" if path.suffix.lower() == ".pdf" else "image/png"

        raw_bytes = path.read_bytes()
        b64_content = base64.b64encode(raw_bytes).decode("ascii")
        data_uri = f"data:{mime_type};base64,{b64_content}"

        if mime_type.startswith("image/"):
            doc_payload = {
                "type": "image_url",
                "image_url": data_uri,
            }
        else:
            doc_payload = {
                "type": "document_url",
                "document_url": data_uri,
            }

    req_body = {
        "model": model,
        "document": doc_payload,
        "include_image_base64": include_images,
    }

    req = urllib.request.Request(endpoint)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.data = json.dumps(req_body).encode("utf-8")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("message", err_body)
        except Exception:
            msg = err_body
        raise RuntimeError(f"OCR API request failed (HTTP {err.code}): {msg}") from err


def main():
    parser = argparse.ArgumentParser(
        description="Extract Markdown and tables from PDFs/images using mistral-ocr-latest."
    )
    parser.add_argument("file_or_url", help="Path to local PDF/image or HTTP URL.")
    parser.add_argument(
        "--model", default="mistral-ocr-latest", help="OCR model ID (default: mistral-ocr-latest)."
    )
    parser.add_argument("--json", action="store_true", help="Output full JSON response.")
    parser.add_argument(
        "-o", "--output", help="Write output to specified file instead of stdout."
    )

    args = parser.parse_args()

    try:
        result = process_document(args.file_or_url, model=args.model)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output_text = json.dumps(result, indent=2)
    else:
        pages = result.get("pages", [])
        markdown_blocks = [page.get("markdown", "") for page in pages]
        output_text = "\n\n---\n\n".join(markdown_blocks)

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.write_text(output_text, encoding="utf-8")
        print(f"OCR output written to {out_path}", file=sys.stderr)
    else:
        print(output_text)


if __name__ == "__main__":
    main()
