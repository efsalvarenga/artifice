---
name: local-code
version: 1.3.0
description: Delegate bounded algorithmic refactoring, logic analysis, FIM synthesis or unit test generation to an installed local coding model via Ollama.
---

# Local Code Refactoring & Logic

## Resources, Authority & Privacy

Select Artifice in this order: explicitly supplied `ARTIFICE_ROOT` -> present `$HOME/.local/share/artifice` (including broken symlinks) -> `$HOME/Repos/artifice`. Validate only the selected source: empty/invalid overrides and broken/invalid selected anchors fail without fallback; unused lower-priority anchors are ignored. Require an absolute path, resolve it physically, and check readable `agents`, `skills`, `scripts` directories and the requested asset. Stop and request repair on validation failure. No physical definition path is required. Bind the quoted `ARTIFICE_ROOT` per command; the target repository is separate.

Documentation: [code-author](../../agents/code-author/agent.md), [model manager](../../scripts/check_ollama.py). When authoring, read the role body under the validated root; do not adopt Antigravity metadata or execute lexical paths through personal registration symlinks. Use the selected project interpreter where needed.

Follow active client/repository authority, including valid preauthorisation. Explicit design/material-revision approval is separate from Git permission; branch changes, staging, commits, pushes and PR publication require operation-specific authorisation.

Check privacy before protected reads using minimum policy metadata. Strict local-only work requires a genuinely local session and verified local endpoint, with no cloud fallback. Stop a cloud conversation first: a local worker leaves it hybrid, not offline.

## 1. Select & Lease

```bash
ARTIFICE_ROOT="<validated-root>"; python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" select --task code
```

`ARTIFICE_CODE_MODEL` covers code/logic/fim/tdd. An explicitly empty value fails before querying Ollama; a non-empty value must exactly match an installed tag. Offline/uninstalled configured selections fail with `fallback: null`, exit 2. Ignore unrelated `ARTIFICE_PROSE_MODEL`.

Unset selection retains installed-list order: first tag containing `qwen2.5-coder:14b`, otherwise first containing `qwen2.5:14b`. Failure's `cloud-flash` hint is advisory, never permission to execute remotely. Do not download models or silently substitute.

Capture successful JSON `model` as `code_model`; success also reports boolean `resident` and `fallback: null`. Bind that exact tag and root independently per command:

```bash
ARTIFICE_ROOT="<validated-root>"; code_model="<successful selection tag>"; python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" warm "$code_model" --lease 5m
```

## 2. Bounded Inference & TDD

Use the same selected tag in inference, not an assumed default. Example payload and request (replace placeholders with authorised inputs):

```python
import json
from urllib.request import Request, urlopen

code_model = "<exact model tag from successful selection>"
payload = {"model": code_model, "messages": [
    {"role": "system", "content": "Generate minimal deterministic code and boundary tests in British English."},
    {"role": "user", "content": "<bounded authorised task>"},
], "stream": False}
request = Request("http://localhost:11434/api/chat", data=json.dumps(payload).encode(),
                  headers={"Content-Type": "application/json"})
with urlopen(request, timeout=120) as response:
    print(response.read().decode())
```

Identify 2–3 concrete boundaries (empty inputs, zero/negative bounds, capacity limits); generate contract tests before logic and verify native Red/Green results. Keep orchestration and architectural contracts with the current client.

## 3. Teardown & Provenance

At authorised leased-wave conclusion:

```bash
ARTIFICE_ROOT="<validated-root>"; python3 "$ARTIFICE_ROOT/scripts/check_ollama.py" unload --all
```

Report actual teardown success/errors, not guaranteed memory or latency. Record `code_model` as worker provenance only if inference actually ran. For separately authorised commits, use actual contributor tags/handles in `Model-Author` and `Co-authored-by`, never a fixed model signature or guessed orchestrator identity.
