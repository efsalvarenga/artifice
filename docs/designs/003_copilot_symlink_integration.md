# Design Specification: Copilot Symlink Integration

**Document ID:** `docs/designs/003_copilot_symlink_integration.md`
**Status:** Approved
**Revision:** 2026-11-04 lean preflight edition
**Author:** Copilot SDK assistant, Gemini 4 Argon & Developer

## 1. Overview & Objectives

Register Artifice's three canonical roles (`code-author`, `code-reviewer`, `developer-coach`) and four shared skills (`spec-egm`, `review`, `coach-frameworks`, `local-code`) in GitHub Copilot through three personal directory symlinks and thin Copilot adapters, without duplicating canonical prompts or breaking Antigravity workflows.

Non-goals: third-party dependencies, generated file copies, client settings mutation, or automatic conflict overwriting.

## 2. Domain Framing & User/System Experience

Canonical files in `agents/` and `skills/` preserve structured domain instructions and resolve `ARTIFICE_ROOT` in order: explicit `ARTIFICE_ROOT`, `$HOME/.local/share/artifice` when present, or `$HOME/Repos/artifice`. Client-specific tool allowlists and Copilot session caveats stay isolated inside `integrations/copilot/agents/*.agent.md`. On-device `--local` mode keeps protected code and diffs out of cloud context with no cloud fallback.

## 3. State Schema & Data Models

| Field | Contract |
| --- | --- |
| Checkout root | Physical repository directory resolved from `scripts/install_copilot.sh`. |
| `HOME` / `COPILOT_HOME` | Normalised absolute paths; `COPILOT_HOME` defaults to `$HOME/.copilot`. |
| Symlinks | `$HOME/.local/share/artifice` -> checkout; `<COPILOT_HOME>/agents` -> `<anchor>/integrations/copilot/agents`; `<COPILOT_HOME>/skills` -> `<anchor>/skills`. |
| Link states | `missing`, `correct-link` (matching literal or resolved physical target), or `conflict` (existing file, real directory, or mismatched/broken link). |
| Copilot adapters | Single-line `name`, non-empty `description`, inline `tools` (`code-author`: `read, search, edit, execute, agent`; `code-reviewer`: `read, search, execute, agent`; `developer-coach`: `read, search, edit, execute, web`), no `model:` lock, and canonical `agents/<role>/agent.md` target. |
| Ollama overrides | `ARTIFICE_CODE_MODEL` (`code/logic/fim/tdd`) and `ARTIFICE_PROSE_MODEL` (`prose/docs/adr/architecture`) require exact installed tags (`exit 0`), failing (`exit 2`, `fallback: null`) when empty, uninstalled, or offline; unset defaults fall back to `qwen2.5-coder:14b` / `qwen2.5:14b` and `mistral-nemo`. |

## 4. Invariants & Rules

* Maintain a single canonical workflow per role and skill; aggregate canonical prompt budget stays within `<= 4,158` words (`<= 900` words per agent, `<= 1,000` words and `<= 180` lines per skill).
* Validate `HOME`, `COPILOT_HOME`, source files, parent path components, and all three destination link states upfront before creating directories or symlinks.
* Never overwrite or delete existing files, real directories, or unrelated/broken symlinks; `--check` performs zero filesystem writes.
* Model selection via `check_ollama.py select --task` governs warming, inference, and truthful provenance consistently without silent substitution.

## 5. Execution & State Mutation Logic

1. Parse CLI mode (`install` with no flags, `--check`, or `--help`; invalid options exit `2`).
2. Validate `$HOME`, `$COPILOT_HOME` (rejecting relative paths, `..` segments, checkout/anchor nesting, and non-directory parent components), and verify readable canonical sources.
3. Classify all three destinations (`missing`, `correct-link`, `conflict`). Exit `1` with zero writes if any source is missing, any destination is `conflict`, or `--check` encounters `missing`; exit `0` if `--check` finds all links complete.
4. Create missing parent directories (`mkdir -p`) and missing symlinks (`ln -s`) in anchor, agents, skills order.

## 6. Edge Cases & Failure Modes

* Spaces in `$HOME` or `$COPILOT_HOME`, existing regular files at parent paths (e.g. `~/.copilot`), broken symlinks, or moved checkouts fail cleanly in preflight with exit `1` and zero mutations.
* Empty or uninstalled `ARTIFICE_CODE_MODEL` / `ARTIFICE_PROSE_MODEL` values fail with `exit 2` and `fallback: null` while ignoring unrelated task overrides.

## 7. Verification & Automated Test Strategy

* [`scripts/lint.sh`](../../scripts/lint.sh) runs [`scripts/lint.py`](../../scripts/lint.py) (Markdown cleanliness, YAML/adapter frontmatter, relative links, Core Diet word/line ceilings, EGM contracts, and `bash -n` syntax) followed by standard-library `unittest` discovery.
* [`tests/test_artifice.py`](../../tests/test_artifice.py) verifies disposable-home installer lifecycles (`--help`, invalid arguments/paths, `--check`, install, idempotence, conflict/bad-parent refusal), mocked `check_ollama.py` selection/override contracts, and `lint.py` adapter/diet/syntax gates without touching personal directories or loading Ollama models.
