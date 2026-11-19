# Pull request checklist

- [ ] Changelog entry added under `## [Unreleased]` in `CHANGELOG.md` (Keep a Changelog categories: Added / Changed / Fixed).
- [ ] Provenance trailers present (`Model-Author`, `Agent-Role`, `Co-authored-by`) and `python3 scripts/validate_provenance.py --message-file <message-file>` exits 0.
- [ ] `./scripts/lint.sh` exits 0.
- [ ] Merger only: move `## [Unreleased]` to `## [vX.Y.Z] - <date>` in `CHANGELOG.md` and create the annotated tag `vX.Y.Z` at merge time. The version bumps on every merge to `main`.
