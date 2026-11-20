# Goldfish Annotated Review Report — Design 008 (resolved)

**Status:** resolved

**Target:** `docs/designs/008_vibe_shrink_review_gh_posting.md` (full file)
**Findings source:** [consolidated review](008_vibe_shrink_review_gh_posting_review.md) — 10 zero-context Goldfish runs, Stages 5–9, trace ID `design-008-review`
**Resolution:** egm-resolve, 2026-11-20 — 24 PROPOSE FIX accepted ("auto accept"), 1 ESCALATE (B4) resolved by author fact, 1 CONTEST (M9) stands, 1 DECLINE (N7, already resolved at filing)

## Prioritized Findings & AI Suggestions

### B1 — Phase A deletion scope omitted real consumers — Severity: Blocker

*   **AI Suggestion:** PROPOSE FIX — **accepted.** Installers (`install_antigravity.sh:59-60`, `install_omp.sh:68-69`, `install_copilot.sh:58-59`), `test_artifice.py:24-27` + installer tests, README:129-158, design-004 retirement disposition, code-author `:92,:96` all added to Phase A scope.

### B2 — "no edits to code-author/agent.md" non-goal contradicted deletion scope — Severity: Blocker

*   **AI Suggestion:** PROPOSE FIX — **accepted.** Non-goal replaced by a word-neutral two-line trim (`:92`, `:96`) scoped into Phase A.

### B3 — per-phase lint-green unsatisfiable; phases are ordering only — Severity: Blocker

*   **AI Suggestion:** PROPOSE FIX — **accepted.** Goals/Overview/Cross-cutting now state one atomic commit per PR, `lint.sh` exit 0 at the PR checkpoint.

### B4 — Phase A+B leave privacy-marked repos with no review path; privacy downgraded to default-allow prose scan — Severity: Blocker

*   **AI Suggestion:** ESCALATE — **resolved by author fact 2026-11-20:** artifice carries no privacy-marked content (ou tier-0 owns its scaffolding per ou#84). Recorded in Phase A.3 + Risks: #41's on-device acceptance waived for artifice; on-device repos use the CUJ 2 paste-ready refusal path; refusal-only marker scan kept.

### B5 — DEFAULT mode (008:22) vs non-goal "no default-on fan-out before field trials" — Severity: Blocker

*   **AI Suggestion:** PROPOSE FIX — **accepted.** Non-goal reworded to *hosted* fan-out; #46 Stage-1 waiver recorded (author decision 2026-11-20, #45 evidence) in Non-Goals/Open Questions/Alternatives.

### B6 — `references/` placement self-contradiction — Severity: Blocker

*   **AI Suggestion:** PROPOSE FIX — **accepted.** `review-framework.md` stays as rubric home; runbook + Phase C checklist inline in SKILL.md; 008:47/008:53 wording fixed.

### B7 — missing Risks & Mitigations / Open Questions / CUJs / NFR / Detailed Implementation Plan — Severity: Blocker

*   **AI Suggestion:** PROPOSE FIX — **accepted.** All sections added per the 006/007 blueprint.

### M1–M10 — Majors

*   **M1** SKILL.md §§1–5 disposition — PROPOSE FIX **accepted** (replace body, keep rubric + persona link, drop `--local`).
*   **M2** test scope — PROPOSE FIX **accepted** (named imports/helper/test classes enumerated).
*   **M3** README scope — PROPOSE FIX **accepted** (line list enumerated).
*   **M4** diet allocation / script choice — PROPOSE FIX **accepted** (per-component budget: ≤6 / ≤60 lines+280 words / ≤20 lines+100 words; no-new-script kept).
*   **M5** guardrails — PROPOSE FIX **accepted** (retry-once + partial-pass block folded in; native-spawn timeout semantics defined; exit codes glossed).
*   **M6** Phase C mechanics — PROPOSE FIX **accepted** (run log at gitignored `.artifice-review-log.jsonl`, sanitised; trace ID `pr-<N>-<head-sha8>`; one bounded retry rule; own-comment edit within comment-only allowance).
*   **M7** copilot spawn fallback — PROPOSE FIX **accepted** (sequential coordinator-run lenses).
*   **M8** dispositions — PROPOSE FIX **accepted** (#46/#39/#24 added; header lists all tracked issues).
*   **M9** one-PR bundling — **CONTEST** — decision stands on the recorded author rejection (Alternatives) plus ou#84 closed; no change.
*   **M10** undefined terms — PROPOSE FIX **accepted** (terminology line added, mirroring 007:13).

### N1–N9 — Nits

*   **N1** "double tokens" → PROPOSE FIX **accepted** (reworded to hosted subprocess round-trip).
*   **N2** present-tense overclaims → PROPOSE FIX **accepted** (post-Phase-A framing).
*   **N3** "shrinks" → "deletes" — **accepted**.
*   **N4** gate wording → "satisfied" — **accepted**.
*   **N5** exit-code gloss, #29 link, AGENTS.md-upward boundary — **accepted**.
*   **N6** long sentences split, Overview trimmed, header conventions aligned — **accepted**.
*   **N7** root scratch files — **DECLINE** — already resolved at filing (folded into docs/, removed).
*   **N8** metrics to run log, comment carries counts/verdicts — **accepted**.
*   **N9** rejection attribution dated + linked — **accepted**.

## Handoff

24 fixes accepted and applied · 1 escalated (B4, resolved by author fact, recorded) · 1 contested (M9, stands) · 1 declined (N7, already resolved) · 0 remaining unaddressed.
Design Status: Draft → **Proposed**. Implementation authorisation remains human-only per #18 and rules/global-agents.md:13.
