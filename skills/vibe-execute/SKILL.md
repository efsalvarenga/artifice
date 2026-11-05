---
name: vibe-execute
version: 1.2.0
description: >-
  Universal external execution gateway for models outside the Gemini family.
  Evaluates task complexity, conducts Grill-Me model selection, and orchestrates
  the Two-Phase Compound Protocol (Macro Triage -> Micro-Dispatch).
argument-hint: "[classify | triage | run] [--model <alias>] [--local] [--auto-approve] <prompt_or_file>"
---

# External Execution Gateway: Mistral Vibe & Local On-Device (`vibe-execute`)

This skill serves as the sovereign external execution gateway whenever an agent or developer requests model inference outside the primary Gemini family. It evaluates prompt complexity, privacy directives, and quota constraints to conduct a front-loaded Grill-Me selection across two execution branches:
* **Branch A (Hosted Mistral):** Cloud inference via Mistral Vibe (`fast`, `codestral`, `mistral-medium-3.5`, `large`).
* **Branch B (Local On-Device Engine):** Air-gapped on-device execution via [`local-code`](../local-code/SKILL.md) and Ollama (`qwen2.5:14b`, `mistral-nemo:12b`).

## Reference Materials

* **Vibe Dispatch Controller:** [`../../scripts/vibe_execute.py`](../../scripts/vibe_execute.py)
* **Local Code Offloading Skill:** [`../local-code/SKILL.md`](../local-code/SKILL.md)
* **Ollama Lifecycle Manager:** [`../../scripts/check_ollama.py`](../../scripts/check_ollama.py)
* **Code Author Agent:** [`../../agents/code-author/agent.md`](../../agents/code-author/agent.md)

Resolve `ARTIFICE_ROOT` in order: explicit `ARTIFICE_ROOT`, `$HOME/.local/share/artifice` when present, or `$HOME/Repos/artifice`.

## Step-by-Step Procedure

### 1. Evaluate Complexity & Privacy Boundaries

Before executing any request outside the Gemini family, classify prompt intent and operational constraints:

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" classify "<USER_PROMPT>" [--local]
```

The classifier routes across five operational tiers:
* **Tier 0 (Air-Gapped / Privacy):** Confidential code, secret vaults, offline constraints, or `--local` flag. Routes to **Branch B (`local`)** via `qwen2.5:14b` with zero cloud egress.
* **Tier 1 (Utility / Fast):** Explanations, commit messages, diff summaries, formatting. Recommends `fast` (`mistral-vibe-cli-fast`), offering `local` as on-device alternative.
* **Tier 2 (Code & Tests):** Pure algorithmic functions, unit test suites, FIM synthesis. Recommends `codestral` (`codestral-latest`), offering `local` (`qwen2.5:14b`) as zero-cost alternative.
* **Tier 3 (Agentic Loops):** Multi-file exploration, repository inspection, autonomous editing. Recommends `mistral-medium-3.5` (`mistral-vibe-cli-latest`).
* **Tier 4 (Flagship Architecture):** High-stakes redesign, systemic trade-offs, concurrency, contracts. Recommends `large` (`mistral-large-4`).

### 2. Front-Loaded "Grill-Me" Alignment Interview

Engage the developer with a focused multiple-choice confirmation via `ask_question`:

* **Question 1 (Execution Branch & Engine):**
  * Present `(Recommended) <Model>` based on the complexity evaluation.
  * Explicitly offer both Hosted Mistral and Local On-Device options (e.g. `codestral` vs `local (Qwen 14B)`).
* **Question 2 (Autonomy & Permissions):**
  * Confirm execution mode: Headless Safe (`-p`), Autonomous Mutating (`--auto-approve`), or Air-Gapped Local.
  * Verify target working directory scope.

### 3. Unified Dispatch

Once aligned on model selection and execution boundaries, dispatch the job:

```bash
# Branch A: Hosted Mistral
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" run "<PROMPT>" --model "<SELECTED_MODEL>" [--auto-approve] [--workdir "<DIR>"]

# Branch B: Local On-Device (Ollama)
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" run "<PROMPT>" --local
```

### 4. Post-Execution Verification & Teardown

After execution finishes:
* Verify process return code and inspect generated stdout/stderr.
* Report execution latency, active model endpoint, and provider (`mistral` or `ollama`).
* If `local` was used, ensure host stewardship by running memory eviction when required:
  ```bash
  python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" unload --all
  ```
* If files were mutated under `--auto-approve`, run native verification (`./scripts/lint.sh`) before completing the turn.

## Compound Task Protocol: Macro Triage to Micro-Dispatch

When handling batched or compound tasks (e.g. multi-comment PR reviews, multi-file refactoring passes, backlog task lists):

### Phase 1: Macro Triage & Graph Ordering

Never dispatch compound items in uncoordinated isolation or cram 10+ items into one monolithic prompt. Ingest all items simultaneously to identify cross-cutting constraints:

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" triage "<COMPOUND_INPUT_FILE>"
```

`mistral-large-4` evaluates the full context, surfaces contradictions, and partitions items into a 3-wave execution manifest:
* **Wave 1 (Architectural / High-Risk):** Systemic contracts, state schemas, breaking interface changes. Recommended engine: `large`.
* **Wave 2 (Implementation & Tests):** Discrete functions, algorithmic logic, unit tests, bug fixes. Recommended engine: `codestral` (cloud) or `local` (Ollama on-device).
* **Wave 3 (Cosmetic & Informational):** Documentation, nits, formatting, explanatory replies. Recommended engine: `fast`.

### Phase 2: Heterogeneous Wave Dispatch & Verification

Execute each wave sequentially with its dedicated engine:
1. Dispatch Wave 1 with `vibe_execute.py run "<WAVE_1_TASKS>" --model large --auto-approve`.
2. Dispatch Wave 2 with `vibe_execute.py run "<WAVE_2_TASKS>" --model codestral` (or `--local` for air-gapped tasks).
3. Dispatch Wave 3 with `vibe_execute.py run "<WAVE_3_TASKS>" --model fast`.
4. Run native baseline checks (`./scripts/lint.sh`) between waves to trap regressions early.
