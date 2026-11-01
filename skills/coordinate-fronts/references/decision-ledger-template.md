# Decision Ledger: [Wave Name or Active Sprint]

**Document ID:** `docs/decisions/pending-decisions.md` (or active canvas linked from `TASKS.md`)  
**Last Updated:** `[YYYY-MM-DD HH:MM]`  
**Status:** Living Document  

> [!NOTE]
> This document centralises all open decisions, developer actions, and reversible coordinator rulings.
> **Active-Only Hygiene:** When an item is resolved, ratified, or mooted, it is immediately moved to `docs/decisions/archive/` (or the repository's `## Archived Rulings`) so this file reflects only current blockers.

---

## 0. Opening Roster (*Pauta de Abertura*)

*Complete these items in Step 0 before launching unattended autonomous execution:*

- [ ] **[OAuth / Credential Gate]** [e.g. Ensure local Google Calendar / Drive plugin is signed in]
- [ ] **[Human Approval Gate]** [e.g. Authorisation to create PR #12 or merge branch X]
- [ ] **[Design Parameter]** [e.g. Confirm primary palette: monochrome ink vs CRT phosphor]

---

## 1. Open Human Decisions (`D01`, `D02`...)

*Items requiring human authority, subjective judgment, or Narrative Sovereignty decisions.*

### D01: [Decision Title in Plain Language]

* **Full Context:** [1–2 paragraphs detailing the background, what the subagent discovered on disk, and what technical fork was reached.]
* **Recommended Choice & Rationale:** [Clear recommendation with empirical justification. Include exact numbers whenever citing measurements.]
* **Trade-Offs & Alternative Options:**
  * *Option A (Recommended):* [Benefits and accepted consequences]
  * *Option B:* [Why this alternative was discarded or deprioritised]
* **Programmed Verification:** [If proposing an experiment: what metric is measured, control baseline, runner script, and target date or sample size `n`.]
* **Default if Unanswered:** [Explicit fallback behaviour if autonomous execution proceeds.]
* **Response:** ___

---

## 2. Actions for Developer (`P01`, `P02`...)

*Commands to execute, 2FA confirmations, external portal logins, or qualitative playtests.*

### P01: [Action Title]

* **Objective:** [What this action achieves]
* **Ready-to-Run Command / Step:**
  ```bash
  [Command or instructions to run]
  ```
* **Expected Outcome:** [What the developer should observe upon execution]
* **Status:** `Pending Developer Action`

---

## 3. Coordinator Reversible Decisions (`C01`, `C02`...)

*Technical choices made autonomously by the coordinator to preserve flow where no genuine product trade-off existed and Narrative Sovereignty was not breached.*

### C01: [Decision Title]

* **Context & Choice:** [1–2 paragraphs detailing the situation, the chosen implementation, and why it is the natural path.]
* **Trade-Off & Impact:** [What was gained, what technical constraints apply, and what was deprioritised.]
* **Revert Instruction:** [Single-line revert phrase, e.g. `"Revert C01: switch to separate subfolder"`.]
* **Status:** `Active (Reversible upon review)`
