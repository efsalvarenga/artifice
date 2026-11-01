#!/usr/bin/env python3
"""check_ollama.py - Zero-dependency Ollama lifecycle & residency manager for artifice.

Provides health checks, resident model inspection, wave-leasing, and cache flushing
for Apple Silicon on-device execution.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_TIMEOUT_SEC = 1.0


def request_json(path: str, data: dict = None, timeout: float = DEFAULT_TIMEOUT_SEC) -> tuple:
    """Send an HTTP request to the local Ollama API."""
    url = f"{OLLAMA_HOST}{path}"
    req = urllib.request.Request(url)
    if data is not None:
        req.add_header("Content-Type", "application/json")
        body = json.dumps(data).encode("utf-8")
    else:
        body = None

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, data=body, timeout=timeout) as resp:
            elapsed = time.perf_counter() - start
            res_body = resp.read().decode("utf-8")
            return resp.status, json.loads(res_body) if res_body else {}, elapsed
    except urllib.error.URLError as e:
        elapsed = time.perf_counter() - start
        return 0, {"error": str(e)}, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - start
        return 0, {"error": str(e)}, elapsed


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


def warm_model(model_name: str, keep_alive: str = "5m") -> dict:
    """Pre-heat a model into GPU memory with a lease."""
    payload = {
        "model": model_name,
        "keep_alive": keep_alive,
    }
    code, res, elapsed = request_json("/api/generate", data=payload, timeout=30.0)
    return {
        "success": code == 200,
        "model": model_name,
        "keep_alive": keep_alive,
        "load_time_sec": round(elapsed, 2),
        "error": res.get("error") if code != 200 else None,
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


def select_best_model(task_type: str) -> dict:
    """Select the best local model based on installed roster and task type."""
    status = get_status()
    if not status["online"]:
        return {
            "model": None,
            "fallback": "cloud-flash",
            "reason": "Ollama daemon is offline",
        }

    available = status["available"]

    if task_type in ("code", "logic", "fim", "tdd"):
        if any("qwen2.5-coder:14b" in m for m in available):
            chosen = next(m for m in available if "qwen2.5-coder:14b" in m)
        elif any("qwen2.5:14b" in m for m in available):
            chosen = next(m for m in available if "qwen2.5:14b" in m)
        else:
            chosen = None
    elif task_type in ("prose", "docs", "adr", "architecture"):
        if any("mistral-nemo" in m for m in available):
            chosen = next(m for m in available if "mistral-nemo" in m)
        else:
            chosen = None
    else:
        chosen = available[0] if available else None

    if chosen:
        is_resident = any(item["name"] == chosen for item in status["resident"])
        return {
            "model": chosen,
            "resident": is_resident,
            "fallback": None,
        }
    else:
        return {
            "model": None,
            "fallback": "cloud-flash",
            "reason": f"No suitable local model found for task '{task_type}'",
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
    select_parser = subparsers.add_parser("select", help="Select optimal model for task")
    select_parser.add_argument("--task", required=True, choices=["code", "logic", "fim", "tdd", "prose", "docs", "adr", "architecture"], help="Task type")

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
        res = select_best_model(args.task)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["model"] else 2)


if __name__ == "__main__":
    main()
