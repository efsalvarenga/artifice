# Task Board & Feedback Pipeline: `artifice`

This document tracks active development tasks, roadmap milestones, and cross-project feedback items captured from consuming repositories (e.g. `emergent`, `arete`).

---

## Incoming Feedback / Inbox

*This section receives asynchronously logged friction, missing edge cases, and enhancement proposals captured from active project sessions across the local repository ecosystem.*

<!-- Incoming entries are appended here following the format:
* **[YYYY-MM-DD]** *(from `<project>` @ `<branch>`)*:
  - **Component:** `<agent/skill/rule>`
  - **Operational Context:** `<what task was underway>`
  - **Specific Friction & Defect:** `<exact issue or edge case>`
  - **Actionable Remediation:** `<concrete proposal to implement>`
-->

---

## Active Roadmap & Backlog

### Milestone 1: Cross-Project Ingestion & CI Verification (v1.2.0)

- [ ] `[AUTO]` Implement verification harness (`./scripts/verify.sh`) to audit Markdown cleanliness, YAML frontmatter syntax, and absolute link resolution across all skills and agents.
- [ ] `[AUTO]` Add automated skill schema validation against Antigravity skill specifications.
- [ ] `[SEMI]` Draft bootstrapping helper script (`./scripts/setup_collaborator.sh`) to streamline global `skills.json` registration for new developers.

---

## Completed Tasks

* **[2026-11-01]** `feat(core): bootstrap artifice repository with code-reviewer and developer-coach` ([PR #1](https://github.com/efsalvarenga/artifice/pull/1))
* **[2026-11-01]** `feat(tools): migrate developer-coach and coach-frameworks from emergent` ([PR #2](https://github.com/efsalvarenga/artifice/pull/2))
* **[2026-11-01]** `feat(review): establish dual-model consensus and on-device air-gapped review modes` ([PR #3](https://github.com/efsalvarenga/artifice/pull/3))
