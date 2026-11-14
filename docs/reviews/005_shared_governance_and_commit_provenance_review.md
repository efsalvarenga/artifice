# Goldfish Review: Shared Governance & Commit Provenance

**Review Target:** [Specification 005](../designs/005_shared_governance_and_commit_provenance.md)  
**Reviewers:** Fresh `design_critic` and `structural` contexts in each of two rounds  
**Consolidation:** Current Copilot assistant; no model identifier claimed  
**Date:** 2026-11-13  
**Verdict:** Approved  
**Reviewed Revision SHA-256:** `ab02c0d679968f11c1ede22bc347b0df27ed5f89cfb55d9f21f08251bfc03c64`  
**Technical Content SHA-256:** `0a9f40e6c34684df596721b12032e1af2aa681d5e2a22ae8ec08941494f852dd`  

---

## 1. Executive Summary

The revised specification passed the requested feature-design and structural review loop after two consecutive clean rounds. All four fresh reviewer contexts completed with zero Blocker, Major or Nit findings. Both reviewers in both rounds assessed the initial R1-R4 findings as addressed in the revised text.

The developer then explicitly approved the technical specification and synchronising its EGM approval records. That permission does not authorise implementation, installation, commits, pushes or a PR.

The initial audit requested revisions. Its complete report is preserved below as a historical snapshot rather than relabelled as an approved first review.

### Review Provenance & Scope

* Four distinct fresh contexts applied the `design_critic` and `structural` personas against the feature-spec standard, two reviewers per round.
* The sole domain background was the explicitly approved original audit. Reviewers received no Elephant conversation, resolution proposal history or prior-round reviewer results.
* Each reviewer read the complete revised specification. Both rounds used the same pinned revision; parent checks confirmed that source inputs were unchanged throughout the loop.
* Review coverage was document-only. No implementation, external documentation, Git history, runtime client sessions or executable behaviour was inspected.
* Approval-record updates were applied only after explicit developer sign-off. The technical content from `### Empirical Starting Point` through the section before the Goldfish gates is unchanged; its fingerprint above excludes approval metadata and gate updates.
* This is not a claim that the initial five-rubric protocol was rerun as five independently isolated stages, or that a full implementation-plan or code audit occurred.

## 2. Invariant & Edge-Case Probing

| Initial finding | Current assessment | Revised specification evidence |
| --- | --- | --- |
| R1: Trailer acceptance | Addressed by both reviewers in both rounds | [Provenance contract](../designs/005_shared_governance_and_commit_provenance.md#provenance-trailer-contract): fixed parsing profile, key comparison, cardinality, co-author repetition, address subset, bounded placeholders and aligned tests |
| R2: Alternatives | Addressed by both reviewers in both rounds | [Alternatives and retained costs](../designs/005_shared_governance_and_commit_provenance.md#alternatives--retained-costs): concrete choice reasons and retained costs |
| R3: Write-time failures | Addressed by both reviewers in both rounds | [Installer integration](../designs/005_shared_governance_and_commit_provenance.md#installer-integration) and [contract tests](../designs/005_shared_governance_and_commit_provenance.md#installer-contract-tests): concurrent destination appearance and partial runtime failure |
| R4: Runtime loading evidence | Addressed by both reviewers in both rounds | [Fresh-client acceptance](../designs/005_shared_governance_and_commit_provenance.md#fresh-client-acceptance): supported targets, installer-only overrides, inclusion evidence and the four required passing rows |

These outcomes concern specified contracts and tests, not completed implementation or actual client-loading evidence.

## 3. Detailed Critiques & Blind Spots

### Completed Review Coverage

| Round | Reviewer | Status | Blocker | Major | Nit |
| --- | --- | --- | --- | --- | --- |
| 1 | `design_critic` | completed | 0 | 0 | 0 |
| 1 | `structural` | completed | 0 | 0 | 0 |
| 2 | `design_critic` | completed | 0 | 0 | 0 |
| 2 | `structural` | completed | 0 | 0 | 0 |

No current findings require textual repair. There were no failed reviewers, accepted risks or contested findings counted towards convergence.

### Remaining Evidence Limits

Native loading descriptions and earlier test counts were statements in the specification, not independently revalidated during these audits. Runtime acceptance remains pending separate installation permission and verification. A green implementation baseline, code correspondence and model/contributor identity cannot be certified by this review.

## 4. Required Revisions

None for the reviewed technical specification. The initial R1-R4 requests were resolved before the loop and independently assessed as addressed in both clean rounds.

Further technical changes require their own appropriate review. Human technical approval and a passing document validator do not grant implementation authority.

## 5. Recommendation & Sign-Off

* **Verdict:** Approved for the reviewed feature-design and structural scope.
* **Convergence:** Two consecutive clean rounds; four requested reviewers completed; zero open findings.
* **Human technical approval:** Explicitly granted on 2026-11-13, including the intentional compatibility changes and approval-record synchronisation.
* **Implementation authorisation:** Not granted. No authoring agent may be released from this record alone.
* **History:** The initial audit and its `Revisions Required` verdict are preserved verbatim below.

### Initial Audit Snapshot

This complete initial report is historical evidence, not the current review verdict. Its original UTF-8 snapshot SHA-256 is `cc4754e43bbd971d4f6cb5bb726b35dd8da02dc3c9c9d27a77999a62180d8221`.

````markdown
# Goldfish Review: Shared Governance & Commit Provenance

**Review Target:** [Specification 005](../designs/005_shared_governance_and_commit_provenance.md)  
**Reviewer:** Goldfish Reviewer Agent (one fresh context; no model identifier claimed)  
**Date:** 2026-11-13  
**Verdict:** Revisions Required

---

## 1. Executive Summary

The provenance checker does not yet have a sufficiently precise acceptance contract: its duplicate-field wording conflicts, and rejecting unspecified template values can require judgements that a structural checker cannot make. The central architectural choices also lack the alternatives evaluation required by the supplied review standard. These are approval blockers, numbered R1 and R2 below.

The basic separation is proportionate to the stated problem: one policy resource, non-overwriting registration, and an explicitly invoked checker rather than automatic Git changes. The specification distinguishes filesystem registration from client inclusion and structural validation from truthful attribution. Two non-blocking recommendations strengthen verification of those boundaries.

### Review provenance and scope

* Subject inputs were the complete specification, lines 1–268, and the supplied repository Goldfish template. The permitted root `AGENTS.md` was absent.
* Method definitions were the loaded `spec-egm` workflow, the user-supplied `egm-review/SKILL.md`, its applicable reviewer personas, and the zoom-out, feature-spec and implementation-readiness document standards. They supplied review criteria, not project evidence.
* No parent history, conversations, earlier agent results, implementation, README, other designs or reviews, issues, URLs, or Git history were consulted. Specification links were not followed. No nested agents or other inference engines were used.
* All five rubric groups were considered in this one fresh reviewer context. This is not a claim of five independently isolated reviewers or full staged execution. No intermediate reports were created.
* **Semantic scope:** `FeatureRange = 1..268`; `DetailedRange = N/A`. Section 5 describes execution contracts, but there is no separate phased implementation plan. Readiness is assessed only against the interfaces, invariants and verification requirements present here. Code correspondence, reuse, exact implementation boundaries and executable phasing remain unassessed.
* No tests, linting, installations or client sessions were run. Existing behaviour, external loading documentation and historical test counts are statements in the specification, not independently verified evidence.

### What this proposes

Introduce one tracked Markdown policy and install live links to it for Antigravity and Copilot. Require model, role and co-author trailers on authorised agent-generated commits, with an explicit Python-and-Git checker for prepared messages or deliberately selected history. Neither the policy nor the checker grants permissions, inserts attribution or proves contributor identity.

### How the existing system works, per this document

The existing installers register agents, skills and discovery configuration, but omit global instructions. Attribution guidance already exists in `code-author`, yet did not cover a reported consuming-repository case. Existing path-safety rules and linting are to be reused, while unavailable original policies will be replaced by an explicitly reconstructed baseline rather than represented as faithfully migrated.

### Rubric coverage

| Rubric group | Assessment and traceability |
| --- | --- |
| Initial zoom-out, including inventive contradiction review | The stated root problems and delivery boundaries are understandable. No false compromise detected in the basic architecture; no additional architectural machinery is justified. Selection trade-offs remain undocumented: R2. |
| Self-contained comprehension | The proposal can be paraphrased without linked background. Exact trailer acceptance and client-relocation support cannot be fully determined from the text: R1 and R4. |
| Design, structure and style critique | R1 concerns observable validation behaviour; R2 concerns the mandatory alternatives rule. The heading hierarchy and prose are readable. Authority caveats identify concrete operator decisions and need not be removed as redundant disclaimers. |
| Final zoom-out | The findings do not justify adding hooks, policy compilation, automatic repair or transactional installation. Resolve the contract and evidence gaps without expanding the architecture: R1–R4. |
| Bounded implementation readiness | R1 leaves acceptance decisions to an implementer. R3 and R4 identify test and acceptance refinements. A full plan audit and codebase-details verification are outside the permitted evidence. |

---

## 2. Invariant & Edge-Case Probing

Severity describes impact; blocking status identifies what prevents specification approval. Confidence concerns the documented gap, not an inferred implementation defect.

| ID | Area / Component | Potential Failure Mode / Ambiguity | Risk Severity |
| :--- | :--- | :--- | :--- |
| R1 | Provenance acceptance | Multiple co-authors are allowed, but blanket duplicate-field rejection can reject them. Template rejection and parts of the lexical contract lack a bounded acceptance rule. | High; blocking; high confidence |
| R2 | Architectural choices | Scope exclusions select live links and explicit checking without the alternatives evaluation required by the review standard. | Med; blocking under the supplied standard; high confidence |
| R3 | Installation state changes | Tests cover preflight conflicts but do not explicitly exercise a destination appearing afterwards or a later write failure with partial new state. | Med; non-blocking test gap; high confidence |
| R4 | Native client acceptance | Installer overrides are not distinguished from supported runtime relocation, and acceptance lacks a per-client support and evidence matrix. | Med; non-blocking acceptance gap; high confidence |

Already specified, rather than newly missing: byte-identical personal files remain conflicts; check mode is read-only; partial installation after an I/O failure does not imply rollback; every selected commit is checked regardless of apparent authorship; empty ranges fail; missing identity must not be fabricated.

---

## 3. Detailed Critiques & Blind Spots

### 3.1 Data Schema Completeness

#### R1 — Complete the deterministic trailer acceptance contract

**Severity:** High — blocking.  
**Confidence:** High.  
**Specification anchors:** §3, lines 105–117; §5, lines 168–171; §6, line 208; §7, lines 232–236.

There are two related contract problems:

1. Lines 111 and 115 permit multiple `Co-authored-by` fields and reject duplicate **singleton** fields. Line 208 instead says a duplicated required field is rejected, without that qualification. Line 233 returns to singleton-only rejection. A literal reading can therefore reject a valid multi-co-author message. The treatment of an identical co-author entry repeated twice is also unstated.
2. The checker must reject “unsubstituted example/template values”, but no recognisable placeholder syntax or reserved values are defined. A word-shaped example can also be a genuine identifier or role. Determining which was intended would cross the structural-only boundary at line 117. The co-author requirement gives the outline `Name <email>`, but not the accepted structural subset. The text also leaves key normalisation, folded values and the treatment of ambient Git trailer configuration implicit.

Git parsing should be reused, not replaced with substring detection. That still leaves a need to state which parsed keys and values satisfy this policy. Otherwise independently written validators and tests can disagree while each claims to implement the prose.

**Smallest required clarification:** Add a compact acceptance table defining key comparison, singleton and co-author duplication, value/folding rules, the supported co-author shape, and syntactically recognisable placeholder forms. Qualify line 208 as duplicate singleton rejection. State whether ambient trailer configuration affects parsing, or fix the parsing profile. Keep participation, actual model identity and contributor legitimacy outside the structural check.

**Acceptance additions:** Include two distinct co-authors; repeated identical co-authors; singleton duplicates with key-case variants; accepted and rejected co-author shapes; recognised placeholder forms versus ordinary non-empty identifiers; and the documented handling of folded values and alternate trailer configuration. These are proposed tests, not completed checks.

### 3.2 State Mutation & Deterministic Consistency

#### R2 — Record the alternatives and retained trade-offs

**Severity:** Med — blocking under the supplied feature-spec standard.  
**Confidence:** High.  
**Specification anchors:** §1, lines 24–39; §3, lines 68–84; §5, lines 173–186.

The supplied feature-spec standard explicitly requires an evaluation of viable alternatives and concrete reasons for rejecting them. The specification selects live symlinks, globally discoverable guidance and an opt-in checker. It excludes copies, compilation and hooks, but does not explain the central choices against alternatives. An exclusion is a scope decision, not by itself a trade-off evaluation.

The reconstruction decision does have a reason: the originals are unavailable, as stated at lines 21 and 201. This finding concerns the remaining architectural choices, not an assertion that the document contains no rationale anywhere.

**Smallest required clarification:** Add a brief alternatives table for the central choices. Relevant comparisons include live links versus managed native copies, global guidance versus retaining persona-only guidance, and explicit checking versus hooks. State the selection reason and retained cost for each choice. Costs to acknowledge include dependence on the linked checkout, policy edits becoming visible across consumers, manual conflict migration, and validation occurring only when invoked.

The chosen architecture may remain unchanged. No prototype, new dependency or additional feature is required to close this finding.

#### R3 — Exercise write-time conflicts and partial runtime failure

**Severity:** Med — non-blocking verification recommendation.  
**Confidence:** High.  
**Specification anchors:** §4, lines 142–144; §5, lines 159–162; §6, line 206; §7, lines 222–226.

The no-overwrite invariant and runtime-failure outcome are already stated. The test list explicitly covers conflicts present during preflight, but not a destination appearing between preflight and creation, or a later creation failing after earlier missing registrations have been added.

This is a coverage gap, not evidence that an existing installer overwrites data. It does not justify requiring rollback where line 162 deliberately declines to promise it.

**Recommended change:** Add deterministic fixtures for both transitions:

* Introduce a conflicting destination after preflight. Assert that its content survives, installation fails and no success is reported.
* Fail a later filesystem operation after an earlier registration succeeds. Assert non-zero status, preserved pre-existing content, no rollback claim, and a subsequent `--check` that reports the actual partial state.

These assertions implement the existing invariants; they do not prescribe a locking mechanism or transactional installer.

### 3.3 Testability & Verification Strategy

#### R4 — Define the client-loading acceptance matrix

**Severity:** Med — non-blocking acceptance recommendation.  
**Confidence:** High for the missing matrix; runtime compatibility remains unverified.  
**Specification anchors:** §2, lines 56–60; §3, lines 73–76; §6, line 211; §7, lines 246–256.

The installation mapping uses `GEMINI_HOME` and `COPILOT_HOME`. The native-loading discussion explicitly describes relocation for the Copilot CLI, but does not distinguish installer/test overrides from supported runtime relocation for every client surface. Fresh-client acceptance names Antigravity, Copilot CLI and the VS Code Copilot harness without specifying which default and relocated combinations are claimed.

The document appropriately separates discovery, inclusion and observed behaviour. It does not define the minimum evidence or pass gate for each supported combination. Recording a symlink, an unverified result or a failed discovery attempt must not become a claim that the policy actually loaded.

This is not a claim that any client ignores an override or that a linked documentation statement is false. Those claims would require evidence outside this review.

**Recommended change:** Add a small matrix covering the three client surfaces, default locations and each claimed relocation. Mark combinations as supported, unsupported or installer-test-only. For supported combinations, identify the effective path, relevant client version/profile, required native inclusion evidence and pass/fail outcome. Make the required passing rows explicit for client-loading claims and the issue #19 closure gate.

Execution may still wait for separate installation permission. The optional draft-message behaviour check at line 250 need not become mandatory or be represented as proof of universal instruction compliance.

---

## 4. Required Revisions

The following changes block specification approval:

1. **R1 — Define trailer acceptance without identity guessing.** Reconcile duplicate-field wording; bound placeholder rejection; specify the remaining lexical and parser-profile decisions; add corresponding positive and negative test cases.
2. **R2 — Add the mandatory alternatives evaluation.** Document selection reasons and retained costs for the central policy-distribution and validation choices. No architectural expansion is required.

R3 and R4 are non-blocking recommendations to strengthen the verification contract. They should be considered when preparing implementation tests and client acceptance, rather than mistaken for observed implementation failures.

---

## 5. Recommendation & Sign-Off

* **Verdict:** Revisions Required.
* **Notes for Elephant Agent:** Resolve R1 and R2 in the specification and request review of the revised text. Keep the existing authority boundaries and structural-versus-truth distinction. Do not add identity inference, automatic Git enforcement or transactional installation merely to answer these findings.
* **Readiness boundary:** The feature contracts can be reviewed here; a phased implementation plan, file-change allowlist, code correspondence, actual compatibility and executed verification cannot be certified from the permitted inputs. The absence of a separate plan is recorded as a limitation, not invented into an additional blocker.
* **Sign-off limitation:** This report supplies a design verdict only. It asserts no human approval, implementation permission, installation permission, completed tests, commits or client-loading evidence.
````
