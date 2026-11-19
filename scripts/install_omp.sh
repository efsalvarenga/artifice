#!/usr/bin/env bash
set -eo pipefail

usage() {
    printf '%s\n' \
        'Usage: bash scripts/install_omp.sh [--check | --help]' \
        'Register Artifice agents, governance, and skills config for omp.' \
        '  Anchor:  $HOME/.local/share/artifice -> checkout' \
        '  Client:  active omp agent dir (PI_CODING_AGENT_DIR, else ~/.omp/profiles/$OMP_PROFILE/agent, else ~/.omp/agent)' \
        '  Config:  <client>/AGENTS.md, <client>/agents, <client>/config.yml (skills.customDirectories)'
}

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }

mode=install
case "$#:${1:-}" in
    0:) ;;
    1:--check) mode=check ;;
    1:--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

command -v python3 >/dev/null || fail 'Python 3 is required for safe symlink and config registration.'
[[ "${HOME:-}" == /* && -d "$HOME" ]] || fail 'HOME must be an existing absolute directory.'
home=$(cd "$HOME" && pwd -P)
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)

if [[ -n "${PI_CODING_AGENT_DIR:-}" ]]; then
    raw_omp=$PI_CODING_AGENT_DIR
elif [[ -n "${OMP_PROFILE:-}" ]]; then
    [[ "$OMP_PROFILE" != */* ]] || fail 'OMP_PROFILE must be a single path segment (flat profile name).'
    raw_omp="$home/.omp/profiles/$OMP_PROFILE/agent"
else
    raw_omp="$home/.omp/agent"
fi
[[ "$raw_omp" == /* && "$raw_omp" != "/" && "$raw_omp" != *'//'* && "/$raw_omp/" != *'/../'* && "/$raw_omp/" != *'/./'* ]] || \
    fail 'The omp agent directory (PI_CODING_AGENT_DIR / OMP_PROFILE) must be a normalised absolute path.'

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
omp_agent_dir=$(resolve_parent_path "$raw_omp")

inside() { [[ "$1" == "$2" || "$1" == "$2/"* ]]; }

inside "$omp_agent_dir" "$anchor" && fail 'The omp agent directory cannot reside inside the resource anchor.'
inside "$omp_agent_dir" "$repo_root" && fail 'The omp agent directory cannot reside inside the checkout.'

destinations=("$anchor" "$omp_agent_dir/AGENTS.md" "$omp_agent_dir/agents")
targets=("$repo_root" "$anchor/rules/global-agents.md" "$anchor/integrations/omp/agents")
physical=("$repo_root" "$repo_root/rules/global-agents.md" "$repo_root/integrations/omp/agents")
states=()
errors=0

for src in agents/{code-author,code-reviewer,developer-coach}/agent.md \
    rules/global-agents.md \
    integrations/omp/agents/{code-author,code-reviewer,developer-coach}.md \
    skills/{review,coach-frameworks,vibe-execute}/SKILL.md \
    scripts/{validate_provenance,build_review_dossier,check_ollama,vibe_execute}.py; do
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
        [[ "$dest" -ef "${physical[$i]}" ]] && state=correct-link
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

# config.yml registration (skills.customDirectories). Probe exit codes:
# 0 = entry already registered under skills.customDirectories (correct-config),
# 1 = file absent (missing), 2 = conflict (not a regular file, or entry not
# registered there; the snippet to add manually is printed). The probe never
# writes.
config_yml="$omp_agent_dir/config.yml"
config_entry="$anchor/skills"
probe_rc=0
python3 -c '
import os, re, sys

config, entry = sys.argv[1], sys.argv[2]
if os.path.lexists(config) and not os.path.isfile(config):
    print("conflict: %s is not a regular file (directory, special file, or dangling symlink)" % config)
    sys.exit(2)
if not os.path.lexists(config):
    sys.exit(1)

top = re.compile(r"^([A-Za-z_][\w-]*):")
cd_key = re.compile(r"^(\s+)customDirectories:\s*$")
item = re.compile(r"^(\s+)-\s*(\S.*)$")
in_skills = False
cd_indent = -1
with open(config, "r", encoding="utf-8") as f:
    for ln in f:
        ln = ln.rstrip("\n")
        m = top.match(ln)
        if m:
            in_skills = m.group(1) == "skills"
            cd_indent = -1
            continue
        if not re.match(r"^\s", ln) or not in_skills:
            continue
        indent = len(ln) - len(ln.lstrip())
        m_cd = cd_key.match(ln)
        if m_cd:
            cd_indent = indent
            continue
        if cd_indent >= 0:
            if indent > cd_indent:
                m_item = item.match(ln)
                if m_item and m_item.group(2).strip().strip("\"\x27") == entry:
                    sys.exit(0)
            else:
                cd_indent = -1
print("conflict: %s does not register %s under skills.customDirectories; add manually:" % (config, entry))
print("  skills:")
print("    customDirectories:")
print("      - " + entry)
sys.exit(2)
' "$config_yml" "$config_entry" || probe_rc=$?
case "$probe_rc" in
    0)
        printf 'correct-config: %s already registers the anchor skills path\n' "$config_yml"
        ;;
    1)
        if [[ "$mode" == check ]]; then
            printf 'missing: %s (skills.customDirectories entry for %s)\n' "$config_yml" "$config_entry"
            errors=1
        fi
        ;;
    2)
        errors=1
        ;;
    *) fail "Unexpected config probe exit: $probe_rc" ;;
esac

[[ "$errors" == 0 ]] || fail 'Preflight failed; no filesystem changes were made. Review conflicts and migrate personal entries manually before retrying.'
if [[ "$mode" == check ]]; then
    printf 'PASS: omp symlink and config registration verified.\n'
    exit 0
fi

for ((i=0; i<${#destinations[@]}; i++)); do
    [[ "${states[$i]}" == missing ]] || continue
    mkdir -p "${destinations[$i]%/*}"
    python3 -c '
import os, sys
try:
    os.symlink(sys.argv[1], sys.argv[2])
except FileExistsError:
    sys.exit("conflict: %s appeared after preflight; migrate it manually before retrying." % sys.argv[2])
' "${targets[$i]}" "${destinations[$i]}"
done

# A missing config.yml is created exclusively with O_CREAT|O_EXCL, so a file
# (or dangling symlink) appearing after preflight is a conflict, never an
# overwrite. An existing file is never modified.
if [[ "$probe_rc" == 1 ]]; then
    mkdir -p "$omp_agent_dir"
    python3 -c '
import os, sys

config, entry = sys.argv[1], sys.argv[2]
text = (
    "# omp agent configuration (managed by artifice install_omp.sh)\n"
    "skills:\n  customDirectories:\n    - %s\n" % entry
)
try:
    fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
except FileExistsError:
    sys.exit("conflict: %s appeared after preflight; migrate it manually before retrying." % config)
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(text)
print("installed: %s (created with skills.customDirectories)" % config)
' "$config_yml" "$config_entry"
fi

printf 'PASS: omp symlinks and config registration installed. Start a fresh omp session to refresh discovery.\n'
