# Goldfish Review: Copilot Symlink Integration

**Review Target:** [003_copilot_symlink_integration.md](../designs/003_copilot_symlink_integration.md)
**Reviewer:** Explore subagent, independent Goldfish design review
**Date:** 2026-11-03
**Verdict:** Approved

---

## 1. Executive Summary

The independent reviewer found the architecture sound but requested concrete contracts for adapter loading, Antigravity coexistence, and cross-directory resource resolution. It also requested smaller clarifications for rollback ownership and the EGM validator. This report condenses the returned findings; it does not change the reviewer's verdict or claim approval of the subsequent revision.

The initial draft had explicit human approval before review. The developer subsequently approved the clarified design and an independent follow-up review approved it on 2026-11-03. The historical findings below retain the initial review's context; implementation now awaits targeted validation, not another human design decision.

## 2. Invariant & Edge-Case Probing

| ID | Area | Finding | Reviewer Severity |
| --- | --- | --- | --- |
| PROBE-01 | Adapter format and loading | Specify Markdown/YAML structure and the actual mechanism for loading the canonical body; do not imply an include feature exists. | High |
| PROBE-02 | Antigravity coexistence | State who creates the anchor, whether Gemini registration changes, and how Antigravity works without installation. | High |
| PROBE-03 | Resource resolution | Define where the fallback protocol lives and how a physical definition path yields a checkout root. | High |
| PROBE-04 | Destination recheck | Distinguish a best-effort check from concurrency protection. | Medium |
| PROBE-05 | Rollback ownership | Define current-invocation tracking and distinguish older artefacts from newly created paths. | Medium |
| PROBE-06 | EGM gate | Define the acronym, command, and limits of automated validation. | Low |

## 3. Detailed Critiques & Blind Spots

### 3.1 Data Schema Completeness

The original specification named adapter fields and role-loading behaviour but did not show a complete adapter. It needed to state explicitly that loading is a natural-language instruction to read a file with a tool, not a parser feature, unsupported field, or automatic Markdown include.

### 3.2 State Mutation & Deterministic Consistency

The resource anchor and fallback needed explicit ownership and physical-path semantics. The installer must leave Antigravity configuration untouched. Current-invocation rollback ownership and the non-atomic nature of rechecks needed clarification.

### 3.3 Testability & Verification Strategy

Filesystem tests cannot demonstrate that Copilot follows an adapter's loading instruction. Live tool activity remains essential. Likewise, Antigravity-only resource resolution must be tested without an installed anchor. An unavailable client must be recorded as unverified, not passed.

## 4. Required Revisions

1. Specify the adapter file format and give a complete short example with tool permissions and explicit role-body loading.
2. Explain that only the Copilot installer creates the shared anchor, registrations are independent, and existing Antigravity installations retain an anchor-free fallback.
3. Place a concrete resource protocol in the shared entry-point bodies, including physical path resolution, validation, and actionable failure behaviour.
4. Track newly created links, expected targets, and directories in in-process arrays; reverse only current-invocation mutations on failure.
5. Define the existing targeted EGM validator and clarify that it is separate from human approval.

The Elephant revision now addresses these points in the specification. That is an author's response, not an independent finding that the revisions are sufficient. The reviewer's request for a large adapter example is met with a minimal complete example rather than a duplicated workflow body.

## 5. Recommendation & Sign-Off

* **Initial verdict:** Revisions Required.
* **Follow-up verdict:** Approved, returned by a fresh Explore subagent on 2026-11-03 after reading only the clarified specification and Goldfish template.
* **Follow-up assessment:** Explicit Markdown/YAML adapter format, tool-mediated role loading, independent client registrations, physical resource resolution, in-process rollback ownership, and EGM validation limits resolve the original concerns. The design is implementable in standard Bash without material changes.
* **Remaining limitations:** Concurrent installation is unsupported, rollback is best-effort, and filesystem success does not prove live discovery or instruction loading. Antigravity live acceptance remains required or explicitly outstanding.
* **Execution record:** Targeted EGM validation, implementation, temporary-home tests, and local activation subsequently completed. On 2026-11-03 the developer authorised feature-branch commits, push, and PR creation; merging remains outside that authorisation. See the specification's acceptance evidence for verified and outstanding client checks.
