# GitHub App Bot Identity Setup

This guide sets up a dedicated GitHub App (`<app-slug>[bot]`) so local coding agents (Antigravity / `agy`, oh-my-pi / `omp`, and GitHub Copilot) commit, push, and open pull requests under a bot identity while human review, approval, and merging stay isolated under your personal GitHub account.

Design specification: [010_github_app_bot_identity.md](designs/010_github_app_bot_identity.md) (issue [#63](https://github.com/efsalvarenga/artifice/issues/63)).

## Prerequisites

* Python 3.8+ (standard library only; no third-party packages).
* `openssl` CLI on `PATH` and POSIX `/dev/fd` support (Linux/macOS).
* Git >= 2.31 (required for `GIT_CONFIG_COUNT` in `exec` and `--worktree` config).
* `gh` CLI (pre-authenticated as your human account for the one-time `bot_user_id` lookup in Step 1).

## 1. Register and Install the GitHub App

1. Open https://github.com/settings/apps/new.
2. Fill in the App details:
   * **GitHub App name:** e.g. `artifice-agent` (globally unique on GitHub).
   * **Homepage URL:** `https://github.com/efsalvarenga/artifice`.
   * **Webhook:** uncheck **Active**.
   * **Repository permissions:** `Contents: Read and write`, `Pull requests: Read and write`, `Issues: Read and write` (`Metadata: Read-only` is added automatically). Leave Organization and Account permissions at `No access`.
   * **Where can this GitHub App be installed?:** select **Any account** if you plan to install the same App on your organisations (e.g. `terra-campaigns`, `AretePX`) as well as your personal account; otherwise select **Only on this account**.
3. Create the App, then:
   * Note the **App ID** and **App slug** (from `https://github.com/apps/<slug>`).
   * Under **Private keys**, click **Generate a private key** and move the `.pem` file outside any repository:

```bash
mkdir -p ~/.config/artifice/github-apps
mv ~/Downloads/<your-app>.private-key.pem ~/.config/artifice/github-app.pem
chmod 600 ~/.config/artifice/github-app.pem
```

4. Click **Install App** in the left sidebar and install on **Only select repositories** for each account or organisation you want to enable. Record each **Installation ID** from the browser URL:
   * Personal account: `https://github.com/settings/installations/<installation-id>`
   * Organisation: `https://github.com/organizations/<org>/settings/installations/<installation-id>`
5. Look up the numeric `<bot-user-id>` for `<app-slug>[bot]`:

```bash
gh api "users/<app-slug>[bot]" --jq .id
```

## 2. Create the Local Profile

Write `~/.config/artifice/github-apps/default.json` (outside any repository). All numeric IDs (`app_id`, `bot_user_id`, `installation_id`, and `installations` values) must be **quoted JSON strings**:

```json
{
  "app_id": "<APP_ID>",
  "app_slug": "<APP_SLUG>",
  "bot_user_id": "<BOT_USER_ID>",
  "installation_id": "<DEFAULT_INSTALLATION_ID>",
  "installations": {
    "efsalvarenga": "<PERSONAL_INSTALLATION_ID>",
    "terra-campaigns": "<TERRA_INSTALLATION_ID>",
    "AretePX": "<ARETEPX_INSTALLATION_ID>"
  },
  "private_key_path": "~/.config/artifice/github-app.pem"
}
```

* `installation_id` is used when `installations` is omitted or no owner is detected. When `installations` is populated, owners are matched case-insensitively and unrecognised owners fail closed (in `git-credential`, unconfigured owners are skipped cleanly so third-party repositories do not receive or evict your token).
* Verify local security invariants and live GitHub authentication (tokens are never printed):

```bash
python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" check --live
```

Additional named profiles (e.g. `~/.config/artifice/github-apps/work.json`) can be selected with `--profile work` on `github_app_auth.py` or via `ARTIFICE_GH_APP_PROFILE=work` (and `ARTIFICE_GH_APP_OWNER=<org>`). Note that `scripts/gh-bot` forwards all CLI flags directly to `gh`, so select non-default profiles/owners for `gh-bot` using environment variables.

## 3. Daily Usage (Human Account Untouched)

### Per-Command Execution (Recommended for All Checkouts & Linked Worktrees)

Your default `git` identity and `~/.config/gh/hosts.yml` remain bound to your human account. Agents route commands through the helper:

```bash
# Offline commit as <app-slug>[bot] (no network call, no GH_TOKEN exposed to hooks)
python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" exec -- git commit -F commit-msg.txt

# HTTPS push using lazily minted 1-hour installation token
python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" exec -- git push -u origin <branch>

# GitHub CLI as <app-slug>[bot] (resolves owner from -R / GH_REPO / origin remote)
"${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/gh-bot" pr create --title "..." --body-file pr.md
```

For an interactive shell session that only needs bot commit author/committer variables, you can export them via:

```bash
eval "$(python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" git-env)"
```

You can optionally symlink `scripts/gh-bot` onto your `PATH`:

```bash
ln -s "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/gh-bot" ~/.local/bin/gh-bot
```

### Optional Persistent Git Config (Dedicated Agent Checkouts Only)

Do **not** use `includeIf "gitdir:..."` for linked worktrees (in Git, `gitdir:` matches the administrative `.git/worktrees/<name>` directory, not the linked checkout path) and do **not** run `git config --local` inside a linked worktree (it writes to the shared main repository's `.git/config` and hijacks human commits/pushes there).

* **Dedicated linked worktree:** enable per-worktree config once, then use `--worktree`:

```bash
HELPER_SCRIPT="${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py"
git config extensions.worktreeConfig true
git config --worktree user.name "<app-slug>[bot]"
git config --worktree user.email "<bot-user-id>+<app-slug>[bot]@users.noreply.github.com"
git config --worktree commit.gpgsign false
git config --worktree credential.https://github.com.useHttpPath true
git config --worktree credential.https://github.com.helper ""
git config --worktree --add credential.https://github.com.helper "!python3 '${HELPER_SCRIPT}' git-credential"
```

* **Dedicated standalone clone (never used for human commits/pushes):** run the same commands with `--local` instead of `--worktree` (skipping `extensions.worktreeConfig`). Note that persistent Git config affects `git` only — always continue using `scripts/gh-bot` for agent `gh` commands.

### HTTPS Remotes Required

GitHub App installation tokens authenticate over HTTPS (`https://github.com/<owner>/<repo>.git`), not SSH. If `origin` uses SSH (`git@github.com:...`), switch it to HTTPS:

```bash
git remote set-url origin "https://github.com/<owner>/<repo>.git"
```

## 4. Commit Provenance & End-to-End Verification

* The bot occupies Git `AUTHOR` and `COMMITTER`; commit trailers continue to carry `Model-Author`, `Agent-Role`, and `Co-authored-by: <Human Name> <<human-email>>`, passing `scripts/validate_provenance.py` unchanged.
* **End-to-end check:**
  1. `python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" check --live` exits 0 and confirms `bot_user_id`.
  2. Commit a change on a feature branch with `python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" exec -- git commit -F <msg>`, push with `exec -- git push -u origin <branch>`, and open a PR with `"${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/gh-bot" pr create ...`.
  3. Confirm on GitHub that commits and the PR author render as `<app-slug>[bot]`, then review, approve, and merge as your human account (`efsalvarenga`).
