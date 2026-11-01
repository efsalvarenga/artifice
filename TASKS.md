# Task Board & Feedback Pipeline: `artifice`

This document tracks active development tasks, roadmap milestones, and cross-project feedback items captured from consuming repositories (e.g. `emergent`, `arete`, `oude-mechanismen`).

---

## Incoming Feedback / Inbox

*This section receives asynchronously logged friction, missing edge cases, and enhancement proposals captured from active project sessions across the local repository ecosystem.*

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
- [ ] `[SEMI]` **TASK-107**: Execute full verification (`verify.sh` + unit tests), run Gatekeeper PR review, and prepare companion slimming PR in `emergent`.

---

## Completed Tasks

* **[2026-11-01]** `feat(core): bootstrap artifice repository with code-reviewer and developer-coach` ([PR #1](https://github.com/efsalvarenga/artifice/pull/1))
* **[2026-11-01]** `feat(tools): migrate developer-coach and coach-frameworks from emergent` ([PR #2](https://github.com/efsalvarenga/artifice/pull/2))
* **[2026-11-01]** `feat(review): establish dual-model consensus and on-device air-gapped review modes` ([PR #3](https://github.com/efsalvarenga/artifice/pull/3))
