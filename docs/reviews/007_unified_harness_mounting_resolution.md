# Goldfish Annotated Review Report

**Target:** `docs/designs/007_unified_harness_mounting.md` (full file; 259 lines at review time, 294 at approval)
*   **Status:** resolved 2026-11-17 · **Date:** 2026-11-17
*   **Source reports:** consolidated into [007_unified_harness_mounting_review.md](007_unified_harness_mounting_review.md); the five per-stage reports were working artefacts and are not retained.
## Prioritised Findings & AI Suggestions

### B1 — omp `AGENTS.md` mount specified two contradictory ways — Severity: Blocker

*   **Affected Scope:** lines 70, 90, 96, 189, 191–194 (mounting model, registration table, installer contract item 7, plan items 1–2)
*   **Discrepancy:** `~/.omp/agent/AGENTS.md` is symlinked to `anchor/rules/global-agents.md` in three places, while plan item 2 creates `integrations/omp/AGENTS.md`, which no registration mounts. Issue #30 proposes the adapter as the target, so one reading contradicts the tracking issue.
*   **Rationale:** omp's own docs (`omp://context-files.md`) confirm the native user context file `~/.omp/agent/AGENTS.md` is read and symlinks work; the current 45-line `rules/global-agents.md` contains no Gemini-only section (that content lives only in the personal `~/.gemini/config/AGENTS.md`, handled by #33), so the adapter's premise is false.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the author decided "unify as symlink when possible" (brainstorm gate, 2026-11-17), and the adapter's stated reason for existing does not hold against the canonical file. Follow-up: comment on issue #30 that its adapter proposal is superseded by the symlink decision.
*   ***Proposed Edit:***
    *   Line 96 / "omp adapters" section: delete the `integrations/omp/AGENTS.md` adapter requirement; state the policy file is the symlink to `rules/global-agents.md`.
    *   Plan item 2 (191–194): delete; renumber remaining items.
    *   Plan item 1 (189): keep `AGENTS.md -> anchor/rules/global-agents.md`; add "anchor created create-if-absent, as in the other installers".
    *   Mounting diagram line 70 and table line 90: unchanged (already the symlink).

### B2 — Unlinked maintainer attributions and zero Markdown links — Severity: Blocker

*   **Affected Scope:** lines 102–170 (Alternatives), all `#NN` references (11, 15, 20, 22, 28, 32, 33, 38, 100, 106, 110–112, 121, 133, 152, 160, 164, 177)
*   **Discrepancy:** every "Rejected by author" cites no deciding issue/PR/discussion; no `[…](…)` links exist anywhere; siblings 005/006 link issues to GitHub URLs and files relatively.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** mechanical; the standard's Alternatives Rule hard-requires it.
*   ***Proposed Edit:*** link issue numbers as `[#NN](https://github.com/efsalvarenga/artifice/issues/NN)`; link repo files relatively (e.g. `[install_antigravity.sh](../scripts/install_antigravity.sh)` from docs/designs/); each "Rejected by author" gains the deciding reference (#30 comment, #33, #34, or the 2026-11-17 brainstorm gate recorded in concepts_brief.md).

### B3 — No labelled Risks & Mitigations register — Severity: Blocker

*   **Affected Scope:** lines 174–181 (NFR)
*   **Discrepancy:** the standard mandates a `## Risks & Mitigations` section; sibling 006:180–189 has one. Failure modes are scattered in NFR bullets.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** add `## Risks & Mitigations` before NFR with a table: dangling anchor (mitigate: `--check` classifies dangling as conflict; lint reads physical checkout); worktree anchor exclusivity (one anchor, conflicts on second); partial installs (no rollback claims, rerun `--check`); lost-update on `config.yml` temp-plus-rename (copy original mode onto temp; document the window); concurrent installer runs (preflight aborts on conflict, but a run mid-write of another is the residual window — accept and document); YAML-subset limits of line-based append (fail-with-guidance outside supported subset); relocated omp root false health (fail-with-guidance when `OMP_PROFILE`/`PI_CODING_AGENT_DIR` set); word/line ceilings incl. #32.

### M1 — omp client-root env vars undecidable — Severity: Major

*   **Affected Scope:** lines 34, 39, 77, 90, 189
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** replace the invented `OMP_AGENT_DIR` with omp-native resolution: client root = active agent dir as omp computes it (`PI_CODING_AGENT_DIR` if set; else `~/.omp/profiles/<name>/agent` when `OMP_PROFILE` is set; else `~/.omp/agent`). State precedence explicitly, and when a non-default relocated root is active the installer either validates it like `GEMINI_HOME`/`COPILOT_HOME` or fails with guidance — default: validate the resolved active dir, refuse only if it cannot be resolved.

### M2 — `config.yml` write semantics under-specified — Severity: Major

*   **Affected Scope:** lines 80, 178, 189, 223
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** specify: supported subset = top-level block-style `skills:` / `customDirectories:` keys only, fail-with-guidance otherwise (flow-style, nested, commented, quoted → guidance). Fresh machine (`config.yml` absent): create it with a minimal template containing the entry (mirrors `skills.json` creation at install_antigravity.sh:122–134). Insertion: if `skills:` exists without `customDirectories:`, insert the key under it; if neither exists, append both at end; entry string `    - /home/.../​.local/share/artifice/skills` (anchor-resolved absolute path). Atomic temp-plus-rename with the original file's mode copied onto the temp; re-read before rename. Idempotent when the anchor entry is already present. Reword :178 to "never transmit, and never parse-and-rewrite".

### M3 — omp adapter tool allowlists never enumerated — Severity: Major

*   **Affected Scope:** lines 196–199 (item 3), 215–218 (item 7)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** add a per-role omp tool mapping table to item 3 (canonical Antigravity name → omp tool): view_file/read_file→`read`, grep_search→`grep`, find_by_name/list_dir→`glob`, edit_file→`edit`, write_file→`write`, run_command→`bash`, send_message→`write`, plus `task`/`wait`/`todo` where the persona spawns; define `OMP_TOOLS` in lint.py and validate adapter `tools:` against it (generalising `COPILOT_TOOLS`).

### M4 — lint coverage for `integrations/omp/` unmechanised — Severity: Major

*   **Affected Scope:** lines 215–218 (item 7)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** generalise the frontmatter gate from `integrations/copilot/agents` to `integrations/*/agents`; adapters get their own fixed ceiling (60 lines, counted separately from the 900-word agent budget) instead of the unimplementable duplication rule; note Bash-syntax and Markdown walks already cover the new files recursively (test_artifice.py:583).

### M5 — Staging assigns no item to a phase — Severity: Major

*   **Affected Scope:** line 247
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** render Staging as a list mapping items to stages with a testable checkpoint each: Stage 1 design merged; Stage 2 items 1, 3, 7, 8, 9 (installer, omp agent adapters, lint, tests) + `--check` green on artemis + omp discovery probe (fresh omp session loads policy/skills/agents) as the checkpoint; Stage 3 item 11 (#33 migration); Stage 4 items 4, 5 (CHANGELOG, PR template) and item 10 README; item 12 deletion folded into Stage 1 (file already absent); Stage 5 procedural (#19 rows, #23 comment).

### M6 — Item 11 fold-vs-drop contradicts harness-neutrality and #33 — Severity: Major

*   **Affected Scope:** lines 112, 235–238
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the named rules (British English, Markdown cleanliness, provenance trailers) already exist verbatim at `rules/global-agents.md:25–45`; the Gemini-only content is personal to agy and is dropped at #33, not folded. The user approved "no `integrations/agy/` adapter" in the plan. Follow-up: comment on #33 to align its step 1 wording.
*   ***Proposed Edit:*** item 11 becomes: "at #33, review the personal 3,601-byte `~/.gemini/config/AGENTS.md`; the canonical policy stays harness-neutral — keep only content that is already present or harness-neutral; drop stale `spec-egm`/`validate_egm.py` references and Gemini-only delegation sections; replace the file with the symlink; verify `install_antigravity.sh --check` passes."

### M7 — Item 12 targets non-existent `design_draft.md` — Severity: Major

*   **Affected Scope:** lines 240–243
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** delete item 12 (the working draft was already removed at finalisation; `git status` confirms) and note `concepts_brief.md` is retained as a historical brainstorm record, marked as non-normative in its header.

### M8 — `v0.1.0` merge contradiction — Severity: Major

*   **Affected Scope:** lines 106, 247, 255
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** state plainly: this design's own merge is tagged `v0.1.0` (Stage 4 runs inside this PR); the verification-plan line becomes "this PR carries `## [v0.1.0] - <date>` and the annotated tag `v0.1.0`".

### M9 — Versioning bundled with the mounting design — Severity: Major (reviewer suggestion: split into its own design/PR)

*   **Affected Scope:** lines 23, 104–106, 201–209, 247
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** the counter-evidence is the author's explicit decision in this conversation (2026-11-17: "start versioning now, bump on every merge"), which lives outside any file the reviewer could read. The coupling risk is real; record it in the risk register (B3) either way. User decides: keep versioning in this PR (with a risk-register entry) or split #20 into its own PR.

### M10 — Undefined terms and dangling decision labels — Severity: Major

*   **Affected Scope:** "Paseo" (:90, :111, :254), "omp"/oh-my-pi (:21), "agy" (:19, :89), "EGM" (:259), "Core Diet" (:251), "artemis" (:38, :100, :112, :253), D3/D5 (:80, :110, :189)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** add a one-line terminology note after the Overview (agy = the Antigravity CLI binary; omp = oh-my-pi, driven here through the Paseo app/daemon; EGM = Elephant-Goldfish Model; Core Diet = the lint word/line ceilings; artemis = this developer workstation) and a short "Decisions" index defining D1–D8 inline (D3 = fail-with-guidance on a populated `skills.customDirectories`; D4 = VS Code Option A; D7 = manual per-merge tagging).

### M11 — CUJ 1 overclaims; no omp discovery probe — Severity: Major

*   **Affected Scope:** line 47
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** CUJ 1 *Then* becomes "registrations are correct and `--check` exits 0 on all three; native inclusion evidence (policy/skills/agents visible in a fresh session) is collected per the #19 matrix"; add to Stage 2 checkpoint: fresh omp-via-Paseo session shows policy, skills, agents loaded.

### M12 — #19 matrix wording — Severity: Major

*   **Affected Scope:** lines 111, 254
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** "add the omp-via-Paseo row (agy, Copilot CLI, and VS Code default-home rows already exist in design 005:289–294)".

### M13 — Claim calibration — Severity: Major

*   **Affected Scope:** lines 91, 177
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** :91 "existing four symlinks" → "existing client-root symlinks (three) plus the anchor"; :177 state ceilings only (140/1,400 policy, 180/1,000 skill, 900 agent) and cite #32 for the agent ceiling without the stale 896/900 figure (currently 878/900 by lint's own counting); move current-value mentions out of the architecture section.

### Nits — Severity: Nit (grouped)

*   **Affected Scope:** :242 "artifact"→"artefact"; :189 split the seven-clause bullet into sub-bullets; :247 render as list (covered by M5); :61 "fully resolved absolute paths" → "anchor-based absolute paths (physical equivalence accepted)"; :11 overview overclaim → "adds a written contract plus a third installer; the two existing installers already comply and need no changes"; :176 split the packed bullet and use requirement voice; "enshrines"→plain verb (:61, :152); "as today"→"as the existing installers" (:77); :100 "no new machinery"→"no new registrations"; header metadata to sibling template (plain `**Author:**` lines, tracking-PR field).
*   ***AI Suggestion:*** PROPOSE FIX (mechanical wording fixes bundled with the edits above)
*   ***Justification:*** all are zero-risk textual repairs; DECLINE-worthy prose-style items (e.g. varying "Rejected by author" refrain) are left as-is per B2's linking fix.

## Summary counts

*   Blockers: 3 (B1–B3) — all PROPOSE FIX
*   Majors: 13 (M1–M13) — 11 PROPOSE FIX, 1 ESCALATE (M9), 0 CONTEST
*   Nits: grouped — PROPOSE FIX (mechanical), rest DECLINE

## Resolution outcome (2026-11-17, "auto accept")

*   **Accepted and applied (PROPOSE FIX):** B1, B2, B3, M1–M8, M10–M13, and the mechanical nits — edits applied to `docs/designs/007_unified_harness_mounting.md` in one batch.
*   **Escalated:** M9 (versioning bundled vs split). Author decision 2026-11-17: open a separate PR for it later — captured as [#37](https://github.com/efsalvarenga/artifice/issues/37); the design keeps D7 documented and points at #37.
*   **Contested:** none.
*   **Declined:** prose-style nits (varying the "Rejected by author" refrain) — B2's linking fix covers the substance.
*   **Unaddressed:** none.
*   **Follow-ups posted:** comment on [#30](https://github.com/efsalvarenga/artifice/issues/30) (omp `AGENTS.md` adapter superseded by the symlink decision) and on [#33](https://github.com/efsalvarenga/artifice/issues/33) (drop-don't-fold wording alignment).
*   **Post-resolution verification:** `./scripts/lint.sh` exit 0 (static linters + 127 unit tests).

## Re-audit outcome (Stage 9, single permitted re-audit, 2026-11-18)

Reviewers: egm-implementation-readiness, egm-codebase-details, egm-style on the revised DetailedRange (lines 222-293), with this report and consolidated_review_report.md in context. Verdict: all accepted 2026-11-17 fixes verified landed against the live repo; no new 🔴; three residual 🟡 (plus nits), all fixed on 2026-11-18:

*   Stage 2 checkpoint was unsatisfiable (demanded all three `--check` exit 0 while agy conflicts until Stage 3) — rescoped Stage 2 to `install_omp.sh --check` + discovery probe; all-three moved to the Stage 3 checkpoint. (PROPOSE FIX, applied)
*   omp tool mapping missed `search_web` and per-role spawn tools — added `search_web` → `web_search` row and a per-role extras line (`code-author`/`code-reviewer`: `task`, `wait`, `todo`). (PROPOSE FIX, applied)
*   `concepts_brief.md` non-normative claim had no in-file evidence — header Status line added marking it a historical, non-normative record governed by design 007. (PROPOSE FIX, applied)
*   `tests/test_governance.py` `clients` tuple needs an explicit third `omp` branch (root, env vars, policy path) — item 8 now spells it out. (PROPOSE FIX, applied)
*   Nits applied: lint verification parenthetical now includes adapter frontmatter; evidence-row field wording aligned to "harness/profile"; adapter suffix convention (`*.agent.md` vs `*.md`) and per-role `OMP_TOOLS` stated in item 6; `config.yml` check ordering (idempotence first, unrelated top-level keys untouched, template shape) stated in contract item 4; Stage 1 wording un-doubled.
*   Declined: splitting item 1's dense bullet (precise, not wrong).

Post-fix verification: `./scripts/lint.sh` exit 0 (static linters + 127 unit tests). Remaining open decisions in the plan: zero.
