#!/usr/bin/env python3
"""vibe_execute.py - Zero-dependency external execution gateway and task classifier.

Evaluates task complexity across non-Gemini execution options:
- Branch A: Hosted Mistral via Vibe CLI (fast, codestral, medium-3.5, large)
- Branch B: On-Device Engine via Ollama / local-code (qwen2.5:14b, mistral-nemo)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

# Ensure scripts directory is available for sibling imports
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    import check_ollama
except ImportError:
    check_ollama = None

VIBE_BIN = os.environ.get("VIBE_BIN")
DEFAULT_VIBE_HOME = os.path.expanduser("~/.vibe")

# Complexity classification heuristics
LOCAL_KEYWORDS = {
    "local", "offline", "private", "confidential", "secret", "air-gap",
    "airgap", "vault", "on-device", "zero-quota"
}

CODE_KEYWORDS = {
    "code", "refactor", "function", "class", "algorithm", "test", "unit test",
    "bug", "fix", "implement", "patch", "fim", "ast", "lint", "syntax",
    "python", "bash", "javascript", "typescript", "rust", "go", "c", "cpp"
}

ARCH_KEYWORDS = {
    "architecture", "design", "system", "trade-off", "tradeoff", "redesign",
    "scalability", "concurrency", "distributed", "race condition", "protocol",
    "invariant", "audit", "security", "contract", "lifecycle", "specification"
}

AGENTIC_KEYWORDS = {
    "crawl", "search", "explore", "multi-file", "repository", "auto-approve",
    "pair program", "review repository", "inspect codebase", "across files"
}

FAST_KEYWORDS = {
    "explain", "what is", "commit message", "format", "typo", "summarise",
    "summarize", "quick", "status", "version", "diff summary", "convert"
}


def _matches_keyword(text: str, kw: str) -> bool:
    """Match keyword using word boundaries for short terms to avoid false positives."""
    if len(kw) <= 2:
        return bool(re.search(r"\b" + re.escape(kw) + r"\b", text))
    return kw in text


def classify_task(prompt: str, is_local_preferred: bool = False) -> dict:
    """Classify prompt complexity and recommend the optimal execution engine."""
    text = prompt.lower()

    # Check for keywords with word boundary guardrails
    has_local = is_local_preferred or any(_matches_keyword(text, kw) for kw in LOCAL_KEYWORDS)
    has_arch = any(_matches_keyword(text, kw) for kw in ARCH_KEYWORDS)
    has_agentic = any(_matches_keyword(text, kw) for kw in AGENTIC_KEYWORDS)
    has_code = any(_matches_keyword(text, kw) for kw in CODE_KEYWORDS)
    has_fast = any(_matches_keyword(text, kw) for kw in FAST_KEYWORDS)

    # Length heuristic
    word_count = len(text.split())

    # Branch B: Explicit privacy / air-gapped / local directive
    if has_local:
        return {
            "tier": 0,
            "category": "On-Device Engine (Local / Air-Gapped via Ollama)",
            "branch": "local",
            "recommended_model": "local",
            "model_endpoint": "qwen2.5:14b",
            "alternatives": ["codestral", "fast"],
            "reasoning": (
                "Air-gapped, privacy, or zero-quota constraints detected. "
                "Routing to local Ollama on-device engine with zero cloud egress."
            ),
        }

    # Branch A: Hosted Mistral classification
    if has_arch or (has_code and word_count > 150):
        tier = 4
        category = "Flagship Architecture & Deep Reasoning"
        recommended = "large"
        model_name = "mistral-large-4"
        alternatives = ["mistral-medium-3.5", "codestral", "local"]
        reasoning = (
            "Complex architectural or systemic reasoning detected. "
            "Deploying mistral-large-4 for maximum analytical depth."
        )
    elif has_agentic or (has_code and not has_fast and word_count > 40):
        tier = 3
        category = "Autonomous Agentic & Tooling Workflow"
        recommended = "mistral-medium-3.5"
        model_name = "mistral-vibe-cli-latest"
        alternatives = ["codestral", "large", "local"]
        reasoning = (
            "Multi-step agentic or codebase inspection task. "
            "mistral-medium-3.5 provides native high-thinking mode and 262k context."
        )
    elif has_code:
        tier = 2
        category = "Dedicated Code & Test Synthesis"
        recommended = "codestral"
        model_name = "codestral-latest"
        alternatives = ["local", "fast", "mistral-medium-3.5"]
        reasoning = (
            "Software engineering or algorithmic task. "
            "codestral-latest is specialised for code syntax, FIM, and tests."
        )
    else:
        tier = 1
        category = "Low-Latency Utility & Fast Interaction"
        recommended = "fast"
        model_name = "mistral-vibe-cli-fast"
        alternatives = ["local", "small", "ministral"]
        reasoning = (
            "Straightforward query or single-step utility. "
            "mistral-vibe-cli-fast delivers sub-second response times."
        )

    return {
        "tier": tier,
        "category": category,
        "branch": "mistral",
        "recommended_model": recommended,
        "model_endpoint": model_name,
        "alternatives": alternatives,
        "reasoning": reasoning,
    }


def find_vibe() -> str:
    """Locate the vibe executable on the system."""
    env_bin = os.environ.get("VIBE_BIN")
    if env_bin and os.path.isfile(env_bin) and os.access(env_bin, os.X_OK):
        return env_bin

    found = shutil.which("vibe")
    if found:
        return found

    for candidate in ("/opt/homebrew/bin/vibe", "/usr/local/bin/vibe"):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return ""


def execute_local(
    prompt: str,
    task_type: str = "code",
    timeout_sec: float = 60.0,
    keep_alive: str = "5m",
) -> dict:
    """Execute a prompt via local on-device Ollama model (local-code branch)."""
    if check_ollama is None:
        return {
            "success": False,
            "error": "check_ollama module unavailable.",
            "returncode": 1,
            "stdout": "",
            "stderr": "check_ollama module missing",
            "elapsed_sec": 0.0,
            "provider": "ollama",
            "model_used": "unknown",
        }

    status = check_ollama.get_status()
    if not status.get("online"):
        return {
            "success": False,
            "error": "Local Ollama daemon is offline (start with: ollama serve).",
            "returncode": 127,
            "stdout": "",
            "stderr": "Ollama daemon unreachable",
            "elapsed_sec": 0.0,
            "provider": "ollama",
            "model_used": "unknown",
        }

    model_info = check_ollama.select_best_model(task_type)
    model_name = model_info.get("model")
    if not model_name:
        return {
            "success": False,
            "error": "No suitable local model found for task type: " + task_type,
            "returncode": 2,
            "stdout": "",
            "stderr": "Model selection failed",
            "elapsed_sec": 0.0,
            "provider": "ollama",
            "model_used": "none",
        }

    # Warm model if not resident
    if not model_info.get("resident"):
        check_ollama.warm_model(model_name, keep_alive=keep_alive)

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a principal software engineer. "
                    "Generate minimal, pure, deterministic code and comprehensive boundary tests in British English."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    start = time.perf_counter()
    code, res, elapsed = check_ollama.request_json("/api/chat", data=payload, timeout=timeout_sec)
    if code != 200:
        return {
            "success": False,
            "error": res.get("error", f"HTTP {code} from Ollama"),
            "returncode": 1,
            "stdout": "",
            "stderr": str(res),
            "elapsed_sec": round(elapsed, 2),
            "provider": "ollama",
            "model_used": model_name,
        }

    content = res.get("message", {}).get("content", "")
    return {
        "success": True,
        "returncode": 0,
        "stdout": content,
        "stderr": "",
        "elapsed_sec": round(elapsed, 2),
        "provider": "ollama",
        "model_used": model_name,
    }


def execute_vibe(
    prompt: str,
    model: str = None,
    workdir: str = None,
    auto_approve: bool = False,
    json_output: bool = False,
    timeout_sec: float = 120.0,
) -> dict:
    """Execute a prompt via Mistral Vibe and return structured results."""
    vibe_bin = find_vibe()
    if not vibe_bin:
        return {
            "success": False,
            "error": "Mistral Vibe binary ('vibe') not found in PATH or standard directories.",
            "returncode": 127,
            "stdout": "",
            "stderr": "",
            "elapsed_sec": 0.0,
            "provider": "mistral",
            "model_used": model or "mistral-medium-3.5",
        }

    cmd = [vibe_bin, "--trust"]
    if workdir:
        cmd.extend(["--workdir", workdir])
    if auto_approve:
        cmd.append("--auto-approve")
    if model:
        cmd.extend(["--model", model])
    if json_output:
        cmd.extend(["--output", "json"])
    cmd.extend(["-p", prompt])

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        elapsed = round(time.perf_counter() - start, 2)
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "elapsed_sec": elapsed,
            "provider": "mistral",
            "model_used": model or "mistral-medium-3.5",
        }
    except subprocess.TimeoutExpired:
        elapsed = round(time.perf_counter() - start, 2)
        return {
            "success": False,
            "error": f"Execution timed out after {timeout_sec} seconds.",
            "returncode": 124,
            "stdout": "",
            "stderr": "",
            "elapsed_sec": elapsed,
            "provider": "mistral",
            "model_used": model or "mistral-medium-3.5",
        }
    except Exception as e:
        elapsed = round(time.perf_counter() - start, 2)
        return {
            "success": False,
            "error": str(e),
            "returncode": 1,
            "stdout": "",
            "stderr": "",
            "elapsed_sec": elapsed,
            "provider": "mistral",
            "model_used": model or "mistral-medium-3.5",
        }


def execute(
    prompt: str,
    model: str = None,
    workdir: str = None,
    auto_approve: bool = False,
    json_output: bool = False,
    timeout_sec: float = 120.0,
) -> dict:
    """Unified execution router: dispatches to Local Ollama or Hosted Mistral."""
    if model in ("local", "ollama", "local-code", "local-qwen") or (model and model.startswith("local-")):
        return execute_local(prompt, task_type="code", timeout_sec=timeout_sec)
    return execute_vibe(
        prompt,
        model=model,
        workdir=workdir,
        auto_approve=auto_approve,
        json_output=json_output,
        timeout_sec=timeout_sec,
    )


def main():
    parser = argparse.ArgumentParser(
        description="External Execution Gateway: Mistral Vibe & Local On-Device."
    )
    subparsers = parser.add_subparsers(dest="command")

    # Classify command
    classify_parser = subparsers.add_parser(
        "classify", help="Classify prompt complexity and suggest optimal engine"
    )
    classify_parser.add_argument("prompt", help="Task prompt or instruction to evaluate")
    classify_parser.add_argument(
        "--local", action="store_true", help="Enforce local on-device preference"
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Dispatch task to selected engine")
    run_parser.add_argument("prompt", help="Task prompt or instruction to execute")
    run_parser.add_argument(
        "--model", help="Model alias override (e.g. codestral, large, fast, local)"
    )
    run_parser.add_argument("--local", action="store_true", help="Force local on-device execution")
    run_parser.add_argument("--workdir", help="Working directory for Vibe")
    run_parser.add_argument("--auto-approve", action="store_true", help="Auto-approve tool calls")
    run_parser.add_argument("--json", action="store_true", help="Emit raw JSON output")
    run_parser.add_argument(
        "--timeout", type=float, default=120.0, help="Execution timeout in seconds"
    )

    args = parser.parse_args()

    if args.command == "classify":
        result = classify_task(args.prompt, is_local_preferred=args.local)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "run":
        selected_model = args.model
        if args.local:
            selected_model = "local"
        elif not selected_model:
            classification = classify_task(args.prompt)
            selected_model = classification["recommended_model"]

        result = execute(
            args.prompt,
            model=selected_model,
            workdir=args.workdir,
            auto_approve=args.auto_approve,
            json_output=args.json,
            timeout_sec=args.timeout,
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result.get("stdout"):
                print(result["stdout"])
            if result.get("stderr") and not result.get("success"):
                print(result["stderr"], file=sys.stderr)
            elif result.get("error") and not result.get("success"):
                print(result["error"], file=sys.stderr)
        return result.get("returncode", 0)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
