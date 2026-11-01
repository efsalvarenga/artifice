# Design Specification: Sovereign Quota Fortress & Unified Review

**Document ID:** `docs/designs/001_sovereign_quota_fortress.md`  
**Status:** Approved  
**Author:** Elephant Agent & Developer  
**Target Milestone:** Milestone 2 (v1.3.0)  

---

## 1. Overview & Objectives

This specification defines the architectural design for **Milestone 2 (v1.3.0)** of `artifice`: establishing sovereign, on-demand local model execution to conserve cloud API tokens, managing host memory leases, and consolidating review capabilities into a single universal skill.

### Goals

* **Quota Conservation:** Automatically offload repetitive logic fuzzing (Pillar 2) and prose evaluations (Pillar 6) to local resident models (`qwen2.5-coder:14b` and `mistral-nemo:12b`) during reviews, saving up to 70% of cloud API tokens.
* **Memory Lifecycle Sovereignty:** Provide zero-dependency host memory management (`scripts/check_ollama.py`) supporting sub-100ms health checks, wave leasing (`keep_alive: 5m`), and explicit memory purging (`unload --all`) to prevent RAM exhaustion on 16 GB Apple Silicon Macs.
* **Universal Review Interface:** Consolidate `review-pr` and `local-review` into a single universal `/review` skill capable of inspecting PRs, branches, diffs, architectural specifications, or individual files.
* **EGM Workshop Formalisation:** Formally enshrine Step 1A (Interactive Design Workshop Canvas) in `spec-egm` to prevent agents from bypassing human design alignment.

### Non-Goals

* **22B Model Dependency:** Attempting to force `codestral:22b` into 16 GB unified memory envelopes (avoiding SSD swap and latency degradation).
* **Autonomous Merge Authority:** Permitting agents to formally approve or merge PRs (formal sign-off remains strictly human `[HUMAN]`).

---

## 2. Domain Framing & User/System Experience

The system balances frontier cloud reasoning with local on-device execution:
* When a user runs `/review [target]`, the primary cloud orchestrator (Gemini) acts as the Planner.
* It queries `scripts/check_ollama.py` to inspect local model availability.
* If resident engines exist, it issues wave leases (`keep_alive: 5m`), delegates orthogonal inspection streams to local subagents, synthesises findings, and purges GPU memory (`unload --all`) upon completion.
* If Ollama is offline or unheated, it instantaneously falls back to cloud `flash` without stalling.

---

## 3. State Schema & Data Models

### Ollama Status Schema (`get_status()`)

```json
{
  "online": true,
  "ping_ms": 14.13,
  "resident": [
    {
      "name": "qwen2.5:14b",
      "size_vram_gb": 9.1,
      "expires_at": "2026-11-01T23:02:17.043799+01:00"
    }
  ],
  "available": [
    "qwen2.5:14b",
    "mistral-nemo:latest"
  ]
}
```

### Model Selection Contract (`select_best_model(task_type)`)

```json
{
  "model": "qwen2.5:14b",
  "resident": true,
  "fallback": null
}
```

### Review Provenance Signature Schema

```markdown
*Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Orchestrator: **<ORCHESTRATOR_MODEL>** · Workers: **<LOCAL_WORKER_1> (Pillar 2 Logic)** + **<LOCAL_WORKER_2> (Pillar 6 Docs)** · Skill: **`review v1.3.0`** · Date: `<YYYY-MM-DD>`*
```

---

## 4. Invariants & Rules

* **Invariant 1 (Host Memory Safety):** Total active local model memory on 16 GB Apple Silicon must never exceed 11.5 GB. Two distinct 14B models must never be kept resident simultaneously; sequential model calls must rely on wave leasing and LRU eviction.
* **Invariant 2 (Zero-Waste Teardown):** Every multi-step review or coding wave that leases local memory must invoke `scripts/check_ollama.py unload --all` upon task conclusion to restore host RAM to 0MB VRAM footprint.
* **Invariant 3 (Zero External Dependencies):** All repository lifecycle scripts in `scripts/` must run strictly on the Python 3 standard library with zero third-party packages.
* **Invariant 4 (EGM Design Precedence):** Implementation code and PR drafting are strictly prohibited until an Elephant Design Specification has been authored in `docs/designs/` and verified with a Goldfish review.

---

## 5. Execution & State Mutation Logic

### 1. Pre-Flight Health Check

1. The orchestrator calls `scripts/check_ollama.py status`.
2. If `online == false`, the review proceeds in pure cloud mode via `flash`.

### 2. Wave Leasing

1. The orchestrator calls `scripts/check_ollama.py warm <model> --lease 5m`.
2. Ollama loads the weights into Metal GPU memory.

### 3. Orthogonal Subagent Execution

1. Subagent 1 probes Pillar 2 logic invariants using local Qwen.
2. Subagent 2 evaluates Pillar 6 prose using local Mistral NeMo.

### 4. Cache Purge

1. Upon synthesis completion, `scripts/check_ollama.py unload --all` is called.
2. Ollama issues `POST /api/generate` with `keep_alive: 0`, evicting the model.

---

## 6. Edge Cases & Failure Modes

* **Ollama Daemon Offline:** Returns `online: false` in $<50\text{ms}$; orchestrator defaults to cloud `flash` without throwing unhandled exceptions.
* **Model Not Pulled:** `select_best_model` detects missing model and specifies fallback `cloud-flash` with clear diagnostic reason.
* **Memory Contention on 16 GB Mac:** Wave leasing uses a 5-minute timeout; explicit `unload --all` provides immediate recovery.

---

## 7. Verification & Automated Test Strategy

### Unit & Functional Tests

* `./scripts/lint.sh`: Audits Markdown cleanliness, YAML frontmatter, relative link integrity, and Core Diet ceilings ($\le 180$ lines).
* `python3 scripts/validate_egm.py .`: Asserts that `docs/designs/001_sovereign_quota_fortress.md` contains all required sections and has a matching approved Goldfish review.
* `scripts/check_ollama.py status`: Validates sub-100ms response time and JSON schema validity.
