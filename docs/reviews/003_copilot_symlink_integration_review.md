# Goldfish Review: Copilot Symlink Integration

**Review Target:** [003_copilot_symlink_integration.md](../designs/003_copilot_symlink_integration.md)
**Revision:** 2026-11-03 lean refactoring
**Reviewer:** Independent code-reviewer Goldfish agents (initial and fresh configuration follow-up)
**Date:** 2026-11-03
**Verdict:** Approved

## 1. Executive Summary

The initial reviewer requested two configuration clarifications. The developer approved the clarified contract, and a fresh zero-context configuration follow-up approved it on 2026-11-03 with no blocking findings. This report condenses both returned reports. Earlier review/installation evidence remains in Git at `6e0579b`, not as approval of this revision.

## 2. Invariant & Edge-Case Probing

| ID | Area | Finding | Status |
| --- | --- | --- | --- |
| B1 | Copilot home | Resolved: unset/empty defaults; non-empty relative paths fail with exit 1 and no writes. | Closed |
| B2 | Model selection | Resolved: selected-task-only validation, explicit defaults/failure ordering and closed typed JSON shapes. | Closed |
| P3 | Resource precedence | Contract and static instruction tests pin selected-source precedence; text-only client operation still needs live acceptance. | Static coverage passes |
| P4 | Ownership | Deterministic installer regressions cover failure/interruption after creation, prior paths and rollback. | Runtime tests pass |
| P5 | Verification | Frozen fixture expectations, raw word/line boundaries and actual aggregate counts are verified. | Automated checks pass |
| P6 | Privacy/provenance | Real selected-tag lookup succeeds; inference/provenance propagation is statically checked, and strict-local refusal needs live acceptance. | Live checks outstanding |

## 3. Detailed Critiques & Blind Spots

Both reviewers received only the specification and Goldfish template; no repository `AGENTS.md` exists. The first synchronous reviewer could not receive follow-up messages, so a fresh reviewer performed the narrower configuration follow-up. Neither inspected implementation or Git history.

The follow-up found configuration, root precedence, counting, interruption and privacy requirements mutually consistent. It confirmed exact-match overrides versus retained substring defaults, failure precedence, task-group isolation and exact success/error key sets.

## 4. Required Revisions

None for the approved contract. Runtime equivalence, measured budgets, JSON/exit assertions and post-creation interruption cleanup still require executable evidence. Live discovery, effective permissions, refresh, command collisions and Antigravity/local-only behaviour remain separate acceptance checks.

## 5. Recommendation & Sign-Off

Initial refactoring verdict: Revisions Required. Fresh configuration follow-up: Approved. The clarified design has explicit human approval; implementation may proceed only after targeted EGM validation. This sign-off does not authorise personal activation or Git publication and does not establish technical privacy containment.

## 6. Implementation Audit & Verification

An independent `code-reviewer` inspected all 24 changed files, including the four untracked Python test modules, against the approved contract and existing behaviour. It found one blocking P2 functionality defect: [adapter validation](../../scripts/lint.py) accepted comment-only and collection-valued descriptions as non-empty strings.

Seven failing subcases reproduced comment-only, sequence, mapping and unmatched collection-marker acceptance. The repair rejects these unquoted forms while preserving valid quoted literal markers; [regressions](../../tests/test_lint.py) cover both. The parent reran all 77 tests and native governance after the fix; all pass. The reviewer found no other meaningful introduced defects. This is a regression-verified closure, not a claim of a second independent post-fix approval.

The 36 installer tests preserve the 21 frozen behaviours and add 15 cases. Native validation covers Markdown, adapter metadata, relative links, raw word/line caps, EGM contracts and Bash syntax. Actual read-only code/prose selections both returned installed `qwen3.8:27b-mlx`, `resident: false`, `fallback: null`; no inference or model loading occurred.

VS Code CLI version is `1.138.0` (`arm64`); Antigravity CLI is unavailable. Live UI discovery, actual workflow loading, effective permissions, source refresh, `review` collisions, Antigravity without an anchor/definition path, strict-local refusal before protected reads and inference remain outstanding. Static instructions and mocked tests do not establish technical containment.

**Post-harvest verification (2026-11-04):** Canonical domain instructions were restored across the three roles and four skills (4,128 words vs `main`'s 4,129 words) with Copilot-specific caveats encapsulated in `integrations/copilot/agents/`, Antigravity `--local` on-device pipeline execution preserved, daemon `SIGHUP` disposition normalised in [`test_install_copilot.py`](../../tests/test_install_copilot.py), brittle frontmatter hash locks replaced in [`test_entry_points.py`](../../tests/test_entry_points.py), and all 74 Python tests wired directly into [`scripts/lint.sh`](../../scripts/lint.sh). Read-only `check_ollama.py select` verified `qwen2.5:14b` (`code`) and `mistral-nemo:latest` (`prose`) on the target Mac.
