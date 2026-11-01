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
   Query the local Ollama instance using the `ollama_chat` tool or directly via curl:
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

3. **Verify and Present**:
   Validate that the generated code satisfies the project's architecture, test requirements, and style guidelines before presenting it to the user.
