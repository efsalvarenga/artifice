## Description

<!-- What does this PR do and why? Reference the driving issue (e.g. `Fixes #N`). -->

## Design-Review

<!-- Path to the governing design doc, e.g. `docs/designs/008_vibe_shrink_review_gh_posting.md`. Required for design-backed changes (advisory Stage 9 provenance; see issue #31). -->

## Implementation Checklist

<!-- Projected from the design doc's Detailed Implementation Plan — one `- [ ]` per step. Tick as steps land; the reviewer re-generates it from the branch's design doc and flags unticked or missing items. -->

- [ ] <!-- plan step 1 -->

## Verification

- [ ] `./scripts/lint.sh` exit 0
- [ ] `python3 scripts/validate_provenance.py --repo . --range <base>..HEAD` PASS
