---
name: spec-egm
version: 1.1.0
description: >-
  Orchestrates the Elephant-Goldfish Model (EGM) specification-driven development
  workflow: pre-spec reconnaissance, interactive design workshops, no-code Elephant
  specs, zero-context Goldfish reviews, and automated contract validation.
argument-hint: "[init <feature_name> | review <spec_path> | validate [repo_path]]"
---

# Elephant-Goldfish Model Specification Workflow (`spec-egm`)

This skill coordinates specification-driven development using the **Elephant-Goldfish Model (EGM)**. It ensures that technical specifications precede implementation, undergo collaborative human design workshops, survive adversarial zero-context critique, and maintain contract consistency.

## Reference Materials

* **Design Specification Template:** [`references/design-spec-template.md`](references/design-spec-template.md)
* **Goldfish Review Template:** [`references/goldfish-review-template.md`](references/goldfish-review-template.md)
* **Validation Script:** [`../../scripts/validate_egm.py`](../../scripts/validate_egm.py)

## Step-by-Step EGM Procedure

### Step 1: Pre-Spec Recon & The Elephant Phase (Strict No-Code)

When a new feature, milestone, or architectural module is requested:

#### 1A. Empirical Recon & Interactive Design Workshop Canvas

1. **60-Second Empirical Disk Recon:**
   Before discussing designs or authoring documents, execute read-only disk checks across the target repository to measure existing types, verify file boundaries, and assess test baselines.
2. **Interactive Design Workshop Canvas:**
   * **Mandatory Alignment Gate:** The agent must *never* unilaterally generate a complete specification in isolation.
   * Present an interactive Design Workshop canvas in chat or artifact format, proactively interrogating the human author on:
     * Architectural options and explicit trade-offs.
     * Data schemas, boundaries, and state representations.
     * Execution mode, model tiering, and failure fallbacks.
   * Align on all decisions upfront before drafting the specification.

#### 1B. Draft the Technical Specification

1. Create `docs/designs/<NNN>_<feature_slug>.md` using [`references/design-spec-template.md`](references/design-spec-template.md).
2. **Strict No-Code Rule:** Focus entirely on data schemas, state invariants, tick/event mechanics, boundary edge cases, and deterministic test requirements. Do not write production code during this phase.
3. Mark `Status: Under Review`.

### Step 2: Zero-Context Goldfish Review

Subject the Elephant draft to an adversarial, zero-context critique:

1. **Mechanically Enforced Zero Context:**
   Invoke a fresh review subagent (or adopt the Goldfish Reviewer persona with zero prior conversational memory). Pass only:
   * The specification file (`docs/designs/<NNN>_<feature_slug>.md`).
   * The repository's `AGENTS.md`.
   * The Goldfish template: [`references/goldfish-review-template.md`](references/goldfish-review-template.md).
2. **Probing for Blind Spots:**
   The reviewer must actively seek contradictions, unbounded types, race conditions, non-deterministic branches, and missing failure modes.
3. **Produce Review Report:**
   Write findings to `docs/reviews/<NNN>_<feature_slug>_review.md` with an explicit verdict: `Approved` or `Revisions Required`.
4. **Resolution:**
   The Elephant agent updates the spec until the Goldfish reviewer signs off with `Verdict: Approved`.

### Step 3: Contract Validation & Autonomous Handoff

Before writing any implementation code or opening an implementation Pull Request:

1. Run the portable contract validator:
   ```bash
   python3 ~/Repos/artifice/scripts/validate_egm.py .
   ```
2. The validator verifies that:
   * Every active specification contains required schema and invariant sections.
   * Every numbered specification has a matching Goldfish review with `Verdict: Approved`.
3. Upon validation success, implementation proceeds autonomously on an isolated feature branch without mid-flight stalls.
