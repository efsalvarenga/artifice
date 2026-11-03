# Proposal: Lean Refactoring of the Copilot Symlink Integration

**Document:** `docs/proposals/copilot_symlink_refactoring_proposal.md`  
**Target Branch:** `feat/copilot-symlink-integration` ([PR #9](https://github.com/efsalvarenga/artifice/pull/9))  
**Status:** Staged Proposal  
**Author:** Principal Code Reviewer & Developer  
**Date:** 2026-11-03  

---

## 1. Executive Summary

This proposal outlines the architectural evaluation, empirical bloat analysis, and step-by-step remediation plan for the GitHub Copilot integration introduced in Pull Request [#9](https://github.com/efsalvarenga/artifice/pull/9).

While the core premise of PR #9 — exposing Artifice's three agent roles and four skills to GitHub Copilot through user-level directory symlinks and thin adapter manifests — is sound and architecturally elegant, its current implementation introduces four critical regressions in existing Antigravity workflows and significantly inflates the repository and prompt footprint:

1. **Repository Footprint Inflation:** Increases total repository word count by **56.5% (+8,399 words)** and line count by **36.9% (+918 lines)** across 7 new files.
2. **Context-Window & Prompt Bloat:** Quietly inflates the canonical agent and skill prompt payload by **30.5% (+1,260 words)**, evading existing line-based ceilings by packing 90–130-word paragraphs into single unwrapped lines.
3. **Antigravity Workflow Regressions:** Hard-codes uninstalled Ollama model tags causing wave-leasing failures, introduces subagent resource-resolution deadlocks when operating in consuming repositories, breaks autonomous feature-branch commit conventions during unattended `/goal` sessions, and invalidates offline `--local` review execution in cloud sessions.
4. **Tooling & Test Inconsistency:** Introduces 474 lines of Bash installer and disposable test fixtures that bypass native static linting, reversing the Occam's razor anti-sprawl refactoring completed in commit `f62cca1`.

This proposal provides an actionable, five-phase blueprint to retain the valuable Copilot adapters whilst cutting ~80% of the added code and documentation, eliminating 100% of the prompt bloat, and restoring seamless Antigravity compatibility.

---

## 2. Evaluation: Antigravity Workflow Regressions

### 2.1 Hard Failure in `review` Wave-Leasing (Invalid Model Tags)

* **Baseline (`main`):** In `skills/review/SKILL.md`, Step 3 leases `qwen2.5:14b` and `mistral-nemo:latest`. These tags match the physical models resident on the host machine as reported by `python3 scripts/check_ollama.py status`.
* **PR #9 Regression:** Rewrites the warming procedure to hard-code `qwen2.5-coder:14b` and `mistral-nemo:12b`. Because neither tag is present locally, executing Step 3 causes `check_ollama.py warm` to fail with exit code `1` (`HTTP 404: model not found`).

### 2.2 Subagent Resource-Resolution Deadlock in Consuming Repositories

* **PR #9 Change:** Replaces all direct paths to Artifice scripts (`~/Repos/artifice/scripts/...`) across all agents and skills with a mandatory multi-step protocol: verify `$HOME/.local/share/artifice`; if absent, resolve the containing directory of `agent.md` and ascend two levels; if unavailable, *"stop and request repair; never guess a username-specific path."*
* **Failure Mechanism:** On hosts where Copilot installation has not been run, `$HOME/.local/share/artifice` does not exist. When Antigravity dispatches a subagent via `invoke_subagent` in another project (e.g. `oude-mechanismen`), it injects the Markdown body into the prompt without exposing the physical file path of `agent.md`. Without an anchor, without a file path, and with an explicit prohibition against falling back to `~/Repos/artifice`, the subagent halts immediately instead of executing utilities like `validate_egm.py` or `build_review_dossier.py`.

### 2.3 Contradiction of Autonomous Git Operations & `/goal` Waves

* **Ecosystem Standard:** Global user rules (`~/.gemini/config/AGENTS.md`) explicitly authorise autonomous commits, pushes, and PR creation on dedicated feature branches in engineering repositories (`AretePX/*`) once local baselines pass. Milestone 3 (`002_craftsman_tdd_pipeline.md`) mandates atomic model-authored commits across the Red, Green, and Refactor phases.
* **PR #9 Regression:** Injects Copilot-specific permission disclaimers across all 7 canonical agent and skill files:
  * *"Require explicit, operation-specific user authorisation for branch changes, staging, commits, pushes, and PR publication."*
  * *"TDD phases complete without commits when permission is absent."*
  * *"A generic autonomous goal does not waive this pause."*
* **Impact:** In Antigravity, this instruction directly contradicts `<user_rules>`, paralyses autonomous `/goal` waves, and halts the deterministic TDD commit cadence.

### 2.4 Invalidation of Offline Mode & Weakened Static Linting

* **Disabling `--local` in Antigravity:** PR #9 alters `--local` in `skills/review/SKILL.md` to require: *"reject cloud-session execution before reading the target... stop before protected-content ingestion and require a genuinely local session."* Because Antigravity is inherently a cloud-orchestrated environment with local subagent offloading, this instruction forces the agent to abort `/review --local` rather than executing local Ollama inference.
* **Circumvention of Gate 3 Link Linting:** PR #9 strips relative Markdown links (e.g. `[../../scripts/validate_egm.py](...)`) across all skills, replacing them with unlinked prose. Consequently, `scripts/lint.py` Gate 3 can no longer mechanically detect broken script or agent references.

---

## 3. Empirical Bloat & Footprint Analysis

### 3.1 Repository Metrics (`main` vs PR #9)

| Metric | `main` Baseline | PR #9 (`copilot`) | Delta |
| :--- | ---: | ---: | ---: |
| **Tracked Files** | 23 | 30 | **+7 files (+30.4%)** |
| **Total Lines** | 2,487 | 3,405 | **+918 lines (+36.9%)** |
| **Total Words** | 14,864 | 23,263 | **+8,399 words (+56.5%)** |
| **Total Size** | 131.1 KB | 196.5 KB | **+65.4 KB (+49.9%)** |

Key drivers of repository inflation:
* **Installer & Test Harness:** `scripts/install_copilot.sh` (216 lines) and `tests/test_install_copilot.sh` (258 lines) total 474 lines of Bash to manage three symlinks.
* **Orphaned Test Directory:** Commit `f62cca1` previously removed `tests/` and Gate 6 to prevent script sprawl. PR #9 reintroduces `tests/` at triple the size, yet `./scripts/lint.sh` never executes it.
* **Specification Bloat:** Design `003` and its Goldfish review add 4,266 words (305 lines), exceeding Designs `001` and `002` combined.
* **README Expansion:** `README.md` grows by +62 lines and +833 words (+135.7%), with the Copilot section alone exceeding the original document's entire length.

### 3.2 Context-Window & Prompt Inflation

`scripts/lint.py` enforces a 180-line ceiling on skills, but lacks word-count limits. PR #9 stays beneath the line limits by formatting long paragraphs onto single lines, significantly inflating the token payload of every agent and skill:

| Prompt Entrypoint | `main` Words | PR #9 Words | Word Inflation |
| :--- | ---: | ---: | ---: |
| `skills/local-code/SKILL.md` | 271 | 429 | **+58.3%** |
| `skills/spec-egm/SKILL.md` | 548 | 772 | **+40.9%** |
| `skills/coach-frameworks/SKILL.md` | 484 | 634 | **+31.0%** |
| `agents/code-author/agent.md` | 759 | 982 | **+29.4%** |
| `skills/review/SKILL.md` | 822 | 1,026 | **+24.8%** |
| `agents/code-reviewer/agent.md` | 650 | 809 | **+24.5%** |
| `agents/developer-coach/agent.md` | 595 | 737 | **+23.9%** |
| **Total Canonical Payload** | **4,129** | **5,389** | **+1,260 words (+30.5%)** |

---

## 4. Step-by-Step Lean Refactoring Plan

### Phase 1: Workspace Preparation (`[AUTO]`)

1. Check out `feat/copilot-symlink-integration` into an isolated Git worktree or active feature branch.
2. Confirm that working tree state on `main` remains clean and unaffected.

### Phase 2: Right-Sizing Specification `003` & Goldfish Review (`[AUTO]`)

1. **Streamline `docs/designs/003_copilot_symlink_integration.md`:**
   * Condense the specification from 248 lines / 3,570 words to ~95 lines / ~850 words, preserving the four required EGM sections.
   * Formalise three lean invariants:
     * *Invariant 1 (Adapter Isolation):* Copilot-specific tool definitions and loading directives remain strictly encapsulated in `integrations/copilot/agents/*.agent.md`.
     * *Invariant 2 (Zero Canonical Regression):* Canonical agents and skills retain relative Markdown links, unblocked autonomous TDD/PR workflows under client global rules, and resilient `${ARTIFICE_ROOT:-$HOME/Repos/artifice}` resolution.
     * *Invariant 3 (Idempotent Installer):* `scripts/install_copilot.sh` creates and validates the three required symlinks without overwriting existing files or directories.
2. **Conduct Zero-Context Goldfish Review (`docs/reviews/003_copilot_symlink_integration_review.md`):**
   * Re-evaluate the right-sized specification against the Goldfish rubric.
   * Verify contract validity via `python3 scripts/validate_egm.py . --spec 003` (exit code `0`).

### Phase 3: Restoring Canonical Prompts & Eliminating Regressions (`[AUTO]`)

1. **Restore Canonical Instructions:**
   * Revert the 7x duplicated permission disclaimers and path ascent procedures across `agents/` and `skills/`.
   * Restore clickable relative Markdown links (`[../../scripts/...](...)`) to satisfy `scripts/lint.py` Gate 3.
2. **Apply Surgical Portability Improvements:**
   * In shell snippets, use `"${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/..."` to allow seamless overrides when invoked via Copilot adapters while preserving default Antigravity paths.
   * In `skills/review/SKILL.md`, use dynamic model selection (`python3 scripts/check_ollama.py select`) or valid installed tags (`qwen2.5:14b`, `mistral-nemo:latest`).
   * In `agents/code-reviewer/agent.md`, guard the global rules check to read `~/.gemini/config/AGENTS.md` if present alongside active client instructions.

### Phase 4: Encapsulating Adapters, Right-Sizing Installer & Linting (`[AUTO]`)

1. **Retain Thin Copilot Adapters:**
   * Preserve `integrations/copilot/agents/{code-author,code-reviewer,developer-coach}.agent.md` (~11 lines each).
   * Ensure adapters instruct Copilot to read canonical roles from `~/.local/share/artifice/agents/<role>/agent.md` and set `ARTIFICE_ROOT`.
2. **Replace `scripts/install_copilot.sh` & Remove `tests/`:**
   * Replace the 216-line installer with a concise, POSIX-compliant ~45-line script supporting `install`, `--check`, and `--help`.
   * Remove `tests/test_install_copilot.sh`, eliminating redundant test harness sprawl.
3. **Enhance Static Governance (`scripts/lint.py`):**
   * Update Gate 2 to validate YAML frontmatter in `integrations/copilot/agents/*.agent.md`.
   * Update Gate 4 to enforce word-count limits on skill files (`SKILL_WORD_LIMIT = 1000`) and agent files (`AGENT_WORD_LIMIT = 900`).
4. **Condense `README.md`:**
   * Replace the 833-word essay with a clear ~18-line integration guide.

### Phase 5: Verification & Pull Request Update (`[AUTO]` $\rightarrow$ `[HUMAN]`)

1. **Execute Native Baselines:**
   * Run `./scripts/lint.sh` to ensure 100% green status across all gates.
   * Smoke-test `install_copilot.sh` and `--check` in a disposable temporary directory.
2. **Commit & Push:**
   * Commit the refactoring to `feat/copilot-symlink-integration` with structured model authorship trailers.
   * Push to remote and update PR #9 description.
3. **Advisory Review & Merge Gate:**
   * Re-run the 8-Pillar audit and post a revised advisory comment to PR #9.
   * Present findings for final human merge sign-off (`[HUMAN]`).

---

## 5. Target Outcomes

| Dimension | Current PR #9 | Refactored Target | Impact |
| :--- | ---: | ---: | :--- |
| **Canonical Prompt Bloat** | +1,260 words (+30.5%) | < +30 words (< +0.8%) | Zero context penalty in Antigravity |
| **Installer & Test Lines** | 474 lines | ~45 lines | -90% shell code, no test sprawl |
| **Antigravity Wave-Leasing** | Broken (404 tags) | Fully Functional | Uses installed host models |
| **Subagent Portability** | Deadlocks without anchor | Fully Functional | Clean fallback to `~/Repos/artifice` |
| **Autonomous Commits / TDD** | Paralyzed by disclaimers | Fully Functional | Preserves `<user_rules>` and TDD |
| **Copilot Capability** | Functional | Fully Functional | 100% feature parity via symlinks |
