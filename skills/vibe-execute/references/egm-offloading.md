# EGM Goldfish Offloading via `vibe_execute.py`

Operational contract for pairing upstream `egm` workflows with `/vibe-execute`: stateful Elephant turns stay on the primary harness (Gemini), while stateless Goldfish lenses fan out in parallel to hosted Mistral via `scripts/vibe_execute.py run`.

## Baseline Pin & Drift Check

Pinned upstream baseline: `google/elephant-goldfish-model` `version 0.1.1` (commit `270b103`). Before dispatching step-numbered workflows, check `~/.gemini/config/plugins/egm/plugin.json` (`version: 0.1.1`) and `git -C ~/.gemini/config/plugins/egm rev-parse HEAD` (`270b103...`) against the pinned baseline and flag any upstream drift (or run `egm-drift-report` if stale).

## Routing Split Table

| Workflow / Step | Memory Role | Execution Engine | Notes |
|---|---|---|---|
| `egm-brainstorm` Steps 1, 3, 4 (intake, synthesis, handoff) | Elephant (stateful) | Gemini (Primary Harness) | Uses multi-turn memory and `ask_question` UI gates; misrouting loses context. |
| `egm-brainstorm` Step 2 (`7` review/ideation lenses) | Goldfish (stateless) | Mistral via `vibe_execute.py run` | Concurrent one-shot subprocesses; return structured Markdown findings. |
| `egm-draft` Steps 1–6 (section drafting & file edits) | Elephant (stateful) | Gemini (Primary Harness) | Interactive section sign-off and workspace file editing. |
| `egm-review` Stages 1–4 (intake, split, preset, staging) | Elephant (stateful) | Gemini (Primary Harness) | Owns target splitting, `ask_question` gates, and final cross-stage synthesis. |
| `egm-review` Stages 5–9 (`10` dispatches) & `egm-review-loop` Step 2.2 | Goldfish (stateless) | Mistral via `vibe_execute.py run` | Concurrent flat-swarm workers with inline persona, standard, target, and `GoldfishContext`. |
| `egm-resolve` & `egm-review-loop` Steps 2.1, 2.3, 2.4 (resolution & convergence) | Elephant (stateful) | Gemini (Primary Harness) | Interactive negotiation, document edits, and target resolution and convergence checks. |
| `egm-drift-report` & `egm-bootstrap` leaf file workers | Goldfish (stateless) | Mistral via `vibe_execute.py run` | Read-only file/sub-tree inspection; leaf reports aggregated by Elephant. |

## Direct-Dispatch Rules

1. Always pass `--mode bounded_chat --require-capability chat --workdir "<REPO_ROOT>" --json` to `scripts/vibe_execute.py run` so `model_inventory.local_policy` evaluates repository privacy directives automatically.
2. Bypass `egm-synthesizer` and never wrap `vibe_execute.py` inside `invoke_subagent`.
3. Inject upstream persona (`agents/*.md`), target standard (`resources/document_standards/{zoom-out-standard,feature-spec-standard,implementation-readiness-standard}.md`), `1`-based numbered target file lines, and `GoldfishContext` baseline files inline into the worker prompt.
4. Label any excerpted baseline file explicitly (`[EXCERPT: lines X-Y of Z]`).
5. Assert the assembled prompt UTF-8 byte length is `< 120,000` bytes before `subprocess.run` to stay within Linux's `128 KiB` `MAX_ARG_STRLEN` per-argument limit.

## Operational Guardrails

1. Discover and confirm the exact `--model` + `--expect-identity` via `ask_question` before the first dispatch.
2. Enforce an explicit `--timeout` budget (e.g. `--timeout 180`; script default is `120.0`s at `scripts/vibe_execute.py:543`, raising exit code `124` with empty `stdout` per lines 290–297).
3. Retry a timed-out or failed lens at most once before recording it as `not run` (never zero findings).
4. Any pass containing one or more `not run` lenses must be flagged as partial in `Reviewer Status` and blocked from Stage 9 sign-off until retried or explicitly waived by the user in the review report and PR description; bound `egm-review-loop` to 5 rounds.
5. Immediately halt hosted Mistral dispatch whenever `--local` or repository privacy directives (`Privacy: on-device`, `Review: local-only`) apply.
