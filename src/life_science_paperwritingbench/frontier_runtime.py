from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRONTIER_REGISTRY_PATH = REPO_ROOT / "configs" / "models" / "frontier_registry_v1.json"
BACKEND_OPENAI_COMPATIBLE = "openai_compatible_api"
BACKEND_ANTHROPIC = "anthropic_api"
BACKEND_VLLM = "vllm_http"
VALID_BACKENDS = {BACKEND_OPENAI_COMPATIBLE, BACKEND_ANTHROPIC, BACKEND_VLLM}
VALID_ROLE_ELIGIBILITY = {"submitter", "judge", "both"}
VALID_JUDGE_POLICIES = {"not_applicable", "official", "diagnostic_only", "experimental"}


def default_frontier_registry_path() -> Path:
    return DEFAULT_FRONTIER_REGISTRY_PATH


def _safe_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off", ""}:
        return False
    return default


def _strip_unquoted_shell_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    result_chars = []
    for char in value:
        if escaped:
            result_chars.append(char)
            escaped = False
            continue
        if char == "\\" and not in_single:
            escaped = True
            result_chars.append(char)
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            result_chars.append(char)
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            result_chars.append(char)
            continue
        if char == "#" and not in_single and not in_double:
            break
        result_chars.append(char)
    return "".join(result_chars).rstrip()


def load_api_keys(path: Path) -> Dict[str, str]:
    keys: Dict[str, str] = {}
    if not path.exists():
        return keys
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        cleaned_value = _strip_unquoted_shell_comment(value.strip())
        keys[name.strip()] = cleaned_value.strip().strip('"').strip("'")
    return keys


def _entry_supports_role(entry: Mapping[str, Any], role: Optional[str]) -> bool:
    if role is None:
        return True
    eligibility = str(entry.get("role_eligibility", "")).strip()
    if eligibility == "both":
        return role in {"submitter", "judge"}
    return eligibility == role


def _flavor_for_backend(backend_type: str) -> str:
    if backend_type == BACKEND_ANTHROPIC:
        return "anthropic"
    return "openai"


def _apply_runtime_overrides(entry: Dict[str, Any], env: Mapping[str, str]) -> Dict[str, Any]:
    overridden = dict(entry)
    endpoint_env = str(overridden.get("endpoint_env", "")).strip()
    if endpoint_env and env.get(endpoint_env):
        overridden["endpoint"] = env[endpoint_env]
    request_model_env = str(overridden.get("request_model_env", "")).strip()
    if request_model_env and env.get(request_model_env):
        overridden["request_model"] = env[request_model_env]
    model_version_note_env = str(overridden.get("model_version_note_env", "")).strip()
    if model_version_note_env and env.get(model_version_note_env):
        overridden["model_version_note"] = env[model_version_note_env]
    return overridden


def _validate_registry_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
    model_label = str(entry.get("model_label", "")).strip()
    if not model_label:
        raise ValueError("registry entry missing model_label")
    backend_type = str(entry.get("backend_type", "")).strip()
    if backend_type not in VALID_BACKENDS:
        raise ValueError(f"registry entry {model_label} has invalid backend_type: {backend_type}")
    role_eligibility = str(entry.get("role_eligibility", "")).strip()
    if role_eligibility not in VALID_ROLE_ELIGIBILITY:
        raise ValueError(
            f"registry entry {model_label} has invalid role_eligibility: {role_eligibility}"
        )
    judge_policy = str(entry.get("judge_policy", "not_applicable")).strip()
    if judge_policy not in VALID_JUDGE_POLICIES:
        raise ValueError(f"registry entry {model_label} has invalid judge_policy: {judge_policy}")
    normalized = dict(entry)
    normalized["model_label"] = model_label
    normalized["backend_type"] = backend_type
    normalized["role_eligibility"] = role_eligibility
    normalized["judge_policy"] = judge_policy
    normalized["endpoint"] = str(normalized.get("endpoint", "")).strip()
    normalized["api_key_env"] = str(normalized.get("api_key_env", "")).strip()
    normalized["request_model"] = str(normalized.get("request_model", "")).strip()
    normalized["family_bias_group"] = str(normalized.get("family_bias_group", "")).strip()
    normalized["token_param"] = str(normalized.get("token_param", "max_tokens")).strip() or "max_tokens"
    normalized["omit_temperature"] = _safe_bool(normalized.get("omit_temperature", False))
    normalized["temperature"] = float(normalized.get("temperature", 0.2))
    normalized["max_tokens"] = int(normalized.get("max_tokens", 1200))
    normalized["provider_name"] = str(normalized.get("provider_name", "")).strip()
    normalized["execution_target"] = str(normalized.get("execution_target", "")).strip()
    normalized["model_version_note"] = str(normalized.get("model_version_note", "")).strip()
    default_submitter_track = (
        "hosted_frontier" if role_eligibility in {"submitter", "both"} else "not_applicable"
    )
    normalized["submitter_track"] = (
        str(normalized.get("submitter_track", default_submitter_track)).strip()
        or default_submitter_track
    )
    normalized["flavor"] = _flavor_for_backend(backend_type)
    return normalized


def load_frontier_registry(
    path: Optional[Path | str] = None,
    *,
    role: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    registry_path = Path(path) if path is not None else DEFAULT_FRONTIER_REGISTRY_PATH
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = payload.get("models", [])
    if not isinstance(rows, list):
        raise ValueError("frontier registry must contain a 'models' list")
    env_values = env or os.environ
    registry: Dict[str, Dict[str, Any]] = {}
    for raw in rows:
        entry = _apply_runtime_overrides(_validate_registry_entry(raw), env_values)
        if not _entry_supports_role(entry, role):
            continue
        label = entry["model_label"]
        if label in registry:
            raise ValueError(f"duplicate model_label in frontier registry: {label}")
        registry[label] = entry
    return registry


def load_frontier_model(
    model_label: str,
    *,
    registry_path: Optional[Path | str] = None,
    role: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    registry = load_frontier_registry(registry_path, role=role, env=env)
    if model_label not in registry:
        available = ", ".join(sorted(registry))
        raise KeyError(f"unknown model_label '{model_label}'. Available: {available}")
    return registry[model_label]


def model_labels_for_role(
    role: str,
    *,
    registry_path: Optional[Path | str] = None,
) -> Tuple[str, ...]:
    return tuple(sorted(load_frontier_registry(registry_path, role=role).keys()))


def default_model_label_for_role(
    role: str,
    *,
    preferred_label: Optional[str] = None,
    registry_path: Optional[Path | str] = None,
) -> str:
    labels = model_labels_for_role(role, registry_path=registry_path)
    if not labels:
        raise ValueError(f"no models available for role '{role}'")
    if preferred_label and preferred_label in labels:
        return preferred_label
    return labels[0]


def default_canary_models(*, registry_path: Optional[Path | str] = None) -> Tuple[str, ...]:
    registry = load_frontier_registry(registry_path)
    labels = []
    for label, entry in registry.items():
        if entry["backend_type"] == BACKEND_VLLM:
            continue
        if entry["judge_policy"] == "official" or _entry_supports_role(entry, "submitter"):
            labels.append(label)
    preferred_order = (
        "deepseek-chat",
        "gpt-4o-mini",
        "gemini-2.5-flash",
        "claude-haiku-4-5",
        "claude-sonnet-4-6",
        "gpt-5.4-mini",
        "gemini-2.5-pro",
    )
    seen = set(labels)
    ordered = [label for label in preferred_order if label in seen]
    ordered.extend(sorted(label for label in labels if label not in ordered))
    return tuple(ordered)


def registry_entry_provenance(entry: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "backend_type": entry.get("backend_type"),
        "provider_name": entry.get("provider_name"),
        "execution_target": entry.get("execution_target"),
        "model_version_note": entry.get("model_version_note"),
        "family_bias_group": entry.get("family_bias_group"),
        "role_eligibility": entry.get("role_eligibility"),
        "judge_policy": entry.get("judge_policy"),
        "submitter_track": entry.get("submitter_track"),
        "request_model": entry.get("request_model"),
    }


def resolve_api_key(entry: Mapping[str, Any], keys: Mapping[str, str]) -> Optional[str]:
    api_key_env = str(entry.get("api_key_env", "")).strip()
    if not api_key_env:
        return None
    return os.environ.get(api_key_env) or keys.get(api_key_env)


def build_openai_compatible_payload(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    temperature: float,
    max_tokens: int,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": provider["request_model"],
        "messages": [{"role": "user", "content": prompt}],
    }
    if not provider.get("omit_temperature"):
        payload["temperature"] = temperature
    payload[str(provider.get("token_param", "max_tokens"))] = max_tokens
    return payload


def build_anthropic_payload(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    temperature: float,
    max_tokens: int,
) -> Dict[str, Any]:
    return {
        "model": provider["request_model"],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }


def _post_json(
    url: str,
    *,
    payload: Mapping[str, Any],
    headers: Mapping[str, str],
    timeout: int,
) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=dict(headers),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_openai_compatible_text(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    choice = choices[0] or {}
    message = choice.get("message") or {}
    content = message.get("content", choice.get("text", ""))
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, Mapping):
                text = item.get("text")
                if text:
                    parts.append(str(text))
        return "".join(parts)
    return str(content or "")


def _extract_anthropic_text(payload: Mapping[str, Any]) -> str:
    content = payload.get("content") or []
    parts = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, Mapping) and item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "".join(parts)


def _normalize_usage(payload: Mapping[str, Any]) -> Dict[str, Optional[int]]:
    usage = payload.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = int(prompt_tokens) + int(completion_tokens)
    return {
        "prompt_tokens": int(prompt_tokens) if prompt_tokens is not None else None,
        "completion_tokens": int(completion_tokens) if completion_tokens is not None else None,
        "input_tokens": int(prompt_tokens) if prompt_tokens is not None else None,
        "output_tokens": int(completion_tokens) if completion_tokens is not None else None,
        "total_tokens": int(total_tokens) if total_tokens is not None else None,
    }


def call_openai_compatible(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    api_key: Optional[str],
    temperature: float = 0.2,
    max_tokens: int = 1200,
    timeout: int = 120,
) -> Dict[str, Any]:
    payload = build_openai_compatible_payload(
        prompt,
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    raw = _post_json(
        str(provider["endpoint"]),
        payload=payload,
        headers=headers,
        timeout=timeout,
    )
    return {
        "output_text": _extract_openai_compatible_text(raw),
        "usage": _normalize_usage(raw),
        "raw": raw,
    }


def call_anthropic(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    api_key: str,
    temperature: float = 0.2,
    max_tokens: int = 1200,
    timeout: int = 120,
) -> Dict[str, Any]:
    payload = build_anthropic_payload(
        prompt,
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    raw = _post_json(
        str(provider["endpoint"]),
        payload=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        timeout=timeout,
    )
    return {
        "output_text": _extract_anthropic_text(raw),
        "usage": _normalize_usage(raw),
        "raw": raw,
    }


def call_model(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    api_key: Optional[str],
    temperature: float = 0.2,
    max_tokens: int = 1200,
    timeout: int = 120,
) -> Dict[str, Any]:
    if provider.get("backend_type") == BACKEND_ANTHROPIC or provider.get("flavor") == "anthropic":
        if not api_key:
            raise RuntimeError(f"missing {provider.get('api_key_env') or 'API key'}")
        return call_anthropic(
            prompt,
            provider=provider,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    return call_openai_compatible(
        prompt,
        provider=provider,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


def call_model_with_retry(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    api_key: Optional[str],
    temperature: float,
    max_tokens: int,
    attempts: int = 3,
    backoff_seconds: float = 2.0,
    timeout: int = 120,
) -> Dict[str, Any]:
    last_error: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            return call_model(
                prompt,
                provider=provider,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, RuntimeError) as exc:
            last_error = exc
            if attempt >= attempts:
                break
            time.sleep(backoff_seconds * attempt)
    raise RuntimeError(f"provider call failed after {attempts} attempts: {last_error}")
