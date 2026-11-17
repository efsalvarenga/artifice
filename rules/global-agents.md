# Shared Cross-Project Governance

These constraints complement active client and repository instructions. They do not grant permissions or establish a universal precedence order. Report unresolved conflicts instead of assuming this policy overrides another authority.

## Workspace & Scope

Confirm the target repository and inspect its existing state before editing. Preserve unrelated user changes. Make complete, narrowly scoped changes; do not perform destructive operations or rewrite history without explicit permission.

Prefer native runtime facilities and existing helpers. Remove speculative abstractions, duplicate workflows and unnecessary files. Keep detailed EGM, TDD, review and model-execution procedures in their existing agents and skills.

## Approval & Git

When EGM is active, distinguish workshop alignment, technical specification approval and implementation authorisation. Neither a review verdict nor a passing validator replaces human permission.

Follow active permissions for commits, pushes and PR creation. Merging remains human-only. Do not install hooks or change Git configuration automatically.

## Verification

Use the repository's existing checks, starting with those covering the change. Verify the required behaviour, not a proxy. Report failures, skipped checks and incomplete acceptance explicitly; do not claim a green baseline or completed delivery without evidence.

## Models & Privacy

Use only authorised execution modes and actual model identities. Respect protected-content and workspace boundaries before sending inputs or outputs to another engine. Never silently substitute a model or fall back to hosted execution.

## Commit Provenance

Every authorised agent-generated commit must contain genuine Git trailers:

* Exactly one `Model-Author`: the actual identifier supported by execution evidence, or the literal `unavailable` if the client does not expose it.
* Exactly one `Agent-Role`: the actual role that performed the work, not automatically `code-author`.
* One or more `Co-authored-by` entries using known, legitimate contributor names and email addresses. Repeated entries are permitted but do not establish additional distinct contributors.

Never invent model names, handles or email addresses. A known client identity may be credited when its model identifier is unavailable. If no legitimate co-author identity is known, stop before committing and request one.

Prepare the message and explicitly run the [provenance validator](../scripts/validate_provenance.py) before an authorised commit. Its mechanical acceptance checks do not prove identity or participation. A failed check blocks that commit; never repair history automatically or bypass the failure.

Audit history only through an explicitly chosen commit or range. Do not scan all history by default or guess which commits were human-authored to exempt them.

## Canonical Resources

Resolve `ARTIFICE_ROOT` from its explicit value, otherwise `$HOME/.local/share/artifice` when present, otherwise `$HOME/Repos/artifice`. Verify readable `agents`, `skills` and `scripts` directories before invoking shared tooling. Resolve this policy's links from the physical `ARTIFICE_ROOT/rules/` directory, not the client's symlink address; report missing resources rather than using a generic fallback.

## Writing

Use British English and follow existing repository conventions subject to active instructions. Follow every Markdown heading with a blank line. Keep shared guidance compact; enforce mechanical requirements in code rather than duplicating defensive prose.
