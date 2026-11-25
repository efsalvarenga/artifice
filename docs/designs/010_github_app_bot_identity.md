# Design 010: Dedicated GitHub App Bot Identity for Agent Commits and PRs

**Author:** efsalvarenga  
**Status:** Approved (efsalvarenga, 2026-11-25 — human sign-off per https://github.com/efsalvarenga/artifice/issues/63; single-pass zero-context review applied)  
**Date:** 2026-11-25  
**Tracking issue:** [efsalvarenga/artifice#63](https://github.com/efsalvarenga/artifice/issues/63)

--------------------------------------------------------------------------------

## Overview

Separate local agent Git commits, pushes, and GitHub CLI (`gh`) operations from the human account (`efsalvarenga`) using a dedicated **GitHub App** (`<app-slug>[bot]`). One zero-dependency Python helper (`scripts/github_app_auth.py`) and a thin `gh` wrapper (`scripts/gh-bot`) mint short-lived (1-hour) installation tokens automatically from a local `.pem` private key, supply HTTPS credentials to `git`, and inject bot commit identity without altering the human's default `gh` session or global Git configuration.

## Goals

* **Human/agent isolation:** Agent commits, branches, PRs, and review comments appear under `<app-slug>[bot]`, enabling independent GitHub PR review, approval, and merging under `efsalvarenga`.
* **Zero third-party dependencies:** Pure Python 3 standard library plus the system `openssl` CLI (no `pip` packages or `jq` required).
* **Always-on bot authorship across harnesses:** Once configured, agents in `agy`, `omp`, and Copilot always author commits, pushes, and PR operations through the bot identity (enforced via [global-agents.md](../../rules/global-agents.md) and optional worktree `includeIf` config). Default profile `default` serves a single shared GitHub App across harnesses, with optional `--profile <name>` / `ARTIFICE_GH_APP_PROFILE` and per-owner `installations` mapping (e.g. `efsalvarenga`, `terra-campaigns`, `AretePX`) for multi-org or future per-role Apps.
* **Automatic runtime auth, non-invasive human defaults:** After one-time App setup, JWT signing, token minting, caching, refresh, and Git/CLI credential injection happen automatically on every agent command, while never modifying `~/.config/gh/hosts.yml`, global `~/.gitconfig`, or repository `.git/config` automatically (per [global-agents.md](../../rules/global-agents.md#approval--git)).
* **Provenance compatibility:** Bot Git author/committer headers work cleanly alongside required provenance trailers validated by [validate_provenance.py](../../scripts/validate_provenance.py).

## Non-Goals

* No automatic GitHub App registration, `.pem` key generation, or silent mutation of `~/.gitconfig` / `.git/config` (one-time setup is explicit and human-run; runtime token minting and bot authentication are automatic once configured).
* No bot-side PR approval or merging (`gh pr merge` remains strictly human-only).
* No weakening of `ADDRESS` validation in [validate_provenance.py](../../scripts/validate_provenance.py); `Co-authored-by:` continues to credit human contributors while the bot occupies Git `AUTHOR`/`COMMITTER`.
* No per-request `--repo` token narrowing (installation scope already enforces least-privilege repository access).
* No changes to canonical agent/skill Markdown bodies in this issue (Core Diet 6-file word budget stays unchanged; shared agent usage guidance lives in [global-agents.md](../../rules/global-agents.md)).

--------------------------------------------------------------------------------

## Technical Plan

### Configuration & File Layout

All secrets and profile configs live outside any Git repository under `${XDG_CONFIG_HOME:-$HOME/.config}/artifice/` (overridable via `ARTIFICE_GH_APP_CONFIG_DIR` or `ARTIFICE_GH_APP_CONFIG`):

```text
~/.config/artifice/
├── github-app.pem                # chmod 600; private key downloaded from GitHub
└── github-apps/
    └── default.json              # named profile ("default" unless overridden)
```

Profile JSON schema and strict validation:

```json
{
  "app_id": "123456",
  "app_slug": "artifice-agent",
  "bot_user_id": "234567890",
  "installation_id": "98765432",
  "installations": {
    "efsalvarenga": "98765432",
    "terra-campaigns": "11223344",
    "AretePX": "55667788"
  },
  "private_key_path": "~/.config/artifice/github-app.pem"
}
```

* **Validation:** profile name `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`; `app_id`, `bot_user_id`, `installation_id`, and all `installations` values `^\d+$`; `app_slug` `^[A-Za-z0-9-]+$`.
* **Precedence:** CLI flags (`--config`, `--profile`, `--owner`) > environment variables (`ARTIFICE_GH_APP_CONFIG`, `ARTIFICE_GH_APP_PROFILE`, `ARTIFICE_GH_APP_CONFIG_DIR`, `ARTIFICE_GH_APP_OWNER`) > defaults (`default` profile under XDG config dir). When `--config` / `ARTIFICE_GH_APP_CONFIG` is set, it loads that file directly instead of looking up `github-apps/<profile>.json`.
* **Owner resolution:** explicit `--owner` / `ARTIFICE_GH_APP_OWNER` > owner parsed from `git-credential` `path` or `gh` `-R`/`--repo` > current repo's `origin` HTTPS remote owner (when `installations` is configured) > top-level `installation_id` fallback.
* **Token cache:** `${XDG_RUNTIME_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}}/artifice/gh-app-tokens/<app_id>-<installation_id>.json`. Keying by numeric `app_id` and `installation_id` prevents cross-profile/config collisions. Cached tokens are reused only when at least 300 seconds remain before `expires_at` (parsed via `strptime("%Y-%m-%dT%H:%M:%SZ")` in UTC).

### JWT Minting & Token Exchange

1. Build RS256 JWT header `{"alg":"RS256","typ":"JWT"}` and payload `{"iat": now - 60, "exp": now + 480, "iss": app_id}` (540 s window, inside GitHub's 600 s hard cap) using URL-safe Base64 without padding.
2. Open the validated `.pem` file descriptor with `O_RDONLY | O_NOFOLLOW` and sign `<header>.<payload>` via `openssl dgst -sha256 -sign /dev/fd/<fd> -binary -passin pass:` (`pass_fds=(fd,)`, `shell=False`, 15 s timeout, no temporary key files).
3. Exchange the JWT via HTTPS `POST https://api.github.com/app/installations/<installation_id>/access_tokens` (`urllib.request`, 15 s timeout, redirects disabled via custom `HTTPRedirectHandler` so `Authorization` headers cannot leak, explicit `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, and `User-Agent: artifice-github-app-auth`).

### CLI Surface (`scripts/github_app_auth.py` & `scripts/gh-bot`)

| Subcommand | Behaviour |
| --- | --- |
| `token [--config C] [--profile P] [--owner O] [--no-cache]` | Prints a valid installation token to stdout. |
| `git-credential [--config C] [--profile P] <get\|store\|erase>` | Implements Git's `credential.helper` protocol for `protocol=https` and `host.lower()=="github.com"`. On `get`, extracts owner from `path` (stripping leading `/`), mints/fetches token, and prints `username=x-access-token` and `password=<token>`. On `erase`, unlinks the matching cache file (so revoked tokens do not linger). Non-GitHub hosts and `store` exit 0 with no output. |
| `git-env [--config C] [--profile P]` | Emits `shlex.quote`-escaped `export` lines for `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, and `GIT_COMMITTER_EMAIL` (`<app-slug>[bot]` and `<bot-user-id>+<app-slug>[bot]@users.noreply.github.com`). |
| `exec [--config C] [--profile P] [--owner O] [--with-gh-token\|--no-gh-token] [--no-git-credential] -- <cmd> [args...]` | Runs `<cmd>` with bot `GIT_AUTHOR_*`/`GIT_COMMITTER_*` and appended `GIT_CONFIG_*` entries (Git >= 2.31; preserves existing `GIT_CONFIG_COUNT`) setting `credential.https://github.com.useHttpPath=true`, clearing inherited `credential.https://github.com.helper`, and setting it to `'!' + shlex.join([sys.executable, resolved_script, 'git-credential', ...])`. Mints `GH_TOKEN` only when `--with-gh-token` is passed or `Path(cmd[0]).name == "gh"` (keeping local `git commit` offline and hooks free of live tokens), and fails closed if `GH_HOST` is set to a non-`github.com` host. |
| `check [--config C] [--profile P] [--owner O] [--live]` | Validates config schema, `.pem` invariants, `openssl` availability, and bot identity format; warns if `bot_user_id == app_id` or if the current repo's `origin` uses SSH. With `--live`, exchanges a token and verifies `GET /users/<app-slug>[bot]` matches `bot_user_id` (never prints the token). |

`scripts/gh-bot` is a thin Bash wrapper that resolves its own physical directory (safe when symlinked into `~/.local/bin`) and runs `exec python3 "$SCRIPT_DIR/github_app_auth.py" exec --with-gh-token -- gh "$@"`, leaving the human's default `gh` auth untouched.

### Security Invariants

1. **Private key mode, ownership, and location (TOCTOU-safe):** Open `.pem` with `O_RDONLY | O_NOFOLLOW` (rejects symlinks), `fstat` to verify regular file, `st_uid == os.geteuid()`, and `(mode & 0o077) == 0`; reject passphrase-protected (`ENCRYPTED`) keys; walk ancestors of both lexical and resolved parent paths using `os.path.lexists` for `.git` (catches both normal checkouts and Git worktrees where `.git` is a file) and refuse keys inside any Git repo. Pass `/dev/fd/<fd>` via `pass_fds` to `openssl`.
2. **No secret leakage:** Neither the private key, JWT, nor installation token may appear in stderr errors, `check` output, or child process argv. Reject `\r`/`\n` in any emitted `git-credential` or `git-env` value.
3. **Host scoping:** `git-credential` responds only to `protocol=https` and `host.lower() == "github.com"`; `exec` fails closed on non-`github.com` `GH_HOST` when minting `GH_TOKEN`.
4. **Safe cache I/O:** Verify cache directory is not a symlink, is owned by `euid`, and has mode `0700`. Read cache via `O_RDONLY | O_NOFOLLOW` + `fstat` (`S_ISREG`, `euid`, `(mode & 0o077) == 0`). Write via sibling temp file (`O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW`, `0600`) + `os.replace()`.
5. **Dedicated worktree / standalone opt-in:** `docs/github_app_bot_setup.md` documents zero-config per-command `exec` (recommended for all shared checkouts and linked worktrees), opt-in `extensions.worktreeConfig` + `git config --worktree` (for dedicated linked worktrees) or `git config --local` (standalone clones only), and HTTPS remote requirements.

--------------------------------------------------------------------------------

## Risks & Mitigations

| Risk | Mitigation |
| --- | --- |
| `.pem` committed, symlinked, or world-readable | `O_NOFOLLOW` + `fstat` (`euid`, `0600`) + `lexists(".git")` ancestor walk + `/dev/fd/<fd>` signing. |
| Repo-local `credential.helper` hijacks human pushes in shared checkouts | `exec` scopes credentials per command via `GIT_CONFIG_*`; setup guide limits persistent config to dedicated agent worktrees. |
| Local `git commit` triggers network or leaks `GH_TOKEN` to hooks | `exec` skips `GH_TOKEN` unless `--with-gh-token` or command is `gh`; `git push` mints lazily via `git-credential`. |
| Revoked token lingers in cache for up to 55 min | `git-credential erase` unlinks the matching cache file on Git 401/403. |
| `scripts/gh-bot` skipped by `lint.py` Bash check | Extend `scripts/lint.py:check_bash_syntax()` to also lint extensionless Bash-shebang scripts under `scripts/`. |
| `[bot]` email format fails `validate_provenance.py` | Bot sits in Git `AUTHOR`/`COMMITTER` headers; `Co-authored-by:` credits human contributors. Verified by unit test (positive + negative assertions). |

--------------------------------------------------------------------------------

## Detailed Implementation Plan

1. `docs/designs/010_github_app_bot_identity.md` — **[Create]** this design specification.
2. `scripts/github_app_auth.py` — **[Create]** zero-dependency GitHub App JWT/token minter, safe cache, `git-credential` (`get`/`store`/`erase`), `git-env`, `exec`, and `check` CLI.
3. `scripts/gh-bot` — **[Create]** thin symlink-safe Bash wrapper running `gh` under bot `GH_TOKEN` and Git identity.
4. `docs/github_app_bot_setup.md` — **[Create]** operator setup guide (GitHub App registration, `.pem` & profile config, `exec` vs `includeIf` / repo-local Git config, SSH-to-HTTPS note, and E2E verification steps).
5. `tests/test_github_app_auth.py` — **[Create]** unit and black-box tests covering config/profile schema validation, `.pem` symlink/mode/worktree-`.git`/encrypted guards, RS256 JWT verification via `openssl`, redirect-blocked token exchange, atomic cache reuse/expiry/`erase`, `git-credential`, `git-env`, `exec` (offline git, `GH_HOST` guard, `GIT_CONFIG_COUNT` preservation, spaces in paths), symlinked `gh-bot`, and `check`.
6. `tests/test_provenance.py` — **[Modify]** add synthetic-fixture test verifying a bot-authored Git commit with standard provenance trailers passes `validate_provenance.py`, while `[bot]` inside `Co-authored-by:` remains rejected.
7. `scripts/lint.py` & `tests/test_artifice.py` — **[Modify]** extend `check_bash_syntax()` to lint extensionless Bash-shebang scripts under `scripts/` (covering `scripts/gh-bot`) and add a unit test.
8. `rules/global-agents.md` — **[Modify]** add concise bot-authorship rule so `agy`, `omp`, and Copilot agents always route Git commits/pushes and `gh` commands through the configured GitHub App bot identity.
9. `README.md` — **[Modify]** document `github_app_auth.py`, `gh-bot`, and `docs/github_app_bot_setup.md` in the directory tree and `## Core Scripts & Verification`.

### Verification Plan

* `./scripts/lint.sh` exit 0 (Markdown headings, relative links, Core Diet, Bash syntax including `scripts/gh-bot`, unit tests).
* `python3 -m unittest discover -s tests -p 'test_*.py'` exit 0 (including `tests/test_github_app_auth.py`, `tests/test_provenance.py`, and `tests/test_artifice.py`).
* `python3 scripts/pr_checklist.py docs/designs/010_github_app_bot_identity.md --check <pr-body.md>` exits 0 on PR creation.
* Live E2E verification (operator step once the GitHub App is configured locally): `python3 scripts/github_app_auth.py check --live`, push branch and open PR via bot identity, confirm `<app-slug>[bot]` authorship, then human review/approval/merge by `efsalvarenga`.
