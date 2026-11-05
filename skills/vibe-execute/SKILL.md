---
name: vibe-execute
version: 1.3.0
description: >-
  Discovery-led Ollama model proposals, exact approved dispatch and compound
  triage. Hosted Mistral/Vibe discovery and execution are deferred.
argument-hint: "[discover | classify | triage | run] [--local] [--provider ollama --model EXACT_TAG --expect-identity FINGERPRINT] <prompt_or_file>"
---

# Discovery & Execution Gateway (`vibe-execute`)

Use **discover → filter → propose → confirm → execute**, not fixed tier-to-model menus. This phase delivers Ollama only; classification describes requirements, while the current assistant reasons about suitability.

## Reference Materials

* [Dispatch controller](../../scripts/vibe_execute.py) and [shared inventory](../../scripts/model_inventory.py)
* [Bounded local coding](../local-code/SKILL.md) and [Ollama lifecycle](../../scripts/check_ollama.py)
* [Review workers and privacy](../review/references/review-framework.md)

Resolve and export `ARTIFICE_ROOT` from its explicit value when set, otherwise `$HOME/.local/share/artifice` when present, otherwise `$HOME/Repos/artifice`, and resolve links from `ARTIFICE_ROOT/skills/vibe-execute/`. Verify readable `agents`, `skills` and `scripts` directories; stop on failure.

## 1. Establish Privacy & Requirements

Check applicable privacy directives before ingesting task material. `--local` governs discovery, triage and every wave. Protected prompts, source, diffs and generated outputs require local pipelines or a verified local session; metadata discovery cannot make a cloud conversation air-gapped.

This Ollama phase permits only configured loopback endpoints and verified on-device inference, even without `--local`. Remote endpoints are diagnosed without contact; cloud-backed or unknown execution locality blocks dispatch. Loopback transport alone does not prove on-device execution.

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" classify "<PROMPT>" --local
```

`classify PROMPT [--local]` emits complexity and requirements only, never a named model. Establish task, capability/context needs, mode, permissions and workdir; do not infer quality from a model name.

## 2. Discover, Propose & Confirm

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" discover --local --workdir "<DIR>"
```

`discover [--local] [--workdir DIR]` accepts no task text. Inspect the entire versioned inventory: exact tags, references, fingerprints, capabilities, context, locality, size and residency evidence, including explicit unknowns. It performs metadata operations only: no warming, inference, unloading or configuration mutation, and no quality ranking. Handle non-zero partial discovery explicitly and disclose missing evidence.

Hosted Mistral/Vibe is **deferred**: absent CLI means `unavailable`; present CLI means `unsupported_version` with `HOSTED_DISCOVERY_DEFERRED`. Presence establishes no selectable model and authorises no configuration/authentication/catalogue/inference access. Do not fabricate hosted menus.

Filter known incompatibilities, then propose at most three inventory choices with evidence and uncertainty. Unknown suitability needs explicit task-scoped acceptance; `--accept-unknown` cannot waive known incompatibility or privacy/locality. Obtain approval of exact identity/fingerprint, requirements, mode and workdir; reuse an explicit request or still-valid approval for this task.

## 3. Exact Dispatch

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" run "<PROMPT>" \
  --provider ollama --model "<EXACT_TAG>" --expect-identity "<FINGERPRINT>" \
  --task code --mode bounded_chat --require-capability chat \
  --local --workdir "<DIR>" --json
```

Carry the approved requirements using:

* `--task code|logic|fim|tdd|prose|docs|adr|architecture|utility`
* `--mode bounded_chat|cli_agent`
* Repeatable `--require-capability chat|tools|fim|vision`
* `--min-context POSITIVE_INT` and, only when approved, `--accept-unknown`
* `--local`, `--workdir DIR`, optional `--json`

The Ollama runner supports **bounded_chat only**; tool metadata or `--auto-approve` cannot create filesystem autonomy. Exact identity, capabilities and locality are revalidated before inference. A changed endpoint/tag/digest or execution failure stops dispatch: no fallback.

Missing normal run selection fails. `--local` alone or a legacy generic local request may resolve only a role override or one known-compatible candidate, never list-first/whitelist selection. Explicit CLI tags precede exact `ARTIFICE_CODE_MODEL` / `ARTIFICE_PROSE_MODEL` overrides.

`check_ollama.py select --task ROLE [--model EXACT_TAG] [--expect-identity HASH] [--accept-unknown]` uses the same inventory. Success returns `model`, `resident`, `fallback: null`, `identity_fingerprint` and `reference`; failure exits `2` with an explicit reason.

## 4. Compound Triage & Ordered Waves

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/vibe_execute.py" triage "<INPUT>" \
  --provider ollama --model "<EXACT_TAG>" --expect-identity "<FINGERPRINT>" \
  --task architecture --mode bounded_chat --local --workdir "<DIR>"
```

Select and approve the triage engine first, carrying the same relevant requirement flags as `run`. An explicit engine or unambiguous local request is required; there is no default large model.

Generated `recommended_engine` values must be discovered `provider/source/model` references. Split only the first two slashes, preserving tag namespaces/suffixes. Validate references and manifest structure/dependencies; reject missing, invented or ineligible engines. Approve concrete wave engines and fingerprints before dispatch.

Execute waves sequentially with native checks between them. `--local` constrains triage **and every wave**, regardless of recommendations.

## 5. Verification, Provenance & Teardown

Check exit status and stdout/stderr; run native verification on applied changes. Report actual provider, exact model, identity and elapsed time, not merely the recommended worker. Preserve existing declared wave lifecycle policy (`check_ollama.py unload --all` after leased local work); discovery never mutates residency.
