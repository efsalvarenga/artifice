#!/usr/bin/env python3
"""Metadata-only model inventory and exact, capability-based selection."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
import hashlib
import http.client
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import threading
from time import monotonic
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime, timezone


DEFAULT_HOST = "http://localhost:11434"
DISCOVERY_TIMEOUT = 15.0
OPERATION_TIMEOUT = 3.0
MAX_WORKERS = 4
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
TASKS = ("code", "logic", "fim", "tdd", "prose", "docs", "adr", "architecture", "utility")
CAPABILITIES = ("chat", "tools", "fim", "vision")
MODES = ("bounded_chat", "cli_agent")
LOCAL_ALIASES = ("local", "ollama", "local-code")

DEFAULT_MISTRAL_MODELS = (
    {"alias": "large", "name": "mistral-large-4", "display_name": "Mistral Large", "context": 1048576},
    {"alias": "codestral", "name": "codestral-latest", "display_name": "Codestral", "context": 262144},
    {"alias": "small", "name": "mistral-small-latest", "display_name": "Mistral Small", "context": 262144},
    {"alias": "ministral", "name": "ministral-8b-latest", "display_name": "Ministral 8B", "context": 131072},
)


class SelectionError(ValueError):
    """An unavailable, ambiguous or incompatible explicit selection."""

    def __init__(self, message: str, diagnostics: list = None, returncode: int = 2):
        super().__init__(message)
        self.diagnostics = list(diagnostics or [])
        self.returncode = returncode


def find_vibe() -> str:
    override = os.environ.get("VIBE_BIN")
    if override is not None:
        return override if os.path.isfile(override) and os.access(override, os.X_OK) else ""
    found = shutil.which("vibe")
    if found:
        return found
    for candidate in (
        os.path.expanduser("~/.local/bin/vibe"),
        "/opt/homebrew/bin/vibe",
        "/usr/local/bin/vibe",
    ):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return ""


def read_vibe_models(workdir: str = None) -> list:
    """Read configured models from user settings or fallback to canonical defaults."""
    user_config = Path(os.environ.get("GEMINI_VIBE_MODELS", Path.home() / ".gemini" / "config" / "vibe_models.json")).expanduser()
    if user_config.is_file():
        try:
            items = json.loads(user_config.read_text(encoding="utf-8"))
            if isinstance(items, list) and items:
                normalized = []
                for entry in items:
                    if isinstance(entry, dict) and entry.get("name"):
                        normalized.append({
                            "alias": entry.get("alias", entry["name"]),
                            "name": entry["name"],
                            "display_name": entry.get("display_name", entry["name"]),
                            "context": entry.get("context", 131072),
                        })
                if normalized:
                    return normalized
        except (OSError, json.JSONDecodeError):
            pass

    vibe_home = Path(os.environ.get("VIBE_HOME", Path.home() / ".vibe")).expanduser()
    config_file = vibe_home / "config.toml"
    discovered = []
    if config_file.is_file():
        try:
            content = config_file.read_text(encoding="utf-8")
            sections = re.findall(r"(?ms)^\[models\.([a-zA-Z0-9_\.\-]+)\]\s*(.*?)(?=\n\[|\Z)", content)
            for alias, body in sections:
                name_match = re.search(r'(?m)^\s*name\s*=\s*["\']([^"\']+)["\']', body)
                name = name_match.group(1).strip() if name_match else alias
                disp_match = re.search(r'(?m)^\s*display_name\s*=\s*["\']([^"\']+)["\']', body)
                disp = disp_match.group(1).strip() if disp_match else name
                is_codestral = "codestral" in name.lower() or "codestral" in alias.lower()
                ctx = 262144 if is_codestral else (32768 if "fast" in alias.lower() else 131072)
                discovered.append({"alias": alias, "name": name, "display_name": disp, "context": ctx})
        except OSError:
            pass
    if not discovered:
        discovered = [dict(m) for m in DEFAULT_MISTRAL_MODELS]
    return discovered


def endpoint(host: str = None) -> tuple:
    """Return a credential-free canonical endpoint and transport locality."""
    value = os.environ.get("OLLAMA_HOST", DEFAULT_HOST) if host is None else host
    if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
        raise ValueError("OLLAMA_HOST must be a non-empty HTTP(S) URL.")
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("OLLAMA_HOST must be an absolute HTTP(S) URL.")
    if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        raise ValueError("OLLAMA_HOST must not contain credentials, a query or a fragment.")
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("OLLAMA_HOST contains an invalid port.") from None
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("OLLAMA_HOST contains an invalid port.")
    hostname = parsed.hostname.lower()
    if hostname in ("localhost", "localhost."):
        hostname = "127.0.0.1"
    try:
        loopback = ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        loopback = False
    authority = "[" + hostname + "]" if ":" in hostname else hostname
    if port is not None:
        authority += ":" + str(port)
    return urlunsplit((parsed.scheme, authority, parsed.path.rstrip("/"), "", "")), (
        "loopback" if loopback else "remote"
    )


def request_json(path: str, data: dict = None, timeout: float = OPERATION_TIMEOUT, host: str = None) -> tuple:
    """Read JSON directly, without proxies/redirects, under a total request timer."""
    base, locality = endpoint(host)
    if locality != "loopback":
        raise ValueError("This Ollama adapter requires a configured loopback endpoint.")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Request timeout must be positive.")
    parsed = urlsplit(base)
    connection_type = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = connection_type(parsed.hostname, parsed.port, timeout=timeout)
    # A deadline-closed socket must not be reopened by HTTPConnection.send().
    connection.auto_open = 0
    response = None
    active_socket = [None]
    expired = threading.Event()
    start = monotonic()

    def abort():
        expired.set()
        current = active_socket[0] or connection.sock
        if current is not None:
            try:
                current.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        connection.close()

    timer = threading.Timer(timeout, abort)
    timer.daemon = True
    timer.start()
    try:
        connection.connect()
        active_socket[0] = connection.sock
        if expired.is_set():
            raise TimeoutError
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        connection.request("POST" if body is not None else "GET", parsed.path + path, body=body, headers=headers)
        response = connection.getresponse()
        if response.status != 200:
            return response.status, {"error": "HTTP " + str(response.status)}, monotonic() - start
        chunks = bytearray()
        while True:
            chunk = response.read(65536)
            if not chunk:
                break
            chunks.extend(chunk)
            if len(chunks) > MAX_RESPONSE_BYTES:
                return 0, {"error": "Metadata response exceeds the size limit."}, monotonic() - start
        if expired.is_set():
            raise TimeoutError
        result = json.loads(chunks.decode("utf-8"))
        return 200, result, monotonic() - start
    except (OSError, http.client.HTTPException, ValueError, UnicodeError) as error:
        message = "Request timed out." if expired.is_set() or isinstance(error, TimeoutError) else (
            "Invalid JSON response." if isinstance(error, (ValueError, UnicodeError)) else "HTTP request failed."
        )
        return 0, {"error": message}, monotonic() - start
    finally:
        timer.cancel()
        if response is not None:
            response.close()
        connection.close()


def local_policy(local_only: bool = False, workdir: str = None) -> bool:
    if type(local_only) is not bool:
        raise ValueError("Local-only policy must be a boolean.")
    if workdir is not None and (
        not isinstance(workdir, (str, os.PathLike)) or not str(workdir).strip()
    ):
        raise ValueError("Working directory must be non-empty.")
    directory = Path(os.getcwd() if workdir is None else workdir).resolve()
    if not directory.is_dir():
        raise ValueError("Working directory must be an existing directory.")
    required = local_only
    for current in (directory, *directory.parents):
        for policy in (current / "AGENTS.md", current / ".agents" / "AGENTS.md"):
            try:
                metadata = policy.stat()
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 65536:
                raise ValueError("Privacy policy must be a regular file of at most 64 KiB.")
            text = policy.read_text(encoding="utf-8")
            policy_text = text.replace("*", "").replace("`", "")
            if re.search(r"\b(?:Privacy\s*:\s*on-device|Review\s*:\s*local-only)\b",
                         policy_text, re.IGNORECASE):
                required = True
        if (current / ".git").exists():
            break
    return required


def requirements(task: str = "code", mode: str = "bounded_chat", required_capabilities=None,
                 min_context: int = None, accept_unknown: bool = False, local_only: bool = False) -> dict:
    if task not in TASKS or mode not in MODES:
        raise ValueError("Unknown task or execution mode.")
    if min_context is not None and (type(min_context) is not int or min_context <= 0):
        raise ValueError("Minimum context must be a positive integer.")
    if type(accept_unknown) is not bool or type(local_only) is not bool:
        raise ValueError("Privacy and uncertainty permissions must be booleans.")
    if required_capabilities is None:
        required_capabilities = []
    if not isinstance(required_capabilities, (list, tuple, set)) or any(
        capability not in CAPABILITIES for capability in required_capabilities
    ):
        raise ValueError("Unknown required capability.")
    capabilities = set(required_capabilities) | {"chat"}
    if mode == "cli_agent":
        capabilities.add("tools")
    return {
        "task": task, "mode": mode,
        "required_capabilities": [capability for capability in CAPABILITIES if capability in capabilities],
        "min_context": min_context, "accept_unknown": accept_unknown, "local_only": local_only,
    }


def role_override(task: str, model: str = None):
    if model is not None:
        if not _name(model):
            raise SelectionError("An explicit model must be non-empty.")
        return model
    variable = None
    if task in ("code", "logic", "fim", "tdd"):
        variable = "ARTIFICE_CODE_MODEL"
    elif task in ("prose", "docs", "adr", "architecture"):
        variable = "ARTIFICE_PROSE_MODEL"
    value = os.environ.get(variable) if variable else None
    if value is not None and not _name(value):
        raise SelectionError(str(variable) + " is empty or invalid.")
    return value


def _name(value) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not any(ord(char) < 32 for char in value)


def _positive(value) -> bool:
    return type(value) is int and value > 0


def _diagnostic(code: str, message: str, stage: str, model: str = None,
                provider: str = "ollama", severity: str = "error") -> dict:
    return {
        "provider": provider, "candidate": model, "stage": stage,
        "severity": severity, "code": code, "message": message,
    }


def _backing(*records) -> bool:
    return any(
        isinstance(record, dict) and any(record.get(key) for key in ("remote_host", "remote_model", "cloud"))
        for record in records
    )


def _candidate(tag: dict, base: str) -> dict:
    name = tag["name"]
    digest = tag.get("digest") if _name(tag.get("digest")) else None
    size = tag.get("size") if type(tag.get("size")) is int and tag["size"] >= 0 else None
    locality = "hosted" if _backing(tag, tag.get("details")) else (
        "on_device" if digest is not None and size is not None and size > 0 else "unknown"
    )
    identity = ["ollama", "default", name]
    aliases = [name]
    if _name(tag.get("model")) and tag["model"] != name:
        aliases.append(tag["model"])
    candidate = {
        "identity": identity, "reference": "/".join(identity), "model_id": name,
        "aliases": sorted(aliases), "execution_ref": name,
        "evidence": ["installed" if locality == "on_device" else "configured"],
        "dispatch_state": "unverified", "execution_modes": ["bounded_chat"],
        "execution_locality": locality,
        "capabilities": {key: None for key in CAPABILITIES}, "capability_sources": {},
        "context_tokens": None, "context_source": None, "size_bytes": size,
        "parameter_size": None, "quantisation": None, "resident": None,
        "digest": digest,
    }
    candidate["identity_fingerprint"] = fingerprint(candidate, base)
    return candidate


def fingerprint(candidate: dict, base: str) -> str:
    return hashlib.sha256(json.dumps({
        "identity": candidate["identity"], "endpoint": base,
        "execution_ref": candidate["execution_ref"], "digest": candidate["digest"],
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _enrich(candidate: dict, body, diagnostics: list) -> bool:
    if not isinstance(body, dict):
        diagnostics.append(_diagnostic("INVALID_MODEL_METADATA", "Model metadata must be an object.",
                                       "show", candidate["model_id"]))
        return False
    complete = True
    capabilities = body.get("capabilities")
    if isinstance(capabilities, list) and all(isinstance(item, str) for item in capabilities):
        candidate["capabilities"] = {
            "chat": "completion" in capabilities or "chat" in capabilities,
            "tools": "tools" in capabilities, "vision": "vision" in capabilities,
            "fim": True if "fim" in capabilities else None,
        }
        candidate["capability_sources"] = {
            key: "api/show" if value is not None else None
            for key, value in candidate["capabilities"].items()
        }
        candidate["dispatch_state"] = "selectable"
    else:
        complete = False
        diagnostics.append(_diagnostic("UNKNOWN_CAPABILITIES", "Model capabilities were not reported.",
                                       "show", candidate["model_id"], severity="warning"))
    info = body.get("model_info")
    limits = []
    if isinstance(info, dict):
        architecture = info.get("general.architecture")
        architecture_limit = info.get(str(architecture) + ".context_length")
        if _name(architecture):
            if _positive(architecture_limit):
                limits = [architecture_limit]
        else:
            reported_limits = {value for key, value in info.items()
                               if key.endswith(".context_length") and _positive(value)}
            if len(reported_limits) == 1:
                limits = list(reported_limits)
            elif reported_limits:
                complete = False
                diagnostics.append(_diagnostic(
                    "CONFLICTING_CONTEXT_METADATA", "Context metadata does not identify a unique model capacity.",
                    "show", candidate["model_id"], severity="warning",
                ))
    if limits:
        candidate["context_tokens"] = min(limits)
        candidate["context_source"] = "advertised_maximum"
    parameters = body.get("parameters")
    configured = None
    configured_present = False
    if isinstance(parameters, dict):
        configured_present = "num_ctx" in parameters
        configured = parameters.get("num_ctx")
    elif isinstance(parameters, str):
        values = re.findall(r"(?m)^\s*num_ctx\b([^\n]*)$", parameters)
        configured_present = bool(values)
        if values and all(re.fullmatch(r"[1-9]\d*", value.strip()) for value in values):
            configured = min(int(value.strip()) for value in values)
    if _positive(configured):
        candidate["context_tokens"] = min(limits + [configured]) if limits else configured
        candidate["context_source"] = "configured_limit"
    elif configured_present:
        candidate["context_tokens"] = None
        candidate["context_source"] = "unknown_configured_limit"
        complete = False
        diagnostics.append(_diagnostic("INVALID_CONTEXT_LIMIT", "Configured context capacity is invalid or unknown.",
                                       "show", candidate["model_id"]))
    reported_details = body.get("details")
    if isinstance(reported_details, dict):
        for source, target in (("parameter_size", "parameter_size"), ("quantization_level", "quantisation")):
            if _name(reported_details.get(source)):
                candidate[target] = reported_details[source]
    if _backing(body, reported_details):
        candidate["execution_locality"] = "hosted"
    if candidate["execution_locality"] != "on_device" or candidate.get("identity_conflict"):
        candidate["dispatch_state"] = "unavailable"
    return complete


def discover(local_only: bool = False, workdir: str = None, timeout_sec: float = DISCOVERY_TIMEOUT) -> dict:
    """Enumerate all advertised Ollama identities before bounded enrichment."""
    if not isinstance(timeout_sec, (int, float)) or isinstance(timeout_sec, bool) or not 0 < timeout_sec <= DISCOVERY_TIMEOUT:
        raise ValueError("Discovery timeout must be positive and at most 15 seconds.")
    local_only = local_policy(local_only, workdir)
    base, locality = endpoint()
    if locality != "loopback" and local_only:
        raise ValueError("Local-only policy rejects a remote Ollama endpoint.")
    start = monotonic()
    deadline = start + timeout_sec
    diagnostics = []
    provider = {
        "provider": "ollama", "source_id": "default", "state": "unavailable",
        "locality": locality, "cli_version": None, "catalogue_state": "not_attempted", "access": "unknown",
    }
    hosted = {
        "provider": "mistral", "source_id": "vibe", "state": "disabled" if local_only else "unavailable",
        "locality": "remote", "cli_version": None, "catalogue_state": "not_attempted", "access": "unknown",
    }
    vibe_candidates = []
    vibe_bin = find_vibe() if not local_only else ""
    if not local_only:
        if vibe_bin:
            hosted.update(state="selectable", catalogue_state="complete", access="verified")
            for item in read_vibe_models(workdir=workdir):
                alias = item["alias"]
                name = item["name"]
                disp = item.get("display_name", name)
                is_codestral = "codestral" in name.lower() or "codestral" in alias.lower()
                extra_aliases = []
                if "large" in alias or "large" in name:
                    extra_aliases.extend(["mistral-large", "mistral-large-latest"])
                elif "codestral" in alias or "codestral" in name:
                    extra_aliases.extend(["codestral", "codestral-latest"])
                aliases = sorted(set(([alias] if alias != name else []) + [a for a in extra_aliases if a != name]))
                c = {
                    "identity": ["mistral", "vibe", name],
                    "model_id": name,
                    "reference": "mistral/vibe/" + name,
                    "execution_ref": alias,
                    "aliases": aliases,
                    "display_name": disp,
                    "provider": "mistral",
                    "digest": "vibe-cli-" + name,
                    "size_bytes": None,
                    "resident": True,
                    "capabilities": {
                        "chat": True,
                        "tools": True,
                        "fim": True if is_codestral else None,
                        "vision": None,
                    },
                    "capability_sources": {
                        "chat": "vibe_config",
                        "tools": "vibe_config",
                        "fim": "vibe_config" if is_codestral else None,
                        "vision": None,
                    },
                    "context_tokens": item.get("context", 131072 if not is_codestral else 262144),
                    "context_source": "configured_limit",
                    "quantisation": None,
                    "parameter_size": None,
                    "dispatch_state": "selectable",
                    "execution_locality": "hosted",
                    "execution_modes": ["bounded_chat", "cli_agent"],
                    "identity_conflict": False,
                }
                c["identity_fingerprint"] = fingerprint(c, "vibe")
                vibe_candidates.append(c)
        else:
            diagnostics.append(_diagnostic(
                "VIBE_CLI_UNAVAILABLE", "Vibe CLI was not found; no hosted models were queried.",
                "availability", provider="mistral", severity="info",
            ))
    snapshot = {
        "schema_version": 1, "observed_at": datetime.now(timezone.utc).isoformat(),
        "status": "unavailable",
        "policy": {"local_only": local_only, "hosted_discovery_allowed": not local_only and bool(vibe_bin)},
        "providers": [provider, hosted], "models": [], "host_ram_bytes": None, "diagnostics": diagnostics,
    }
    try:
        pages, page_size = os.sysconf("SC_PHYS_PAGES"), os.sysconf("SC_PAGE_SIZE")
        if not _positive(pages) or not _positive(page_size):
            raise ValueError("Unknown physical RAM")
        snapshot["host_ram_bytes"] = pages * page_size
    except (OSError, ValueError):
        diagnostics.append(_diagnostic("UNKNOWN_HOST_RAM", "Physical RAM was not reported.",
                                       "hardware", severity="info"))
    if locality != "loopback":
        diagnostics.append(_diagnostic("REMOTE_OLLAMA_ENDPOINT", "This phase supports loopback Ollama endpoints only.",
                                       "endpoint"))
        snapshot["models"].extend(vibe_candidates)
        if snapshot["models"]:
            snapshot["status"] = "complete"
        return snapshot

    def fetch(path, data=None):
        remaining = deadline - monotonic()
        if remaining <= 0:
            return 0, {"error": "Discovery deadline reached."}, 0.0
        return request_json(path, data=data, timeout=min(OPERATION_TIMEOUT, remaining), host=base)

    code, body, _ = fetch("/api/tags")
    if code != 200 or not isinstance(body, dict) or not isinstance(body.get("models"), list):
        provider["state"] = "error" if code == 200 else "unavailable"
        diagnostics.append(_diagnostic("OLLAMA_INVENTORY_UNAVAILABLE", "Ollama did not return a valid model roster.",
                                       "tags"))
        snapshot["models"].extend(vibe_candidates)
        if snapshot["models"]:
            snapshot["status"] = "partial"
        return snapshot
    provider.update(state="available", catalogue_state="complete", access="verified")
    partial = False
    models = {}
    for tag in body["models"]:
        if not isinstance(tag, dict) or not _name(tag.get("name")):
            partial = True
            diagnostics.append(_diagnostic("INVALID_MODEL_ENTRY", "An advertised model has no valid identity.", "tags"))
            continue
        candidate = _candidate(tag, base)
        previous = models.get(candidate["model_id"])
        if previous is not None:
            identity_conflict = previous["identity_fingerprint"] != candidate["identity_fingerprint"]
            locality_conflict = previous["execution_locality"] != candidate["execution_locality"]
            if identity_conflict or locality_conflict:
                partial = True
                previous["identity_conflict"] = True
                previous["dispatch_state"] = "unavailable"
                if identity_conflict:
                    diagnostics.append(_diagnostic("MODEL_IDENTITY_CONFLICT", "Duplicate tags have conflicting identities.",
                                                   "tags", candidate["model_id"]))
                if locality_conflict:
                    localities = (previous["execution_locality"], candidate["execution_locality"])
                    previous["execution_locality"] = "hosted" if "hosted" in localities else "unknown"
                    previous["evidence"] = ["configured"]
                    diagnostics.append(_diagnostic(
                        "MODEL_LOCALITY_CONFLICT", "Duplicate tags have conflicting execution locality.",
                        "tags", candidate["model_id"],
                    ))
            else:
                previous["aliases"] = sorted(set(previous["aliases"]) | set(candidate["aliases"]))
            continue
        models[candidate["model_id"]] = candidate
    snapshot["models"] = [models[name] for name in sorted(models)]
    local_models = []
    for candidate in snapshot["models"]:
        if candidate["execution_locality"] == "on_device" and not candidate.get("identity_conflict"):
            local_models.append(candidate)
            continue
        candidate["dispatch_state"] = "unavailable"
        if candidate["execution_locality"] != "on_device":
            unknown = candidate["execution_locality"] == "unknown"
            partial = partial or unknown
            diagnostics.append(_diagnostic(
                "UNKNOWN_EXECUTION_LOCALITY" if unknown else "CLOUD_BACKED_MODEL",
                "Model details were not queried because on-device weights are not verified.",
                "locality", candidate["model_id"], severity="warning" if unknown else "info",
            ))

    code, body, _ = fetch("/api/ps")
    if code == 200 and isinstance(body, dict) and isinstance(body.get("models"), list):
        names = [entry.get("name") for entry in body["models"] if isinstance(entry, dict) and _name(entry.get("name"))]
        valid = len(names) == len(body["models"])
        for candidate in snapshot["models"]:
            candidate["resident"] = True if candidate["model_id"] in names else (False if valid else None)
        if not valid:
            partial = True
            diagnostics.append(_diagnostic("INVALID_RESIDENCY", "Residency contains malformed entries.", "ps"))
    else:
        partial = True
        diagnostics.append(_diagnostic("UNKNOWN_RESIDENCY", "Ollama residency could not be inspected.", "ps"))

    if local_models:
        pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        futures = {}
        try:
            for offset in range(0, len(local_models), MAX_WORKERS):
                if monotonic() >= deadline:
                    raise FuturesTimeoutError
                batch = local_models[offset:offset + MAX_WORKERS]
                futures = {pool.submit(fetch, "/api/show", {"model": model["model_id"]}): model for model in batch}
                for future in as_completed(futures, timeout=max(0.0, deadline - monotonic())):
                    candidate = futures[future]
                    code, body, _ = future.result()
                    if code != 200:
                        partial = True
                        diagnostics.append(_diagnostic("MODEL_METADATA_UNAVAILABLE", "Model detail metadata is unavailable.",
                                                       "show", candidate["model_id"]))
                    elif not _enrich(candidate, body, diagnostics):
                        partial = True
        except FuturesTimeoutError:
            partial = True
            diagnostics.append(_diagnostic("DISCOVERY_TIMEOUT", "Discovery reached its aggregate deadline.", "deadline"))
        finally:
            for future in futures:
                future.cancel()
            pool.shutdown(wait=True, cancel_futures=True)
    if monotonic() >= deadline and any(model["dispatch_state"] == "unverified" for model in snapshot["models"]):
        partial = True
        if not any(item["code"] == "DISCOVERY_TIMEOUT" for item in diagnostics):
            diagnostics.append(_diagnostic("DISCOVERY_TIMEOUT", "Discovery reached its aggregate deadline.", "deadline"))
    provider["catalogue_state"] = "partial" if partial else "complete"
    snapshot["models"].extend(vibe_candidates)
    snapshot["status"] = "partial" if partial else "complete"
    diagnostics.sort(key=lambda item: (item["provider"], item["candidate"] or "", item["stage"], item["code"]))
    return snapshot


def candidate_issues(candidate: dict, task_requirements: dict) -> list:
    issues = []
    if candidate.get("identity_conflict") or candidate.get("dispatch_state") in ("unavailable", "configuration_required"):
        issues.append("Model identity or dispatch support is unavailable.")
    if task_requirements.get("local_only") and candidate.get("execution_locality") != "on_device":
        issues.append("On-device execution locality is required by local policy.")
    elif not task_requirements.get("local_only") and candidate.get("execution_locality") not in ("on_device", "hosted"):
        issues.append("Execution locality is not verified.")
    if task_requirements["mode"] not in candidate.get("execution_modes", []):
        issues.append("The adapter does not support the requested execution mode.")
    capabilities = candidate.get("capabilities", {})
    for capability in task_requirements["required_capabilities"]:
        value = capabilities.get(capability)
        if value is False:
            issues.append("Required capability is unsupported: " + capability + ".")
        elif value is not True and not task_requirements["accept_unknown"]:
            issues.append("Required capability is unknown: " + capability + ".")
    context = candidate.get("context_tokens")
    minimum = task_requirements["min_context"]
    if minimum is not None:
        if context is None and not task_requirements["accept_unknown"]:
            issues.append("Context capacity is unknown.")
        elif context is not None and context < minimum:
            issues.append("Context capacity is below the requested minimum.")
    return issues


def select_candidate(snapshot: dict, provider: str = None, model: str = None,
                     task_requirements: dict = None, expect_identity: str = None) -> dict:
    def reject(message):
        raise SelectionError(message, diagnostics=snapshot.get("diagnostics", []))

    if type(snapshot.get("schema_version")) is not int or snapshot["schema_version"] != 1:
        reject("Unsupported inventory schema version.")
    if provider is not None and provider not in ("ollama", "mistral"):
        reject("Unknown model provider.")
    if model is not None and not _name(model):
        reject("An explicit model must be non-empty.")
    if expect_identity is not None and (
        not isinstance(expect_identity, str) or re.fullmatch(r"[a-f0-9]{64}", expect_identity) is None
    ):
        reject("Expected identity must be a SHA-256 fingerprint.")
    requested = requirements(**task_requirements) if task_requirements is not None else requirements()
    if model is None:
        requested["accept_unknown"] = False
    if requested.get("local_only") and provider == "mistral":
        reject("Local-only policy rejects hosted execution.")
    matches = [
        item for item in snapshot["models"]
        if (provider is None or item["identity"][0] == provider)
        and (model is None or model in (item["model_id"], item["reference"], item["execution_ref"])
             or model in item["aliases"])
    ]
    if model is not None and len(matches) > 1:
        reject("The explicit model reference is ambiguous.")
    eligible = [item for item in matches if not candidate_issues(item, requested)]
    if len(eligible) > 1:
        reject("Several models are compatible; choose an exact model from discovery.")
    if not eligible:
        if matches:
            reject("; ".join(candidate_issues(matches[0], requested)))
        if provider == "mistral":
            reject("No suitable hosted model was found; inspect discovery and select explicitly.")
        reject("No suitable installed model was found; inspect discovery and select explicitly.")
    selected = eligible[0]
    if expect_identity is not None and selected["identity_fingerprint"] != expect_identity:
        reject("Model identity changed after approval; discover and approve it again.")
    return selected


def emit_diagnostics(snapshot: dict, stream) -> None:
    for diagnostic in snapshot["diagnostics"]:
        print(json.dumps(diagnostic, sort_keys=True), file=stream)
