# Design Specification: Copilot Symlink Integration

**Document ID:** `docs/designs/003_copilot_symlink_integration.md`
**Status:** Approved
**Revision:** 2026-11-03 lean refactoring
**Author:** Copilot SDK assistant & Developer

## 1. Overview & Objectives

Retain three thin Copilot adapters, four shared skills and three directory symlinks while reducing duplicated prompts, installer complexity and documentation. Preserve Antigravity entry points, tools, existing authorisation and installer safety.

The developer confirmed safety over a 45-line target, validated per-task model overrides, strict `--local` privacy and override/anchor/legacy discovery. Earlier approvals and installation evidence remain in Git at `6e0579b`; they do not approve this revision.

Non-goals: new dependencies, generated copies, orchestration frameworks, downloads, global configuration changes, Windows, concurrent installers, personal activation or Git publication.

## 2. Domain Framing & User/System Experience

Installation from any working directory exposes source edits and future components without regeneration. Refresh may require a new conversation/window; filesystem visibility does not prove client discovery or instruction loading.

Canonical bodies follow active client/repository authority, including valid preauthorisation, without granting permissions. Design approval remains separate from Git permission. Only Antigravity optionally reads existing Gemini global rules. Strict local-only work requires a genuinely local session before protected-content ingestion; ordinary cloud-orchestrated Ollama use remains hybrid, never labelled offline.

## 3. State Schema & Data Models

| Field | Contract |
| --- | --- |
| Installer root | Absolute physical checkout derived from its script, never the consuming repository. |
| `HOME` | Existing absolute directory; unset, empty or relative fails. |
| Copilot home | Unset/empty `COPILOT_HOME` defaults to `$HOME/.copilot`; a non-empty relative value fails with exit 1 and no writes. |
| Resource anchor | `$HOME/.local/share/artifice` -> physical checkout. |
| Registrations | `<copilot-home>/agents` -> `<anchor>/integrations/copilot/agents`; `<copilot-home>/skills` -> `<anchor>/skills`. |
| Link state | `missing`, `correct-link` (valid literal/equivalent physical target), or `conflict` (including broken links and real directories). |

Roles: `code-author`, `code-reviewer`, `developer-coach`. Skills: `spec-egm`, `review`, `coach-frameworks`, `local-code`.

Adapters retain single-line `name`/`description`, an inline `tools` list and no `model`. Names match filenames; descriptions are non-empty. Author tools: `read, search, edit, execute, agent`; reviewer: `read, search, execute, agent`; coach: `read, search, edit, execute, web`. Require exactly these sets without duplicates/wildcards and a directive to read the matching canonical `agents/<role>/agent.md` body under the validated root before acting. Antigravity metadata is not Copilot tool configuration. Failed loading stops the role.

Resource precedence, expressed compactly in entry points: explicitly supplied `ARTIFICE_ROOT`, otherwise present anchor, otherwise `$HOME/Repos/artifice`. Validate only the selected source: a valid override ignores a broken lower-priority anchor. The selected path must be absolute, physically resolved and contain readable `agents`, `skills`, `scripts` plus the requested resource. Empty/invalid overrides and broken/invalid selected anchors fail without fallback. No definition path is required. Bind the quoted root per command; pass the consuming repository separately.

`ARTIFICE_CODE_MODEL` covers `code/logic/fim/tdd`; `ARTIFICE_PROSE_MODEL` covers `prose/docs/adr/architecture`. Validate only the requested task group's override; ignore the other variable even when invalid. Reject an explicitly empty selected override before querying Ollama. A non-empty override must exactly match an installed tag.

| Selected override / daemon | Selection / exit |
| --- | --- |
| Empty | Failure, `fallback: null`, exit 2. |
| Non-empty / offline | Failure with offline reason, `fallback: null`, exit 2. |
| Non-empty / online, installed | Exact configured tag, exit 0. |
| Non-empty / online, uninstalled | Failure with uninstalled-tag reason, `fallback: null`, exit 2. |
| Unset / offline | Failure with offline reason, `fallback: "cloud-flash"`, exit 2. |
| Unset / online | Existing defaults below; success exits 0, no suitable model exits 2 with advisory `"cloud-flash"` fallback. |

Defaults preserve installed-list order: coding first prefers tags containing `qwen2.5-coder:14b`, then `qwen2.5:14b`; prose selects the first containing `mistral-nemo`. Preserve `select --task`. Success JSON has exactly `model: string`, `resident: boolean` (selected tag currently resident), `fallback: null`; failure has exactly `model: null`, `fallback: null | "cloud-flash"`, `reason: non-empty string`. Fallback hints never authorise cloud execution.

## 4. Invariants & Rules

* One canonical workflow per role/skill; retain relative Markdown documentation links and skill-local references. Runtime resources use the validated root, not lexical traversal through personal symlinks.
* Destinations are distinct, outside the checkout and cycle-free. Validate physical parents; never overwrite/adopt conflicts, broaden permissions or alter client configuration.
* Preflight every source/destination before writing. `--check` never mutates; correct links retain their text. Installation remains independent of Ollama.
* Rollback removes only current-invocation links still targeting their expected sources and newly created empty directories, including mutations completed immediately before a failure/interruption. Preserve pre-existing paths; report cleanup failures.
* Model selection must feed warming, inference, review streams and truthful provenance consistently. Never invent identities or silently substitute for invalid overrides.
* Canonical skills remain <=180 lines and <=1,000 words; canonical agents <=900 words. Count `text.split()` words including frontmatter/code and `splitlines()` lines. Report the three role/four skill entry-point total against 4,129 words at `a219f8e`, aiming <=4,158; unmet targets require disclosure, never weakened safeguards.

## 5. Execution & State Mutation Logic

1. Parse no options/install, `--check`, `--help`; unknown/extra arguments exit 2 without mutation. Help/success exit 0; validation/install/check failures exit 1 with diagnostics.
2. Resolve/validate homes and checkout. Verify readable canonical roles, adapters, four skill entry points and `validate_egm.py`, `build_review_dossier.py`, `check_ollama.py`. Future components remain directory-discovered.
3. Plan/classify all three links and validate parents, distinctness and cycles before mutation. Report missing/conflicting paths; check mode exits here.
4. Create only missing parents/links in anchor, agents, skills order. Recheck destinations before mutation; track owned changes in-process and roll back in reverse order after failure or catchable interruption.
5. Verify all registrations. Report filesystem success separately from live acceptance.

Keep Bash compatibility. Simplify only where behavioural tests demonstrate equivalence. Native governance includes adapter validation, line/word budgets and Bash syntax checks; disposable-home runtime tests remain explicitly runnable.

## 6. Edge Cases & Failure Modes

Cover spaces, equivalent link targets, symlinked parents with `..`, non-directory/root parents, missing sources, moved checkouts, invalid homes/options, late mutator failure and interruption. Checkout movement requires explicit owned-anchor repair, never automatic replacement/fetching.

Concurrent installers and third-party changes to destinations/parent symlinks are unsupported, as is uncatchable termination. Diagnose partial installations with `--check`; complete only when conflict-free. Missing models/daemon fail local selection without downloads or implicit cloud execution. Client discovery/permission failures and `review` command collisions remain acceptance gaps, not permission to copy resources, rename skills or change settings.

## 7. Verification & Automated Test Strategy

Freeze expectations from the existing 21 installer fixture cases before refactoring, replacing source extraction/`eval` with black-box tests. Use disposable homes/checkouts and exact-scope cleanup, never personal registrations. Assert exit codes, exact targets, missing-only `--check` exit 1 without writes, idempotence, prior-path preservation and changed/new source visibility. Use mutator shims, not sleeps, to deterministically inject failure/interruption after successful creation but before bookkeeping; catchable interruption exits 1 and rolls back owned paths.

Standard-library tests mock Ollama: both task groups, ignored unrelated overrides, valid/shared tags, unset/empty/uninstalled overrides, defaults, daemon failure, JSON shapes and exit codes. Verify selected-tag use in warming, inference and provenance. Test adapter metadata/loading targets; budget boundaries 1,000/1,001 words, 900/901 words, 180/181 lines and long single-line payloads. Validate restored links and root-policy coverage, including text-only discovery, invalid selected roots, spaces and a separate consuming repository.

Run focused tests, installer Bash syntax/runtime tests, Python unittest discovery, targeted EGM validation, native lint and whitespace checks. Measure prompt, installer/harness and documentation totals. No test may load/download/unload models.

Live acceptance separately verifies three agents/four skills, actual canonical reads, effective tools, explicit `review` selection, fresh-session refresh, cloud-session `--local` refusal before protected reads and Antigravity operation without an anchor/definition path. Record locality evidence and unavailable checks as outstanding. Behavioural prose is not a technical sandbox or proof of privacy.

## 8. Goldfish Review Gates

* [x] Human planning decisions confirmed; implementation requested.
* [x] Clarified revision explicitly approved by the developer on 2026-11-03.
* [x] Independent zero-context Goldfish configuration follow-up approves this revision on 2026-11-03.
* [x] Material revisions reapproved; `python3 scripts/validate_egm.py . --spec 003` passed before `code-author` TDD.
* [x] Baselines, measured outcomes, independent implementation review and live acceptance gaps recorded.

Implementation does not authorise staging, commits, pushes, PR updates or personal activation. Preserve actual model/agent provenance for separately authorised Git operations.

**Implementation evidence (2026-11-03):** 77 Python tests, including 36 installer regressions, and all six native governance gates pass. Canonical prompts total 3,905 words. The installer is 196 lines; installer plus complete runtime harness is 655 lines versus 474 originally. Independent implementation review found one adapter-scalar validation defect; failing regressions reproduced it and the repair passes. See the [review record](../reviews/003_copilot_symlink_integration_review.md) for closure and live acceptance limits.
