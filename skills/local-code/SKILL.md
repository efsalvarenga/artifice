---
name: local-code
version: 1.3.0
description: Delegate deep algorithmic refactoring, logic analysis, FIM synthesis, or unit test generation to local Qwen 2.5 Coder 14B running via Ollama.
---

# Local Code Refactoring & Logic with Qwen 2.5 Coder

Use this skill when delegating bounded code generation, complex refactoring, test suite synthesis, or Fill-in-the-Middle (FIM) operations to local `qwen2.5-coder:14b` (with fallback to `qwen2.5:14b`). Integrates natively with `code-author` ("The Craftsman") during specification-driven TDD workflows.

## Reference Materials

* **Ollama Residency & Lifecycle Manager:** Read `scripts/check_ollama.py` under the resolved Artifice root when needed.
* **Code Author Agent:** Read `agents/code-author/agent.md` under the resolved root and apply its Markdown body, not its Antigravity tool metadata.

### Resource Resolution & Permissions

Use `$HOME/.local/share/artifice` when present; resolve it physically and validate its `agents`, `skills`, and `scripts` directories. A broken or invalid anchor is an error. Only when absent, resolve this definition's containing directory physically before ascending two directories. Validate the checkout and requested resource; stop and request repair if unavailable. Bind the absolute directory as `ARTIFICE_ROOT` for each relevant command, quoting it and keeping target repositories separate; do not assume shell state persists. Use the selected Python interpreter where required.

Local inference does not make the surrounding cloud conversation private. For strict local-only work, stop before protected-content ingestion and require a genuinely local session without cloud fallback. Require explicit operation-specific permission for branch changes, staging, commits, pushes, and PR publication. Design approval remains separate from implementation or Git permission.

## Step-by-Step Procedure

### 1. Select & Lease Local Model

Check daemon readiness and select the coding engine:
```bash
python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" select --task code
```
For active coding waves, lease the model for 5 minutes to avoid cold-start reloads:
```bash
python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" warm "<selected-installed-model>" --lease 5m
```

### 2. Invoke Local Model

Query the local Ollama instance directly via HTTP API or MCP:
```bash
curl -s http://localhost:11434/api/chat -d '{
  "model": "<selected-installed-model>",
  "messages": [
    {"role": "system", "content": "You are a principal software engineer. Generate minimal, pure, deterministic code and comprehensive boundary tests in British English."},
    {"role": "user", "content": "<PROMPT>"}
  ],
  "stream": false
}'
```

### 3. Boundary Edge-Case Probing & TDD Contracts

When synthesising code or expanding test suites under `code-author`:
* Explicitly identify 2–3 boundary conditions (e.g. empty collections, zero/negative bounds, capacity limits).
* Generate dedicated contract tests asserting invariants against these edge cases.
* Only if committing is separately authorised, attribute code synthesised by local models accurately in Git trailers:
  `Co-authored-by: Qwen 2.5 Coder 14B <qwen2.5-coder@ollama.local>`.

### 4. Teardown & Purge

Once bounded coding or test synthesis concludes, flush memory:
```bash
python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" unload --all
```
