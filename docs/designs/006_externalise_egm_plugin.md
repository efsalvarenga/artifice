# Externalise EGM to Upstream Plugin and Document Mistral Goldfish Offloading

**Author:** efsalvarenga  
**Status:** Proposed  
**Date:** 2026-11-15  
**Tracking PR:** [PR #29](https://github.com/efsalvarenga/artifice/pull/29)

> **Historical record:** the `vibe-execute` gateway and `scripts/vibe_execute.py` / `check_ollama.py` / `model_inventory.py` described here were retired by [design 008](008_vibe_shrink_review_gh_posting.md).

## Overview

Artifice currently ships its own custom Elephant-Goldfish Model (EGM) specification skill, templates, and mechanical section-header validator alongside its core agents and model-dispatch tools. Because the upstream `google/elephant-goldfish-model` (`egm`) plugin is used directly for ideation, drafting, and multi-lens review, Artifice's internal EGM copy duplicates upstream capabilities while enforcing legacy section-number checks that reject upstream-formatted specifications.

This design removes Artifice's built-in EGM implementation and establishes the upstream `egm` plugin as a documented external prerequisite. It replaces mechanical section-header validation with early Pull Request and commit provenance referencing upstream `egm-review` Stage 9 (Implementation Readiness Test) sign-off. It also removes the legacy `docs/designs/` regex scraper from `scripts/build_review_dossier.py`, and documents how to pair upstream `egm` with `/vibe-execute` (`scripts/vibe_execute.py`) so stateless Goldfish review passes run on hosted Mistral models instead of consuming Gemini quota.

## The Problem

Maintaining a bespoke EGM implementation inside Artifice creates three problems:

1.  **Duplicate workflow and compliance overhead:** Artifice's `spec-egm` skill and `validate_egm.py` script enforce fixed numbered headings (`1. Overview & Objectives`, `3. State Schema`, `4. Invariants & Rules`, `7. Verification`) and a separate `docs/reviews/` verdict file. When the author uses upstream `egm` (`egm-brainstorm`, `egm-draft`, `egm-review`, `egm-review-loop`), Artifice's validator rejects upstream-formatted design documents unless they are rewritten into legacy numbered sections with a `docs/reviews/` verdict file. Similarly, `extract_spec_invariants` in `scripts/build_review_dossier.py` scrapes `## 4. Invariants & Rules`, which only matches legacy Artifice specs.
2.  **High Gemini token spend during multi-lens EGM reviews:** Upstream `egm` spawns `7` stateless (`Goldfish`) lenses during brainstorming (`skills/egm-brainstorm/SKILL.md:162-174`) and `10` Goldfish dispatches across a full five-stage review (`skills/egm-review/SKILL.md:315-426`). Running every stateless Goldfish reviewer through native Google Antigravity harness subagents (`invoke_subagent`) consumes Gemini quota, whereas routing the entire EGM workflow through `scripts/vibe_execute.py` breaks stateful (`Elephant`) phases that depend on multi-turn conversation memory and native interactive UI gates (`ask_question`).
3.  **Undocumented cross-harness expectations:** Artifice supports both Google Antigravity and GitHub Copilot, whereas upstream `egm` documents Antigravity installation (`~/.gemini/config/plugins/egm/`) but omits Copilot from `docs/harnesses.md`, while its experimental `docs/copilot.md` leaves `copilot plugin install` unverified (`lines 59–61`) and does not establish VS Code or cloud-agent support (`lines 6–7`). Leaving this implicit causes mid-workflow failures when `/egm-*` skills are invoked on unconfigured hosts.

The proposed solution deletes Artifice's internal EGM skill, validator, lint gate, and dossier regex scraper, and documents the upstream `egm` prerequisite and Antigravity-vs.-Copilot scope in `README.md`. It also shifts design-readiness accountability to PR/commit Stage 9 provenance audited during `/review`, and adds a reference guide under `skills/vibe-execute/` defining which stateless EGM phases offload to Mistral.

## Goals

*   **Eliminate duplicate EGM maintenance in Artifice:** Remove `skills/spec-egm/`, `scripts/validate_egm.py`, `lint.py` Gate 5, `extract_spec_invariants` in `scripts/build_review_dossier.py`, and all corresponding installer and unit-test checks so `0` lines of custom EGM validator or template code remain in `scripts/` and `skills/`, with `./scripts/lint.sh` and `unittest` returning exit code `0`.
*   **Preserve design readiness accountability via PR/commit provenance:** Require `code-author` to record upstream `egm-review` Stage 9 (Implementation Readiness Test) or human sign-off in early PR descriptions or commit trailers, verified by `code-reviewer` under Pillar 1 during `/review`.
*   **Document clear external prerequisite and harness boundaries:** Record the tested upstream `google/elephant-goldfish-model` baseline (`version 0.1.1`, commit `270b103`), manual verification steps, Antigravity installation command, and explicit Copilot support limitations in `README.md`, while preserving existing `docs/designs/001`–`004` and `docs/reviews/001`–`004` as legacy historical records.
*   **Achieve zero Gemini subagent dispatches on offloaded Goldfish reviews:** Provide an actionable routing and guardrail reference in `skills/vibe-execute/references/egm-offloading.md` (linked from `skills/vibe-execute/SKILL.md` within its 180-line / 1,000-word Core Diet ceiling) with a measurable target of `0` native Gemini `invoke_subagent` calls during offloaded stateless Goldfish passes while keeping stateful Elephant phases on Gemini.

## Non-Goals

*   **Automated plugin installation or host-state linting:** Artifice installers (`install_antigravity.sh`, `install_copilot.sh`) and `lint.py` will not clone, submodule, or probe `~/.gemini/config/plugins/egm/`.
*   **New in-repo design-document schema, marker linters, or GitHub Actions CI workflows:** Artifice will not replace `validate_egm.py` with a new file-header stamp, custom Markdown schema check in `lint.py`, or a new `.github/workflows/` CI gate.
*   **Offloading stateful Elephant phases to `vibe_execute.py`:** Interactive clarification (`egm-brainstorm` Step 1), section-by-section drafting (`egm-draft`), finding resolution (`egm-resolve`), and `egm-synthesizer` orchestration will not be routed through one-shot `vibe_execute.py` subprocesses.
*   **Modifying out-of-repo host files in this changeset:** Global user files outside the repository (such as `~/.gemini/config/AGENTS.md`) are not modified by repository commits and remain a manual host update.

## Open Questions

*   None.

## Critical User Journeys (CUJs)

### CUJ 1: Developer Sets Up Artifice and Verifies the Upstream EGM Prerequisite

*   **Given**: A developer clones or updates Artifice on an Antigravity or Copilot host and runs `./scripts/install_antigravity.sh` or `./scripts/install_copilot.sh`.
*   **When**: The installer runs preflight checks and the developer consults `README.md` for specification workflow prerequisites.
*   **Then**: The installer succeeds without checking for `skills/spec-egm/SKILL.md` or `scripts/validate_egm.py` (with `install_copilot.sh` printing a short non-probing reminder about manual Copilot setup), and `README.md` provides the tested `google/elephant-goldfish-model` baseline (`0.1.1` / `270b103`), the Antigravity install command, a manual check (`~/.gemini/config/plugins/egm/plugin.json` for `0.1.1` and `git -C ~/.gemini/config/plugins/egm rev-parse HEAD` for commit `270b103`), and explicit Copilot limitations.

### CUJ 2: Author Runs `/egm-review /vibe-execute` to Offload Goldfish Reviews to Mistral

*   **Given**: A developer has drafted a design document with `/egm-draft` on Gemini and invokes an EGM review or brainstorm step alongside `/vibe-execute` in a repository without `--local` privacy restrictions.
*   **When**: The orchestrator loads `skills/vibe-execute/SKILL.md` and follows the link to `skills/vibe-execute/references/egm-offloading.md`.
*   **Then**: After proposing and confirming the exact Mistral model and identity fingerprint via `ask_question`, the orchestrator keeps stateful Elephant gates on Gemini, bypasses `egm-synthesizer`, and dispatches the stateless Goldfish lenses directly in parallel via `scripts/vibe_execute.py run` (`--workdir` included) with bounded timeouts and `not run` failure accounting.

### CUJ 3: Craftsman Implements an Approved Design and Gatekeeper Audits Provenance

*   **Given**: A design document has completed upstream `egm-review` Stage 9 (Implementation Readiness Test) and received human sign-off.
*   **When**: `code-author` begins contract-first Test-Driven Development (TDD), opens an early PR, runs `./scripts/lint.sh`, and hands off to `code-reviewer` (`/review`).
*   **Then**: `code-author` ingests invariants from the approved design document without calling `validate_egm.py`, records the design document path and Stage 9 sign-off in the PR description or commit trailers (`Design-Review:`), `./scripts/lint.sh` passes without running Gate 5 against `docs/designs/`, and `code-reviewer` verifies the Stage 9 provenance under Pillar 1.

## Technical Plan (Architecture)

The architecture replaces Artifice's internal EGM subsystem with three decoupled mechanisms: (1) removal of duplicate EGM files and static-analysis hooks, (2) a Git/PR provenance contract linking `code-author` and `code-reviewer` to upstream `egm-review` Stage 9, and (3) a stateless flat-swarm offloading bridge in `skills/vibe-execute/`.

### Terminology & Harness Primitives

*   **Elephant & Goldfish**: The two EGM execution roles: the **Elephant** is the stateful primary orchestrator retaining multi-turn conversation memory; a **Goldfish** is an isolated, zero-context reviewer agent run in a fresh context window with no conversation history.
*   **`scripts/vibe_execute.py` (`/vibe-execute`)**: Artifice's existing CLI gateway script and skill for discovering, fingerprint-verifying, and dispatching bounded prompts to external hosted Mistral Vibe or local Ollama models in fresh one-shot subprocesses.
*   **`ask_question` & `invoke_subagent`**: Google Antigravity primary-harness tools: `ask_question` renders interactive single-select or multi-select UI gates for user confirmation, and `invoke_subagent` spawns native child subagent conversations on Gemini.
*   **`egm-synthesizer`**: Upstream `egm`'s intermediate subagent coordinator (`agents/synthesizer.md`) that fans out review lenses via `invoke_subagent`; bypassed under `/vibe-execute` offloading so Mistral calls do not incur wrapper Gemini subagent turns.
*   **`GoldfishContext`**: The curated bundle of repository baseline files (with explicit `1`-based line ranges) passed alongside the numbered target design document in each stateless Goldfish prompt (except Stage 6, which inspects self-containment without baseline files).
*   **`/review` & `Core Diet`**: `/review` is Artifice's universal 8-Pillar code and architectural review skill (`skills/review/SKILL.md`), executed by `code-reviewer`. `Core Diet` is Artifice's anti-bloat governance policy enforced by `scripts/lint.py` (`SKILL_LINE_LIMIT = 180`, `SKILL_WORD_LIMIT = 1000`, `AGENT_WORD_LIMIT = 900`).
*   **`agy` & `omp` (`oh-my-pi`)**: `agy` is the Google Antigravity CLI binary (`agy plugin install ...`); `omp` (`oh-my-pi`) is an external open-source multi-model coding agent harness tracked for future evaluation in [Issue #28](https://github.com/efsalvarenga/artifice/issues/28).
*   **Upstream `egm` Workflows (`v0.1.1`, commit `270b103`)**:
    *   `egm-brainstorm`: Interactive concept clarification (`Step 1`), followed by a `7`-lens parallel Goldfish brainstorm (`Step 2`: `egm-design`, `egm-codebase-details`, `egm-zoom-out`, `egm-comprehension`, `egm-implementation-readiness`, `egm-structural`, `egm-inventive-catalyst`; `skills/egm-brainstorm/SKILL.md:162-174`), brief synthesis (`Step 3`), and handoff (`Step 4`).
    *   `egm-draft`: Interactive section-by-section drafting workflow that creates design specifications split cleanly between architectural sections and a `## Detailed Implementation Plan`.
    *   `egm-review` & **Stage 9 (`Implementation Readiness Test`)**: A 9-stage specification review workflow (`skills/egm-review/SKILL.md:1-10, 82-224, 315-426`) whose consolidated output artefact is `consolidated_review_report.md` (with a `Reviewer Status` table tracking `completed` vs. `not run` lenses). **Stages 1–4** handle interactive intake, pipeline preset selection, semantic boundary split (`FeatureRange` vs. `DetailedRange`), and staging strategy. **Stages 5–9** execute five Goldfish review phases (`10` Goldfish worker dispatches across a full pass): Stage 5 Initial Zoom Out (`egm-zoom-out`, `egm-inventive-catalyst`), Stage 6 Comprehension Test (`egm-comprehension`), Stage 7 Critic Review (`egm-design`, `egm-structural`, `egm-style`), Stage 8 Intermediate Zoom Out (`egm-zoom-out`), and **Stage 9 Implementation Readiness Test** (`egm-implementation-readiness`, `egm-codebase-details`, `egm-style` auditing `DetailedRange` against `resources/document_standards/implementation-readiness-standard.md` for Zero-Decision readiness — leaving no design or file-target choices to the implementer — with phased executability and verified repository symbol accuracy).
    *   `egm-review-loop`, `egm-resolve`, `egm-drift-report`, `egm-bootstrap`: Supporting `egm` skills that iterate review/resolve rounds (up to 5), negotiate finding fixes interactively (`egm-resolve`), audit spec-vs.-code drift (`egm-drift-report`), and generate directory documentation via leaf workers (`egm-bootstrap`).

### 1. Subsystem Removal and Governance Cleanup

Artifice's internal EGM files (`skills/spec-egm/` and `scripts/validate_egm.py`) are deleted. Four repository consumers that previously referenced them are updated:

*   **Static Linter (`scripts/lint.py`)**: Gate 5 (`Validating EGM Specification Contracts`) is removed so `lint.py` no longer imports or executes `validate_egm` when `docs/designs/` is present. Gate 6 (`Checking Native Bash Syntax`) is renumbered to Gate 5. Core Diet ceilings and Markdown heading/link validation remain unchanged.
*   **Review Dossier (`scripts/build_review_dossier.py`)**: `extract_spec_invariants` (which regex-matched `## 4. Invariants & Rules` in `docs/designs/*.md`) is removed so `build_dossier` compiles repository-level invariants from `AGENTS.md` when present (or falls back to its built-in rules block at `lines 15–26` / `lines 110–130` when absent) without assuming legacy section headers.
*   **Symlink Installers (`scripts/install_antigravity.sh` and `scripts/install_copilot.sh`)**: Preflight file-existence loops drop `skills/spec-egm/SKILL.md` and `scripts/validate_egm.py`; `install_copilot.sh` adds a short non-probing informational notice referencing `README.md`.
*   **Unit Test Suite (`tests/test_artifice.py`)**: Removes `import validate_egm`, drops `"spec-egm"` from the canonical word-budget list, and deletes `PathTraversalTests` (which tested `validate_egm.sanitise_spec_path` and `validate_egm.validate_repo`).

### 2. Stage 9 Provenance Handoff Contract (`code-author` to `code-reviewer`)

Instead of gating TDD on an in-repo Python validator script, readiness is tracked through Git and Pull Request provenance:

*   **Pre-TDD Intake & Applicability Scope (`agents/code-author/agent.md`)**: Before writing Phase 1 (Red) tests for a design-backed feature, `code-author` confirms that the target design document has cleared upstream `egm-review` Stage 9 (Implementation Readiness Test) or received explicit human sign-off. Phase 1 ingests invariants and verification criteria directly from the approved design document (`Goals`, `Non-Functional Requirements`, `Risks & Mitigations`, and `Detailed Implementation Plan`) rather than hardcoded `Section 4` and `Section 7` numbers. Trivial documentation updates, chores, or hotfixes with no `docs/designs/` specification are exempt from Stage 9 provenance.
*   **Early PR & Trailer Provenance**: On design-backed changesets, `code-author` records the approved design document path and Stage 9 sign-off status in the PR description (encouraging early draft PR creation) or via a structured commit provenance trailer (`Design-Review: docs/designs/<NNN>_<slug>.md (Stage 9 completed)`).
*   **Gatekeeper Verification (`skills/review/references/review-framework.md`)**: When `/review` runs on a design-backed PR or branch, Pillar 1 (`Design & Architecture Alignment`) checks implementation alignment against the approved design document and confirms Stage 9 or human readiness provenance. Because Artifice relies intentionally on human-gated PR review without `.github/workflows/`, unreviewed direct commits bypass advisory Pillar 1 auditing unless `/review` is invoked explicitly (accepted trade-off documented in `## Risks & Mitigations`).

### 3. Elephant / Goldfish Split Offloading Architecture (`vibe-execute`)

When a developer pairs an upstream `/egm-*` skill with `/vibe-execute`, execution splits along EGM's memory boundary:

```text
+-------------------------------------------------------------------+
| Primary Harness Orchestrator (Gemini — "The Elephant")            |
|  - Stateful multi-turn memory & file editing                      |
|  - Native ask_question single-select UI gates                     |
|  - Runs: egm-brainstorm (Steps 1, 3, 4), egm-draft (Steps 1-6),   |
|          egm-resolve, egm-review Stages 1-4,                      |
|          egm-review-loop (Steps 2.1, 2.3, 2.4)                    |
+-------------------------------------------------------------------+
          |
          | 1. Discover & confirm exact Mistral model + fingerprint
          |    via ask_question (unless --local / privacy policy)
          | 2. Bypass egm-synthesizer & native invoke_subagent
          | 3. Inject upstream persona, document standard, &
          |    [EXCERPT]-marked GoldfishContext within argv envelope
          v
+-------------------------------------------------------------------+
| Parallel Stateless Workers via scripts/vibe_execute.py run        |
|  - Fresh zero-context CLI process per lens (Mistral, --workdir)   |
|  - Runs: egm-brainstorm Step 2 (7 lenses),                        |
|          egm-review Stages 5-9 (10 dispatches) /                  |
|          egm-review-loop Step 2.2 (max 5 rounds),                 |
|          egm-drift-report, egm-bootstrap leaf workers             |
|  - Guardrails: bounded per-lens timeout, single retry, and        |
|    mandatory "not run" failure accounting (never zero findings)   |
+-------------------------------------------------------------------+
```

To remain within `skills/vibe-execute/SKILL.md`'s 1,000-word Core Diet ceiling enforced by `scripts/lint.py`, `SKILL.md` adds only a reference link and a short pointer in Section 4, while the full routing table, prompt-assembly contract, and operational guardrails live in `skills/vibe-execute/references/egm-offloading.md`.

## Alternatives Considered

### Alternative A: Keep a Thin Validator, File Marker, or Automated Plugin Probe in `lint.py` / Installers

*   **Pros**: Provides an automated CI or install-time signal verifying that the upstream `egm` plugin is present on the host or that new `docs/designs/` documents carry an explicit readiness stamp.
*   **Cons**: Couples repository scripts (`lint.py`, `install_antigravity.sh`, `install_copilot.sh`) to out-of-repo `~/.gemini` host state, leaves Copilot without parity (since upstream `egm` omits Copilot from `docs/harnesses.md` and leaves `copilot plugin install` unverified in `docs/copilot.md`), and risks rubber-stamped header markers replacing substantive review.
*   **Reason for Rejection**: Rejected: keeping host-coupled probes or custom file-header stamps recreates the maintenance and compliance overhead described in `## The Problem`; Git/PR Stage 9 provenance audited during `/review` preserves accountability without custom linters.

### Alternative B: Broaden or Retain `extract_spec_invariants` in `scripts/build_review_dossier.py`

*   **Pros**: Continues surfacing design-document bullets inside the compact review dossier compiled for `/review` without manual linking.
*   **Cons**: Couples `build_review_dossier.py` to upstream `egm` template headings (`## Goals`, `## Non-Functional Requirements`) that Artifice does not control, or leaves a legacy `## 4. Invariants & Rules` regex that only matches legacy specs while ignoring upstream-formatted documents.
*   **Reason for Rejection**: Rejected: removing `extract_spec_invariants` keeps `build_review_dossier.py` focused on repository `AGENTS.md` governance invariants without scraping external plugin section layouts.

### Alternative C: Run the Full EGM Workflow on Mistral or Wrap `vibe_execute.py` Inside `invoke_subagent`

*   **Pros**: Could keep native `egm-synthesizer` orchestration intact (if wrapped in `invoke_subagent`) or attempt to offload all EGM turns off Gemini.
*   **Cons**: One-shot `vibe_execute.py run` invocations lack multi-turn Elephant conversation memory and cannot render Antigravity's native `ask_question` UI gates (`egm-brainstorm` Step 1, `egm-draft`, `egm-resolve`). Wrapping `vibe_execute.py` inside `invoke_subagent` spends Gemini tokens on every wrapper subagent turn in addition to Mistral worker tokens, even though `vibe_execute.py` already runs in a fresh zero-context process.
*   **Reason for Rejection**: Rejected: direct parallel `vibe_execute.py run` calls for stateless Goldfish reviewers combined with Gemini for stateful Elephant turns achieves cross-model isolation without wrapper token waste or broken UI gates.

### Alternative D: Place EGM Offloading Guidance Only in `README.md` or Inline in `skills/vibe-execute/SKILL.md`

*   **Pros**: Keeping the note only in `README.md` leaves `skills/vibe-execute/SKILL.md` completely agnostic of external plugins; writing a principle-only paragraph directly inside `SKILL.md` avoids adding a new file under `skills/vibe-execute/references/`.
*   **Cons**: Agents invoked with `/egm-review /vibe-execute` in downstream repositories load `skills/vibe-execute/SKILL.md`, not Artifice's `README.md`, so `README.md`-only guidance is missed at runtime. Conversely, placing a complete routing table and guardrail specification inside `SKILL.md` crowds its 1,000-word Core Diet ceiling (`scripts/lint.py`).
*   **Reason for Rejection**: Rejected: linking from a short pointer in `skills/vibe-execute/SKILL.md` to `skills/vibe-execute/references/egm-offloading.md` ensures the guidance is loaded at runtime while keeping `SKILL.md` under `lint.py`'s word limit.

## Non-Functional Requirements

### Security and Privacy

*   **Remote Execution Boundary (`--workdir` & `--local`):** Hosted Mistral dispatch via `scripts/vibe_execute.py` sends prompt payloads (target document, inline persona/standard prompts, and `GoldfishContext` excerpts) to Mistral's hosted service. Per `scripts/vibe_execute.py` (`lines 128–139`), `_prepare()` evaluates `model_inventory.local_policy(local_only, workdir)` whenever `--workdir` or `--local` is supplied and rejects hosted dispatch (`SelectionError`) if local-only policy applies; additionally, `_dispatch_vibe` (`lines 242–243`) returns exit code `2` when `local_only` is set. Therefore `egm-offloading.md` mandates passing `--workdir "<REPO_ROOT>"` on every `vibe_execute.py run` invocation, and the orchestrator must halt to prevent protected material leaving the device whenever `--local` or repository local-only privacy directives apply.
*   **Deleted Path-Traversal Surface:** Deleting `scripts/validate_egm.py` removes `sanitise_spec_path` and its `PathTraversalTests` alongside the script, eliminating that CLI argument surface.

### Performance, Latency, and Quota Economics

*   **Bounded Parallelism & Zero Native Subagent Spend:** Stateless Goldfish flat-swarm calls run concurrently up to the lens count per pass (`7` lenses in `egm-brainstorm` Step 2 per `skills/egm-brainstorm/SKILL.md:162-174`; `10` dispatches across `egm-review` Stages 5–9 per `skills/egm-review/SKILL.md:315-426`; `egm-review-loop` capped at 5 rounds), targeting `0` native Gemini `invoke_subagent` calls for offloaded lenses.
*   **Explicit Timeouts & Failure Accounting:** Each `scripts/vibe_execute.py run` invocation requires an explicit `--timeout` budget (script default `120.0` seconds at `scripts/vibe_execute.py:543`, raised per workflow need). Per `scripts/vibe_execute.py` (`lines 290–297`), timeout raises `subprocess.TimeoutExpired` and returns exit code `124` with empty `stdout`; timed-out or non-zero workers may be retried at most once and must be recorded as `not run` (never as zero findings). Any review pass containing one or more `not run` lenses must be flagged as partial in `consolidated_review_report.md`'s `Reviewer Status` table and cannot be recorded as a completed Stage 9 sign-off until the failed lens is re-run or explicitly waived by the human author in the report and PR description.
*   **Core Diet Compliance:** Edits to `skills/vibe-execute/SKILL.md`, `agents/code-author/agent.md`, and `skills/review/references/review-framework.md` must stay within `scripts/lint.py` ceilings (`180` lines / `1,000` words for skills, `900` words for agents, and the canonical word budget in `tests/test_artifice.py`).

### Rollout and Rollback

*   **Legacy Artefacts:** Existing `docs/designs/001`–`004` and `docs/reviews/001`–`004` remain untouched in-repo as historical records; removing Gate 5 from `scripts/lint.py` ensures they continue to pass linting without modification.
*   **Rollback:** Restoring the deleted files, lint gate, and tests is a single `git revert` of the implementation commit(s).

### Future Improvements

*   **`omp` (`oh-my-pi`) Headless Evaluation ([Issue #28](https://github.com/efsalvarenga/artifice/issues/28)):** Evaluating native `egm` plugin execution inside the external `omp` coding harness is deferred to a separate future PR once `omp` installation and its fallback-chain / Thin-Orchestrator policy boundaries with `vibe-execute` are resolved.

## Risks & Mitigations

| Risk / Failure Mode | Impact | Mitigation |
|---|---|---|
| **Missing or rubber-stamped Stage 9 provenance (or bypassed `/review`)** | Design-backed implementation merges without verified Stage 9 readiness. | Mandatory `Design-Review:` trailer or PR summary in `code-author`, verified by `code-reviewer` under Pillar 1. Consistent with Non-Goal 2 (no new `.github/workflows/` CI gates or schema linters), Artifice intentionally accepts advisory Pillar 1 + human PR review for design-backed PRs. |
| **Stateful Elephant phase misrouted to `vibe_execute.py`** | Multi-turn context lost; interactive `ask_question` UI gates fail inside one-shot CLI subprocesses. | Memory-boundary Routing Split Table in `egm-offloading.md` restricts `vibe_execute.py` strictly to stateless Goldfish passes while keeping clarification, drafting, synthesis, and resolution on Gemini. |
| **Timed-out or failed Goldfish lens treated as `0` findings** | Partial review is silently recorded as a clean Stage 9 pass. | Single-retry cap, mandatory `not run` accounting on exit code `124` or empty output, and explicit partial-pass blocking rule requiring re-run or human waiver recorded in the report and PR description before sign-off. |
| **Hosted Mistral dispatch on privacy-restricted repo** | Protected source code sent to external hosted APIs. | Mandatory `--workdir "<REPO_ROOT>"` triggers `model_inventory.local_policy` inside `_prepare()` (`scripts/vibe_execute.py:128-139`), backed by orchestrator pre-flight halting whenever `--local` or repository local-only privacy directives apply. |
| **Unconfigured GitHub Copilot host invokes `/egm-*`** | Mid-workflow failure when upstream `egm` plugin is not installed on Copilot hosts. | Explicit Antigravity-vs.-Copilot support matrix and manual `~/.gemini/config/plugins/egm/plugin.json` verification check documented in `README.md`, plus a non-probing informational notice printed during `scripts/install_copilot.sh`. |
| **`GoldfishContext` excerpt truncation or Linux `MAX_ARG_STRLEN` overflow** | Unmarked excerpt truncation produces false findings, or a single CLI prompt argument exceeding `131,072` bytes fails with `OSError: [Errno 7]`. | Prompt builder labels partial files with explicit `1`-based `[EXCERPT: lines X-Y of Z]` markers and enforces a `< 120,000`-byte UTF-8 per-argument envelope check prior to `vibe_execute.py run`. |

## Detailed Implementation Plan

### Incremental Execution Phases & Stability Checkpoints

Apply the 14 target file edits in three ordered phases:

1.  **Phase 1: Detach Callers, Installers, Dossier Scraper, and Unit Tests (Items 5, 6, 7, 8, 14)**
    *   Update `scripts/lint.py`, `scripts/build_review_dossier.py`, `scripts/install_antigravity.sh`, `scripts/install_copilot.sh`, and `tests/test_artifice.py` so nothing imports `validate_egm` or references `skills/spec-egm/`.
    *   *Checkpoint:* Run `python3 -m unittest discover -s tests -v` and confirm all unit tests pass before deleting internal EGM files.
2.  **Phase 2: Remove Retired Internal EGM Files (Items 1, 2, 3, 4)**
    *   Delete `skills/spec-egm/SKILL.md`, `skills/spec-egm/references/design-spec-template.md`, `skills/spec-egm/references/goldfish-review-template.md`, and `scripts/validate_egm.py`.
    *   *Checkpoint:* Run `./scripts/lint.sh`, `bash scripts/install_antigravity.sh --check`, `bash scripts/install_copilot.sh --check`, and `python3 -m unittest discover -s tests -v`.
3.  **Phase 3: Author Offloading Reference, Provenance Rules, and Documentation (Items 9, 10, 11, 12, 13)**
    *   Create `skills/vibe-execute/references/egm-offloading.md` and update `agents/code-author/agent.md`, `skills/review/references/review-framework.md`, `skills/vibe-execute/SKILL.md`, and `README.md`.
    *   *Checkpoint:* Run the full Verification Plan below (`./scripts/lint.sh`, `unittest`, installer smoke checks, `build_review_dossier.py .`, and residual reference `grep`).

### Target Files to Create, Modify, or Delete

#### 1. `skills/spec-egm/SKILL.md` (`[Delete]`)

*   **Type / Scope**: Skill definition
*   **Proposed Changes**: Delete the custom Artifice EGM specification skill. Upstream `google/elephant-goldfish-model` replaces this workflow.

#### 2. `skills/spec-egm/references/design-spec-template.md` (`[Delete]`)

*   **Type / Scope**: Skill template reference
*   **Proposed Changes**: Delete Artifice's legacy fixed-section design template (`1. Overview & Objectives`, `3. State Schema`, `4. Invariants & Rules`, `7. Verification`), which is superseded by upstream `egm-draft/references/design_doc.md`.

#### 3. `skills/spec-egm/references/goldfish-review-template.md` (`[Delete]`)

*   **Type / Scope**: Skill template reference
*   **Proposed Changes**: Delete Artifice's legacy single-file Goldfish review template (`docs/reviews/<NNN>_*_review.md`), which is superseded by upstream `egm-review` and `egm-review-loop`.

#### 4. `scripts/validate_egm.py` (`[Delete]`)

*   **Type / Scope**: Python validation script
*   **Proposed Changes**: Delete `scripts/validate_egm.py` (`lines 1–222`), the section-header and `Verdict: Approved` validator script. Readiness enforcement shifts to upstream `egm-review` Stage 9 and PR/commit provenance.

#### 5. `scripts/lint.py` (`[Modify]`)

*   **Type / Scope**: Static governance linter
*   **Proposed Changes**: Remove Gate 5 (`Validating EGM Specification Contracts` block importing `validate_egm` at `lines 388–405` when `docs/designs` exists) and renumber Gate 6 (`Checking Native Bash Syntax`, `line 407`) to Gate 5. Leave the module docstring (`lines 2–7`, after shebang `line 1`) unchanged, as it does not reference EGM. Preserve Core Diet limits, Markdown heading blank-line checks, relative-link checks, and Copilot adapter checks unchanged.

#### 6. `scripts/build_review_dossier.py` (`[Modify]`)

*   **Type / Scope**: Invariant dossier compiler
*   **Proposed Changes**: Remove `extract_spec_invariants` (`lines 70–95`) and its call/output loop in `build_dossier` (`lines 102, 138–139`) so the dossier no longer regex-scrapes `## 4. Invariants & Rules` from `docs/designs/*.md`. Keep `find_repo_agents_md` (plus built-in rules fallback when `AGENTS.md` is absent), `extract_invariants`, CLI flags (`repo_root`, `--files`), and the `dossier_lines[:38]` (`<= 40 lines`) cap (`lines 141–142`) intact.

#### 7. `scripts/install_antigravity.sh` (`[Modify]`)

*   **Type / Scope**: Symlink installer
*   **Proposed Changes**: Remove `spec-egm` from the `skills/{...}/SKILL.md` preflight list (`line 62`) and `validate_egm` from the `scripts/{...}.py` preflight list (`line 63`) so preflight checks pass without deleted EGM files. Keep anchor, symlink, `skills.json`, and `--check` logic unchanged.

#### 8. `scripts/install_copilot.sh` (`[Modify]`)

*   **Type / Scope**: Symlink installer
*   **Proposed Changes**: Remove `spec-egm` from `lines 56` and `validate_egm` from `line 57` in the preflight loop so Copilot symlink installation and `--check` succeed without deleted EGM files. Print a short non-probing informational notice (`"Note: upstream egm plugin setup is manual on Copilot hosts; see README.md."`) before exit `0` on `--check` and install paths (`lines 84–93`).

#### 9. `agents/code-author/agent.md` (`[Modify]`)

*   **Type / Scope**: Canonical agent instructions
*   **Proposed Changes**: Keep total word count below `AGENT_WORD_LIMIT = 900`:
    *   **Section 2 (`Invariant & Contract Ingestion`, lines 30–36):** Replace the `spec-egm` link and `1. **Verify Target EGM Contract:** validate_egm.py . --spec <NNN>` block with: `Before production code or tests for a design-backed feature, confirm that the target design document (docs/designs/<NNN>_<slug>.md) has completed upstream egm-review Stage 9 (Implementation Readiness Test) or received explicit human sign-off (trivial docs, chores, and hotfixes without a design doc are exempt), then ingest repository invariants:` while keeping the `build_review_dossier.py` command (`lines 37–40`).
    *   **Phase 1 (`Red (Contract Tests)`, line 48):** Replace `"Ingest invariant assertions from Section 4 and Section 7 of the approved specification."` with `"Ingest invariant assertions and verification criteria from the approved design document (Goals, Non-Functional Requirements, Risks & Mitigations, and Detailed Implementation Plan)."`
    *   **Section 4 (`Model Commit Authorship & Provenance`, heading line 84; item 3 `Mandatory Provenance Trailers`, lines 95–102):** Add the optional/design-backed provenance trailer `Design-Review: docs/designs/<NNN>_<slug>.md (Stage 9 completed)` (or equivalent PR description entry, encouraging early draft PR creation) alongside `Model-Author:`, `Agent-Role:`, and `Co-authored-by:`.

#### 10. `skills/review/references/review-framework.md` (`[Modify]`)

*   **Type / Scope**: Review rubric reference
*   **Proposed Changes**: In `### Pillar 1: Design & Architecture Alignment (\`DESIGN\`)` (`lines 7–18`), replace the single bullet on `line 10` (`* **EGM Specification Compliance:** Does the implementation faithfully fulfil the active approved specification in \`docs/designs/\`?`) with two bullets under `* **What to Check:**`:
    *   `* **Design Specification Alignment:** Does the implementation faithfully fulfil the active approved specification in \`docs/designs/\` (or linked PR design doc)?`
    *   `* **Stage 9 Readiness Provenance:** For changesets backed by a \`docs/designs/\` specification, does the PR description or \`Design-Review:\` commit provenance record upstream \`egm-review\` Stage 9 (Implementation Readiness Test) completion or explicit human sign-off?`
    Also append `* Missing Stage 9 or human readiness provenance on a design-backed PR.` under `* **Blocking Triggers:**` (`lines 14–18`).

#### 11. `skills/vibe-execute/SKILL.md` (`[Modify]`)

*   **Type / Scope**: Skill definition
*   **Proposed Changes**: Under `## Reference Materials` (`lines 14–18`), append `* [EGM Goldfish offloading](references/egm-offloading.md)`. At the end of Section 4 (`## 4. Compound Execution & Triage`, appending after `line 82`), add a final item: `3. **Upstream EGM Offloading:** When pairing /egm-* skills with /vibe-execute, keep stateful Elephant turns (clarification, drafting, resolution) on the primary harness and fan out stateless Goldfish lenses in parallel via scripts/vibe_execute.py run per [EGM Goldfish offloading](references/egm-offloading.md).` Ensure total size remains below `SKILL_LINE_LIMIT = 180` and `SKILL_WORD_LIMIT = 1000`.

#### 12. `skills/vibe-execute/references/egm-offloading.md` (`[Create]`)

*   **Type / Scope**: Skill reference guide
*   **Proposed Changes**: Author the operational contract using this exact structure and content specification:
    *   **Baseline Pin & Drift Check:** State pinned upstream baseline `google/elephant-goldfish-model` `version 0.1.1` (commit `270b103`). Before dispatching step-numbered workflows, instruct the orchestrator to check `~/.gemini/config/plugins/egm/plugin.json` (`version: 0.1.1`) and `git -C ~/.gemini/config/plugins/egm rev-parse HEAD` (`270b103...`) against the pinned baseline and flag any upstream drift (or run `egm-drift-report` if stale).
    *   **Routing Split Table:**

        | Workflow / Step | Memory Role | Execution Engine | Notes |
        |---|---|---|---|
        | `egm-brainstorm` Steps 1, 3, 4 (intake, synthesis, handoff) | Elephant (stateful) | Gemini (Primary Harness) | Uses multi-turn memory and `ask_question` UI gates; misrouting loses context. |
        | `egm-brainstorm` Step 2 (`7` review/ideation lenses) | Goldfish (stateless) | Mistral via `vibe_execute.py run` | Concurrent one-shot subprocesses; return structured Markdown findings. |
        | `egm-draft` Steps 1–6 (section drafting & file edits) | Elephant (stateful) | Gemini (Primary Harness) | Interactive section sign-off and workspace file editing. |
        | `egm-review` Stages 1–4 (intake, split, preset, staging) | Elephant (stateful) | Gemini (Primary Harness) | Owns target splitting, `ask_question` gates, and final cross-stage synthesis. |
        | `egm-review` Stages 5–9 (`10` dispatches) & `egm-review-loop` Step 2.2 | Goldfish (stateless) | Mistral via `vibe_execute.py run` | Concurrent flat-swarm workers with inline persona, standard, target, and `GoldfishContext`. |
        | `egm-resolve` & `egm-review-loop` Steps 2.1, 2.3, 2.4 (resolution & convergence) | Elephant (stateful) | Gemini (Primary Harness) | Interactive negotiation, document edits, and target resolution and convergence checks. |
        | `egm-drift-report` & `egm-bootstrap` leaf file workers | Goldfish (stateless) | Mistral via `vibe_execute.py run` | Read-only file/sub-tree inspection; leaf reports aggregated by Elephant. |

    *   **Direct-Dispatch Rules:** (1) Always pass `--mode bounded_chat --require-capability chat --workdir "<REPO_ROOT>" --json` to `scripts/vibe_execute.py run` so `model_inventory.local_policy` evaluates repository privacy directives automatically. (2) Bypass `egm-synthesizer` and never wrap `vibe_execute.py` inside `invoke_subagent`. (3) Inject upstream persona (`agents/*.md`), target standard (`resources/document_standards/{zoom-out-standard,feature-spec-standard,implementation-readiness-standard}.md`), `1`-based numbered target file lines, and `GoldfishContext` baseline files inline into the worker prompt. (4) Label any excerpted baseline file explicitly (`[EXCERPT: lines X-Y of Z]`). (5) Assert the assembled prompt UTF-8 byte length is `< 120,000` bytes before `subprocess.run` to stay within Linux's `128 KiB` `MAX_ARG_STRLEN` per-argument limit.
    *   **Operational Guardrails:** (1) Discover and confirm exact `--model` + `--expect-identity` via `ask_question` before the first dispatch. (2) Enforce an explicit `--timeout` budget (e.g. `--timeout 180`; script default is `120.0`s at `scripts/vibe_execute.py:543`, raising exit code `124` with empty `stdout` per `lines 290–297`). (3) Retry a timed-out or failed lens at most once before recording it as `not run` (never zero findings). (4) Any pass containing one or more `not run` lenses must be flagged as partial in `Reviewer Status` and blocked from Stage 9 sign-off until retried or explicitly waived by the user in the review report and PR description; bound `egm-review-loop` to 5 rounds. (5) Immediately halt hosted Mistral dispatch whenever `--local` or repository privacy directives (`Privacy: on-device`, `Review: local-only`) apply.

#### 13. `README.md` (`[Modify]`)

*   **Type / Scope**: Repository documentation
*   **Proposed Changes**:
    *   Remove `validate_egm.py` (`line 29`), `spec-egm/` (`line 32`), `### 1. spec-egm` (`lines 67–70`, renumbering `review`, `coach-frameworks`, `local-code`, `vibe-execute` to `1–4`), and `validate_egm.py` (`line 97`), and remove `"EGM contracts,"` from the `lint.sh` summary (`line 96`).
    *   In `## Directory Structure` (`lines 19–20`, under `├── docs/` at `line 18`), update the `docs/designs/` and `docs/reviews/` comments to note that `001`–`004` are legacy historical records preserved from the retired internal EGM format.
    *   Immediately after `## Core Scripts & Verification` (heading at `line 92`, section spanning `lines 92–99` before `## Discovery & Model Approval` at `line 100`), insert `## External Prerequisites (Upstream EGM)` containing: the upstream repository URL (`https://github.com/google/elephant-goldfish-model`), tested baseline (`version 0.1.1`, commit `270b103`), the Antigravity CLI (`agy`) install command (`agy plugin install https://github.com/google/elephant-goldfish-model`), the manual host verification steps (`~/.gemini/config/plugins/egm/plugin.json` reports `0.1.1`, `git -C ~/.gemini/config/plugins/egm rev-parse HEAD` matches `270b103...`, and `/egm-review` loads), and explicit Copilot scope noting upstream `egm`'s `docs/harnesses.md` omits Copilot while `docs/copilot.md` leaves `copilot plugin install` unverified (`lines 59–61`) and does not establish VS Code or cloud-agent support (`lines 6–7`).

#### 14. `tests/test_artifice.py` (`[Modify]`)

*   **Type / Scope**: Unit and integration tests
*   **Proposed Changes**:
    *   Remove `import validate_egm` (`line 25`), remove `"spec-egm"` from the `canonical` skill tuple in `test_live_repository_and_canonical_word_budget` (`line 469`), and remove `PathTraversalTests` (`lines 510–548`).
    *   Add `test_lint_allows_upstream_egm_design_doc_without_legacy_sections` (verifying `lint.lint_repository` returns `0` when a temporary repo's `docs/designs/001_sample.md` uses upstream headings and has no `docs/reviews/` verdict file) and `test_build_review_dossier_omits_spec_invariant_scraper` (verifying `build_review_dossier.build_dossier` compiles `AGENTS.md` invariants without reading `docs/designs/` or defining `extract_spec_invariants`).
    *   Confirm `lint.lint_repository` in `test_live_repository_and_canonical_word_budget` verifies `skills/vibe-execute/SKILL.md` link validity (`references/egm-offloading.md`) and word/line budgets.

### Verification Plan

*   **Static Analysis & Linting**: Run `./scripts/lint.sh` and confirm exit code `0` (verifying Markdown heading blank-line cleanliness, relative links including `skills/vibe-execute/references/egm-offloading.md`, YAML frontmatter, Core Diet word/line ceilings on `skills/vibe-execute/SKILL.md` and `agents/code-author/agent.md`, and Bash syntax on installers).
*   **Unit & Integration Tests**: Run `python3 -m unittest discover -s tests -v` and confirm all tests pass without `validate_egm` or `spec-egm` dependencies, including `test_lint_allows_upstream_egm_design_doc_without_legacy_sections` and `test_build_review_dossier_omits_spec_invariant_scraper`.
*   **Installer & Script Smoke Checks**: Run `bash scripts/install_antigravity.sh --check`, `bash scripts/install_copilot.sh --check`, and `python3 scripts/build_review_dossier.py .` to confirm clean execution.
*   **Residual Reference Check**: Run `grep -rnE "validate_egm|spec-egm" scripts/ skills/ agents/ integrations/ tests/ README.md` and confirm exit code `1` (zero stale references outside historical `docs/designs/001`–`004` and `docs/reviews/001`–`004`).

*Drafted with EGM*
