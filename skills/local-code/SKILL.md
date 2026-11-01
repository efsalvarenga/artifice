---
name: local-code
version: 1.2.0
description: Delegate deep algorithmic refactoring, logic analysis, FIM synthesis, or unit test generation to local Qwen 2.5 Coder 14B running via Ollama.
---

# Local Code Refactoring & Logic with Qwen 2.5 Coder

Use this skill when delegating bounded code generation, complex refactoring, test suite synthesis, or Fill-in-the-Middle (FIM) operations to local `qwen2.5-coder:14b` (with fallback to `qwen2.5:14b`).

## Reference Materials

* **Ollama Residency & Lifecycle Manager:** [`../../scripts/check_ollama.py`](../../scripts/check_ollama.py)

## Step-by-Step Procedure

### 1. Select & Lease Local Model

Check daemon readiness and select the coding engine:
```bash
python3 ~/Repos/artifice/scripts/check_ollama.py select --task code
```
For active coding waves, lease the model for 5 minutes to avoid cold-start reloads:
```bash
python3 ~/Repos/artifice/scripts/check_ollama.py warm qwen2.5:14b --lease 5m
```

### 2. Invoke Local Model

Query the local Ollama instance directly via HTTP API or MCP:
```bash
curl -s http://localhost:11434/api/chat -d '{
  "model": "qwen2.5:14b",
  "messages": [
    {"role": "system", "content": "You are a principal software engineer. Generate minimal, pure, deterministic code and comprehensive boundary tests in British English."},
    {"role": "user", "content": "<PROMPT>"}
  ],
  "stream": false
}'
```

### 3. Boundary Edge-Case Probing

When synthesizing code or expanding test suites:
* Explicitly identify 2–3 boundary conditions (e.g. empty collections, zero/negative bounds, capacity limits).
* Generate dedicated contract tests asserting invariants against these edge cases.

### 4. Teardown & Purge

Once bounded coding or test synthesis concludes, flush memory:
```bash
python3 ~/Repos/artifice/scripts/check_ollama.py unload --all
```
