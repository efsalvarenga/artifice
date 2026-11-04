---
name: spec-egm
version: 1.2.0
description: >-
  Orchestrates the Elephant-Goldfish Model (EGM) specification-driven development
  workflow: pre-spec reconnaissance, front-loaded Grill-Me workshops, no-code Elephant
  specs, zero-context Goldfish reviews, and hardened implementation handoff.
argument-hint: "[init <feature_name> | review <spec_path> | validate [repo_path] [--spec <id>]]"
---

# Elephant-Goldfish Specification Workflow

Align with the human before drafting, review independently, then validate the approved contract before implementation.

## Resources & Authority

Select Artifice in this order: explicitly supplied `ARTIFICE_ROOT` -> present `$HOME/.local/share/artifice` (including broken symlinks) -> `$HOME/Repos/artifice`. Validate only the selected source: empty/invalid overrides and broken/invalid selected anchors fail without fallback; unused lower-priority anchors are ignored. Require an absolute path, resolve it physically, and check readable `agents`, `skills`, `scripts` directories and the requested asset. Stop and request repair on validation failure. No physical definition path is required. Bind the quoted `ARTIFICE_ROOT` per command; the target repository is separate.

Follow active client/repository authority, including valid preauthorisation. Branch changes, staging, commits, pushes and PR publication need operation-specific permission; this workflow grants none. Human design approval is distinct from review approval and Git permission. Use British English and blank lines after headings; preserve human narrative sovereignty. Strict local-only work requires a genuinely local session before protected reads, with no cloud fallback.

Documentation: [design template](references/design-spec-template.md), [Goldfish template](references/goldfish-review-template.md), [validator](../../scripts/validate_egm.py), [code-author](../../agents/code-author/agent.md). Runtime reads use the validated root, never lexical traversal through personal registration symlinks. Use the selected project interpreter where needed.

## 1. Reconnaissance & Elephant Design — No Code

1. **Empirical recon:** Start with approximately 60 seconds of permitted read-only disk checks. Measure existing types, file boundaries and native test baselines before discussing designs or writing documents.
2. **Front-loaded Grill-Me workshop:** Exhaust human-dependent decisions across:
   * Scope, non-goals, boundaries and trade-offs.
   * State schemas, invariants, valid bounds, persistence and concurrency.
   * Orchestrator/local engines and workspace isolation (`inherit`/`share`).
   * Verification, boundary/mutation probes, failure handling and recovery.
3. Require explicit human confirmation of the workshop canvas before drafting. Do not equate brief chat or an autonomous goal with design sign-off.
4. Draft `docs/designs/<NNN>_<feature_slug>.md` from the design template, marked `Status: Under Review`. Specify schemas, state/event mechanics, invariants, edge cases, truthful provenance and deterministic tests. Do not write production code.
5. Present the design for explicit approval before implementation. Material revisions require renewed approval.

## 2. Zero-Context Goldfish Review

Invoke a fresh independent reviewer through the current client's authorised delegation mechanism. Supply only the specification, repository `AGENTS.md` if present (otherwise state its absence), and Goldfish template. Changing persona does not clear this conversation's context. If independent delegation is unavailable, report the limitation and request independent review; never self-certify.

Probe contradictions, unbounded types, races, non-determinism and missing failure modes. Record `Approved` or `Revisions Required` in `docs/reviews/<NNN>_<feature_slug>_review.md`. Iterate the specification and independent review until approved; present material changes for renewed human approval.

## 3. Validation & Authoring Handoff

Confirm explicit human approval of the final revision, then run targeted validation:

```bash
ARTIFICE_ROOT="<validated-root>"; python3 "$ARTIFICE_ROOT/scripts/validate_egm.py" "<target_repo>" --spec "<NNN>"
```

The validator checks required sections and matching approved Goldfish review; it does not supply human sign-off. Stop on non-zero exit status. Only a green contract permits handoff to `code-author`: Red contract tests, minimal Green implementation, Razor refactoring, native baseline gate, independent review.

TDD phases need no commits. Separately authorised Git operations retain accurate `Model-Author`, `Agent-Role` and `Co-authored-by` provenance for actual contributors without guessing hidden model identities.
