---
name: review-pr
version: 1.0.0
description: >-
  Conducts a formal Pull Request or git diff code review using the Principal Code
  Reviewer ("The Gatekeeper") persona and the 8-Pillar Code Review Framework
  (Google Engineering Practices + Conventional Comments + Project Rules). Use
  whenever asked to review a PR, audit a branch diff, or evaluate code changes.
---

# Pull Request Code Review Skill (`review-pr`)

This skill orchestrates a formal, structured Pull Request code review in any project using the **Principal Code Reviewer ("The Gatekeeper")** persona and the **8-Pillar Code Review Framework**.

## Reference Materials

* **Code Reviewer Agent Definition:** [`../../agents/code-reviewer/agent.md`](../../agents/code-reviewer/agent.md)
* **Detailed 8-Pillar Rubric & Conventional Comments Reference:** [`references/review-framework.md`](./references/review-framework.md)

## Step-by-Step Review Procedure

### Step 1: Identify Scope & Target Diff

1. Inspect open GitHub Pull Requests or local branch diffs against `main`:
   ```bash
   gh pr list
   git status
   git log main..HEAD --oneline
   ```
2. If a PR number or branch is specified, inspect its metadata and changed files:
   ```bash
   gh pr view <PR_NUMBER>
   gh pr diff <PR_NUMBER>
   ```
   If reviewing an unpushed local branch:
   ```bash
   git diff main...HEAD --stat
   git diff main...HEAD
   ```

### Step 2: Ingest Local Governance & Verification Gates

1. **Read Global & Local Rules:**
   * Ingest `~/.gemini/config/AGENTS.md`.
   * Check the project root for local rules: `AGENTS.md`, `GEMINI.md`, or `.agents/rules/*.md`.
2. **Execute Available Test Suites & Verification Scripts:**
   Detect and run the project's verification commands:
   * Verification scripts: `./scripts/verify*.sh` or `./scripts/test*.sh`
   * Node/TypeScript: `npm test` or `pnpm test` or `bun test`
   * Python: `pytest`
   * Rust: `cargo test`
   Record all test results for inclusion in the review report.

### Step 3: Dispatch or Execute the `code-reviewer` Evaluation

* Adopt the **Principal Code Reviewer ("The Gatekeeper")** persona (or dispatch the subagent defined in [`../../agents/code-reviewer/agent.md`](../../agents/code-reviewer/agent.md)).
* Systematically evaluate every changed file across all **8 Pillars**:
  1. `DESIGN` — Architecture & Specification Alignment
  2. `FUNCTIONALITY` — Invariants, Correctness & Edge Cases
  3. `COMPLEXITY` — Simplicity & Maintainability
  4. `TESTS` — Automated Test Coverage & Verification Results
  5. `NAMING` — Domain Language Clarity
  6. `COMMENTS_DOCS` — Explaining Why & Markdown Cleanliness
  7. `STYLE_TYPES` — Type Strictness & Git Hygiene
  8. `LORE_LOCALISATION` — British English & Narrative Sovereignty

### Step 4: Generate & Sign the Review Report

1. Format findings using Conventional Comments (`issue`, `suggestion`, `question`, `praise`).
2. **Output Location:**
   * Present the structured review directly in-chat or in an Antigravity artifact canvas.
   * If the repository has a `docs/reviews/` directory (or the user requests a committed review), save the report to `docs/reviews/pr_<PR_NUMBER>_review.md`.
3. **Mandatory Provenance Signature:**
   Always sign the review with the formal provenance footer:

   ```markdown
   ---

   *Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Model: **`<Model Name>`** · Skill: **`review-pr v1.0.0`** · Date: `<YYYY-MM-DD>`*
   ```
