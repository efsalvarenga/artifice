# Design 007: Unified Multi-Harness Mounting for Artifice

**Author:** efsalvarenga
**Status:** Proposed
**Date:** 2026-11-17

--------------------------------------------------------------------------------

## Overview

Artifice keeps one canonical copy of its agents, skills, and governance rules in the checkout behind the anchor `~/.local/share/artifice` (a symlink to `~/Repos/artifice`) and mounts that copy into every AI harness in use. This design specifies the missing omp installer ([#30](https://github.com/efsalvarenga/artifice/issues/30)) and aligns all harness installers under one minimal contract. It settles the VS Code mount surface, records the "nothing to migrate" audit boundary for [#23](https://github.com/efsalvarenga/artifice/issues/23), and defines the one additional omp evidence row to append to the existing matrix in design 005 for [#19](https://github.com/efsalvarenga/artifice/issues/19). Versioning remains out of scope for this design and is tracked in [#37](https://github.com/efsalvarenga/artifice/issues/37).

Terminology used below: *agy* is the Google Antigravity CLI binary; *omp* is oh-my-pi, driven in this setup through the Paseo app/daemon; EGM is the upstream Elephant-Goldfish Model plugin; Core Diet is the word/line ceilings enforced by [scripts/lint.py](../../scripts/lint.py); *artemis* is this developer workstation.

## The Problem

Each harness mounts artifice differently, and partly by hand. Antigravity gets directory symlinks plus a hand-maintained `AGENTS.md` that is a regular file, so `install_antigravity.sh --check` already reports a conflict on this machine. Copilot gets symlinks through `install_copilot.sh`. omp has skills mounted through a manually added `skills.customDirectories` entry but no `AGENTS.md`, no agents directory, and no installer at all. There is no versioning: no git tags and no changelog. [#25](https://github.com/efsalvarenga/artifice/issues/25) asks for the symlink architecture to be formalised, [#30](https://github.com/efsalvarenga/artifice/issues/30) for a native omp integration, [#23](https://github.com/efsalvarenga/artifice/issues/23) for the remaining local-config migration, and [#19](https://github.com/efsalvarenga/artifice/issues/19) for fresh-client evidence per harness. Without one written installer contract, every new harness re-invents registration, conflicts are handled ad hoc, and drift between harnesses grows.

## Goals

*   One written installer contract for every `scripts/install_<harness>.sh`, with thin adapters only where a harness needs them (agent adapters for omp and Copilot; no agy adapter) and a non-overwriting installer supporting `--check` and conflict-safe atomic preflight.
*   `AGENTS.md` unified as a symlink to [rules/global-agents.md](../../rules/global-agents.md) wherever the harness follows symlinks; the current regular-file drift is handled as a documented manual migration ([#33](https://github.com/efsalvarenga/artifice/issues/33)), never auto-adopted.
*   omp mounting: `~/.omp/agent/AGENTS.md` and `~/.omp/agent/agents` symlinks plus the `skills.customDirectories` entry in `~/.omp/agent/config.yml`, failing with guidance when the key already holds other directories.
*   The VS Code mount surface decided in this design, with verification in a live VS Code session as an acceptance step ([#34](https://github.com/efsalvarenga/artifice/issues/34)).
*   [scripts/lint.py](../../scripts/lint.py) and [tests/](../../tests/) coverage for the new installer and `integrations/omp/`.

## Non-Goals

*   [#28](https://github.com/efsalvarenga/artifice/issues/28) (hybrid agy + omp headless worker) stays deferred to its own PR after the omp mount exists.
*   Versioning (`CHANGELOG.md`, tags, and PR template mechanics), tracked in [#37](https://github.com/efsalvarenga/artifice/issues/37).
*   No automatic Git hooks, Git configuration changes, or `.github/workflows/` CI gates.
*   No silent merging, backing up, or adopting of personal files (`AGENTS.md`, `config.yml`, `config.json`, `vibe_models.json`).
*   No whole-directory symlink of `~/.omp/agent/skills` (it would redirect omp's native user-skill writes into the checkout).
*   No compiled or packaged distribution of `scripts/`; [#25](https://github.com/efsalvarenga/artifice/issues/25) keeps the live-anchor, no-reinstall loop (visible at the next fresh session, not zero-latency within one).
*   No migration of non-empty personal agy config files into the repository; [#23](https://github.com/efsalvarenga/artifice/issues/23) closes as "nothing to migrate" with audit evidence after the PR merges.
*   Relocated-profile mounts (custom `OMP_PROFILE` / `PI_CODING_AGENT_DIR`, explicit `GEMINI_HOME` / `COPILOT_HOME`) are installer-test-only unless separately runtime-verified.

## Open Questions

*   **VS Code verification ([#34](https://github.com/efsalvarenga/artifice/issues/34))**: confirm in a live VS Code session on artemis that the default-home `~/.copilot/copilot-instructions.md` symlink is actually loaded by the installed Copilot extension.
*   **Relocated profiles**: whether `OMP_PROFILE` / `PI_CODING_AGENT_DIR` mounts deserve runtime evidence or stay installer-test-only.

## Decisions

Design decisions:

*   **D1** — one installer contract per harness (below).
*   **D2** — `AGENTS.md` symlink to the canonical policy wherever possible; manual migration for existing regular files ([#33](https://github.com/efsalvarenga/artifice/issues/33)).
*   **D3** — `config.yml`: idempotent if the anchor entry is present; fail-with-guidance if the key holds other directories; otherwise a narrow atomic append.
*   **D4** — VS Code Option A (default home), decided 2026-11-17, pending live verification ([#34](https://github.com/efsalvarenga/artifice/issues/34)).
*   **D5** — [#23](https://github.com/efsalvarenga/artifice/issues/23) closes via an evidence comment after the PR merges.
*   **D6** — [#19](https://github.com/efsalvarenga/artifice/issues/19) evidence matrix gains the omp-via-Paseo row.
*   **D7** — risk register in Risks & Mitigations below.

## Critical User Journeys (CUJs)

### CUJ 1: Fresh machine bootstrap

*   **Given**: a new machine with a fresh clone of artifice at `~/Repos/artifice` and the harness CLIs installed.
*   **When**: the developer runs `bash scripts/install_antigravity.sh`, `bash scripts/install_copilot.sh`, and `bash scripts/install_omp.sh`, then starts a fresh session in each harness.
*   **Then**: every registration is correct and `--check` exits 0 on all three; no personal file was overwritten; native inclusion evidence (policy, skills, and personas visible in each fresh session) is collected per the [#19](https://github.com/efsalvarenga/artifice/issues/19) matrix — registration on disk is not proof of loading.

### CUJ 2: Adding a new harness

*   **Given**: the installer contract in this design and an existing `install_<harness>.sh` as the template.
*   **When**: a fourth harness appears.
*   **Then**: a new `integrations/<harness>/` adapter set plus `install_<harness>.sh` following the same contract is the only work; the per-harness inventories hardcoded in the tests (`tests/test_governance.py`) and installer source lists gain the new entries; no changes to the canonical `agents/`, `skills/`, or `rules/` layout.

--------------------------------------------------------------------------------

## Technical Plan (Architecture)

### Mounting model

One canonical source: the artifice checkout at `~/Repos/artifice`, exposed through the anchor symlink `~/.local/share/artifice`. Every harness registration points at the anchor with absolute paths (physical equivalence accepted); never at per-harness copies. Editing a skill or rule in the checkout is visible to every harness at the next fresh session.

```text
~/Repos/artifice                 canonical checkout: agents/ skills/ rules/ integrations/ scripts/
        ^
        |  symlink
~/.local/share/artifice          stable anchor
        |
        +-- agy:     ~/.gemini/config/{skills,agents} -> anchor dirs; AGENTS.md -> anchor/rules/global-agents.md; skills.json registers the anchor skills path (absolute)
        +-- omp:     ~/.omp/agent/AGENTS.md -> anchor/rules/global-agents.md; ~/.omp/agent/agents -> anchor/integrations/omp/agents; config.yml skills.customDirectories += anchor/skills
        +-- copilot: ~/.copilot/{agents -> anchor/integrations/copilot/agents, skills -> anchor/skills, copilot-instructions.md -> anchor/rules/global-agents.md}
        +-- vscode:  default home via ~/.copilot/copilot-instructions.md (D4, Option A)
```

### The installer contract (every `scripts/install_<harness>.sh`)

1.  **Client root**: validated, normalised absolute path resolved the way the harness itself resolves it. For agy and Copilot that is the existing `GEMINI_HOME` / `COPILOT_HOME` override with the default home fallback. For omp it is the active agent directory: `PI_CODING_AGENT_DIR` if set, else `~/.omp/profiles/<name>/agent` when `OMP_PROFILE` is set, else `~/.omp/agent`. The installer introduces no new environment variable of its own. The client root may not live inside the anchor or inside the checkout; if the active root cannot be resolved, the installer fails with guidance.
2.  **Preflight**: classify every destination as `missing`, `correct-link`, or `conflict` (existing regular file, real directory, mismatched or dangling symlink). Any conflict aborts before any write. Zero writes on conflict; existing personal files are never merged, backed up, replaced, or adopted.
3.  **Atomic writes**: symlinks are created with Python's `os.symlink` create-if-absent, so a destination that appears after preflight is reported as a conflict, never followed or overwritten. The anchor itself is created create-if-absent when missing, as in the existing installers.
4.  **Config registrations** (agy `skills.json`, omp `config.yml`) follow the same discipline. If `config.yml` is absent, create a minimal file containing `skills.customDirectories` with the anchor path. If it exists and already contains that path under `skills.customDirectories`, report `correct-config`. If it exists without that entry, fail with guidance and an exact three-line YAML snippet for manual update. `--check` reports a missing entry with zero writes.
5.  **`--check` is read-only**: exit 0 when every destination and config entry is correct, exit 1 otherwise, and never writes.
6.  **Partial installs**: no rollback claims; rerun `--check` to inspect the actual state.
7.  **Policy file**: `AGENTS.md`-equivalents are symlinks to [rules/global-agents.md](../../rules/global-agents.md) wherever the harness follows symlinks (all three current harnesses do). The canonical policy stays harness-neutral; harness-specific content is dropped at migration time, not folded in. Thin `integrations/<harness>/` adapters are allowed only for agent definitions, never for the policy file.

### Per-harness registration table

| Harness | Client root | Registrations |
| --- | --- | --- |
| agy (Antigravity) | `${GEMINI_HOME:-$HOME/.gemini}/config` | `skills` symlink, `agents` symlink, `AGENTS.md` symlink to `rules/global-agents.md`, `skills.json` with the absolute anchor skills path |
| omp (via Paseo) | active agent dir: `PI_CODING_AGENT_DIR`, else `~/.omp/profiles/<OMP_PROFILE>/agent`, else `~/.omp/agent` | `AGENTS.md` symlink to `rules/global-agents.md`, `agents` symlink to `integrations/omp/agents`, `skills.customDirectories` entry in `config.yml` |
| Copilot CLI | `${COPILOT_HOME:-$HOME/.copilot}` | existing three client-root symlinks (agents adapters, skills, `copilot-instructions.md`) plus the anchor |
| VS Code Copilot | default home (D4, Option A) | `~/.copilot/copilot-instructions.md` symlink, already provided by `install_copilot.sh` |

### omp agent adapters (`integrations/omp/agents/`)

`integrations/omp/agents/{code-author,code-reviewer,developer-coach}.md` are thin adapters with omp-native frontmatter. omp does not normalise Antigravity tool names (`view_file`, `run_command`, …), so the adapter `tools:` lists must use omp tool names. Per-role mapping from the canonical [agents/](../../agents/) frontmatter:

| Canonical (agy) tool | omp tool |
| --- | --- |
| `view_file`, `read_file` | `read` |
| `grep_search` | `grep` |
| `find_by_name`, `list_dir` | `glob` |
| `edit_file` | `edit` |
| `write_file` | `write` |
| `run_command` | `bash` |
| `send_message` | `send_message` |
| `search_web` | `web_search` |

Per-role extra omp tools: `code-author` and `code-reviewer` (hybrid offloading) also get `task`, `wait`, and `todo`; `developer-coach` gets none beyond the mapping. Adapter bodies delegate to the canonical `agents/<role>/agent.md` content by path reference without duplicating it.

### VS Code mount surface (D4 — decided 2026-11-17, pending live verification)

**Decision: Option A — default home only.** VS Code Copilot reads the same `~/.copilot/copilot-instructions.md` symlink that `install_copilot.sh` already creates, so no new registrations are needed. Multi-profile and repo-level prompt files stay out of scope. Verification in a live VS Code session on artemis remains the acceptance step ([#34](https://github.com/efsalvarenga/artifice/issues/34)).

Options B and C were rejected by the author on 2026-11-17 (surface verification pending under [#34](https://github.com/efsalvarenga/artifice/issues/34)): B adds per-repo prompt files without a verified consumer need yet; C touches editor settings for coverage Option A already provides.

### Procedural items

*   **[#23](https://github.com/efsalvarenga/artifice/issues/23) closure**: after the PR merges, comment with the audit evidence (`mcp_config.json` empty at 0 bytes; no backup scripts, MCP templates, or user sidecars; non-empty personal files left in place deliberately) and close.
*   **[#19](https://github.com/efsalvarenga/artifice/issues/19) evidence matrix**: add the omp-via-Paseo row to [design 005](005_shared_governance_and_commit_provenance.md)'s fresh-client acceptance matrix (the agy, Copilot CLI, and VS Code default-home rows already exist there); each row records client surface, version, harness/profile, effective home, policy path, fresh-session identifier, and native inclusion evidence (policy content visible in the session, not file existence).
*   **[#33](https://github.com/efsalvarenga/artifice/issues/33) manual migration**: on artemis, review the current 3,601-byte `~/.gemini/config/AGENTS.md`, drop the stale `spec-egm` / `validate_egm.py` references and the Gemini-only delegation sections, keep [rules/global-agents.md](../../rules/global-agents.md) harness-neutral (no fold-in of agy-specific content), replace the file with the symlink to the canonical policy, and verify `install_antigravity.sh --check` passes.

--------------------------------------------------------------------------------

## Alternatives Considered

### Whole-directory symlink `~/.omp/agent/skills -> anchor/skills`

*   **Pros**: one link instead of a config entry.
*   **Cons**: redirects omp's native user-skill writes into the canonical checkout, breaking the rule that harness-native writes must not land there (recorded in the [#30](https://github.com/efsalvarenga/artifice/issues/30) comment).
*   **Reason for Rejection**: breaks the read-only-anchor invariant. The `skills.customDirectories` config entry keeps native skills local and artifice skills read-only through the anchor.

### Per-skill symlinks under `~/.omp/agent/skills/<name>/`

*   **Pros**: works without editing `config.yml`.
*   **Cons**: multiplies the destinations the installer must preflight and race-check for every new skill.
*   **Reason for Rejection**: the single `customDirectories` entry achieves the same discovery with one registration. Retained as a fallback if the `config.yml` write proves unsafe.

### Thin per-harness `AGENTS.md` adapter files instead of the symlink

*   **Pros**: lets each harness trim content it cannot follow.
*   **Cons**: forks the canonical policy into per-harness copies — the drift that [#25](https://github.com/efsalvarenga/artifice/issues/25)'s single-canonical-source architecture and design 005's one-policy-owner invariant exist to prevent.
*   **Reason for Rejection**: adapters are allowed only for agent definitions; the policy file is always the symlink to `rules/global-agents.md`.

### Automatic merge, backup, or adoption of conflicting personal files during install

*   **Pros**: hands-free setup on machines with existing files.
*   **Cons**: changes personal policy ownership silently.
*   **Reason for Rejection**: [design 005](005_shared_governance_and_commit_provenance.md) makes existing personal files conflicts that abort the installer before any write, with manual migration guidance.

### A shared parameterised installer framework across harnesses

*   **Pros**: one code path for all harnesses.
*   **Cons**: the registrations differ in kind (symlinks vs `skills.json` vs a `config.yml` entry), so a framework mostly parameterises around the differences.
*   **Reason for Rejection**: the two existing installers already encode the safe pattern; copying that shape per harness is less code and easier to audit.

### Closing [#23](https://github.com/efsalvarenga/artifice/issues/23) immediately without the merged PR and audit evidence

*   **Pros**: tidies the issue list sooner.
*   **Cons**: asserts "nothing to migrate" without evidence.
*   **Reason for Rejection**: design 005 keeps #23 partial until the audit is delivered; the closure comment follows the merged PR and records the empty-`mcp_config.json` evidence.

### VS Code Options B (repo-level prompt files) and C (`.vscode/` wiring)

*   **Pros**: B covers per-repo prompt files; C also wires editor settings.
*   **Cons**: no verified consumer need yet; C touches editor settings for coverage Option A already provides.
*   **Reason for Rejection**: rejected by the author on 2026-11-17 (D4; pending live verification under [#34](https://github.com/efsalvarenga/artifice/issues/34)); revisited only if a concrete need appears.

--------------------------------------------------------------------------------

## Risks & Mitigations

| Risk | Mitigation |
| --- | --- |
| Dangling anchor if the checkout moves or is deleted; every link through it breaks | `--check` classifies dangling links as conflicts; lint keeps reading the physical checkout rather than the anchor, so a green lint run must never be read as mount health |
| One anchor can point at only one physical checkout; a second mounted worktree surfaces as a conflict | accepted limitation: `--check` compares resolved physical targets, so only explicit registrations to the active checkout are accepted |
| Partial install after a runtime failure leaves earlier registrations in place | no rollback claims; rerun `--check` to inspect actual state |
| Lost update on the `config.yml` temp-plus-rename if the user edits concurrently | copy the original file's mode onto the temp file; re-read before rename; document the residual window |
| Concurrent runs of two installers against the same anchor | preflight aborts on conflict, but a mid-write race remains; accept and document |
| Line-based `config.yml` edit corrupts unsupported YAML shapes | supported subset is top-level block-style keys only; anything else fails with guidance |
| Relocated omp root (`OMP_PROFILE` / `PI_CODING_AGENT_DIR`) gives a false-health `--check` exit 0 | installer resolves the active agent dir exactly as omp does and fails with guidance when it cannot |
| Word/line ceilings: policy 140/1,400, skills 180/1,000, agents 900 words ([#32](https://github.com/efsalvarenga/artifice/issues/32)); adapters get their own fixed 60-line ceiling | persona edits stay word-neutral; lint enforces the ceilings |

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Security & privacy**: installers never transmit personal config contents, and never parse-and-rewrite them; the `config.yml` edit is a narrow line-based append within the supported subset, and conflict guidance prints commands without reading personal file bytes.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Create/Modify

#### 1. `scripts/install_omp.sh` (Create)

*   **Type / Scope**: Bash installer mirroring [install_antigravity.sh](../../scripts/install_antigravity.sh).
*   **Proposed Changes**: anchor validation and create-if-absent; preflight classifying every destination as missing / correct-link / conflict with zero writes on conflict; atomic create-if-absent symlinks via Python `os.symlink`; creates `AGENTS.md -> anchor/rules/global-agents.md` and `agents -> anchor/integrations/omp/agents` under the active agent dir (resolved per the client-root rule above); `config.yml` handling per D3 and the supported-subset rule (idempotent / fail-with-guidance / narrow atomic append with mode copy; fresh-machine template creation); read-only `--check` with exit 0/1 and no writes.

#### 2. `integrations/omp/agents/code-author.md`, `code-reviewer.md`, `developer-coach.md` (Create)

*   **Type / Scope**: thin task-agent adapters.
*   **Proposed Changes**: omp-native frontmatter (`name`, `description`, `tools` per the mapping table above) whose bodies delegate to the canonical `agents/<role>/agent.md` without duplicating it.

#### 3. `docs/designs/007_unified_harness_mounting.md` (Create)

*   **Type / Scope**: this document.

#### 4. `scripts/lint.py` (Modify)

*   **Type / Scope**: governance linter.
*   **Proposed Changes**: generalise the adapter frontmatter gate from `integrations/copilot/agents` to `integrations/*/agents`, accepting Copilot's `*.agent.md` suffix and omp's plain `*.md` suffix; validate omp adapter `tools:` against per-role `OMP_TOOLS` sets enumerated in the mapping table above. Bash-syntax and Markdown walks already cover the new files recursively.

#### 5. `tests/test_artifice.py` (Modify)

*   **Type / Scope**: installer black-box tests.
*   **Proposed Changes**: cases for `install_omp.sh` on a disposable home — missing / correct-link / conflict destinations, the three `config.yml` paths plus the fresh-machine create path and the unsupported-shape fail path, `--check` exit codes, and no-clobber guarantees.

#### 6. `tests/test_governance.py` (Modify)

*   **Type / Scope**: policy-symlink governance tests.
*   **Proposed Changes**: add a third `omp` branch alongside the existing copilot/antigravity branches (client root `~/.omp/agent` overridable via `PI_CODING_AGENT_DIR` / `OMP_PROFILE`, policy at `~/.omp/agent/AGENTS.md`, env-var name, home-dir assertions), extend the tests to the omp registrations (`AGENTS.md` and `agents` symlinks), and add `"omp"` to the `clients` tuple at `tests/test_governance.py:21`.

#### 7. `README.md` (Modify)

*   **Type / Scope**: project documentation.
*   **Proposed Changes**: add the omp integration (`scripts/install_omp.sh`) beside the Antigravity and Copilot sections, and refresh the Directory Structure tree for the new files. Keep growth economical.

### Staging

*   **Stage 1 — this design merged.** Checkpoint: `./scripts/lint.sh` exit 0.
*   **Stage 2 — omp mount.** Items 1, 2, 4, 5, 6, 7. Checkpoint: `install_omp.sh --check` exit 0 on artemis (agy `--check` is expected to conflict until the Stage 3 migration), and a fresh omp-via-Paseo session shows the policy, skills, and agents loaded (the omp discovery probe, recorded as a [#19](https://github.com/efsalvarenga/artifice/issues/19) evidence row).
*   **Stage 3 — agy migration.** [#33](https://github.com/efsalvarenga/artifice/issues/33) manual migration on artemis, then live VS Code verification ([#34](https://github.com/efsalvarenga/artifice/issues/34)). Checkpoint: all three installers' `--check` exit 0 on artemis; fresh agy session shows the canonical policy.
*   **Stage 5 — procedural.** Collect the [#19](https://github.com/efsalvarenga/artifice/issues/19) evidence rows and post the [#23](https://github.com/efsalvarenga/artifice/issues/23) closure comment. [#28](https://github.com/efsalvarenga/artifice/issues/28) stays deferred until the omp mount exists.

### Verification Plan

*   **Lint**: `./scripts/lint.sh` exit 0 (heading blank lines, relative links, adapter frontmatter, Bash syntax, Core Diet ceilings).
*   **Unit / black-box**: `python3 -m unittest discover -s tests -p 'test_*.py'` exit 0 via `lint.sh`, including the new `install_omp.sh` cases.
*   **Installer checks**: `--check` passes on artemis for all three installers after the [#33](https://github.com/efsalvarenga/artifice/issues/33) migration; conflict behaviour covered by tests.
*   **Runtime evidence ([#19](https://github.com/efsalvarenga/artifice/issues/19))**: a fresh omp-via-Paseo session shows the policy, skills, and agents; a fresh agy session after #33; VS Code verified in a live session ([#34](https://github.com/efsalvarenga/artifice/issues/34)). Each row records client surface, version, harness/profile, effective home, policy path, fresh-session identifier, and native inclusion evidence.

--------------------------------------------------------------------------------

*Drafted with EGM*
