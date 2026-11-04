# Artifice

A curated, version-controlled collection of shared agent skills, procedures, and workflows for Google Antigravity and GitHub Copilot.

*Artifice* (English: the craft, the ingenious device; Portuguese *artífice*: the master craftsman, the architect of a work) serves as the centralised repository of capabilities mounted globally across all local development projects.

## Directory Structure

```text
artifice/
├── agents/                       # Three canonical role bodies
├── skills/                       # Four workflows and skill-local references
├── integrations/copilot/agents/  # Thin client-specific adapters
├── scripts/                      # Installation, models and native governance
├── tests/                        # Standard-library contracts; separate Bash runtime runner
├── docs/                         # Designs, Goldfish reviews and proposals
└── TASKS.md                      # Roadmap and incoming tooling feedback
```

## Available Agents

### 1. `code-author`

[The Craftsman](agents/code-author/agent.md): approved contracts, Red/Green TDD, minimal code, truthful provenance and green baseline gating.

### 2. `code-reviewer`

[The Gatekeeper](agents/code-reviewer/agent.md): eight-pillar PR, branch, file and architectural review using Conventional Comments.

### 3. `developer-coach`

[The Catalyst](agents/developer-coach/agent.md): evidence-based framework evaluation, sibling-repository scouting, developer ergonomics and four-test lesson triage.

## Available Skills

### 1. `spec-egm`

* **Trigger:** `/spec-egm [init | review | validate]`
* **Role:** [Elephant-Goldfish workflow](skills/spec-egm/SKILL.md): reconnaissance, human workshops, no-code design, independent zero-context review and mechanical contract validation.

### 2. `review`

* **Trigger:** `/review [--local] [PR_NUMBER | branch | <file_or_doc_path>]`
* **Role:** [Eight-pillar review](skills/review/SKILL.md), with optional selected local workers and the [strict session boundary](#workflow-boundaries).

### 3. `coach-frameworks`

* **Trigger:** `/coach-frameworks`
* **Role:** [Framework coaching](skills/coach-frameworks/SKILL.md), ecosystem precedents and developer-experience improvements filtered through the four-test lesson gate.

### 4. `local-code`

* **Trigger:** `/local-code`
* **Backend:** An installed Ollama coding model, with [validated overrides and preserved defaults](#local-model-configuration).
* **Role:** [Bounded refactoring, boundary tests and FIM synthesis](skills/local-code/SKILL.md) with wave-leased memory management.

## Core Scripts

* `./scripts/check_ollama.py`: Ollama lifecycle and residency manager providing health checks, model selection, wave-leasing (`keep_alive: 5m`), and memory cache flushing. Latency and final memory use are measured, not guaranteed.
* `./scripts/lint.py`: Native governance for Markdown, relative links, canonical frontmatter, Copilot adapters, Bash syntax and Core Diet (skills <=180 lines/1,000 words; agents <=900 words, including frontmatter/code).
* `./scripts/lint.sh`: Physical-path execution wrapper for `lint.py`; disposable runtime tests remain separate.
* `./scripts/validate_egm.py`: Validates EGM specification sections, matching Goldfish reviews, and approval verdicts with targeted `--spec` validation. This does not replace explicit human design approval.
* `./scripts/build_review_dossier.py`: Extracts and formats intentional repository invariants for local review models.

## Integration with Copilot

From the checkout, or invoke the installer by absolute path from any directory:

```bash
bash scripts/install_copilot.sh
bash scripts/install_copilot.sh --check
```

`HOME` must be an existing absolute directory. Unset/empty `COPILOT_HOME` defaults below; a custom value must be absolute and used by the intended client.

```text
$HOME/.local/share/artifice -> physical Artifice checkout
${COPILOT_HOME:-$HOME/.copilot}/agents -> resource anchor/integrations/copilot/agents
${COPILOT_HOME:-$HOME/.copilot}/skills -> resource anchor/skills
```

Directory links expose edits and future components without regeneration. Keep the checkout available; start a fresh chat/reload for stale discovery.
See [verification](#verification), [ownership/conflicts/recovery](#conflicts--recovery) and [privacy/models/authority](#workflow-boundaries). No client settings or global configuration are changed.

### Verification

```bash
for script in scripts/*.sh tests/*.sh; do bash -n "$script" || exit; done
bash tests/test_install_copilot.sh
python3 -m unittest discover -s tests -p 'test_*.py'
ARTIFICE_ROOT="<validated-root>"; python3 "$ARTIFICE_ROOT/scripts/validate_egm.py" "<target_repo>" --spec 003
./scripts/lint.sh
git diff --check
```

Use the selected project interpreter where needed. Tests use standard-library `unittest`, mocked Ollama rosters and scoped disposable homes/checkouts, never personal registrations or live model loading/inference/download/unloading. The Bash runtime runner retains the original 21 installer cases and additional deterministic mutator-failure/interruption probes; it never evaluates extracted source. Native lint checks syntax, not runtime installation.

Filesystem success does not prove client discovery. In **Chat: Open Customizations**, confirm `code-author`, `code-reviewer`, `developer-coach` and `/spec-egm`, `/review`, `/coach-frameworks`, `/local-code`. Confirm Artifice's `review` rather than a colliding built-in. Ask each agent for its canonical file and inspect the actual read; check a skill's template/utility and source refresh in a fresh session. Separately verify effective tools, cloud-session `--local` refusal before protected reads, and Antigravity without an anchor/definition path. Record unavailable checks as outstanding; static prose tests are not live workflow or privacy proof.

### Conflicts & Recovery

Installation refuses existing real files or directories, wrong or broken links, invalid parents, and paths that would register inside the checkout or create a cycle. It never replaces them, even when a conflicting directory is empty. If you have unrelated personal agents or skills, decide on a different layout rather than forcing installation. Prevent simultaneous installers or external writes to these paths.

`--check` is read-only. Installation rolls back only links and empty directories created by its own invocation after a catchable failure. It preserves prior correct links. Power loss, uncatchable termination, or filesystem errors can leave partial state; inspect it with `--check` before retrying.

If the checkout moves, manually verify and repoint only the owned `$HOME/.local/share/artifice` link to the new physical checkout; the two registration links can remain unchanged. For removal, inspect targets with `readlink` and remove only these owned symlinks, never their directory contents or an unrelated path. There is no force-replace or automatic uninstall mode. Symlinks are machine-local; install separately on another host rather than expecting Settings Sync to provision them.

### Workflow Boundaries

Follow active client/repository authority, including valid preauthorisation. Both clients require explicit approval of presented designs/material revisions before implementation. Branch changes, staging, commits, pushes and PR publication each need operation-specific permission; installation/implementation grants no Git rights. Attribute only assistants and workers actually used, never guessed hidden identities.

Global governance stays client-specific: Copilot uses its active instructions and target-repository rules, while Antigravity may read its existing Gemini global rules. The installer does not migrate or modify global configuration. Normal client trust, sandbox, and approval controls still apply; terminal-enabled review is not a technical read-only boundary.

Ordinary cloud+Ollama work is hybrid, not offline. Strict `--local`/local-only work requires a genuinely local session before protected reads with no cloud fallback. Check minimum policy metadata first; behavioural instructions do not provide technical containment.

### Local Model Configuration

Set `ARTIFICE_CODE_MODEL` for code/logic/fim/tdd and `ARTIFICE_PROSE_MODEL` for prose/docs/adr/architecture to exact installed tags when needed. The groups may share a tag. No model is presumed installed; configuration never downloads one.

Only the selected task group's override is validated. An explicitly empty value fails before any daemon query. A non-empty value must exactly match an installed tag; offline or uninstalled selections fail with exit 2 and `fallback: null`. Unrelated invalid overrides are ignored.

Unset defaults preserve installed-list order: coding prefers the first tag containing `qwen2.5-coder:14b`, then `qwen2.5:14b`; prose selects the first containing `mistral-nemo`. Unset/offline or no suitable default fails with advisory `fallback: "cloud-flash"` and exit 2. The hint never authorises remote execution.

`select --task` retains its existing choices. Success JSON is exactly `{model: string, resident: boolean, fallback: null}`; failure is `{model: null, fallback: null | "cloud-flash", reason: non-empty string}`. Carry the successful actual tags as `code_model`/`prose_model` through warming, inference payloads, review streams and provenance; sign only for workers actually used. See [local-code](skills/local-code/SKILL.md) and [review](skills/review/SKILL.md) for examples.

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

Shared entry points select explicitly supplied `ARTIFICE_ROOT`, otherwise present `$HOME/.local/share/artifice` (including broken symlinks), otherwise legacy `$HOME/Repos/artifice`. Validate only the selected source: empty/invalid overrides or selected broken anchors fail; unused broken lower-priority anchors are ignored. Require an absolute physically resolved root containing readable `agents`, `skills`, `scripts` directories and the requested asset. Text-only discovery needs no physical definition path. The installer itself always derives its root from its script, not these runtime overrides.

Bind the quoted root per command; keep the consuming repository separate. Relative Markdown links are documentation, not executable paths through personal registration symlinks. Read templates and shared utilities under the validated root. No persistent variable is required.

Copilot discovery and Antigravity live acceptance must be verified separately from filesystem installation.
