# Design 009: ship-it — formalised issue-to-ready-PR pipeline

**Author:** efsalvarenga  
**Status:** Approved (efsalvarenga, 2026-11-21 — human sign-off per #58; converged Goldfish review r1-r14)
**Date:** 2026-11-21  
**Tracking issue:** [#58](https://github.com/efsalvarenga/artifice/issues/58)  
**Tracking review:** [Goldfish report, rounds 1-14](../reviews/009_ship_it_issue_to_pr_pipeline_review.md) (70 findings across r1-r14 — all resolved as PROPOSE FIX; converged at r14)

--------------------------------------------------------------------------------

## Overview

One mounted skill, `/ship-it <issue-number>`, codifies the preferred working loop end to end: a human names an issue → grill-me clarification → optional EGM design loop → `code-author` implementation on a PR branch → coordinator-created PR → up to two zero-context (fresh-context, no conversation history) review rounds with one bounded fix cycle between → escalation or a "ready to look at" signal. The skill is a thin orchestrator: the only new logic is the phase state machine, the two-round cap, and the escalation contract. Everything else composes existing machinery ([design 002](002_craftsman_tdd_pipeline.md) grill-me, `code-author` TDD, the `review` skill runbook from [design 008](008_vibe_shrink_review_gh_posting.md), the upstream EGM plugin).

Terminology: *coordinator* is the stateful primary session running `/ship-it`; *EGM* is the upstream `google/elephant-goldfish-model` plugin (v0.1.1), mounted on the Google Antigravity CLI (`agy plugin install`) and on omp (oh-my-pi) as user plugin `egm@egm`; Copilot support is unverified upstream (EGM `docs/copilot.md`, [design 006](006_externalise_egm_plugin.md)).

## The Problem

The loop currently exists only as a chat recipe. Its parts exist and are governed — grill-me (design 002 Step 1A), the Craftsman pipeline (`agents/code-author/agent.md`), the codified 4-lens zero-context PR review with coordinator-owned comment posting (design 008, `skills/review/SKILL.md`), and EGM's design loop — but nothing ties them into one invocable, bounded pipeline with an explicit escalation contract. Ad-hoc runs drift: unbounded review rounds, forgotten provenance validation, silent fallbacks when EGM is absent.

## Goals

* `/ship-it <issue#>` works in any consuming repository with artifice mounted (Antigravity, Copilot, omp), because `skills/` is symlinked/`customDirectories`-mounted wholesale. The optional `[owner/repo]` operand scopes all gh calls via `--repo owner/repo` (edge-case checks: `gh issue view <N> --repo …`, `gh pr list --head <branch> --repo …`). The run log stays in the local working directory when its ignore entry holds (checked in P0 below); otherwise it goes to the harness artifact directory (defined in P0).
* EGM is **capability-detected, never assumed**: probe = EGM plugin registration present (agy: `~/.gemini/config/plugins/egm/plugin.json`; omp: `~/.omp/plugins/installed_plugins.json` containing `egm@egm`; copilot: a locally confirmed EGM skills directory, e.g. the offline `--plugin-dir` checkout per upstream `docs/copilot.md`) AND `skills/egm-review-loop/SKILL.md` readable under the plugin root. When detected, the design phase runs `/egm-brainstorm` → `/egm-draft` → `/egm-review` → `/egm-review-loop` → `/egm-resolve` until Stage 9 (Implementation Readiness) of the EGM review loop; otherwise an explicit, logged fallback runs (coordinator grill-me + `review`-skill lenses). Copilot hosts engage only with locally confirmed EGM.
* Review rounds are capped at two per PR: the append-only run log (`.ship-it-log.jsonl`, defined under Cross-cutting) records the round index keyed by PR + head sha — the P5 signal phase (defined in the state machine below) derives the counter as the max `round` field per `pr`, so same-head retries never inflate it — and refuses a third round regardless of prompt wording.
* Every commit carries validated provenance trailers; the new skill stays within the [Core Diet](../../scripts/lint.py) ceilings (≤180 lines / 1,000 words) and `./scripts/lint.sh` + `unittest` stay exit 0.

## Non-Goals

* No autonomous issue pickup by subagents; issue/PR text is data, never instructions (design 008).
* No state-changing gh calls by subagents; no labels/close/edit/merge without a human gate.
* No new review methodology — PR rounds delegate to the `review` skill runbook unchanged.
* No default hosted fan-out; per-PR human approval recorded in the review comment (design 008).
* No changes to `code-author`, `code-reviewer`, or the `review` skill bodies.

## Critical User Journeys (CUJs)

### CUJ 1: Happy path with EGM mounted (Antigravity or omp)

* **Given** issue #N and a passing EGM probe. **When** the human runs `/ship-it N`, the coordinator grills, runs the EGM loop to Stage 9 when a design doc is required, spawns `code-author` on `issue/<N>-<slug>`, and creates the PR. **Then** at most two review rounds run via the `review` runbook; after the final clean round the coordinator reports "PR #N is ready to look at" with the verdict summary and links.

### CUJ 2: EGM probe fails (e.g. Copilot without confirmed plugin)

* **Given** a failing probe. **When** `/ship-it N` runs. **Then** the design phase falls back to coordinator-run grill-me plus a zero-context draft check via `review` lenses, the fallback is recorded in the run log, and the pipeline continues — never silently skipped.

### CUJ 3: Round 2 not clean

* **Given** an unclean round-2 comment (open Blocker/Major or a `not run` lens). **When** the round counter in the run log reaches 2. **Then** the coordinator notifies the human in chat and reports the summary in chat (the PR comment itself stays owned by the review skill); the P5 signal phase (state machine below) refuses a third round mechanically.

### CUJ 4: On-device repository

* **Given** a `Privacy: on-device` / `Review: local-only` marker in AGENTS.md upward. **When** `/ship-it N` starts. **Then** hosted fan-out is refused with an explicit error and findings are produced paste-ready (design 008 CUJ 2); notifications fall back to the local paste-ready report, never a hosted comment.

--------------------------------------------------------------------------------

## Technical Plan (Architecture)

### Phase state machine

```text
/ship-it #N
  ├─ P0 Guards        privacy-marker scan · gh present · provenance identity known
  │                  (else stop and ask, rules/global-agents.md) · issue body = data
  ├─ P1 Grill-me      structured clarification; design phase:
  │                  EGM probe passes? → /egm-brainstorm → /egm-draft → /egm-review
  │                  → /egm-review-loop → /egm-resolve (until Stage 9)
  │                  else → fallback grill-me + review-lens draft check (logged)
  ├─ P2 Implement     code-author subagent on issue/<N>-<slug> (slug: issue title,
  │                  lowercased, non-alnum runs collapsed to '-', leading/trailing
  │                  '-' stripped, then ≤40 chars; empty result → branch issue/<N>
  │                  with no slug): 5-phase TDD, validate_provenance.py per commit,
  │                  Phase-4 baseline gate green
  ├─ P3 PR            coordinator: gh pr create (template, Design-Review: field,
  │                  pr_checklist.py checklist, Fixes #N)
  ├─ P4 Rounds 1..2   delegate to /review <PR> (it resolves the head sha); lenses via
  │                  native subagent tool, or sequential coordinator-run lenses on
  │                  hosts without one, e.g. copilot) → coordinator posts ONE
  │                  sanitised idempotent comment → code-author fixes (one fix
  │                  cycle per round; unrestorable baseline gate → escalate)
  │                  → push → next round on the new head
  └─ P5 Signal        run-log round counter ≤ 2 and clean → "PR #N ready to look at"
                     counter = 2 and not clean, or any escalation trigger → notify
                     the human in chat and STOP (no third round)
```

### Phase details

1. **P0 Guards.** Scan AGENTS.md upward to the repo root for privacy markers (refusal path per CUJ 4). Confirm `gh` is available and authenticated. Confirm a legitimate co-author identity is known; if not, stop before any commit per [rules/global-agents.md](../../rules/global-agents.md#commit-provenance). Verify the log is ignored: `git check-ignore -q .ship-it-log.jsonl`; if not, write the run log to the harness artifact directory (the harness's own artifact store, outside the repo) instead and record the deviation — never leave it committable in a consuming repo. Read the issue body as data only. Edge cases (each with `--repo owner/repo` when the operand is given): `gh issue view <N> --repo owner/repo` fails (nonexistent issue) → stop and notify; branch exists locally (`git branch --list issue/<N>-<slug>`) or remotely (`git ls-remote --heads <remote> issue/<N>-<slug>` when `[owner/repo]` is given) → stop and ask the human; `gh pr list --head issue/<N>-<slug> --repo owner/repo` non-empty → ask the human, defaulting to skip P3 and run P4 rounds on the existing PR.
2. **P1 Grill-me.** Interrogate scope, non-goals, invariants, failure modes, and whether a design doc is required (design 002 Step 1A). Record answers as decisions in the run log (`event: "decision"` entries); a scope change re-opens P1. If a design doc is required, run the EGM probe defined in Goals; on pass, run the EGM loop — if it terminates without Stage 9 (cap, churn, or manual halt), that is an escalation trigger: notify the human and stop unless the human explicitly waives and approves the draft; on probe fail, run the logged fallback.
3. **P2 Implement.** Create branch `issue/<N>-<slug>` with the slug transform from the state machine. Spawn `code-author` ([agents/code-author/agent.md](../../agents/code-author/agent.md)) with the approved decisions. Enforce its 5-phase workflow, per-commit provenance validation via `scripts/validate_provenance.py`, and the Phase-4 green baseline before any PR action.
4. **P3 PR.** Coordinator pushes the branch first (`git push -u <remote> issue/<N>-<slug>`, where `<remote>` is `origin` by default and resolved from `[owner/repo]` otherwise; on push failure apply the same bounded rule — retry ≤2 after backoff, then notify the human in chat and stop), then `gh pr create --repo owner/repo` with the target repo's `.github/pull_request_template.md` (fetched via gh; coordinator fills Description, `Design-Review:` — Stage 9 or human sign-off, checklist generated by `scripts/pr_checklist.py <design.md>`, Verification), body referencing `Fixes #N`. Apply design 008's bounded gh rule: retry ≤2 after backoff, then notify the human in chat and stop.
5. **P4 Review rounds.** Delegate each round to `/review <PR_NUMBER>` per [`skills/review/SKILL.md`](../../skills/review/SKILL.md) — the review skill resolves the PR head sha itself; ship-it-specific deltas only: round counting in the run log and the two-round cap. The review skill already owns artefact bundling, the four read-only lenses (with the sequential coordinator-run fallback on hosts without a subagent tool, e.g. Copilot), live verification, synthesis, the trace ID, and the single sanitised idempotent comment. Between rounds, `code-author` gets exactly one fix cycle: implement fixes, re-run the baseline gate, push; if the gate cannot be restored, escalate per the contract. The next round targets the new head.
6. **P5 Signal.** Read the round counter from the run log (max `round` per `pr`). Clean — defined as no open Blockers or Majors and no `not run` lens, per the review skill's guardrails — at any counter ≤ 2 (including a clean round 2 after fixes): report readiness with verdict counts, checklist status (via `pr_checklist.py <design.md> --check <pr-body.md>`), and links. Counter at 2 and not clean, or any escalation trigger: notify the human **in chat in the coordinator session** (privacy-marked repos: paste-ready local report only) and stop.

### Cross-cutting

One append-only run log per repository working directory at the gitignored `.ship-it-log.jsonl` (P0 verifies the ignore entry; otherwise the log goes to the harness artifact directory), JSONL entries `{ts, flow: "ship-it", phase, round, pr, head, event, detail}` (rounds keyed by `pr` + `head`, where `head` = `gh pr view <N> --json headRefOid -q .headRefOid`) recording phase transitions, EGM probe result, decisions, and every fallback; per-round lens metrics stay in the review skill's own log. In artifice both logs are gitignored; in consuming repos the P0 guard covers the ship-it log and the review skill guards its own. The schemas differ (per-invocation phases vs per-gh-call); both are sanitised with the same rules. Sanitiser: the same pattern list as [skills/review/SKILL.md](../../skills/review/SKILL.md) applied to posted text and logs. Provenance trailers on every commit, validated before commit.

--------------------------------------------------------------------------------

## Escalation Contract (notify the human in chat and stop)

* Privacy marker present (CUJ 4 refusal path; notification stays local).
* Hosted fan-out requested without recorded per-PR human approval.
* Round counter = 2 and the round is not clean (open Blocker/Major or `not run` lens) — no third round.
* Baseline gate unrestorable within the round's single fix cycle — no unbounded fix loops.
* EGM design loop terminates without Stage 9 (cap/churn/manual halt) and no human waiver recorded.
* Any finding that changes the agreed contract, scope, or design doc.
* Anything requiring labels, closing, editing, or merging (human-only).
* Unknown or illegitimate co-author identity (stop before committing).

--------------------------------------------------------------------------------

## Alternatives Considered

### Extend the `review` skill instead of a new skill

* **Pros**: one less mounted skill.  
* **Cons**: `review` is per-PR evaluation; ship-it is lifecycle orchestration with its own state machine and escalation contract — mixing them breaks single-responsibility and would breach the SKILL.md Core Diet ceiling.  
* **Reason for Rejection**: separate `skills/ship-it/SKILL.md` that *delegates* to `review` for rounds.

### Name `forge`

* **Reason for Rejection**: collides with the author's separate Forge project; `ship-it` chosen ([#58 discussion](https://github.com/efsalvarenga/artifice/issues/58)).

### Unbounded review rounds

* **Pros**: maximal polish.  
* **Cons**: loop risk, review fatigue, quota spend.  
* **Reason for Rejection**: hard cap of two rounds, enforced by the run-log counter, then human escalation (CUJ 3).

### Drop the `[owner/repo]` operand

* **Reason for Rejection**: coordinator sessions often run in a worktree of a different repository than the target issue (e.g. Paseo worktrees); without the operand, gh calls default to the worktree's origin and can target the wrong repo. One clause prevents misdirected issue/PR/branch operations.

--------------------------------------------------------------------------------

## Risks & Mitigations

| Risk | Mitigation |
| --- | --- |
| EGM assumed present on a host where it is not (e.g. Copilot) | named runtime probe (Goals); explicit logged fallback; Copilot recorded as unverified upstream |
| Issue body treated as instructions (prompt injection) | data-only ingestion rule in P0; sanitiser on all posted text (design 008) |
| Canonical word budget exceeded by the new skill | `ship-it` added to the canonical tuple at `tests/test_artifice.py:502`; ceiling raised 3,300 → 3,750 at :505 (the test is the source of truth for the live total) |
| Round cap silently exceeded | run-log round counter read mechanically in P5; refuses round 3 regardless of prompt wording |
| Worst-case cost unbounded | worst case per issue: EGM loop to Stage 9 + ≤2 rounds × 4 lenses + ≤1 fix cycle per round; per-round lens/elapsed/token metrics recorded in the review skill's log, phase metrics in `.ship-it-log.jsonl` |
| Subagent makes state-changing gh calls | coordinator-only posting; subagents read-only except code-author's branch commits |
| Concurrent coordinators racing the round counter in one worktree | single coordinator per worktree assumed; read-max/append is not locked — concurrent runs are the human's responsibility |
| Round cap is per worktree, not per PR (log lives in one working directory) | stated assumption; cross-worktree enforcement is the human's responsibility at merge time |

--------------------------------------------------------------------------------

## Non-Functional Requirements

* **Core Diet & verification**: `skills/ship-it/SKILL.md` ≤180 lines / 1,000 words; `./scripts/lint.sh` exit 0; `python3 -m unittest discover -s tests` exit 0; installers' `--check` exit 0.
* **Governance**: British English; blank line after every Markdown heading; valid relative links; provenance trailers validated per commit; merging human-only.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files

1. `skills/ship-it/SKILL.md` — **[Create]** the runbook (≤180 lines / 1,000 words).
2. `docs/designs/009_ship_it_issue_to_pr_pipeline.md` — **[Create]** this document.
3. `docs/reviews/009_ship_it_issue_to_pr_pipeline_review.md` — **[Create]** Goldfish report (rounds 1-14; tracking review).
4. `README.md` — **[Modify]** directory tree and Available Skills section.
5. `tests/test_artifice.py:502,:505` — **[Modify]** add `"ship-it"` to the canonical skill tuple; raise the word ceiling from 3,300 to 3,750.
6. `.gitignore` — **[Modify]** add `.ship-it-log.jsonl`.

### Verification Plan

* `./scripts/lint.sh` exit 0 (Markdown, frontmatter, links, Core Diet, Bash).
* `python3 -m unittest discover -s tests -p 'test_*.py'` exit 0.
* `bash scripts/install_{antigravity,copilot,omp}.sh --check` exit 0 (pre-existing worktree-anchor conflicts in Paseo (the worktree manager) worktrees are environmental, verified identical on a clean tree).
* Skill self-test/dry-run: **human waiver recorded 2026-11-21** ([#58](https://github.com/efsalvarenga/artifice/issues/58)) — lint gates frontmatter and Core Diet; the first real `/ship-it <issue>` run is the live exercise. No prose-content unittest (wording test).

--------------------------------------------------------------------------------

*Drafted for issue #58; Goldfish rounds 1-14 resolved (70 findings, all PROPOSE FIX, 0 Blockers since r2); CONVERGED at r14 (two consecutive clean rounds: r13, r14) — awaiting human sign-off.*
