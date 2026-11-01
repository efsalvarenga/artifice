# Artifice

A curated, version-controlled collection of global agent skills, procedures, and workflows for Google Antigravity.

*Artifice* (English: the craft, the ingenious device; Portuguese *artífice*: the master craftsman, the architect of a work) serves as the centralised repository of capabilities mounted globally across all local development projects.

## Directory Structure

```text
artifice/
├── README.md
├── TASKS.md                 # Roadmap board & incoming tooling feedback inbox
├── agents/
│   ├── code-reviewer/       # Principal Code Reviewer ("The Gatekeeper")
│   └── developer-coach/     # Principal Developer Coach ("The Catalyst")
├── scripts/
│   ├── lint.sh              # Static governance linter (Markdown, YAML, links, Core Diet)
│   ├── verify.sh            # Continuous verification orchestrator (lint + unit tests)
│   ├── validate_egm.py      # Portable EGM contract validator
│   ├── check_decisions.py   # Decision ledger linter & active-only auditor
│   ├── build_review_dossier.py # Compact repository invariant digest compiler
│   └── sabotage_check.py    # Worktree-isolated mutation test verification
├── skills/
│   ├── spec-egm/            # Elephant-Goldfish Model specification workflow
│   ├── coordinate-fronts/   # Multi-front wave coordination & decision ledgers
│   ├── review-pr/           # Universal 8-pillar code review & Conventional Comments
│   ├── coach-frameworks/    # Framework evaluation & ecosystem DX coaching
│   ├── local-code/          # Algorithmic refactoring & tests via local Qwen 2.5 14B
│   └── local-review/        # Architectural review & prose via local Mistral NeMo 12B
└── tests/
    └── test_scripts.py      # Automated python unit test suite
```

## Available Skills

### 1. `spec-egm`

* **Trigger:** `/spec-egm [init | review | validate]`
* **Role:** Orchestrates the Elephant-Goldfish Model (EGM) specification-driven development workflow: pre-spec empirical reconnaissance, no-code Elephant design specs, zero-context Goldfish reviews, and contract validation.

### 2. `coordinate-fronts`

* **Trigger:** `/coordinate-fronts [plan | status | audit]`
* **Role:** Multi-front wave coordinator activated when 3+ independent tasks stack up or an autonomous wave begins. Features upfront opening rosters (*pauta de abertura*), pilot block dispatch, independent disk audits (*autorrelato não se aceita*), 3-tier decision ledgers, pairwise seam audits, and closing review passes.

### 3. `review-pr`

* **Trigger:** `/review-pr [--local] [PR or branch]`
* **Persona:** Principal Code Reviewer ("The Gatekeeper")
* **Role:** Universal Pull Request and branch diff code review combining Google Engineering Practices, Conventional Comments, automated verification execution, and dynamic ingestion of project-local `AGENTS.md` rules.
* **Dual-Model Consensus & Privacy:** Employs Gemini for global architectural synthesis while delegating dense algorithmic fuzzing to local Qwen 2.5 14B and prose review to local Mistral NeMo 12B. Supports 100% on-device air-gapped reviews via the `--local` flag or repository privacy directives.

### 4. `coach-frameworks`

* **Trigger:** `/coach-frameworks`
* **Persona:** Principal Developer Coach ("The Catalyst")
* **Role:** Strategic framework evaluation, ecosystem scouting across `~/Repos/*`, developer ergonomics coaching, and tooling inbox triage using the 4-Test Lesson Acceptance Gate.

### 5. `local-code`

* **Trigger:** `/local-code`
* **Backend:** Local `qwen2.5:14b` running via Ollama.
* **Role:** Deep algorithmic refactoring, unit test generation, and complex logical analysis paired with `sabotage_check.py` for test hardening.

### 6. `local-review`

* **Trigger:** `/local-review`
* **Backend:** Local `mistral-nemo:12b` running via Ollama.
* **Role:** Long-context architectural reviews, code diff evaluation, and technical documentation synthesis armed with `build_review_dossier.py`.

## Core Verification Scripts

* `./scripts/lint.sh`: Audits Markdown heading cleanliness, table formatting, YAML frontmatter syntax, relative link integrity, and Core Diet ceilings (140 lines on global `AGENTS.md`, 180 lines on `SKILL.md`).
* `./scripts/verify.sh`: Continuous verification orchestrator running `./scripts/lint.sh` and the automated Python unit test suite.
* `./scripts/sabotage_check.py`: Applies targeted mutations to boundary conditions and asserts tests turn red (`KILLED`), exposing blind spots.
* `./scripts/validate_egm.py`: Validates EGM specification sections, matching Goldfish reviews, and approval verdicts.

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
