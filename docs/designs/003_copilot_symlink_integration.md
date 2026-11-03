# Design Specification: Copilot Symlink Integration

**Document ID:** `docs/designs/003_copilot_symlink_integration.md`
**Status:** Approved
**Author:** GitHub Copilot & Developer
**Date:** 2026-11-03
**Target Milestone:** Cross-client Artifice integration

---

## 1. Overview & Objectives

Expose Artifice's three agent roles and four skills to GitHub Copilot through user-level symlinks, retaining the existing Antigravity entry points and one canonical copy of each workflow. No generated copies, synchronisation process, or per-project installation is required.

The developer confirmed local activation after testing, whole-directory registration links, client-specific global governance, and shared design-approval and Git-authorisation boundaries. On 2026-11-03, the developer explicitly approved the initial draft and subsequently approved this clarified revision: "the reviewed design is approved" followed by "go for it". Implementation remains conditional on independent Goldfish approval and targeted EGM validation.

### Goals

* Make existing and subsequently added components discoverable without rerunning installation while their parent registration directories remain unchanged.
* Separate Copilot tool configuration from shared role instructions rather than translating or duplicating entire agents.
* Resolve shared resources independently of the target repository and the client's treatment of symlink paths.
* Preserve Antigravity skill registration and agent headers; make shared procedure bodies client-neutral.
* Test installation in a temporary home before creating links on this Mac.

### Non-Goals

* Extensions, plugin packaging, MCP servers, runtime hooks, model downloads, background watchers, or automatic commits and pushes.
* Migration of Gemini global configuration into Artifice, or changes to either client's global rules.
* Enforcing approvals as a security boundary, guaranteeing independent reasoning, or making a cloud conversation air-gapped.
* Windows, remote-host provisioning, automatic merging of existing personal registration directories, or automatic checkout updates.
* Refactoring Ollama orchestration, changing model-selection algorithms, or fixing unrelated lint findings.

---

## 2. Domain Framing & User/System Experience

The user runs `bash scripts/install_copilot.sh` once from any working directory. Copilot discovers agents and skills in native personal locations. Subsequent Artifice edits are visible through those links; a fresh session or window reload may be required. Filesystem visibility does not imply immediate prompt-context refresh.

Agent selection establishes the role and tool configuration. Skills remain separately discoverable workflows; registration alone does not invoke them. The current repository supplies its own instructions, contracts, test commands, and working tree. Artifice supplies reusable procedures and utilities.

Antigravity continues reading the existing `agents/<role>/agent.md` definitions and its existing skill registration. Its tool lists remain intact. Shared wording must support both clients without importing Antigravity's YAML tool names into Copilot.

The shared resource anchor is preferred on this Mac and is created by the Copilot installer. Antigravity does not need to own or create it: when absent, its shared procedures resolve the physical agent or skill definition back to its Artifice checkout using the resource protocol below. Do not silently assume that the current working directory is Artifice. If neither source can be established, stop with an actionable diagnostic.

Copilot's personal directories and Antigravity's existing registration are separate discovery namespaces referencing the same checkout, not registrations with each other. The installer does not touch Gemini configuration or Antigravity registration. An Antigravity-only installation must continue working without running the Copilot installer.

---

## 3. State Schema & Data Models

### Repository Artefacts

```text
agents/<role>/agent.md                       Existing canonical roles
skills/<skill>/SKILL.md                      Existing shared workflows
integrations/copilot/agents/<role>.agent.md  Three new thin adapters
scripts/install_copilot.sh                   One Bash installer
tests/test_install_copilot.sh                Dependency-free installation tests
README.md                                   Setup, verification, recovery
```

Roles are `code-author`, `code-reviewer`, and `developer-coach`. Skills are initially `spec-egm`, `review`, `coach-frameworks`, and `local-code`. Copilot adapters contain only discovery metadata, tool permissions, and explicit role-loading instructions, not duplicate workflow bodies.

### Copilot Adapter Contract

Each adapter is UTF-8 Markdown with YAML frontmatter bounded by `---`. Required fields are `name`, matching the role, `description`, describing when to use it, and `tools`, containing that role's approved Copilot aliases. Omit `model` to inherit the current selection. The author adapter's complete structural example is:

```markdown
---
name: code-author
description: Implement approved specifications using contract-first TDD.
tools: [read, search, edit, execute, agent]
---

Before acting, use a read tool to open
`~/.local/share/artifice/agents/code-author/agent.md`.
Apply its Markdown body as the role instructions, subject to the client's
active higher-priority instructions. Its YAML frontmatter is Antigravity
metadata, not your tool configuration. If the file cannot be read, stop
and report the missing resource; do not act as a generic author.
Use the shared resource-resolution protocol in that body for Artifice assets.
```

This is a natural-language directive to use a tool, not an include field, automatic Markdown expansion, or custom parser. Successful tool-mediated reading is a live acceptance requirement. Reviewer and coach adapters use the same structure with their own role targets and tool lists. Shared role bodies must contain the resource protocol and must not require loading any other client's global metadata.

### Shared Resource-Resolution Protocol

This protocol lives in the existing shared role and skill Markdown bodies at their resource-entry sections. It is an instruction for the active agent using ordinary filesystem tools, not new runtime code, a helper daemon, or an Antigravity extension. Keep repetitions compact and limited to the seven entry points.

1. If `$HOME/.local/share/artifice` exists, resolve it to a physical directory and verify it contains the expected `agents`, `skills`, and `scripts` directories. A present but broken or invalid anchor is an error; do not silently substitute another checkout.
2. Only when the anchor is absent, use the actual definition path supplied by discovery or the read operation. Resolve its containing directory physically before ascending two directories. Both `agents/<role>/agent.md` and `skills/<skill>/SKILL.md` have this depth. Do not ascend a lexical symlink path before resolving its containing directory.
3. Validate that candidate checkout's `agents`, `skills`, and `scripts` directories and the particular requested resource exist and are readable. If the physical source path is unavailable or validation fails, stop and ask for the checkout location or installation repair; never guess from the target repository or a username-specific path.
4. Bind the resulting absolute directory as `ARTIFICE_ROOT` for the relevant shell command or explicitly resolved read path. It is a procedure-local value, not a persistent environment setting; do not assume it survives separate shell executions. Quote it when constructing commands and supply the target repository as a separate argument.

For example, without an anchor, a discovery path physically resolving to `/work/artifice/skills/spec-egm/SKILL.md` yields `ARTIFICE_ROOT=/work/artifice`, and the validator is `/work/artifice/scripts/validate_egm.py`. With the anchor installed, use the checkout that the anchor identifies instead. A target repository such as `/work/anvil` remains the validator's separate target, not a source for the utility.

### Registration Paths

| Field | Type and Constraint |
| --- | --- |
| Checkout root | Existing absolute physical directory, derived from the installer's own location, never from the current working directory. |
| Home | Existing absolute directory from `HOME`; reject unset, empty, or relative values. |
| Copilot home | Absolute directory from `COPILOT_HOME` when non-empty, otherwise `$HOME/.copilot`. Reject relative values. |
| Resource anchor | `$HOME/.local/share/artifice`, a symlink to the physical checkout root. |
| Agent registration | `<copilot-home>/agents`, a symlink to `<resource-anchor>/integrations/copilot/agents`. |
| Skill registration | `<copilot-home>/skills`, a symlink to `<resource-anchor>/skills`. |

All three destinations must be distinct and outside the checkout. Refuse configurations that would create a link cycle or put Copilot registration inside the shared skill or adapter sources. Existing parent paths must resolve to directories; report resolved installation locations before mutation.

Each destination is classified as `missing`, `correct-link`, or `conflict`. A correct link has the expected target, either literally or by resolving both existing directory targets to the same physical directory. A broken link, wrong link, real directory, or regular file is a conflict, not an invitation to replace it.

### Installer Interface

| Invocation | Behaviour |
| --- | --- |
| No options | Preflight every source and destination, then create only missing parents and links. |
| `--check` | Read-only verification of sources and all three links; never create directories or repair anything. |
| `--help` | Explain paths, options, limitations, and conflict recovery without mutation. |
| Unknown options or positional arguments | Report usage and exit non-zero without mutation. |

Exit `0` means installation is complete or the requested help was displayed. Exit `1` means validation, installation, or check failure. Exit `2` means invalid CLI usage. Correct-link destinations are left untouched.

---

## 4. Invariants & Rules

* **One source of truth:** No generated agents, copied skill trees, or translated workflow snapshots. Editing canonical role or skill content does not require installation to run again.
* **No destructive installation:** Never use force replacement, delete conflicting destinations, adopt existing real directories, or modify unrelated configuration. Preflight conflicts prevent all installation changes.
* **Idempotence:** Running installation repeatedly with correct links changes nothing. Whole-directory links expose additions and removals without per-component link maintenance.
* **Explicit role loading:** Copilot adapters direct the agent to read the canonical role's Markdown body before acting. Antigravity YAML frontmatter is not Copilot tool configuration. Failure to load the role stops execution rather than silently degrading to a generic agent.
* **Explicit tools:** Author permits `read`, `search`, `edit`, `execute`, and `agent`; reviewer permits `read`, `search`, `execute`, and `agent`; coach permits `read`, `search`, `edit`, `execute`, and `web`. Model selection is inherited. No wildcard permissions or platform-specific handoff assumptions.
* **Review posture:** The reviewer does not rewrite implementation. Terminal access is needed for baselines and is not a technical read-only sandbox; normal client approvals remain in force.
* **Resource ownership:** Resolve tools from Artifice and pass the target repository separately. Keep skill-local template references relative; replace ambiguous cross-directory references and hard-coded `~/Repos/artifice` commands with explicit resource-root instructions.
* **Client-specific governance:** Copilot uses its active instructions and target-repository rules. Read Gemini global rules only when operating in Antigravity and when that file exists. Do not make Gemini configuration a Copilot dependency.
* **Human design approval:** Present the specification and pause before any implementation. An approved Goldfish verdict or successful validator is not human approval. Material revisions require renewed approval; a generic autonomous goal is not an implicit waiver.
* **Git authorisation:** Require explicit user authorisation for branch changes, staging, commits, pushes, and PR publication. Authorisation is operation-specific; permission to create this branch does not permit commits or pushes. TDD phases can complete without commits. Preserve provenance conventions for authorised commits, without guessing a hidden model identity.
* **No false privacy claims:** `--local` in a cloud conversation does not establish air-gapped execution. For strict local-only requirements, stop before ingesting protected content and direct the user to a genuinely local session. Do not silently substitute cloud execution when local inference is required.
* **Compatibility:** Preserve agent and skill names unless a live discovery collision is demonstrated. Do not assume the Artifice `review` skill wins over any built-in command with the same name.

These are behavioural instructions, not deterministic enforcement. Runtime permissions and approval controls remain separate.

---

## 5. Execution & State Mutation Logic

### Installer

1. Parse options and validate the absolute home and Copilot-home paths. Use the macOS-provided Bash and filesystem utilities without new package dependencies.
2. Derive and validate the physical checkout. Verify the three adapters, the four existing skill entry points, their canonical roles, and the referenced script sources exist. New future components do not require a fixed installer manifest update.
3. Build the three-link plan and classify every destination before mutation. In check mode, report every missing or conflicting entry and exit without writes.
4. On installation, abort on any source, parent, or destination conflict before creating parents or links. Report the exact conflicting path and expected target.
5. Create required parents and missing links in dependency order: resource anchor, agents, skills. Quote all filesystem paths and preserve spaces. Recheck destinations before creating links; never intentionally write through an existing destination directory. This is a best-effort recheck, not synchronisation: if it fails, abort and perform rollback.
6. Track newly created links, their expected targets, and directories in in-process Bash arrays, adding entries only after successful creation. On a subsequent creation failure or catchable interruption, process those arrays in reverse order: remove only links still pointing to their expected targets and remove only newly created empty directories. Preserve pre-existing correct links. Report rollback failures explicitly. Do not persist a ledger or adopt artefacts left by earlier runs into the current rollback set.
7. Verify all registrations and report that filesystem installation succeeded, with live discovery still pending. Installation never invokes a model, Git write, repository workflow, or client settings migration.

Concurrent installers or external writes to installation destinations are unsupported; they are not made safe by preflight alone. Uncatchable termination or power loss may leave a partial installation, which `--check` must diagnose and a subsequent conflict-free install may complete.

### Shared Instructions and Adapters

1. Add three small Copilot adapters with meaningful descriptions, supported tool lists, and explicit canonical-role loading. Do not rely on Markdown links being automatically included or on unsupported inheritance syntax.
2. Make shared procedure bodies describe the current orchestrator and available delegation capabilities rather than requiring Gemini or Antigravity tool identifiers. Preserve local model workflows where requested and available; do not broaden them into a new orchestration implementation.
3. Apply the human approval and Git-authorisation rules to the author role, specification skill, and any other active shared instruction that would otherwise contradict them. Do not rewrite historical approved specifications as though these policies had always existed.
4. Keep resource paths that remain inside a skill directory as normal relative Markdown links. Express external stable-home resource paths as explicit inline paths and shell examples, with instructions to read the referenced file when needed. This avoids introducing a new Markdown-link resolver just for this integration.
5. Document one-time setup, `COPILOT_HOME`, the Antigravity resource-root fallback, reload expectations, conflict recovery, checkout movement, and manual removal of only owned symlinks. Do not add a force or automatic uninstall mechanism.

### Rollout and Approval

After the initial human approval, obtain a fresh Goldfish review, resolve findings, and re-present material design changes for approval. Before implementation, require both renewed explicit human approval of this revision and successful targeted EGM validation for `003`.

EGM means Elephant-Goldfish Model: a written design plus an independent adversarial review. The existing external gate is `scripts/validate_egm.py`, invoked from Artifice as `python3 scripts/validate_egm.py . --spec 003`. It checks required sections and a matching review with `Verdict: Approved`; it does not prove or replace human approval. Use the actual selected Python interpreter when executing the command.

After implementation passes temporary-home tests, activate the installation on this Mac under the user's existing authorisation. Any unexpected real-directory or unrelated-link conflict requires a new decision rather than automatic repair. Do not commit or push.

---

## 6. Edge Cases & Failure Modes

| Case | Required Outcome |
| --- | --- |
| Missing adapter, canonical role, skill, or script | Fail preflight before installation mutations. |
| Existing personal agents or skills directory | Refuse replacement, even when empty; report the whole-directory ownership conflict. |
| Broken or wrong destination symlink | Refuse replacement; `--check` fails and reports it. |
| Existing correct link written with an equivalent target | Accept after physical-target comparison; leave its text unchanged. |
| Spaces in home, checkout, or Copilot home | Install and verify successfully without shell splitting. |
| Invocation from another working directory | Resolve the same checkout and never create target-repository files. |
| Invalid parent, permission failure, or partial installation | Fail clearly; roll back only this invocation's new artefacts where possible. |
| Checkout moved or removed | Check fails; explicitly repoint the owned resource anchor after reviewing the new checkout. Never clone or fetch automatically. |
| New component after installation | Parent directory links expose it; request rediscovery or a fresh session, not regeneration. |
| Client ignores directory links or cannot read the target | Mark live acceptance failed; do not claim support or silently fall back to copies or settings edits. |
| `review` command collision | Test explicit skill selection; propose a separately approved name adjustment only if selection is unreliable. |
| Ollama absent or unavailable | Report the workflow dependency; installation itself remains independent of Ollama. |
| Copilot sandbox or trust restrictions block Artifice access | Report the denied resource and use normal client approvals; do not broaden permissions automatically. |

---

## 7. Verification & Automated Test Strategy

### Focused Automated Checks

* Run Bash syntax validation for installer and test harness. Tests use disposable checkout fixtures and temporary `HOME` and `COPILOT_HOME`; never mutate real personal registration.
* Verify clean installation, idempotent rerun, exact link targets, inherited and explicit Copilot homes, equivalent correct links, and invocation outside the checkout.
* Cover invalid CLI arguments, invalid homes, invalid source trees, wrong links, broken links, files, real directories, and non-directory parents. Assert that preflight failures leave all other destinations untouched.
* Verify `--check` succeeds only for complete valid registrations and has no filesystem side effects when anything is missing or conflicting.
* Induce a controlled link-creation failure after preflight; verify rollback preserves pre-existing paths and removes only new owned artefacts. Do not rely on permission-denial tests alone when executed with elevated privileges.
* Edit fixture role and skill content and add a fixture component after installation; confirm the same registration links expose the changes without rerunning installation.
* From the installed paths, verify access to canonical roles, skill-local references, and shared scripts. Test explicit home-path resource instructions rather than assuming symlink realpath resolution.
* Validate adapter names, descriptions, tool lists, and role targets; validate existing skill names and resource references. Run Artifice's native lint and targeted EGM checks, distinguishing pre-existing failures from regressions.

### Live Client Acceptance

Filesystem tests are necessary but do not prove Copilot discovery, tool configuration, instruction loading, command selection, or refresh behaviour. Verify on this Mac's installed VS Code and selected Copilot harness, recording versions and results.

1. Confirm all three agents and four skills appear in Customizations and the relevant picker or skill-selection UI. Check `review` specifically for a command collision.
2. Give each role a harmless read-only task that requires consulting its canonical definition. Inspect tool activity, available tools, and loaded resources; do not infer loading from the role's name alone.
3. Ask a skill to locate its template and shared utility without running the substantive workflow, downloading models, committing, or publishing anything.
4. Confirm a later source edit is discovered in a fresh session without installation changes. Do not require existing conversation context to refresh automatically.
5. Confirm Antigravity still discovers its original skills, loads the existing role definitions, and resolves resources with its existing registration. If unavailable, record this as an outstanding acceptance check, not a pass.
6. Verify specification-only requests stop for human approval and implementation does not imply permission to commit. Record these as behavioural smoke checks, not guarantees of enforcement.

### Specification Checkpoint

At draft time, check the eight template sections, heading spacing, pending approval state, and whitespace. The full EGM gate must remain blocked until a genuine matching Goldfish review exists; do not manufacture an approval artefact to make lint green.

---

## 8. Goldfish Review Gates

* [x] Initial specification presented to the human developer.
* [x] Initial human approval recorded on 2026-11-03: "I approve the spec."
* [x] Fresh Goldfish review completed; verdict is Revisions Required.
* [x] Adapter-loading, coexistence, resource-resolution, rollback-state, and EGM-gate clarifications drafted.
* [x] Revised specification explicitly approved by the human developer on 2026-11-03.
* [x] Follow-up independent Goldfish review approves the revised specification on 2026-11-03.
* [x] Targeted EGM validation for `003` passed before implementation.
* [x] Temporary-home installation and compatibility checks passed before local activation; expanded regression suite now covers 21 cases.
* [x] Live Copilot results and unavailable Antigravity/UI checks recorded below; outstanding checks are not claimed as passed.

**Human approval:** Both the initial and clarified designs were approved on 2026-11-03. Independent design review and targeted validation passed before implementation. Local installation was authorised and completed. On 2026-11-03, the developer additionally authorised commits on the feature branch, pushing that branch, and creating a GitHub pull request. Merging remains outside this authorisation.

### Acceptance Evidence (2026-11-03)

* **Automated:** Bash syntax validation, 21 disposable-home installation cases, full native governance lint, targeted EGM validation, adapter YAML/tool-list checks, and tracked whitespace checks passed. The optional Gemini global rules file is absent on this Mac; lint reports a warning, not a failure.
* **Installation:** The resource anchor and both whole-directory registration links were created without conflicts. Real-home installation rerun and `--check` passed idempotently. Shared scripts were not copied, models were not downloaded, and client settings were not changed.
* **Copilot runtime:** Registered `code-author`, `code-reviewer`, and `developer-coach` were each invoked through the custom-agent delegation mechanism and successfully read their canonical role body. They correctly reported explicit design approval, operation-specific Git permission, and client-specific global governance.
* **Skill resources:** Installed `spec-egm`, `coach-frameworks`, `review`, and `local-code` definitions were read through the personal skill registration. Template/rubric and shared-script locations resolved. These are resource-loading checks, not full workflow or local-model inference runs.
* **Implementation review:** Independent review identified physical-parent traversal, root-parent recursion, and interrupted-mutator rollback gaps. Focused failing regressions reproduced the gaps, and subsequent repairs pass the expanded harness. Concurrent external writes and uncatchable termination remain outside the approved guarantees.
* **Antigravity static compatibility:** Original agent tool lists were compared with the branch baseline and retained. Existing registration configuration was not touched. Anchor-free physical resource resolution is exercised in temporary fixtures.
* **Still outstanding:** Visual Customizations/picker discovery, the `review` slash-command collision check, effective UI tool permissions, and source-refresh behaviour in a new interactive chat. Live Antigravity discovery/loading is unavailable in this session and remains unverified. No cloud conversation was represented as air-gapped.
