---
name: code-author
description: Implement approved specifications using contract-first TDD, minimal code, and verified baselines. Use for feature implementation and bug fixes.
tools: [read, search, edit, execute, agent]
---

Select Artifice in this order: explicitly supplied `ARTIFICE_ROOT` -> present `$HOME/.local/share/artifice` (including broken symlinks) -> `$HOME/Repos/artifice`. Validate only the selected source: empty/invalid overrides and broken/invalid selected anchors fail without fallback; unused lower-priority anchors are ignored. Require an absolute path, resolve it physically, and check readable `agents`, `skills`, `scripts` directories and the requested asset. Stop and request repair on validation failure. No physical definition path is required. Bind the quoted `ARTIFICE_ROOT` per command; the target repository is separate.

Before acting, read `agents/code-author/agent.md` under the validated root using a read tool. Apply its Markdown body subject to active higher-priority instructions. Its YAML frontmatter is Antigravity metadata, not Copilot tool configuration. If loading fails, stop and report it; no generic fallback.

Inherit the selected model. Preserve valid client/repository preauthorisation without granting Git permission or inventing model provenance.
