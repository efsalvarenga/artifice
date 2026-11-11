#!/usr/bin/env python3
"""mistral_embed.py - Generate text or code embeddings using mistral-embed and codestral-embed.

Part of the Artifice harness for Mistral AI specialised modalities.
"""

import argparse
import json
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


def generate_embeddings(
    texts: list[str],
    model: str = "mistral-embed",
    api_key: str = None,
) -> dict:
    """Send text batch to Mistral Embeddings endpoint."""
    api_key = api_key or get_api_key()
    endpoint = "https://api.mistral.ai/v1/embeddings"

    req_body = {
        "model": model,
        "input": texts,
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
        raise RuntimeError(f"Embeddings API request failed (HTTP {err.code}): {msg}") from err


def main():
    parser = argparse.ArgumentParser(
        description="Generate text or code embeddings using mistral-embed or codestral-embed."
    )
    parser.add_argument("inputs", nargs="+", help="Strings or file paths to embed.")
    parser.add_argument(
        "--model",
        choices=["mistral-embed", "codestral-embed"],
        default="mistral-embed",
        help="Embedding model ID (default: mistral-embed; use codestral-embed for source code).",
    )
    parser.add_argument(
        "--code",
        action="store_true",
        help="Shortcut to use codestral-embed model.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only vector dimensions and count instead of raw floats.",
    )
    parser.add_argument(
        "-o", "--output", help="Write JSON output to specified file instead of stdout."
    )

    args = parser.parse_args()
    model = "codestral-embed" if args.code else args.model

    items_to_embed = []
    for item in args.inputs:
        path = Path(item).expanduser()
        if path.is_file():
            try:
                items_to_embed.append(path.read_text(encoding="utf-8"))
            except OSError as err:
                print(f"Warning: Could not read file {item}: {err}", file=sys.stderr)
        else:
            items_to_embed.append(item)

    if not items_to_embed:
        print("Error: No valid input texts provided.", file=sys.stderr)
        sys.exit(1)

    try:
        result = generate_embeddings(items_to_embed, model=model)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.summary:
        data = result.get("data", [])
        dims = len(data[0]["embedding"]) if data else 0
        tokens = result.get("usage", {}).get("total_tokens", 0)
        output_text = json.dumps(
            {
                "model": model,
                "vectors": len(data),
                "dimensions": dims,
                "total_tokens": tokens,
            },
            indent=2,
        )
    else:
        output_text = json.dumps(result, indent=2)

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.write_text(output_text, encoding="utf-8")
        print(f"Embeddings written to {out_path}", file=sys.stderr)
    else:
        print(output_text)


if __name__ == "__main__":
    main()
