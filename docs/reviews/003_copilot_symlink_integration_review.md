# Goldfish Review: Copilot Symlink Integration

**Review Target:** [003_copilot_symlink_integration.md](../designs/003_copilot_symlink_integration.md)
**Revision:** 2026-11-04 lean preflight edition
**Reviewer:** Independent code-reviewer Goldfish audit & Occam's Razor consolidation
**Date:** 2026-11-04
**Verdict:** Approved

## 1. Executive Summary

The Copilot symlink integration contract was approved after resolving `COPILOT_HOME` path normalisation, task-isolated `ARTIFICE_CODE_MODEL` / `ARTIFICE_PROSE_MODEL` selection semantics, Antigravity `--local` on-device pipeline compatibility, and Occam's Razor simplification of the installer, adapter linter, and test suite.

## 2. Invariant & Edge-Case Verification

| Area | Resolution | Status |
| --- | --- | --- |
| Upfront preflight safety | `install_copilot.sh` validates `HOME`, `COPILOT_HOME`, parent directories, required sources, and all three link states before any `mkdir -p` or `ln -s` call, eliminating bespoke rollback state machines. | Verified |
| Canonical prompt diet | Canonical roles and skills retain `main`'s structured domain instructions at `4,128` words (`-1` vs `main`'s `4,129` words), keeping Copilot caveats inside `integrations/copilot/agents/*.agent.md`. | Verified |
| Dynamic model overrides | `check_ollama.py select --task` isolates `code` and `prose` overrides, rejects empty/uninstalled tags (`exit 2`, `fallback: null`), and preserves default fallbacks. | Verified |
| Governance & tests | `lint.py` validates adapter metadata/targets, word/line ceilings, and `bash -n` syntax; `tests/test_artifice.py` executes automatically inside `./scripts/lint.sh`. | Verified |

## 3. Residual Live Acceptance Scope

Static governance and disposable-home tests verify filesystem registration, conflict refusal, and selection contracts, while live Copilot UI picker discovery and fresh-session reload behaviour remain interactive client checks.
