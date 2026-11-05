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
        warm = check_ollama.warm_model(model_name, keep_alive=keep_alive)
        if not warm["success"]:
            error = warm.get("error") or f"Failed to warm model '{model_name}'."
            return {
                "success": False,
                "error": error,
                "returncode": 1,
                "stdout": "",
                "stderr": error,
                "elapsed_sec": warm.get("load_time_sec", 0.0),
                "provider": "ollama",
                "model_used": model_name,
            }

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

    message = res.get("message") if isinstance(res, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        error = "Ollama returned no non-empty assistant content."
        return {
            "success": False,
            "error": error,
            "returncode": 1,
            "stdout": "",
            "stderr": error,
            "elapsed_sec": round(elapsed, 2),
            "provider": "ollama",
            "model_used": model_name,
        }
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


TRIAGE_PROMPT_TEMPLATE = """You are a principal software architect performing Macro Triage on a compound engineering task.

Analyse the input items below and generate a structured JSON execution manifest:
1. Detect any conflicting, duplicate, or overlapping instructions.
2. Order items by dependency (e.g. contracts and schemas before implementation).
3. Partition items into up to three ordered execution waves (omit empty waves):
   - Wave 1 (Architectural / High-Risk): Systemic contracts, state schemas, breaking interface changes. Recommended engine: 'large' or 'mistral-medium-3.5'.
   - Wave 2 (Implementation & Tests): Discrete functions, algorithmic logic, unit tests, bug fixes. Recommended engine: 'codestral' (cloud) or 'local' (Ollama on-device).
   - Wave 3 (Cosmetic & Informational): Documentation, nits, code formatting, explanatory review replies. Recommended engine: 'fast'.

Input compound task:
{input_text}

Output format:
Respond strictly with a valid JSON object in British English matching this schema:
{{
  "summary": "Brief executive summary of compound task",
  "conflicts_detected": ["..."],
  "total_items": 3,
  "waves": [
    {{
      "wave": 1,
      "category": "Architectural / High-Risk",
      "recommended_engine": "large",
      "items": [
        {{"id": 1, "description": "...", "files": ["..."], "dependency": null}}
      ]
    }},
    {{
      "wave": 2,
      "category": "Implementation & Tests",
      "recommended_engine": "codestral",
      "items": [
        {{"id": 2, "description": "...", "files": ["..."], "dependency": 1}}
      ]
    }},
    {{
      "wave": 3,
      "category": "Cosmetic & Informational",
      "recommended_engine": "fast",
      "items": [
        {{"id": 3, "description": "...", "files": ["..."], "dependency": null}}
      ]
    }}
  ]
}}
"""


def validate_manifest(manifest: object) -> None:
    """Validate the multi-wave triage contract and normalise total_items before execution."""
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object.")
    if not isinstance(manifest.get("summary"), str) or not manifest["summary"].strip():
        raise ValueError("Manifest summary must be a non-empty string.")
    conflicts = manifest.get("conflicts_detected")
    if not isinstance(conflicts, list) or not all(isinstance(item, str) for item in conflicts):
        raise ValueError("conflicts_detected must be a list of strings.")
    waves = manifest.get("waves")
    if not isinstance(waves, list) or not (1 <= len(waves) <= 3):
        raise ValueError("Manifest must contain between 1 and 3 ordered waves.")
    seen = set()
    prev_wave = 0
    for wave in waves:
        wave_num = wave.get("wave") if isinstance(wave, dict) else None
        if type(wave_num) is not int or not (1 <= wave_num <= 3) or wave_num <= prev_wave:
            raise ValueError("Wave numbers must be strictly increasing within 1..3.")
        prev_wave = wave_num
        if not all(isinstance(wave.get(key), str) and wave[key].strip() for key in ("category", "recommended_engine")):
            raise ValueError("Each wave needs a category and recommended_engine.")
        items = wave.get("items")
        if not isinstance(items, list):
            raise ValueError("Wave items must be a list.")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Each task must be an object.")
            identifier = item.get("id")
            if type(identifier) is not int or identifier < 1 or identifier in seen:
                raise ValueError("Task IDs must be unique positive integers.")
            if not isinstance(item.get("description"), str) or not item["description"].strip():
                raise ValueError("Each task needs a non-empty description.")
            files = item.get("files")
            if not isinstance(files, list) or not all(isinstance(path, str) and path.strip() for path in files):
                raise ValueError("Task files must be a list of non-empty strings.")
            dependency = item.get("dependency")
            if dependency is not None and (type(dependency) is not int or dependency not in seen):
                raise ValueError("Task dependencies must refer to an earlier task.")
            seen.add(identifier)
    if not seen:
        raise ValueError("Manifest must contain at least one task.")
    manifest["total_items"] = len(seen)


def triage_compound_task(
    input_text: str,
    model: str = "large",
    timeout_sec: float = 120.0,
) -> dict:
    """Perform Phase 1 Macro Triage on a compound task via mistral-large-4 or specified engine."""
    prompt = TRIAGE_PROMPT_TEMPLATE.format(input_text=input_text)
    res = execute(
        prompt,
        model=model,
        json_output=False,
        timeout_sec=timeout_sec,
    )
    if not res.get("success"):
        return {
            "success": False,
            "error": res.get("error") or res.get("stderr"),
            "manifest": None,
            "raw_output": res.get("stdout", ""),
        }

    raw = res.get("stdout", "").strip()
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    json_str = json_match.group(1) if json_match else raw
    try:
        manifest = json.loads(json_str)
        validate_manifest(manifest)
        return {
            "success": True,
            "manifest": manifest,
            "model_used": res.get("model_used"),
            "elapsed_sec": res.get("elapsed_sec"),
        }
    except ValueError as error:
        return {
            "success": False,
            "error": f"Invalid triage manifest: {error}",
            "manifest": None,
            "raw_output": raw,
            "model_used": res.get("model_used"),
            "elapsed_sec": res.get("elapsed_sec"),
        }


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

    # Triage command (Phase 1 of Compound Protocol)
    triage_parser = subparsers.add_parser(
        "triage", help="Perform Phase 1 Macro Triage on a compound task"
    )
    triage_parser.add_argument("input", help="File path or text containing compound task items")
    triage_parser.add_argument(
        "--model", default="large", help="Model to perform triage (default: large)"
    )
    triage_parser.add_argument("--local", action="store_true", help="Force local on-device triage")
    triage_parser.add_argument(
        "--timeout", type=float, default=120.0, help="Triage timeout in seconds"
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

    if args.command == "triage":
        input_data = args.input
        if os.path.isfile(input_data):
            with open(input_data, "r", encoding="utf-8") as f:
                input_data = f.read()

        model = "local" if args.local else args.model
        result = triage_compound_task(input_data, model=model, timeout_sec=args.timeout)
        if not result["success"]:
            print(result.get("error") or "Triage execution failed", file=sys.stderr)
            return 1
        print(json.dumps(result["manifest"], indent=2))
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
