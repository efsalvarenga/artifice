#!/usr/bin/env bash
set -eo pipefail

usage() {
    printf '%s\n' \
        'Usage: bash scripts/install_copilot.sh [--check | --help]' \
        'Register Artifice agents and skills in personal Copilot directories via symlinks.' \
        '  Anchor: $HOME/.local/share/artifice -> checkout' \
        '  Links:  ${COPILOT_HOME:-$HOME/.copilot}/{agents,skills}'
}

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }

mode=install
case "$#:${1:-}" in
    0:) ;;
    1:--check) mode=check ;;
    1:--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

[[ "${HOME:-}" == /* && -d "$HOME" ]] || fail 'HOME must be an existing absolute directory.'
home=$(cd "$HOME" && pwd -P)
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
raw_copilot=${COPILOT_HOME:-$home/.copilot}
[[ "$raw_copilot" == /* && "$raw_copilot" != "/" && "/$raw_copilot/" != *'/../'* && "/$raw_copilot/" != *'/./'* ]] || \
    fail 'COPILOT_HOME must be a normalised absolute path.'

resolve_parent_path() {
    local p=${1%/} tail=""
    [[ -n "$p" ]] || p=/
    while [[ ! -d "$p" ]]; do
        [[ ! -e "$p" && ! -L "$p" ]] || fail "Path component is not a directory: $p"
        tail="/${p##*/}$tail"
        p=${p%/*}; p=${p:-/}
    done
    printf '%s%s\n' "$(cd "$p" && pwd -P)" "$tail"
}

anchor="$(resolve_parent_path "$home/.local/share")/artifice"
copilot_home=$(resolve_parent_path "$raw_copilot")

inside() { [[ "$1" == "$2" || "$1" == "$2/"* ]]; }
inside "$copilot_home" "$anchor" && fail 'COPILOT_HOME cannot reside inside the resource anchor.'
inside "$copilot_home" "$repo_root" && fail 'COPILOT_HOME cannot reside inside the checkout.'

destinations=("$anchor" "$copilot_home/agents" "$copilot_home/skills")
targets=("$repo_root" "$anchor/integrations/copilot/agents" "$anchor/skills")
physical=("$repo_root" "$repo_root/integrations/copilot/agents" "$repo_root/skills")
states=()
errors=0

for src in agents/{code-author,code-reviewer,developer-coach}/agent.md \
    integrations/copilot/agents/{code-author,code-reviewer,developer-coach}.agent.md \
    skills/{spec-egm,review,coach-frameworks,local-code}/SKILL.md \
    scripts/{validate_egm,build_review_dossier,check_ollama}.py; do
    [[ -f "$repo_root/$src" && -r "$repo_root/$src" ]] || {
        printf 'Missing source: %s\n' "$repo_root/$src" >&2
        errors=1
    }
done

for i in 0 1 2; do
    dest=${destinations[$i]}
    inside "$dest" "$repo_root" && fail "Destination cannot reside inside checkout: $dest"
    state=missing
    if [[ -L "$dest" ]]; then
        state=conflict
        if [[ -d "$dest" ]]; then
            actual=$(cd "$dest" && pwd -P)
            [[ $(readlink "$dest") == "${targets[$i]}" || "$actual" == "${physical[$i]}" ]] && state=correct-link
        fi
    elif [[ -e "$dest" ]]; then
        state=conflict
    fi
    states+=("$state")
    printf '%s: %s -> %s\n' "$state" "$dest" "${targets[$i]}"
    [[ "$state" == conflict || ( "$mode" == check && "$state" == missing ) ]] && errors=1 || true
done

[[ "$errors" == 0 ]] || fail 'Preflight failed; no filesystem changes were made.'
if [[ "$mode" == check ]]; then
    printf 'PASS: Copilot symlink registration verified.\n'
    exit 0
fi

for i in 0 1 2; do
    [[ "${states[$i]}" == missing ]] || continue
    mkdir -p "${destinations[$i]%/*}"
    ln -s "${targets[$i]}" "${destinations[$i]}"
done
printf 'PASS: Copilot symlinks installed. Start a fresh Copilot session to refresh discovery.\n'
