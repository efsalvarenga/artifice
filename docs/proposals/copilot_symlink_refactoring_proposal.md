# Proposal: Lean Refactoring of the Copilot Symlink Integration

**Document:** `docs/proposals/copilot_symlink_refactoring_proposal.md`
**Target branch:** `feat/copilot-symlink-integration` ([PR #9](https://github.com/efsalvarenga/artifice/pull/9))
**Status:** Implemented; automated verification passes; live client acceptance outstanding
**Date:** 2026-11-03

## 1. Decision

Keep the useful architecture: three thin Copilot adapters, four shared skills and three user-level directory symlinks, with one canonical workflow per component. Remove duplicated prompt instructions and unnecessary complexity without weakening installation or privacy guarantees.

The developer approved the clarified [contract 003](../designs/003_copilot_symlink_integration.md), its independent [Goldfish configuration follow-up](../reviews/003_copilot_symlink_integration_review.md) approved it, and targeted EGM validation passed before implementation.

This approved scope supersedes the original proposal's deletion of regression tests, mandatory 45-line POSIX rewrite, fixed replacement model tags, weakening of `--local` and automatic Git publication. Size reductions are measured outcomes, not permission to remove contracts.

## 2. Verified Historical Baselines

These are immutable Git snapshots, not claims about the refactored working tree:

| Snapshot | Files | Lines | Words | Bytes |
| --- | ---: | ---: | ---: | ---: |
| `main` at `a219f8e` | 23 | 2,487 | 14,864 | 131,074 |
| Initial integration at `f320097` | 30 | 3,405 | 23,263 | 196,466 |
| Integration plus original proposal at `6e0579b` | 31 | 3,559 | 24,885 | 208,925 |

The integration added 8,399 repository words (+56.5%). Its seven canonical entry points grew by 1,260 words (+30.5%):

| Entry point | `main` words | Integration words |
| --- | ---: | ---: |
| `agents/code-author/agent.md` | 759 | 982 |
| `agents/code-reviewer/agent.md` | 650 | 809 |
| `agents/developer-coach/agent.md` | 595 | 737 |
| `skills/coach-frameworks/SKILL.md` | 484 | 634 |
| `skills/local-code/SKILL.md` | 271 | 429 |
| `skills/review/SKILL.md` | 822 | 1,026 |
| `skills/spec-egm/SKILL.md` | 548 | 772 |
| **Total** | **4,129** | **5,389** |

Other verified starting costs: installer/harness 216/258 lines; design/review 3,570/696 words; README 1,447 words. Line ceilings alone do not catch long unwrapped prompt paragraphs. Existing lint does not discover Copilot adapters or enforce canonical word budgets.

## 3. Confirmed Non-Regression Decisions

* **Resource discovery:** Explicit `ARTIFICE_ROOT` -> present `$HOME/.local/share/artifice` -> `$HOME/Repos/artifice`. Validate only the selected source, physically and independently of the consuming repository. Invalid overrides or selected broken anchors fail; a valid override ignores an unused broken anchor. No definition path is required.
* **Governance:** Keep client-specific tools/loading in adapters and follow active client/repository authority, including valid preauthorisation. Shared prompts do not grant Git permission. Gemini global rules are optional and Antigravity-specific; no global configuration is migrated.
* **Models:** Reconnaissance found only `qwen3.8:27b-mlx`, which existing code/prose defaults do not select. Neither restoring old tags nor merely calling `select` repairs that host. Add task-scoped `ARTIFICE_CODE_MODEL`/`ARTIFICE_PROSE_MODEL`, validated against installed tags; preserve unset-variable defaults and reject invalid overrides without substitution.
* **Privacy:** `--local` keeps its strict on-device meaning. Cloud-orchestrated Ollama execution remains available as hybrid work, never described as air-gapped. Local-only directives forbid protected-content ingestion into a cloud session and implicit cloud fallback.
* **Installation:** Retain Bash, CLI behaviour, source/parent validation, conflict refusal, read-only checks, idempotence, physical equivalence, cycle prevention and owned-path rollback after failure/interruption. Concurrency and uncatchable termination remain unsupported.
* **Coverage:** Preserve all behaviours represented by the existing 21 fixture cases. Replace dynamic source extraction/`eval` with a black-box regression; simplify fixtures, not safety assertions. A 45-line target cannot override these requirements.

## 4. Implementation Order

1. **Contract gate:** Condense design 003, retain all eight sections, distinguish historical approval from the revised contract, obtain human/independent approval and run targeted EGM validation. Completed before author handoff.
2. **Tests first:** Establish a safe installer baseline and focused failing standard-library tests for model overrides, adapter validation and word/line boundaries. Use controlled mutator shims, not timing assumptions.
3. **Shared workflows:** Restore checked relative documentation links, apply compact root discovery and client governance, then propagate selected model tags consistently through warming, inference and provenance.
4. **Installer:** Remove only complexity whose redundancy is demonstrated by equivalent behavioural tests. Use disposable homes/checkouts; never personal registrations.
5. **Native governance/docs:** Discover adapters, check their role/tool/loading contracts, enforce prompt budgets and integrate Bash syntax validation. Shorten setup guidance while retaining recovery, refresh and privacy limitations.
6. **Verification:** Run focused and complete baselines, measure actual footprints, obtain independent implementation review and record live-client gaps honestly.

## 5. Acceptance & Publication Boundaries

| Area | Required result |
| --- | --- |
| Canonical prompts | Skills <=180 lines/1,000 words; agents <=900 words; aggregate aim <=4,158 words against the 4,129-word baseline. |
| Installer | Existing safety/CLI/rollback behaviours retained; report actual installer/harness size rather than promising a 90% reduction. |
| Models | Exact configured installed tags, task-group isolation, explicit errors and preserved JSON/exit contracts; no downloads or implicit cloud execution. |
| Static governance | All adapters checked; word thresholds include frontmatter/code and cannot be bypassed by long lines; restored links resolve. |
| Runtime verification | Disposable-home tests and Python unit tests pass; no `eval`, real-home mutation or model loading in tests. |
| Client acceptance | Separately verify discovery, canonical reads, effective tools, command collision, refresh, strict-local refusal and Antigravity without an anchor/definition path. |

Native commands are documented in the [contract](../designs/003_copilot_symlink_integration.md) and [README](../../README.md). Filesystem and mocked tests do not establish live client behaviour or technical privacy containment. Unavailable acceptance checks remain outstanding.

The implementation request does not authorise staging, commits, pushes, PR edits, personal activation or merge. Each requires separate applicable permission; historical authorisation is not reused.

## 6. Measured Implementation Results

| Measure | Before | Implemented |
| --- | ---: | ---: |
| Canonical entry-point words | 5,389 | 3,905 (-27.5%; also below `main`'s 4,129) |
| Installer lines | 216 | 196 |
| Installer plus complete runtime harness lines | 474 | 655 |
| Installer regression behaviours | 21 | 36 |
| README words | 1,447 | 1,292 |

All 77 Python tests, six native governance gates and whitespace checks pass. Both task groups select the installed model through validated ephemeral overrides without loading it. Independent implementation review found an adapter-description validation gap; failing regressions reproduced it and the repair passes all checks.

The runtime harness moved to standard-library fixtures and expanded coverage. Its growth is explicit: this is not a 45-line installer or an 80% overall code reduction. Prompt reduction and installer simplification were achieved without deleting safety coverage. Live client and inference checks remain outstanding in the [review record](../reviews/003_copilot_symlink_integration_review.md).
