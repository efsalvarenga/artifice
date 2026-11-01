# Artifice

A curated, version-controlled collection of global agent skills, procedures, and workflows for Google Antigravity.

*Artifice* (English: the craft, the ingenious device; Portuguese *artífice*: the master craftsman, the architect of a work) serves as the centralised repository of capabilities mounted globally across all local development projects.

## Directory Structure

```text
artifice/
├── README.md
└── skills/
    ├── local-code/       # Algorithmic refactoring & tests via local Qwen 2.5 14B
    └── local-review/     # Architectural review & prose via local Mistral NeMo 12B
```

## Available Skills

### 1. `local-code`
* **Trigger:** `/local-code`
* **Backend:** Local `qwen2.5:14b` running via Ollama.
* **Role:** Deep algorithmic refactoring, unit test generation, and complex logical analysis.

### 2. `local-review`
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
