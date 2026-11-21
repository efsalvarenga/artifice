## Description

<!-- What does this PR do and why? Reference the driving issue (e.g. `Fixes #N`). -->

## Design-Review

<!-- Path to the governing design doc, e.g. `docs/designs/008_vibe_shrink_review_gh_posting.md`. Required for design-backed changes; Stage 9 readiness provenance is advisory (issue #31). -->

## Implementation Checklist

<!-- One `- [ ]` per step of the design doc's implementation plan. Generate with: python3 scripts/pr_checklist.py <design.md> — paste the output here. Tick as steps land; reviewers run `python3 scripts/pr_checklist.py <design.md> --check <this PR body>` to flag missing/extra items. -->

## Verification

- [ ] `./scripts/lint.sh` exit 0
- [ ] `python3 scripts/validate_provenance.py --repo . --range <base>..HEAD` PASS
