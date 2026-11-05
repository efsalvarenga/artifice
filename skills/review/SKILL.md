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

This skill orchestrates a rigorous evaluation of Pull Requests, branch diffs, individual files, or architectural design documents using the **Principal Code Reviewer ("The Gatekeeper")** persona and the **8-Pillar Code Review Framework**.

## Reference Materials

* **Code Reviewer Persona:** [`../../agents/code-reviewer/agent.md`](../../agents/code-reviewer/agent.md)
* **8-Pillar Rubric & Conventional Comments:** [`references/review-framework.md`](references/review-framework.md)
* **Ollama Residency & Lifecycle Manager:** [`../../scripts/check_ollama.py`](../../scripts/check_ollama.py)
* **Repository Invariant Dossier Compiler:** [`../../scripts/build_review_dossier.py`](../../scripts/build_review_dossier.py)

`ARTIFICE_ROOT`: explicit value, existing `$HOME/.local/share/artifice`, then `$HOME/Repos/artifice`; resolve links from `ARTIFICE_ROOT/skills/review/`.

## Step-by-Step Review Procedure

### Step 1: Scope, Privacy & Baseline Detection

1. **Parse Arguments:**
   * `--local`: Enforces 100% on-device review via local Ollama models without reading protected diff or source bytes into cloud context (no cloud fallback).
   * Target: PR number (`12`), branch name (`agent/feature`), file path (`engine.ts`), or document (`docs/designs/001_spec.md`).
2. **Check Privacy Directives First:**
   If `--local` is passed or `AGENTS.md` declares `Privacy: on-device` / `Review: local-only`, engage **Pathway B (On-Device Mode)** before reading target code or diffs. Run Step 3's model checks first; stop if either worker is unavailable.
3. **Target Ingestion & Native Baselines:**
   In Pathway A, inspect `gh pr diff <PR>`, `git diff main...HEAD`, or the target file directly. Run native verification (`./scripts/lint.sh`, `npm test`, `pytest`, `cargo test`) to record baseline pass/fail status.

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
   * **Overlooked Defect Inspection:** Scrutinises the diff for subtle bugs or edge cases missed by local workers.
   * **False-Positive Filtering:** Filters worker findings against intentional repository invariants.
   * **Executive Synthesis:** Unifies findings under Conventional Comments (`issue`, `suggestion`, `question`, `praise`).

#### Pathway B: On-Device Privacy Mode (`--local` or Privacy Directive)

* Protected code and diffs stay strictly on-device (dispatched directly via local shell/Ollama scripts or within a verified local session, never ingested into cloud context or falling back to cloud).
* Code analysis (Pillars 2, 3, 5, 7) runs on `code_model`; architectural, documentation, and governance review (Pillars 1, 6, 8) plus final report synthesis run on `prose_model`.

### Step 5: Wave Teardown & Provenance Signature

1. Flush resident Ollama models to restore host memory:

   ```bash
   python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" unload --all
   ```

2. Sign with accurate provenance (recording only workers actually used, or `none`):

   ```markdown
   ---

   *Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Orchestrator: **`<Actual Model or Assistant>`** · Workers: **`<code_model + prose_model, or none>`** · Skill: **`review v1.3.0`** · Date: `<YYYY-MM-DD>`*
   ```
