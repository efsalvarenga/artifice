# Artifice

A curated, version-controlled collection of shared agent skills, procedures, and workflows for Google Antigravity and GitHub Copilot.

*Artifice* (English: the craft, the ingenious device; Portuguese *artífice*: the master craftsman, the architect of a work) serves as the centralised repository of capabilities mounted globally across all local development projects.

## Directory Structure

```text
artifice/
├── README.md
├── TASKS.md                      # Roadmap board & incoming tooling feedback inbox
├── agents/
│   ├── code-author/              # Principal Code Author ("The Craftsman")
│   ├── code-reviewer/            # Principal Code Reviewer ("The Gatekeeper")
│   └── developer-coach/          # Principal Developer Coach ("The Catalyst")
├── integrations/
│   └── copilot/agents/           # Thin Copilot adapters delegating to canonical roles
├── docs/
│   ├── designs/                  # Elephant design specifications (001_*, 002_*, 003_*)
│   └── reviews/                  # Adversarial Goldfish reviews
├── scripts/
│   ├── check_ollama.py           # Ollama residency, selection & wave-leasing controller
│   ├── install_copilot.sh        # Non-overwriting personal Copilot symlink installer
│   ├── lint.py                   # Unified static governance & Core Diet linter
│   ├── lint.sh                   # Execution wrapper for lint.py
│   ├── validate_egm.py           # Portable EGM contract validator (--spec support)
│   └── build_review_dossier.py   # Compact repository invariant digest compiler
├── skills/
│   ├── spec-egm/                 # Elephant-Goldfish Model specification workflow
│   ├── review/                   # Universal 8-Pillar code & architecture review
│   ├── coach-frameworks/         # Framework evaluation & ecosystem DX coaching
│   └── local-code/               # Algorithmic refactoring & tests via local Ollama
└── tests/                        # Standard-library unit & black-box installer tests
```

## Available Agents

### 1. `code-author`

* **Persona:** [Principal Code Author ("The Craftsman")](agents/code-author/agent.md)
* **Role:** Primary implementation agent adhering to contract-first Test-Driven Development (TDD), minimal deterministic code, model-attributed Git commits, and pre-review green baseline gating.

### 2. `code-reviewer`

* **Persona:** [Principal Code Reviewer ("The Gatekeeper")](agents/code-reviewer/agent.md)
* **Role:** Universal evaluation of Pull Requests, branch diffs, single files, or architectural design specifications using the 8-Pillar Framework, Conventional Comments, and hybrid offloading.

### 3. `developer-coach`

* **Persona:** [Principal Developer Coach ("The Catalyst")](agents/developer-coach/agent.md)
* **Role:** Strategic framework evaluation, ecosystem scouting across sibling repositories, developer ergonomics coaching, and tooling inbox triage using the 4-Test Lesson Acceptance Gate.

## Available Skills

### 1. `spec-egm`

* **Trigger:** `/spec-egm [init | review | validate]`
* **Role:** Orchestrates the [Elephant-Goldfish Model (EGM)](skills/spec-egm/SKILL.md) workflow: pre-spec empirical reconnaissance, front-loaded Grill-Me workshops, no-code Elephant specs, zero-context Goldfish reviews, and mechanical contract validation.

### 2. `review`

* **Trigger:** `/review [--local] [PR_NUMBER | branch | <file_or_doc_path>]`
* **Role:** [Universal 8-Pillar evaluation](skills/review/SKILL.md) using the current client orchestrator with optional wave-leased Ollama worker streams (`code_model` + `prose_model`) and strict `--local` on-device privacy mode.

### 3. `coach-frameworks`

* **Trigger:** `/coach-frameworks`
* **Role:** [Strategic framework evaluation](skills/coach-frameworks/SKILL.md), sibling-repository scouting, and developer ergonomics coaching filtered through the 4-Test Lesson Acceptance Gate.

### 4. `local-code`

* **Trigger:** `/local-code`
* **Role:** [Bounded algorithmic refactoring](skills/local-code/SKILL.md), unit test generation, and Fill-in-the-Middle (FIM) synthesis via an installed Ollama coding model.

## Core Scripts & Verification

* `./scripts/check_ollama.py`: Ollama residency and selection controller (`status`, `select --task <task>`, `warm <model> --lease 5m`, `unload --all`). Honours `ARTIFICE_CODE_MODEL` and `ARTIFICE_PROSE_MODEL` overrides when set, defaulting to `qwen2.5-coder:14b` / `qwen2.5:14b` for code and `mistral-nemo` for prose.
* `./scripts/lint.sh` (`./scripts/lint.py`): Unified static governance linter auditing Markdown heading cleanliness, YAML frontmatter, Copilot adapter contracts, relative links, Core Diet line/word ceilings, EGM contracts, and Bash syntax.
* `./scripts/validate_egm.py`: Validates EGM specification sections and matching approved Goldfish reviews (`--spec <id>`).
* `./scripts/build_review_dossier.py`: Compiles intentional repository invariants for review streams.
* `python3 -m unittest discover -s tests`: Executes the dependency-free unit and disposable-home installer test suite.

## Integration with Antigravity

Mounted globally inside `~/.gemini/config/skills.json` (with agent symlinks in `~/.gemini/config/agents/`):

```json
{
  "entries": [
    {
      "path": "~/Repos/artifice/skills"
    }
  ]
}
```

Shared roles and skills resolve `ARTIFICE_ROOT` via explicit `ARTIFICE_ROOT`, `$HOME/.local/share/artifice` when present, or `$HOME/Repos/artifice`.

## Integration with Copilot

Install user-level directory symlinks once from any working directory:

```bash
bash scripts/install_copilot.sh
bash scripts/install_copilot.sh --check
```

The installer derives the physical checkout from its own path, refuses to overwrite existing files, directories, or mismatched links, rolls back its own partial changes on failure, and creates three symlinks:

```text
$HOME/.local/share/artifice                  -> physical Artifice checkout
${COPILOT_HOME:-$HOME/.copilot}/agents       -> $HOME/.local/share/artifice/integrations/copilot/agents
${COPILOT_HOME:-$HOME/.copilot}/skills       -> $HOME/.local/share/artifice/skills
```

Thin adapters in `integrations/copilot/agents/` configure Copilot tool permissions and load the canonical `agents/<role>/agent.md` body without duplicating prompts. Start a fresh Copilot chat or reload the window after installation if discovery is stale.
