# The Universal 8-Pillar Code Review Framework

This reference defines the formal evaluation rubric used by the **Principal Code Reviewer ("The Gatekeeper")** on Pull Requests and branch diffs. It synthesises **Google's Engineering Practices Code Review Standard**, **Conventional Comments**, and dynamic project-local governance.

## 1. The 8 Evaluation Pillars

### Pillar 1: Design & Architecture Alignment (`DESIGN`)

* **What to Check:**
  * Does the change align with existing architecture and design documents?
  * Are module boundaries respected (e.g. headless core separated from UI/client)?
  * Is the interface minimal, cohesive, and decoupled?
* **Blocking Triggers:**
  * Unauthorised architectural drift or leaking abstractions.
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

## 3. Dual-Model Consensus & Privacy Directives

The code review framework supports two cooperative execution topologies:

### A. Dual-Model Consensus Protocol

* **Primary Architect (Gemini):** Performs whole-repository architectural review, multi-file coherence checks, and synthesises findings across all 8 pillars.
* **Algorithmic Oracle (Local Qwen 2.5 14B):** Cross-examines state transitions, pure mathematical functions, parser state machines, and edge-case boundary conditions under Pillar 2.
* **Prose & Cadence Oracle (Local Mistral NeMo 12B):** Audits human readability, documentation cadence, and explanatory clarity under Pillar 6.

### B. Air-Gapped Privacy Protocol

* **Trigger:** `--local` flag in CLI or `Privacy: on-device` directive in project-local `AGENTS.md`.
* **Security Guarantee:** Completely air-gaps the code review process. No source code diffs or metadata leave your local workstation.
* **On-Device Execution:** Local Qwen 2.5 14B performs code invariant checks, while local Mistral NeMo 12B synthesises the structured review report and Conventional Comments directly on your Apple Silicon GPU.
