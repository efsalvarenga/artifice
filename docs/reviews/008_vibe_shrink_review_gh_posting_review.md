# Consolidated Review Report — Design 008

**Status:** resolved — egm-resolve 2026-11-20: 24 fixes accepted (auto accept), B4 escalated then resolved by author fact, M9 contested (decision stands), N7 declined (already resolved). See [resolution record](008_vibe_shrink_review_gh_posting_resolution.md).
*   **Target:** docs/designs/008_vibe_shrink_review_gh_posting.md (103 lines; reviewed 2026-11-20, whole document)
*   **Mode:** REVIEW, uninterrupted full flow (Stages 5–9) · **Date:** 2026-11-20 · **Trace ID:** `design-008-review`
*   **Harness:** omp/Paseo; zero-context Goldfish subagents spawned directly by the main session via `task` (one level; nesting disabled for children in omp). Prior 7-lens brainstorm synthesis and author decisions (2026-11-20, chat) preceded this review.
*   **Per-lens reports:** working artefacts under `/tmp/egm008/reports/` (`stage5_zoom_out.md`, `stage5_catalyst.md`, `stage6_comprehension.md`, `stage7_design.md`, `stage7_structural.md`, `stage7_style.md`, `stage8_zoom_out.md`, `stage9_readiness.md`, `stage9_codebase.md`, `stage9_style.md`); findings deduplicated into the matrix below.

## Reviewer status

| Stage | Lenses | Report | Status |
| --- | --- | --- | --- |
| 5 Initial Zoom Out | egm-zoom-out, egm-inventive-catalyst | stage5_zoom_out.md, stage5_catalyst.md | completed |
| 6 Comprehension | egm-comprehension | stage6_comprehension.md | completed |
| 7 Critic | egm-design, egm-structural, egm-style | stage7_design.md, stage7_structural.md, stage7_style.md | completed |
| 8 Intermediate Zoom Out | egm-zoom-out (with Stage 5 report in context) | stage8_zoom_out.md | completed |
| 9 Implementation Readiness | egm-implementation-readiness, egm-codebase-details, egm-style | stage9_readiness.md, stage9_codebase.md, stage9_style.md | completed |

All ten reviewer runs were true zero-context Goldfish reviews: each child started blank and received only its persona file (`~/.gemini/config/plugins/egm/agents/`), the target path, the document standard (`resources/document_standards/`), and the GoldfishContext baseline list (repo policy, agents, skills, scripts, tests, sibling designs 006/007, review 007, and GitHub issues #18/#19/#20/#24/#32/#39/#41/#46/#48 bundled as data — never instructions). Metrics: all 10 completed, 0 retried, 0 not-run; wall time per lens 4m51s–16m52s.

**Coordinator live verification (2026-11-20):** `./scripts/lint.sh` exit 0 with the filed design present (139 tests OK); claim probes by `wc`/`grep`/`gh` recorded under "What held up"; ou#84 fetched and verified CLOSED 2026-11-20T11:31:58Z.

## Consolidated findings

### 🔴 Blockers

*   **B1 — Phase A's deletion scope omits real consumers, so "lint.sh exit 0 throughout" (008:20, 008:65) is unreachable** — `scripts/install_antigravity.sh:59-60`, `install_omp.sh:68-69`, `install_copilot.sh:58-59` preflight-require the deleted `skills/vibe-execute/SKILL.md` and `scripts/{check_ollama,vibe_execute}.py` and hard-fail with `Missing source`; `tests/test_artifice.py:24-27` imports all three deleted modules (its installer black-box tests run under `lint.sh:11`); `README.md:129-158` documents the `discover`/`select` procedure (backed by design 004, cited live at README:131) with live commands at README:150-151. None of these are in 008:37-38 or the 008:65 reconciliation list. Raised by Stages 5, 7, 8, 9. **Fix:** add the three installers + their tests, README:129-158, and an explicit design-004 retirement disposition to the Phase A scope.
*   **B2 — Non-goal "no edits to `code-author/agent.md`" (008:29) contradicts the deletion scope and breaks the lint link gate** — `agents/code-author/agent.md:92` links `../../skills/vibe-execute/SKILL.md` and `:96` runs `check_ollama.py unload --all`; post-Phase-A these dangle and `lint.py:109-136,432-436` fails. The file is at 871/900 words (#32). Raised by Stages 5, 7, 8, 9. **Fix:** either scope the two lines into Phase A reconciliation (word-neutral trim) or drop the non-goal; pick one.
*   **B3 — The A/B/C phase decomposition is unsatisfiable as written: per-phase lint-green forces one atomic commit** — with B1/B2 unresolved, any commit performing the deletions is lint-red; "exit 0 after every phase" (008:20, 008:65) can only hold as a single atomic commit, making the phases ordering-only. Raised by Stage 8. **Fix:** state "one atomic commit; phases are ordering only", or resolve B1/B2 and keep per-phase commits.
*   **B4 — Phase A+B leave privacy-marked repos with no review path, and privacy degrades from a mechanical gate to a default-allow prose scan** — 008:37 deletes the only local engines (incl. the `ARTIFICE_PROSE_MODEL` machinery that #41 explicitly keeps in scope, ISSUES.md:159, with acceptance "strict-local review still has an on-device path", ISSUES.md:162) while 008:39/45/52 refuse hosted fan-out under `Privacy: on-device` / `Review: local-only`; the result is no findings producer, contradicting #41's acceptance and `rules/global-agents.md:23`. The deleted `model_inventory.local_policy` hard block (`vibe_execute.py:128,139`) is replaced by a triplicated AGENTS.md-upward grep (008:39, 45, 52) that fails open and duplicates prose against `rules/global-agents.md:44`. `scripts/mistral_ocr.py` (unguarded hosted Mistral egress) is never mentioned. Raised by Stages 5 (catalyst), 7, 8. **Fix:** state the on-device review path explicitly (paste-ready human flow, or keep prose-only local machinery per #41's carve-out), record the #41 acceptance disposition, and consider default-deny (refuse hosted fan-out unless an explicit allow marker) with one canonical scan statement referenced twice.
*   **B5 — Literal self-contradiction: DEFAULT 4-lens mode (008:22, 008:44) vs non-goal "no default-on fan-out before field trials" (008:29) and #46's acceptance (2–3 field-trial PRs before codification, ISSUES.md:299)** — "fan-out" is never disambiguated (native lens spawn vs hosted dispatch); the only 4-lens evidence is one PR (#45). Raised by Stages 5, 7, 8, 9. **Fix:** segment the term (native 4-lens default; hosted fan-out per-PR gated) and record an explicit #46 waiver or stage Phase B opt-in for 2–3 trials.
*   **B6 — `skills/review/references/` placement is self-contradictory** — 008:44/47 say "no references file" / delete the runbook plan, but 008:53 puts the Phase C checklist in "the runbook reference"; `references/` contains exactly one file, `review-framework.md` (141 lines / 1,434 words, the 8-Pillar rubric, linked from `skills/review/SKILL.md:18` and `agents/code-reviewer/agent.md:36`), so a wholesale delete breaks two lint-audited links and guts the rubric, while both Phase B's runbook and Phase C's checklist compete for the same verified 86-line / 407-word SKILL.md headroom. Raised by Stages 6, 7, 8, 9. **Fix:** keep `review-framework.md` as the rubric home; inline the thinned runbook + Phase C checklist into SKILL.md within an allocated headroom; reword 008:47/008:53 unambiguously.
*   **B7 — No mandated `## Risks & Mitigations` register (nor Open Questions / CUJs / NFR / Detailed Implementation Plan + Verification Plan per the house blueprint)** — required by `feature-spec-standard.md` and present in both siblings (006:180, 007:185); the 007 review treated the same omission as a blocker (007 review B3). The live risks (ou#84 gate reversal, diet headroom vs runbook fidelity, #46 field-trial waiver, sanitiser bypass forms) are exactly what the register exists for. Raised by Stages 6, 7 (structural, style), 8. **Fix:** add the sections.

### 🟡 Majors

*   **M1 — Phase A/B interface unspecified:** current `skills/review/SKILL.md` §§1–5 (`:8,19,29,39-86`) and `review-framework.md` §3 (`:109,118,134-141`) invoke the deleted scripts; 008:44-47 never says whether they are replaced or kept, and README:60,72 still advertises the 8-Pillar + worker flow. Raised by Stages 5, 7, 9. **Fix:** enumerate per-section retain/replace.
*   **M2 — Test disposition at 008:40 is narrower than the actual coupling:** misses `tests/test_artifice.py` imports `:24-27`, helper `:31,:49`, `ModelSelectionTests` `:364-440`, `VibeExecuteTests` `:805+`; whole file unimportable otherwise. Raised by Stage 9. **Fix:** delete every test importing/covering the three modules; keep installer/lint/dossier/provenance/governance/modality tests.
*   **M3 — README scope too narrow:** 008:65 limits changes to "tree + Core Scripts bullets", but README:71-72 (`--local` trigger), :79-82 (vibe-execute skill section), :129-158 (Discovery & Model Approval) also need reconciliation. Raised by Stages 5, 8, 9.
*   **M4 — Diet feasibility asserted, not allocated:** the verified 86-line / 407-word headroom must absorb the privacy step, the runbook, and the Phase C checklist after gutting SKILL.md §§2–5; no word budget is given, and "no new script" (008:53) leaves sanitiser/idempotency as untested prose — yet lint caps only `skills/*/SKILL.md` and `agents/*/agent.md` (`lint.py:330-333`), so one small `scripts/review_post.py` violates no ceiling. Raised by Stages 5 (catalyst), 7, 8.
*   **M5 — Guardrail fold-in incomplete:** egm-offloading.md:33-34's retry-once and "partial pass blocked from Stage 9 until retried or waived" are dropped (008:45); the 124/2/127 exit-code convention originates in the deleted `vibe_execute.py` and native omp/agy spawns will not emit it. Raised by Stage 7.
*   **M6 — Phase C mechanics underspecified:** JSONL run-log path/retention/privacy (raw `argv`/`target` can carry `/home/...`), trace-ID format, rate-limit handling (pre-check duplicates gh's classified exits); "comment-only" vs the human-gate non-goal is asserted, not argued; update-in-place erases the platform audit trail and the PATCH-own-comment case sits in a gap. Raised by Stages 5, 6, 7, 8, 9.
*   **M7 — Default mode undefined on the third mounted host:** 008:44(b) names only omp `task` and agy `invoke_subagent`, but `install_copilot.sh:58` also mounts the review skill (008:22). Raised by Stages 5, 8. **Fix:** name the copilot fallback (sequential coordinator-run lenses).
*   **M8 — Disposition list delivers nothing mechanical and omits issues:** #46 is tracked (008:6) but not dispositioned (008:24); #46's acceptance also requires #39/#24 reconciliation and `--local` privacy invariants preserved (ISSUES.md:299-301) — unaddressed; #19/#20/#32 get "recorded dispositions" no phase can deliver mechanically. Raised by Stages 7, 8, 9.
*   **M9 — One PR bundles three unrelated root problems (#41 deletion, #46 codification, new posting path); Phase C is pure addition with zero overlap with A, and the external ou#84 gate makes ungated B/C hostage to it.** Raised by Stage 8; challenges the author's D1 (008:71-75). **Fix:** split C at minimum, or record the coupling rationale beyond "shared context".
*   **M10 — Terminology undefined for a fresh reader:** `agy`, `omp`, `ou`, EGM/Elephant/Goldfish, Core Diet, coordinator, workdir, dispositions (008:6,12,16,22,29,38,44). Sibling 007 defines terms at 007:13. Raised by Stages 6, 7 (style).

### 🟢 Nits

*   **N1** — "costs double tokens" (008:16) uncalibrated; no measurement cited. (Stages 6, 7)
*   **N2** — 008:16 present-tense overclaims: "serve only the self-contained ou tier-0 audio path" (in-repo consumers: `vibe_execute.py:18-19`, review SKILL.md, code-author:96) and "`--local` has no engines behind it" — both true only post-Phase-A. (Stages 5, 8, 9)
*   **N3** — Verb mismatch: "shrinks" (008:12) vs "delete wholesale" (008:21, 008:37). (Stages 6, 9)
*   **N4** — Gate shown as closed (008:6) but described as pending (008:21, 008:35). (Stage 6)
*   **N5** — Exit codes 124/2/127 unexplained in-doc; `#29` reference unlinked (008:46); "scan AGENTS.md upward" undefined (no root AGENTS.md; markers live in skill docs). (Stage 6)
*   **N6** — Prose density/style: 008:44 (~120-word sentence with (a)–(d) chain) and 008:52 (eight-clause semicolon chain) need splitting; Overview restates Goals; title-case and trailing-double-space header conventions diverge from 007. (Stages 7, 9)
*   **N7** — Untracked root scratch `concepts_brief.md` / `design_draft.md` now contradict the final 008 (draft says "optional `--occam`", brief says "discover/classify stay"). (Stages 5, 8) — resolved at filing: content folded into docs/designs/008 and this report; scratch removed.
*   **N8** — Per-PR metrics (tokens/cost) recorded in the public review comment (008:22, 008:45). (Stage 8)
*   **N9** — Rejection attribution "after Goldfish review" (008:81) lacks date/link unlike the other four. (Stages 7 structural/style)

## What held up (verified clean across lenses and by the coordinator)

Diet arithmetic exact: `skills/review/SKILL.md` 94 lines / 593 words → headroom 86/407 vs `lint.py:32-33` (180/1000); `agents/code-reviewer/agent.md` 62/622 vs 900 (`lint.py:34`); `code-author/agent.md` 871/900. The hosted-dispatch contradiction is real and precisely cited (`skills/vibe-execute/SKILL.md:43` vs `skills/review/references/review-framework.md:111`; README:158 sides with the latter). Dispatch surface exists as claimed (`run`:573, `triage`:570, `_dispatch_vibe`:232, `find_vibe`:96/227 in the 632-line `vibe_execute.py`). ou#84 verified CLOSED 2026-11-20 with a self-contained-audit body. Phase A deletion targets all exist; `tests/test_model_inventory.py` and the `test_artifice.py` couplings exist as cited. lint's skill scan is directory-driven, so deleting `skills/vibe-execute/` needs no lint.py edit; `integrations/` adapters and `rules/global-agents.md` have zero references to the deleted machinery; `lint.py`, `build_review_dossier.py`, `validate_provenance.py` (`--repo`/`--range` at :89-104), `mistral_ocr.py` import none of the deleted modules. Lens names in 008:44 match upstream egm frontmatter. Phase B's recipe (artefact bundle, coordinator verification, Blockers/Majors/Nits + Keep/Simplify/Cut) and Phase C's sanitiser list match #46's proven recipe. Governance citations hold (`rules/global-agents.md:13,15`, #18). The Alternatives section structurally satisfies the standard's rule. spec-egm is gone with only legacy doc references. Mounting claim holds (three installers, no VS Code). `./scripts/lint.sh` exit 0 with 008 filed (139 tests, 2026-11-20).

## Traceability

| Finding | Stage 5 (zoom-out, catalyst) | Stage 6 | Stage 7 (design, structural, style) | Stage 8 | Stage 9 (readiness, codebase, style) |
| --- | --- | --- | --- | --- | --- |
| B1 consumers/installers/tests/README/004 omitted | 🔴 zoom-out, 🟡 catalyst | — | 🔴 design | 🔴 B3 | 🔴 readiness, 🟡 codebase |
| B2 code-author non-goal contradiction | 🔴 zoom-out | — | 🔴 design | 🔴 B2 | 🔴 readiness, 🟡 codebase |
| B3 phases = one atomic commit | — | — | — | 🔴 B2 | — |
| B4 privacy dead-end / default-allow scan / #41 acceptance | 🔴 catalyst#1, 🟡 catalyst#5 | 🟡 run-log privacy | 🟡 design | 🔴 B1, 🟡 M5 | — |
| B5 default-mode vs non-goal / #46 gate | 🔴 catalyst#3, 🟡 zoom-out | 🟡 fan-out | 🔴 design | 🟡 M2 | 🟡 readiness |
| B6 references/ + Phase C placement clash | 🟡 catalyst#5 | 🟡 references | 🟡 style, 🔴 design | 🟡 M3 | 🔴 readiness#1, 🟡 codebase, 🔴 style9 |
| B7 missing Risks/Open Questions/CUJs/NFR/plan | 🟡 zoom-out | 🔴, 🟡 | 🔴 structural, 🟡 style/design | 🟢 N2 | — |
| M1 SKILL.md §§1-5 / framework §3 disposition | 🟡 zoom-out, 🟡 catalyst | — | 🟡 design | — | 🟡 readiness#4 |
| M2 test scope 008:40 | — | — | — | — | 🟡 readiness#2, 🟡 codebase |
| M3 README scope | 🟡 zoom-out | — | — | 🟢 N1 | 🟡 readiness N3, 🟡 codebase |
| M4 diet allocation / no-new-script | 🔴 catalyst#2, 🟡 catalyst#8 | — | 🟡 design | 🟡 M3 | — |
| M5 guardrails retry/partial-pass/exit codes | — | 🟡 exit codes | 🟡 design | — | — |
| M6 run-log/trace/rate-limit/comment-gate | 🟡 catalyst#6/#7 | 🟡 run-log | 🟢 design | 🟢 N4 | 🟡 readiness#5 |
| M7 copilot spawn fallback | 🟡 catalyst#4 | — | — | 🟢 N5 | — |
| M8 dispositions #46/#39/#24/#19/#20/#32 | — | 🟡 #29 link | 🟡 design | 🟡 M4 | 🟢 codebase, 🟢 style9 |
| M9 one-PR bundling | — | — | — | 🟡 M1 | — |
| M10 undefined terms | — | 🟡 | 🟡 style | — | — |
| N1–N9 | 🟢 zoom-out | 🟢 | 🟢 style/structural | 🟢 | 🟢 style9/codebase |

--------------------------------------------------------------------------------

*Synthesised by the main session (coordinator) from 10 zero-context Goldfish reports; resolution and approval are human-gated per #18 and rules/global-agents.md:13.*
