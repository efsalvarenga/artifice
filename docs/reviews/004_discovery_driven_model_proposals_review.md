# Design Review: Discovery-Driven Model Proposals

**Review Target:** [Design 004](../designs/004_discovery_driven_model_proposals.md)
**Reviewer:** Copilot SDK assistant (`gpt-6.1-sol`), direct contract review
**Date:** 2026-11-05
**Verdict:** Approved

## 1. Executive Summary

The discovery-first design addresses an observed failure: the installed
`qwen3.8:27b-mlx` model is outside the selector's preferred-name list. The proposed
separation between metadata discovery, assistant recommendations and exact
execution is appropriate.

The developer authorised implementation on 2026-11-05 and subsequently chose
Ollama delivery now, explicitly deferring hosted discovery rather than creating
an isolated Vibe runtime. The approved scope is the local phase; this verdict
does not approve or certify the future hosted adapter.

This is a direct orchestrator review, not an independent or zero-context agent
review. It must not be represented as independent approval. The review examines
the specification and existing selection, dispatch and test contracts.

## 2. Invariant & Edge-Case Probing

| ID | Area | Probe | Resolution required |
| --- | --- | --- | --- |
| PROBE-01 | Hosted compatibility | Is the Vibe metadata path real, read-only and version-bounded? | Resolved by explicit developer deferral; CLI presence never establishes selectable hosted models. |
| PROBE-02 | CLI requirements | Can the runner validate the same task requirements the developer approved? | Specification defines task, mode, capability, context and unknown-evidence flags. |
| PROBE-03 | Locality | Does a loopback proxy or cloud-backed model incorrectly satisfy local-only policy? | Separate transport locality from model execution evidence; unknown locality blocks strict-local dispatch. |
| PROBE-04 | Selection | Does a one-model roster accidentally become a suitability assertion? | Automatic selection requires known compatible metadata; unknown suitability is never implicitly accepted. |
| PROBE-05 | Manifest identity | Are provider-qualified identities unambiguous when tags contain slashes or colons? | `provider/source/model` splits at the first two slashes; exact tag remainder is preserved. |
| PROBE-06 | Compatibility | Could optional Vibe discovery introduce a Python 3.11 requirement into the Python 3.9 controller? | No hosted runtime is introduced in this phase; controller remains standard-library Python 3.9. |
| PROBE-07 | Failure isolation | Can partial results hide provider failures or remove discovered models? | Preserve identities, structured diagnostics, partial status and non-zero discovery result. |

## 3. Detailed Critiques & Blind Spots

### 3.1 Data Schema Completeness

Task requirements need concrete CLI representation rather than an implicit
assistant-only object. Model identities must survive namespaces and arbitrary
provider aliases without prefix-based routing. A changed endpoint or alias must
invalidate the approved fingerprint before warming or inference.

### 3.2 State Mutation & Deterministic Consistency

Vibe configuration/authentication helpers may perform migrations, cache writes or
credential refresh. An ordinary configuration constructor is not automatically
safe for discovery. The adapter needs a verified, narrowly scoped read-only path
and explicit unsupported-version behaviour.

Reported installed weights, a trusted configured loopback runtime and absence of
remote-backing metadata may establish on-device evidence. This is not attestation
of an arbitrary proxy; unverified execution locality must remain blocked under
strict policy.

### 3.3 Testability & Verification Strategy

Fixtures can cover both providers without credentials or inference. Deadline
tests must bound the aggregate operation, not just individual socket timeouts.
Selection and dispatch tests must prove that missing/unknown metadata never
becomes an automatic model-quality decision or privacy waiver.

The existing baseline comprises 26 passing selection/gateway tests. Tests that
assert the old hardcoded names and automatic cloud fallback must be updated for
the authorised behaviour change, while preserving warming, error and manifest
regressions.

## 4. Resolved Revisions

1. The compatibility investigation verified Vibe 3.1.0's Python 3.12 requirement,
   mutating normal configuration path and lack of an existing read-only export.
   The developer explicitly deferred the hosted adapter. It must remain
   unavailable for selection and dispatch until separately verified.
2. The specification defines task requirement flags and reversible
   provider-qualified model references.
3. The specification distinguishes local-weight evidence from loopback
   transport and prohibits automatic acceptance of unknown capabilities.
4. This document records direct-review provenance rather than claiming an
   independent zero-context review.

## 5. Recommendation & Sign-Off

**Verdict:** Approved

The local-phase design is sufficiently concrete for contract-first
implementation. Run targeted EGM validation before production changes. No
production changes or model inference were performed as part of this review.

## 6. Implementation Verification

The targeted EGM gate and all 44 existing tests passed before implementation.
Contract-first tests subsequently cover unfamiliar tags, ambiguous selection,
unknown capabilities, exact identities, local privacy and structured errors.

Direct implementation inspection identified two additional boundary defects:
HTTPConnection could reopen a timer-closed socket and send after its deadline,
and conflicting context metadata could be reported as a known capacity. Both
were reproduced with failing tests and corrected. Metadata work is submitted in
batches of at most four, preserving the full roster without an unbounded queue.

A metadata-only live CLI check discovered and selected `qwen3.8:27b-mlx` in
0.117 seconds. Residency was unchanged and no model inference, configuration
mutation or provider installation was performed. Hosted discovery remains
explicitly deferred.

Final validation passed the native governance checks and all 79 tests after
restoring the existing documentation resource-path contracts without weakening
tests. The final live discovery took 0.107 seconds and again left residency
unchanged.

---

*Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) - Orchestrator: **`gpt-6.1-sol`** - Workers: **`none`** - Skill: **`review`** - Date: `2026-11-05`*
