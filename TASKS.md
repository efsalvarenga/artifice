# Task Board & Feedback Pipeline: `artifice`

This document tracks active development tasks, roadmap milestones, and cross-project feedback items captured from consuming repositories (e.g. `emergent`, `arete`, `oude-mechanismen`).

---

## Incoming Feedback / Inbox

*This section receives asynchronously logged friction, missing edge cases, and enhancement proposals captured from active project sessions across the local repository ecosystem.*

* **[2026-11-01]** *(from `antigravity` @ `main`)*:
  - **Autonomy Mode:** `[SEMI]`
  - **Component:** `skills/local-code`, `skills/local-review`, Ollama model roster
  - **Operational Context:** Evaluating developer tooling and sovereign model tiers for Antigravity 2.0 workflows.
  - **Specific Friction & Defect / Enhancement:** The current local execution roster relies on `qwen2.5:14b` (`local-code`) and `mistral-nemo:12b` (`local-review`). `codestral:22b` provides specialised Fill-in-the-Middle (FIM) and code synthesis across 80+ programming languages, which could improve code generation and mutation test verification while keeping execution 100% on-device and preserving API quota. Need to evaluate RAM/VRAM footprint on Apple Silicon and inference latency via Ollama.
  - **Actionable Remediation:** Pull and benchmark `codestral:22b` via Ollama (`ollama pull codestral:22b`). Compare latency, memory pressure, and task fidelity against `qwen2.5:14b` on representative refactoring and test-generation tasks; if favourable, update `skills/local-code/SKILL.md` to support `codestral:22b` as an option.
  - **Status:** Open

* **[2026-11-01]** *(from `antigravity` @ `main`)*:
  - **Autonomy Mode:** `[SEMI]`
  - **Component:** `rules/quota-guardrails`, `skills/coordinate-fronts`, `skills/local-code`
  - **Operational Context:** Architecting model tiering and division of labour between frontier agents and local coding models in Antigravity 2.0.
  - **Specific Friction & Defect / Enhancement:** High-tier frontier model quota is frequently consumed on repetitive unit test boilerplate, syntax adjustments, and brute-force refactoring passes during multi-wave goals, accelerating quota burn (5-hour and weekly limits). A structured division of labour is needed where the orchestrating frontier model delegates bounded execution micro-passes to local engines (Codestral/Mistral via Ollama or low-cost API) while retaining high-level planning, Elephant-Goldfish specs, multi-agent coordination, and Git/PR drafting.
  - **Actionable Remediation:** Formulate an operational guideline and dispatch contract in `rules/quota-guardrails` (or as a coordination pattern in `skills/coordinate-fronts`) specifying criteria for offloading bounded micro-tasks (e.g. test boilerplate expansion, algorithmic syntax passes) to local/specialised models (`local-code` / Codestral) while keeping contract definitions and final PR verification strictly on frontier orchestrators.
  - **Status:** Open

<!-- Incoming entries are appended here following the format:
* **[YYYY-MM-DD]** *(from `<project>` @ `<branch>`)*:
  - **Component:** `<agent/skill/rule>`
  - **Operational Context:** `<what task was underway>`
  - **Specific Friction & Defect:** `<exact issue or edge case>`
  - **Actionable Remediation:** `<concrete proposal to implement>`
  - **Status:** Open
-->

> [!IMPORTANT]
> **The 4-Test Lesson Acceptance Gate (Default = DISCARD):**
> When triaging incoming feedback for potential promotion into global `AGENTS.md` or shared `skills/`:
> 1. **Measured Cost:** Did an actual defect, stalled task, or rework occur? (Hypothetical issues are discarded).
> 2. **Uncovered (`grep` First):** Does `grep` across existing rules/skills confirm no general rule already covers it? (If covered, sharpen existing triggers instead).
> 3. **Generalises:** Does it apply across multiple projects and repositories? (Local quirks belong in local code or local linters).
> 4. **Changes Decisions & Cannot Be Automated:** Does it alter what a competent model would do, and can it *not* be enforced via code, static types, or `verify.sh`? (*"Prefer code over prose"*).

---

## Active Roadmap & Backlog

### Milestone 1: Governance, Wave Coordination & Verification (v1.2.0)

- [x] `[AUTO]` **TASK-101**: Implement verification harness (`./scripts/verify.sh`) auditing Markdown cleanliness, YAML frontmatter syntax, relative link resolution, and Core Diet line/word ceilings on `AGENTS.md` (140 lines) and `SKILL.md` (180 lines).
- [x] `[AUTO]` **TASK-102**: Implement `scripts/build_review_dossier.py` to compile compact ($\le 40$-line) repository invariant digests, and wire it into `review-pr` and `local-review`.
- [x] `[SEMI]` **TASK-103**: Implement `skills/spec-egm/` (promoted from `emergent`) and portable validator `scripts/validate_egm.py`.
- [x] `[SEMI]` **TASK-104**: Implement `skills/coordinate-fronts/`, block contract templates, and the unified Decision Ledger (`scripts/check_decisions.py`).
- [x] `[SEMI]` **TASK-106**: Implement targeted test sabotage and mutation verification probe (`scripts/sabotage_check.py`) with worktree isolation, wired into `local-code` and `review-pr`.
- [x] `[SEMI]` **TASK-107**: Execute full verification (`verify.sh` + unit tests), run Gatekeeper PR review, and prepare companion slimming PR in `emergent` ([artifice PR #6](https://github.com/efsalvarenga/artifice/pull/6), [emergent PR #5](https://github.com/terra-campaigns/emergent/pull/5)).

### Soak Period Evaluation & Final Promotion (Execute After 9th November 2026 Only)

*The new orchestration framework, skills, and linters are currently under an operational soak across active workspaces. The PRs evaluated in this soak are:*
* **`artifice` [PR #6](https://github.com/efsalvarenga/artifice/pull/6):** `agent/ecosystem-governance-and-coordination` $\rightarrow$ `main` (Multi-front coordination, EGM, anti-bloat linters, dossier compiler, and mutation test probe).
* **`emergent` [PR #5](https://github.com/terra-campaigns/emergent/pull/5):** `agent/ecosystem-governance-slim` $\rightarrow$ `main` (Ecosystem de-duplication, slimmed `AGENTS.md`, and delegated EGM cycle).

- [ ] `[SEMI]` **TASK-108**: Triage `## Incoming Feedback / Inbox` items logged during the soak period using the 4-Test Lesson Acceptance Gate.
- [ ] `[AUTO]` **TASK-109**: Run full regression verification on `artifice` (`./scripts/lint.sh` and `./scripts/verify.sh`) on branch `agent/ecosystem-governance-and-coordination` ([PR #6](https://github.com/efsalvarenga/artifice/pull/6)).
- [ ] `[AUTO]` **TASK-110**: Run full regression verification on `emergent` (`./scripts/run_egm_cycle.sh validate` and `./scripts/verify_implementation.sh`) on branch `agent/ecosystem-governance-slim` ([PR #5](https://github.com/terra-campaigns/emergent/pull/5)).
- [ ] `[AUTO]` **TASK-111**: Execute closing pre-merge Dual-Model Consensus audits (`review-pr`) across both PRs.
- [ ] `[HUMAN]` **TASK-112**: Final human review and merge approval for [artifice PR #6](https://github.com/efsalvarenga/artifice/pull/6) and [emergent PR #5](https://github.com/terra-campaigns/emergent/pull/5) into their respective `main` branches.

### Future Milestones: Slimming & De-Engineering (December 2026)

- [ ] `[SEMI]` **TASK-113**: Comprehensive ecosystem audit to slim the repository of overlapping, redundant, and over-engineered processes across `artifice` and consuming repositories. Focus on:
  - Reviewing actual operational usage across the ecosystem to prune ceremonial gates, unused templates, and speculative abstractions.
  - Eliminating defensive prose in `AGENTS.md` and `SKILL.md` that can be replaced by deterministic linters (`scripts/lint.sh`) or dropped entirely ("prefer code over prose").
  - Consolidating overlapping workflows across skills (`spec-egm`, `coordinate-fronts`, `review-pr`, `coach-frameworks`) to minimise token overhead and developer cognitive load.

### Backlog & Operational Hardening

- [ ] `[AUTO]` **TASK-114**: Harden the EGM-to-wave handoff bridge:
  - Add an explicit `Target Specification: docs/designs/<NNN>_<feature>.md` metadata field to `skills/coordinate-fronts/references/block-contract-template.md` (requiring validation by `validate_egm.py`).
  - Add an explicit prerequisite in `skills/coordinate-fronts/SKILL.md` (Step 2) instructing coordinators to verify that `validate_egm.py` passes on the target specification before drafting block contracts for major architectural features.

---

## Completed Tasks

* **[2026-11-01]** `feat(core): bootstrap artifice repository with code-reviewer and developer-coach` ([PR #1](https://github.com/efsalvarenga/artifice/pull/1))
* **[2026-11-01]** `feat(tools): migrate developer-coach and coach-frameworks from emergent` ([PR #2](https://github.com/efsalvarenga/artifice/pull/2))
* **[2026-11-01]** `feat(review): establish dual-model consensus and on-device air-gapped review modes` ([PR #3](https://github.com/efsalvarenga/artifice/pull/3))
