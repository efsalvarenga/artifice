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

* **Code Reviewer Persona:** Read `agents/code-reviewer/agent.md` under the resolved Artifice root and apply its Markdown body, not its Antigravity tool metadata.
* **8-Pillar Rubric & Conventional Comments:** [`references/review-framework.md`](references/review-framework.md)
* **Ollama Residency & Lifecycle Manager:** `scripts/check_ollama.py` under the resolved root.
* **Repository Invariant Dossier Compiler:** `scripts/build_review_dossier.py` under the resolved root.

### Resource Resolution & Privacy Boundary

Use `$HOME/.local/share/artifice` when present; resolve it physically and verify its `agents`, `skills`, and `scripts` directories. A broken or invalid anchor is an error. Only when absent, resolve this definition's containing directory physically before ascending two directories. Validate the checkout and requested resource; stop and request repair if unavailable. Bind the absolute directory as `ARTIFICE_ROOT` for each relevant command, quoting it and passing the target repository separately; do not assume shell state persists. Use the selected Python interpreter where required.

Before reading target code or diffs, establish the requested privacy mode and read only the minimum applicable policy metadata. A cloud conversation cannot provide strict local-only review: stop before protected-content ingestion and require a genuinely local session. Ollama workers do not make a cloud session air-gapped, and local-only work never falls back to cloud. Require explicit operation-specific permission for branch changes, staging, commits, pushes, and PR publication.

## Step-by-Step Review Procedure

### Step 1: Scope & Target Detection

1. **Parse Arguments:**
   * `--local`: Requires a genuinely local session and on-device review via Ollama; reject cloud-session execution before reading the target.
   * Target: PR number (`12`), branch name (`agent/feature`), file path (`engine.ts`), or document (`docs/designs/001_spec.md`).
2. **Target Ingestion:**
   * **PR or Branch:** Run `gh pr diff <PR>` or `git diff main...HEAD`.
   * **Document or File:** Read target content directly for architectural analysis.
3. **Execute Native Baselines:**
   Run the repository's native test and lint commands (`./scripts/lint.sh`, `npm test`, `pytest`, `cargo test`) to record baseline pass/fail status.

### Step 2: Ingest Invariants, Specifications & Privacy Directives

1. **Ingest Active EGM Specification:**
   Inspect `docs/designs/` for the specification corresponding to this feature or milestone. If present, ingest its **State Schema**, **Invariants & Rules**, and **Edge Cases** as the authoritative source-of-truth contract.
2. **Compile Repository Invariant Dossier:**
   Run the dossier compiler to assemble intentional project invariants:
   ```bash
   python3 "$ARTIFICE_ROOT/scripts/build_review_dossier.py" "<target_repo>"
   ```
3. **Check Privacy Directives:**
   If `AGENTS.md` contains an on-device directive, enforce the session boundary above before reading protected target content. Do not automatically claim the cloud conversation is offline.

### Step 3: Lifecycle Leasing & Model Selection

1. Check Ollama daemon and select resident engines:
   ```bash
   python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" status
   ```
2. **Wave Leasing:** Pre-heat selected installed models to reduce cold-start latency; do not promise a response-time bound:
   ```bash
   python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" warm qwen2.5-coder:14b --lease 5m
   python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" warm mistral-nemo:12b --lease 5m
   ```

### Step 4: Hybrid Execution & Subagent Dispatch

#### Pathway A: Current-Orchestrator Hybrid Review (Default)

The cloud orchestrator acts as **Lead Architect, Quality Inspector, and Synthesiser**:

1. **Orchestrator Direct Evaluation (Pillar 1 — Design & Specification Contract Alignment):**
   The current orchestrator directly evaluates the PR diff against the active approved EGM specification in `docs/designs/`:
   * **Contract Fulfillment:** Verifies that all state schemas, methods, and mutation rules match the specification 1:1.
   * **Invariant Protection:** Confirms that all invariants declared in Section 4 of the specification are strictly upheld.
   * **Drift Control:** Flags any unauthorised architectural expansion, speculative abstractions, or omitted capabilities as a blocking defect (`[issue] (blocking, DESIGN)`).
2. **Native Local Harness (Pillar 4 — Tests & Linters):**
   Executes `./scripts/lint.sh`, `pytest`, `cargo test`, or `npm test` directly on the machine to establish baseline test coverage and zero linter warnings.
3. **Local Subagent 1 — Code & Logic Stream (`qwen2.5-coder:14b`):**
   Ingests code diffs and repository invariant dossiers to audit:
   * **Pillar 2 (Functionality & Invariants):** Pries into 2–3 concrete boundary edge cases (empty inputs, bounds, state corruption) and asserts test coverage.
   * **Pillar 3 (Complexity & Occam's Razor):** Flags unnecessary classes, wrappers, defensive boilerplate, or over-engineered abstractions.
   * **Pillar 5 (Naming & Domain Clarity):** Audits domain vocabulary, boolean predicates, and identifier clarity.
   * **Pillar 7 (Style & Type Safety):** Audits strict type annotations, unchecked casts, and language-specific idioms.
4. **Local Subagent 2 — Prose & Governance Stream (`mistral-nemo:12b`):**
   Ingests documentation, markdown files, and commit logs to audit:
   * **Pillar 6 (Comments & Documentation):** Verifies explanatory comments (*why* vs *what*) and enforces mandatory heading blank lines.
   * **Pillar 8 (Localisation & Governance):** Scans for 100% British English orthography and verifies human narrative sovereignty.
5. **Orchestrator Quality Gate & Blind-Spot Verification:**
   Before authoring the final review, the orchestrator cross-audits the local models' findings against the diff:
   * **Overlooked Defect Inspection:** Scrutinises the diff to identify subtle bugs, concurrency hazards, or edge cases missed by the local workers.
   * **False-Positive Filtering:** Validates reported defects against intentional repository invariants to eliminate hallucinations.
   * **Executive Synthesis & Verdict:** Unifies findings under Conventional Comments (`issue`, `suggestion`, `praise`) and issues the structured verdict.

#### Pathway B: Air-Gapped Offline Mode (`--local` or Privacy Directive)

* This pathway requires a genuinely local session; verify the execution environment rather than claiming isolation from the flag alone.
* Code analysis (Pillars 2, 3, 5, 7) runs on local `qwen2.5-coder:14b`.
* Document, architectural, and governance evaluation (Pillars 1, 6, 8) and final 8-pillar report synthesis run on local `mistral-nemo:12b`.

### Step 5: Wave Teardown & Memory Purge

Upon completing the review report, flush GPU memory to restore host RAM:
```bash
python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" unload --all
```

### Step 6: Provenance Signature & Output

Format findings using Conventional Comments (`issue`, `suggestion`, `question`, `praise`). Sign with the explicit multi-model provenance footer:

```markdown
---

*Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Orchestrator: **<actual assistant or exposed model identity>** · Workers: **<only workers actually used, or none>** · Skill: **`review v1.3.0`** · Date: `<YYYY-MM-DD>`*
```
