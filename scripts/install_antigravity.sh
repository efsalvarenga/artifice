#!/usr/bin/env bash
set -eo pipefail

usage() {
    printf '%s\n' \
        'Usage: bash scripts/install_antigravity.sh [--check | --help]' \
        'Register Artifice agents, skills, governance, and personal Antigravity configuration.' \
        '  Anchor:  $HOME/.local/share/artifice -> checkout' \
        '  Config:  ${GEMINI_HOME:-$HOME/.gemini}/config/{agents,skills,skills.json,AGENTS.md}'
}

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }

mode=install
case "$#:${1:-}" in
    0:) ;;
    1:--check) mode=check ;;
    1:--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

command -v python3 >/dev/null || fail 'Python 3 is required for safe symlink registration.'
[[ "${HOME:-}" == /* && -d "$HOME" ]] || fail 'HOME must be an existing absolute directory.'
home=$(cd "$HOME" && pwd -P)
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
raw_gemini=${GEMINI_HOME:-$home/.gemini}
[[ "$raw_gemini" == /* && "$raw_gemini" != "/" && "$raw_gemini" != *'//'* && "/$raw_gemini/" != *'/../'* && "/$raw_gemini/" != *'/./'* ]] || \
    fail 'GEMINI_HOME must be a normalised absolute path.'

resolve_parent_path() {
    local p=${1%/} tail="" physical
    [[ -n "$p" ]] || p=/
    while [[ ! -d "$p" ]]; do
        [[ ! -e "$p" && ! -L "$p" ]] || fail "Path component is not a directory: $p"
        tail="/${p##*/}$tail"
        p=${p%/*}; p=${p:-/}
    done
    physical=$(cd "$p" && pwd -P) || fail "Cannot resolve physical directory: $p"
    printf '%s%s\n' "$physical" "$tail"
}

anchor="$(resolve_parent_path "$home/.local/share")/artifice"
gemini_home=$(resolve_parent_path "$raw_gemini")
gemini_config=$(resolve_parent_path "$gemini_home/config")

inside() { [[ "$1" == "$2" || "$1" == "$2/"* ]]; }

inside "$gemini_home" "$anchor" && fail 'GEMINI_HOME cannot reside inside the resource anchor.'
inside "$gemini_home" "$repo_root" && fail 'GEMINI_HOME cannot reside inside the checkout.'

destinations=("$anchor" "$gemini_config/agents" "$gemini_config/skills" "$gemini_config/AGENTS.md")
targets=("$repo_root" "$anchor/agents" "$anchor/skills" "$anchor/rules/global-agents.md")
physical=("$repo_root" "$repo_root/agents" "$repo_root/skills" "$repo_root/rules/global-agents.md")
states=()
errors=0

for src in agents/{code-author,code-reviewer,developer-coach}/agent.md \
    rules/global-agents.md \
    skills/{spec-egm,review,coach-frameworks,local-code,vibe-execute}/SKILL.md \
    scripts/{validate_egm,validate_provenance,build_review_dossier,check_ollama,vibe_execute}.py; do
    [[ -f "$repo_root/$src" && -r "$repo_root/$src" ]] || {
        printf 'Missing source: %s\n' "$repo_root/$src" >&2
        errors=1
    }
done

for ((i=0; i<${#destinations[@]}; i++)); do
    dest=${destinations[$i]}
    inside "$dest" "$repo_root" && fail "Destination cannot reside inside checkout: $dest"
    state=missing
    if [[ -L "$dest" ]]; then
        state=conflict
        if [[ -d "${physical[$i]}" && -d "$dest" ]]; then
            actual=$(cd "$dest" && pwd -P)
            [[ $(readlink "$dest") == "${targets[$i]}" || "$actual" == "${physical[$i]}" ]] && state=correct-link
        elif [[ -f "${physical[$i]}" && -f "$dest" && -r "$dest" ]]; then
            actual=$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$dest")
            [[ "$actual" == "${physical[$i]}" ]] && state=correct-link
        fi
    elif [[ -e "$dest" ]]; then
        state=conflict
    fi
    if [[ "$mode" == install && "$state" == missing ]]; then
        parent=${dest%/*}
        while [[ ! -d "$parent" ]]; do
            parent=${parent%/*}; parent=${parent:-/}
        done
        [[ -w "$parent" ]] || fail "Parent directory not writable: $parent"
    fi
    states+=("$state")
    printf '%s: %s -> %s\n' "$state" "$dest" "${targets[$i]}"
    [[ "$state" == conflict || ( "$mode" == check && "$state" == missing ) ]] && errors=1 || true
done

skills_json="$gemini_config/skills.json"
if [[ -f "$skills_json" ]]; then
    if grep -q '~' "$skills_json"; then
        printf 'conflict: %s contains unresolved tilde (~); Antigravity requires absolute paths.\n' "$skills_json"
        errors=1
    elif grep -q "$anchor/skills" "$skills_json" || grep -q "$repo_root/skills" "$skills_json"; then
        printf 'correct-config: %s configured with absolute skills path\n' "$skills_json"
    else
        printf 'warning: %s exists but does not reference Artifice skills\n' "$skills_json"
    fi
else
    printf 'missing: %s\n' "$skills_json"
    [[ "$mode" == check ]] && errors=1 || true
fi

[[ "$errors" == 0 ]] || fail 'Preflight failed; no filesystem changes were made. Review conflicts and migrate personal entries manually before retrying.'
if [[ "$mode" == check ]]; then
    printf 'PASS: Antigravity symlink registration verified.\n'
    exit 0
fi

for ((i=0; i<${#destinations[@]}; i++)); do
    [[ "${states[$i]}" == missing ]] || continue
    mkdir -p "${destinations[$i]%/*}"
    python3 -c 'import os, sys; os.symlink(sys.argv[1], sys.argv[2])' "${targets[$i]}" "${destinations[$i]}"
done

mkdir -p "$gemini_config"
if [[ ! -f "$skills_json" ]]; then
    cat << EOF > "$skills_json"
{
  "entries": [
    {
      "path": "$anchor/skills"
    }
  ]
}
EOF
    printf 'installed: %s\n' "$skills_json"
fi

printf 'PASS: Antigravity symlinks and configuration installed. Start a fresh Antigravity session to refresh discovery.\n'
