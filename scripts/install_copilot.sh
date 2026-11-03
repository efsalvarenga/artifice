#!/usr/bin/env bash
set -eo pipefail

usage() {
    printf '%s\n' \
        'Usage: bash scripts/install_copilot.sh [--check | --help]' \
        'Link this checkout into personal Copilot registration directories.' \
        'Resource anchor: $HOME/.local/share/artifice' \
        'Registration: ${COPILOT_HOME:-$HOME/.copilot}/{agents,skills}' \
        '--check verifies without writing; --help displays this message.' \
        'Existing files, directories, and unrelated or broken links are never replaced.' \
        'Prevent concurrent installation. Review conflicts manually and rerun after repair.' \
        'A fresh client session may be needed; installation does not prove live discovery.'
}

mode=install
case "$#:${1:-}" in
    0:) ;;
    1:--check) mode=check ;;
    1:--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

[[ "${HOME:-}" == /* && -d "$HOME" ]] || fail 'HOME must be an existing absolute directory.'
home=$(cd "$HOME" && pwd -P)
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
copilot_home=${COPILOT_HOME:-$home/.copilot}
[[ "$copilot_home" == /* ]] || fail 'COPILOT_HOME must be absolute.'
anchor="$home/.local/share/artifice"

planned_directory() {
    local path=$1 segment current=/ candidate
    local segments=()
    IFS=/ read -r -a segments <<< "$path"
    for segment in "${segments[@]}"; do
        case "$segment" in
            ''|.) continue ;;
            ..)
                [[ -d "$current" ]] || {
                    printf 'Error: cannot traverse missing parent: %s\n' "$current" >&2
                    return 1
                }
                current=${current%/*}
                current=${current:-/}
                continue
                ;;
        esac
        candidate="${current%/}/$segment"
        if [[ -e "$candidate" || -L "$candidate" ]]; then
            [[ -d "$candidate" ]] || {
                printf 'Error: parent is not a readable directory: %s\n' "$candidate" >&2
                return 1
            }
            current=$(cd "$candidate" && pwd -P) || return 1
        else
            current=$candidate
        fi
    done
    printf '%s\n' "$current"
}

inside() {
    [[ "$1" == "$2" || "$1" == "$2/"* ]]
}

inside "$copilot_home" "$anchor" && fail 'Copilot registration cannot be inside the resource anchor.'
inside "$copilot_home" "$repo_root" && fail 'Copilot registration cannot be inside the checkout.'
anchor_parent=$(planned_directory "${anchor%/*}") || exit 1
anchor="$anchor_parent/artifice"
inside "$copilot_home" "$anchor" && fail 'Copilot registration would create a resource cycle.'
copilot_home=$(planned_directory "$copilot_home") || exit 1
inside "$copilot_home" "$anchor" && fail 'Copilot registration would create a resource cycle.'
inside "$copilot_home" "$repo_root" && fail 'Copilot registration resolves inside the checkout.'

destinations=("$anchor" "$copilot_home/agents" "$copilot_home/skills")
targets=("$repo_root" "$anchor/integrations/copilot/agents" "$anchor/skills")
physical_targets=("$repo_root" "$repo_root/integrations/copilot/agents" "$repo_root/skills")
created_links=()
created_targets=()
created_directories=()
states=()
errors=0

for role in code-author code-reviewer developer-coach; do
    for source in "agents/$role/agent.md" "integrations/copilot/agents/$role.agent.md"; do
        [[ -f "$repo_root/$source" && -r "$repo_root/$source" ]] || {
            printf 'Missing or unreadable source: %s\n' "$repo_root/$source" >&2
            errors=$((errors + 1))
        }
    done
done
for skill in spec-egm review coach-frameworks local-code; do
    [[ -f "$repo_root/skills/$skill/SKILL.md" && -r "$repo_root/skills/$skill/SKILL.md" ]] || {
        printf 'Missing skill: %s\n' "$repo_root/skills/$skill/SKILL.md" >&2
        errors=$((errors + 1))
    }
done
for source in validate_egm.py build_review_dossier.py check_ollama.py; do
    [[ -f "$repo_root/scripts/$source" && -r "$repo_root/scripts/$source" ]] || {
        printf 'Missing script: %s\n' "$repo_root/scripts/$source" >&2
        errors=$((errors + 1))
    }
done

classify() {
    local destination=$1 expected=$2 expected_physical=$3 actual
    if [[ -L "$destination" ]]; then
        if [[ -d "$destination" ]]; then
            actual=$(cd "$destination" && pwd -P) || return 1
            if [[ $(readlink "$destination") == "$expected" || "$actual" == "$expected_physical" ]]; then
                printf 'correct-link\n'
                return
            fi
        fi
        printf 'conflict\n'
    elif [[ -e "$destination" ]]; then
        printf 'conflict\n'
    else
        printf 'missing\n'
    fi
}

for index in 0 1 2; do
    destination=${destinations[$index]}
    inside "$destination" "$repo_root" && fail "Destination is inside checkout: $destination"
    for prior in 0 1 2; do
        if [[ "$index" != "$prior" && "$destination" == "${destinations[$prior]}" ]]; then
            fail "Duplicate destination: $destination"
        fi
    done
    planned_directory "${destination%/*}" >/dev/null || errors=$((errors + 1))
    states[$index]=$(classify "$destination" "${targets[$index]}" "${physical_targets[$index]}")
    printf '%s: %s -> %s\n' "${states[$index]}" "$destination" "${targets[$index]}"
    if [[ "${states[$index]}" == conflict || ( "$mode" == check && "${states[$index]}" == missing ) ]]; then
        errors=$((errors + 1))
    fi
done
[[ "$errors" == 0 ]] || fail 'Preflight failed; no installation paths were changed. Review the reported conflicts or missing sources.'
if [[ "$mode" == check ]]; then
    printf 'PASS: filesystem registration is complete. Live client acceptance is separate.\n'
    exit 0
fi

rollback() {
    local exit_code=$? index path
    trap - EXIT INT TERM HUP
    [[ "$signal_pending" == 0 ]] || exit_code=1
    if [[ "$exit_code" != 0 ]]; then
        for ((index=${#created_links[@]}-1; index>=0; index--)); do
            path=${created_links[$index]}
            if [[ -L "$path" && $(readlink "$path") == "${created_targets[$index]}" ]]; then
                rm "$path" || printf 'Rollback failed for link: %s\n' "$path" >&2
            fi
        done
        for ((index=${#created_directories[@]}-1; index>=0; index--)); do
            path=${created_directories[$index]}
            if [[ -d "$path" && ! -L "$path" ]]; then
                rmdir "$path" || printf 'Rollback could not remove directory: %s\n' "$path" >&2
            fi
        done
    fi
    exit "$exit_code"
}
signal_pending=0
trap rollback EXIT
trap 'signal_pending=1' INT TERM HUP

check_signal() {
    [[ "$signal_pending" == 0 ]] || fail 'Installation interrupted; rolling back owned paths.'
}

ensure_directory() {
    local directory=$1 parent result=0
    check_signal
    if [[ -e "$directory" || -L "$directory" ]]; then
        [[ -d "$directory" ]] || fail "Parent changed during installation: $directory"
        return
    fi
    parent=${directory%/*}
    ensure_directory "${parent:-/}"
    mkdir "$directory" || result=$?
    if [[ -d "$directory" && ! -L "$directory" ]]; then
        created_directories[${#created_directories[@]}]=$directory
    fi
    [[ "$result" == 0 ]] || fail "Cannot create directory: $directory"
    check_signal
}

for index in 0 1 2; do
    check_signal
    destination=${destinations[$index]}
    state=$(classify "$destination" "${targets[$index]}" "${physical_targets[$index]}")
    [[ "$state" != conflict ]] || fail "Destination changed during installation: $destination"
    [[ "$state" != correct-link ]] || continue
    ensure_directory "${destination%/*}"
    [[ ! -e "$destination" && ! -L "$destination" ]] || fail "Destination is no longer missing: $destination"
    result=0
    ln -s "${targets[$index]}" "$destination" || result=$?
    if [[ -L "$destination" && $(readlink "$destination") == "${targets[$index]}" ]]; then
        created_links[${#created_links[@]}]=$destination
        created_targets[${#created_targets[@]}]=${targets[$index]}
    fi
    [[ "$result" == 0 ]] || fail "Cannot create link: $destination"
    check_signal
done
for index in 0 1 2; do
    [[ $(classify "${destinations[$index]}" "${targets[$index]}" "${physical_targets[$index]}") == correct-link ]] || \
        fail "Final verification failed: ${destinations[$index]}"
done
check_signal
printf 'PASS: filesystem installation complete. Start a fresh Copilot session to verify discovery and role loading.\n'
