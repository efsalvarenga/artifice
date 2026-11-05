---
name: review
version: 1.4.0
description: >-
  Universal code and architectural review skill using the Principal Code Reviewer
  ("The Gatekeeper") persona and the 8-Pillar Framework. Driven by the orchestrator
  with optional external offloading via vibe-execute and explicit privacy boundaries.
argument-hint: "[--local] [PR_NUMBER | branch | <file_or_doc_path>]"
---

# Universal Code & Architecture Review (`review`)

Evaluate PRs, diffs, files or designs using **The Gatekeeper** and the **8-Pillar Framework**.

## Reference Materials

* [Reviewer persona](../../agents/code-reviewer/agent.md)
* [Rubric, worker selection and privacy](references/review-framework.md)
* [Discovery gateway](../vibe-execute/SKILL.md) and [Ollama lifecycle](../../scripts/check_ollama.py)
* [Invariant dossier compiler](../../scripts/build_review_dossier.py)

Resolve and export `ARTIFICE_ROOT` from its explicit value when set, otherwise `$HOME/.local/share/artifice` when present, otherwise `$HOME/Repos/artifice`, and resolve links from `ARTIFICE_ROOT/skills/review/`. Verify readable `agents`, `skills` and `scripts` directories; stop on failure.

## 1. Scope, Privacy & Baseline

Parse target: PR number, branch, file or design. Check privacy **before** reading target content.

* **Normal:** Inspect the target and record native test/lint baselines. Workers are optional; direct review is valid.
* **Strict local:** `--local`, `Privacy: on-device` or `Review: local-only` requires on-device workers. Complete Step 3 before protected ingestion; both role assignments must succeed, though one model may fill both. Protected prompts, source, diffs and outputs stay in local pipelines or verified local sessions, never cloud context. Discovery does not make this conversation air-gapped.

## 2. Ingest Invariants

Use the approved specification's state schema, invariants and edge cases. Keep strict-local ingestion on-device.

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/build_review_dossier.py" .
```

## 3. Discover, Approve & Lease Workers

When justified, use gateway metadata-only discovery. Propose code/prose assignments from capability, context and locality evidence; obtain approval of concrete tags, fingerprints and requirements. No static defaults, quality ranking or cloud fallback; hosted Vibe support is deferred.

Select each approved worker through the shared inventory, using `--model EXACT_TAG --expect-identity HASH` and task-scoped `--accept-unknown` only when approved. Exact CLI tags precede `ARTIFICE_CODE_MODEL` / `ARTIFICE_PROSE_MODEL`; implicit selection requires an override or one known-compatible candidate. Exit `2` means failure, never use `fallback`.

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" select --task code --model "$code_model" --expect-identity "$code_identity"
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" select --task prose --model "$prose_model" --expect-identity "$prose_identity"
```

After successful revalidation, warm only non-empty selected tags:

```bash
if [[ ! ${ARTIFICE_ROOT+x} ]]; then
  ARTIFICE_ROOT="$HOME/Repos/artifice"
  [[ ! -d "$HOME/.local/share/artifice" ]] || ARTIFICE_ROOT="$HOME/.local/share/artifice"
fi
export ARTIFICE_ROOT
if [[ -n "${code_model:-}" ]]; then
  if ! python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" warm "$code_model" --lease 5m; then
    printf 'Ollama worker warming failed: %s\n' "$code_model" >&2
    code_model=""
  fi
fi
if [[ -n "${prose_model:-}" && "$prose_model" != "${code_model:-}" ]]; then
  if ! python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" warm "$prose_model" --lease 5m; then
    printf 'Ollama worker warming failed: %s\n' "$prose_model" >&2
    prose_model=""
  fi
fi
```

Report optional selection/warming failures visibly and omit that worker. In strict-local mode, stop if either assignment fails, before protected ingestion; uncertainty acceptance never relaxes privacy.

## 4. Evaluate & Verify

* **Normal:** The orchestrator covers design/contracts, inspects defects, filters false positives against invariants and synthesises Conventional Comments across all eight pillars. Delegate only justified bounded work.
* **Strict local:** `code_model` covers Pillars 2, 3, 5, 7; `prose_model` covers 1, 6, 8 and synthesis. Native checks cover Pillar 4.
* Dispatch through gateway `run` with exact provider/tag/fingerprint and approved requirements; Ollama supports bounded chat only. Revalidate identity, capabilities and locality before inference. Run native checks between waves.

## 5. Teardown & Actual Provenance

Preserve existing post-wave teardown after leased work, never during discovery:

```bash
python3 "${ARTIFICE_ROOT:-$HOME/Repos/artifice}/scripts/check_ollama.py" unload --all
```

List only workers actually used, preserving exact references and roles (or `none`):

```markdown
---

*Signed by: **Principal Code Reviewer ("The Gatekeeper")** (`code-reviewer`) · Orchestrator: **`<Actual Model or Assistant>`** · Workers: **`<actual references + roles, or none>`** · Skill: **`review v1.4.0`** · Date: `<YYYY-MM-DD>`*
```
