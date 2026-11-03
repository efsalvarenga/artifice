# The Developer Coaching & Framework Scouting Reference

This reference details the operational methodologies, reconnaissance rubrics, and evaluation standards utilised by the **Principal Developer Coach ("The Catalyst")** (`developer-coach`) across the local repository ecosystem and external state-of-the-art sources.

## 1. Core Coaching Rubrics & Evaluation Dimensions

When auditing existing frameworks or evaluating proposed alternatives, the coach assesses six fundamental dimensions:

### Dimension 1: Velocity & Cognitive Overhead (`VELOCITY`)

* **Assessment:** Does the framework enable fast iteration, or does it demand excessive cognitive overhead and ceremony for trivial additions?
* **Scouting Indicators:** How many files must be touched to add a single feature or module? Is there boilerplate that can be automated?

### Dimension 2: Architectural Integrity & State Isolation (`INTEGRITY`)

* **Assessment:** Does the architecture enforce clear boundaries and single-direction data flow?
* **Scouting Indicators:** Are core business models strictly isolated from external presentation layers or volatile third-party APIs?

### Dimension 3: Type Safety & Compiler Assistance (`TYPES`)

* **Assessment:** Does the codebase harness strict static typing to make invalid states unrepresentable?
* **Scouting Indicators:** Discriminated unions, immutable data structures, exhaustive pattern matching, and runtime schema validators.

### Dimension 4: Verification Rigour & Test Ergonomics (`TESTABILITY`)

* **Assessment:** How straightforward is it to write and maintain tests?
* **Scouting Indicators:** Clean test fixtures, fast execution, and deterministic assertions over fragile mocking.

### Dimension 5: Ecosystem Harmony & Portability (`PORTABILITY`)

* **Assessment:** Can utilities, scripts, and architectural concepts be shared cleanly across sibling repositories adjacent to the confirmed target?
* **Scouting Indicators:** Shared script standards, consistent configuration conventions, and modular interoperability.

### Dimension 6: Governance Ergonomics (`GOVERNANCE`)

* **Assessment:** Does the framework make adherence to guidelines (British English, Markdown cleanliness, Conventional Commits) natural rather than punitive?
* **Scouting Indicators:** Pre-commit hooks, automated formatting, linting rules, and clear diagnostics.

## 2. Reconnaissance Guide: Sibling Ecosystem Scouting

When the current client's tools and permissions allow adjacent repository inspection, use the confirmed target's parent directory. When scouting for patterns, follow these repo-specific intelligence maps:

* **`arete` & `arete-engine`:** Deep functional domain modelling, strict typing, Obsidian integration, CLI automation, and continuous verification.
* **`emergent`:** Headless simulation purity, pure reducers, EGM governance, strict TypeScript, and end-to-end perception tests.
* **`charged` & `hostile`:** Game systems, procedural generation, spatial topologies, combat state reducers, and git hooks.
* **`oude-mechanismen`:** Mechanical state machines, deterministic clockwork simulations, versioning conventions, and campaign archival pipelines.
* **`forge`:** Scaffolding, repository templating, operational runbooks (`OPERATIONS.md`), and reading radar research.

## 3. External Scouting via Web Search

When scouting external open-source ecosystems, prioritise authoritative, modern sources:

* Modern language and runtime specifications (TypeScript 5.x+, Python 3.12+, modern Rust/Go).
* Functional and reactive design patterns (algebraic data types, optics, state charts).
* Sub-second bundling, fast snapshot testing, and Playwright automation.
