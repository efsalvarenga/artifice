---
name: review
version: 1.3.0
description: >-
  Universal code and architectural review skill using the Principal Code Reviewer
   ("The Gatekeeper") persona and the 8-Pillar Framework. Uses the current client
   orchestrator with optional local Ollama consultation and explicit privacy boundaries.
argument-hint: "[--local] [PR_NUMBER | branch | <file_or_doc_path>]"
---

# Universal Code & Architecture Review

## Resources, Authority & Privacy

Select Artifice in this order: explicitly supplied `ARTIFICE_ROOT` -> present `$HOME/.local/share/artifice` (including broken symlinks) -> `$HOME/Repos/artifice`. Validate only the selected source: empty/invalid overrides and broken/invalid selected anchors fail without fallback; unused lower-priority anchors are ignored. Require an absolute path, resolve it physically, and check readable `agents`, `skills`, `scripts` directories and the requested asset. Stop and request repair on validation failure. No physical definition path is required. Bind the quoted `ARTIFICE_ROOT` per command; the target repository is separate.

Establish privacy before protected reads, using arguments and minimum applicable policy metadata. `--local`, `Privacy: on-device` or `Review: local-only` requires a genuinely local session with no cloud fallback. Stop a cloud conversation before ingesting target code, diffs, specifications or dossiers. Cloud+Ollama remains hybrid, not offline; behavioural instructions do not establish technical containment.

Read `agents/code-reviewer/agent.md` under the validated root and apply its Markdown body, not its Antigravity metadata. Documentation: [role](../../agents/code-reviewer/agent.md), [eight-pillar rubric/Conventional Comments](references/review-framework.md), [model manager](../../scripts/check_ollama.py), [dossier compiler](../../scripts/build_review_dossier.py). Do not execute lexical paths through personal registration symlinks. Use the selected project interpreter where needed.

Follow active client/repository authority, including valid preauthorisation. This skill grants no Git permission; branch changes, staging, commits, pushes and PR publication require operation-specific authorisation. Explicit design/material-revision approval remains separate from review approval.

## 1. Scope, Invariants & Baseline

Parse a PR number, branch, file or document. After privacy clearance, read the target (`gh pr diff <PR>`, `git diff main...HEAD`, or direct file read). Ingest the active EGM specification's schema, invariants and edge cases. Compile repository constraints:

```bash
ARTIFICE_ROOT="<validated-root>"; python3 "$ARTIFICE_ROOT/scripts/build_review_dossier.py" "<target_repo>"
```

Run authorised native tests/lint and record pass/fail, rather than assuming a clean baseline.

## 2. Select & Lease Workers

For authorised local consultation, select each needed task group independently:

```bash
ARTIFICE_ROOT="<validated-root>"; python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" select --task code
ARTIFICE_ROOT="<validated-root>"; python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" select --task prose
```

`ARTIFICE_CODE_MODEL` covers code/logic/fim/tdd; `ARTIFICE_PROSE_MODEL` covers prose/docs/adr/architecture. Only the selected group's override is validated. Empty, offline or uninstalled configured selections fail with exit 2 and no fallback. Unset variables retain [existing defaults](../../README.md#local-model-configuration); `cloud-flash` failure hints are advisory, never execution permission.

Capture successful JSON `model` values as `code_model`/`prose_model`. Bind the exact tags and root independently in every tool command; shell state does not persist:

```bash
ARTIFICE_ROOT="<validated-root>"; code_model="<successful code selection tag>"; python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" warm "$code_model" --lease 5m
ARTIFICE_ROOT="<validated-root>"; prose_model="<successful prose selection tag>"; python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" warm "$prose_model" --lease 5m
```

Use those same selected tags in Ollama inference payloads, never hard-coded defaults:

```python
code_request = {"model": code_model, "messages": code_messages, "stream": False}
prose_request = {"model": prose_model, "messages": prose_messages, "stream": False}
```

## 3. Evaluate & Synthesise

In ordinary hybrid work, the current client orchestrator directly evaluates design/specification alignment and native verification. When delegated consultation is appropriate, `code_model` audits functionality, complexity, naming and types (pillars 2/3/5/7); `prose_model` audits comments/docs, British English and narrative sovereignty (6/8). Probe 2–3 concrete boundaries and assert coverage.

Cross-check worker findings against the actual diff and intentional invariants. Remove false positives, inspect overlooked defects and synthesise all eight pillars. Under strict local-only policy, perform all work in the verified local session: code analysis uses `code_model`; architecture, documentation, governance and final synthesis use `prose_model`.

## 4. Teardown & Truthful Report

At authorised leased-wave conclusion, report actual teardown success/errors, without latency or zero-memory guarantees:

```bash
ARTIFICE_ROOT="<validated-root>"; python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" unload --all
```

Use Conventional Comments (`issue`, `suggestion`, `question`, `praise`), explicit severity/pillar and an evidence-backed verdict. Include baseline failures and unavailable checks.

Sign as `code-reviewer` ("The Gatekeeper"), skill `review v1.3.0`, date, actual assistant/exposed model, and worker provenance: actual `code_model`/`prose_model` tags **only if used**, otherwise `none`. Never guess identities or claim on-device execution without verified session/worker locality.
