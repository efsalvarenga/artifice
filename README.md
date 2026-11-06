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
│   ├── designs/                  # Approved design specifications
│   └── reviews/                  # Adversarial Goldfish reviews
├── scripts/
│   ├── check_ollama.py           # Ollama residency, selection & wave-leasing controller
│   ├── install_copilot.sh        # Non-overwriting personal Copilot symlink installer
│   ├── lint.py                   # Unified static governance & Core Diet linter
│   ├── lint.sh                   # Execution wrapper for lint.py
│   ├── model_inventory.py        # Shared metadata inventory & identity validation
│   ├── vibe_execute.py           # Discovery, task classification & exact dispatch
│   ├── validate_egm.py           # Portable EGM contract validator (--spec support)
│   └── build_review_dossier.py   # Compact repository invariant digest compiler
├── skills/
│   ├── spec-egm/                 # Elephant-Goldfish Model specification workflow
│   ├── review/                   # Universal 8-Pillar code & architecture review
│   ├── coach-frameworks/         # Framework evaluation & ecosystem DX coaching
│   ├── vibe-execute/             # Discovery-led model proposals & execution gateway
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

### 5. `vibe-execute`

* **Trigger:** `/vibe-execute [discover | classify | triage | run]`
* **Role:** [Discover, filter, propose, confirm, execute](skills/vibe-execute/SKILL.md): metadata-led model selection across local Ollama and hosted Mistral, exact identity-bound dispatch and compound execution.

## Core Scripts & Verification

* `./scripts/vibe_execute.py`: Shared discovery, requirements-only classification, approved exact-model execution and compound triage. No static model defaults or automatic fallback.
* `./scripts/check_ollama.py`: Ollama residency and selection controller (`status`, `select --task <role>`, `warm <model> --lease 5m`, `unload --all`). Exact CLI models take precedence over `ARTIFICE_CODE_MODEL` / `ARTIFICE_PROSE_MODEL` role overrides. Without an explicit choice, selection requires an override or one known-compatible candidate; ambiguity fails rather than taking the first model.
* `./scripts/lint.sh [target]` (`./scripts/lint.py`): Unified governance runner auditing Markdown heading cleanliness, YAML/adapter frontmatter, relative links, Core Diet ceilings, EGM contracts, and Bash syntax. The target defaults to the current directory; Artifice's unit suite runs only when that target resolves to this checkout.
* `./scripts/validate_egm.py`: Validates EGM specification sections and matching approved Goldfish reviews (`--spec <id>`).
* `./scripts/build_review_dossier.py`: Compiles intentional repository invariants for review streams.

## Discovery & Model Approval

[Design 004](docs/designs/004_discovery_driven_model_proposals.md) delivers Ollama discovery now, with a [direct contract review](docs/reviews/004_discovery_driven_model_proposals_review.md), not a claim of independent zero-context review. The assistant proposes at most three choices from live evidence; the developer approves the concrete model, requirements, execution mode and working directory before inference. Reuse an explicit request or still-valid task approval. Dispatch revalidates the exact identity fingerprint, capabilities and locality; changed identities or failures never trigger substitution.

Resolve and export `ARTIFICE_ROOT`: use its explicit value when set, otherwise `$HOME/.local/share/artifice` when present, otherwise `$HOME/Repos/artifice`. Verify readable `agents`, `skills` and `scripts` directories before invoking shared scripts. These commands inspect live metadata only:

```bash
if [ "${ARTIFICE_ROOT+x}" != x ]; then
  if [ -d "$HOME/.local/share/artifice" ]; then
    ARTIFICE_ROOT="$HOME/.local/share/artifice"
  else
    ARTIFICE_ROOT="$HOME/Repos/artifice"
  fi
fi
for resource in agents skills scripts; do
  if [ ! -d "$ARTIFICE_ROOT/$resource" ] || [ ! -r "$ARTIFICE_ROOT/$resource" ] || [ ! -x "$ARTIFICE_ROOT/$resource" ]; then
    printf 'Unreadable Artifice resource: %s\n' "$ARTIFICE_ROOT/$resource" >&2
    exit 1
  fi
done
export ARTIFICE_ROOT
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" discover --local --workdir .
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" select --task code
```

Discovery preserves every advertised Ollama identity and explicit unknown metadata, without ranking, warming, inference or unloading. Partial results and diagnostics must be disclosed, not treated as complete. Selection returns `model`, `resident`, `fallback: null`, `identity_fingerprint` and `reference`; unsuccessful selection exits `2` with a reason.

This Ollama phase permits only configured loopback endpoints and verified on-device inference, even without `--local`. Remote endpoints are diagnosed without contact; cloud-backed or unknown execution locality blocks dispatch. Discovery does not make a cloud conversation air-gapped: protected prompts, source, diffs **and outputs** require local pipelines or verified local sessions. `--accept-unknown` accepts task-specific suitability uncertainty, never a privacy exception.

**Hosted support is deferred.** Absent Vibe is `unavailable`; present Vibe is `unsupported_version` with `HOSTED_DISCOVERY_DEFERRED`, not a selectable model source. CLI presence authorises no configuration, authentication, catalogue or inference access. No hosted model menu or Vibe bridge ships here. See the [gateway workflow](skills/vibe-execute/SKILL.md) for exact run/triage flags; Ollama supports bounded chat, not autonomous filesystem editing.

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

Shared roles and skills use the validated, exported `ARTIFICE_ROOT` described above.

## Integration with Copilot

Install user-level directory symlinks once from any working directory:

```bash
bash scripts/install_copilot.sh
bash scripts/install_copilot.sh --check
```

The installer derives the physical checkout from its own path and validates sources, parent directories and targets before writing. If a parent cannot be resolved, installation aborts without creating links or directories. It never overwrites existing files, directories or mismatched links, and creates three symlinks:

```text
$HOME/.local/share/artifice                  -> physical Artifice checkout
${COPILOT_HOME:-$HOME/.copilot}/agents       -> $HOME/.local/share/artifice/integrations/copilot/agents
${COPILOT_HOME:-$HOME/.copilot}/skills       -> $HOME/.local/share/artifice/skills
```

Thin adapters in `integrations/copilot/agents/` configure Copilot tool permissions and load the canonical `agents/<role>/agent.md` body without duplicating prompts. Use unindented, single-line string values for `name` and non-empty `description`, and an inline `tools` list. Quote YAML indicators, colon-space text such as `"Review: code"`, and null or boolean literals. Start a fresh Copilot chat or reload the window after installation if discovery is stale.

Copilot's symlink paths are discovery addresses, not resource bases. Resolve linked resources from each canonical `ARTIFICE_ROOT/skills/<skill>/` directory before normalising `..` segments. For example, the review persona belongs under `ARTIFICE_ROOT/agents/code-reviewer/agent.md`, not Copilot's adapter directory; shared scripts likewise belong under `ARTIFICE_ROOT/scripts/`. Links inside a nested reference document use that document's canonical parent directory.
