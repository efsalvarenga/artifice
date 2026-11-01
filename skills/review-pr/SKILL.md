---
name: review-pr
version: 1.1.0
description: >-
  Conducts a formal Pull Request or git diff code review using the Principal Code
  Reviewer ("The Gatekeeper") persona and the 8-Pillar Code Review Framework
  (Google Engineering Practices + Conventional Comments + Project Rules).
  Supports Dual-Model Consensus and 100% On-Device execution via --local or
  repository Privacy Directives.
argument-hint: "[--local] [PR_NUMBER or branch]"
---

# Pull Request Code Review Skill (`review-pr`)

This skill orchestrates a formal, structured Pull Request code review in any project using the **Principal Code Reviewer ("The Gatekeeper")** persona, the **8-Pillar Code Review Framework**, and flexible cloud-local model delegation.

## Reference Materials

* **Code Reviewer Agent Definition:** [`../../agents/code-reviewer/agent.md`](../../agents/code-reviewer/agent.md)
* **Detailed 8-Pillar Rubric & Conventional Comments Reference:** [`references/review-framework.md`](./references/review-framework.md)

## Step-by-Step Review Procedure

### Step 1: Identify Scope & Arguments

1. Parse arguments for:
   * **`--local` flag:** Forces 100% on-device review via local Ollama models.
   * **Target PR or Branch:** Explicit PR number or branch name.
2. Inspect open GitHub Pull Requests or local branch diffs against `main`:
   ```bash
   gh pr list
   git status
   git log main..HEAD --oneline
   ```
3. If a PR number or branch is specified, inspect its metadata and changed files:
   ```bash
   gh pr view <PR_NUMBER>
   gh pr diff <PR_NUMBER>
   ```
   If reviewing an unpushed local branch:
   ```bash
   git diff main...HEAD --stat
   git diff main...HEAD
   ```

### Step 2: Ingest Local Governance & Privacy Directives

1. **Read Global & Local Rules:**
   * Ingest `~/.gemini/config/AGENTS.md`.
   * Check the project root for local rules: `AGENTS.md`, `GEMINI.md`, or `.agents/rules/*.md`.
2. **Compile Repository Invariant Dossier:**
   Run the dossier compiler to assemble intentional project invariants for local reviewers:
   ```bash
   python3 ~/Repos/artifice/scripts/build_review_dossier.py .
   ```
3. **Check for Privacy Directives:**
   If `AGENTS.md` contains an on-device directive (e.g. `Privacy: on-device`, `Review: local-only`, or `Air-Gapped`), automatically switch to **Mode 2 (Air-Gapped / On-Device)** even if `--local` was not passed in the command line.
4. **Execute Available Test Suites & Linters:**
   Detect and run the project's native build, test, and lint commands:
   * Linters & verification: `./scripts/lint*.sh`, `./scripts/verify*.sh`, or `./scripts/test*.sh`
   * Node/TypeScript: `npm run build && npm test` or `pnpm test` or `bun test`
   * Python: `pytest`
   * Rust: `cargo test`
   Record all test results for inclusion in the review report.

### Step 3: Dispatch or Execute the Review

* Adopt the **Principal Code Reviewer ("The Gatekeeper")** persona.
* Choose the execution pathway based on privacy requirements:

#### Pathway A: Dual-Model Consensus (Default)

* Primary 8-Pillar audit driven by the active cloud orchestrator (Gemini).
* **Local Qwen 2.5 14B Consultation (Pillar 2):** For dense mathematical logic, state reducers, or boundary conditions, call local Qwen via Ollama (using the `ollama` MCP server or direct HTTP) armed with the compiled dossier:
  ```bash
  curl -s http://localhost:11434/api/chat -d '{
    "model": "qwen2.5:14b",
    "messages": [
      {"role": "system", "content": "You are a compiler engineer and logic auditor. Invariant directives: <REPO_DOSSIER>. Identify 2–3 concrete boundary edge cases in this diff, pry into potential failure modes, and verify if tests cover them in British English."},
      {"role": "user", "content": "<CODE_DIFF_SNIPPET>"}
    ],
    "stream": false
  }'
  ```
* **Local Mistral NeMo 12B Consultation (Pillar 6):** For long-form documentation, ADRs, or READMEs, call local Mistral for natural prose evaluation.

#### Pathway B: Air-Gapped / On-Device Mode (`--local` or Privacy Directive)

* Zero code diffs leave the machine.
* The Gatekeeper evaluates code invariants using local `qwen2.5:14b` and synthesises the final review report using local `mistral-nemo:12b` via Ollama directly.

### Step 4: Generate & Sign the Review Report

1. Format findings using Conventional Comments (`issue`, `suggestion`, `question`, `praise`).
2. **Output Location:**
   * Present the structured review directly in-chat or in an Antigravity artefact canvas.
   * If the repository has a `docs/reviews/` directory (or the user requests a committed review), save the report to `docs/reviews/pr_<PR_NUMBER>_review.md`.
3. **Mandatory Provenance Signature:**
   Always sign the review with the formal provenance footer reflecting the models used:

   *For Dual-Model Consensus:*
   ```markdown
   ---

   *Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Models: **Gemini 3.8 Flash + Qwen 2.5 14B (Dual-Model Consensus)** · Skill: **`review-pr v1.1.0`** · Date: `<YYYY-MM-DD>`*
   ```

   *For 100% On-Device Mode:*
   ```markdown
   ---

   *Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Models: **Mistral NeMo 12B + Qwen 2.5 14B (100% On-Device Offline)** · Skill: **`review-pr v1.1.0`** · Date: `<YYYY-MM-DD>`*
   ```
