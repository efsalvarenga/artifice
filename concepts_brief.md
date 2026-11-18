# Design 007: Unified Multi-Harness Mounting and Semver Versioning for Artifice

* Author: efsalvarenga
*   **Status:** historical brainstorm record — non-normative; where it differs, [docs/designs/007_unified_harness_mounting.md](docs/designs/007_unified_harness_mounting.md) governs.
* Date: 2026-11-17

## Overview

Artifice keeps one canonical copy of its agents, skills, and governance rules in the checkout behind the anchor `~/.local/share/artifice -> ~/Repos/artifice`, and mounts that copy into every AI harness the developer uses. Design 007 turns the two existing installers (`scripts/install_antigravity.sh`, `scripts/install_copilot.sh`) into a uniform per-harness mounting architecture: each harness gets a thin `integrations/<harness>/` adapter set plus a non-overwriting `scripts/install_<harness>.sh` with `--check` and conflict-safe atomic preflight. It adds the missing `omp` mount (issue #30), frames the VS Code mount surface as a decision for `/egm-draft`, records the "nothing to migrate" audit for issue #23, defines the fresh-client evidence matrix for issue #19, and introduces semver versioning (a Keep a Changelog `CHANGELOG.md` plus an annotated `vX.Y.Z` tag on every merge to main) even though skills are consumed live from the anchor rather than from a tagged release.

Reviewer status: the seven Goldfish lenses (egm-design, egm-codebase-details, egm-zoom-out, egm-comprehension, egm-implementation-readiness, egm-structural, egm-inventive-catalyst) are all marked `not run` as true zero-context subagents, because subagent spawning is disabled in this harness. Their perspectives were applied serially in this context instead. Per `egm-brainstorm`, an in-context review is not a Goldfish review, so the swarm should be re-run on a harness with subagent support before Stage 9 sign-off.

## Analysis

Weakest points first.

### 1. The AGENTS.md symlink unification is not installable on this machine today

`~/.gemini/config/AGENTS.md` is currently a regular 3,601-byte file, not the symlink `scripts/install_antigravity.sh` expects, so `install_antigravity.sh --check` reports a conflict right now. Design 005 is explicit that a regular file is a conflict even when its bytes match the policy, and that the installer must never adopt, back up, replace, or merge personal instruction files automatically. So the "symlink everywhere possible" half of the hypothesis collides with the "non-overwriting" half on the current machine: unification can only happen as a documented manual migration step (the developer reviews the 3,601-byte file, moves any personal rules they want to keep, deletes it, and re-runs the installer). Design 007 must say this out loud instead of assuming the symlink already exists.

### 2. The omp `config.yml` write is the one mutation the installer family currently avoids

The existing installers only create missing symlinks and write `skills.json` when the file is absent; they never edit an existing personal config file. The hypothesis asks `install_omp.sh` to write a `skills.customDirectories` entry into `~/.omp/agent/config.yml`, which breaks that pattern and leaves a real decision open: what happens when the key already exists with other directories? Merge (append the anchor entry) or fail (report a conflict with manual guidance)? The machine today has exactly one entry, so both choices are idempotent here, but on a machine with other custom directories they diverge. Merging mutates personal state, which sits uneasily next to design 005's no-automatic-merge rule; failing keeps the non-overwriting contract but makes install non-idempotent in spirit and pushes work onto the user. There is also a mechanical hazard: Python's standard library has no YAML parser, so a full parse-and-re-serialise would reorder keys and drop comments; only a narrow, line-based append with an atomic temp-file-plus-rename (and a re-read before the rename to abort on concurrent modification) is safe. `--check` must report a missing entry with zero writes. Merge versus fail must be decided in `/egm-draft`; the default recommendation is fail-with-guidance unless the anchor entry is already present.

### 3. The VS Code surface is deferred, not decided

The hypothesis leaves the VS Code mount surface as an open question "to be decided in this EGM process" but then says the user will verify later in front of VS Code. Design 005's acceptance matrix already documents that the VS Code Copilot harness reads the same `~/.copilot/copilot-instructions.md` as Copilot CLI, which `install_copilot.sh` already symlinks. What genuinely remains open is narrower than the hypothesis suggests: multi-profile VS Code (per-profile storage), relocated `COPILOT_HOME`, and the newer repo-level `.github/copilot-instructions.md` / prompt-file surfaces. These should be framed as explicit options to settle in `/egm-draft`, with runtime verification in front of VS Code as an acceptance step, not as an afterthought.

### 4. "Bump on every merge" has no compliant automation

`rules/global-agents.md` forbids installing hooks or changing Git configuration automatically, merging is human-only, and design 006 explicitly excludes `.github/workflows/` CI gates. That rules out a post-merge hook or a GitHub Action as the bump trigger. The only trigger consistent with the repo's own governance is manual-in-PR: a PR template checklist item, a `CHANGELOG.md` entry under `## [Unreleased]` in the same PR (issue #20 already demands changelog synchronisation with delivery), a small explicit script check that the version was bumped, and the human merger creating the annotated tag `vX.Y.Z` at merge time. Starting at `v0.1.0` is honest, since no tags exist today; the changelog must also state that consumption is live from the anchor, so tags are provenance labels, not release artefacts.

### 5. The installer-per-harness contract needs one written page

Each harness currently improvises. Design 007 should fix one contract for `scripts/install_<harness>.sh`: normalised absolute client-root override (`GEMINI_HOME`, `COPILOT_HOME`, and a new validated `OMP_AGENT_DIR`-style override for omp) with the same containment checks (client root may not live inside the anchor or the checkout); preflight classification of every destination as missing / correct-link / conflict, with zero writes on any conflict; atomic create-if-absent via Python's `os.symlink` so a destination appearing after preflight is never followed or overwritten; `--check` as a read-only report (exit 0 all-correct, exit 1 otherwise, no writes); config writes (agy `skills.json`, omp `config.yml`) held to the same preflight discipline plus atomic temp-plus-rename; and honest partial-state reporting after runtime failures (no rollback claims; rerun `--check`).

### 6. Issue #23 closure and issue #19 evidence are procedural, not code

Closing #23 with a comment is only legitimate after the merged PR and must record what was audited, when, on which machine: `~/.gemini/config/mcp_config.json` is empty (0 bytes), no backup scripts, MCP templates, or user sidecars exist under `~/.gemini/config`, and the non-empty personal files (`config.json`, `vibe_models.json`, `skills.json`, `import_manifest.json`) were reviewed and deliberately left in place as personal client state. Design 005 requires #23 to stay partial until the deferred audit is delivered or split into tracked follow-ups, so the comment must say "nothing to migrate" with that evidence, not just assert it. For #19, design 005 already defines the required fresh-client acceptance rows (Antigravity, Copilot CLI default home, VS Code Copilot harness default home, Copilot CLI with `COPILOT_HOME`); design 007 adds omp rows. Each row needs the client surface, version, harness/profile, effective home or override, policy path, a fresh-session identifier, and native inclusion evidence showing the policy content in the session — file existence is not inclusion evidence. #19 stays open until every required row passes.

### 7. Risks and edge cases the plan must carry

* Broken symlinks: if the checkout moves or is deleted, the anchor dangles and every link through it breaks. `--check` must classify dangling links as conflicts, and lint must keep reading the physical checkout rather than the anchor, so a green lint run must never be read as mount health.
* Profiles: `OMP_PROFILE` / `PI_CODING_AGENT_DIR` can relocate omp's agent directory away from `~/.omp/agent`. The omp installer must either validate a relocated root like the other overrides or refuse explicitly and document relocated profiles as installer-test-only.
* Worktrees: `repo_root` is derived from the script's own path, so a git worktree of artifice installs fine, but the anchor can point at only one physical checkout; a link to a second worktree must surface as a conflict because `--check` compares resolved physical targets.
* Lint ceilings and word budgets: `scripts/lint.py` enforces 140 lines / 1,400 words on the global policy, 180 lines / 1,000 words per skill, and 900 words per agent file. `agents/code-author/agent.md` is already within a few words of the 900-word ceiling (issue #32), so persona edits must be word-neutral, and design 007 must decide whether `integrations/<harness>/` adapter files count against agent budgets (keep them thin either way) and keep README growth economical.
* Partial installs: a runtime failure after a successful preflight can leave earlier registrations in place; the existing rule — no rollback claims, rerun `--check` — must extend to the `config.yml` write.

### 8. What is genuinely new is small

Most of #25 is already built: the anchor, the two installers, the governance tests, and the canonical `agents/` / `skills/` / `rules/` layout all exist and pass. The real new work is `scripts/install_omp.sh`, `integrations/omp/`, the `config.yml` entry handling, the VS Code decision, the versioning mechanics, and the evidence matrix. A parameterised "installer framework" shared across three harnesses would be over-engineering; the registrations differ in kind (symlinks versus `skills.json` versus a `config.yml` entry), so copying the proven installer shape per harness is the boring, correct choice.

## Goals vs. Non-Goals

### In-Scope Goals

* One installer contract per harness (`agy`, `omp`, Copilot/VS Code), each with `integrations/<harness>/` thin adapters and a non-overwriting `scripts/install_<harness>.sh` supporting `--check` and conflict-safe atomic preflight.
* `AGENTS.md` unified as a symlink to `rules/global-agents.md` wherever the harness follows symlinks, with the current regular-file drift handled as a documented manual migration (conflict today, never auto-adopted).
* omp mounting: `~/.omp/agent/AGENTS.md` and `~/.omp/agent/agents` symlinks plus the `skills.customDirectories` entry in `~/.omp/agent/config.yml`, with an explicit merge-versus-fail decision for an existing key.
* The VS Code mount surface decided in `/egm-draft`, with front-of-VS-Code verification as acceptance.
* The #23 "nothing to migrate" closure comment after the PR merges, with the audit evidence recorded.
* The #19 fresh-client evidence matrix contents, including omp-via-Paseo, agy, and VS Code sessions.
* Semver versioning from `v0.1.0`: Keep a Changelog `CHANGELOG.md`, annotated tag `vX.Y.Z` on every merge to main, triggered manually in the PR with the human merger creating the tag.
* `lint.py` and `tests/` coverage for the new installer and `integrations/omp/`.

### Out-of-Scope Non-Goals

* Issue #28 (hybrid agy + omp headless worker) stays deferred to its own PR after the omp mount exists (per design 006).
* No automatic Git hooks, no Git configuration changes, no `.github/workflows/` CI gates for the version bump.
* No silent merging, backing up, or adopting of personal files (`AGENTS.md`, `config.yml`, `config.json`, `vibe_models.json`).
* No whole-directory symlink of `~/.omp/agent/skills` (it would redirect omp's native user-skill writes into the checkout; recorded in the #30 comment).
* No compiled or packaged distribution of `scripts/` (pyproject, FastMCP) — #25 keeps the zero-latency symlink architecture.
* No migration of non-empty personal agy config files into the repository.
* Relocated-profile mounts (custom `OMP_PROFILE` / `PI_CODING_AGENT_DIR`, explicit `GEMINI_HOME` / `COPILOT_HOME`) are installer-test-only unless separately runtime-verified.

## Alternatives Weighed

### Whole-directory symlink `~/.omp/agent/skills -> anchor/skills`

Rejected because a whole-directory symlink redirects omp's native user-skill writes into the artifice checkout, corrupting the read-only canonical resource (recorded in the #30 comment). The `skills.customDirectories` config entry keeps native skills local and artifice skills read-only through the anchor.

### Per-skill symlinks under `~/.omp/agent/skills/<name>/`

Rejected as the default because it multiplies the destinations the installer must preflight and race-check for each new skill, while the single `customDirectories` entry achieves the same discovery with one registration. Retained as a fallback if the `config.yml` write proves unsafe.

### Thin per-harness `AGENTS.md` adapter files instead of the symlink

Rejected as the default because it forks the canonical policy into per-harness copies, which is exactly the drift that #25's single-canonical-source architecture and design 005's one-policy-owner invariant exist to prevent. Adapters are kept only where a harness cannot follow symlinks or genuinely needs trimmed content; the current agy regular file is a manual-migration conflict, not a reason to switch strategy.

### Automatic merge, backup, or adoption of conflicting personal files during install

Rejected because design 005 makes existing personal files conflicts that abort the installer before any write, with manual migration guidance; automatic merging would change personal policy ownership.

### Automatic version bump via commit hook or GitHub Action on merge

Rejected because `rules/global-agents.md` forbids installing hooks or changing Git configuration automatically, merging is human-only, and design 006 excludes CI workflows. The bump is manual-in-PR with the human merger tagging `vX.Y.Z`.

### Consuming skills from tagged releases instead of the live anchor

Rejected because #25 enshrines the zero-latency symlink loop: prompts are edited in the checkout and consumed immediately. Tags and the changelog are provenance labels only.

### A shared parameterised installer framework across harnesses

Rejected because the three harnesses register different kinds of things (symlinks, `skills.json`, a `config.yml` entry) and the two existing installers already encode the safe pattern; duplicating that shape per harness is less code than a framework and easier to audit.

### Closing #23 immediately without the merged PR and audit evidence

Rejected because design 005 keeps #23 partial until the deferred audit is delivered or split into tracked follow-ups; the closure comment must follow the PR and record the empty-`mcp_config.json` evidence and the list of personal files deliberately left in place.

## Key Decisions & Staging for Next Steps

1. **Installer-per-harness contract (D1):** one written contract as in Analysis item 5 — normalised validated client-root overrides, missing/correct-link/conflict preflight with zero writes on conflict, atomic create-if-absent, read-only `--check`, atomic config writes, honest partial-state reporting. Applies to agy, omp, and Copilot/VS Code alike.
2. **AGENTS.md decision (D2):** symlink to `rules/global-agents.md` wherever possible; the current 3,601-byte regular file at `~/.gemini/config/AGENTS.md` is a conflict today and becomes a documented manual migration step, never an automatic adoption. Accepted 2026-11-17; the manual migration on artemis is tracked as #33.
3. **omp `config.yml` decision (D3):** decide merge versus fail in `/egm-draft` for an existing `skills.customDirectories` key with other directories. Default recommendation: fail-with-guidance; treat "anchor entry already present" as correct idempotent state; any write must be a narrow line-based append with atomic temp-plus-rename and a re-read before rename; `--check` reports the missing entry with zero writes. Accepted 2026-11-17: fail-with-guidance default, implemented in-PR by `install_omp.sh`; no separate issue needed.
4. **VS Code decision (D4):** decide the mount surface in `/egm-draft` — default-home VS Code Copilot is already covered by `install_copilot.sh`'s `~/.copilot/copilot-instructions.md` symlink (design 005 matrix); the open remainder is profiles and repo-level prompt files. Verification in front of VS Code is an acceptance step. Accepted 2026-11-17; the surface decision plus in-front-of-VS-Code verification is tracked as #34.
5. **#23 closure mechanics (D5):** after the PR merges, comment on #23 with the audit evidence and close. Draft template: "Audited `~/.gemini/config` on 2026-11-17 on this host: `mcp_config.json` is empty (0 bytes); no backup scripts, MCP templates, or user sidecars exist. Non-empty personal files (`config.json`, `vibe_models.json`, `skills.json`, `import_manifest.json`) were reviewed and deliberately left in place as personal client state. Nothing to migrate. Canonical AGENTS.md ownership lives in `rules/global-agents.md` via the installer symlink. Closing."
6. **#19 evidence matrix (D6):** extend design 005's fresh-client acceptance matrix with omp-via-Paseo rows; each row records client surface, version, harness/profile, effective home or override, policy path, fresh-session identifier, and native inclusion evidence (policy content visible in the session, not file existence). #19 closes only when all required rows pass.
7. **Versioning mechanics (D7):** create `CHANGELOG.md` in Keep a Changelog format (`# Changelog`, `## [Unreleased]`, then `## [vX.Y.Z] - YYYY-MM-DD` with Added/Changed/Fixed sections); start at `v0.1.0`; every PR that delivers work adds its changelog entry under `## [Unreleased]` (issue #20); the PR template gains a checklist item that the version was bumped and the changelog entry exists; the human merger moves `## [Unreleased]` to `## [vX.Y.Z] - <date>` and creates the annotated tag `vX.Y.Z`. No hooks, no CI. The changelog states that consumption is live from the anchor, so tags mark provenance, not release artefacts. Accepted 2026-11-17: manual-in-PR bump on every merge to main; recurring enforcement overlaps #20 (changelog lifecycle), so no separate issue.
8. **Risk register (D8):** carry Analysis item 7 — broken-symlink handling, `OMP_PROFILE` / `PI_CODING_AGENT_DIR` profile relocation, worktrees competing for one anchor, lint ceilings and word budgets (including whether `integrations/<harness>/` adapters count against agent budgets and the near-ceiling `agents/code-author/agent.md`), and partial-install honesty.

Staging: Stage 1 — run `/egm-draft` on this brief to produce `docs/designs/007_*` and settle D3 and D4. Stage 2 — implement `scripts/install_omp.sh` plus `integrations/omp/` and their black-box tests. Stage 3 — perform and document the agy `AGENTS.md` manual migration, then verify the VS Code surface in front of VS Code. Stage 4 — introduce `CHANGELOG.md`, the PR template checklist, and the first `v0.1.0` tag. Stage 5 — collect the #19 evidence matrix rows and post the #23 closure comment. Issue #28 remains deferred until the omp mount exists.
