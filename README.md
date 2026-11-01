# Artifice

A curated, version-controlled collection of global agent skills, procedures, and workflows for Google Antigravity.

*Artifice* (English: the craft, the ingenious device; Portuguese *artífice*: the master craftsman, the architect of a work) serves as the centralised repository of capabilities mounted globally across all local development projects.

## Directory Structure

```text
artifice/
├── README.md
├── agents/
│   ├── code-reviewer/       # Principal Code Reviewer ("The Gatekeeper")
│   └── developer-coach/     # Principal Developer Coach ("The Catalyst")
└── skills/
    ├── local-code/          # Algorithmic refactoring & tests via local Qwen 2.5 14B
    ├── local-review/        # Architectural review & prose via local Mistral NeMo 12B
    ├── review-pr/           # Universal 8-pillar code review & Conventional Comments
    └── coach-frameworks/    # Framework evaluation & ecosystem DX coaching
```

## Available Skills

### 1. `review-pr`

* **Trigger:** `/review-pr [--local]`
* **Persona:** Principal Code Reviewer ("The Gatekeeper")
* **Role:** Universal Pull Request and branch diff code review combining Google Engineering Practices, Conventional Comments, automated verification execution, and dynamic ingestion of project-local `AGENTS.md` rules.
* **Dual-Model Consensus & Privacy:** Employs Gemini for global architectural synthesis while delegating dense algorithmic fuzzing to local Qwen 2.5 14B and prose review to local Mistral NeMo 12B. Supports 100% on-device air-gapped reviews via the `--local` flag or repository privacy directives.

### 2. `coach-frameworks`

* **Trigger:** `/coach-frameworks`
* **Persona:** Principal Developer Coach ("The Catalyst")
* **Role:** Strategic framework evaluation, ecosystem scouting across `~/Repos/*`, and developer ergonomics coaching. Delivers adaptive recommendations in chat, Antigravity artifact canvases, or structured RFC proposals.

### 3. `local-code`

* **Trigger:** `/local-code`
* **Backend:** Local `qwen2.5:14b` running via Ollama.
* **Role:** Deep algorithmic refactoring, unit test generation, and complex logical analysis.

### 4. `local-review`

* **Trigger:** `/local-review`
* **Backend:** Local `mistral-nemo:12b` running via Ollama.
* **Role:** Long-context architectural reviews, code diff evaluation, and technical documentation synthesis.

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
