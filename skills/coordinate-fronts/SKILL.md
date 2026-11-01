---
name: coordinate-fronts
version: 1.0.0
description: >-
  Orchestrates multi-front task batches, milestone waves, and autonomous goal
  runs: front-loaded opening rosters, pilot block dispatch, independent disk
  audits, unified decision ledgers, cross-block seam checks, and closing code reviews.
argument-hint: "[plan | status | audit <block_id>]"
---

# Multi-Front Wave Coordination Skill (`coordinate-fronts`)

This skill coordinates multi-task execution waves, complex milestones, and unattended autonomous batches. When 3+ independent tasks stack up or an autonomous wave begins, it activates the **Coordinator Protocol**: the coordinator plans, issues disk contracts, audits disk state, and routes decisions, while ephemeral subagents execute blocks.

## Reference Materials

* **Block Contract Template:** [`references/block-contract-template.md`](references/block-contract-template.md)
* **Decision Ledger Template:** [`references/decision-ledger-template.md`](references/decision-ledger-template.md)
* **Decision Ledger Linter:** [`../../scripts/check_decisions.py`](../../scripts/check_decisions.py)

## Step-by-Step Coordination Procedure

### Step 1: Pre-Flight Reconnaissance & Opening Roster (*Pauta de Abertura*)

1. **60-Second Empirical Disk Recon:**
   Execute fast read-only checks on git status, active branch, test baselines, and file counts. Never copy unverified claims or counts from prior chat turns into block specifications.
2. **Precedent Search Before Asking:**
   Before querying the developer, search `AGENTS.md`, `decisions.md`, `docs/designs/`, and `git log -S` for existing precedents.
3. **Assemble the Opening Roster:**
   Isolate every requirement demanding physical human presence (plugin/OAuth credentials, git branch authorisation, qualitative design choices) into Section 0 of the Decision Ledger. Request them in a single batch in Step 0 before autonomous execution begins.

### Step 2: Formulate Block Contracts & Pilot-First Dispatch

1. **Write Block Contracts:**
   Author a concise contract for each front using [`references/block-contract-template.md`](references/block-contract-template.md). Store contracts in `.gemini/antigravity/brain/<id>/` or `docs/waves/`.
   * **Explicit Scope & Verification:** State exact deliverables, verification commands, and repository-specific git boundaries (`arete` strictly unstaged; `AretePX/*` atomic feature branches).
   * **Quota Hygiene:** Do not include scarcity or token-saving phrasing inside subagent prompts.
2. **Pilot Block Execution:**
   When running a homogeneous wave or a new workflow pattern, launch **Block 1 as a Pilot** via `invoke_subagent`. Audit it completely before releasing Blocks $2 \dots N$, resolving shared tool/spec friction once.
3. **Batch Dispatch:**
   Dispatch remaining blocks. Disjoint file sets run concurrently (up to 3 parallel subagents); overlapping modules run sequentially.

### Step 3: Independent Coordinator Disk Audit (*"Autorrelato Não Se Aceita"*)

Subagent self-reports are never accepted on trust alone. Upon receiving a completion report, the coordinator independently verifies:

1. `git status --short` & `git diff --stat`: Confirm zero untracked debris and strict adherence to git constraints (zero commits in `arete`).
2. `git log -1`: Validate commit message and author trailers (where commits are permitted).
3. Independent Test Execution: Run the project's verification command directly or inspect fresh timestamped logs.
4. Modification Timestamps (`mtime`): Verify only expected files were modified and external databases remain unpolluted.
5. Daemons & Processes: Verify modified services have fresh PIDs and healthy response codes.
6. Report Archival: Append any corrections as errata rather than silently rewriting subagent history.

### Step 4: Route Decisions to the Unified Ledger

Update `docs/decisions/pending-decisions.md` (or the canvas linked from `TASKS.md`):

1. **Open `[HUMAN]` Decisions (`D01`, `D02`...):** Context, recommended option, trade-offs, programmed verification, and fallback default. All Narrative Sovereignty decisions route here.
2. **Developer Actions (`P01`, `P02`...):** Ready-to-run commands, credential entries, or qualitative playtests.
3. **Coordinator Reversible Decisions (`C01`, `C02`...):** Obvious technical choices decided autonomously with plain-English rationale and a 1-line revert instruction.
4. **Active-Only Hygiene:** When items are resolved or ratified, move them immediately to `docs/decisions/archive/` and validate with `python3 ~/Repos/artifice/scripts/check_decisions.py`.

### Step 5: Cross-Block Seam Check & Closing Code Review

1. **Pairwise Seam Audit:**
   Identify any module touched by $\ge 2$ blocks. Inspect the composition of changes to ensure one block did not invalidate another's invariant.
2. **Mandatory Review Gate:**
   Invoke the **Principal Code Reviewer ("The Gatekeeper")** via [`review-pr`](../review-pr/SKILL.md) across the cumulative wave diff before presenting final results to the developer.
