#!/usr/bin/env python3
"""Zero-dependency GitHub App bot authentication helper for Git and gh CLI.

Mints short-lived (1-hour) GitHub App installation tokens via Python stdlib and
the system `openssl` CLI, caches them safely under XDG runtime/cache directories,
implements Git's `credential.helper` protocol, and runs commands under the bot's
Git identity and `GH_TOKEN` without modifying human defaults.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import datetime
import errno
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import stat
import subprocess
import sys
import time
from typing import Mapping, Optional, TextIO
from urllib.error import HTTPError, URLError
import urllib.parse
import urllib.request

PROFILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
NUMERIC_ID_RE = re.compile(r"^\d+$")
SLUG_RE = re.compile(r"^[A-Za-z0-9-]+$")
GITHUB_API_BASE = "https://api.github.com"
API_VERSION = "2022-11-28"
USER_AGENT = "artifice-github-app-auth"
CACHE_MARGIN_SECONDS = 300
HTTP_TIMEOUT_SECONDS = 15
OPENSSL_TIMEOUT_SECONDS = 15


class AuthError(Exception):
    """Actionable failure in configuration, key validation, or GitHub auth."""


@dataclass(frozen=True)
class BotConfig:
    profile: str
    config_path: Path
    explicit_config: bool
    app_id: str
    app_slug: str
    bot_user_id: str
    installation_id: Optional[str]
    installations: dict[str, str]
    private_key_path: Path

    @property
    def bot_name(self) -> str:
        return f"{self.app_slug}[bot]"

    @property
    def bot_email(self) -> str:
        return f"{self.bot_user_id}+{self.app_slug}[bot]@users.noreply.github.com"

    def resolve_installation_id(self, owner: Optional[str] = None) -> str:
        if owner:
            key = owner.strip().lower()
            if key in self.installations:
                return self.installations[key]
        if self.installation_id:
            return self.installation_id
        if len(self.installations) == 1:
            return next(iter(self.installations.values()))
        target = f" for owner '{owner}'" if owner else ""
        raise AuthError(f"No installation_id configured{target} in {self.config_path}.")


def validate_profile_name(profile: str) -> str:
    if not profile or not PROFILE_RE.fullmatch(profile):
        raise AuthError(
            f"Invalid profile name {profile!r}; expected ^[A-Za-z0-9][A-Za-z0-9_-]{{0,63}}$."
        )
    return profile


def _expand_path(raw: str, env: Mapping[str, str]) -> Path:
    if raw == "~":
        home = env.get("HOME") or os.path.expanduser("~")
        return Path(home)
    if raw.startswith("~/"):
        home = env.get("HOME") or os.path.expanduser("~")
        return Path(home) / raw[2:]
    return Path(os.path.expanduser(raw))


def _config_dir(env: Mapping[str, str]) -> Path:
    override = env.get("ARTIFICE_GH_APP_CONFIG_DIR")
    if override:
        return _expand_path(override, env)
    xdg = env.get("XDG_CONFIG_HOME")
    if xdg:
        return _expand_path(xdg, env) / "artifice"
    home = env.get("HOME") or os.path.expanduser("~")
    return Path(home) / ".config" / "artifice"


def _cache_dir(env: Mapping[str, str]) -> Path:
    base = env.get("XDG_RUNTIME_DIR") or env.get("XDG_CACHE_HOME")
    if base:
        return _expand_path(base, env) / "artifice" / "gh-app-tokens"
    home = env.get("HOME") or os.path.expanduser("~")
    return Path(home) / ".cache" / "artifice" / "gh-app-tokens"


def _require_regex(value: object, pattern: re.Pattern[str], field: str, source: Path) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise AuthError(f"Invalid or missing '{field}' in {source}.")
    return value


def load_config(
    config_path: Optional[str] = None,
    profile: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> BotConfig:
    active_env = env if env is not None else os.environ
    explicit_raw = config_path if config_path is not None else active_env.get("ARTIFICE_GH_APP_CONFIG")
    prof_raw = profile if profile is not None else (active_env.get("ARTIFICE_GH_APP_PROFILE") or "default")
    prof = validate_profile_name(prof_raw)

    if explicit_raw:
        cfg_file = _expand_path(explicit_raw, active_env)
        explicit = True
    else:
        cfg_file = _config_dir(active_env) / "github-apps" / f"{prof}.json"
        explicit = False

    try:
        raw_text = cfg_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise AuthError(f"Cannot read GitHub App config {cfg_file}: {exc}") from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise AuthError(f"Invalid JSON in {cfg_file}: {exc}") from exc

    if not isinstance(data, dict):
        raise AuthError(f"Config root in {cfg_file} must be a JSON object.")

    app_id = _require_regex(data.get("app_id"), NUMERIC_ID_RE, "app_id", cfg_file)
    app_slug = _require_regex(data.get("app_slug"), SLUG_RE, "app_slug", cfg_file)
    bot_user_id = _require_regex(data.get("bot_user_id"), NUMERIC_ID_RE, "bot_user_id", cfg_file)

    inst_raw = data.get("installation_id")
    installation_id: Optional[str] = None
    if inst_raw is not None:
        installation_id = _require_regex(inst_raw, NUMERIC_ID_RE, "installation_id", cfg_file)

    installations: dict[str, str] = {}
    inst_map = data.get("installations")
    if inst_map is not None:
        if not isinstance(inst_map, dict):
            raise AuthError(f"'installations' in {cfg_file} must be an object mapping owner to numeric ID.")
        for owner_key, owner_inst in inst_map.items():
            if not isinstance(owner_key, str) or not owner_key.strip():
                raise AuthError(f"Empty owner key in 'installations' of {cfg_file}.")
            installations[owner_key.strip().lower()] = _require_regex(
                owner_inst, NUMERIC_ID_RE, f"installations.{owner_key}", cfg_file
            )

    if installation_id is None and not installations:
        raise AuthError(f"Config {cfg_file} must define 'installation_id' or a non-empty 'installations' map.")

    pem_raw = data.get("private_key_path")
    if not isinstance(pem_raw, str) or not pem_raw.strip():
        raise AuthError(f"Missing 'private_key_path' in {cfg_file}.")
    pem_path = _expand_path(pem_raw.strip(), active_env)

    return BotConfig(
        profile=prof,
        config_path=cfg_file,
        explicit_config=explicit,
        app_id=app_id,
        app_slug=app_slug,
        bot_user_id=bot_user_id,
        installation_id=installation_id,
        installations=installations,
        private_key_path=pem_path,
    )


def _assert_not_inside_git_repo(path: Path) -> None:
    checked: set[Path] = set()
    candidates = [path.parent]
    try:
        candidates.append(path.parent.resolve())
    except OSError:
        pass
    for start in candidates:
        cur = start
        while True:
            if cur in checked:
                break
            checked.add(cur)
            if os.path.lexists(cur / ".git"):
                raise AuthError(
                    f"Private key {path} resides inside a Git repository ({cur}); move it outside any repository."
                )
            if cur.parent == cur:
                break
            cur = cur.parent


def validate_and_open_private_key(path: Path) -> int:
    _assert_not_inside_git_repo(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise AuthError(f"Private key {path} must not be a symlink.") from exc
        raise AuthError(f"Cannot open private key {path}: {exc}") from exc

    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise AuthError(f"Private key {path} must be a regular file.")
        if st.st_uid != os.geteuid():
            raise AuthError(f"Private key {path} must be owned by the current user.")
        if (st.st_mode & 0o077) != 0:
            raise AuthError(
                f"Private key {path} has overly permissive mode {oct(stat.S_IMODE(st.st_mode))}; run: chmod 600 {path}"
            )
        header = os.pread(fd, 4096, 0)
        if b"ENCRYPTED" in header:
            raise AuthError(
                f"Private key {path} is passphrase-protected; GitHub App keys must be unencrypted PEM with mode 0600."
            )
        if b"PRIVATE KEY-----" not in header:
            raise AuthError(f"File {path} does not appear to be a valid PEM private key.")
    except Exception:
        os.close(fd)
        raise

    return fd


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def mint_jwt(app_id: str, private_key_path: Path, now: Optional[int] = None) -> str:
    if not NUMERIC_ID_RE.fullmatch(app_id):
        raise AuthError(f"Invalid app_id {app_id!r}.")
    ts = int(time.time()) if now is None else int(now)
    header = json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8")
    payload = json.dumps({"iat": ts - 60, "exp": ts + 480, "iss": app_id}, separators=(",", ":")).encode("utf-8")
    signing_input = f"{_b64url(header)}.{_b64url(payload)}".encode("ascii")

    fd = validate_and_open_private_key(private_key_path)
    try:
        try:
            proc = subprocess.run(
                ["openssl", "dgst", "-sha256", "-sign", f"/dev/fd/{fd}", "-binary", "-passin", "pass:"],
                input=signing_input,
                capture_output=True,
                timeout=OPENSSL_TIMEOUT_SECONDS,
                pass_fds=(fd,),
            )
        except FileNotFoundError as exc:
            raise AuthError("Required 'openssl' executable not found on PATH.") from exc
        except subprocess.TimeoutExpired as exc:
            raise AuthError("Timed out signing JWT with openssl.") from exc
    finally:
        os.close(fd)

    if proc.returncode != 0 or not proc.stdout:
        raise AuthError("openssl failed to sign GitHub App JWT.")
    return f"{signing_input.decode('ascii')}.{_b64url(proc.stdout)}"


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(newurl, code, f"HTTP redirect blocked ({code})", headers, fp)


def _api_request(method: str, url: str, headers: dict[str, str], body: Optional[bytes] = None) -> dict:
    opener = urllib.request.build_opener(_NoRedirectHandler())
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with opener.open(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        raise AuthError(f"GitHub API {method} failed with HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise AuthError(f"GitHub API {method} failed: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AuthError("GitHub API returned invalid JSON.") from exc
    if not isinstance(parsed, dict):
        raise AuthError("GitHub API returned unexpected payload.")
    return parsed


def _parse_utc(timestamp: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc
        )
    except ValueError as exc:
        raise AuthError(f"Unexpected expires_at timestamp format: {timestamp!r}") from exc


def _check_no_newlines(value: str, label: str) -> str:
    if "\r" in value or "\n" in value or "\x00" in value:
        raise AuthError(f"Unsafe control character in {label}.")
    return value


def exchange_installation_token(
    app_id: str,
    installation_id: str,
    private_key_path: Path,
) -> tuple[str, str]:
    if not NUMERIC_ID_RE.fullmatch(installation_id):
        raise AuthError(f"Invalid installation_id {installation_id!r}.")
    jwt = mint_jwt(app_id, private_key_path)
    url = f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": USER_AGENT,
    }
    data = _api_request("POST", url, headers=headers, body=b"")
    token = data.get("token")
    expires_at = data.get("expires_at")
    if not isinstance(token, str) or not token or not isinstance(expires_at, str) or not expires_at:
        raise AuthError("GitHub API response missing installation token or expires_at.")
    _check_no_newlines(token, "token")
    _parse_utc(expires_at)
    return token, expires_at


def _ensure_safe_cache_dir(cache_dir: Path) -> None:
    if os.path.lexists(cache_dir):
        st = os.lstat(cache_dir)
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
            raise AuthError(f"Token cache directory {cache_dir} must be a non-symlink directory.")
        if st.st_uid != os.geteuid():
            raise AuthError(f"Token cache directory {cache_dir} is not owned by the current user.")
        if (st.st_mode & 0o077) != 0:
            os.chmod(cache_dir, 0o700)
        return
    cache_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(cache_dir, 0o700)


def _cache_file_path(cfg: BotConfig, installation_id: str, env: Mapping[str, str]) -> Path:
    return _cache_dir(env) / f"{cfg.app_id}-{installation_id}.json"


def _read_cached_token(path: Path) -> Optional[str]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags)
    except OSError:
        return None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid() or (st.st_mode & 0o077) != 0:
            return None
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            data = json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    finally:
        if fd >= 0:
            os.close(fd)

    if not isinstance(data, dict):
        return None
    token = data.get("token")
    expires_at = data.get("expires_at")
    if not isinstance(token, str) or not token or not isinstance(expires_at, str):
        return None
    if "\r" in token or "\n" in token or "\x00" in token:
        return None
    try:
        exp = _parse_utc(expires_at)
    except AuthError:
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    if (exp - now).total_seconds() < CACHE_MARGIN_SECONDS:
        return None
    return token


def _write_cached_token(path: Path, token: str, expires_at: str) -> None:
    _ensure_safe_cache_dir(path.parent)
    tmp_path = path.parent / f".{path.name}.{secrets.token_hex(8)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(tmp_path), flags, 0o600)
    try:
        payload = json.dumps({"token": token, "expires_at": expires_at}).encode("utf-8")
        os.write(fd, payload)
        os.fsync(fd)
    except Exception:
        os.close(fd)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    os.close(fd)
    os.replace(tmp_path, path)


def get_installation_token(
    cfg: BotConfig,
    owner: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    no_cache: bool = False,
) -> str:
    active_env = env if env is not None else os.environ
    installation_id = cfg.resolve_installation_id(owner)
    cache_path = _cache_file_path(cfg, installation_id, active_env)

    if not no_cache:
        cached = _read_cached_token(cache_path)
        if cached:
            return cached

    token, expires_at = exchange_installation_token(cfg.app_id, installation_id, cfg.private_key_path)
    if not no_cache:
        _write_cached_token(cache_path, token, expires_at)
    return token


def erase_cached_token(
    cfg: BotConfig,
    owner: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    active_env = env if env is not None else os.environ
    installation_id = cfg.resolve_installation_id(owner)
    cache_path = _cache_file_path(cfg, installation_id, active_env)
    try:
        os.unlink(cache_path)
    except FileNotFoundError:
        pass


def fetch_bot_user_id(app_slug: str, token: str) -> str:
    encoded = urllib.parse.quote(f"{app_slug}[bot]", safe="")
    url = f"{GITHUB_API_BASE}/users/{encoded}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": USER_AGENT,
    }
    data = _api_request("GET", url, headers=headers)
    user_id = data.get("id")
    if not isinstance(user_id, int):
        raise AuthError(f"GitHub API did not return a numeric user id for {app_slug}[bot].")
    return str(user_id)


def _extract_owner_from_repo_spec(spec: str) -> Optional[str]:
    text = spec.strip()
    if text.startswith("https://github.com/"):
        text = text[len("https://github.com/"):]
    elif text.startswith("github.com/"):
        text = text[len("github.com/"):]
    text = text.lstrip("/")
    if "/" not in text:
        return None
    owner = text.split("/", 1)[0].strip()
    return owner or None


def _extract_owner_from_gh_args(args: list[str]) -> Optional[str]:
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "--":
            break
        if arg in ("-R", "--repo") and idx + 1 < len(args):
            return _extract_owner_from_repo_spec(args[idx + 1])
        if arg.startswith("--repo="):
            return _extract_owner_from_repo_spec(arg.split("=", 1)[1])
        if arg.startswith("-R") and len(arg) > 2:
            return _extract_owner_from_repo_spec(arg[2:])
        idx += 1
    return None


def _detect_origin_remote(cwd: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    if res.returncode != 0:
        return None, None
    url = res.stdout.strip()
    if url.startswith("https://github.com/"):
        owner = _extract_owner_from_repo_spec(url)
        return owner, url
    if url.startswith("git@github.com:"):
        rest = url[len("git@github.com:"):]
        owner = rest.split("/", 1)[0].strip() or None
        return owner, url
    return None, url


def _build_git_credential_helper(cfg: BotConfig) -> str:
    argv = [sys.executable, str(Path(__file__).resolve()), "git-credential"]
    if cfg.explicit_config:
        argv.extend(["--config", str(cfg.config_path)])
    else:
        argv.extend(["--profile", cfg.profile])
    return "!" + shlex.join(argv)


def _append_git_configs(env: dict[str, str], entries: list[tuple[str, str]]) -> None:
    raw_count = env.get("GIT_CONFIG_COUNT")
    if raw_count is None or raw_count == "":
        count = 0
    else:
        try:
            count = int(raw_count)
        except ValueError as exc:
            raise AuthError(f"Malformed GIT_CONFIG_COUNT={raw_count!r} in environment.") from exc
        if count < 0:
            raise AuthError(f"Negative GIT_CONFIG_COUNT={raw_count!r} in environment.")
    for key, value in entries:
        env[f"GIT_CONFIG_KEY_{count}"] = key
        env[f"GIT_CONFIG_VALUE_{count}"] = value
        count += 1
    env["GIT_CONFIG_COUNT"] = str(count)


def run_git_credential(
    cfg: BotConfig,
    action: str,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    env: Optional[Mapping[str, str]] = None,
) -> int:
    attrs: dict[str, str] = {}
    for line in stdin:
        stripped = line.rstrip("\r\n")
        if not stripped:
            break
        key, sep, value = stripped.partition("=")
        if sep:
            attrs[key] = value

    if attrs.get("protocol", "").lower() != "https" or attrs.get("host", "").lower() != "github.com":
        return 0

    owner: Optional[str] = None
    raw_path = attrs.get("path", "").lstrip("/")
    if raw_path:
        owner = raw_path.split("/", 1)[0] or None

    if action == "get":
        token = _check_no_newlines(get_installation_token(cfg, owner=owner, env=env), "token")
        stdout.write(f"username=x-access-token\npassword={token}\n")
        return 0
    if action == "erase":
        erase_cached_token(cfg, owner=owner, env=env)
        return 0
    if action == "store":
        return 0
    raise AuthError(f"Unsupported git-credential action: {action!r}")


def run_git_env(cfg: BotConfig, stdout: TextIO = sys.stdout) -> int:
    pairs = (
        ("GIT_AUTHOR_NAME", _check_no_newlines(cfg.bot_name, "GIT_AUTHOR_NAME")),
        ("GIT_AUTHOR_EMAIL", _check_no_newlines(cfg.bot_email, "GIT_AUTHOR_EMAIL")),
        ("GIT_COMMITTER_NAME", _check_no_newlines(cfg.bot_name, "GIT_COMMITTER_NAME")),
        ("GIT_COMMITTER_EMAIL", _check_no_newlines(cfg.bot_email, "GIT_COMMITTER_EMAIL")),
    )
    for key, value in pairs:
        stdout.write(f"export {key}={shlex.quote(value)}\n")
    return 0


def run_exec(
    cfg: BotConfig,
    cmd: list[str],
    owner: Optional[str] = None,
    with_gh_token: Optional[bool] = None,
    no_git_credential: bool = False,
    env: Optional[Mapping[str, str]] = None,
) -> int:
    if not cmd:
        raise AuthError("exec requires a command after '--'.")
    child_env = dict(env if env is not None else os.environ)
    child_env["GIT_AUTHOR_NAME"] = _check_no_newlines(cfg.bot_name, "GIT_AUTHOR_NAME")
    child_env["GIT_AUTHOR_EMAIL"] = _check_no_newlines(cfg.bot_email, "GIT_AUTHOR_EMAIL")
    child_env["GIT_COMMITTER_NAME"] = _check_no_newlines(cfg.bot_name, "GIT_COMMITTER_NAME")
    child_env["GIT_COMMITTER_EMAIL"] = _check_no_newlines(cfg.bot_email, "GIT_COMMITTER_EMAIL")

    if not no_git_credential:
        helper_cmd = _build_git_credential_helper(cfg)
        _append_git_configs(
            child_env,
            [
                ("credential.https://github.com.useHttpPath", "true"),
                ("credential.https://github.com.helper", ""),
                ("credential.https://github.com.helper", helper_cmd),
            ],
        )

    is_gh = Path(cmd[0]).name == "gh"
    need_token = is_gh if with_gh_token is None else with_gh_token
    if need_token:
        gh_host = child_env.get("GH_HOST", "").strip()
        if gh_host and gh_host.lower() != "github.com":
            raise AuthError(
                f"Refusing to inject GitHub.com App token when GH_HOST={gh_host!r}."
            )
        resolved_owner = owner or child_env.get("ARTIFICE_GH_APP_OWNER")
        if not resolved_owner and is_gh:
            resolved_owner = _extract_owner_from_gh_args(cmd[1:])
        if not resolved_owner and cfg.installations:
            resolved_owner, _ = _detect_origin_remote()
        token = get_installation_token(cfg, owner=resolved_owner, env=child_env)
        child_env["GH_TOKEN"] = token

    proc = subprocess.run(cmd, env=child_env)
    return proc.returncode


def run_check(
    cfg: BotConfig,
    owner: Optional[str] = None,
    live: bool = False,
    env: Optional[Mapping[str, str]] = None,
    stream: TextIO = sys.stdout,
) -> int:
    fd = validate_and_open_private_key(cfg.private_key_path)
    os.close(fd)

    try:
        openssl_proc = subprocess.run(["openssl", "version"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuthError(f"openssl check failed: {exc}") from exc
    if openssl_proc.returncode != 0:
        raise AuthError("openssl version exited non-zero.")

    installation_id = cfg.resolve_installation_id(owner)
    stream.write(f"Profile: {cfg.profile} ({cfg.config_path})\n")
    stream.write(f"Bot identity: {cfg.bot_name} <{cfg.bot_email}>\n")
    stream.write(f"App ID: {cfg.app_id} | Installation ID: {installation_id}\n")
    stream.write(f"Private key: {cfg.private_key_path} (mode 0600, outside Git repo)\n")

    if cfg.bot_user_id == cfg.app_id:
        stream.write(
            "WARNING: bot_user_id equals app_id; verify via `gh api users/<slug>[bot] --jq .id`.\n"
        )

    _, remote_url = _detect_origin_remote()
    if remote_url and (remote_url.startswith("git@") or remote_url.startswith("ssh://")):
        stream.write(
            f"WARNING: origin remote uses SSH ({remote_url}); GitHub App tokens require HTTPS remotes.\n"
        )

    if live:
        token = get_installation_token(cfg, owner=owner, env=env, no_cache=True)
        live_user_id = fetch_bot_user_id(cfg.app_slug, token)
        if live_user_id != cfg.bot_user_id:
            raise AuthError(
                f"Configured bot_user_id ({cfg.bot_user_id}) does not match GitHub's {cfg.bot_name} id ({live_user_id})."
            )
        stream.write("Live verification: OK (installation token minted and bot user ID matched).\n")
    else:
        stream.write("Offline verification: OK.\n")
    return 0


def _add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="Explicit path to a GitHub App profile JSON file")
    parser.add_argument("--profile", help="Named profile under ~/.config/artifice/github-apps/<profile>.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_token = sub.add_parser("token", help="Mint or read cached installation token")
    _add_common_flags(p_token)
    p_token.add_argument("--owner", help="Repository owner/org for multi-installation lookup")
    p_token.add_argument("--no-cache", action="store_true", help="Bypass token cache and mint fresh token")

    p_cred = sub.add_parser("git-credential", help="Git credential.helper protocol handler")
    _add_common_flags(p_cred)
    p_cred.add_argument("action", choices=("get", "store", "erase"))

    p_env = sub.add_parser("git-env", help="Emit shell export lines for bot GIT_AUTHOR_*/GIT_COMMITTER_*")
    _add_common_flags(p_env)

    p_exec = sub.add_parser("exec", help="Execute a command with bot Git identity and optional GH_TOKEN")
    _add_common_flags(p_exec)
    p_exec.add_argument("--owner", help="Repository owner/org for multi-installation lookup")
    tok_group = p_exec.add_mutually_exclusive_group()
    tok_group.add_argument("--with-gh-token", action="store_true", help="Always mint and inject GH_TOKEN")
    tok_group.add_argument("--no-gh-token", action="store_true", help="Never mint or inject GH_TOKEN")
    p_exec.add_argument("--no-git-credential", action="store_true", help="Do not inject GIT_CONFIG_* credential helper")
    p_exec.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute (prefix with '--')")

    p_check = sub.add_parser("check", help="Validate config, private key invariants, and optionally live auth")
    _add_common_flags(p_check)
    p_check.add_argument("--owner", help="Repository owner/org for multi-installation lookup")
    p_check.add_argument("--live", action="store_true", help="Mint a live token and verify bot user ID against GitHub")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        cfg = load_config(config_path=args.config, profile=args.profile)
        if args.command == "token":
            owner = args.owner or os.environ.get("ARTIFICE_GH_APP_OWNER")
            token = get_installation_token(cfg, owner=owner, no_cache=args.no_cache)
            sys.stdout.write(token + "\n")
            return 0
        if args.command == "git-credential":
            return run_git_credential(cfg, args.action)
        if args.command == "git-env":
            return run_git_env(cfg)
        if args.command == "exec":
            cmd = list(args.cmd)
            if cmd and cmd[0] == "--":
                cmd = cmd[1:]
            with_gh: Optional[bool] = None
            if args.with_gh_token:
                with_gh = True
            elif args.no_gh_token:
                with_gh = False
            return run_exec(
                cfg,
                cmd=cmd,
                owner=args.owner,
                with_gh_token=with_gh,
                no_git_credential=args.no_git_credential,
            )
        if args.command == "check":
            owner = args.owner or os.environ.get("ARTIFICE_GH_APP_OWNER")
            return run_check(cfg, owner=owner, live=args.live)
    except AuthError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
