# Consolidated Review Report — Design 007

*   **Target:** docs/designs/007_unified_harness_mounting.md (294 lines at approval; reviewed 2026-11-17 at 259 lines, FeatureRange 1–181, DetailedRange 182–259)
*   **Mode:** REVIEW, uninterrupted full flow (Stages 5–9) · **Date:** 2026-11-17
*   **Harness:** omp/Paseo; zero-context Goldfish subagents spawned directly by the main session (one level; nesting is disabled for children in omp)

## Reviewer status

| Stage | Lenses | Report | Status |
| --- | --- | --- | --- |
| 5 Initial Zoom Out | egm-zoom-out, egm-inventive-catalyst | zoom_out_report.md | completed |
| 6 Comprehension | egm-comprehension | comprehension_report.md | completed |
| 7 Critic | egm-design, egm-structural, egm-style | critic_report.md | completed |
| 8 Intermediate Zoom Out | egm-zoom-out (with Stage 5 report in context) | intermediate_zoom_out_report.md | completed |
| 9 Implementation Readiness | egm-implementation-readiness, egm-codebase-details, egm-style | implementation_readiness_report.md | completed |

All ten reviewer runs were true zero-context Goldfish reviews: each child started blank and received only its persona file, the target ranges, the standards, and the GoldfishContext baseline list.

Individual per-stage reports (zoom-out, comprehension, critic, intermediate zoom-out, implementation readiness) were working artefacts; their findings are deduplicated into this file's traceability matrix.

## Consolidated findings

### 🔴 Blockers

*   **B1 — omp `AGENTS.md` mount specified two contradictory ways** (007:70, :90, :189 symlink to `rules/global-agents.md` vs :96 and item 2 :191–194 creating an unmounted `integrations/omp/AGENTS.md` adapter; one reading also contradicts issue #30, which proposes the adapter as the target). Raised by Stages 5, 6, 8, 9. **Fix:** pin one mount target; if the adapter wins, update the table/diagram/item 1; if the symlink wins, delete item 2. Decide against issue #30's text.
*   **B2 — Alternatives rejections attributed to the maintainer with no linked deciding issue/PR/discussion, and zero Markdown links in the whole doc** (007:102–170; standard's Alternatives Rule; siblings 005/006 link issues and files). Raised by Stages 7, 8. **Fix:** link each rejection to its deciding discussion (e.g. #30 comment, #33, #34, the brainstorm gate) or use purely technical rationale; convert issue/file references to links.
*   **B3 — No labelled `## Risks & Mitigations` register** (007:174–178 NFR bullets; sibling 006:180 has the table; standard mandates it). Missing failure modes: lost-update on the `config.yml` temp-plus-rename, concurrent installer runs on one anchor, YAML-subset limits of line-based append, false-health from a relocated omp root. Raised by Stages 7, 8. **Fix:** add the section with owners and mitigations.

### 🟡 Majors

*   **M1 — omp client-root env vars undecidable**: invented `OMP_AGENT_DIR` vs native `OMP_PROFILE` / `PI_CODING_AGENT_DIR` (:34, :39, :77, :90, :189); no precedence, no fail-with-guidance on relocated environments (false `--check` health). Stages 5, 6, 7, 8.
*   **M2 — `config.yml` write under-specified**: supported YAML subset undefined (block-style top-level key only, fail otherwise); no fresh-machine create-template (unlike agy `skills.json`, install_antigravity.sh:122–134); insertion detail for `skills:` present without `customDirectories:` (:80, :178, :189, :223). Stages 5, 7, 8, 9.
*   **M3 — omp adapter tool allowlists never enumerated** (item 3 :196–199; no `OMP_TOOLS` equivalent to design 003's pinned sets; lint hardcodes `COPILOT_TOOLS`). Stages 8, 9.
*   **M4 — lint coverage for `integrations/omp/` unmechanised** (item 7 :215–218; lint.py frontmatter gate hardcodes `integrations/copilot/agents`; conditional adapter budget rule has no detector — make it unconditional or a fixed small ceiling; Bash-syntax/Markdown walks already recursive). Stages 5, 8, 9.
*   **M5 — Staging assigns no item to a phase and has no testable checkpoints** (:247); README (item 10) and the deletion (item 12) belong to no stage. Stages 8, 9.
*   **M6 — Item 11 "fold agy rules into the canonical policy" contradicts harness-neutrality and issue #33** (:112, :235–238 vs #33's `integrations/agy/AGENTS.md` disposition; the named rules already exist at `rules/global-agents.md:25–45`). Fix: policy stays harness-neutral; drop, don't fold. Stages 7, 8, 9.
*   **M7 — Item 12 targets non-existent `design_draft.md`** (:240–243; verified absent by glob and `git status`). Stages 5, 8, 9.
*   **M8 — `v0.1.0` merge contradiction** (:255 "first merge after this PR" vs :106/:247 Stage 4 inside this PR). Stages 8, 9.
*   **M9 — Versioning is a second root problem bundled into a mounting design**; split issue #20 into its own design/PR. Stages 5, 8.
*   **M10 — Zero-context terms undefined**: "Paseo", "omp"/oh-my-pi, "agy", "EGM", "Core Diet", "artemis", and dangling decision labels D3/D5/D7 (:80, :100, :104, :110, :189). Stages 6, 8, 9.
*   **M11 — CUJ 1 overclaims** (:47): registration is not proof of loading (README:120, design 005); add a Stage-2 omp discovery probe and make the *Then* conditional on #19 evidence. Stages 7, 8.
*   **M12 — #19 matrix wording**: design 005 already has agy/VS Code rows; only the omp-via-Paseo row is new (:111, :254). Stages 7, 8.
*   **M13 — Claim calibration**: `agents/code-author/agent.md` is 878/900 by lint's own counting, not 896/900 (:177); "existing four symlinks" miscounts (three under `COPILOT_HOME` plus the anchor, :91); stale current-value counts belong out of the architecture section (:177). Stages 7, 8.

### 🟢 Nits

*   Wording/voice: "enshrines" → plain verbs; "as today" → "as the existing installers"; "no new machinery" → "no new registrations"; split the seven-clause contract bullet (:189) and render Staging as a list (:247); "artifact" → "artefact" (:242); "fake HOME" → "disposable home"; "green" → "exit 0"; define "agy" and "Paseo" at first use; gloss "artemis"; "in front of VS Code" → "in a live VS Code session". (critic_report.md egm-style, implementation_readiness_report.md egm-style)
*   Header metadata should match the sibling template (plain `**Author:**`/`**Status:**`/`**Date:**`, tracking-PR field). (critic_report.md egm-structural)
*   Overview :11 overclaims ("turns the two existing installers") — no item modifies them; state that they already comply and need no changes. (Stages 5, 7, 8)

## What held up (verified clean across lenses)

Installer contract (:75–83) faithfully generalises both existing installers (containment, preflight states, zero-writes-on-conflict, atomic create-if-absent, read-only `--check`, no-rollback honesty). Rejecting a shared installer framework, the whole-directory omp skills symlink, per-harness policy forks, auto-merge-on-conflict, hook/CI version bumps, and tagged-release consumption are all correct and evidence-backed. D4 Option A is coherent and consistent with design 005. Lint ceilings and issue numbers verified against the repo. The Detailed Implementation Plan's 12-item file inventory is complete and correctly marked Create/Modify.

## Traceability

| Finding | Stage 5 | Stage 6 | Stage 7 | Stage 8 | Stage 9 |
| --- | --- | --- | --- | --- | --- |
| B1 omp AGENTS.md contradiction | zoom-out #1, catalyst 🔴 | comprehension 🔴#1 | — | 🔴#1 | readiness 🔴, codebase 🔴, style 🔴 |
| B2 unlinked rejections / no links | zoom-out #9 | comprehension 🟡#6 | structural 🔴, design F8 | 🔴#2 | — |
| B3 missing risk register | — | — | structural 🟡#2, design F5 | 🔴#3 | — |
| M1 env-var precedence | zoom-out #2 | comprehension 🟡#4 | design F2 | 🟡#4 | readiness 🟡#4 |
| M2 config.yml semantics | catalyst 🟡#5 | — | design F3 | 🟡#7 | readiness 🟡#3 |
| M3 omp tool allowlists | — | — | — | 🟡#11 | readiness 🟡#2, codebase 🟡#5 |
| M4 lint gate for omp | zoom-out #5 | — | — | 🟡#10 | readiness 🟡#7, codebase 🟡#5/#6 |
| M5 staging mapping | — | — | — | 🟡#9 | readiness 🟡#5, style 🟡#5 |
| M6 fold-vs-drop vs #33 | — | — | design F4 | 🟡#12 | codebase 🟡#2/#3 |
| M7 phantom design_draft.md | zoom-out #4 | comprehension 🟢#10 | — | 🟡#9 | readiness 🟢#8, codebase 🟡#4, style 🟡#2 |
| M8 v0.1.0 merge contradiction | — | — | — | 🟡#8 | style 🟡#3 |
| M9 versioning bundled | zoom-out #3 | — | — | 🟡#8 | — |
| M10 undefined terms / D-labels | zoom-out #9 | comprehension 🔴#2, 🟡#3, 🟢#9 | — | 🟡#5 | style 🟡#4 |
| M11 CUJ 1 overclaim | — | — | design F1 | 🟡#6 | — |
| M12 #19 matrix wording | — | — | design F12 | 🟢#18 | — |
| M13 claim calibration | — | comprehension 🟢#12 | style 🟡#1/#2 | 🟡#14, 🟢#15 | — |
