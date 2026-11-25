# GitHub App Bot Identity Setup

This guide sets up a dedicated GitHub App (`<app-slug>[bot]`) so local coding agents (`agy`, `omp`, Copilot) commit, push, and open pull requests under a bot identity while human review, approval, and merging stay isolated under your personal GitHub account.

Design specification: [010_github_app_bot_identity.md](designs/010_github_app_bot_identity.md) (issue [#63](https://github.com/efsalvarenga/artifice/issues/63)).

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

4. Click **Install App** in the left sidebar and install on **Only select repositories** for each account/org you want to enable. Record each **Installation ID** from `https://github.com/settings/installations/<installation-id>`.
5. Look up the numeric `<bot-user-id>` for `<app-slug>[bot]`:

```bash
gh api "users/<app-slug>[bot]" --jq .id
```

## 2. Create the Local Profile

Write `~/.config/artifice/github-apps/default.json` (outside any repository):

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

Verify both local security invariants and live GitHub authentication (tokens are never printed):

```bash
python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" check --live
```

Additional named profiles (e.g. `~/.config/artifice/github-apps/work.json`) can be selected via `--profile work` or `ARTIFICE_GH_APP_PROFILE=work`.

## 3. Daily Usage (Human Account Untouched)

### Per-Command Execution (Recommended for Shared Checkouts)

Your default `git` identity and `~/.config/gh/hosts.yml` remain bound to your human account. Agents route commands through the helper:

```bash
# Offline commit as <app-slug>[bot] (no network call, no GH_TOKEN exposed to hooks)
python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" exec -- git commit -F commit-msg.txt

# HTTPS push using lazily minted 1-hour installation token
python3 "${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py" exec -- git push -u origin <branch>

# GitHub CLI as <app-slug>[bot] (resolves owner from -R / origin remote)
"${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/gh-bot" pr create --title "..." --body-file pr.md
```

You can optionally symlink `scripts/gh-bot` into `~/.local/bin/gh-bot` (`ln -s "$HOME/.local/share/artifice/scripts/gh-bot" ~/.local/bin/gh-bot`).

### Optional Worktree-Scoped Git Config (`includeIf`)

For dedicated agent worktree roots (where you never run human commits or pushes), you may opt in to automatic Git bot identity and credentials via `~/.gitconfig`:

```ini
# ~/.gitconfig
[includeIf "gitdir:~/.gemini/antigravity-cli/worktrees/"]
    path = ~/.config/artifice/gitconfig-bot
```

```ini
# ~/.config/artifice/gitconfig-bot
[user]
    name = <app-slug>[bot]
    email = <bot-user-id>+<app-slug>[bot]@users.noreply.github.com
[credential "https://github.com"]
    useHttpPath = true
    helper =
    helper = !python3 ~/.local/share/artifice/scripts/github_app_auth.py git-credential
```

For a single dedicated checkout instead of `includeIf`, run:

```bash
git config --local user.name "<app-slug>[bot]"
git config --local user.email "<bot-user-id>+<app-slug>[bot]@users.noreply.github.com"
git config --local credential.https://github.com.useHttpPath true
git config --local credential.https://github.com.helper ""
git config --local --add credential.https://github.com.helper "!python3 ${ARTIFICE_ROOT:-$HOME/.local/share/artifice}/scripts/github_app_auth.py git-credential"
```

### HTTPS Remotes Required

GitHub App installation tokens authenticate over HTTPS (`https://github.com/<owner>/<repo>.git`), not SSH. If a repository uses an SSH remote (`git@github.com:...`), switch `origin` to HTTPS or add `[url "https://github.com/"] insteadOf = git@github.com:` inside `~/.config/artifice/gitconfig-bot`.

## 4. Commit Provenance & End-to-End Verification

* The bot occupies Git `AUTHOR` and `COMMITTER`; commit trailers continue to carry `Model-Author`, `Agent-Role`, and `Co-authored-by: <Human Name> <<human-email>>`, passing `scripts/validate_provenance.py` unchanged.
* **End-to-end check:**
  1. `python3 scripts/github_app_auth.py check --live` exits 0 and confirms `bot_user_id`.
  2. Push a branch and open a PR with `github_app_auth.py exec -- git push ...` and `scripts/gh-bot pr create ...`.
  3. Confirm on GitHub that commits and the PR author render as `<app-slug>[bot]`, then review, approve, and merge as your human account (`efsalvarenga`).
