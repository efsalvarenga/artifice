# Artifice

A curated, version-controlled collection of global agent skills, procedures, and workflows for Google Antigravity.

*Artifice* (English: the craft, the ingenious device; Portuguese *artífice*: the master craftsman, the architect of a work) serves as the centralised repository of capabilities mounted globally across all local development projects.

## Directory Structure

```text
artifice/
├── README.md
├── TASKS.md                 # Roadmap board & incoming tooling feedback inbox
├── agents/
│   ├── code-author/         # Principal Code Author ("The Craftsman")
│   ├── code-reviewer/       # Principal Code Reviewer ("The Gatekeeper")
│   └── developer-coach/     # Principal Developer Coach ("The Catalyst")
├── docs/
│   ├── designs/             # Elephant design specifications (001_*, 002_*)
│   └── reviews/             # Adversarial Goldfish reviews
├── scripts/
│   ├── check_ollama.py      # Ollama residency, lifecycle & wave-leasing controller
│   ├── lint.py              # Unified static governance linter (Markdown, YAML, links, Core Diet)
│   ├── lint.sh              # Execution wrapper for lint.py
│   ├── validate_egm.py      # Portable EGM contract validator (--spec support)
│   └── build_review_dossier.py # Compact repository invariant digest compiler
├── skills/
│   ├── spec-egm/            # Elephant-Goldfish Model specification workflow & workshops
│   ├── review/              # Universal code & architecture review (PR, branch, file, doc)
│   ├── coach-frameworks/    # Framework evaluation & ecosystem DX coaching
│   └── local-code/          # Algorithmic refactoring & tests via local Qwen 2.5 Coder
└── tests/
    └── test_validate_egm.py # Automated unit tests for EGM contract validation
```

## Available Agents

### 1. `code-author`

* **Persona:** Principal Code Author ("The Craftsman")
* **Role:** Primary implementation agent adhering to contract-first Test-Driven Development (TDD), minimal deterministic code, model-attributed Git commits, and pre-review green baseline gating.

### 2. `code-reviewer`

* **Persona:** Principal Code Reviewer ("The Gatekeeper")
* **Role:** Universal evaluation of Pull Requests, branch diffs, single files, or architectural design specifications using the 8-Pillar Framework, Conventional Comments, and hybrid offloading.

### 3. `developer-coach`

* **Persona:** Principal Developer Coach ("The Catalyst")
* **Role:** Strategic framework evaluation, ecosystem scouting across `~/Repos/*`, developer ergonomics coaching, and tooling inbox triage using the 4-Test Lesson Acceptance Gate.

## Available Skills

### 1. `spec-egm`

* **Trigger:** `/spec-egm [init | review | validate]`
* **Role:** Orchestrates the Elephant-Goldfish Model (EGM) specification-driven development workflow: pre-spec empirical reconnaissance, collaborative interactive Design Workshops, no-code Elephant design specs, zero-context Goldfish reviews, and automated contract validation.

### 2. `review`

* **Trigger:** `/review [--local] [PR_NUMBER | branch | <file_or_doc_path>]`
* **Persona:** Principal Code Reviewer ("The Gatekeeper")
* **Role:** Universal evaluation of Pull Requests, branch diffs, single files, or architectural design specifications using the 8-Pillar Framework and Conventional Comments.
* **Hybrid Offloading:** Orchestrated by Gemini, decomposing the review into orthogonal streams: delegating Pillar 2 logic fuzzing to local `qwen2.5-coder:14b` and Pillar 6 documentation review to local `mistral-nemo:12b` via wave-leased Ollama memory.
* **Offline Privacy Mode:** Supports 100% on-device air-gapped review via the `--local` flag or repository privacy directives.

### 3. `coach-frameworks`

* **Trigger:** `/coach-frameworks`
* **Persona:** Principal Developer Coach ("The Catalyst")
* **Role:** Strategic framework evaluation, ecosystem scouting across `~/Repos/*`, developer ergonomics coaching, and tooling inbox triage using the 4-Test Lesson Acceptance Gate.

### 4. `local-code`

* **Trigger:** `/local-code`
* **Backend:** Local `qwen2.5-coder:14b` (fallback `qwen2.5:14b`) running via Ollama.
* **Role:** Deep algorithmic refactoring, unit test generation, Fill-in-the-Middle (FIM) synthesis, and boundary edge-case probing with wave-leased memory management.

## Core Scripts

* `./scripts/check_ollama.py`: Ollama lifecycle and residency manager providing sub-100ms health checks, model selection, wave-leasing (`keep_alive: 5m`), and memory cache flushing.
* `./scripts/lint.py`: Unified static governance linter auditing Markdown heading cleanliness, YAML frontmatter syntax, relative link integrity, and Core Diet ceilings across repositories.
* `./scripts/lint.sh`: Execution wrapper delegating directly to `lint.py`.
* `./scripts/validate_egm.py`: Validates EGM specification sections, matching Goldfish reviews, and approval verdicts with targeted `--spec` validation.
* `./scripts/build_review_dossier.py`: Extracts and formats intentional repository invariants for local review models.

## Integration with Antigravity

Mounted globally inside `~/.gemini/config/skills.json`:

```json
{
  "entries": [
    {
      "path": "~/Repos/artifice/skills"
    }
  ]
}
```
