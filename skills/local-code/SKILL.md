---
name: local-code
version: 1.3.0
description: Delegate bounded algorithmic refactoring, logic analysis, FIM synthesis or unit test generation to an installed local coding model via Ollama.
---

# Local Code Refactoring & Logic (`local-code`)

Use this skill directly or as the on-device branch of [`vibe-execute`](../vibe-execute/SKILL.md) when delegating bounded code generation, algorithmic refactoring, test suite synthesis, or Fill-in-the-Middle (FIM) operations to an installed local coding model via Ollama. Integrates natively with [`code-author`](../../agents/code-author/agent.md) ("The Craftsman") during specification-driven TDD workflows.

## Reference Materials

* **External Gateway:** [`../vibe-execute/SKILL.md`](../vibe-execute/SKILL.md)
* **Ollama Residency & Lifecycle Manager:** [`../../scripts/check_ollama.py`](../../scripts/check_ollama.py)
* **Code Author Agent:** [`../../agents/code-author/agent.md`](../../agents/code-author/agent.md)

Resolve `ARTIFICE_ROOT` in order: explicit `ARTIFICE_ROOT`, `$HOME/.local/share/artifice` when present, or `$HOME/Repos/artifice`.

## Step-by-Step Procedure

### 1. Select & Lease Local Model

Select the installed coding engine dynamically (honouring `ARTIFICE_CODE_MODEL` when set, otherwise preferring `qwen2.5-coder:14b` then `qwen2.5:14b`):

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" select --task code
```

Capture the returned JSON `model` string as `code_model` (stop if exit code is non-zero; under strict local-only policy, never fall back to cloud). Lease `code_model` for 5 minutes to avoid cold-start reloads:

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" warm "$code_model" --lease 5m
```

### 2. Invoke Local Model

Query the local Ollama instance directly via HTTP API or MCP using the selected `code_model` tag:

```bash
curl -s http://localhost:11434/api/chat -d "{
  \"model\": \"$code_model\",
  \"messages\": [
    {\"role\": \"system\", \"content\": \"You are a principal software engineer. Generate minimal, pure, deterministic code and comprehensive boundary tests in British English.\"},
    {\"role\": \"user\", \"content\": \"<PROMPT>\"}
  ],
  \"stream\": false
}"
```

### 3. Boundary Edge-Case Probing & TDD Contracts

When synthesising code or expanding test suites under `code-author`:

* Explicitly identify 2–3 boundary conditions (e.g. empty collections, zero/negative bounds, capacity limits).
* Generate dedicated contract tests asserting invariants against these edge cases and verify native Red/Green execution.
* When committing code synthesised by local models (subject to active client/repository Git rules), attribute the actual `code_model` tag used in Git trailers (`Co-authored-by: <code_model> <ollama@artifice.local>`).

### 4. Teardown & Purge

Once bounded coding or test synthesis concludes, flush resident models from memory:

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" unload --all
```
