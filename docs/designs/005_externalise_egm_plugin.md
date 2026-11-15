# Externalise EGM to Upstream Plugin and Document Mistral Goldfish Offloading

*   **Author:** efsalvarenga
*   **Status:** Proposed
*   **Date:** 2026-11-15

--------------------------------------------------------------------------------

## Overview

Artifice currently ships its own custom Elephant-Goldfish Model (EGM) specification skill, templates, and mechanical section-header validator alongside its core agents and model-dispatch tools. Now that the official upstream `google/elephant-goldfish-model` (`egm`) plugin is used directly for ideation, drafting, and multi-lens review, Artifice's internal EGM copy duplicates upstream capabilities while imposing rigid section-number checks that do not improve design quality.

This design removes Artifice's built-in EGM implementation and establishes the upstream `egm` plugin as a documented external prerequisite. It replaces mechanical section-header validation with early Pull Request and commit provenance referencing upstream `egm-review` Stage 9 (Implementation Readiness Test) sign-off, removes the legacy `docs/designs/` regex scraper from `scripts/build_review_dossier.py`, and documents how to pair upstream `egm` with `/vibe-execute` so stateless Goldfish review passes run on hosted Mistral models instead of consuming Gemini quota.

## The Problem

Maintaining a bespoke EGM implementation inside Artifice creates three practical problems:

1.  **Duplicate workflow and compliance overhead:** Artifice's `spec-egm` skill and `validate_egm.py` script enforce fixed numbered headings (`1. Overview & Objectives`, `3. State Schema`, `4. Invariants & Rules`, `7. Verification`) and a separate `docs/reviews/` verdict file. When the author uses the upstream `egm` plugin (`egm-brainstorm`, `egm-draft`, `egm-review`, `egm-review-loop`), Artifice's validator rejects upstream-formatted design documents and forces boilerplate compliance without improving technical rigour. Similarly, `extract_spec_invariants` in `scripts/build_review_dossier.py` scrapes `## 4. Invariants & Rules`, which only matches legacy Artifice specs.
2.  **High Gemini token spend during multi-lens EGM reviews:** Upstream `egm` skills spawn up to 7–10 isolated Goldfish reviewer subagents per pass (and multiple rounds in `egm-review-loop`). Running every stateless Goldfish reviewer through native harness subagents consumes Gemini quota, whereas naively routing the entire EGM workflow through `vibe_execute.py` breaks stateful Elephant phases that depend on multi-turn conversation memory and native interactive UI gates (`ask_question`).
3.  **Undocumented cross-harness expectations:** Artifice supports both Google Antigravity and GitHub Copilot, whereas upstream `egm` documents Antigravity installation (`~/.gemini/config/plugins/egm/`) but omits a Copilot installation workflow in its harness documentation. Leaving this implicit causes confusing mid-workflow failures when `/egm-*` skills are invoked on unconfigured hosts.

The proposed solution deletes Artifice's internal EGM skill, validator, lint gate, and dossier regex scraper; documents the upstream `egm` prerequisite and Antigravity-vs.-Copilot scope in `README.md`; shifts readiness accountability to PR/commit Stage 9 provenance audited during `/review`; and adds a reference guide under `skills/vibe-execute/` defining which stateless EGM phases offload to Mistral.

## Goals

*   **Eliminate duplicate EGM maintenance in Artifice:** Remove `skills/spec-egm/`, `scripts/validate_egm.py`, `lint.py` Gate 5, `extract_spec_invariants` in `scripts/build_review_dossier.py`, and all corresponding installer and unit-test checks so `lint.sh` passes with zero custom EGM validator code.
*   **Preserve design readiness accountability via PR/commit provenance:** Require `code-author` to record upstream `egm-review` Stage 9 (Implementation Readiness Test) or human sign-off in early PR descriptions or commit trailers, verified by `code-reviewer` under Pillar 1 during `/review`.
*   **Document clear external prerequisite and harness boundaries:** Record the tested upstream `google/elephant-goldfish-model` baseline (`version 0.1.1`, commit `270b103`), manual verification steps, Antigravity installation command, and explicit Copilot support limitations in `README.md`, while preserving existing `docs/designs/001`–`004` and `docs/reviews/001`–`004` as legacy historical records.
*   **Reduce Gemini token usage on stateless Goldfish reviews:** Provide an actionable routing and guardrail reference in `skills/vibe-execute/references/egm-offloading.md` (linked from `skills/vibe-execute/SKILL.md` within its 180-line / 1,000-word governance ceiling) so stateless Goldfish lenses run in parallel on Mistral via `vibe_execute.py` while stateful Elephant phases stay on Gemini.

## Non-Goals

*   **Automated plugin installation or host-state linting:** Artifice installers (`install_antigravity.sh`, `install_copilot.sh`) and `lint.py` will not clone, submodule, or probe `~/.gemini/config/plugins/egm/`.
*   **New in-repo design-document schema or marker linters:** Artifice will not replace `validate_egm.py` with a new file-header stamp or custom Markdown schema check in `lint.py`.
*   **Offloading stateful Elephant phases to `vibe_execute.py`:** Interactive clarification (`egm-brainstorm` Step 1), section-by-section drafting (`egm-draft`), finding resolution (`egm-resolve`), and `egm-synthesizer` orchestration will not be routed through one-shot `vibe_execute.py` subprocesses.
*   **Modifying out-of-repo host files in this changeset:** Global user files outside the repository (such as `~/.gemini/config/AGENTS.md`) are not modified by repository commits and remain a manual host update.

## Open Questions

*   None — all open architectural and scoping questions from brainstorming and Step 1 intake have been resolved.

## Critical User Journeys (CUJs)

### CUJ 1: Developer Sets Up Artifice and Verifies the Upstream EGM Prerequisite

*   **Given**: A developer clones or updates Artifice on an Antigravity or Copilot host and runs `./scripts/install_antigravity.sh` or `./scripts/install_copilot.sh`.
*   **When**: The installer runs preflight checks and the developer consults `README.md` for specification workflow prerequisites.
*   **Then**: The installer succeeds without checking for `skills/spec-egm/SKILL.md` or `scripts/validate_egm.py`, and `README.md` provides the tested `google/elephant-goldfish-model` baseline (`0.1.1` / `270b103`), the Antigravity install command, a manual check to confirm `~/.gemini/config/plugins/egm/plugin.json` is present, and an explicit note that upstream `egm` does not document a Copilot install command.

### CUJ 2: Author Runs `/egm-review /vibe-execute` to Offload Goldfish Reviews to Mistral

*   **Given**: A developer has drafted a design document with `/egm-draft` on Gemini and invokes an EGM review or brainstorm step alongside `/vibe-execute` in a repository without `--local` privacy restrictions.
*   **When**: The orchestrator loads `skills/vibe-execute/SKILL.md` and follows the link to `skills/vibe-execute/references/egm-offloading.md`.
*   **Then**: After proposing and confirming the exact Mistral model and identity fingerprint via `ask_question`, the orchestrator keeps stateful Elephant gates on Gemini, bypasses `egm-synthesizer`, and dispatches the stateless Goldfish lenses directly in parallel via `vibe_execute.py run` with bounded timeouts and `not run` failure accounting.

### CUJ 3: Craftsman Implements an Approved Design and Gatekeeper Audits Provenance

*   **Given**: A design document has completed upstream `egm-review` Stage 9 (Implementation Readiness Test) and received human sign-off.
*   **When**: `code-author` begins contract-first TDD, opens an early PR, runs `./scripts/lint.sh`, and hands off to `code-reviewer` (`/review`).
*   **Then**: `code-author` ingests invariants from the approved design document without calling `validate_egm.py`, records the design document path and Stage 9 sign-off in the PR description or commit trailers, `./scripts/lint.sh` passes without running Gate 5 against `docs/designs/`, and `code-reviewer` verifies the Stage 9 provenance under Pillar 1.

## Technical Plan (Architecture)

The architecture replaces Artifice's internal EGM subsystem with three decoupled mechanisms: (1) removal of duplicate EGM files and static-analysis hooks, (2) a Git/PR provenance contract linking `code-author` and `code-reviewer` to upstream `egm-review` Stage 9, and (3) a stateless flat-swarm offloading bridge in `skills/vibe-execute/`.

### 1. Subsystem Removal and Governance Cleanup

Artifice's internal EGM files (`skills/spec-egm/` and `scripts/validate_egm.py`) are deleted. Four repository consumers that previously referenced them are updated:

*   **Static Linter (`scripts/lint.py`)**: Gate 5 (`Validating EGM Specification Contracts`) is removed so `lint.py` no longer imports or executes `validate_egm` when `docs/designs/` is present. Gate 6 (`Checking Native Bash Syntax`) is renumbered to Gate 5. Core Diet ceilings (`SKILL_LINE_LIMIT = 180`, `SKILL_WORD_LIMIT = 1000`, `AGENT_WORD_LIMIT = 900`) and Markdown heading/link validation remain unchanged.
*   **Review Dossier (`scripts/build_review_dossier.py`)**: `extract_spec_invariants` (which regex-matched `## 4. Invariants & Rules` in `docs/designs/*.md`) is removed so `build_dossier` compiles repository-level invariants from `AGENTS.md` without assuming legacy section headers.
*   **Symlink Installers (`scripts/install_antigravity.sh` and `scripts/install_copilot.sh`)**: Preflight file-existence loops drop `skills/spec-egm/SKILL.md` and `scripts/validate_egm.py`.
*   **Unit Test Suite (`tests/test_artifice.py`)**: Removes `import validate_egm`, drops `"spec-egm"` from the canonical word-budget list, and deletes `PathTraversalTests` (which tested `validate_egm.sanitise_spec_path` and `validate_egm.validate_repo`).

### 2. Stage 9 Provenance Handoff Contract (`code-author` to `code-reviewer`)

Instead of gating TDD on an in-repo Python validator script, readiness is tracked through Git and Pull Request provenance:

*   **Pre-TDD Intake (`agents/code-author/agent.md`)**: Before writing Phase 1 (Red) tests, `code-author` confirms that the target design document has cleared upstream `egm-review` Stage 9 (Implementation Readiness Test) or received explicit human sign-off. Phase 1 ingests invariants and verification criteria directly from the approved design document (`Goals`, `Non-Functional Requirements`, and `Detailed Implementation Plan`) rather than hardcoded `Section 4` and `Section 7` numbers.
*   **Early PR & Trailer Provenance**: `code-author` records the approved design document path and Stage 9 sign-off status in the PR description (encouraging early draft PR creation) or commit trailers.
*   **Gatekeeper Verification (`skills/review/references/review-framework.md`)**: Pillar 1 (`Design & Architecture Alignment`) checks that implementation changes match the approved design document in `docs/designs/` and that PR/commit provenance records Stage 9 or human sign-off.

### 3. Elephant / Goldfish Split Offloading Architecture (`vibe-execute`)

When a developer pairs an upstream `/egm-*` skill with `/vibe-execute`, execution splits along EGM's memory boundary:

```text
+-------------------------------------------------------------------+
| Primary Harness Orchestrator (Gemini — "The Elephant")            |
|  - Stateful multi-turn memory & file editing                      |
|  - Native ask_question single-select UI gates                     |
|  - Runs: egm-brainstorm (Steps 1, 3, 4), egm-draft (Steps 1-6),   |
|          egm-resolve, egm-review-loop (Steps 2.1, 2.3, 2.4)       |
+-------------------------------------------------------------------+
          |
          | 1. Discover & confirm exact Mistral model + fingerprint
          |    via ask_question (unless --local policy applies)
          | 2. Bypass egm-synthesizer & native invoke_subagent
          | 3. Inject upstream persona + standard inline into prompt
          v
+-------------------------------------------------------------------+
| Parallel Stateless Workers via vibe_execute.py run (Mistral)      |
|  - Fresh zero-context CLI process per lens                        |
|  - Runs: egm-brainstorm Step 2 (up to 7 lenses),                  |
|          egm-review Stages 5-9 / egm-review-loop Step 2.2         |
|          (flat-swarm reviewers, max 5 rounds),                    |
|          egm-drift-report, egm-bootstrap leaf workers             |
|  - Guardrails: explicit --timeout (120s default; exit 124 ->      |
|    retry once -> record as "not run", never zero findings)        |
+-------------------------------------------------------------------+
```

To stay within `skills/vibe-execute/SKILL.md`'s 1,000-word budget (currently 731 words / 86 lines), `SKILL.md` adds only a reference link and a short pointer in Section 4, while the full routing table, prompt-assembly contract, and operational guardrails live in `skills/vibe-execute/references/egm-offloading.md`.

## Alternatives Considered

### Alternative A: Keep a Thin Validator, File Marker, or Automated Plugin Probe in `lint.py` / Installers

*   **Pros**: Provides an automated CI or install-time signal verifying that the upstream `egm` plugin is present on the host or that new `docs/designs/` documents carry an explicit readiness stamp.
*   **Cons**: Couples repository scripts (`lint.py`, `install_antigravity.sh`, `install_copilot.sh`) to out-of-repo `~/.gemini` host state, leaves Copilot without parity (since upstream `egm` omits a Copilot install workflow), and risks rubber-stamped header markers replacing genuine review.
*   **Reason for Rejection**: Rejected by author: keeping host-coupled probes or custom file-header stamps recreates the maintenance and compliance overhead that motivated removing Artifice's internal EGM validator; Git/PR Stage 9 provenance audited during `/review` preserves accountability without custom linters.

### Alternative B: Broaden or Retain `extract_spec_invariants` in `scripts/build_review_dossier.py`

*   **Pros**: Continues surfacing design-document bullets inside the compact review dossier compiled for `/review` without manual linking.
*   **Cons**: Couples `build_review_dossier.py` to upstream `egm` template headings (`## Goals`, `## Non-Functional Requirements`) that Artifice does not control, or leaves a legacy `## 4. Invariants & Rules` regex that silently ignores all new upstream EGM documents while scanning `docs/designs/` arbitrarily.
*   **Reason for Rejection**: Rejected by author: removing `extract_spec_invariants` keeps `build_review_dossier.py` focused on repository `AGENTS.md` governance invariants without scraping arbitrary design-doc section layouts.

### Alternative C: Run the Full EGM Workflow on Mistral or Wrap `vibe_execute.py` Inside `invoke_subagent`

*   **Pros**: Could keep native `egm-synthesizer` orchestration intact (if wrapped in `invoke_subagent`) or attempt to offload all EGM turns off Gemini.
*   **Cons**: One-shot `vibe_execute.py run` invocations lack multi-turn Elephant conversation memory and cannot render Antigravity's native `ask_question` UI gates (`egm-brainstorm` Step 1, `egm-draft`, `egm-resolve`). Wrapping `vibe_execute.py` inside `invoke_subagent` spends Gemini tokens on every wrapper subagent turn in addition to Mistral worker tokens, even though `vibe_execute.py` already runs in a fresh zero-context process.
*   **Reason for Rejection**: Rejected by author: direct parallel `vibe_execute.py run` calls for stateless Goldfish reviewers combined with Gemini for stateful Elephant turns achieves cross-model isolation without wrapper token waste or broken UI gates.

### Alternative D: Place EGM Offloading Guidance Only in `README.md` or Inline in `skills/vibe-execute/SKILL.md`

*   **Pros**: Keeping the note only in `README.md` leaves `skills/vibe-execute/SKILL.md` completely agnostic of external plugins; writing a principle-only paragraph directly inside `SKILL.md` avoids adding a new file under `skills/vibe-execute/references/`.
*   **Cons**: Agents invoked with `/egm-review /vibe-execute` in downstream repositories load `skills/vibe-execute/SKILL.md`, not Artifice's `README.md`, so `README.md`-only guidance is missed at runtime. Conversely, placing a complete routing table and guardrail specification inside `SKILL.md` crowds its 1,000-word governance ceiling (currently 731 words / 86 lines, leaving only 269 words of headroom).
*   **Reason for Rejection**: Rejected by author: linking from a short pointer in `skills/vibe-execute/SKILL.md` to `skills/vibe-execute/references/egm-offloading.md` guarantees runtime discoverability while keeping `SKILL.md` well under `lint.py`'s word limit.

--------------------------------------------------------------------------------

## Non-Functional Requirements

### Security and Privacy

*   **Remote Execution Boundary (`--local`):** Hosted Mistral dispatch via `vibe_execute.py` sends prompt payloads (target document, inline persona/standard prompts, and `GoldfishContext` excerpts) to Mistral's hosted service. Whenever `--local` or a repository privacy directive (`Privacy: on-device`, `Review: local-only`) applies, `vibe_execute.py` disables hosted Mistral execution; Goldfish offloading must halt rather than silently sending protected material off-device.
*   **Deleted Path-Traversal Surface:** Deleting `scripts/validate_egm.py` removes `sanitise_spec_path` and its `PathTraversalTests` alongside the script, eliminating that CLI argument surface.

### Performance, Latency, and Quota Economics

*   **Bounded Parallelism & Iteration Caps:** Stateless Goldfish flat-swarm calls run concurrently up to the lens count per pass (up to 7 lenses in `egm-brainstorm`, up to the requested stage reviewers in `egm-review-loop` capped at 5 rounds).
*   **Explicit Timeouts & Failure Accounting:** Each `vibe_execute.py run` invocation uses an explicit `--timeout` budget (default `120` seconds). Because `vibe_execute.py` returns exit code `124` with empty stdout on timeout, timed-out or non-zero workers may be retried at most once and must be recorded as `not run` (never as zero findings).
*   **Core Diet Compliance:** Edits to `skills/vibe-execute/SKILL.md`, `agents/code-author/agent.md`, and `skills/review/references/review-framework.md` must stay within `scripts/lint.py` ceilings (`180` lines / `1,000` words for skills, `900` words for agents, and the canonical word budget in `tests/test_artifice.py`).

### Rollout and Rollback

*   **Legacy Artefacts:** Existing `docs/designs/001`–`004` and `docs/reviews/001`–`004` remain untouched in-repo as historical records; removing Gate 5 from `scripts/lint.py` ensures they continue to pass linting without modification.
*   **Rollback:** Restoring the deleted files, lint gate, and tests is a single `git revert` of the implementation commit(s).

### Future Improvements

*   **`omp` (`oh-my-pi`) Headless Integration (Issue `#28`):** Once `omp` is installed and its fallback-chain / Thin-Orchestrator policy clashes with `vibe-execute` are resolved in a dedicated future PR, upstream `egm` can run natively inside `omp` (`omp plugin install egm@egm`), potentially superseding `skills/vibe-execute/references/egm-offloading.md`.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Create, Modify, or Delete

#### 1. `skills/spec-egm/SKILL.md` (`[Delete]`)

*   **Type / Scope**: Skill definition
*   **Proposed Changes**: Delete the custom Artifice EGM specification skill. Upstream `google/elephant-goldfish-model` replaces this workflow directly.

#### 2. `skills/spec-egm/references/design-spec-template.md` (`[Delete]`)

*   **Type / Scope**: Skill template reference
*   **Proposed Changes**: Delete Artifice's legacy fixed-section design template (`1. Overview & Objectives`, `3. State Schema`, `4. Invariants & Rules`, `7. Verification`), which is superseded by upstream `egm-draft/references/design_doc.md`.

#### 3. `skills/spec-egm/references/goldfish-review-template.md` (`[Delete]`)

*   **Type / Scope**: Skill template reference
*   **Proposed Changes**: Delete Artifice's legacy single-file Goldfish review template (`docs/reviews/<NNN>_*_review.md`), which is superseded by upstream `egm-review` and `egm-review-loop`.

#### 4. `scripts/validate_egm.py` (`[Delete]`)

*   **Type / Scope**: Python validation script
*   **Proposed Changes**: Delete the 222-line section-header and `Verdict: Approved` validator script. Readiness enforcement shifts to upstream `egm-review` Stage 9 and PR/commit provenance.

#### 5. `scripts/lint.py` (`[Modify]`)

*   **Type / Scope**: Static governance linter
*   **Proposed Changes**: Remove Gate 5 (`Validating EGM Specification Contracts` block importing `validate_egm` when `docs/designs` exists) and renumber Gate 6 (`Checking Native Bash Syntax`) to Gate 5. Update the module docstring if needed so it no longer implies EGM contract validation. Preserve Core Diet limits, Markdown heading blank-line checks, relative-link checks, and Copilot adapter checks unchanged.

#### 6. `scripts/build_review_dossier.py` (`[Modify]`)

*   **Type / Scope**: Invariant dossier compiler
*   **Proposed Changes**: Remove `extract_spec_invariants` and its call/output loop in `build_dossier` so the dossier no longer regex-scrapes `## 4. Invariants & Rules` from `docs/designs/*.md`. Keep `find_repo_agents_md`, `extract_invariants`, repository-specific rules, CLI flags (`repo_root`, `--files`), and the 40-line cap intact.

#### 7. `scripts/install_antigravity.sh` (`[Modify]`)

*   **Type / Scope**: Symlink installer
*   **Proposed Changes**: Remove `spec-egm` from the `skills/{...}/SKILL.md` preflight list and `validate_egm` from the `scripts/{...}.py` preflight list so preflight checks pass without deleted EGM files. Keep anchor, symlink, `skills.json`, and `--check` logic unchanged.

#### 8. `scripts/install_copilot.sh` (`[Modify]`)

*   **Type / Scope**: Symlink installer
*   **Proposed Changes**: Remove `spec-egm` from the `skills/{...}/SKILL.md` preflight list and `validate_egm` from the `scripts/{...}.py` preflight list so Copilot symlink installation and `--check` succeed without deleted EGM files.

#### 9. `agents/code-author/agent.md` (`[Modify]`)

*   **Type / Scope**: Canonical agent instructions
*   **Proposed Changes**: In Section 2 (`Invariant & Contract Ingestion`), replace the `spec-egm` link and `validate_egm.py . --spec <NNN>` command with a procedural gate requiring that the target design document has cleared upstream `egm-review` Stage 9 (Implementation Readiness Test) or received explicit human sign-off, while keeping the `build_review_dossier.py` command. In Phase 1 (`Red (Contract Tests)`), replace hardcoded `Section 4 and Section 7` references with ingesting invariants and verification criteria from the approved design document (`Goals`, `Non-Functional Requirements`, and `Detailed Implementation Plan`). In Section 4 (`Model Commit Authorship & Provenance`), require recording the design document path and Stage 9 sign-off in the PR description (encouraging early PR creation) or a `Design-Review:` / commit provenance trailer. Keep total word count below `AGENT_WORD_LIMIT = 900`.

#### 10. `skills/review/references/review-framework.md` (`[Modify]`)

*   **Type / Scope**: Review rubric reference
*   **Proposed Changes**: Update Pillar 1 (`Design & Architecture Alignment`) to verify implementation alignment against the active approved design document in `docs/designs/` (or PR-linked design doc) and confirm that PR description or commit provenance records upstream `egm-review` Stage 9 (Implementation Readiness Test) or human sign-off.

#### 11. `skills/vibe-execute/SKILL.md` (`[Modify]`)

*   **Type / Scope**: Skill definition
*   **Proposed Changes**: Add a link to `[EGM Goldfish offloading](references/egm-offloading.md)` under `Reference Materials` and a concise (~30–40 word) pointer in Section 4 (`Compound Execution & Triage`) stating that pairing `/egm-*` with `/vibe-execute` keeps stateful Elephant work on the primary harness and fans out stateless Goldfish reviewers directly via `vibe_execute.py run`. Ensure total size remains well below `SKILL_LINE_LIMIT = 180` and `SKILL_WORD_LIMIT = 1000`.

#### 12. `skills/vibe-execute/references/egm-offloading.md` (`[Create]`)

*   **Type / Scope**: Skill reference guide
*   **Proposed Changes**: Document the operational contract for pairing upstream `egm` with `/vibe-execute`:
    *   **Routing Split Table**: Map stateful Elephant workflows (`egm-brainstorm` clarification, `egm-draft`, `egm-resolve`, and `egm-review-loop` target resolution / resolution / convergence checks) to the primary harness (Gemini), and stateless Goldfish workflows (`egm-brainstorm` lenses, `egm-review` / `egm-review-loop` flat-swarm reviewers, `egm-drift-report`, `egm-bootstrap` leaf workers) to Mistral via `vibe_execute.py run`, noting failure modes if stateful steps are misrouted.
    *   **Direct-Dispatch Rules**: Instruct the orchestrator to bypass `egm-synthesizer` (since `vibe` CLI cannot call `invoke_subagent`), avoid wrapping `vibe_execute.py` inside `invoke_subagent`, inject upstream persona and standard text inline, and pass `GoldfishContext` excerpts concisely.
    *   **Operational Guardrails**: Require exact model + fingerprint approval via `ask_question` before dispatch, enforce explicit `--timeout` budgets (noting exit `124` returns empty stdout), allow at most 1 retry per failed lens before marking it `not run` (never zero findings), bound concurrent lenses per pass and `egm-review-loop` to 5 rounds, and halt hosted Mistral dispatch whenever `--local` or repository local-only privacy directives apply.

#### 13. `README.md` (`[Modify]`)

*   **Type / Scope**: Repository documentation
*   **Proposed Changes**:
    *   Remove `skills/spec-egm/` and `scripts/validate_egm.py` from `Directory Structure`, `Available Skills` (renumbering skills 1–4), and `Core Scripts & Verification`.
    *   Add a short note under `Directory Structure` or `External Prerequisites` marking existing `docs/designs/001`–`004` and `docs/reviews/001`–`004` as legacy historical records from the retired internal EGM format.
    *   Add an `External Prerequisites (Upstream EGM)` section documenting `https://github.com/google/elephant-goldfish-model` (tested baseline `version 0.1.1`, commit `270b103`), the Antigravity CLI install command (`agy plugin install https://github.com/google/elephant-goldfish-model`), a manual verification step (`~/.gemini/config/plugins/egm/plugin.json` present / `/egm-review` loads), and explicit Copilot scope noting upstream `egm`'s `docs/harnesses.md` omits a Copilot install workflow.

#### 14. `tests/test_artifice.py` (`[Modify]`)

*   **Type / Scope**: Unit and integration tests
*   **Proposed Changes**: Remove `import validate_egm`, remove `"spec-egm"` from the `canonical` skill tuple in `test_live_repository_and_canonical_word_budget`, and remove `PathTraversalTests` (which exclusively test `validate_egm`). Add a regression check confirming `lint.lint_repository` passes when a repository's `docs/designs/` contains an upstream-EGM-formatted design document without legacy numbered headings or a `docs/reviews/` verdict file, and add a check confirming `build_review_dossier.build_dossier` runs cleanly without `extract_spec_invariants`. Also verify `tests/test_artifice.py` tests `skills/vibe-execute/SKILL.md` link/word-budget compliance via `lint.lint_repository`.

### Verification Plan

*   **Static Analysis & Linting**: Run `./scripts/lint.sh` and confirm exit code `0` (verifying Markdown heading blank-line cleanliness, relative links including `skills/vibe-execute/references/egm-offloading.md`, YAML frontmatter, Core Diet word/line ceilings on `skills/vibe-execute/SKILL.md` and `agents/code-author/agent.md`, and Bash syntax on installers).
*   **Unit & Integration Tests**: Run `python3 -m unittest discover -s tests -v` and confirm all tests pass without `validate_egm` or `spec-egm` dependencies, including the new `lint.py` non-legacy `docs/designs/` test and `build_review_dossier.py` test.
*   **Installer & Script Smoke Checks**: Run `bash scripts/install_antigravity.sh --check` (or temporary-HOME sandbox test) and `bash scripts/install_copilot.sh --check`, and run `python3 scripts/build_review_dossier.py .` to confirm clean execution.
*   **Residual Reference Check**: Grep across `scripts/`, `skills/`, `agents/`, `integrations/`, `tests/`, and `README.md` for `validate_egm` and `spec-egm` to confirm zero stale references remain outside historical `docs/designs/001`–`004` and `docs/reviews/001`–`004`.

--------------------------------------------------------------------------------

*Drafted with EGM*
