---
name: review
version: 1.3.0
description: >-
  Universal code and architectural review skill using the Principal Code Reviewer
  ("The Gatekeeper") persona and the 8-Pillar Framework. Uses the current client
  orchestrator with optional local Ollama consultation and explicit privacy boundaries.
argument-hint: "[--local] [PR_NUMBER | branch | <file_or_doc_path>]"
---

# Universal Code & Architecture Review (`review`)

Evaluates Pull Requests, branch diffs, files, or design documents using **The Gatekeeper** persona and the **8-Pillar Framework**.

## Reference Materials

* **Code Reviewer Persona:** [`../../agents/code-reviewer/agent.md`](../../agents/code-reviewer/agent.md)
* **8-Pillar Rubric & Conventional Comments:** [`references/review-framework.md`](references/review-framework.md)
* **Ollama Residency & Lifecycle Manager:** [`../../scripts/check_ollama.py`](../../scripts/check_ollama.py)
* **Repository Invariant Dossier Compiler:** [`../../scripts/build_review_dossier.py`](../../scripts/build_review_dossier.py)

Resolve `ARTIFICE_ROOT` from an explicit value, `$HOME/.local/share/artifice` when present, or `$HOME/Repos/artifice`, and resolve links from `ARTIFICE_ROOT/skills/review/`.

## Step-by-Step Review Procedure

### Step 1: Scope, Privacy & Baseline Detection

1. **Parse Arguments:**
   * `--local`: Enforces strict on-device review via Ollama (no cloud ingestion or fallback).
   * Target: PR number (`12`), branch (`agent/feature`), file (`engine.ts`), or design doc (`docs/designs/001_spec.md`).
2. **Check Privacy Directives First:**
   If `--local` is passed or `AGENTS.md` declares `Privacy: on-device` / `Review: local-only`, engage **Pathway B** before reading target files or diffs. Run Step 3 first; stop if either worker is unavailable.
3. **Target Ingestion & Native Baselines (Pathway A):**
   Inspect `gh pr diff <PR>`, `git diff main...HEAD`, or the target file, and run native suites (`./scripts/lint.sh`, `npm test`, `pytest`, `cargo test`) to record baseline status.

### Step 2: Ingest Invariants & Specifications

1. **Ingest Active EGM Specification:**
   Inspect `docs/designs/` for the active specification and ingest its **State Schema**, **Invariants & Rules**, and **Edge Cases** as the source-of-truth contract.
2. **Compile Repository Invariant Dossier:**

   ```bash
   python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/build_review_dossier.py" .
   ```

### Step 3: Model Selection & Wave Leasing

1. Select installed local worker models dynamically (honouring optional `ARTIFICE_CODE_MODEL` and `ARTIFICE_PROSE_MODEL` overrides; exit `2` indicates unavailable local selection):

   ```bash
   python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" select --task code
   python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" select --task prose
   ```

2. Warm only selected, non-empty models, following the failure rules in [`review-framework.md`](references/review-framework.md):

   ```bash
   if [[ -n "${code_model:-}" ]]; then
     python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" warm "$code_model" --lease 5m || code_model=""
   fi
   if [[ -n "${prose_model:-}" ]]; then
     python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" warm "$prose_model" --lease 5m || prose_model=""
   fi
   ```

### Step 4: Hybrid or On-Device Execution

#### Pathway A: Current-Orchestrator Hybrid Review (Default)

The current client orchestrator acts as **Lead Architect, Quality Inspector, and Synthesiser**:

1. **Orchestrator Direct Evaluation (Pillar 1 — Design & Contract Alignment):**
   * **Contract Fulfilment:** Verifies state schemas, methods, and mutation rules match the approved specification 1:1.
   * **Invariant Protection:** Confirms all Section 4 invariants are strictly upheld.
   * **Drift Control:** Flags unauthorised expansion, speculative abstractions, or omitted capabilities as `[issue] (blocking, DESIGN)`.
2. **Native Local Harness (Pillar 4 — Tests & Linters):**
   Verifies local test coverage and zero linter errors.
3. **Local Code Stream (`code_model`):**
   Audits **Pillar 2 (Functionality & Invariants)** with 2–3 concrete boundary probes, **Pillar 3 (Complexity & Occam's Razor)**, **Pillar 5 (Naming)**, and **Pillar 7 (Style & Types)**.
4. **Local Prose Stream (`prose_model`):**
   Audits **Pillar 6 (Comments & Documentation)** and **Pillar 8 (British English & Narrative Sovereignty)**.
5. **Orchestrator Quality Gate & Synthesis:**
   * **Overlooked Defect Inspection:** Scrutinises diffs for subtle bugs or edge cases missed by workers.
   * **False-Positive Filtering:** Filters worker findings against repository invariants.
   * **Executive Synthesis:** Unifies findings under Conventional Comments (`issue`, `suggestion`, `question`, `praise`).

#### Pathway B: On-Device Privacy Mode (`--local` or Privacy Directive)

* Protected code and diffs stay strictly on-device via local shell/Ollama pipelines or a verified local session (never ingested into cloud context, with no cloud fallback).
* `code_model` audits Pillars 2, 3, 5, 7; `prose_model` audits Pillars 1, 6, 8 and synthesises the final report.

### Step 5: Wave Teardown & Provenance Signature

1. Unload resident Ollama models to restore host memory:

   ```bash
   python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" unload --all
   ```

2. Sign with provenance (listing only workers actually used, or `none`):

   ```markdown
   ---

   *Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Orchestrator: **`<Actual Model or Assistant>`** · Workers: **`<code_model + prose_model, or none>`** · Skill: **`review v1.3.0`** · Date: `<YYYY-MM-DD>`*
   ```
