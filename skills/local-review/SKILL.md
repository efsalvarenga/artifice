---
name: local-review
description: Review architectural docs, large code diffs, or draft release documentation using the local mistral-nemo:12b model running via Ollama.
---

# Local Document & Code Review with Mistral NeMo

Use this skill when the user requests a comprehensive architectural review, long-context code evaluation, PR feedback, or documentation drafting powered by the local `mistral-nemo:12b` model.

## Procedure

1. **Collate Context**:
   Gather the relevant document, diff, or file contents. Benefit from Mistral NeMo's 128k native context window for multi-file reviews.

2. **Invoke Local Model**:
   Query the local Ollama instance using the `ollama_chat` tool or directly via curl:
   ```bash
   curl -s http://localhost:11434/api/chat -d '{
     "model": "mistral-nemo",
     "messages": [
       {"role": "system", "content": "You are a senior systems architect. Provide thoughtful, well-structured architectural review and documentation in British English."},
       {"role": "user", "content": "<PROMPT>"}
     ],
     "stream": false
   }'
   ```

3. **Synthesise Feedback**:
   Format the resulting insights with clear headings, bullet points, and actionable next steps.
