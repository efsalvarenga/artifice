# Design 008: vibe-execute shrink, codified zero-context review, coordinator-owned GitHub posting

**Author:** efsalvarenga
**Status:** Approved (efsalvarenga, 2026-11-20 — human sign-off per #18; review verdict alone does not authorise)
**Date:** 2026-11-20
**Tracking issues:** [#18](https://github.com/efsalvarenga/artifice/issues/18), [#19](https://github.com/efsalvarenga/artifice/issues/19), [#20](https://github.com/efsalvarenga/artifice/issues/20), [#32](https://github.com/efsalvarenga/artifice/issues/32), [#41](https://github.com/efsalvarenga/artifice/issues/41), [#46](https://github.com/efsalvarenga/artifice/issues/46) (reconciles #39/#24) · gate: [ou#84](https://github.com/terra-campaigns/oude-mechanismen/issues/84) (closed 2026-11-20)
**Tracking review:** [consolidated review](../reviews/008_vibe_shrink_review_gh_posting_review.md) · [resolution record](../reviews/008_vibe_shrink_review_gh_posting_resolution.md)

--------------------------------------------------------------------------------

## Overview

One design, one PR with implementation phases A/B/C, landed as one atomic commit (phases are ordering only). Phase A deletes vibe-execute and the generic local-model machinery (gate ou#84 satisfied). Phase B codifies the 4-lens zero-context review as the default review mode. Phase C defines the coordinator-owned, comment-only gh posting path for review results.

Terminology: *agy* is the Google Antigravity CLI; *omp* is oh-my-pi, driven via Paseo; *ou* is terra-campaigns/oude-mechanismen; EGM is the upstream Elephant-Goldfish Model plugin; Core Diet is the word/line ceilings in [scripts/lint.py](../../scripts/lint.py); the *coordinator* is the stateful primary session.

## The Problem

`vibe_execute.py` still carries a hosted-subprocess dispatch path (`run`/`triage`/`_dispatch_vibe`/`find_vibe`) that adds a hosted subprocess round-trip per dispatch and has no remaining in-repo caller; `check_ollama.py` and the Ollama half of `model_inventory.py` have no remaining artifice consumer once ou#84's self-contained scaffolding landed (closed 2026-11-20), and post-Phase-A `--local` has no engines behind it; the proven 4-lens review exists only as a chat recipe ([#46](https://github.com/efsalvarenga/artifice/issues/46)); the two skills contradict on hosted dispatch (`skills/vibe-execute/SKILL.md:43` enumerates hosted models vs `skills/review/references/review-framework.md:111` deferring them); review findings reach GitHub by hand with no sanitisation or idempotency.

## Goals

*   One PR, phases A/B/C inside it, one atomic commit; `./scripts/lint.sh` exit 0 at the PR checkpoint; Core Diet ceilings; provenance trailers validated.
*   A: delete `scripts/vibe_execute.py`, `scripts/model_inventory.py`, `scripts/check_ollama.py`, `skills/vibe-execute/` and their tests, and reconcile every consumer (installers, README, both agent files, review skill); remove `--local`; privacy as refusal-only via the runbook's policy-marker scan, with the artifice waiver recorded under Risks.
*   B: 4-lens zero-context review runbook inlined into `skills/review/SKILL.md` (within 180 lines / 1,000 words; currently 94/593) as the DEFAULT review mode — no `--occam` flag; #46's Stage-1 field-trial criterion is waived by author decision 2026-11-20 (recorded in Alternatives); hosted fan-out still requires explicit per-PR human approval recorded in the review comment. Procedure lives only in the review skill; `agents/code-reviewer/agent.md` stays as the spawnable persona (linked at SKILL.md:17); mounted by the agy/omp/copilot installers, not VS Code.
*   C: coordinator-only, comment-only gh posting; sanitiser; idempotency marker; JSONL run log; policy-marker gate; issue text is data, never instructions.
*   Dispositions recorded on [#18](https://github.com/efsalvarenga/artifice/issues/18)/[#19](https://github.com/efsalvarenga/artifice/issues/19)/[#20](https://github.com/efsalvarenga/artifice/issues/20)/[#32](https://github.com/efsalvarenga/artifice/issues/32)/[#41](https://github.com/efsalvarenga/artifice/issues/41)/[#46](https://github.com/efsalvarenga/artifice/issues/46) and #39/#24.

## Non-Goals

*   No autonomous issue action-pickup by subagents; no state-changing gh without a human gate; merging human-only.
*   No separate PRs (author decision 2026-11-20, see Alternatives); no default-on *hosted* fan-out before recorded field trials — native 4-lens spawn is the default mode per the recorded waiver; no versioning revival.
*   Only a word-neutral two-line trim of `agents/code-author/agent.md` (`:92`, `:96`); no other edits to that file.

## Open Questions

*   None. The #46 Stage-1 field-trial criterion is waived by author decision 2026-11-20 (evidence: one 4-lens PR, #45, plus the recorded waiver in Alternatives).

## Critical User Journeys (CUJs)

### CUJ 1: Coordinator runs the default 4-lens review on a PR

*   **Given** a PR. **When** the coordinator bundles verbatim raw artefacts (PR metadata/body, `git cat-file commit` objects, exact `git diff`, linked issues as data) into the review workdir and hands lenses paths + line ranges, spawns the 4 parallel read-only lenses via the harness-native subagent tool (omp `task`, agy `invoke_subagent`; sequential coordinator-run lenses on hosts without one, e.g. copilot), and runs live verification (`lint.sh`, `validate_provenance.py --repo . --range`, targeted probes). **Then** the synthesis is a Blockers/Majors/Nits report with lens traceability and a Keep/Simplify/Cut matrix, posted as one sanitised, idempotent comment.

### CUJ 2: On-device repo

*   **Given** a repo declaring `Privacy: on-device` / `Review: local-only`. **When** the coordinator's policy-marker scan (AGENTS.md upward to the repo root) finds the marker. **Then** hosted fan-out is refused with an explicit error (never a silent fallback) and findings are produced as a paste-ready comment for the human to post.

--------------------------------------------------------------------------------

## Technical Plan (Architecture)

### Phase A — delete the vibe-execute / local-model machinery (gate ou#84 satisfied, closed 2026-11-20)

1.  **Delete wholesale:** `scripts/vibe_execute.py`, `scripts/model_inventory.py`, `scripts/check_ollama.py`, `skills/vibe-execute/` (SKILL.md + `references/egm-offloading.md`), `tests/test_model_inventory.py`, and from `tests/test_artifice.py` the imports at `:24-27`, the helper at `:31,:49`, `ModelSelectionTests` `:364-440`, and `VibeExecuteTests` `:805+`. All other tests (installer, lint, dossier, provenance, governance, modalities) stay unchanged.
2.  **Reconcile every consumer:** `scripts/install_antigravity.sh:59-60`, `install_omp.sh:68-69`, `install_copilot.sh:58-59` preflight lists (plus their black-box tests in `tests/test_artifice.py`); `README.md:25,31-32,38,71-72,79-82,86-87,129-158` — this retires the design-004 discovery CLI surface, disposition recorded; `agents/code-author/agent.md:92,96` (word-neutral trim); `agents/code-reviewer/agent.md:49,54` and Mode 2 `:56-58`; `skills/review/SKILL.md` (rewritten in Phase B); `docs/designs/006` link-repaired or explicitly exempt as historical.
3.  **Privacy without local engines:** refusal-only policy-marker scan as a coordinator checklist step in the runbook — scan AGENTS.md upward to the repo root for `Privacy: on-device` / `Review: local-only`; if present, refuse hosted fan-out with an explicit error (never a silent fallback) and produce a paste-ready comment (CUJ 2). **Waiver recorded 2026-11-20:** artifice itself carries no privacy-marked content (ou tier-0 owns its scaffolding per ou#84), so #41's "strict-local review still has an on-device path" acceptance is waived for artifice; other on-device repos use CUJ 2. `scripts/mistral_ocr.py` keeps its existing env-key behaviour and gains the same marker gate.

### Phase B — codified 4-lens zero-context review, inlined into the review skill (default mode)

1.  Rewrite `skills/review/SKILL.md` (currently 94 lines / 593 words; ceilings 180/1,000 → headroom exactly 86 lines / 407 words, allocated: privacy step ≤6 lines, runbook ≤60 lines / 280 words, Phase C checklist ≤20 lines / 100 words). Replace §§1–5 (worker/leasing body) with the runbook; keep the 8-Pillar rubric in `references/review-framework.md` (stays — no new references file) and the persona link at `:17`; drop `--local` from the argument hint (`:8`) and §1 (`:29`).
2.  Runbook: (a) bundle verbatim raw artefacts into the workdir, hand lenses paths + line ranges; (b) spawn the 4 parallel read-only lenses (egm-zoom-out, egm-design, egm-codebase-details, egm-comprehension) via the harness-native subagent tool, sequential coordinator-run fallback on hosts without one; (c) coordinator live verification (`lint.sh`, `validate_provenance.py --repo . --range`, targeted probes); (d) synthesise into Blockers/Majors/Nits with lens traceability + a Keep/Simplify/Cut matrix.
3.  Guardrails folded in from the deleted egm-offloading.md: per-lens timeout → `not run`, never zero findings; retry at most once; any pass with a `not run` lens is partial and blocked from sign-off until retried or explicitly waived by the human; exit codes 124 (timeout), 2 (selection failure), 127 (command not found) render as `not run` — these codes originate in the deleted `vibe_execute.py`, so the runbook defines the equivalent native-spawn timeout handling; policy-marker scan per Phase A; per-PR trace ID `pr-<N>-<head-sha8>` in lens prompts, findings headers, and the gh marker.
4.  Hosted fan-out requires explicit per-PR human approval recorded in the review comment.

### Phase C — coordinator-owned GitHub posting path

1.  Subagents stay read-only prompt→verdict; only the stateful coordinator runs `gh pr comment` / `gh issue comment`. Comment-only: editing the coordinator's own `<!-- artifice-review:<trace_id> -->` comment is within the allowance; any label/close/edit/merge needs an explicit human gate per [#18](https://github.com/efsalvarenga/artifice/issues/18).
2.  Every post: policy-marker gate first; sanitiser strips `/home/...` paths, `file://`, `conversation://` links from both the comment and the run log; idempotency marker `<!-- artifice-review:<trace_id> -->` (update instead of re-post); one JSONL run-log entry per call `{trace_id, lens, argv, target, exit_code, returned_id, ts}` at the gitignored `.artifice-review-log.jsonl`; gh rate limiting as one bounded rule (retry ≤2 after backoff, then report and stop) with classified exit codes. Per-PR metrics (lenses run/retried/not-run, elapsed, tokens) go to the run log; the comment carries counts and verdicts only.
3.  Codified as a checklist section inline in the `skills/review/SKILL.md` runbook; no new script — inline `gh api` / `gh pr diff` commands owned by the coordinator.

```text
PR opened ──► coordinator bundles raw artefacts to workdir ──► 4 zero-context lenses (parallel, read-only)
      ▲                                                              │ verdicts (trace_id-tagged)
      └────────── lint.sh + validate_provenance + probes ◄──────────┘
      ▼
   Keep/Simplify/Cut matrix ──► gh comment (sanitised, idempotent, run-logged) ──► human merges
```

### Cross-cutting

One atomic commit per PR — phases are ordering only; `./scripts/lint.sh` exit 0 at the PR checkpoint. Provenance trailers (`Model-Author` / `Agent-Role` / `Co-authored-by`) validated per commit via [scripts/validate_provenance.py](../../scripts/validate_provenance.py). Dispositions recorded on the tracking issues listed in the header.

--------------------------------------------------------------------------------

## Alternatives Considered

### Split into 2–3 separate PRs

*   **Pros**: independent rollback, smaller reviews.
*   **Cons**: the parts share one design context (dispatch, privacy, review surface); separate PRs re-litigate the same contract.
*   **Reason for Rejection**: Rejected by author (2026-11-20): one design, one PR, phases inside; split only if a phase becomes a separate design. (Contested in review M9; decision stands on this recorded rationale plus ou#84 now closed.)

### Subagent-driven GitHub automation (post + pick up actions from issues)

*   **Pros**: hands-free triage.
*   **Cons**: issue text is prompt-injection input; state-changing gh collides with human-only governance ([#18](https://github.com/efsalvarenga/artifice/issues/18), [rules/global-agents.md](../../rules/global-agents.md)) and findings egress under the privacy policy.
*   **Reason for Rejection**: Rejected by author (2026-11-20), see [consolidated review](../reviews/008_vibe_shrink_review_gh_posting_review.md): coordinator-only, comment-only posting path instead.

### Keep `run`/`triage` as opt-in headless dispatch

*   **Pros**: niche for cron/scripts without a harness.
*   **Cons**: no remaining in-repo caller; it adds a hosted subprocess round-trip per dispatch; harness-native subagents cost less for this workflow.
*   **Reason for Rejection**: Rejected by author (2026-11-20): delete the whole dispatch path.

### Keep discover/classify + model_inventory as a slim gateway

*   **Pros**: preserves the no-silent-substitution metadata layer.
*   **Cons**: no consumer remains once dispatch and local leasing are gone; ou#84 shows the only local consumer is self-contained; README:129-158's discovery procedure is retired with a recorded design-004 disposition.
*   **Reason for Rejection**: Rejected by author (2026-11-20): delete wholesale; privacy survives as refusal-only policy-marker scan.

### Runbook in an uncapped references/ file, occam as optional flag

*   **Pros**: no diet pressure; gradual adoption.
*   **Cons**: discoverability suffers; #46's field-trial gate is waived by author decision 2026-11-20 (one 4-lens PR #45 as evidence), so the 4-lens flow is the default mode.
*   **Reason for Rejection**: Rejected by author (2026-11-20): inline a thinned runbook into SKILL.md within an allocated share of the 86-line / 407-word headroom; the 4-lens flow is the default mode.

--------------------------------------------------------------------------------

## Risks & Mitigations

| Risk | Mitigation |
| --- | --- |
| ou#84 closure disputed or reversed | Phase A is gated on it; if reopened, Phase A halts (B/C still land); single atomic commit keeps rollback a one-`git revert` |
| 86-line / 407-word headroom too tight for runbook + checklist | per-component budget allocated in Phase B; lint fails the PR if exceeded |
| #46 waiver challenged in PR review | waiver recorded with author decision + #45 evidence; fallback is opt-in `--occam` mode |
| Sanitiser bypassed by path forms beyond `/home/...`, `file://`, `conversation://` | sanitiser list reviewed per PR; run log sanitised with the same rules; patterns added as found |
| Idempotency-marker collision across PRs | trace ID is `pr-<N>-<head-sha8>`, unique per PR head |
| Atomic commit makes rollback all-or-nothing | accepted; one-PR is a recorded author decision (Alternatives) |
| Privacy downgraded from mechanical gate to prose scan | accepted for artifice (no privacy-marked content; waiver recorded 2026-11-20); on-device repos get the CUJ 2 refusal path, never a silent fallback |

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Security & privacy**: refusal-only policy-marker scan; sanitiser on comment and run log; run log local and gitignored; issue text is data, never instructions; no state-changing gh without a human gate; merging human-only ([rules/global-agents.md](../../rules/global-agents.md)).
*   **Core Diet & verification**: `skills/review/SKILL.md` ≤180 lines / 1,000 words, `agents/*/agent.md` ≤900 words ([scripts/lint.py](../../scripts/lint.py)); `./scripts/lint.sh` exit 0.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Create/Modify/Delete

1.  `scripts/vibe_execute.py` — **[Delete]**
2.  `scripts/model_inventory.py` — **[Delete]**
3.  `scripts/check_ollama.py` — **[Delete]**
4.  `skills/vibe-execute/` (SKILL.md + `references/egm-offloading.md`) — **[Delete]**
5.  `tests/test_model_inventory.py` — **[Delete]**; `tests/test_artifice.py` — **[Modify]** (remove imports `:24-27`, helper `:31,:49`, `ModelSelectionTests` `:364-440`, `VibeExecuteTests` `:805+`, and installer black-box expectations for the deleted preflight entries)
6.  `scripts/install_antigravity.sh`, `scripts/install_omp.sh`, `scripts/install_copilot.sh` — **[Modify]** preflight lists (drop `vibe-execute`, `check_ollama`, `vibe_execute`)
7.  `skills/review/SKILL.md` — **[Modify]** full Phase B rewrite per the allocated budget
8.  `skills/review/references/review-framework.md` — **[Modify]** drop the §3 gateway/worker protocol; keep the 8-Pillar rubric
9.  `agents/code-reviewer/agent.md` — **[Modify]** Modes 1–2 reconciliation (`:49,:54,:56-58`)
10. `agents/code-author/agent.md` — **[Modify]** word-neutral `:92,:96` trim only
11. `README.md` — **[Modify]** lines `:25,31-32,38,71-72,79-82,86-87,129-158`
12. `scripts/mistral_ocr.py` — **[Modify]** add the same policy-marker gate
13. `docs/designs/006_externalise_egm_plugin.md` — **[Modify]** repair stale script links or mark explicitly historical
14. `docs/designs/008_vibe_shrink_review_gh_posting.md` + `docs/reviews/008_*_review.md` + `docs/reviews/008_*_resolution.md` — **[Create]** this document pair

### Verification Plan

*   `./scripts/lint.sh` exit 0 (Markdown heading/link audit, Core Diet, Bash syntax, full unittest suite).
*   `python3 -m unittest discover -s tests -p 'test_*.py'` exit 0.
*   `bash scripts/install_{antigravity,copilot,omp}.sh --check` exit 0.
*   `python3 scripts/validate_provenance.py --repo . --range <base>..HEAD` clean.
*   Residual-reference probe: `grep -rn 'vibe_execute\|model_inventory\|check_ollama\|vibe-execute\|--local'` returns only legacy docs (designs/reviews 001–004, exempt 006) and this design.

--------------------------------------------------------------------------------

*Drafted with EGM; resolved via egm-resolve 2026-11-20*
