---
name: coordinate-fronts
version: 1.1.0
description: >-
  Orchestrates multi-front task batches, milestone waves, and autonomous goal
  runs: front-loaded opening alignment, in-memory pilot block dispatch, independent disk
  audits, native UI decision resolution, cross-block seam checks, and closing code reviews.
argument-hint: "[plan | status | audit <block_id>]"
---

# Multi-Front Wave Coordination Skill (`coordinate-fronts`)

This skill coordinates multi-task execution waves, complex milestones, and unattended autonomous batches. When 3+ independent tasks stack up or an autonomous wave begins, it activates the **Coordinator Protocol**: the coordinator plans, dispatches in-memory task prompts, independently audits disk state, and resolves decisions via native Antigravity channels, while ephemeral subagents execute blocks.

## Step-by-Step Coordination Procedure

### Step 1: Pre-Flight Reconnaissance & Upfront Alignment

1. **60-Second Empirical Disk Recon:**
   Execute fast read-only checks on git status, active branch, test baselines, and file counts. Never copy unverified claims or counts from prior chat turns into block specifications.
2. **Precedent Search Before Asking:**
   Before querying the developer, search `AGENTS.md`, `docs/designs/`, and `git log -S` for existing precedents.
3. **Upfront Alignment Gate:**
   Identify every requirement demanding physical human presence (plugin/OAuth credentials, git branch authorisation, qualitative design choices). Resolve them up front before launching autonomous execution.

### Step 2: Formulate In-Memory Subagent Prompts & Pilot-First Dispatch

1. **Direct In-Memory Scoping:**
   Do NOT write markdown contract files to disk. Pass scope, file boundaries, verification commands, and repository-specific git constraints directly into `invoke_subagent` via its `Prompt` argument:
   * **Explicit Scope & Verification:** State exact deliverables, target test command, and git constraints (`arete` strictly unstaged; engineering repos atomic feature branches).
   * **Quota Hygiene:** Do not include scarcity or token-saving phrasing inside subagent prompts.
2. **Pilot Block Execution:**
   When running a homogeneous wave or a new workflow pattern, launch **Block 1 as a Pilot** via `invoke_subagent`. Audit it completely before releasing Blocks $2 \dots N$, resolving shared tool/spec friction once.
3. **Batch Dispatch:**
   Dispatch remaining blocks. Disjoint file sets run concurrently (up to 3 parallel subagents); overlapping modules run sequentially.

### Step 3: Independent Coordinator Disk Audit (*"Autorrelato Não Se Aceita"*)

Subagent self-reports are never accepted on trust alone. Upon receiving a completion report, the coordinator independently verifies:

1. `git status --short` & `git diff --stat`: Confirm zero untracked debris and strict adherence to git constraints (zero commits in `arete`).
2. `git log -1`: Validate commit message and author trailers (where commits are permitted).
3. **Independent Test Execution:** Run the project's verification command directly or inspect fresh timestamped logs.
4. **Modification Timestamps (`mtime`):** Verify only expected files were modified and external databases remain unpolluted.
5. **Daemons & Processes:** Verify modified services have fresh PIDs and healthy response codes.
6. **Report Archival:** Append any corrections as errata rather than silently rewriting subagent history.

### Step 4: Resolve Decisions via Native Antigravity Channels

Do NOT create file-based markdown decision ledgers on disk. Handle decisions and blockers through Antigravity's native interaction channels:

1. **Interactive Choices (`ask_question`):** When human judgment is required, present structured options using the `ask_question` tool with a recommended answer first.
2. **Direct Chat Clarifications:** Clarify minor ambiguities directly in chat.
3. **Autonomous Technical Choices:** For low-stakes engineering choices, proceed autonomously, document the rationale in the turn summary, and provide a 1-line revert command.

### Step 5: Cross-Block Seam Check & Closing Code Review

1. **Pairwise Seam Audit:**
   Identify any module touched by $\ge 2$ blocks. Inspect the composition of changes to ensure one block did not invalidate another's invariant.
2. **Mandatory Review Gate:**
   Invoke the **Principal Code Reviewer ("The Gatekeeper")** via [`review-pr`](../review-pr/SKILL.md) across the cumulative wave diff before presenting final results to the developer.
