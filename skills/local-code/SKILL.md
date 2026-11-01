---
name: local-code
description: Delegate deep algorithmic refactoring, logic analysis, or unit test generation to the local qwen2.5:14b model running via Ollama.
---

# Local Code Refactoring & Logic with Qwen 2.5

Use this skill when the user requests an offline code analysis, complex refactoring, test suite synthesis, or algorithmic debugging powered by the local `qwen2.5:14b` model.

## Procedure

1. **Extract Code Context**:
   Identify the target source file, function block, or algorithmic problem to be analysed.

2. **Invoke Local Model**:
   Query the local Ollama instance directly (via the `ollama` MCP server or HTTP API) using `qwen2.5:14b`:
   ```bash
   curl -s http://localhost:11434/api/chat -d '{
     "model": "qwen2.5:14b",
     "messages": [
       {"role": "system", "content": "You are an expert software engineer. Provide clean, well-tested, robust code in British English."},
       {"role": "user", "content": "<PROMPT>"}
     ],
     "stream": false
   }'
   ```

3. **Pry into Boundary Edge Cases**:
   When generating or refactoring code and unit tests, explicitly identify 2–3 boundary conditions (e.g. empty inputs, zero/negative bounds, capacity limits, concurrent access) and ensure dedicated unit tests explicitly cover them.
