# Block Contract: [Block ID] — [Block Title]

**Block ID:** `[ID]` (e.g. `001` or `B01`)  
**Target Repository:** `[Path]` (e.g. `~/Repos/emergent`)  
**Active Branch:** `[Branch]` (e.g. `agent/milestone-3-rules`)  
**Execution Autonomy:** `[AUTO]` | `[SEMI]`  
**Subagent Model:** `flash` (default) | `inherit` | `pro`  

---

## 0. Authorisation & Operational Framing

* **Framing & Authorization:** [Verbatim developer instruction, timestamp, and target scope.]
* **Pilot Status:** [Yes (Block 1 Pilot) / No (Standard Batch Block)]

---

## 1. Objective & Scope Boundaries

### In Scope

* [Specific capability, refactor, or test suite to deliver]

### Out of Scope (Explicit Guardrails)

* [Forbidden modifications, deferred items, or adjacent modules that must NOT be touched]

---

## 2. Measured Disk Baseline

Do not assume state from prior conversation turns. Verify and record the empirical baseline before modifying code:

| Metric / Check | Command Executed | Baseline Result (Before Edits) |
| :--- | :--- | :--- |
| **Active Branch Status** | `git status --short` | [Clean / Untracked files noted] |
| **Target Test Suite** | `[e.g. npm test -- --run]` | [e.g. 42 passed, 0 failed] |
| **Linter / Verification** | `[e.g. ./scripts/verify.sh]` | [e.g. 0 errors] |

---

## 3. Deliverables & Verification Protocol

### Deliverables (In Sequence)

1. **Deliverable 1:** [File / module to create or edit]
2. **Deliverable 2:** [Automated tests covering invariants and boundary conditions]

### Verification Commands

```bash
# Verification commands to execute before delivering the closing report:

[e.g. ./scripts/verify_implementation.sh]
[e.g. python3 ~/Repos/artifice/scripts/sabotage_check.py run --cases tests/sabotage_cases.json]
```

---

## 4. Governance & Repository Constraints

* **Git Operations Boundary:**
  * **Personal Life Vaults (`~/Repos/arete`):** **NEVER** run `git commit` or autonomously commit changes. Leave all modified files in the working directory (staged or unstaged) for human review.
  * **Engineering Repositories (`AretePX/*`):** Commit atomically to dedicated feature branches (`agent/*` or `<handle>/*`). Pushing directly to `main` is strictly prohibited.
* **Markdown Cleanliness:** Leave an empty blank line immediately beneath every heading.
* **Language & Localisation:** 100% **British English** across all code, comments, commit messages, and documentation.
* **Narrative Sovereignty:** Zero autonomous lore invention. Place any worldbuilding ambiguities into Section 3 of the closing report.
* **Token & Scarcity Hygiene:** Maintain complete engineering rigour and testing depth. Do not compromise verification for brevity.

---

## 5. Required Closing Report (`<NNN>_<ID>_report.md`)

The subagent must conclude execution by delivering a structured report with four mandatory sections:

1. **Delivered & Placar:** Concise summary of changes, commit hashes (if applicable), and test pass/fail counts.
2. **Autonomous Decisions & Rationale:** Minor technical choices made, why alternatives were discarded, and how to inspect them.
3. **Open Human Blockers:** Any subjective decisions, 2FA/login gates, or narrative lore questions formatted with full context, recommendation, trade-offs, and defaults.
4. **Proposed Lessons (`Trigger -> Conduct -> Suggested Home`):** Candidate operational learnings evaluated against the 4-Test Acceptance Gate.
