#!/usr/bin/env bash
set -eo pipefail

usage() {
    printf '%s\n' \
        'Usage: bash scripts/install_antigravity.sh [--check | --help]' \
        'Register Artifice agents, skills, and configuration in personal Antigravity directories.' \
        '  Anchor:  $HOME/.local/share/artifice -> checkout' \
        '  Config:  ${GEMINI_HOME:-$HOME/.gemini}/config/{agents,skills,skills.json}'
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
raw_gemini=${GEMINI_HOME:-$home/.gemini}
[[ "$raw_gemini" == /* && "$raw_gemini" != "/" && "/$raw_gemini/" != *'/../'* && "/$raw_gemini/" != *'/./'* ]] || \
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
gemini_config="$gemini_home/config"

inside() {
    local c1 c2
    c1=$(realpath -s -m -- "$1" 2>/dev/null || echo "$1")
    c2=$(realpath -s -m -- "$2" 2>/dev/null || echo "$2")
    [[ "$c1" == "$c2" || "$c1" == "$c2/"* ]]
}

inside "$gemini_home" "$anchor" && fail 'GEMINI_HOME cannot reside inside the resource anchor.'
inside "$gemini_home" "$repo_root" && fail 'GEMINI_HOME cannot reside inside the checkout.'

destinations=("$anchor" "$gemini_config/agents" "$gemini_config/skills")
targets=("$repo_root" "$anchor/agents" "$anchor/skills")
physical=("$repo_root" "$repo_root/agents" "$repo_root/skills")
states=()
errors=0

for src in agents/{code-author,code-reviewer,developer-coach}/agent.md \
    skills/{spec-egm,review,coach-frameworks,local-code,vibe-execute}/SKILL.md \
    scripts/{validate_egm,build_review_dossier,check_ollama,vibe_execute}.py; do
    [[ -f "$repo_root/$src" && -r "$repo_root/$src" ]] || {
        printf 'Missing source: %s\n' "$repo_root/$src" >&2
        errors=1
    }
done

for i in 0 1 2; do
    dest=${destinations[$i]}
    inside "$dest" "$repo_root" && fail "Destination cannot reside inside checkout: $dest"
    
    parent="$(dirname "$dest")"
    while [[ ! -d "$parent" && -n "$parent" && "$parent" != "/" ]]; do
        parent="$(dirname "$parent")"
    done
    [[ -w "$parent" ]] || fail "Parent directory not writable: $parent"

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

[[ "$errors" == 0 ]] || fail 'Preflight failed; no filesystem changes were made.'
if [[ "$mode" == check ]]; then
    printf 'PASS: Antigravity symlink registration verified.\n'
    exit 0
fi

for i in 0 1 2; do
    [[ "${states[$i]}" == missing ]] || continue
    mkdir -p "${destinations[$i]%/*}"
    ln -s "${targets[$i]}" "${destinations[$i]}"
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
