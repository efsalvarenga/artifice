# Artifice

A curated, version-controlled collection of shared agent skills, procedures, and workflows for Google Antigravity and GitHub Copilot.

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
├── integrations/
│   └── copilot/agents/      # Thin Copilot adapters reading the canonical roles
├── scripts/
│   ├── install_copilot.sh   # Non-overwriting personal symlink installation
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
  └── test_install_copilot.sh # Disposable-home installation regression tests
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
* **Hybrid Offloading:** The selected client orchestrator decomposes the review into orthogonal streams, consulting local Qwen and Mistral models through Ollama when available and requested. Antigravity may use Gemini; Copilot inherits its selected model.
* **Offline Privacy Mode:** `--local` or repository privacy directives require a genuinely local session before protected-content ingestion. A local worker does not make a cloud Copilot or Antigravity conversation air-gapped; no automatic cloud fallback is permitted for local-only work.

### 3. `coach-frameworks`

* **Trigger:** `/coach-frameworks`
* **Persona:** Principal Developer Coach ("The Catalyst")
* **Role:** Strategic framework evaluation, ecosystem scouting across `~/Repos/*`, developer ergonomics coaching, and tooling inbox triage using the 4-Test Lesson Acceptance Gate.

### 4. `local-code`

* **Trigger:** `/local-code`
* **Backend:** Local `qwen2.5-coder:14b` (fallback `qwen2.5:14b`) running via Ollama.
* **Role:** Deep algorithmic refactoring, unit test generation, Fill-in-the-Middle (FIM) synthesis, and boundary edge-case probing with wave-leased memory management.

## Core Scripts

* `./scripts/check_ollama.py`: Ollama lifecycle and residency manager providing health checks, model selection, wave-leasing (`keep_alive: 5m`), and memory cache flushing. Latency and final memory use are measured, not guaranteed.
* `./scripts/lint.py`: Unified static governance linter auditing Markdown heading cleanliness, YAML frontmatter syntax, relative link integrity, and Core Diet ceilings across repositories.
* `./scripts/lint.sh`: Execution wrapper delegating directly to `lint.py`.
* `./scripts/validate_egm.py`: Validates EGM specification sections, matching Goldfish reviews, and approval verdicts with targeted `--spec` validation. This does not replace explicit human design approval.
* `./scripts/build_review_dossier.py`: Extracts and formats intentional repository invariants for local review models.

## Integration with Copilot

From the Artifice checkout, install once:

```bash
bash scripts/install_copilot.sh
bash scripts/install_copilot.sh --check
```

You may invoke the installer by its absolute path from another directory. It derives the checkout from its own location, preserves paths containing spaces, and creates only these directory symlinks:

```text
$HOME/.local/share/artifice -> physical Artifice checkout
${COPILOT_HOME:-$HOME/.copilot}/agents -> resource anchor/integrations/copilot/agents
${COPILOT_HOME:-$HOME/.copilot}/skills -> resource anchor/skills
```

`HOME` must be an existing absolute directory. Set `COPILOT_HOME` to an absolute directory only when the intended client uses that same configuration home. The installer does not set a persistent environment variable or change VS Code settings.

Whole-directory links expose later edits, additions, and removals without regeneration or another install. The checkout must remain available. Start a fresh chat, or reload the window if discovery is stale; already loaded conversation instructions are not guaranteed to refresh.

Select `code-author`, `code-reviewer`, or `developer-coach` from the agent picker. Each adapter explicitly reads the existing role's Markdown body, retaining client-specific tool configuration without copying the workflow. Skills can be selected separately using `/spec-egm`, `/review`, `/coach-frameworks`, and `/local-code` when the client exposes them. If a built-in command shares `review`, confirm the selected item is Artifice's skill rather than assuming precedence.

### Verification

```bash
bash -n scripts/install_copilot.sh tests/test_install_copilot.sh
bash tests/test_install_copilot.sh
python3 scripts/lint.py .
```

Use the selected project interpreter in place of `python3` where necessary. Installation and its Bash tests need no Ollama daemon, model download, new package, or Git write. Tests use disposable homes, not your real personal registration.

Filesystem checks do not prove client discovery. In **Chat: Open Customizations**, confirm all three agents and four skills are visible. Give each agent a harmless read-only request to report its canonical instruction file; inspect the actual read operation. Ask a skill to locate its template and shared utility without running its full workflow. Verify a source change in a fresh session, then check Antigravity separately. Record missing-client checks as outstanding rather than passed.

### Conflicts & Recovery

Installation refuses existing real files or directories, wrong or broken links, invalid parents, and paths that would register inside the checkout or create a cycle. It never replaces them, even when a conflicting directory is empty. If you have unrelated personal agents or skills, decide on a different layout rather than forcing installation. Prevent simultaneous installers or external writes to these paths.

`--check` is read-only. Installation rolls back only links and empty directories created by its own invocation after a catchable failure. It preserves prior correct links. Power loss, uncatchable termination, or filesystem errors can leave partial state; inspect it with `--check` before retrying.

If the checkout moves, manually verify and repoint only the owned `$HOME/.local/share/artifice` link to the new physical checkout; the two registration links can remain unchanged. For removal, inspect targets with `readlink` and remove only these owned symlinks, never their directory contents or an unrelated path. There is no force-replace or automatic uninstall mode. Symlinks are machine-local; install separately on another host rather than expecting Settings Sync to provision them.

### Workflow Boundaries

Both clients require explicit approval of presented designs and material revisions before implementation. Branch changes, staging, commits, pushes, and PR publication each require operation-specific permission. Implementation permission does not authorise Git writes. Provenance describes only assistants and workers actually used; do not infer hidden model identifiers.

Global governance stays client-specific: Copilot uses its active instructions and target-repository rules, while Antigravity may read its existing Gemini global rules. The installer does not migrate or modify global configuration. Normal client trust, sandbox, and approval controls still apply; terminal-enabled review is not a technical read-only boundary.

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

This registration remains independent of Copilot and is not edited by the installer. Existing Antigravity agent filenames and tool headers are retained. The shared instruction bodies use the current client orchestrator rather than assuming a Gemini-only runtime.

Shared roles and skills first resolve `$HOME/.local/share/artifice` when present. If absent in an Antigravity-only setup, physically resolve the definition's containing directory before ascending two directories to the checkout. Validate the expected `agents`, `skills`, and `scripts` directories plus the requested resource. A present but broken anchor is an error, not permission to guess another checkout.

Bind that verified absolute directory as `ARTIFICE_ROOT` separately for each tool command and pass the target repository explicitly. No persistent variable is required. Skill-local templates remain relative; shared scripts and role definitions are read from the resolved checkout, not from the current target repository. If discovery does not expose a physical definition path and no anchor exists, request the checkout location or installation repair.

Copilot discovery and Antigravity live acceptance must be verified separately from filesystem installation.
