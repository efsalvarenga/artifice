---
name: spec-egm
version: 1.2.0
description: >-
  Orchestrates the Elephant-Goldfish Model (EGM) specification-driven development
  workflow: pre-spec reconnaissance, front-loaded Grill-Me workshops, no-code Elephant
  specs, zero-context Goldfish reviews, and hardened implementation handoff.
argument-hint: "[init <feature_name> | review <spec_path> | validate [repo_path] [--spec <id>]]"
---

# Elephant-Goldfish Model Specification Workflow (`spec-egm`)

This skill coordinates specification-driven development using the **Elephant-Goldfish Model (EGM)**. It ensures that technical specifications precede implementation, undergo collaborative front-loaded human design alignment, survive adversarial zero-context critique, and pass mechanical verification before releasing authoring agents.

## Reference Materials

* **Design Specification Template:** [`references/design-spec-template.md`](references/design-spec-template.md)
* **Goldfish Review Template:** [`references/goldfish-review-template.md`](references/goldfish-review-template.md)
* **Validation Script:** [`../../scripts/validate_egm.py`](../../scripts/validate_egm.py)
* **Code Author Agent:** [`../../agents/code-author/agent.md`](../../agents/code-author/agent.md)

Resolve `ARTIFICE_ROOT` from an explicit value, `$HOME/.local/share/artifice` when present, or `$HOME/Repos/artifice`, and resolve links from `ARTIFICE_ROOT/skills/spec-egm/`.

## Step-by-Step EGM Procedure

### Step 1: Pre-Spec Recon & The Elephant Phase (Strict No-Code)

When a new feature, milestone, or architectural module is requested:

#### 1A. Empirical Recon & Front-Loaded "Grill-Me" Workshop

1. **60-Second Empirical Disk Recon:**
   Before discussing designs or authoring documents, execute read-only disk checks across the target repository to measure existing types, verify file boundaries, and assess test baselines.
2. **Front-Loaded "Grill-Me" Alignment Canvas:**
   * **Mandatory Alignment Gate:** Never unilaterally generate a complete specification in isolation or conflate brief conversational chat with design sign-off.
   * Proactively interrogate the human author across four structured categories to exhaust all human-dependent decisions before execution:
     * *Architectural Scope & Non-Goals:* Explicit exclusions, design boundaries, and trade-off choices.
     * *State Schemas & Invariant Contracts:* Data structures, valid value bounds, persistence, and concurrency rules.
     * *Execution Mode & Model Tiering:* Current client orchestrator vs local engines (`local-code`), workspace isolation mode (`inherit` vs `share`).
     * *Verification & Failure Fallbacks:* Test harness, boundary conditions, mutation probes, and recovery mechanisms.
   * Require explicit human confirmation on the workshop canvas before proceeding to Step 1B.

#### 1B. Draft the Technical Specification

1. Create `docs/designs/<NNN>_<feature_slug>.md` using [`references/design-spec-template.md`](references/design-spec-template.md) (resolved under `ARTIFICE_ROOT/skills/spec-egm/`).
2. **Strict No-Code Rule:** Focus entirely on data schemas, state invariants, tick/event mechanics, boundary edge cases, model commit attribution, and deterministic test requirements. Do not write production code during this phase.
3. Mark `Status: Under Review` and present the specification to the human developer for approval before entering Step 3 implementation (unless unattended `/goal` execution was explicitly commanded).

### Step 2: Zero-Context Goldfish Review

Subject the Elephant draft to an adversarial, zero-context critique:

1. **Mechanically Enforced Zero Context:**
   Invoke a fresh review subagent via the active client's delegation capability (report if delegation is unavailable rather than self-certifying). Pass only:
   * The specification file (`docs/designs/<NNN>_<feature_slug>.md`).
   * The repository's `AGENTS.md` (if present).
   * The Goldfish template: [`references/goldfish-review-template.md`](references/goldfish-review-template.md).
2. **Probing for Blind Spots:**
   Actively seek contradictions, unbounded types, race conditions, non-deterministic branches, and missing failure modes.
3. **Produce Review Report:**
   Write findings to `docs/reviews/<NNN>_<feature_slug>_review.md` with an explicit verdict: `Approved` or `Revisions Required`.
4. **Resolution:**
   Update the specification until the Goldfish reviewer signs off with `Verdict: Approved`, presenting any material design revisions for human sign-off.

### Step 3: Hardened Contract Validation & Implementation Handoff

Before writing implementation code or dispatching authoring subagents:

1. Run the targeted contract validator:

   ```bash
   python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/validate_egm.py" . --spec <NNN>
   ```

2. Confirm exit code `0` (verifying required sections and an approved Goldfish review).
3. **The Craftsman Handoff (`code-author`):**
   * Proceed via [`code-author`](../../agents/code-author/agent.md) ("The Craftsman") following the contract-first TDD cycle: Red (failing invariant assertions) $\rightarrow$ Green (minimal deterministic logic) $\rightarrow$ Refactor (Occam's Razor) $\rightarrow$ Pre-Review Baseline Gate (`./scripts/lint.sh`).
   * When commits are authorised by active client/repository Git rules, author atomic phase commits with accurate model provenance trailers (`Model-Author`, `Agent-Role`, and GitHub-rendered `Co-authored-by`).
   * **Strict Merge Invariant:** Under NO circumstances may any agent call 'gh pr merge', invoke the GitHub PR merge API, or execute 'git merge' into main. Merging is strictly reserved for the human developer.
