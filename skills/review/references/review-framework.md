# The Universal 8-Pillar Code Review Framework

This reference defines the formal evaluation rubric used by the **Principal Code Reviewer ("The Gatekeeper")** on Pull Requests and branch diffs. It synthesises **Google's Engineering Practices Code Review Standard**, **Conventional Comments**, and dynamic project-local governance.

## 1. The 8 Evaluation Pillars

### Pillar 1: Design & Architecture Alignment (`DESIGN`)

* **What to Check:**
  * **EGM Specification Compliance:** Does the implementation faithfully fulfil the active approved specification in `docs/designs/`?
  * Are all state schemas, invariants, and edge cases defined in the specification implemented?
  * Are module boundaries respected (e.g. headless core separated from UI/client)?
  * Is the interface minimal, cohesive, and decoupled?
* **Blocking Triggers:**
  * Architectural drift or deviation from the approved `docs/designs/` specification.
  * Omission of promised specification invariants or edge cases.
  * Unauthorised scope expansion beyond the approved specification.
  * Direct coupling between domain engines and presentation layers.

### Pillar 2: Functionality & Invariants (`FUNCTIONALITY`)

* **What to Check:**
  * Are state transitions safe, correct, and idempotent where required?
  * Are boundary conditions (null/empty inputs, capacity limits, collections) protected?
  * Are operations deterministic across environments (no unseeded randomness or clock drift in core logic)?
* **Active Edge-Case Probing ("Pry There"):**
  * Explicitly identify 2–3 concrete boundary edge cases in the changed code (e.g. empty collections, zero/negative inputs, capacity limits, race conditions, or unhandled exceptions).
  * Pry into how the implementation behaves on those inputs and assert whether automated tests explicitly cover them.
* **Blocking Triggers:**
  * Data corruption, uncaught edge cases, or unintentional state mutation.

### Pillar 3: Complexity & Maintainability (`COMPLEXITY`)

* **What to Check:**
  * Are functions small, cohesive, and single-purpose?
  * Is control flow readable with early returns?
  * Is the code free of speculative generality or dead code?
* **Blocking Triggers:**
  * Over-engineered abstractions, excessive nesting, or unreachable branches.

### Pillar 4: Automated Tests & Verification (`TESTS`)

* **What to Check:**
  * Are unit and integration tests provided for every new code path and edge case?
  * Do existing and new test suites pass cleanly?
  * Do project verification scripts (`npm test`, `pytest`, `cargo test`, `./scripts/verify*`) exit with zero errors?
* **Blocking Triggers:**
  * Any failing test or missing test coverage for critical business logic.

### Pillar 5: Naming & Domain Clarity (`NAMING`)

* **What to Check:**
  * Do variable and type names match the project's ubiquitous domain vocabulary?
  * Are boolean predicates named unambiguously (`isValid`, `hasPermission`)?
* **Blocking Triggers:**
  * Ambiguous, deceptive, or contradictory naming.

### Pillar 6: Comments & Documentation (`COMMENTS_DOCS`)

* **What to Check:**
  * Do comments document *why* an invariant exists rather than restating the syntax?
  * Are relevant markdown documentation files updated to match the implementation?
  * Does every Markdown heading (`#`, `##`, `###`, `####`) leave an empty blank line immediately beneath it?
* **Blocking Triggers:**
  * Stale documentation, misleading comments, or Markdown heading cleanliness violations.

### Pillar 7: Style, Type Safety & Git Hygiene (`STYLE_TYPES`)

* **What to Check:**
  * Are type definitions strict (no unapproved `any` or loose casts)?
  * Does the code adhere to the project's linter and formatter standards?
  * Is the branch isolated (not committing directly to `main`)?
* **Blocking Triggers:**
  * Type-safety bypasses, lint errors, or direct unreviewed commits to `main`.

### Pillar 8: Localisation & Governance Compliance (`LORE_LOCALISATION`)

* **What to Check:**
  * Is all written text (comments, docs, UI strings, commit messages) in **British English**?
  * If external LLM APIs are invoked, do their prompts mandate British English output?
  * Are world lore and creative elements authored or approved by humans (no AI-hallucinated worldbuilding)?
* **Blocking Triggers:**
  * American English spelling in documentation or user-facing copy.
  * Autonomous invention of major creative lore.

## 2. Conventional Comments Specification

Every review finding must follow the structured Conventional Comments pattern:

```text
<label> (<severity>, <pillar>): [file:line](file:///path#Lline) — <Subject>

<Discussion/Recommendation>
```

| Label | Intent | Typical Severity |
| :--- | :--- | :--- |
| `issue` | Highlights a functional defect, invariant breach, or rule violation. | `blocking` |
| `suggestion` | Proposes a concrete refactoring, clearer type signature, or test improvement. | `blocking` or `non-blocking` |
| `question` | Seeks clarification on intent or implementation choices. | `non-blocking` |
| `thought` | Shares a perspective or architectural idea for future consideration. | `non-blocking` |
| `nitpick` | Small stylistic preference that does not block merging. | `non-blocking` |
| `praise` | Celebrates elegant code, robust tests, or excellent abstractions. | `non-blocking` |

## 3. Discovery-Led Workers & Privacy Directives

The [gateway](../../vibe-execute/SKILL.md) and [review workflow](../SKILL.md) use the same live inventory and identity validator. Discovery is metadata-only: no ranking, warming, inference, unloading or configuration changes. This Ollama phase permits only configured loopback endpoints and verified on-device inference, even without `--local`. Remote endpoints are diagnosed without contact; cloud-backed or unknown execution locality blocks dispatch. Residency is provisional evidence, not proof of capacity or readiness.

Hosted Mistral/Vibe is deferred. An absent CLI is `unavailable`; a present CLI is `unsupported_version` with `HOSTED_DISCOVERY_DEFERRED`, not a selectable engine. Do not inspect hosted configuration/authentication/catalogues or invent hosted choices.

### A. Shared Selection Contract

1. Establish task requirements and privacy before protected ingestion. Refresh inventory for the task; disclose partial discovery and handle its non-zero status explicitly.
2. Propose at most three eligible choices from capability, context and locality evidence. Do not use tag names as quality evidence. One discovered model may serve both code and prose roles.
3. Confirm concrete tags, fingerprints, requirements, mode and working directory. Reuse explicit requests or still-valid task approval.
4. Validate each assignment with `check_ollama.py select --task ROLE [--model EXACT_TAG] [--expect-identity HASH] [--accept-unknown]`. Exact CLI models precede `ARTIFICE_CODE_MODEL` / `ARTIFICE_PROSE_MODEL`. Without an explicit choice, require a role override or one known-compatible candidate, never a preferred-name list or list-first choice.
5. Accept selection only on exit `0` with non-empty `model`, `identity_fingerprint` and `reference`; success also preserves `resident` and `fallback: null`. Failure exits `2` with an explicit reason and `fallback: null`. Empty, missing or incompatible overrides fail rather than substituting.
6. Preserve exact tags through warming, inference and provenance. Revalidate identity, requirements and locality before inference; endpoint, alias or digest drift requires renewed approval. Use gateway `run`, not an unchecked raw HTTP inference path.

Known-incompatible models are excluded. Explicit task-scoped `--accept-unknown` may accept unknown suitability, never known incompatibility or a privacy/locality exception. A role override names an identity; it does not implicitly accept unknown metadata. Tool capability cannot create a missing harness: Ollama supports `bounded_chat` only, not filesystem autonomy through `--auto-approve`.

Inventory references are `provider/source/model`, split at the first two slashes only; preserve model namespaces, case and tag suffixes. Compound `recommended_engine` values are proposals from that inventory, not dispatch authority. Validate and approve each concrete wave engine/fingerprint before dispatch, retain `--local` throughout and run native checks between waves.

### B. Optional Worker Protocol

* **Current Orchestrator:** Covers all eight pillars directly when appropriate, filters false positives against repository invariants and synthesises Conventional Comments.
* **Code Worker (`code_model`):** Cross-examines state transitions, pure functions, parsers and boundary conditions.
* **Prose Worker (`prose_model`):** Audits readability, documentation and explanatory clarity.
* Warm only successfully selected, non-empty tags. Surface selection/warming failures on stderr before clearing an optional worker; disclose omissions and continue directly with the native harness where permitted.
* Sign only with actual workers and exact references, not proposed or failed assignments. If one model fills both roles, record that fact without inventing a second model.

### C. Required On-Device Protocol

* **Trigger:** `--local`, `Privacy: on-device`, or `Review: local-only` in applicable policy metadata.
* **Privacy Boundary:** Protected prompts, source, diffs and generated outputs must not enter cloud model context or leave the device. Metadata discovery does not make a cloud conversation air-gapped.
* **Eligibility:** Require configured loopback transport and verified on-device execution evidence. Cloud-backed and unknown execution locality cannot satisfy strict policy; a loopback proxy is not proof of on-device inference.
* **Execution:** Use local shell/Ollama pipelines or a verified local session: `code_model` covers Pillars 2, 3, 5, 7; `prose_model` covers 1, 6, 8 and synthesis. Native checks cover Pillar 4. One model may fill both required assignments.
* Select and warm both role assignments before protected ingestion. If either fails, stop before reading the target; no cloud fallback or privacy waiver. `--local` governs triage and every wave regardless of generated recommendations.
* Preserve the existing declared post-wave unload policy; discovery never mutates models or evicts other workloads.
