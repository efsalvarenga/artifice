#!/usr/bin/env python3
"""check_ollama.py - Zero-dependency Ollama lifecycle & residency manager for artifice.

Provides health checks, resident model inspection, wave-leasing, and cache flushing
for Apple Silicon on-device execution.
"""

import argparse
import json
import os
import sys

import model_inventory

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_TIMEOUT_SEC = 1.0


def request_json(path: str, data: dict = None, timeout: float = DEFAULT_TIMEOUT_SEC, host: str = None) -> tuple:
    """Use the same direct endpoint transport as inventory and selection."""
    host = os.environ.get("OLLAMA_HOST", OLLAMA_HOST) if host is None else host
    return model_inventory.request_json(path, data=data, timeout=timeout, host=host)


def get_status() -> dict:
    """Check daemon reachability, available models, and currently resident models."""
    status_code, tags_res, ping_time = request_json("/api/tags", timeout=1.5)
    if status_code != 200:
        return {
            "online": False,
            "ping_ms": round(ping_time * 1000, 2),
            "resident": [],
            "available": [],
            "error": tags_res.get("error", "Daemon unreachable"),
        }

    available_models = [m["name"] for m in tags_res.get("models", [])]

    # Query currently loaded models via /api/ps
    ps_code, ps_res, _ = request_json("/api/ps", timeout=1.5)
    resident_models = []
    if ps_code == 200:
        for m in ps_res.get("models", []):
            resident_models.append({
                "name": m.get("name"),
                "size_vram_gb": round(m.get("size_vram", 0) / (1024**3), 2),
                "expires_at": m.get("expires_at"),
            })

    return {
        "online": True,
        "ping_ms": round(ping_time * 1000, 2),
        "resident": resident_models,
        "available": available_models,
    }


def warm_model(model_name: str, keep_alive: str = "5m", options: dict = None, host: str = None) -> dict:
    """Pre-heat a model into GPU memory with a lease.

    Verifies that the model was successfully loaded by checking the response
    and confirming the model appears in the resident model list.
    """
    payload = {
        "model": model_name,
        "keep_alive": keep_alive,
    }
    if options:
        payload["options"] = options
    code, res, elapsed = request_json("/api/generate", data=payload, timeout=30.0, host=host)

    if code != 200:
        return {
            "success": False,
            "model": model_name,
            "keep_alive": keep_alive,
            "load_time_sec": round(elapsed, 2),
            "error": res.get("error") or f"HTTP {code} while warming model",
            "verified": False,
        }

    ps_code, ps_res, _ = request_json("/api/ps", timeout=2.0, host=host)
    entries = ps_res.get("models") if isinstance(ps_res, dict) else None
    valid = isinstance(entries, list) and all(
        isinstance(entry, dict) and isinstance(entry.get("name"), str) and entry["name"]
        for entry in entries
    )
    resident_models = [entry["name"] for entry in entries] if valid else []
    verified = ps_code == 200 and valid and model_name in resident_models
    error = None
    if ps_code != 200:
        detail = ps_res.get("error") if isinstance(ps_res, dict) else None
        detail = detail or f"HTTP {ps_code}"
        error = f"Cannot verify model residency: {detail}"
    elif not valid:
        error = "Cannot verify model residency: invalid metadata."
    elif not verified:
        error = f"Model '{model_name}' is not resident after warming."

    return {
        "success": verified,
        "model": model_name,
        "keep_alive": keep_alive,
        "load_time_sec": round(elapsed, 2),
        "error": error,
        "verified": verified,
    }


def unload_model(model_name: str) -> dict:
    """Instantly evict a model from GPU memory."""
    payload = {
        "model": model_name,
        "keep_alive": 0,
    }
    code, res, elapsed = request_json("/api/generate", data=payload, timeout=5.0)
    return {
        "success": code == 200,
        "model": model_name,
        "evicted": True,
        "time_ms": round(elapsed * 1000, 2),
        "error": res.get("error") if code != 200 else None,
    }


def unload_all() -> dict:
    """Evict all resident models from GPU memory to restore host RAM."""
    status = get_status()
    if not status["online"]:
        return {"online": False, "evicted": []}

    results = []
    for item in status["resident"]:
        res = unload_model(item["name"])
        results.append(res)

    return {"online": True, "evicted": results}


def select_best_model(task_type: str, model: str = None, expect_identity: str = None,
                      accept_unknown: bool = False, workdir: str = None,
                      min_context: int = None, required_capabilities=None) -> dict:
    """Resolve an explicit choice or one known-compatible installed model."""
    snapshot = None
    try:
        override = model_inventory.role_override(task_type, model)
        requested = model_inventory.requirements(
            task=task_type, accept_unknown=accept_unknown, local_only=True,
            min_context=min_context, required_capabilities=required_capabilities,
        )
        snapshot = model_inventory.discover(local_only=True, workdir=workdir)
        selected = model_inventory.select_candidate(
            snapshot, provider="ollama", model=override, task_requirements=requested,
            expect_identity=expect_identity,
        )
    except (ValueError, OSError) as error:
        return {
            "model": None,
            "fallback": None,
            "reason": str(error),
            "diagnostics": snapshot["diagnostics"] if snapshot is not None else [],
        }
    return {
        "model": selected["model_id"], "resident": selected["resident"], "fallback": None,
        "identity_fingerprint": selected["identity_fingerprint"], "reference": selected["reference"],
        "diagnostics": snapshot["diagnostics"],
    }


def main():
    parser = argparse.ArgumentParser(description="Ollama Lifecycle & Residency Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser("status", help="Get daemon status and resident models")

    # warm
    warm_parser = subparsers.add_parser("warm", help="Pre-heat a model into memory")
    warm_parser.add_argument("model", help="Model name to warm")
    warm_parser.add_argument("--lease", default="5m", help="Lease duration (e.g. 5m, 10m)")

    # unload
    unload_parser = subparsers.add_parser("unload", help="Unload model from memory")
    unload_parser.add_argument("model", nargs="?", default=None, help="Model to unload")
    unload_parser.add_argument("--all", action="store_true", help="Unload all resident models")

    # select
    select_parser = subparsers.add_parser("select", help="Resolve an exact or unambiguous compatible local model")
    select_parser.add_argument("--task", required=True, choices=model_inventory.TASKS, help="Task type")
    select_parser.add_argument("--model", help="Exact installed tag, overriding the role environment variable")
    select_parser.add_argument("--expect-identity", help="Fingerprint from the approved inventory")
    select_parser.add_argument("--accept-unknown", action="store_true", help="Explicitly accept unknown suitability")
    select_parser.add_argument("--min-context", type=int, help="Positive minimum context capacity")
    select_parser.add_argument("--require-capability", action="append", choices=model_inventory.CAPABILITIES, default=[])
    select_parser.add_argument("--workdir", help="Working directory for privacy policy")

    args = parser.parse_args()

    if args.command == "status":
        st = get_status()
        print(json.dumps(st, indent=2))
        sys.exit(0 if st["online"] else 1)

    elif args.command == "warm":
        res = warm_model(args.model, keep_alive=args.lease)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["success"] else 1)

    elif args.command == "unload":
        if args.all or not args.model:
            res = unload_all()
        else:
            res = unload_model(args.model)
        print(json.dumps(res, indent=2))
        sys.exit(0)

    elif args.command == "select":
        res = select_best_model(
            args.task, model=args.model, expect_identity=args.expect_identity,
            accept_unknown=args.accept_unknown, workdir=args.workdir,
            min_context=args.min_context, required_capabilities=args.require_capability,
        )
        for diagnostic in res.get("diagnostics", []):
            print(json.dumps(diagnostic, sort_keys=True), file=sys.stderr)
        if res.get("reason"):
            print(res["reason"], file=sys.stderr)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["model"] else 2)


if __name__ == "__main__":
    main()
