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

This skill coordinates specification-driven development using the **Elephant-Goldfish Model (EGM)**. It ensures that technical specifications precede implementation, undergo collaborative front-loaded human design alignment, survive adversarial zero-context critique, and enforce mechanical verification before releasing authoring subagents.

## Reference Materials

* **Design Specification Template:** [`references/design-spec-template.md`](references/design-spec-template.md)
* **Goldfish Review Template:** [`references/goldfish-review-template.md`](references/goldfish-review-template.md)
* **Validation Script:** Read `scripts/validate_egm.py` under the resolved Artifice resource root when needed.

### Resource Resolution

Use `$HOME/.local/share/artifice` when present; resolve it physically and validate its `agents`, `skills`, and `scripts` directories. A present broken or invalid anchor is an error. Only when absent, resolve this definition's containing directory physically before ascending two directories. Validate the checkout and requested resource; if discovery has no physical source or a resource is unavailable, stop and request repair rather than guessing from the target repository.

Bind the resolved absolute directory as `ARTIFICE_ROOT` for each relevant command, quoting it and passing the target repository separately. Do not assume the value persists between shell executions. Use the selected Python interpreter in place of `python3` where required.

Require explicit operation-specific permission for branch changes, staging, commits, pushes, and PR publication. Drafting or implementation permission does not authorise those operations.

## Step-by-Step EGM Procedure

### Step 1: Pre-Spec Recon & The Elephant Phase (Strict No-Code)

When a new feature, milestone, or architectural module is requested:

#### 1A. Empirical Recon & Front-Loaded "Grill-Me" Workshop

1. **60-Second Empirical Disk Recon:**
   Before discussing designs or authoring documents, execute read-only disk checks across the target repository to measure existing types, verify file boundaries, and assess test baselines.
2. **Front-Loaded "Grill-Me" Alignment Canvas:**
   * **Mandatory Alignment Gate:** The agent must *never* unilaterally generate a complete specification in isolation or conflate brief conversational chat with design sign-off.
   * Proactively interrogate the human author across four structured categories to exhaust all human-dependent decisions before execution:
     * *Architectural Scope & Non-Goals:* Explicit exclusions, design boundaries, and trade-off choices.
     * *State Schemas & Invariant Contracts:* Data structures, valid value bounds, persistence, and concurrency rules.
     * *Execution Mode & Model Tiering:* Orchestrator vs local engines (`local-code`), workspace isolation mode (`inherit` vs `share`).
     * *Verification & Failure Fallbacks:* Test harness, boundary conditions, mutation probes, and recovery mechanisms.
   * Require explicit human confirmation on the workshop canvas before proceeding to Step 1B.

#### 1B. Draft the Technical Specification

1. Create `docs/designs/<NNN>_<feature_slug>.md` using [`references/design-spec-template.md`](references/design-spec-template.md).
2. **Strict No-Code Rule:** Focus entirely on data schemas, state invariants, tick/event mechanics, boundary edge cases, model commit attribution, and deterministic test requirements. Do not write production code during this phase.
3. Mark `Status: Under Review`.
4. Present the document and stop for explicit human design approval before any implementation. Material revisions require renewed approval; a generic autonomous goal does not waive this pause.

### Step 2: Zero-Context Goldfish Review

Subject the Elephant draft to an adversarial, zero-context critique:

1. **Mechanically Enforced Zero Context:**
   Invoke a fresh review subagent using the current client's delegation capability. Do not claim that changing persona clears the current conversation's memory. If independent delegation is unavailable, report the limitation and request an independent review rather than self-certifying. Pass only:
   * The specification file (`docs/designs/<NNN>_<feature_slug>.md`).
   * The repository's `AGENTS.md`.
   * The Goldfish template: [`references/goldfish-review-template.md`](references/goldfish-review-template.md).
2. **Probing for Blind Spots:**
   The reviewer must actively seek contradictions, unbounded types, race conditions, non-deterministic branches, and missing failure modes.
3. **Produce Review Report:**
   Write findings to `docs/reviews/<NNN>_<feature_slug>_review.md` with an explicit verdict: `Approved` or `Revisions Required`.
4. **Resolution:**
   The Elephant agent updates the spec until the Goldfish reviewer signs off with `Verdict: Approved`.
5. Present material revisions for renewed human approval. The review verdict is independent of human sign-off.

### Step 3: Hardened Contract Validation & Implementation Handoff

Before writing any implementation code or dispatching authoring subagents:

1. Confirm explicit human approval of the final presented design, then run the targeted contract validator:
   ```bash
   python3 "$ARTIFICE_ROOT/scripts/validate_egm.py" "<target_repo>" --spec <NNN>
   ```
2. The validator verifies that:
   * The target specification exists and contains all required sections (Overview, Schema, Invariants, Verification).
   * A matching Goldfish review exists with `Verdict: Approved`.
3. **The Craftsman Handoff (`code-author`):**
   * Upon successful validation (exit code `0`), implementation proceeds via `code-author` ("The Craftsman") following the contract-first TDD cycle: Red (failing invariant assertions) $\rightarrow$ Green (minimal deterministic logic) $\rightarrow$ Refactor (Occam's Razor) $\rightarrow$ Pre-Review Baseline Gate (`./scripts/lint.sh`).
   * TDD phases do not require commits. Only when separately authorised, commits retain accurate model and agent provenance (`Model-Author`, `Co-authored-by`) without guessing hidden model identifiers.
