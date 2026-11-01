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
  - **Status:** In Progress (Triaged into Milestone 2, TASK-201)

* **[2026-11-01]** *(from `antigravity` @ `main`)*:
  - **Autonomy Mode:** `[SEMI]`
  - **Component:** `rules/quota-guardrails`, `skills/local-code`
  - **Operational Context:** Architecting model tiering and division of labour between frontier agents and local coding models in Antigravity 2.0.
  - **Specific Friction & Defect / Enhancement:** High-tier frontier model quota is frequently consumed on repetitive unit test boilerplate, syntax adjustments, and brute-force refactoring passes during multi-wave goals, accelerating quota burn (5-hour and weekly limits). A structured division of labour is needed where the orchestrating frontier model delegates bounded execution micro-passes to local engines (Codestral/Mistral via Ollama or low-cost API) while retaining high-level planning, Elephant-Goldfish specs, multi-agent coordination, and Git/PR drafting.
  - **Actionable Remediation:** Formulate an operational guideline and dispatch contract in `rules/quota-guardrails` specifying criteria for offloading bounded micro-tasks (e.g. test boilerplate expansion, algorithmic syntax passes) to local/specialised models (`local-code` / Codestral) while keeping contract definitions and final PR verification strictly on frontier orchestrators.
  - **Status:** In Progress (Triaged into Milestone 2, TASK-205)

* **[2026-11-01]** *(from `oude-mechanismen` @ `v0.1.1`)*:
  - **Autonomy Mode:** `[AUTO]`
  - **Component:** `skills/lint-wiki/SKILL.md`
  - **Operational Context:** Structural auditing and diagnostic reporting across narrative campaign lore and static site notes.
  - **Specific Friction & Defect / Enhancement:** Running `lint-wiki` across extensive campaign vaults consumes high-tier cloud API quota for routine advisory checks (dead links, orphan pages, stubs, image references). Because this audit is advisory and non-blocking, it should be executed entirely on-device using local Ollama models (`qwen2.5:14b` or `mistral-nemo:12b`) paired with fast local Python scripts, preserving cloud quota for frontier coding tasks.
  - **Actionable Remediation:** Update `skills/lint-wiki/SKILL.md` in `oude-mechanismen` to target local Ollama models, offload deterministic checks to a local Python script, and run 100% on-device. Logged task in `oude-mechanismen/TASKS.md`.
  - **Status:** In Progress (Pattern codified in Milestone 2)

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
> 4. **Changes Decisions & Cannot Be Automated:** Does it alter what a competent model would do, and can it *not* be enforced via code, static types, or `lint.sh`? (*"Prefer code over prose"*).

---

## Active Roadmap & Backlog

### Milestone 1: Governance, Wave Coordination & Verification (v1.2.0) [COMPLETED]

*Milestone 1 established cross-repository governance, EGM verification, and anti-bloat linters. Merged to `main` via [artifice PR #6](https://github.com/efsalvarenga/artifice/pull/6).*

- [x] `[AUTO]` **TASK-101**: Implement unified static governance linter (`./scripts/lint.py` with `lint.sh` wrapper) for direct cross-repository execution, auditing Markdown cleanliness, YAML frontmatter syntax, relative link resolution, and Core Diet line/word ceilings on `AGENTS.md` (140 lines) and `SKILL.md` (180 lines).
- [x] `[AUTO]` **TASK-102**: Implement `scripts/build_review_dossier.py` to compile compact ($\le 40$-line) repository invariant digests, and wire it into `review-pr` and `local-review`.
- [x] `[SEMI]` **TASK-103**: Implement `skills/spec-egm/` (promoted from `emergent`) and portable validator `scripts/validate_egm.py`.
- [x] `[SEMI]` **TASK-104**: Absorbed core subagent orchestration rules (pilot-first execution, worktree isolation, independent verification) directly into global `AGENTS.md`; pruned obsolete `skills/coordinate-fronts/` and file-based decision ledgers.
- [x] `[SEMI]` **TASK-106**: Integrate active edge-case probing into `review-pr` (Pillar 2) and `local-code`, eliminating mechanical file mutation scripts in favour of analytical reviewer probing.
- [x] `[SEMI]` **TASK-107**: Execute static verification (`lint.sh`), run Gatekeeper PR review, and prepare companion slimming PR in `emergent` ([artifice PR #6](https://github.com/efsalvarenga/artifice/pull/6), [emergent PR #5](https://github.com/terra-campaigns/emergent/pull/5)).
- [x] `[AUTO]` **TASK-109**: Run full regression linting on `artifice` (`./scripts/lint.sh`) on branch `agent/ecosystem-governance-and-coordination` ([PR #6](https://github.com/efsalvarenga/artifice/pull/6)).
- [x] `[AUTO]` **TASK-111**: Execute closing pre-merge Dual-Model Consensus audits (`review-pr`) across PR #6.
- [x] `[HUMAN]` **TASK-112**: Final human review and merge approval for [artifice PR #6](https://github.com/efsalvarenga/artifice/pull/6) into `main`.

*Cross-Project Soak Note:* Companion PR in `emergent` ([PR #5](https://github.com/terra-campaigns/emergent/pull/5)) remains open under soak observation with pre-flight Gatekeeper approval.

---

### Milestone 2: Sovereign Quota Fortress — Automated Hybrid Offloading (v1.3.0)

*Milestone 2 eliminates the dichotomy between all-cloud and all-local execution. It introduces transparent hybrid offloading to resident Ollama models on Apple Silicon, consolidates the review tools portfolio, and establishes a strict division of labour to conserve cloud API quota.*

- [x] `[AUTO]` **TASK-201**: Evaluate Apple Silicon RAM/VRAM constraints and benchmark `codestral:22b` vs `qwen2.5:14b` / `qwen2.5-coder:14b` via Ollama; documented hardware boundaries and 16 GB Metal GPU limits.
- [x] `[AUTO]` **TASK-202**: Implement zero-dependency Ollama residency and lifecycle probe (`scripts/check_ollama.py`) with wave-leasing (`keep_alive: 5m`), explicit eviction (`unload --all`), and sub-100ms health checks.
- [x] `[SEMI]` **TASK-203**: Consolidate review skills by folding standalone `local-review` and `review-pr` into a single universal `skills/review/` (supporting PR, branch, file, and design doc modes), reducing skill count while preserving Core Diet limits ($\le 180$ lines).
- [x] `[SEMI]` **TASK-204**: Implement Gemini-orchestrated hybrid offloading in `skills/review/SKILL.md` (decomposing Pillar 2 edge cases to Qwen Coder and Pillar 6 prose to Mistral NeMo with explicit multi-model provenance footer).
- [x] `[SEMI]` **TASK-205**: Codify frontier-to-local division of labour guidelines in `skills/local-code/SKILL.md` and enshrine Step 1A Interactive Design Workshop in `skills/spec-egm/SKILL.md`.
- [x] `[AUTO]` **TASK-206**: Execute full static verification (`./scripts/lint.sh`), run Gatekeeper pre-flight review, and prepare PR ([artifice PR #7](https://github.com/efsalvarenga/artifice/pull/7)).

---

### Backlog & Future Milestones

- [ ] `[SEMI]` **TASK-113**: Comprehensive ecosystem audit to slim the repository of overlapping, redundant, and over-engineered processes across `artifice` and consuming repositories. Focus on:
  - Reviewing actual operational usage across the ecosystem to prune ceremonial gates, unused templates, and speculative abstractions.
  - Eliminating defensive prose in `AGENTS.md` and `SKILL.md` that can be replaced by deterministic linters (`scripts/lint.sh`) or dropped entirely ("prefer code over prose").
  - Consolidating overlapping workflows across skills (`spec-egm`, `review-pr`, `coach-frameworks`) to minimise token overhead and developer cognitive load.
- [ ] `[AUTO]` **TASK-114**: Harden the EGM-to-implementation handoff bridge:
  - Add an explicit check ensuring that `validate_egm.py` passes on the target specification before dispatching implementation subagents for major architectural features.
- [ ] `[SEMI]` **TASK-115**: Codify the Front-Loaded "Grill-Me" Interview Protocol into `spec-egm` and autonomous `/goal` workflows:
  - Update `skills/spec-egm/SKILL.md` (Elephant Phase) to mandate an interactive grilling session before implementation begins.
  - Require the agent to proactively interrogate the developer on all anticipated architectural trade-offs, qualitative preferences, third-party credentials, edge-case failure modes, and recovery fallbacks ahead of time.
  - Purpose: Maximise continuous autonomy during the execution phase by resolving all human-dependent decisions up front, enabling unattended execution once the developer's "OK" is given.
- [ ] `[SEMI]` **TASK-118**: Architect and configure dedicated Code Authoring Agent (`code-author`) and Implementation Protocol:
  - **Dedicated Author Persona:** Define the Principal Code Author ("The Craftsman") agent persona in `agents/code-author/agent.md`, establishing an explicit division of labour between feature authoring and the Gatekeeper (`code-reviewer`).
  - **Specification-Driven TDD Workflow:** Codify the implementation workflow following EGM specification approval:
    - Ingest approved design specifications (`docs/designs/*.md`) and repository invariants via `build_review_dossier.py`.
    - Adopt a strict contract-first test-driven approach: write failing boundary tests covering invariants before writing production logic.
    - Implement minimal, pure, deterministic code to turn tests green.
  - **Model Tiering & Local Offloading:** Establish operational guidelines for delegating bounded authoring tasks (e.g. test boilerplate, state reducer logic) to local coding models (`qwen2.5:14b` or `codestral:22b` via Ollama) or `flash`, while retaining architectural coordination on frontier models.
  - **Pre-Review Local Baseline Gate:** Mandate that authoring subagents run the repository's native test and lint suites (`./scripts/lint.sh`) locally to establish a 100% green baseline before requesting Gatekeeper review (`review-pr`) or drafting PRs.
- [ ] `[SEMI]` **TASK-119**: Audit and migrate versionable governance, global rules, and configuration from local Gemini config (`~/.gemini/config/`) into `artifice`:
  - **Global Rules Migration (`AGENTS.md`):** Evaluate transferring canonical ownership of the 10 core governance rules in `~/.gemini/config/AGENTS.md` (Git operations, Launchd, Markdown cleanliness, British English, Narrative Sovereignty, Feedback pipeline, Guido autonomy tags, Pre-flight recon, Quota & workspace guardrails, and Post-PR review trigger) into version-controlled `artifice` (e.g. `rules/global-agents.md` or `config/AGENTS.md`), symlinking or syncing them to `~/.gemini/config/AGENTS.md`.
  - **Config & Script Audit:** Review untracked files in `~/.gemini/config/` (such as `scripts/backup.sh`, custom sidecars, and MCP server templates in `mcp_config.json`) to determine which utilities belong in `artifice` as reproducible repository assets.
  - **Bootstrap & Dotfiles Harness:** Provide a one-command setup or symlink installer in `artifice/scripts/` (e.g. `./scripts/bootstrap_config.sh`) allowing an engineer on a fresh machine to clone `artifice` and instantly link skills, agents, and global governance rules into their local Antigravity environment.
- [ ] `[SEMI]` **TASK-120**: Analyse and codify the "Ruthless Occam's Razor" philosophy across the agentic ecosystem:
  - **Operational Analysis:** Evaluate the ecosystem to determine where the "ruthless Occam's razor" philosophy (anti-accretion, native runtime first, minimal sufficient implementation) should be formally codified to prevent premature abstractions and file sprawl.
  - **Target Checkpoints for Implementation:**
    1. *Specification Gate (`spec-egm`):* Prune speculative schemas and premature generality during Elephant drafting and Goldfish reviews.
    2. *Code Review Gate (`review-pr` / `code-reviewer` Pillar 3):* Sharpen the Gatekeeper rubric to explicitly challenge unnecessary classes, wrappers, and file proliferation in PR diffs.
    3. *Tooling Gate (`scripts/`):* Mandate single unified scripts and native in-memory runtime primitives over file-based IPC and multi-file satellite sprawl.
    4. *Global Governance (`AGENTS.md`):* Formulate a compact rule enshrining the 4 Razor Questions (*Native First*, *Observed vs Hypothetical*, *Consolidation*, *Code Over Prose*).


---

## Completed Tasks

* **[2026-11-01]** `feat(core): bootstrap artifice repository with code-reviewer and developer-coach` ([PR #1](https://github.com/efsalvarenga/artifice/pull/1))
* **[2026-11-01]** `feat(tools): migrate developer-coach and coach-frameworks from emergent` ([PR #2](https://github.com/efsalvarenga/artifice/pull/2))
* **[2026-11-01]** `feat(review): establish dual-model consensus and on-device air-gapped review modes` ([PR #3](https://github.com/efsalvarenga/artifice/pull/3))
