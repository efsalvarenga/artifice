# Design Specification: Shared Governance & Commit Provenance

**Document ID:** `docs/designs/005_shared_governance_and_commit_provenance.md`  
**Status:** Approved  
**Author:** Developer & current Copilot assistant; exact model identifier unavailable  
**Target Milestone:** Shared governance and provenance delivery for issues #23 and #19  
**Workshop Date:** 2026-11-13  
**Technical Approval:** Explicit developer sign-off on 2026-11-13  
**Implementation Authorisation:** Granted by the developer on 2026-11-14 for code and automated tests only  

---

## 1. Overview & Objectives

Establish one version-controlled, cross-project governance policy that Antigravity and Copilot actually load, and provide explicit validation of agent-generated Git commit provenance.

The developer approved the workshop canvas, the resolution edits and this final technical specification. This sign-off authorises approval-record synchronisation only, not implementation, installation, commits, pushes or PR creation.

On 2026-11-14, the developer separately authorised implementation using Occam's Razor and independent subagent review where possible. Live installation, commits, pushes and PR creation remain unauthorised.

### Empirical Starting Point

* [Issue #23](https://github.com/efsalvarenga/artifice/issues/23) requests migration of local governance and portable configuration. The [Antigravity installer](../../scripts/install_antigravity.sh) already installs agents, skills, and discovery configuration, but not global rules. The [Copilot installer](../../scripts/install_copilot.sh) also omits global instructions.
* [Issue #19](https://github.com/efsalvarenga/artifice/issues/19) records missing provenance in a consuming repository despite attribution instructions already existing in [code-author](../../agents/code-author/agent.md). Making those instructions globally discoverable addresses the observed coverage gap.
* The expected original global rule files are absent on this machine. The approved approach is to reconstruct a compact baseline from current Artifice guidance, not claim a faithful migration of unavailable files or all ten historical rules.
* The clean checkout at `3153868` passed twelve targeted installer/global-governance tests during the workshop. The preceding full verification of that same commit passed static linting and 94 tests.

### Goals

* Own shared constraints in one compact Markdown file, installed through live symlinks rather than generated or copied policies.
* Support Antigravity and the Copilot harness, including its documented CLI and VS Code user-instruction locations.
* Extend existing non-overwriting installers to register and check the policy.
* Require truthful model, agent-role, and co-author attribution for authorised agent-generated commits.
* Provide an explicitly invoked validator for pending commit messages and selected commits or ranges.
* Keep detailed procedures in agents and skills, with deterministic checks preferred over additional defensive prose.

### Non-Goals

* Backup scripts, MCP templates, sidecars, or a full personal-configuration migration. These remain deferred work under #23 or explicitly split follow-ups; this delivery must not close #23 as wholly complete.
* Reconstructing absent Launchd, narrative-domain, or machine-specific policies without an available source or a separately agreed addition.
* Automatic Git hooks, Git configuration changes, message rewriting, provenance injection, historical rewriting, or automatic scanning of all history.
* New packaging, policy compilation, model-provider integrations, or local/hosted model offloading.
* Fixing the separate EGM approval-validator issue #18 or treating an existing validator result as human approval.
* Claiming support for arbitrary SDK host applications or legacy VS Code harnesses solely because the Copilot harness supports these paths.

### Alternatives & Retained Costs

| Decision | Alternative | Selection reason | Retained cost |
| --- | --- | --- | --- |
| One canonical policy with live symlinks | Managed copies in each client's native directory | Keep one editable policy and avoid copy drift or a synchronisation/build step | The checkout must remain available at the linked location; shared edits affect every consumer, and clients may require a fresh session |
| Compact globally loaded constraints | Keep shared rules only in individual agent personas | Address the recorded cross-repository coverage gap without duplicating complete workflows | Global instructions consume context and may conflict with repository guidance; keep them small and respect active permissions |
| Explicit message/history validator | Install commit hooks or automatic provenance injection | Make scope visible and preserve existing Git configuration, human commits and truthful attribution | The validator can be skipped; it checks structure only and cannot attest contributor identity |

Conflicting personal instruction files require manual review and migration. Automatic merging or copying of those files would change personal policy ownership and is outside this delivery.

---

## 2. Domain Framing & User/System Experience

An engineer clones Artifice and runs the existing installer for each client they want to configure. The installer reports the existing agent/skill registrations and the new global-policy registration. A conflicting personal instruction file stops that installer before writes, with guidance to review and migrate it manually.

After a successful install, editing the canonical policy changes the bytes visible through both client links without a build or reinstall. A fresh client session may still be necessary for the runtime to reload instructions.

Before an authorised agent-generated commit, the agent prepares a commit message and explicitly validates it. The validator reports missing or malformed trailers rather than inserting values or guessing an identity. A developer can also audit a deliberately selected commit or bounded range.

The global policy does not grant Git permissions, override active client/repository instructions, or define a new instruction-precedence engine. Applicable instructions are combined by the clients; contradictory permissions must be resolved rather than assuming this policy wins.

### Native Loading Evidence

* [Antigravity global rules](https://antigravity.google/docs/rules.md) support `~/.gemini/config/AGENTS.md` as continuously active plain Markdown without frontmatter.
* [Copilot CLI instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions) support `~/.copilot/copilot-instructions.md`, with `COPILOT_HOME` relocating that user directory.
* The [VS Code custom-instructions reference](https://code.visualstudio.com/docs/agents/reference/custom-instructions-reference) documents the same personal file for the Copilot harness. Legacy Local-profile instructions and arbitrary SDK host configuration are different integration contracts.

Filesystem registration and documented discovery support are not proof that a particular running client included or followed the policy. Fresh-session verification remains an explicit acceptance step.

---

## 3. State Schema & Data Models

### Canonical Policy & Installation Mapping

The proposed canonical resource is `rules/global-agents.md`, a regular readable Markdown file owned by Artifice. It requires no client-specific frontmatter or include expansion.

| Resource | Destination | Logical link target |
| --- | --- | --- |
| Shared resource anchor | `$HOME/.local/share/artifice` | Physical Artifice checkout |
| Antigravity global policy | `${GEMINI_HOME:-$HOME/.gemini}/config/AGENTS.md` | Anchor plus `/rules/global-agents.md` |
| Copilot global policy | `${COPILOT_HOME:-$HOME/.copilot}/copilot-instructions.md` | Anchor plus `/rules/global-agents.md` |

Preserve the existing installer environment overrides and physical-path validation. An override relocates installer destinations; runtime support is a separate claim governed by the acceptance matrix in section 7. A valid link directly to the same physical canonical file is equivalent to the anchor-based link, consistent with existing installer behaviour.

| Destination state | Meaning | Required result |
| --- | --- | --- |
| Missing | Neither a filesystem entry nor a dangling link exists | Install may create the link after all preflight checks; `--check` fails without writes |
| Correct link | Resolves to the readable canonical file | Leave unchanged; installation and `--check` succeed |
| Conflict | Regular file, directory, different link, broken link, or otherwise invalid target | Report the conflict; abort before writes |

A regular destination file is a conflict even when its bytes match the policy. The installer must not implicitly adopt, replace, back up, or repair personal instructions.

### Global Policy Boundary

The policy contains concise constraints, not copies of full workflows:

| Concern | Required boundary |
| --- | --- |
| Instructions and authority | Respect active permissions and repository instructions; do not manufacture a universal client precedence order |
| Workspace stewardship | Confirm the target and preserve pre-existing user changes; avoid destructive or unrelated actions |
| Git operations | Commit/push only when authorised; preserve the existing human-only merge boundary |
| Approval | When EGM is active, distinguish workshop approval, specification approval, and implementation permission |
| Verification | Use existing native checks; report failures and incomplete verification accurately |
| Privacy and models | Respect protected-content boundaries, approved execution scope, and actual model identity; never silently substitute |
| Commit provenance | Apply the shared trailer contract to authorised agent-generated commits, regardless of which agent persona performed them |
| Writing conventions | Retain existing British English and Markdown-cleanliness conventions subject to applicable instructions |

Detailed EGM, TDD, review, model-selection, and teardown procedures remain in their current agents and skills. The canonical policy must fit the existing global Core Diet ceilings: at most 140 lines and 1,400 words.

### Provenance Trailer Contract

Required fields must be genuine Git trailers, not incidental text in the message body or an unexpanded template:

| Trailer | Cardinality | Value contract |
| --- | --- | --- |
| `Model-Author` | Exactly one | Non-empty exact identifier from available runtime/execution evidence, or the literal `unavailable` when the client does not expose it |
| `Agent-Role` | Exactly one | Non-empty actual contributing role; do not label every agent `code-author` |
| `Co-authored-by` | One or more | GitHub-compatible `Name <email>` entries for legitimate contributing identities whose details are known |

`unavailable` is an explicit limitation, not permission to guess a model from its behaviour or invent a name, handle, or email address. A known client identity may provide truthful co-authorship when its underlying model identifier is unavailable. If no legitimate co-author identity is available, stop before committing and request one rather than generating a surrogate.

Additional trailers remain permitted. Apply the following fixed acceptance profile to Git's parsed trailing metadata; do not search the message body for keywords.

| Rule | Acceptance contract |
| --- | --- |
| Parsing | Use input-only Git trailer parsing with `:` as the separator and continuation unfolding. Do not insert, rewrite, alias or synthesise entries. Repository, user and system `trailer.*` settings must not change the result or execute configured commands. |
| Required keys | Compare the exact names `Model-Author`, `Agent-Role` and `Co-authored-by` case-insensitively using ASCII case folding. Alternate spelling, aliases and `=` separators do not satisfy a required field. |
| Required values | After Git unfolds continuations, trim outer ASCII spaces and tabs. Reject empty values, remaining line breaks and ASCII control characters. Preserve other content; do not infer identity from a value's wording. |
| Singleton fields | Require exactly one `Model-Author` and exactly one `Agent-Role`, including occurrences with different key casing. Two identical singleton values are still invalid. |
| Co-author repetition | Require at least one valid `Co-authored-by`. Multiple entries, including identical repeats, are permitted; repeats do not establish additional distinct contributors. Every entry must satisfy the same structural checks. |
| Unknown model | The documented unavailable-model marker is the literal lowercase `unavailable`. Other structurally valid values are identity claims, not proof that the model exists or participated. |
| Co-author shape | Each entry contains one non-empty display name followed by one ASCII address in angle brackets, separated by at least one space. No text may follow the closing bracket. The name may be Unicode but must not contain angle brackets or ASCII control characters. |
| Template tokens | Reject only the reserved token forms defined below. Ordinary names, roles or model identifiers are not rejected merely because they resemble an example. |

The supported address subset is an unquoted ASCII address with exactly one `@`. Its local part consists of non-empty dot-separated atoms of ASCII letters, digits and the punctuation ``!#$%&'*+-/=?^_`{|}~``. Its domain consists of non-empty dot-separated labels with alphanumeric first and last characters and optional interior hyphens. Quoted local parts, address lists, IP-literal domains and non-ASCII addresses are outside this subset. These checks do not verify delivery or GitHub account ownership.

Reserved template tokens are `${IDENTIFIER}` and `{{IDENTIFIER}}`, where `IDENTIFIER` matches `[A-Za-z_][A-Za-z0-9_]*`, and uppercase angle-bracket tokens matching `<[A-Z][A-Z0-9_]*>`. Reject these tokens anywhere in a required value, including a co-author display name. No other word-shaped example is inferred to be a placeholder. Structurally valid fabricated identities remain prohibited by the attribution policy, even when their fabrication cannot be detected by the validator.

The validator verifies structure and the explicit unavailable-marker convention. It cannot attest that a stated model or contributor actually participated; truthful attribution remains an agent/developer responsibility.

### Explicit Validator Interface

The proposed entry point is `scripts/validate_provenance.py`, using the standard library and existing Git executable:

```text
python3 "$ARTIFICE_ROOT/scripts/validate_provenance.py" --message-file PATH
python3 "$ARTIFICE_ROOT/scripts/validate_provenance.py" --repo PATH --commit REV
python3 "$ARTIFICE_ROOT/scripts/validate_provenance.py" --repo PATH --range BASE..HEAD
```

* Select exactly one input mode. History modes require an explicit repository path; there is no implicit current-repository or all-history scan.
* `--commit` resolves exactly one commit. `--range` requires two explicit commit endpoints with two-dot range semantics and validates every selected commit, including merges.
* The caller selects the audit scope. There is no heuristic for distinguishing human and agent authorship, and no silently exempted commit inside that scope.
* An empty selected range is an error, not a successful audit.
* Exit `0` means every selected message satisfies the structural contract. Exit `1` reports invalid provenance, unreadable input, failed Git resolution, or an empty selection. Exit `2` reports invalid CLI usage.
* Diagnostics identify the message file or commit and the failed field/operation. Do not silently skip failed inputs, repair messages, or print an all-valid result after a failure.

---

## 4. Invariants & Rules

1. **One policy owner:** Both client destinations resolve to the same canonical resource; there is no generated client copy or second normative trailer schema.
2. **No implied authority:** Installing guidance or passing a validator never authorises commits, pushes, merges, installation elsewhere, or implementation of an unapproved specification.
3. **Preflight before writes:** Missing sources, invalid containment/parents, and destination conflicts are detected before that installer creates any new entry.
4. **No overwrite:** Existing personal files, directories, mismatched links, and unrelated configuration remain untouched.
5. **Read-only checking:** `--check`, provenance validation, and history auditing do not change instruction files, Git history, Git configuration, hooks, the index, or the worktree.
6. **Exact scope:** Only the explicitly selected message, commit, or range is audited. All selected messages must pass; unrelated history is not inspected.
7. **Truth before completeness claims:** Missing model evidence uses `unavailable`; missing legitimate co-author identity blocks committing. Structural validation must not be presented as identity attestation.
8. **Observable failures:** Invalid input and operational failures produce actionable diagnostics and non-zero status; there is no inferred identity or success-shaped fallback.
9. **Live iteration:** Policy changes are visible through installed links without compilation or reinstall, subject to client session reload behaviour.
10. **Human handoff:** This draft remains `Under Review` until explicit technical sign-off. Workshop approval, formatting checks, and an EGM validator exit code are not substitutes.

---

## 5. Execution & State Mutation Logic

### Installer Integration

1. Extend each existing installer's source and destination inventory with the canonical policy and native client file destination.
2. Apply existing path-containment and source/parent validation to the new file registration. File links must be checked as files rather than attempting to resolve them by changing into a directory.
3. Classify every existing and new registration before writes. Conflicts report the affected path and explain that personal content must be reviewed and moved manually before retrying.
4. In check mode, report actual state and exit without creating directories or links. In install mode, create only missing registrations once the complete preflight succeeds. If a destination appears after preflight, creation must fail without following, writing through or overwriting that entry. Report the conflict and preserve it. Newly created registrations from earlier operations may remain, as described by the existing runtime-failure rule.
5. Preserve existing agent, skill, anchor, discovery-configuration, argument, and environment-override behaviour. Installing clients in either order must remain idempotent.
6. Runtime I/O failures remain explicit failures. Do not promise transactional rollback after a later filesystem error; preserve pre-existing data and let a subsequent `--check` report actual state.

No live installation is authorised by this draft. Automated verification uses disposable homes rather than the engineer's real client directories.

### Provenance Validation

1. Validate input-mode arguments before reading messages or repository data.
2. For a message file, read that exact file. For history, resolve the explicit repository and revisions using read-only Git operations; report resolution errors.
3. Use the fixed Git parsing and acceptance profile from section 3; validate all required occurrences, singleton cardinality, co-author structure and the defined reserved template tokens.
4. Report each selected invalid message with its identifier. Return success only when the non-empty selection is wholly valid.

The authoring workflow invokes the checker on a prepared message before an authorised commit. An after-the-fact audit is a separate explicit operation, not a reason to commit first and repair history later.

### Shared Guidance & Documentation

* Make the canonical policy the normative provenance contract referenced by [code-author](../../agents/code-author/agent.md) and [spec-egm](../../skills/spec-egm/SKILL.md), resolving resources through the existing canonical `ARTIFICE_ROOT` rules.
* Remove conflicting or duplicated runtime trailer instructions rather than appending another competing schema. Preserve the role-specific TDD workflow and existing prompt budgets.
* Update the [README](../../README.md) with the policy resource, client paths, safe migration behaviour, validator modes, unavailable-model convention, limitations, and fresh-session verification.
* Keep historical approved designs/reviews intact. This design changes the future runtime contract, not the recorded history of earlier approvals.

### Canonical Policy Linting & Compatibility

Repository verification must check the tracked policy using the existing Markdown checks and exact global Core Diet ceilings, without requiring an installed personal copy. Resolve the canonical resource from the physical Artifice checkout, not a consuming repository's working directory; portable linting must not require every consuming repository to contain a `rules/` directory.

Retain `GLOBAL_AGENTS_PATH` for an explicitly selected external-policy check, without letting it bypass canonical-policy validation. Installed link state belongs to installer `--check`; the default canonical check must not depend on an absent personal file.

Intentional compatibility changes requiring technical sign-off are:

* Global attribution now applies to all authorised agent-generated commits, not only sessions that loaded `code-author`.
* Exact model identity may explicitly be `unavailable`; fabricated identity examples are not instructions to generate fictional contributors.
* Canonical-policy linting becomes mandatory even when no personal global rule file exists. Preserve the environment override's documented purpose and report an explicitly requested unreadable file as an error.
* Existing personal instruction files remain conflicts, not candidates for automatic conversion.

---

## 6. Edge Cases & Failure Modes

| Case | Required handling |
| --- | --- |
| Original global rules unavailable | Use only the agreed reconstructed baseline; do not invent missing historical policy or claim faithful migration |
| Policy source missing/unreadable or destination resolves to a directory | Fail source/type validation; never report a correct policy link |
| Existing personal policy, even byte-identical | Conflict with manual-migration guidance; no writes to any registration in that installer |
| Broken or mismatched destination link | Conflict, not implicit repair |
| Correct direct-checkout link, alias parent, or paths with spaces | Recognise physical equivalence within existing path-safety rules; preserve idempotence |
| Failure after successful preflight | Surface the runtime error without success/rollback claims; never overwrite pre-existing content |
| Model identity unavailable | Permit the exact marker with truthful role and legitimate co-authorship |
| Required field missing/blank, duplicate singleton, invalid co-author, reserved template token, or body-only provenance | Reject with field-specific diagnostics; multiple valid co-author entries remain permitted |
| Unknown revision, non-commit object, invalid repository, or empty range | Reject explicitly; do not substitute `HEAD` or inspect a wider range |
| Selected range contains a human-authored commit | Validate it like every selected message; the caller must choose a narrower scope rather than relying on authorship guessing |
| Fresh client does not show the policy | Report discovery/inclusion as unverified or failed; do not infer loading from the symlink alone |
| EGM validator returns success while approval is absent | Keep implementation blocked on explicit human sign-off; do not fix or conceal #18 inside this work |

---

## 7. Verification & Automated Test Strategy

### Installer Contract Tests

Extend the existing standard-library black-box tests with disposable homes and client-root overrides:

* Fresh installation, read-only missing-state check, repeat installation, and successful post-install checks for both clients.
* Both installation orders, same canonical target, correct file contents, and immediate visibility of a temporary fixture policy change without reinstall.
* Existing regular files, byte-identical files, directories, mismatched links, and dangling links: non-zero status, migration diagnostics, preserved content, and no partial writes on preflight conflict.
* Missing/unreadable policy sources, file-versus-directory errors, valid equivalent file links, alias parents, containment failures, and paths with spaces.
* Existing agent/skill/discovery registrations, CLI errors, and environment overrides retain their intended behaviour. Tests must not mutate the real checkout's policy to demonstrate live updates.
* Introduce a file or directory at a planned destination after preflight but before link creation. Assert non-zero status, preserved content, no writes inside that destination and no success report.
* Fail a later filesystem operation after an earlier missing registration has been created. Assert non-zero status, preserved pre-existing content, no rollback claim, and a subsequent read-only `--check` that identifies the actual partial installation state.

### Provenance Contract Tests

Use synthetic messages and disposable Git repositories, never the developer's history:

* Valid known-model and explicit-`unavailable` messages; actual roles other than `code-author`; multiple legitimate-format co-authors and additional trailers.
* Each missing/blank required field and body-only provenance examples fail.
* Two distinct co-authors and repeated identical valid co-authors pass. Duplicate singleton fields fail, including duplicates whose key casing differs.
* Required keys with case variants pass; aliases, alternate spelling and `=` separators do not satisfy them.
* Valid single-line values and Git-folded values pass after the defined unfolding and outer trim; empty or control-bearing normalised values fail.
* Test the documented simple co-author address subset, including a plus-tagged local part and Unicode display name. Reject missing names, malformed brackets, trailing text, address lists and unsupported address forms.
* Each reserved template-token form fails in required values. An ordinary non-empty identifier is not rejected because it resembles an example; structural acceptance is not identity verification.
* Repository, user, system and environment-supplied trailer configuration must not alter acceptance, add values, hide duplicates or execute configured trailer commands. Use isolated fixtures; never change the developer's Git configuration.
* Genuine trailing metadata is recognised according to Git conventions rather than keyword presence.
* Each explicit input mode returns the documented status and identifies failing inputs. A range succeeds only when every selected message passes.
* Empty ranges, invalid/non-commit revisions, unreadable message files, missing repositories, missing modes, and conflicting modes fail without broader scans or guessed defaults.
* Validation leaves messages, configuration, hooks, the index, worktree, and commit history unchanged. Fixture identities are test data, not attribution claims.

### Policy & Consumer Verification

* Verify canonical policy limits at exactly 140/141 lines and 1,400/1,401 words, Markdown cleanliness, and resolvable canonical resource links.
* Prove canonical lint works without installed global files and when targeting a consuming repository. Test the preserved explicit `GLOBAL_AGENTS_PATH` interface and its failure reporting.
* Verify runtime consumers reference one normative provenance contract and remain inside their existing Core Diet ceilings.
* Run the focused tests first, then `./scripts/lint.sh .` before implementation handoff is considered complete. No new third-party dependencies are required.

### Fresh-Client Acceptance

After separate installation approval, verify the following runtime targets in fresh sessions. A supported target is an acceptance requirement, not a claim that verification has already passed.

| Client surface | Effective policy path | Support classification | Required before a delivery claim |
| --- | --- | --- | --- |
| Antigravity, with the tested product surface recorded | `$HOME/.gemini/config/AGENTS.md` | Supported target; runtime acceptance pending | Passing native inclusion evidence for the recorded surface/version |
| Copilot CLI, default home | `$HOME/.copilot/copilot-instructions.md` | Supported target; runtime acceptance pending | Passing native inclusion evidence |
| VS Code Copilot harness, default home | `$HOME/.copilot/copilot-instructions.md` | Supported target; runtime acceptance pending | Passing native inclusion evidence for the recorded harness/profile |
| Copilot CLI, explicit `COPILOT_HOME` | `$COPILOT_HOME/copilot-instructions.md` | Documented relocated target; runtime acceptance pending | Passing inclusion evidence from a process started with the explicit override |
| Antigravity, explicit `GEMINI_HOME` | `$GEMINI_HOME/config/AGENTS.md` | Installer-test-only; runtime relocation unclaimed | Isolated installer tests; no runtime support claim |
| VS Code Copilot harness, explicit `COPILOT_HOME` | `$COPILOT_HOME/copilot-instructions.md` | Installer-test-only; runtime relocation unclaimed | Isolated installer tests; no runtime support claim |

For each runtime target, record the actual client surface, version, harness/profile where applicable, effective home/override, policy path, fresh-session identifier or capture, and evidence that the canonical policy content was included. Native diagnostics must identify inclusion, not only show that a file exists or was discovered. If available diagnostics cannot establish inclusion, record the result as unverified and keep that row incomplete.

The three default rows and the documented Copilot CLI relocation row must pass before claiming this delivery's client-loading acceptance or proposing closure of #19. A missing client or unavailable installation permission leaves acceptance pending; it is not a reason to substitute a filesystem check or claim success. Evidence from one Antigravity surface, version or Copilot harness must not be generalised to untested products or SDK hosts.

Where separately authorised, a non-sensitive task can request a draft commit message without repeating the policy or creating a commit. Inspect its provenance and run the explicit validator. Record discovery, inclusion, and observed behaviour separately; instructions are guidance, not a guarantee of compliance.

### Delivery & Approval Boundary

Execution stays with the current assistant in the inherited workspace, without model offloading. No implementation tests, production files, real installations, commits, pushes, or PR creation are authorised by drafting this document.

Issue #19 may be proposed for closure only after the shared guidance, explicit validation and all four required runtime-acceptance rows are delivered with passing evidence. Issue #23 remains partial until the deferred audit/migration is delivered or transparently split into tracked follow-ups.

---

## 8. Goldfish Review Gates

- [x] Front-loaded workshop canvas explicitly approved for specification drafting only
- [x] Zero-context Goldfish review completed and recorded without fabricated review provenance
- [x] Logic contradictions and edge-case holes addressed
- [x] Human developer approves this technical specification and intentional compatibility changes
- [x] Human developer explicitly authorises implementation

The current [Review 005](../reviews/005_shared_governance_and_commit_provenance_review.md) records `Verdict: Approved` after two consecutive clean review-loop rounds. Its [initial audit snapshot](../reviews/005_shared_governance_and_commit_provenance_review.md#initial-audit-snapshot) preserves the earlier `Revisions Required` report verbatim. Human technical sign-off and the later implementation authorisation are recorded above; live installation and Git operations still require separate permission.
