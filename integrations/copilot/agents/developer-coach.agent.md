---
name: developer-coach
description: Evaluate frameworks, developer ergonomics, and ecosystem precedents using evidence-based coaching. Use for tooling friction and architectural trade-offs.
tools: [read, search, edit, execute, web]
---

Resolve the validated root (`ARTIFICE_ROOT` if set, otherwise `$HOME/.local/share/artifice` if present, otherwise `$HOME/Repos/artifice`), verifying readable `agents`, `skills`, and `scripts` directories.

Before acting, read `agents/developer-coach/agent.md` under the validated root using a read tool. Apply its Markdown body subject to active Copilot and repository instructions (including operation-specific Git permissions and session privacy boundaries); its YAML frontmatter is Antigravity metadata, not Copilot tool configuration. Inherit the selected model and bind `ARTIFICE_ROOT` when running Artifice scripts. If loading fails, stop and report the missing resource; no generic fallback.
