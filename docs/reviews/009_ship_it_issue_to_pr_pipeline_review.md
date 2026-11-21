# Goldfish Review of Design 009 (ship-it) — Round design009-r1

**Target:** [docs/designs/009_ship_it_issue_to_pr_pipeline.md](../designs/009_ship_it_issue_to_pr_pipeline.md) (full file, lines 1-162 at review time)  
**Round ID:** design009-r1 · **Date:** 2026-11-21 · **Tracking issue:** [#58](https://github.com/efsalvarenga/artifice/issues/58)  
**Mode:** REVIEW (document audit)  
**Dispatch note:** omp `task` subagent spawning is disabled in this harness, so per the round rules the synthesizer ran all six lenses itself, sequentially, against the persona files and standards. No reviewer timed out or failed; none is `not run`.

## Reviewer Status

| Reviewer | Persona | Standard | Status |
| --- | --- | --- | --- |
| egm-design | design_critic.md | feature-spec-standard.md | completed |
| egm-structural | structural.md | feature-spec-standard.md | completed |
| egm-implementation-readiness | implementation_readiness.md | implementation-readiness-standard.md | completed |
| egm-comprehension | comprehension.md | feature-spec-standard.md | completed |
| egm-zoom-out | zoom_out.md | zoom-out-standard.md | completed |
| egm-codebase-details | codebase_details.md | feature-spec-standard.md | completed |

## Codebase facts verified while auditing

- `scripts/validate_provenance.py`, `scripts/pr_checklist.py`, `.github/pull_request_template.md` (with `Design-Review:` field), `rules/global-agents.md#commit-provenance`, `agents/code-author/agent.md` (5-phase TDD, Phase-4 gate, Stage-9-or-human-sign-off at :29), `skills/review/SKILL.md` (4 lenses at :36; trace ID `pr-<N>-<head-sha8>`; marker `<!-- artifice-review:<trace_id> -->`), `docs/designs/006_externalise_egm_plugin.md` — all exist as cited.
- `scripts/lint.py:32-33`: `SKILL_LINE_LIMIT = 180`, `SKILL_WORD_LIMIT = 1000`.
- `tests/test_artifice.py:496` is `test_live_repository_and_canonical_word_budget`; the canonical tuple at :500-502 and the word ceiling `assertLessEqual(total_words, 3750)` at :505.

## Findings (Blockers → Majors → Nits; 14 deduplicated)

### 🔴 Canonical word ceiling misstated as 3,300 (actual: 3,750)

* **Lens:** egm-codebase-details · **Scope:** design lines 131, 151
* The doc instructs "recalculate the 3,300-word ceiling", but `tests/test_artifice.py:505` asserts 3,750 and the tuple at :502 already contains `"ship-it"`. A document statement contradicting the code is a Blocker. **Fix:** reference the real 3,750 ceiling and the 3,300 → 3,750 raise.

### 🟡 P4 omits the sequential-lens fallback required on hosts without a subagent tool (Copilot)

* **Lens:** egm-design · **Scope:** design lines 23, 42-44, 85
* Goal claims Copilot support and CUJ 2 covers it, but P4 only says "spawn via the harness-native subagent tool"; `skills/review/SKILL.md:36` mandates "on hosts without one (e.g. copilot), fall back to sequential coordinator-run lenses". **Fix:** add the fallback to P4 and the state-machine diagram.

### 🟡 Two-round cap enforced only in prose

* **Lens:** egm-design · **Scope:** design lines 25, 72-74, 86, 98, 132
* **Fix:** make the round counter mechanical — the run log records the round index per PR head and P5 reads it and refuses a third round regardless of prompt wording.

### 🟡 Branch slug derivation undefined

* **Lens:** egm-implementation-readiness · **Scope:** `issue/<N>-<slug>`
* **Fix:** specify the transform: `gh issue view <N> --json title -q .title` → lowercase, non-alphanumeric runs to `-`, collapse, truncate to 40 chars.

### 🟡 EGM capability-detection mechanism unspecified

* **Lens:** egm-implementation-readiness · **Scope:** "capability-detected, never assumed"
* **Fix:** name the probe — plugin registration present (agy: `~/.gemini/config/plugins/egm/plugin.json`; omp: `~/.omp/plugins/installed_plugins.json` containing `egm@egm`) AND `skills/egm-review-loop/SKILL.md` readable under the plugin root; otherwise the logged fallback.

### 🟡 Run log path and schema undefined

* **Lens:** egm-implementation-readiness · **Scope:** design cross-cutting
* **Fix:** path `.ship-it-log.jsonl` (gitignored), JSONL fields `{ts, flow, phase, round, pr, head, event, detail}`; separate from `.artifice-review-log.jsonl` because the schema differs (per-invocation phases vs per-gh-call) — justification recorded.

### 🟡 No test plan or dry-run for the new skill itself

* **Lens:** egm-implementation-readiness · **Scope:** Verification Plan
* **Resolution:** explicit human waiver recorded 2026-11-21 (issue #58): lint gates frontmatter/Core Diet; the first real `/ship-it` run is the live exercise. No prose-content unittest (wording test).

### 🟢 Nits (8)

1. Link "Core Diet" to `../../scripts/lint.py` at first use (egm-comprehension).
2. Expand `agy` / `omp` at first use (egm-comprehension).
3. Gloss "Stage 9 (Implementation Readiness)" of the upstream EGM review loop at first use (egm-comprehension).
4. Expand `<head-sha8>` = first 8 hex chars of the PR head sha; state the `<!-- artifice-review:<trace_id> -->` marker (egm-comprehension).
5. Convert sibling-design and #58 references to relative links (egm-structural).
6. "Tracking review" placeholder → fill with this file's link (egm-structural).
7. Record worst-case cost budget: ≤ 2 rounds × 4 lenses + EGM design loop + fix cycles; per-phase lens/elapsed/token metrics in the run log (egm-design).
8. Specify the notify channel: chat message to the human in the coordinator session; privacy-marked repos → paste-ready local report only, never a hosted comment (egm-design). Plus: P4 should delegate to `skills/review/SKILL.md` instead of re-enumerating the runbook (egm-zoom-out).

## Severity totals

🔴 1 · 🟡 5 · 🟢 8 · **Total: 14** — all resolved as PROPOSE FIX (auto-accept, 2026-11-21); none contested.
# Goldfish Review Report

**Target:** `docs/designs/009_ship_it_issue_to_pr_pipeline.md` (full file, lines 1–170 at review time)
**Round ID:** design009-r2 · **Date:** 2026-11-21 · **Tracking issue:** [#58](https://github.com/efsalvarenga/artifice/issues/58)
**Mode:** REVIEW (document audit, round 2 — verifies round-1 repairs and hunts new gaps)
**Dispatch note:** omp `task` subagent spawning is disabled in this harness, so per the round rules the synthesizer ran all six lenses itself, sequentially, each persona file read first, auditing the full target against its standard. No reviewer timed out or failed; none is `not run`.

## Reviewer Status

| Reviewer | Persona | Standard | Status |
| --- | --- | --- | --- |
| egm-design | design_critic.md | feature-spec-standard.md | completed |
| egm-structural | structural.md | feature-spec-standard.md | completed |
| egm-implementation-readiness | implementation_readiness.md | implementation-readiness-standard.md | completed |
| egm-comprehension | comprehension.md | feature-spec-standard.md | completed |
| egm-zoom-out | zoom_out.md | zoom-out-standard.md | completed |
| egm-codebase-details | codebase_details.md | feature-spec-standard.md | completed |

## Round-1 Fix Verification (design009-r1, 14 findings — all landed, 0 re-opened)

| Round-1 finding | Status | Evidence in current file |
| --- | --- | --- |
| 🔴 Ceiling misstated as 3,300 | **landed** | :136 "ceiling raised 3,300 → 3,750 at :505"; code check: `tests/test_artifice.py:502` tuple contains `"ship-it"`, `:505` asserts `assertLessEqual(total_words, 3750)` |
| 🟡 P4 Copilot sequential-lens fallback | **landed** | state machine :73–75 "or sequential coordinator-run lenses on hosts without one (e.g. copilot)"; :90 delegates to `skills/review/SKILL.md` which mandates the fallback at its :36 |
| 🟡 Two-round cap mechanical | **landed** | :25, :79–81, :95 (run-log `round` field), :103, :137 — run-log counter read in P5, refuses round 3 regardless of prompt wording |
| 🟡 Slug transform | **landed** | :68–69 "slug: issue title, lowercased, non-alnum runs → '-', ≤40 chars" (edge cases still open — see egm-implementation-readiness-design009-r2-2) |
| 🟡 EGM probe named | **landed** | :24 probe paths verified real on this host: `~/.gemini/config/plugins/egm/plugin.json` exists; `~/.omp/plugins/installed_plugins.json` contains `"egm@egm"`; upstream plugin ships `skills/egm-review-loop/SKILL.md` |
| 🟡 Run log path + schema | **landed** | :95 `.ship-it-log.jsonl`, JSONL `{ts, flow: "ship-it", phase, round, pr, head, event, detail}`, gitignored (`.gitignore:8`), distinct from `.artifice-review-log.jsonl` (`.gitignore:7`) with justification |
| 🟡 Skill test/dry-run waiver | **landed** | :166 human waiver recorded 2026-11-21 (#58), no prose-content unittest |
| 🟢 Nit 1 Core Diet link | **landed** | :26 links `../../scripts/lint.py` (exists; constants at lint.py:32-33 = 180/1,000) |
| 🟢 Nit 2 agy/omp expansion | **landed** | :15 "Google Antigravity CLI", "omp (oh-my-pi)" |
| 🟢 Nit 3 Stage 9 gloss | **landed** | :24 "Stage 9 (Implementation Readiness)" |
| 🟢 Nit 4 head-sha8 gloss + marker | **landed** | :76–77 first 8 hex chars; `<!-- artifice-review:… -->` marker matches `skills/review/SKILL.md:40,:44` |
| 🟢 Nit 5 relative sibling/#58 links | **landed** | :7, :13, :15 relative; all resolve (checked every link in the file) |
| 🟢 Nit 6 tracking-review link | **landed** | :7 links `../reviews/009_ship_it_issue_to_pr_pipeline_review.md` (exists; reports 14 findings, matching :7's count) |
| 🟢 Nit 7 worst-case cost | **landed** | :138 worst-case budget + per-phase metrics in `.ship-it-log.jsonl` |
| 🟢 Nit 8 notify channel + P4 delegation | **landed** | :91 in-chat notification, privacy-marked repos paste-ready only; :90 delegates to the review skill (residual inconsistency — see egm-zoom-out-design009-r2-1) |

Codebase facts re-verified while auditing: `scripts/validate_provenance.py`, `scripts/pr_checklist.py`, `.github/pull_request_template.md` (`Design-Review:` field at :5), `rules/global-agents.md#commit-provenance`, `agents/code-author/agent.md` (5-phase TDD, Phase-4 gate, Stage-9-or-sign-off at :29), `skills/review/SKILL.md` (4 lenses + Copilot fallback :36, trace ID :40, marker :44), `docs/designs/006_externalise_egm_plugin.md` (Copilot scope), `scripts/lint.py:32-33`, `tests/test_artifice.py:500-505`, `skills/ship-it/SKILL.md` (61 lines / 596 words, within 180/1,000), README ship-it entries (:35, :78-81) — all exist as cited.

## Prioritized Findings (Blockers → Majors → Nits)

All 7 findings are **NEW**; **0 round-1 findings re-opened** (no settled finding regressed).

### Broken relative link to the review skill — Severity: 🔴 Blocker

* **ID:** egm-structural-design009-r2-1 (confirmed by egm-codebase-details)
* **Reviewer Lens:** egm-structural
* **Affected Scope:** line 90 (`[\`skills/review/SKILL.md\`](../review/SKILL.md)`)
* **Discrepancy Description:** The link target `../review/SKILL.md` resolves from `docs/designs/` to `docs/review/SKILL.md`, which does not exist (`docs/` contains only `designs/` and `reviews/`); the correct target is `../../skills/review/SKILL.md`. Every other link in the file was resolved and passes. `scripts/lint.py` walks all Markdown under the target (`find_markdown_files`, :58-65, skipping only `.git`/`node_modules`/`.system_generated`) and fails on unresolvable relative links (:107-135), so this file as written makes `./scripts/lint.sh` exit non-zero.
* **Rationale & Recommendation:** This contradicts the document's own NFR (:145 "`./scripts/lint.sh` exit 0") and Verification Plan (:163) — the gate the doc claims green fails on the doc itself, and every later reader/CI inherits the failure. Fix: change the target at :90 to `../../skills/review/SKILL.md` (link text is already correct).

### Stale "actual total 3,720" word-count claim — Severity: 🟡 Major

* **ID:** egm-codebase-details-design009-r2-1
* **Reviewer Lens:** egm-codebase-details
* **Affected Scope:** line 136 (Risks & Mitigations, row "Canonical word budget exceeded by the new skill")
* **Discrepancy Description:** :136 states "(actual total 3,720)". Recomputing exactly as `tests/test_artifice.py:500-505` does (sum of `str.split()` word counts over the six canonical files: agents code-author 832, code-reviewer 542, developer-coach 616, skills review 572, coach-frameworks 521, ship-it 596) yields **3,679**, not 3,720. The actionable parts of the row are correct (tuple at :502 contains `"ship-it"`; ceiling 3,750 at :505); only the parenthetical metric is wrong.
* **Rationale & Recommendation:** A document stating a checkable number that the code does not reproduce is a false statement later readers inherit; the pinned number is also brittle by construction — any edit to a canonical file silently invalidates it. Fix: drop the parenthetical (the test itself is the source of truth) or date-stamp it ("3,679 as of 2026-11-21").

### "Clean" readiness criterion in P5 undefined — Severity: 🟡 Major

* **ID:** egm-implementation-readiness-design009-r2-1
* **Reviewer Lens:** egm-implementation-readiness
* **Affected Scope:** lines 40 ("after the final clean round"), 79 ("counter < 2 and clean"), 91 ("Clean within two rounds")
* **Discrepancy Description:** P5's readiness signal hinges on "clean", but the document never defines it — no Blockers only? no Blockers and no Majors? are Nits tolerated? `skills/review/SKILL.md` produces Blockers/Majors/Nits verdicts and blocks sign-off on any `not run` lens, but defines no "clean" verdict (grep confirms "clean" appears only in a provenance context in design 008). The escalation path is keyed to Blockers (:80-81, :103), so the round-1/round-2 readiness threshold is a genuine design decision left to the implementer, and it directly changes whether the human is notified.
* **Rationale & Recommendation:** Violates the Zero-Decision Rule of the implementation-readiness standard. Fix: define clean at P5, e.g. "no open Blockers or Majors and no `not run` lens (per the review skill's guardrails)".

### Forward references: "P5" and "the run log" used before definition — Severity: 🟢 Nit

* **ID:** egm-comprehension-design009-r2-1
* **Reviewer Lens:** egm-comprehension
* **Affected Scope:** line 25 (Goals) — first uses of "P5" and "the run log"
* **Discrepancy Description:** Line 25 says "the run log records the round index per PR head, and P5 reads that counter…", but the phase labels P0–P5 are only introduced by the state machine at :60-82 and the run log's path/schema only at :95. A naive reader hits both terms before any definition.
* **Rationale & Recommendation:** Self-containment gap for a fresh reader. Fix: gloss at first use ("the P5 signal phase, defined in the state machine below"; "the per-invocation run log `.ship-it-log.jsonl`, defined under Cross-cutting") or move the definitions earlier.

### Slug transform edge cases unspecified — Severity: 🟢 Nit

* **ID:** egm-implementation-readiness-design009-r2-2
* **Reviewer Lens:** egm-implementation-readiness
* **Affected Scope:** lines 68-69 (state machine P2); same gap in `skills/ship-it/SKILL.md:38`
* **Discrepancy Description:** "lowercased, non-alnum runs → '-', ≤40 chars" does not say what to do with leading/trailing hyphens produced by the transform (e.g. title "Hello, World!" → `hello-world-`), nor the empty/all-non-alnum title case, nor whether truncation to 40 happens before or after stripping (order changes the result).
* **Rationale & Recommendation:** Branch names like `issue/58-hello-world-` are ugly but valid, so this is not blocking; still, the transform is meant to be mechanical with zero implementer choices. Fix: specify "collapse runs, strip leading/trailing '-', then truncate to 40 chars; empty result → fall back to `issue-<N>`" (or equivalent) in both the design and the skill.

### Trace ID listed as a "ship-it-specific delta" though the review skill owns it — Severity: 🟢 Nit

* **ID:** egm-zoom-out-design009-r2-1
* **Reviewer Lens:** egm-zoom-out
* **Affected Scope:** line 90 ("ship-it-specific deltas only: round counting in the run log, trace ID `pr-<N>-<head-sha8>`, the two-round cap")
* **Discrepancy Description:** The same sentence states the review skill already owns the single sanitised idempotent comment, yet the delta list includes the trace ID `pr-<N>-<head-sha8>` — which originates in `skills/review/SKILL.md:40` and design 008, not in ship-it. The state-machine diagram (:73-78) also re-enumerates trace/marker/comment detail.
* **Rationale & Recommendation:** Round-1 nit 8 (delegate instead of re-enumerating) landed in substance — :90 delegates — but this residual self-contradiction invites an implementer to re-implement trace-ID logic in ship-it. Fix: drop the trace ID from the delta list (keep round counting and the two-round cap) and trim the diagram to "delegate to /review".

### P3 `gh pr create` does not inherit design 008's bounded gh retry rule — Severity: 🟢 Nit

* **ID:** egm-design-design009-r2-1
* **Reviewer Lens:** egm-design
* **Affected Scope:** lines 71-72, 89 (P3 PR creation)
* **Discrepancy Description:** Design 008 Phase C defines a bounded gh rule (retry ≤2 after backoff, then report and stop) for the coordinator-owned posting path. Design 009's P3 makes a coordinator `gh pr create` call but never references that rule, so a rate-limited or transient-failing PR creation has no specified failure behaviour.
* **Rationale & Recommendation:** Unmitigated operational edge on the one gh call ship-it owns outright (posting is delegated to the review skill, which has the rule). Fix: one clause in P3 — apply design 008's bounded retry (≤2 after backoff, then notify the human and stop), consistent with the Escalation Contract.

## Severity totals

🔴 1 · 🟡 2 · 🟢 4 · **Total: 7** — all NEW; re-opened round-1 findings: 0 of 14 (all verified landed).

---

*Round design009-r2 appended 2026-11-21: 6/6 lenses completed, 0 round-1 findings re-opened, 7 new (1 Blocker, 2 Majors, 4 Nits) — all resolved as PROPOSE FIX.*

--------------------------------------------------------------------------------

## Round design009-r3 (2026-11-21)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). Round-2 fixes verified landed; **0 of 7 re-opened** (and 0 of 14 from r1). New findings: 5 (0 Blocker, 2 Majors, 3 Nits), all resolved as PROPOSE FIX:

### 🟡 Stale status lines (:7, :170)

Doc said "awaiting round 2" while the linked review already held r2. **Fix:** tracking-review line and footer now cite rounds 1-3.

### 🟡 P5 terminal-state gap (:79-81, :91, :103, CUJ 3)

At counter = 2 with open Majors only (or a `not run` lens), neither the readiness nor the Blockers-only escalation branch fired. **Fix:** escalation now triggers on "counter = 2 and not clean" (open Blocker/Major or `not run` lens), in the diagram, P5, and the Escalation Contract.

### 🟢 Date-stamped word total stale (:136)

"3,679 as of 2026-11-21" went stale same-day (live total 3,688 after the r2 slug fix). **Fix:** parenthetical dropped; the test at `tests/test_artifice.py:505` is the source of truth.

### 🟢 Slug fallback ambiguity (:68-70, `skills/ship-it/SKILL.md:38`)

"empty → `issue-<N>`" would have yielded `issue/<N>-issue-<N>`. **Fix:** empty result → branch `issue/<N>` with no slug, in both files.

### 🟢 Copilot probe path unnamed (:24)

**Fix:** copilot probe = locally confirmed EGM skills directory (upstream `docs/copilot.md` offline `--plugin-dir` checkout); absent → logged fallback.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r3.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r4 (2026-11-21)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). Round-3 fixes verified landed; **0 re-opened** across all prior rounds. New findings: 5 (0 Blocker, 1 Major, 4 Nits), all resolved as PROPOSE FIX:

### 🟡 Unbounded fix cycles between rounds (:75-79, :91, :139, :100-107)

Only review rounds were capped, not fix cycles — undercutting the "bounded pipeline" premise. **Fix:** exactly one `code-author` fix cycle per round; unrestorable baseline gate is a new escalation trigger; worst-case budget updated to ≤1 fix cycle per round; mirrored in `skills/ship-it/SKILL.md`.

### 🟢 Run-log append semantics (:25, :96)

**Fix:** log is append-only JSONL per working directory; rounds keyed by `pr` + `head`.

### 🟢 P0 edge cases unspecified (:62-63, :87, :89)

**Fix:** nonexistent issue → stop and notify; existing branch → stop and ask; open PR on the branch → skip P3, run P4 on it.

### 🟢 "zero-context" unglossed (:13)

**Fix:** glossed at first use (fresh context, no conversation history).

### 🟢 Tracking-review wording (:157)

**Fix:** plan item now says "rounds 1-3 and counting".

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r4.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r5 (2026-11-21) — cap round

6/6 lenses completed (sequential in-harness dispatch; none `not run`). Round-4 fixes verified landed; live canonical total recomputed 3,746 ≤ 3,750. Findings: 4 (0 Blocker, 2 Majors, 2 Nits) — 1 re-opened, 3 new, all resolved as PROPOSE FIX:

### 🔁 🟡 Re-opened: header :7 stale (r3-era counts)

The r4 repair updated only the footer. **Fix:** header now cites rounds 1-5 (14+7+5+5+4 = 35).

### 🟡 Design/skill stop-condition mismatch (:100-109 vs SKILL.md:53)

The "finding that changes the agreed contract/scope" escalation bullet had been lost in an r4 edit. **Fix:** restored in the Escalation Contract.

### 🟢 Round-counter derivation undefined

**Fix:** P5 derives the counter as max `round` per `pr` in the append-only log; same-head retries never inflate it.

### 🟢 Cap is per worktree, not per PR

**Fix:** stated as an explicit assumption in Risks; cross-worktree enforcement is the human's at merge time.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r5.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r6 (2026-11-21) — past cap, human-approved continuation

6/6 lenses completed (sequential in-harness dispatch; none `not run`). Round-5 fixes verified landed; 0 prior re-openings regressed. Findings: 5 (0 Blocker, 1 Major, 4 Nits) — 1 re-opened, 4 new, all resolved as PROPOSE FIX:

### 🔁 🟢 Re-opened: "P5" forward reference (r2/r3 class)

The r5 rewrite of the Goals bullet dropped the "P5 signal phase (defined below)" gloss. **Fix:** gloss restored at :25 and CUJ 3 :48.

### 🟡 EGM loop can end without Stage 9

Upstream `/egm-review-loop` may terminate at cap/churn/manual halt. **Fix:** that is now an explicit escalation trigger (notify and stop) unless the human waives and approves the draft — P1 :89, Escalation Contract :107, SKILL.md:34/:53.

### 🟢 Plan item said "rounds 1-3" (:161)

**Fix:** now "rounds 1-6"; header/footer counts updated (40 findings total).

### 🟢 P4 "head sha" vs `/review` interface

**Fix:** P4 now invokes `/review <PR_NUMBER>`; the review skill resolves the head sha itself.

### 🟢 Skill escalation trigger missing "or design doc"

**Fix:** SKILL.md:53 now matches design :108.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r6.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r7 (2026-11-21)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). Round-6 fixes verified landed. Findings: 5 (0 Blocker, 1 Major, 4 Nits) — 1 re-opened, 4 new, all resolved as PROPOSE FIX:

### 🔁 🟢 Re-opened: "head sha" phrasing in diagram :75 and SKILL.md:47

**Fix:** both now delegate via `/review <PR_NUMBER>`; `head` acquisition specified as `gh pr view <N> --json headRefOid -q .headRefOid` (:97).

### 🟡 P5 readiness branch missed counter = 2 AND clean

The common fix-then-clean path (clean round 2) was an undefined terminal state in the diagram/skill. **Fix:** readiness = clean at any counter ≤ 2 (:81, :93, SKILL.md:51).

### 🟢 "Paseo" undefined (:171)

**Fix:** glossed as the worktree manager.

### 🟢 Lens metrics duplicated across two logs

**Fix:** per-round lens metrics stay in the review skill's log; `.ship-it-log.jsonl` keeps phase events only (:97, :142).

### 🟢 Concurrent coordinators could race the round counter

**Fix:** recorded as an assumption in Risks (:144) — single coordinator per worktree; no locking.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r7.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r8 (2026-11-21)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). All 45 settled round 1-7 findings verified still landed; **0 re-opened**. New: 3 Nits, 0 Blockers, 0 Majors — all resolved as PROPOSE FIX:

### 🟢 CUJ 3 "posts the summary" had no destination (:48)

**Fix:** summary is reported in chat; the PR comment stays owned by the review skill.

### 🟢 "Record answers as decisions" had no persistence target (:89)

**Fix:** decisions recorded as `event: "decision"` entries in `.ship-it-log.jsonl`.

### 🟢 CUJ 3 trigger narrower than the real one (:46-48)

**Fix:** CUJ 3 now triggers on any unclean round 2 (open Blocker/Major or `not run` lens), matching P5 :93 and Escalation :105.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r8.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r9 (2026-11-21)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). All 48 settled findings verified still landed; **0 re-opened**. New: 4 (0 Blockers, 1 Major, 3 Nits), all resolved as PROPOSE FIX:

### 🟡 Run log not gitignored in consuming repos (:23/:97/:165)

The ignore entry exists only in artifice's `.gitignore`. **Fix:** P0 now runs `git check-ignore -q .ship-it-log.jsonl`; if not ignored, the log goes to the harness artifact directory and the deviation is recorded — never committable in a consuming repo (:88, :97, SKILL.md:57).

### 🟢 CUJ 1 stated the EGM loop unconditionally (:40 vs :89)

**Fix:** CUJ 1 now conditions it on a design doc being required.

### 🟢 P5 "checklist status" had no acquisition command (:93, SKILL.md:51)

**Fix:** `pr_checklist.py --check` against the PR body, in both files.

### 🟢 Sanitiser pattern list duplicated (:97, SKILL.md:57)

**Fix:** both now cross-reference the review skill's list as the single source.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r9.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r10 (2026-11-21)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). All 52 settled findings verified still landed; **0 re-opened**. New: 3 Nits, all resolved as PROPOSE FIX:

### 🟢 `git check-ignore -q` missing operand (:88)

**Fix:** `git check-ignore -q .ship-it-log.jsonl`; "harness artifact directory" glossed at first use.

### 🟢 `pr_checklist.py` cited without mandatory operands (:91/:93, SKILL.md:51)

**Fix:** `pr_checklist.py <design.md> --check <pr-body.md>` everywhere.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r10.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r11 (2026-11-21)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). All 55 settled findings verified still landed; **0 re-opened**. New: 5 (0 Blockers, 2 Majors, 3 Nits), all resolved as PROPOSE FIX:

### 🟡 Design/skill contradiction on existing-PR edge case (:88 vs SKILL.md:29)

**Fix:** both now say ask the human, defaulting to skip P3 and run P4 on the existing PR.

### 🟡 check-ignore guard existed only in the design

**Fix:** SKILL.md P0 step 2 now runs `git check-ignore -q .ship-it-log.jsonl` with the artifact-dir fallback.

### 🟢 `[owner/repo]` operand undefined

**Fix:** Goals :23 defines it (`--repo owner/repo`; log stays local).

### 🟢 Bounded gh retry not mirrored in skill P3

**Fix:** SKILL.md:43 now carries retry ≤2 then notify and stop.

### 🟢 Footer claim "0 Blockers since r1" wrong (r2 had 1)

**Fix:** footer now says "0 Blockers since r2".

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r11.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r12 (2026-11-21)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). All 60 settled findings verified still landed; **0 re-opened**. New: 5 (0 Blockers, 1 Major, 4 Nits), all resolved as PROPOSE FIX:

### 🟡 Initial branch push before P3 unspecified (:68-91, :143)

**Fix:** P3 now pushes `issue/<N>-<slug>` (`git push -u origin`, remote per `[owner/repo]`) before `gh pr create`; mirrored in SKILL.md:43.

### 🟢 Log-location contradiction (:23 vs :88/:97)

**Fix:** log stays local only when the ignore entry holds; otherwise the harness artifact directory.

### 🟢 "both logs gitignored" overclaim for consuming repos (:97)

**Fix:** scoped to artifice; P0 guard covers ship-it's log elsewhere, the review skill guards its own.

### 🟢 PR-body assembly mechanics (:91)

**Fix:** template fetched from the target repo via gh; coordinator fills the sections.

### 🟢 Edge-case check commands under `[owner/repo]` (:88)

**Fix:** `gh issue view <N> --repo …`, `git branch --list`, `gh pr list --head <branch> --repo …`.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r12.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r13 (2026-11-21) — CLEAN (0 Blockers, 0 Majors)

6/6 lenses completed (sequential in-harness dispatch; none `not run`). All 65 settled findings verified still landed; **0 re-opened**. New: 3 Nits, all resolved as PROPOSE FIX:

### 🟢 Edge-case gh commands missing inline `--repo` (:88)

**Fix:** `gh issue view <N> --repo owner/repo`, `gh pr list --head <branch> --repo owner/repo`.

### 🟢 Push remote unnamed under `[owner/repo]` (:91)

**Fix:** `git push -u <remote> <branch>`, remote = origin by default, resolved from the operand otherwise; `gh pr create --repo owner/repo`.

### 🟢 `[owner/repo]` operand lacked recorded motivation

**Fix:** Alternatives entry added (worktree-of-another-repo hazard).

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r13.md` (session artifact, not committed).

--------------------------------------------------------------------------------

## Round design009-r14 (2026-11-21) — CLEAN → loop CONVERGED

6/6 lenses completed (sequential in-harness dispatch; none `not run`). All 68 settled findings verified still landed; **0 re-opened**. New: 2 Nits, all resolved as PROPOSE FIX:

### 🟢 Forward references at :23 ("P0 guard", "harness artifact directory")

**Fix:** glossed inline at first use.

### 🟢 Push failure behaviour and remote branch check unspecified (:91, :88)

**Fix:** push failure → bounded retry ≤2 then notify and stop (same rule as gh); remote branch check via `git ls-remote --heads <remote>` when `[owner/repo]` is given.

**Verdict: CONVERGED at r14** — r13 and r14 both clean (0 Blockers, 0 Majors, no `not run` lenses), all 68 prior findings verified landed each round. 70 findings total, all PROPOSE FIX.

Full raw report: `/tmp/egm-goldfish-context/goldfish_review_report_design009_r14.md` (session artifact, not committed).
