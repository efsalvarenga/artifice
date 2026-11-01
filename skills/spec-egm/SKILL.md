---
name: spec-egm
version: 1.0.0
description: >-
  Orchestrates the Elephant-Goldfish Model (EGM) specification-driven development
  workflow: pre-spec empirical reconnaissance, no-code Elephant design specs,
  zero-context Goldfish reviews, and automated contract validation.
argument-hint: "[init <feature_name> | review <spec_path> | validate [repo_path]]"
---

# Elephant-Goldfish Model Specification Workflow (`spec-egm`)

This skill coordinates specification-driven development using the **Elephant-Goldfish Model (EGM)**. It ensures that technical specifications precede implementation, undergo rigorous zero-context critique, and maintain contract consistency.

## Reference Materials

* **Design Specification Template:** [`references/design-spec-template.md`](references/design-spec-template.md)
* **Goldfish Review Template:** [`references/goldfish-review-template.md`](references/goldfish-review-template.md)
* **Validation Script:** [`../../scripts/validate_egm.py`](../../scripts/validate_egm.py)

## Step-by-Step EGM Procedure

### Step 1: Pre-Spec Recon & The Elephant Phase (Strict No-Code)

When a new feature, engine capability, or architectural module is requested:

1. **60-Second Empirical Disk Recon:**
   Before authoring the design document, execute read-only checks across the target repository to measure existing types, verify file boundaries, and assess test baselines. Do not rely on assumptions carried over from prior conversation context.
2. **Precedent Search:**
   Search repository rulings (`decisions.md`, `AGENTS.md`, `TASKS.md`, and `git log -S`) for relevant architectural precedents.
3. **Draft the Specification:**
   * Create `docs/designs/<NNN>_<feature_slug>.md` using [`references/design-spec-template.md`](references/design-spec-template.md).
   * **Strict No-Code Rule:** Focus entirely on data schemas, state invariants, tick or event mechanics, edge cases, and deterministic test requirements. Do not write production implementation code during this phase.
   * Mark `Status: Under Review`.

### Step 2: Zero-Context Goldfish Review

Once the Elephant draft is complete, subject it to an adversarial, zero-context review:

1. **Mechanically Enforced Zero Context:**
   Invoke a fresh review subagent (or adopt the Goldfish Reviewer persona with zero prior conversational memory). Pass only:
   * The newly drafted specification file (`docs/designs/<NNN>_<feature_slug>.md`).
   * The repository's `AGENTS.md`.
   * The Goldfish template: [`references/goldfish-review-template.md`](references/goldfish-review-template.md).
2. **Probing for Blind Spots:**
   The reviewer must actively seek contradictions, unbounded types, race conditions, non-deterministic branches, and missing failure modes.
3. **Produce Review Report:**
   Write the findings to `docs/reviews/<NNN>_<feature_slug>_review.md` with an explicit verdict: `Approved` or `Revisions Required`.
4. **Resolution:**
   If revisions are required, the Elephant agent updates the specification until the Goldfish reviewer signs off with `Verdict: Approved`.

### Step 3: Contract Validation & Drift Control

Before writing any implementation code or opening an implementation Pull Request:

1. Run the portable contract validator:
   ```bash
   python3 ~/Repos/artifice/scripts/validate_egm.py .
   ```
2. The validator verifies that:
   * Every active specification in `docs/designs/` contains required schema and invariant sections.
   * Every numbered specification has a matching Goldfish review in `docs/reviews/`.
   * Every matching review ends with `Verdict: Approved`.
3. If validation succeeds, implementation may proceed on an isolated feature branch.
