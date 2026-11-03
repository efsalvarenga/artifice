#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
[[ -f "$repo_root/scripts/install_copilot.sh" ]] || {
    printf 'FAIL: installer has not been implemented\n' >&2
    exit 1
}
test_root=$(mktemp -d "${TMPDIR:-/tmp}/artifice-tests.XXXXXX")
test_root=$(cd "$test_root" && pwd -P)
trap 'rm -rf "$test_root"' EXIT
case_number=0

new_case() {
    case_number=$((case_number + 1))
    case_root="$test_root/case $case_number"
    checkout="$case_root/checkout with spaces"
    home="$case_root/home with spaces"
    copilot="$home/.copilot"
    anchor="$home/.local/share/artifice"
    mkdir -p "$checkout" "$home"
    cp -R "$repo_root/agents" "$repo_root/skills" "$repo_root/scripts" \
        "$repo_root/integrations" "$checkout/"
    installer="$checkout/scripts/install_copilot.sh"
}

run_install() {
    HOME="$home" COPILOT_HOME="$copilot" bash "$installer" "$@"
}

expect_exit() {
    local expected=$1
    shift
    local result=0
    "$@" >"$case_root/output" 2>&1 || result=$?
    if [[ "$result" != "$expected" ]]; then
        cat "$case_root/output" >&2
        printf 'FAIL: expected exit %s, got %s\n' "$expected" "$result" >&2
        exit 1
    fi
}

assert_absent() {
    [[ ! -e "$1" && ! -L "$1" ]] || {
        printf 'FAIL: unexpected path %s\n' "$1" >&2
        exit 1
    }
}

assert_links() {
    [[ $(readlink "$anchor") == "$checkout" ]] || { printf 'FAIL: anchor target\n' >&2; exit 1; }
    [[ $(readlink "$copilot/agents") == "$anchor/integrations/copilot/agents" ]] || { printf 'FAIL: agent target\n' >&2; exit 1; }
    [[ $(readlink "$copilot/skills") == "$anchor/skills" ]] || { printf 'FAIL: skill target\n' >&2; exit 1; }
}

new_case
expect_exit 1 run_install --check
assert_absent "$home/.local"
assert_absent "$copilot"
expect_exit 0 run_install --help
assert_absent "$copilot"
expect_exit 2 run_install --unknown
expect_exit 2 run_install --check unexpected
assert_absent "$anchor"
expect_exit 0 run_install
assert_links
expect_exit 0 run_install
assert_links
expect_exit 0 run_install --check
[[ -r "$copilot/agents/code-author.agent.md" ]]
[[ -r "$copilot/skills/spec-egm/references/design-spec-template.md" ]]
[[ -r "$anchor/scripts/validate_egm.py" ]]
[[ -r "$anchor/agents/code-author/agent.md" ]]
cp "$checkout/skills/local-code/SKILL.md" "$checkout/skills/local-code/added-resource.md"
[[ -r "$copilot/skills/local-code/added-resource.md" ]]
mkdir "$checkout/skills/future-skill"
cp "$checkout/skills/local-code/SKILL.md" "$checkout/skills/future-skill/SKILL.md"
[[ -r "$copilot/skills/future-skill/SKILL.md" ]]
cp "$checkout/agents/code-reviewer/agent.md" "$checkout/agents/code-author/agent.md"
cmp "$checkout/agents/code-reviewer/agent.md" "$anchor/agents/code-author/agent.md"
cp "$checkout/skills/spec-egm/SKILL.md" "$checkout/skills/local-code/SKILL.md"
cmp "$checkout/skills/spec-egm/SKILL.md" "$copilot/skills/local-code/SKILL.md"

new_case
copilot="$case_root/custom copilot"
expect_exit 0 run_install
assert_links
assert_absent "$home/.copilot"

new_case
expect_exit 0 env -u COPILOT_HOME HOME="$home" bash "$installer"
assert_links

new_case
mkdir -p "$home/.local/share" "$copilot"
ln -s "$checkout/." "$anchor"
ln -s "$checkout/integrations/copilot/agents" "$copilot/agents"
ln -s "$checkout/skills/." "$copilot/skills"
expect_exit 0 run_install
[[ $(readlink "$anchor") == "$checkout/." ]]
[[ $(readlink "$copilot/skills") == "$checkout/skills/." ]]

for conflict in directory file wrong-link broken-link; do
    new_case
    mkdir "$copilot"
    case "$conflict" in
        directory) mkdir "$copilot/skills" ;;
        file) touch "$copilot/skills" ;;
        wrong-link) ln -s "$home" "$copilot/skills" ;;
        broken-link) ln -s "$case_root/missing" "$copilot/skills" ;;
    esac
    expect_exit 1 run_install
    expect_exit 1 run_install --check
    assert_absent "$home/.local"
    assert_absent "$copilot/agents"
    [[ -e "$copilot/skills" || -L "$copilot/skills" ]]
done

new_case
mkdir "$home/.local"
touch "$home/.local/share"
expect_exit 1 run_install
assert_absent "$copilot"

new_case
rm "$checkout/agents/code-author/agent.md"
expect_exit 1 run_install
assert_absent "$home/.local"
assert_absent "$copilot"

new_case
expect_exit 1 env -u HOME COPILOT_HOME="$copilot" bash "$installer"
expect_exit 1 env HOME='' bash "$installer"
expect_exit 1 env HOME='relative' bash "$installer"
expect_exit 1 env HOME="$home" COPILOT_HOME='relative' bash "$installer"
copilot="$checkout/personal"
expect_exit 1 run_install
assert_absent "$copilot"
copilot="$anchor/personal"
expect_exit 1 run_install
assert_absent "$anchor"

new_case
mkdir -p "$home/.local/share"
ln -s "$checkout" "$anchor"
ln() {
    if [[ "${@: -1}" == "$COPILOT_HOME/skills" ]]; then
        return 1
    fi
    /bin/ln "$@"
}
export -f ln
expect_exit 1 run_install
[[ -L "$anchor" ]]
assert_absent "$copilot"
unset -f ln
expect_exit 0 run_install
assert_links

new_case
ln() {
    if [[ "${@: -1}" == "$COPILOT_HOME/skills" ]]; then
        return 1
    fi
    /bin/ln "$@"
}
export -f ln
expect_exit 1 run_install
assert_absent "$home/.local"
assert_absent "$copilot"
unset -f ln

new_case
expect_exit 0 run_install
copilot="$copilot/agents/code-reviewer.agent.md/../.."
expect_exit 1 run_install --check

new_case
mkdir "$case_root/alias target"
ln -s "$case_root/alias target" "$home/alias"
copilot="$home/alias/../physical copilot"
expect_exit 0 run_install
[[ -L "$case_root/physical copilot/skills" ]]
assert_absent "$home/physical copilot"

new_case
ln() {
    /bin/ln "$@" || return
    if [[ "${@: -1}" == "$COPILOT_HOME/skills" ]]; then
        kill -TERM "$$"
    fi
}
export -f ln
expect_exit 1 run_install
assert_absent "$home/.local"
assert_absent "$copilot"
unset -f ln

new_case
mkdir() {
    /bin/mkdir "$@" || return
    kill -TERM "$$"
}
export -f mkdir
expect_exit 1 run_install
assert_absent "$home/.local"
assert_absent "$copilot"
unset -f mkdir

new_case
ln() {
    /bin/ln "$@" || return
    if [[ "${@: -1}" == "$COPILOT_HOME/skills" ]]; then
        return 143
    fi
}
export -f ln
expect_exit 1 run_install
assert_absent "$home/.local"
assert_absent "$copilot"
unset -f ln

new_case
mkdir() {
    /bin/mkdir "$@" || return
    return 143
}
export -f mkdir
expect_exit 1 run_install
assert_absent "$home/.local"
assert_absent "$copilot"
unset -f mkdir

new_case
(
    cd "$case_root"
    expect_exit 0 run_install
)
assert_links
physical_source=$(cd "$(dirname "$copilot/skills/spec-egm/SKILL.md")" && pwd -P)
fallback_root=$(cd "$physical_source/../.." && pwd -P)
[[ "$fallback_root" == "$checkout" ]]
rm "$anchor"
[[ -r "$fallback_root/scripts/validate_egm.py" ]]
expect_exit 1 run_install --check

new_case
ensure_source=$(sed -n '/^ensure_directory() {/,/^}/p' "$installer")
expect_exit 1 env HOME="$home" bash -c '
    eval "$1"
    created_directories=()
    check_signal() { :; }
    fail() { exit 1; }
    mkdir() { [[ "$1" == /artifice-root-parent-probe ]] && exit 1; exit 99; }
    ensure_directory /artifice-root-parent-probe
' bash "$ensure_source"

printf 'PASS: %s temporary-home cases (installation, conflicts, rollback, resources, updates).\n' "$case_number"
