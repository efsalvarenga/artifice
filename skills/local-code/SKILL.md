---
name: local-code
version: 1.4.0
description: Delegate bounded algorithmic refactoring, logic analysis, FIM synthesis or unit test generation to an installed local coding model via Ollama.
---

# Local Code Refactoring & Logic (`local-code`)

Use bounded Ollama synthesis for refactoring, logic, tests or FIM through [`vibe-execute`](../vibe-execute/SKILL.md), integrating with [`code-author`](../../agents/code-author/agent.md).

Resolve and export `ARTIFICE_ROOT` from its explicit value when set, otherwise `$HOME/.local/share/artifice` when present, otherwise `$HOME/Repos/artifice`, and resolve links from `ARTIFICE_ROOT/skills/local-code/`. Verify readable `agents`, `skills` and `scripts` directories; stop on failure.

## 1. Discover & Approve

Establish privacy before ingestion. Protected task material **and outputs** stay in local pipelines or verified local sessions, not cloud context.

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" discover --local --workdir "<DIR>"
```

Discovery is metadata-only, without ranking or residency changes. Propose from capability/context/locality evidence, not names. Approve exact tag/fingerprint, requirements and workdir; capture these as `code_model` and `code_identity`. No fixed default: implicit selection needs a role override or one known-compatible candidate.

## 2. Validate & Execute

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" select --task code \
  --model "$code_model" --expect-identity "$code_identity"
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" run "<PROMPT>" \
  --provider ollama --model "$code_model" --expect-identity "$code_identity" \
  --task code --mode bounded_chat --local --workdir "<DIR>" --json
```

Stop on selection/execution failure; never substitute. Explicit tags precede `ARTIFICE_CODE_MODEL`. Use approved `logic`, `fim` or `tdd` requirements and capability/context flags where relevant; see the gateway contract. Task-scoped `--accept-unknown` never bypasses privacy. The runner revalidates identity, capabilities and locality before inference and manages warming. Bounded chat grants no filesystem autonomy, including through `--auto-approve`.

## 3. Verify & Release

Probe 2–3 boundary conditions and verify native Red/Green tests before accepting changes. Record the actual model tag in authorised Git provenance (`Co-authored-by: <MODEL_NAME> <<TAG>@ollama.local>`). Hosted support is deferred, never a fallback.

Retain the existing post-wave [lifecycle policy](../../scripts/check_ollama.py):

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" unload --all
```
