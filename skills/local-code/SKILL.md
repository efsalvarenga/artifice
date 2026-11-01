---
name: local-code
description: Delegate deep algorithmic refactoring, logic analysis, or unit test generation to the local qwen2.5:14b model running via Ollama.
---

# Local Code Refactoring & Logic with Qwen 2.5

Use this skill when the user requests an offline code analysis, complex refactoring, test suite synthesis, or algorithmic debugging powered by the local `qwen2.5:14b` model.

## Procedure

1. **Extract Code Context**:
   Identify the target source file, function block, or algorithmic problem to be analysed.

2. **Invoke Local Model (under Heavy Lock)**:
   Query the local Ollama instance protected by `heavy_lock.py` to prevent memory thrashing on Apple Silicon:
   ```bash
   python3 ~/Repos/artifice/scripts/heavy_lock.py run --slot gpu --name "local-code" -- \
   curl -s http://localhost:11434/api/chat -d '{
     "model": "qwen2.5:14b",
     "messages": [
       {"role": "system", "content": "You are an expert software engineer. Provide clean, well-tested, robust code in British English."},
       {"role": "user", "content": "<PROMPT>"}
     ],
     "stream": false
   }'
   ```

3. **Verify with Targeted Sabotage Probe**:
   When generating new unit tests, verify they catch boundary errors using `sabotage_check.py`:
   ```bash
   python3 ~/Repos/artifice/scripts/sabotage_check.py probe \
     --file <target_file> \
     --old "<boundary_guard>" \
     --new "<mutated_guard>" \
     --test-cmd "<test_command>"
   ```
   Confirm that the test turns red on mutated logic (mutant is `KILLED`) before declaring the test complete.
