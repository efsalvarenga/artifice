# Task Board & Feedback Pipeline: `artifice`

This document tracks active development tasks, roadmap milestones, and cross-project feedback items captured from consuming repositories (e.g. `emergent`, `arete`, `oude-mechanismen`).

---

## Incoming Feedback / Inbox

*This section receives asynchronously logged friction, missing edge cases, and enhancement proposals captured from active project sessions across the local repository ecosystem.*

* **[2026-11-06]** *(from `oude-mechanismen` @ `efsalvarenga/prune-filter-studio`)*:
  - **Autonomy Mode:** `[AUTO]`
  - **Component:** `skills/vibe-execute/SKILL.md`
  - **Operational Context:** Proposing candidate models during `/vibe-execute` discovery.
  - **Specific Friction & Defect:** The agent output a static Markdown table in chat asking the user to type back their model selection in text, rather than using the native `ask_question` tool as an interactive multiple-choice prompt. This violated developer ergonomics and the expected interactive Grill-Me experience.
  - **Actionable Remediation:** Update `skills/vibe-execute/SKILL.md` under `## 2. Discover, Propose & Confirm` to explicitly mandate that discovered candidate model proposals must always be presented via the native `ask_question` tool, with the top candidate prefixed by `(Recommended)` and detailing engine locality, context limits, and identity fingerprint.
  - **Status:** Closed (Delivered in PR #11: codified native `ask_question` model proposal mandate in `skills/vibe-execute/SKILL.md`)

* **[2026-11-05]** *(from `oude-mechanismen` @ `efsalvarenga/decomposed-scribing-engine`)*:
  - **Autonomy Mode:** `[AUTO]`
  - **Component:** `scripts/check_ollama.py`, `rules/quota-guardrails`
  - **Operational Context:** Standardised local Ollama models on 16 GB Apple Silicon M5; uninstalled `mistral-nemo` due to repetition loops and factual hallucinations.
  - **Specific Friction & Defect:** `scripts/check_ollama.py` hardcodes `mistral-nemo` as the sole local model for prose/docs tasks (`task_type in ("prose", "docs", "adr", "architecture")`). When `mistral-nemo` is uninstalled, `check_ollama.py` immediately falls back to `cloud-flash` with exit code 2, even though `qwen2.5:14b` is installed, resident, and highly capable of local prose synthesis.
  - **Actionable Remediation:** Update `scripts/check_ollama.py` to allow `qwen2.5:14b` as a secondary local candidate for prose/docs tasks when `mistral-nemo` is missing before falling back to cloud models.
  - **Status:** Open

* **[2026-11-01]** *(from `antigravity` @ `main`)*:
  - **Autonomy Mode:** `[SEMI]`
  - **Component:** `skills/local-code`, `skills/local-review`, Ollama model roster
  - **Operational Context:** Evaluating developer tooling and sovereign model tiers for Antigravity 2.0 workflows.
  - **Specific Friction & Defect / Enhancement:** The current local execution roster relies on `qwen2.5:14b` (`local-code`) and `mistral-nemo:12b` (`local-review`). `codestral:22b` provides specialised Fill-in-the-Middle (FIM) and code synthesis across 80+ programming languages, which could improve code generation and mutation test verification while keeping execution 100% on-device and preserving API quota. Need to evaluate RAM/VRAM footprint on Apple Silicon and inference latency via Ollama.
  - **Actionable Remediation:** Pull and benchmark `codestral:22b` via Ollama (`ollama pull codestral:22b`). Compare latency, memory pressure, and task fidelity against `qwen2.5:14b` on representative refactoring and test-generation tasks; if favourable, update `skills/local-code/SKILL.md` to support `codestral:22b` as an option.
  - **Status:** Closed (Delivered in Milestone 2, PR #7)

* **[2026-11-01]** *(from `antigravity` @ `main`)*:
  - **Autonomy Mode:** `[SEMI]`
  - **Component:** `rules/quota-guardrails`, `skills/local-code`
  - **Operational Context:** Architecting model tiering and division of labour between frontier agents and local coding models in Antigravity 2.0.
  - **Specific Friction & Defect / Enhancement:** High-tier frontier model quota is frequently consumed on repetitive unit test boilerplate, syntax adjustments, and brute-force refactoring passes during multi-wave goals, accelerating quota burn (5-hour and weekly limits). A structured division of labour is needed where the orchestrating frontier model delegates bounded execution micro-passes to local engines (Codestral/Mistral via Ollama or low-cost API) while retaining high-level planning, Elephant-Goldfish specs, multi-agent coordination, and Git/PR drafting.
  - **Actionable Remediation:** Formulate an operational guideline and dispatch contract in `rules/quota-guardrails` specifying criteria for offloading bounded micro-tasks (e.g. test boilerplate expansion, algorithmic syntax passes) to local/specialised models (`local-code` / Codestral) while keeping contract definitions and final PR verification strictly on frontier orchestrators.
  - **Status:** Closed (Delivered in Milestone 2, PR #7)

* **[2026-11-01]** *(from `artifice` @ `agent/sovereign-quota-fortress`)*:
  - **Autonomy Mode:** `[SEMI]`
  - **Component:** `skills/spec-egm`, `rules/egm-governance`, `scripts/validate_egm.py`
  - **Operational Context:** Scoping and launching Milestone 2 ("Sovereign Quota Fortress"). The developer requested an upfront interactive Design Workshop followed by plan building and autonomous execution.
  - **Specific Friction & Defect:**
    1. The agent conflated a conversational chat Q&A with the formal EGM design phase. It treated brief conversational agreement as license to execute immediately, completely omitting the formal, persistent Elephant Specification (`docs/designs/<NNN>_<feature>.md`).
    2. The agent bypassed the adversarial zero-context Goldfish review (`docs/reviews/<NNN>_<feature>_review.md`), eliminating the contract-checking safety net.
    3. `artifice` lacked the repository infrastructure for EGM (`docs/designs/`, `docs/reviews/`, and local pre-implementation enforcement), failing to dogfood its own `validate_egm.py` validator.
    4. By jumping directly from chat into code modification, the developer was deprived of a formal, persistent architectural canvas to inspect, review, and refine before implementation started. In `emergent`, this phase was an explicit, unhurried, document-grounded step backed by `run_egm_cycle.sh`.
  - **Actionable Remediation:**
    1. **Dogfood EGM in `artifice`:** Scaffold `docs/designs/` and `docs/reviews/` in `artifice` and formally author `docs/designs/001_sovereign_quota_fortress.md` accompanied by an adversarial Goldfish review in `docs/reviews/001_sovereign_quota_fortress_review.md`.
    2. **Enforce Pre-Implementation Gate in `lint.sh`:** Update `./scripts/lint.sh` to execute `python3 scripts/validate_egm.py .` as a mandatory static gate whenever `docs/designs/` is present, mechanically blocking PR creation unless EGM contracts are 100% green.
    3. **Enshrine Procedural Invariant in `AGENTS.md` & `spec-egm`:** Clarify that chat Q&A is merely Step 1A (Workshop); Step 1B (formal spec document) and Step 2 (Goldfish review) must produce committed markdown artifacts *before* any implementation code or PR drafting is permitted.
  - **Status:** Closed (Delivered in Milestone 2, PR #7)

* **[2026-11-01]** *(from `oude-mechanismen` @ `v0.1.1`)*:
  - **Autonomy Mode:** `[AUTO]`
  - **Component:** `skills/lint-wiki/SKILL.md`
  - **Operational Context:** Structural auditing and diagnostic reporting across narrative campaign lore and static site notes.
  - **Specific Friction & Defect / Enhancement:** Running `lint-wiki` across extensive campaign vaults consumes high-tier cloud API quota for routine advisory checks (dead links, orphan pages, stubs, image references). Because this audit is advisory and non-blocking, it should be executed entirely on-device using local Ollama models (`qwen2.5:14b` or `mistral-nemo:12b`) paired with fast local Python scripts, preserving cloud quota for frontier coding tasks.
  - **Actionable Remediation:** Update `skills/lint-wiki/SKILL.md` in `oude-mechanismen` to target local Ollama models, offload deterministic checks to a local Python script, and run 100% on-device. Logged task in `oude-mechanismen/TASKS.md`.
  - **Status:** In Progress (Pattern codified in Milestone 2)

* **[2026-11-02]** *(from `artifice` @ `agent/craftsman-tdd-pipeline`)*:
  - **Autonomy Mode:** `[SEMI]`
  - **Component:** `skills/spec-egm`, `rules/egm-governance`
  - **Operational Context:** Transitioning from Step 1A (Grill-Me Workshop) to Step 1B (Spec Drafting) for Milestone 3.
  - **Specific Friction & Defect:** The agent promised to proceed to Step 1B to draft the technical specification (`docs/designs/002_craftsman_tdd_pipeline.md`). However, instead of drafting the document, presenting it to the human developer, and pausing for inspection and approval, the agent cascaded autonomously through Step 1B, Step 2 (Goldfish review), Step 3 (EGM validation), and the entire implementation (TDD Red/Green code, commits, git push, PR creation) in a single uninterrupted turn. The human author was completely deprived of the design canvas review phase.
  - **Actionable Remediation:** Update `skills/spec-egm/SKILL.md` and repository guidelines to mandate an explicit interactive human pause after Step 1B / Step 2 before implementation begins (`[SEMI]` gate). The agent must output the design specification, present its key sections to the user, and pause for human sign-off before entering Step 3 or dispatching implementation subagents, unless unattended continuous execution (`/goal`) was explicitly commanded.
  - **Status:** Open

* **[2026-11-02]** *(from `oude-mechanismen` @ `efsalvarenga/decomposed-scribing-engine`)*:
  - **Autonomy Mode:** `[AUTO]`
  - **Component:** `rules/git-operations`, `agents/code-author`
  - **Operational Context:** Autonomous commit and PR creation on engineering feature branch in `oude-mechanismen`.
  - **Specific Friction & Defect:** The model authored a feature commit and opened PR #2 in `oude-mechanismen` without appending model provenance git trailers (`Model-Author:`, `Agent-Role:`, `Co-authored-by:`). While this attribution standard was codified inside `artifice` (`agents/code-author/agent.md`), it was omitted from the cross-repository `Git Operations Constraint` rule, leading to missing agent co-authorship in Git logs across consuming engineering repositories.
  - **Actionable Remediation:** Promote the Model Commit Authorship invariant into the global `Git Operations Constraint` user rule, mandating that all autonomous commits generated by models append `Model-Author`, `Agent-Role: code-author`, and `Co-authored-by: <AGENT_NAME> <<MODEL_HANDLE>@antigravity.local>` trailers by default.
  - **Status:** Open

* **[2026-11-03]** *(from `oude-mechanismen` @ `efsalvarenga/decomposed-scribing-engine`)*:
  - **Autonomy Mode:** `[AUTO]`
  - **Component:** `skills/spec-egm`, `agents/code-author`, `rules/task-board-governance`
  - **Operational Context:** Concluding milestones, feature branches, and Pull Requests across repositories.
  - **Specific Friction & Defect:** Task boards (`TASKS.md`) across repositories accumulate completed items indefinitely in `## Incoming Feedback / Inbox` or active boards, leading to file bloat and obscuring pending tasks. Agents frequently mark tasks as completed in-place rather than purging them, while `CHANGELOG.md` is left out of sync with the tasks actually delivered in the PR.
  - **Actionable Remediation:** Codify an automated **Task Lifecycle & Purging Step** into the core `artifice` workflow (`spec-egm`, `code-author`, and PR finalisation procedures): upon completing a task or drafting a PR, the agent must autonomously:
    1. Transfer the delivered task items into `CHANGELOG.md` under `## [Unreleased]` (adhering to Keep a Changelog categories: Added, Changed, Fixed, etc.).
    2. Purge the completed entries completely from `TASKS.md` so the board exclusively reflects open and actionable work.
    3. Include `CHANGELOG.md` and `TASKS.md` updates in the final feature commit before opening the PR.
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

### Milestone 2: Sovereign Quota Fortress — Automated Hybrid Offloading (v1.3.0) [COMPLETED]

*Milestone 2 established sovereign hybrid execution, wave-leased host memory management, the unified /review skill, and EGM Gate 5 validation. Merged to `main` via [artifice PR #7](https://github.com/efsalvarenga/artifice/pull/7).*

- [x] `[AUTO]` **TASK-201**: Evaluate Apple Silicon RAM/VRAM constraints and benchmark `codestral:22b` vs `qwen2.5:14b` / `qwen2.5-coder:14b` via Ollama; documented hardware boundaries and 16 GB Metal GPU limits.
- [x] `[AUTO]` **TASK-202**: Implement zero-dependency Ollama residency and lifecycle probe (`scripts/check_ollama.py`) with wave-leasing (`keep_alive: 5m`), explicit eviction (`unload --all`), and sub-100ms health checks.
- [x] `[SEMI]` **TASK-203**: Consolidate review skills by folding standalone `local-review` and `review-pr` into a single universal `skills/review/` (supporting PR, branch, file, and design doc modes), reducing skill count while preserving Core Diet limits ($\le 180$ lines).
- [x] `[SEMI]` **TASK-204**: Implement Gemini-orchestrated hybrid offloading in `skills/review/SKILL.md` (decomposing Pillar 2 edge cases to Qwen Coder and Pillar 6 prose to Mistral NeMo with explicit multi-model provenance footer).
- [x] `[SEMI]` **TASK-205**: Codify frontier-to-local division of labour guidelines in `skills/local-code/SKILL.md` and enshrine Step 1A Interactive Design Workshop in `skills/spec-egm/SKILL.md`.
- [x] `[AUTO]` **TASK-206**: Execute full static verification (`./scripts/lint.sh`), run Gatekeeper pre-flight review, and prepare PR ([artifice PR #7](https://github.com/efsalvarenga/artifice/pull/7)).

---

### Milestone 3: The Craftsman & TDD Pipeline — Sovereign Code Authoring (v1.4.0) [IN PROGRESS]

*Milestone 3 completes the agent triumvirate (Catalyst -> Craftsman -> Gatekeeper) by introducing the dedicated Code Authoring Agent (`code-author`), codifying the Front-Loaded "Grill-Me" Interview Protocol into `spec-egm`, and hardening the EGM contract handoff bridge.*

- [x] `[AUTO]` **TASK-114**: Harden the EGM-to-implementation handoff bridge:
  - Added targeted specification validation (`--spec <id_or_path>`) to `scripts/validate_egm.py` supporting numeric prefixes and exact filenames.
  - Verified directly in `./scripts/lint.sh` static governance gate.
- [x] `[SEMI]` **TASK-115**: Codify the Front-Loaded "Grill-Me" Interview Protocol into `spec-egm` and autonomous `/goal` workflows:
  - Updated `skills/spec-egm/SKILL.md` (Step 1A) to mandate front-loaded interrogation across four key categories (Scope, Schemas, Model Tiering, Verification) before drafting specifications.
  - Codified explicit human workshop confirmation gate prior to no-code specification authoring.
- [x] `[SEMI]` **TASK-118**: Architect and configure dedicated Code Authoring Agent (`code-author`) and Implementation Protocol:
  - **Dedicated Author Persona:** Defined Principal Code Author ("The Craftsman") agent persona in `agents/code-author/agent.md`, establishing the contract-first counterpart to The Gatekeeper (`code-reviewer`).
  - **Specification-Driven TDD Workflow:** Codified the 5-phase implementation lifecycle: Ingestion -> Red (failing invariant assertions) -> Green (minimal deterministic logic) -> Refactor (Occam's razor) -> Pre-Review Baseline Gate.
  - **Model Commit Authorship:** Enshrined the rule that models that author code author the commits, requiring explicit model provenance trailers (`Model-Author` and `Co-authored-by`).
  - **Model Tiering & Local Offloading:** Established division of labour with `skills/local-code` (Ollama `qwen2.5-coder:14b` / `flash`) and wave memory purging.
- [ ] `[AUTO]` **TASK-121**: Execute full static verification (`./scripts/lint.sh`), run Gatekeeper pre-flight review (`review`), and prepare PR.

---

### Backlog & Future Milestones

- [ ] `[SEMI]` **TASK-113**: Comprehensive ecosystem audit to slim the repository of overlapping, redundant, and over-engineered processes across `artifice` and consuming repositories. Focus on:
  - Reviewing actual operational usage across the ecosystem to prune ceremonial gates, unused templates, and speculative abstractions.
  - Eliminating defensive prose in `AGENTS.md` and `SKILL.md` that can be replaced by deterministic linters (`scripts/lint.sh`) or dropped entirely ("prefer code over prose").
  - Consolidating overlapping workflows across skills (`spec-egm`, `review-pr`, `coach-frameworks`) to minimise token overhead and developer cognitive load.
- [ ] `[SEMI]` **TASK-119**: Audit and migrate versionable governance, global rules, and configuration from local Gemini config (`~/.gemini/config/`) into `artifice`:
  - **Global Rules Migration (`AGENTS.md`):** Evaluate transferring canonical ownership of the 10 core governance rules in `~/.gemini/config/AGENTS.md` (Git operations, Launchd, Markdown cleanliness, British English, Narrative Sovereignty, Feedback pipeline, Guido autonomy tags, Pre-flight recon, Quota & workspace guardrails, and Post-PR review trigger) into version-controlled `artifice` (e.g. `rules/global-agents.md` or `config/AGENTS.md`), symlinking or syncing them to `~/.gemini/config/AGENTS.md`.
  - **Config & Script Audit:** Review untracked files in `~/.gemini/config/` (such as `scripts/backup.sh`, custom sidecars, and MCP server templates in `mcp_config.json`) to determine which utilities belong in `artifice` as reproducible repository assets.
  - **Bootstrap & Dotfiles Harness:** Provide a one-command setup or symlink installer in `artifice/scripts/` (`./scripts/install_antigravity.sh`) allowing an engineer on a fresh machine to clone `artifice` and instantly link skills, agents, and global governance rules into their local Antigravity environment. (Delivered via `scripts/install_antigravity.sh`).
- [ ] `[SEMI]` **TASK-120**: Analyse and codify the "Ruthless Occam's Razor" philosophy across the agentic ecosystem:
  - **Operational Analysis:** Evaluate the ecosystem to determine where the "ruthless Occam's razor" philosophy (anti-accretion, native runtime first, minimal sufficient implementation) should be formally codified to prevent premature abstractions and file sprawl.
  - **Target Checkpoints for Implementation:**
    1. *Specification Gate (`spec-egm`):* Prune speculative schemas and premature generality during Elephant drafting and Goldfish reviews.
    2. *Code Review Gate (`review-pr` / `code-reviewer` Pillar 3):* Sharpen the Gatekeeper rubric to explicitly challenge unnecessary classes, wrappers, and file proliferation in PR diffs.
    3. *Tooling Gate (`scripts/`):* Mandate single unified scripts and native in-memory runtime primitives over file-based IPC and multi-file satellite sprawl.
    4. *Global Governance (`AGENTS.md`):* Formulate a compact rule enshrining the 4 Razor Questions (*Native First*, *Observed vs Hypothetical*, *Consolidation*, *Code Over Prose*).
- [ ] `[SEMI]` **TASK-122**: Enshrine Markdown Symlink Architecture for Prompts and Skills (Zero-Latency Loop):
  - **Core Architectural Invariant:** Retain `agents/` and `skills/` as canonical Markdown symlinks mapped into Antigravity (`~/.gemini/config/skills.json`, `~/.gemini/config/agents/`) and Copilot (`~/.copilot/agents`, `~/.copilot/skills`) rather than compiling or bundling them into static package distributions (e.g. pure APM compilation).
  - **Zero-Latency Rationale:** Preserves instantaneous, uncompiled local prompt engineering and iteration loops without build or re-installation steps.
  - **Decoupled Execution Boundary:** Maintain a strict separation between declarative prompt guidance (retained as symlinked markdown) and imperative machinery/scripts (`scripts/` evaluated for standalone CLI packaging via `pyproject.toml` or FastMCP exposure).

---

## Completed Tasks

* **[2026-11-01]** `feat(core): bootstrap artifice repository with code-reviewer and developer-coach` ([PR #1](https://github.com/efsalvarenga/artifice/pull/1))
* **[2026-11-01]** `feat(tools): migrate developer-coach and coach-frameworks from emergent` ([PR #2](https://github.com/efsalvarenga/artifice/pull/2))
* **[2026-11-01]** `feat(review): establish dual-model consensus and on-device air-gapped review modes` ([PR #3](https://github.com/efsalvarenga/artifice/pull/3))
* **[2026-11-01]** `feat(governance): integrate wave coordination, EGM, and anti-bloat verification` ([PR #6](https://github.com/efsalvarenga/artifice/pull/6))
* **[2026-11-01]** `feat(review): establish sovereign hybrid offloading and unified review skill` ([PR #7](https://github.com/efsalvarenga/artifice/pull/7))
