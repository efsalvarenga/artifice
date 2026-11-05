# Design Proposal: Discovery-Driven Model Proposals

**Document ID:** `docs/designs/004_discovery_driven_model_proposals.md`
**Status:** Approved
**Date:** 2026-11-05
**Author:** Copilot SDK assistant (`gpt-6.1-sol`) & Developer
**Scope:** Full delivery authorised on 2026-11-05: Ollama discovery and native Mistral Vibe discovery/dispatch delivered under a unified metadata contract.

## 1. Overview & Objectives

Replace model-name-first routing with **discover -> filter -> propose -> confirm -> execute**. Artifice should describe the engines actually available in the developer's environment; the current assistant should recommend an appropriate shortlist from that inventory.

### Accepted Delivery Scope

This implementation delivers the shared inventory, Ollama metadata, native Mistral Vibe discovery and dispatch, explicit selection/dispatch, consumer workflows and compound execution.

The Vibe executable resolver locates the native Vibe CLI (`vibe`). When present and `--local` is not asserted, configured models are enumerated from `~/.vibe/config.toml` (or canonical Mistral aliases: `large`, `codestral`, `fast`, `small`, `ministral`), exposing them with explicit capabilities and SHA-256 fingerprints. Dispatch is routed through `vibe --trust --model <ref> -p <prompt>`, strictly blocked when `--local` or repository privacy policies are active.

### Empirical Starting Point

Read-only reconnaissance on 2026-11-05 established:

* The configured Ollama-compatible service is reachable and advertises `qwen3.8:27b-mlx`, with no resident models. No model was loaded or queried for inference.
* The existing Vibe executable resolver finds no CLI on this machine.
* [Local selection](../../scripts/check_ollama.py) recognises a few preferred model names; it does not select an unfamiliar installed coding or prose model without an override.
* [Gateway classification and compound triage](../../scripts/vibe_execute.py) embed hosted model names independently of provider availability.
* The selected model-selection and gateway baseline passes: 26 tests in [the existing suite](../../tests/test_artifice.py).
* The available controller runtime is Python 3.9.6. A design that assumes standard-library `tomllib` would introduce an unacknowledged runtime incompatibility.

### Goals

* Discover every advertised model from the configured Ollama-compatible service, plus Vibe's effective configured models and authenticated hosted catalogue when permitted.
* Give `vibe-execute`, `local-code` and `review` one shared inventory contract.
* Keep recommendation reasoning in the current assistant, not a model-name whitelist or numerical quality-ranking engine.
* Distinguish installation, configuration, account visibility, capabilities and actual dispatch support.
* Preserve explicit model overrides, local-only privacy boundaries and truthful execution provenance.
* Bind execution to the approved model identity; never silently substitute another model or provider.

### Non-Goals

* Automatic commits, global provider installation or external-model inference during implementation verification.
* Scanning arbitrary model files, other machines or every local runtime. Ollama-compatible endpoints and Mistral Vibe are the initial adapters; direct MLX and LM Studio adapters are separate work.
* Benchmarking, downloading, warming, unloading or invoking models during discovery.
* New autonomous local tool loops, automatic provider configuration, credential refresh/login, persistent inventory caches or telemetry.
* New third-party dependencies in Artifice, a Python runtime upgrade, or a framework/plugin architecture for two adapters.

### Alternatives & Trade-Offs

| Approach | Benefit | Cost / limitation | Decision |
| --- | --- | --- | --- |
| Extend the current preferred-name lists | Small initial change | Every new installation can require another edit; availability and suitability remain conflated | Reject |
| Discover and apply automatic quality scores | Reproducible ordering | Capability metadata does not establish coding quality; scoring becomes another brittle policy registry | Reject |
| Discover structured evidence; assistant proposes | Adapts to the environment and task, with explainable uncertainty | Requires provider adapters and human confirmation | Adopt |

## 2. Domain Framing & User/System Experience

The developer confirmed assistant-led recommendations, authenticated metadata-only hosted discovery when permitted, shared integration across all three skills, session-only snapshots and no silent substitution or cloud fallback.

### Normal Interaction

1. Establish task requirements, privacy constraints and execution mode before reading protected task material.
2. Discover provider and model metadata. Discovery takes no task prompt, source code or diff. Only narrowly scoped provider configuration may be read from the working directory.
3. Present a short inventory summary, including unavailable providers and incomplete metadata.
4. Propose at most three suitable choices, with one recommendation when evidence supports it. Explain capability fit, context, resource caveats and local/hosted trade-offs. Do not invent benchmark scores, prices or latency measurements.
5. Obtain approval of the concrete model, execution mode and working directory. Reuse an explicit model request or still-valid approval for the same task rather than repeatedly asking.
6. Revalidate that identity and dispatch it exactly. Report the actual provider, model and elapsed execution time.

The entire discovered inventory remains available for inspection; the three-choice presentation limit must not truncate discovery. An embedding-only model can appear in the inventory while being excluded from a coding shortlist.

For this machine, discovery must report `qwen3.8:27b-mlx` rather than claim that no local models exist. Its tag alone does not prove coding quality, supported capabilities, memory fit or readiness. No hosted model should be offered as immediately executable when Vibe is absent.

### Local-Only Interaction

`--local` and applicable repository privacy directives disable hosted discovery and dispatch before either begins. A configured remote `OLLAMA_HOST` is not an on-device engine merely because it speaks the Ollama API. Conversely, a loopback endpoint can proxy hosted inference: cloud-backed models and models with unverified execution locality cannot satisfy strict on-device policy.

A cloud-hosted assistant may coordinate non-sensitive setup, but must not ingest protected prompts, source, diffs or generated analysis. Protected inference and synthesis require an on-device pipeline or a verified local session. Metadata discovery does not make the surrounding conversation air-gapped.

## 3. State Schema & Data Models

Use plain, validated standard-library data structures, with JSON at command boundaries. Unknown metadata is `null`, not an invented value or an unsupported capability.

### Inventory Snapshot

| Field | Type and contract |
| --- | --- |
| `schema_version` | Integer, initially `1`; unknown versions are rejected by consumers. |
| `observed_at` | UTC RFC 3339 timestamp; informational, not evidence that dispatch remains available. |
| `status` | `complete`, `partial` or `unavailable`. |
| `policy` | Object containing boolean `local_only` and `hosted_discovery_allowed`; local-only always overrides hosted permission. |
| `providers` | Provider observations for `ollama` and `mistral`, including intentionally disabled providers. |
| `models` | Array of unique model candidates, sorted by provider, source and exact model identity; never ordered as a quality ranking. |
| `host_ram_bytes` | Positive integer or `null`; advisory physical RAM, not available accelerator memory. |
| `diagnostics` | Structured diagnostics with provider, optional candidate identity, stage, severity, code and sanitised message. |

### Provider Observation

| Field | Type and contract |
| --- | --- |
| `provider` / `source_id` | Provider enum and non-empty configuration-scoped identifier. |
| `state` | `disabled`, `available`, `unavailable`, `auth_required`, `unsupported_version` or `error`. |
| `locality` | `loopback`, `remote` or `unknown`, established from the effective endpoint rather than the provider name; describes transport, not where inference executes. |
| `cli_version` | Non-empty string or `null`; CLI presence is not authentication evidence. |
| `catalogue_state` | `complete`, `partial` or `not_attempted`. |
| `access` | `verified`, `configured`, `missing` or `unknown`; catalogue access does not guarantee later inference or quota. |

### Model Candidate

| Field | Type and contract |
| --- | --- |
| `identity` | Tuple of provider, source identifier and exact resolved model identifier; aliases for the same identity are merged. |
| `reference` | Reversible `provider/source/model_id` string; split at the first two slashes only. Source identifiers contain no slash; model identifiers retain their original namespace and suffix. |
| `model_id` | Non-empty opaque identifier; preserve case, namespace, slashes, colons and suffixes. |
| `aliases` | Array of distinct non-empty aliases supplied by that provider/configuration. |
| `execution_ref` | Exact tag or Vibe-supported reference, or `null` when configuration is required. |
| `evidence` | Non-empty array drawn from `installed`, `configured` and `account_catalogue`. These describe evidence, not quality. |
| `dispatch_state` | `selectable`, `unverified`, `configuration_required` or `unavailable`; does not assert task suitability. |
| `execution_modes` | Adapter-supported subset of `bounded_chat` and `cli_agent`. A model's tool capability cannot create a missing execution harness. |
| `execution_locality` | `on_device`, `hosted` or `unknown`, with evidence from trusted runtime configuration and model metadata. Loopback transport alone is insufficient. |
| `capabilities` | `chat`, `tools`, `fim` and `vision`, each `true`, `false` or `null`, with source attribution. |
| `context_tokens` | Positive integer or `null`; identify whether it is an advertised maximum or an effective configured limit. |
| `size_bytes` | Non-negative integer or `null`; storage size is not a GPU-memory requirement. |
| `parameter_size` / `quantisation` | Provider-reported non-empty strings or `null`; no model-name parsing as authoritative evidence. |
| `resident` | Boolean or `null`; failed residency inspection is not equivalent to `false`. |
| `digest` | Provider-reported immutable identifier or `null`. |
| `identity_fingerprint` | SHA-256 of canonical provider/source endpoint identity, resolved model, execution reference and digest when supplied; never includes credentials. |

Conflicting capability claims remain `null` with a diagnostic unless one source demonstrably describes the effective configuration. Configured context limits constrain advertised maxima. No hardcoded family table fills metadata gaps.

Duplicate tags with contradictory execution locality are quarantined even when
their identity fingerprints match. Preserve hosted evidence ahead of unknown
locality, mark the model unavailable and report `MODEL_LOCALITY_CONFLICT`;
roster order and uncertainty acceptance cannot restore its eligibility.

### Task Requirements & Approved Selection

Requirements contain task kind (`code`, `logic`, `fim`, `tdd`, `prose`, `docs`, `adr`, `architecture` or `utility`), privacy policy, `bounded_chat` or `cli_agent` execution mode, required capabilities and any known minimum context length. Context bounds are positive integers or `null`; do not manufacture requirements from prompt length alone.

An approved selection binds the candidate identity, execution reference, fingerprint, requirements, working directory and permission mode. It is held in the current session, not a new disk cache. Exact execution flags carry that selection across CLI invocations.

Known-incompatible candidates are excluded. Candidates with unknown suitability metadata may be presented conditionally, with explicit uncertainty acceptance before dispatch. Automatic callers cannot assume that acceptance; privacy/locality requirements cannot be waived through this mechanism. A model's estimated resource demands are advisory unless supported by measured evidence.

Automatic one-candidate selection requires known compatible metadata. An explicit
role override establishes identity, not permission to waive unknown suitability.
On-device evidence requires trusted configured loopback transport, reported local
weights and no reported remote/cloud backing; this is not attestation of an
arbitrary proxy. Missing local-weight or backing evidence remains unknown.
In the accepted Ollama phase, cloud-backed or unverified-locality tags remain
visible but their detail endpoints are not queried and they cannot be dispatched,
even through an uncertainty-acceptance flag.

## 4. Invariants & Rules

1. **Discovery precedes recommendation.** No installed-name whitelist, static hosted menu or manifest recommendation can establish availability.
2. **Discovery is metadata-only.** No inference, task-content ingestion, model lifecycle operations, configuration writes or authentication flows. Read only the provider configuration needed for discovery; never transmit it or task text as a catalogue request.
3. **Local-only means on-device.** Require verified loopback transport and on-device execution evidence; reject remote/cloud-backed or unverified execution and prohibit proxy/redirect escape from that boundary. Hosted adapters are not contacted.
4. **Missing and unknown are explicit.** An empty catalogue, failed probe, unsupported CLI and unknown capability are different states.
5. **Explicit choices are authoritative.** Empty overrides, missing referenced models and incompatible or ambiguous choices fail with diagnostics, not substitution.
6. **Recommendation is not dispatch authority.** The assistant proposes from inventory evidence; the runner validates exact selection and policy mechanically.
7. **Approval cannot drift.** A changed alias mapping, endpoint or available digest invalidates the selection. Report the change and require a new choice; do not pick the next candidate.
8. **Availability is provisional.** Installed/configured/account-visible does not guarantee successful loading, quota or inference. Execution failures remain explicit.
9. **No silent cloud fallback.** Optional workers may be skipped visibly in normal review mode; required local-only workers cannot be replaced by cloud evaluation.
10. **Keep implementation small.** Standard-library controller, existing Python compatibility and two concrete adapters; no registry of speculative providers or quality scores.

## 5. Execution & State Mutation Logic

### Shared Ownership

Introduce one small `scripts/model_inventory.py` module containing normalisation, identity validation and provider discovery. Keep Ollama lifecycle operations in [check_ollama.py](../../scripts/check_ollama.py), dispatch and compound execution in [vibe_execute.py](../../scripts/vibe_execute.py), and recommendation guidance in the skills.

All three consumers use the same inventory and validation helpers. The inventory module must not call task classification or inference.

### Ollama Adapter

1. Inspect the configured endpoint and enforce locality policy before opening a connection.
2. Enumerate `GET /api/tags`; preserve every valid advertised identity, regardless of its name.
3. Read residency from `GET /api/ps`, then retrieve capability and context evidence through metadata-only `POST /api/show` requests. Do not return Modelfiles, templates or raw model metadata wholesale.
4. An unsupported detail endpoint leaves candidates visible with unknown fields and an explicit diagnostic. Malformed identifiable entries are diagnosed and excluded; malformed top-level data fails the provider probe.

Residency and hardware hints inform proposals but must not imply a proven memory fit. Existing dispatch-time wave leasing and host-memory constraints remain applicable; discovery must not evict other workloads to improve its options.

### Vibe / Hosted Mistral Adapter

1. Reuse the existing executable resolver. Without Vibe, mark hosted execution unavailable and make no authenticated catalogue request.
2. Read Vibe's effective configuration for the selected working directory: model aliases, provider endpoint and applicable model restrictions. Do not assume one global configuration or that an arbitrary account-visible model is accepted by `--model`.
3. When permitted and existing credentials are usable without login/refresh, query the catalogue appropriate to that Vibe deployment. Preserve configured entries if the request fails, but mark hosted access unverified and emit a diagnostic.
4. Reconcile catalogue entries with CLI dispatch support and configuration restrictions. Account-visible but non-selectable entries remain visible as `configuration_required` or unavailable; never create aliases or modify configuration automatically.
5. Do not equate Vibe subscription credentials with a standard Mistral API key or infer remaining quota from a successful catalogue request.

**Compatibility gate:** Vibe is not installed here, so no non-interactive model-export command has been locally verified. Do not invent a `vibe --list-models` dependency. The implementation must first verify a supported read-only export or a narrow, version-gated bridge in Vibe's own runtime that resolves configuration/authentication without starting an agent. If neither is safe, report `unsupported_version` and retain local discovery.

Upstream Vibe already has a [catalogue client](https://github.com/mistralai/mistral-vibe/blob/c96a6dbb34d34f8a868b3f67b279ecabbf1aa616/vibe/core/model_catalog/client.py) and [catalogue models](https://github.com/mistralai/mistral-vibe/blob/c96a6dbb34d34f8a868b3f67b279ecabbf1aa616/vibe/core/model_catalog/models.py). Reuse its effective configuration/authentication semantics where safe, not its silent fallback or cache-writing behaviour. Artifice must preserve explicit failures and unknown capability fields.

A bridge uses dependencies already provided by the optional Vibe installation; it must not add dependencies to Artifice or implement a partial TOML parser for Python 3.9. Unsupported versions are explicit compatibility failures, not an empty hosted inventory.

### Bounds, Output & Errors

* A discovery pass has a 15-second wall-clock budget, at most four concurrent metadata operations and a maximum three-second timeout per operation, bounded by the remaining budget.
* Enumerate identities before enriching details. Follow hosted pagination within the same budget; incomplete enumeration is `partial`, never a complete empty catalogue.
* No artificial model-count cap. Discovered identities remain present if their detail requests time out.
* `discover` prints one versioned JSON snapshot to stdout and sanitised diagnostics to stderr. Complete usable discovery exits `0`; partial/error or no usable provider exits `1`; invalid arguments or policy conflicts exit `2`. A reachable, valid empty catalogue is complete discovery, not execution success.
* An absent optional CLI is an explicit unavailable observation, not an error by itself when another provider completes. Metadata errors cannot be hidden behind another provider's success.
* No persistent cache. Refresh before presenting a new task's options and revalidate the selected identity immediately before inference. Revalidation may inspect only that selection; it must not rerank or substitute.
* Partial discovery may support a provisional proposal from validated candidates, with the missing evidence and provider failures prominently disclosed. The caller must handle the non-zero discovery result explicitly rather than ignoring it; eligibility and privacy validation still apply.
* Do not log keys, bearer tokens, raw configuration, credential-bearing URLs or unredacted provider response bodies. Provider labels and model identifiers are untrusted metadata, never instructions or shell fragments.

### Proposed Command Contract

The following interface is proposed, not implemented:

```text
vibe_execute.py discover [--local] [--workdir DIR]
vibe_execute.py classify "TASK" [--local]
vibe_execute.py run "TASK" --provider ollama --model EXACT_TAG --expect-identity FINGERPRINT
vibe_execute.py run "TASK" --provider mistral --model EXACT_REFERENCE --expect-identity FINGERPRINT
```

`classify` describes task requirements and complexity only; it no longer claims that a named model is available. `discover` accepts no task text. `run` retains explicit locality and permission controls; the provider flag never overrides `--local`.

`run` and `triage` carry `--task`, `--mode`, repeatable
`--require-capability`, optional positive `--min-context`, and task-scoped
`--accept-unknown` flags. Chat is always required; `cli_agent` additionally
requires tool support. `--auto-approve` is an explicit CLI-agent permission,
never a request to give a bounded Ollama chat runner filesystem autonomy.
Local inference must request an approved minimum context explicitly rather than
mistaking an advertised maximum for an active runtime configuration.

Direct CLI users may supply an exact provider/model without a prior proposal fingerprint: this is an explicit request to resolve the current identity, which must be validated and reported. Assistant-approved proposals always pass the fingerprint. Missing selection exits `2` with instructions to discover/choose; it does not automatically invoke a hardcoded model.

The runner must receive and validate the approved task requirements as well as model identity. Unknown suitability evidence requires an explicit, task-scoped acceptance flag; it must never relax a privacy requirement or a known incompatibility.

### Consumer Integration & Intentional Behaviour Changes

| Surface | Required change |
| --- | --- |
| [vibe-execute](../../skills/vibe-execute/SKILL.md) | Replace static tier-to-model menus with discovery and assistant-led proposals. Preserve task complexity as guidance, not a model catalogue. |
| [local-code](../../skills/local-code/SKILL.md) | Use local-only discovery and an exact approved installed tag; preserve bounded coding/TDD workflows and actual-model provenance. |
| [review](../../skills/review/SKILL.md) and [its reference](../../skills/review/references/review-framework.md) | Select code/prose workers from shared evidence; one model may serve both roles. Optional workers can be omitted visibly; local-only mode still requires both role assignments before protected ingestion. |
| `check_ollama.py select --task` | Preserve `model`, `resident` and `fallback` output. Return a model only for a valid explicit override or one unambiguous eligible local candidate; otherwise exit `2` with a reason and `fallback: null`. Never make an implicit choice among several candidates. |
| Existing `ARTIFICE_CODE_MODEL` / `ARTIFICE_PROSE_MODEL` | Preserve exact-tag semantics and task-role scope; empty, missing or invalid values still fail explicitly. All selection failures return `fallback: null`. |
| Existing generic local aliases | Keep them as local discovery requests, not aliases for Qwen. They resolve only through an explicit role override or one unambiguous eligible candidate; otherwise require selection. |
| Existing `--model` without `--provider` | Accept only a legacy generic local request or an exact, uniquely resolved Vibe reference. Assistant-generated calls use explicit providers. Remove prefix-based provider guessing; an arbitrary `local-*` name is not a routing directive. |
| Compound triage | Select the triage engine first. Include eligible inventory identities in its execution context; wave proposals reference those identities rather than `large`, `codestral` or `fast`. Validate identities against the inventory and obtain approval before dispatch. |
| [README](../../README.md), applicable agent instructions and tests | Document the new commands, changed defaults, privacy boundary and compatibility limitations; remove claims of fixed model preferences. Keep shared prompt budgets within existing limits. |

For compound local-only work, triage and every wave must remain local regardless of generated recommendations. Existing manifest shape/dependency checks remain; provider-qualified inventory references replace the meaning of `recommended_engine`. Missing or invented references fail validation.

On adoption, this design supersedes only fixed-model preferences and automatic cloud-fallback clauses in [design 001](001_sovereign_quota_fortress.md) and [design 003](003_copilot_symlink_integration.md). It retains standard-library tooling, privacy, specification precedence and exact-model provenance. Historical approval is not rewritten as part of this proposal.

### Phased Adoption

1. **Compatibility and contracts:** verify Vibe's read-only integration against a supported installed version; create redacted fixtures and failing inventory/identity/privacy tests.
2. **Discovery:** implement both adapters, structured diagnostics and the shared JSON contract. This phase performs no inference.
3. **Selection and dispatch:** wire all three consumers, overrides, explicit identity binding and inventory-constrained compound triage together; update related documentation in the same change.
4. **Acceptance:** run native verification and metadata-only smoke checks. Any inference smoke test requires separate explicit permission and a non-sensitive prompt.

The compatibility gate must pass before claiming hosted discovery support.
Investigation found no installed runtime and no safe drop-in configuration
export. The developer explicitly deferred that phase rather than authorising an
isolated Vibe/Python 3.12 test environment. No bridge or hosted inference is
included in the current implementation.

## 6. Edge Cases & Failure Modes

| Case | Required behaviour |
| --- | --- |
| Only an unfamiliar local tag is installed | Include it; determine suitability from metadata or show explicit uncertainty. Do not report no installed models. |
| No installed models | Complete empty inventory with explanation; selection exits `2`. No pull or cloud fallback. |
| Several plausible local models | Assistant proposes; non-interactive selection requires an exact choice rather than taking the first list item. |
| Embedding-only model or unsupported execution mode | Keep it visible; exclude it from incompatible task proposals. |
| `/api/ps` or `/api/show` fails | Retain discovered candidates; affected fields become `null`, with partial status and diagnostics. |
| Vibe absent, incompatible or unauthenticated | Report the distinct state; do not offer hosted dispatch as ready or start login. |
| Catalogue access succeeds but inference is denied | Surface the execution error; account visibility is not an inference guarantee. |
| Catalogue entry is blocked by Vibe configuration | Keep the restriction; never manufacture a usable alias. |
| Alias, endpoint or digest changes after approval | Reject stale selection before warming/inference; require renewed approval. |
| Remote/proxied Ollama or a cloud-backed model under local-only policy | Refuse before transmitting protected input; no hosted discovery or fallback. Unknown execution locality also blocks strict-local dispatch. |
| Metadata is missing, contradictory or malformed | Preserve unknowns and diagnostics; do not guess from the family name. |
| Deadline expires during a large or paginated inventory | Return explicit partial results and non-zero status; never hide truncation. |
| Model fails to load or available memory changes | Surface dispatch failure without swapping models or evicting unrelated work during discovery. |

## 7. Verification & Automated Test Strategy

Use standard-library `unittest`, mocked HTTP/subprocesses, fake clocks and disposable configuration fixtures. Automated tests must not load a model, require real credentials, mutate personal configuration or contact a hosted service.

### Contract & Integration Acceptance

* **Roster independence:** exercise zero, one and several installed models, unfamiliar tags, namespaces and reordered lists. Every valid discovered identity appears exactly once, with deterministic non-quality ordering. Conflicting duplicate locality is quarantined in both orderings, including under `--accept-unknown`.
* **Concrete regression:** a fixture advertising only `qwen3.8:27b-mlx` is discoverable without a whitelist or override. Missing capability evidence is explicit, not treated as proof of suitability.
* **Capability filtering:** embedding-only, unsupported tool-loop, insufficient-context, unknown and conflicting-metadata cases produce the specified exclusions or conditional proposals.
* **Provider distinction:** in the accepted local phase, assert distinct Vibe-absent and hosted-adapter-deferred states with zero hosted/configuration/authentication calls. Authentication, restrictions and catalogue integration tests belong to the deferred hosted phase.
* **Exact identity:** prove byte-for-byte model/reference preservation through approval, warming, inference and provenance. Changed mapping/endpoint/digest prevents every inference call.
* **Overrides and ambiguity:** preserve role-specific environment overrides and existing response keys; invalid/empty values, ambiguous choices and all failures have `fallback: null` and non-zero selection exit.
* **Read-only discovery:** assert no chat/generate/pull/unload requests, agent start, cache/configuration writes, credential refresh or task-content ingestion. Only allowlisted provider configuration is read; neither it nor task content appears in outgoing metadata requests.
* **Privacy:** `--local` produces zero hosted calls; remote endpoints, proxies, redirects, cloud-backed models and unknown execution locality cannot satisfy on-device policy. Protected outputs are not returned into cloud orchestration.
* **Bounds:** fake-clock tests assert the 15-second aggregate deadline, three-second operation limit, maximum four concurrent operations and explicit partial status on exhaustion. Pagination and detail failures never silently discard discovered identities.
* **Error/output shape:** assert JSON schema, stable diagnostic codes, stderr separation, redaction and exact exit codes. A partial inventory is never presented as complete.
* **All consumers:** verify `vibe-execute`, `local-code`, normal/strict-local review and compound triage use the same inventory and identity validator. Unknown manifest identities cannot reach dispatch.
* **Resource stewardship:** discovery leaves residency unchanged; dispatch still checks warming success and preserves existing wave-leasing safeguards.

Run the smallest affected unit selectors during development, then [the native lint/test wrapper](../../scripts/lint.sh) before implementation handoff. Preserve installer, adapter, prompt-budget and existing manifest regression coverage.

### Proposal Validation & Approval Boundary

For this document, validate headings and relative links with the existing Markdown checker. The recorded 26-test baseline predates any implementation change.

The [contract review](../reviews/004_discovery_driven_model_proposals_review.md)
records its actual provenance and remaining gates. It is a direct review, not an
independent zero-context review. `validate_egm.py . --spec 004` and the full
repository approval gate must not be described as passing until the recorded
review and human approval are complete. Do not weaken the validator or invent
independent approval to make a draft green.

## 8. Goldfish Review Gates

- [x] Human workshop scope confirmed before drafting
- [x] Vibe scope decision recorded: hosted adapter deferred, with explicit unsupported behaviour
- [x] Direct design review completed and recorded without claiming independent approval
- [x] Local-phase contradictions, privacy boundaries and failure contracts resolved
- [x] Human developer approves the proposal and intentional compatibility changes
- [x] Matching contract review has `Verdict: Approved` for the accepted local phase
- [x] Targeted EGM validation passes before implementation

---

*Signed by: **Principal Developer Coach ("The Catalyst")** (`developer-coach`) - Model: **`gpt-6.1-sol`** - Skills: **`coach-frameworks v1.1.0`**, **`spec-egm`** - Date: `2026-11-05`*
