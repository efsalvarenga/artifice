---
name: review
version: 1.3.0
description: >-
  Universal code and architectural review skill using the Principal Code Reviewer
  ("The Gatekeeper") persona and the 8-Pillar Framework. Orchestrated by Gemini
  with native subagent dispatch to resident Ollama models (Qwen Coder + Mistral NeMo).
argument-hint: "[--local] [PR_NUMBER | branch | <file_or_doc_path>]"
---

# Universal Code & Architecture Review (`review`)

This skill orchestrates a rigorous evaluation of Pull Requests, branch diffs, individual files, or architectural design documents using the **Principal Code Reviewer ("The Gatekeeper")** persona and the **8-Pillar Code Review Framework**.

## Reference Materials

* **Code Reviewer Persona:** [`../../agents/code-reviewer/agent.md`](../../agents/code-reviewer/agent.md)
* **8-Pillar Rubric & Conventional Comments:** [`references/review-framework.md`](references/review-framework.md)
* **Ollama Residency & Lifecycle Manager:** [`../../scripts/check_ollama.py`](../../scripts/check_ollama.py)
* **Repository Invariant Dossier Compiler:** [`../../scripts/build_review_dossier.py`](../../scripts/build_review_dossier.py)

## Step-by-Step Review Procedure

### Step 1: Scope & Target Detection

1. **Parse Arguments:**
   * `--local`: Forces 100% on-device offline review via local Ollama models.
   * Target: PR number (`12`), branch name (`agent/feature`), file path (`engine.ts`), or document (`docs/designs/001_spec.md`).
2. **Target Ingestion:**
   * **PR or Branch:** Run `gh pr diff <PR>` or `git diff main...HEAD`.
   * **Document or File:** Read target content directly for architectural analysis.
3. **Execute Native Baselines:**
   Run the repository's native test and lint commands (`./scripts/lint.sh`, `npm test`, `pytest`, `cargo test`) to record baseline pass/fail status.

### Step 2: Ingest Invariants & Privacy Directives

1. Ingest `AGENTS.md` and compile project invariants:
   ```bash
   python3 ~/Repos/artifice/scripts/build_review_dossier.py .
   ```
2. If `AGENTS.md` contains an on-device privacy directive (e.g. `Privacy: on-device`), automatically engage **Offline Mode** (`--local`).

### Step 3: Lifecycle Leasing & Model Selection

1. Check Ollama daemon and select resident engines:
   ```bash
   python3 ~/Repos/artifice/scripts/check_ollama.py status
   ```
2. **Wave Leasing:** Pre-heat the models for the review wave to ensure $<200\text{ms}$ subagent response:
   ```bash
   python3 ~/Repos/artifice/scripts/check_ollama.py warm qwen2.5:14b --lease 5m
   python3 ~/Repos/artifice/scripts/check_ollama.py warm mistral-nemo:latest --lease 5m
   ```

### Step 4: Hybrid Execution & Subagent Dispatch

#### Pathway A: Gemini-Orchestrated Hybrid Review (Default)

The cloud orchestrator acts as Planner, breaking the review into orthogonal inspection streams across local engines and native test harnesses:

1. **Native Local Harness (Pillar 4 — Tests & Linters):**
   Executes `./scripts/lint.sh`, `pytest`, `cargo test`, or `npm test` directly on the machine to establish baseline test coverage and zero linter warnings.
2. **Local Subagent 1 — Code & Logic Stream (`qwen2.5-coder:14b`):**
   Ingests code diffs and repository invariant dossiers to audit:
   * **Pillar 2 (Functionality & Invariants):** Pries into 2–3 concrete boundary edge cases (empty inputs, bounds, state corruption) and asserts test coverage.
   * **Pillar 3 (Complexity & Occam's Razor):** Flags unnecessary classes, wrappers, defensive boilerplate, or over-engineered abstractions.
   * **Pillar 5 (Naming & Domain Clarity):** Audits domain vocabulary, boolean predicates, and identifier clarity.
   * **Pillar 7 (Style & Type Safety):** Audits strict type annotations, unchecked casts, and language-specific idioms.
3. **Local Subagent 2 — Architecture & Text Stream (`mistral-nemo:12b`):**
   Ingests documentation, markdown files, and commit logs to audit:
   * **Pillar 1 (Design & Architecture Alignment):** Verifies consistency against approved specifications in `docs/designs/` and global `AGENTS.md`.
   * **Pillar 6 (Comments & Documentation):** Verifies explanatory comments (*why* vs *what*) and enforces mandatory heading blank lines.
   * **Pillar 8 (Localisation & Governance):** Scans for 100% British English orthography and verifies human narrative sovereignty.
4. **Cloud Orchestrator Synthesis (Gemini):**
   Gemini receives the concise local findings, arbitrates disagreements, frames observations under Conventional Comments (`issue`, `suggestion`, `praise`), and generates the final structured verdict.

#### Pathway B: Air-Gapped Offline Mode (`--local` or Privacy Directive)

* Zero code or text leaves the local machine.
* Code analysis (Pillars 2, 3, 5, 7) runs on local `qwen2.5-coder:14b`.
* Document, architectural, and governance evaluation (Pillars 1, 6, 8) and final 8-pillar report synthesis run on local `mistral-nemo:12b`.

### Step 5: Wave Teardown & Memory Purge

Upon completing the review report, flush GPU memory to restore host RAM:
```bash
python3 ~/Repos/artifice/scripts/check_ollama.py unload --all
```

### Step 6: Provenance Signature & Output

Format findings using Conventional Comments (`issue`, `suggestion`, `question`, `praise`). Sign with the explicit multi-model provenance footer:

```markdown
---

*Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Orchestrator: **Gemini 3.8 Flash** · Workers: **Qwen 2.5 14B (Pillar 2 Logic)** + **Mistral NeMo 12B (Pillar 6 Docs)** · Skill: **`review v1.3.0`** · Date: `<YYYY-MM-DD>`*
```
