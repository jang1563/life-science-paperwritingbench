#!/usr/bin/env python3
"""Run a low-cost completion-style canary probe across selected models.

The probe does not rely on token log-probabilities. Instead, it asks a model
to continue a partially revealed canary string and checks whether the model
reproduces the full unpublished string exactly.

To avoid leaking canaries further, written artifacts store hashes, lengths,
and match metrics rather than raw canary strings or raw model outputs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from life_science_paperwritingbench import DEFAULT_CANARY_PREFIX, generate_canary_string  # noqa: E402


PROVIDERS: Dict[str, Dict[str, Any]] = {
    "deepseek-chat": {
        "endpoint": "https://api.deepseek.com/chat/completions",
        "api_key_env": "DEEPSEEK_API_KEY",
        "request_model": "deepseek-chat",
        "flavor": "openai",
    },
    "gemini-2.5-flash": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key_env": "GEMINI_API_KEY",
        "request_model": "gemini-2.5-flash",
        "flavor": "openai",
    },
    "gemini-2.5-pro": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key_env": "GEMINI_API_KEY",
        "request_model": "gemini-2.5-pro",
        "flavor": "openai",
    },
    "gpt-4o-mini": {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "request_model": "gpt-4o-mini",
        "flavor": "openai",
    },
    "gpt-5-mini": {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "request_model": "gpt-5-mini",
        "token_param": "max_completion_tokens",
        "omit_temperature": True,
        "flavor": "openai",
    },
    "gpt-5.4-mini": {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "request_model": "gpt-5.4-mini",
        "token_param": "max_completion_tokens",
        "flavor": "openai",
    },
    "claude-haiku-4-5": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "request_model": "claude-haiku-4-5",
        "flavor": "anthropic",
    },
    "claude-sonnet-4-6": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "request_model": "claude-sonnet-4-6",
        "flavor": "anthropic",
    },
}

DEFAULT_MODELS: Tuple[str, ...] = (
    "deepseek-chat",
    "gpt-4o-mini",
    "gpt-5.4-mini",
    "claude-sonnet-4-6",
    "gemini-2.5-pro",
)

DEFAULT_RELEASE_INDEX_PATH = (
    REPO_ROOT
    / "knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/release_index.jsonl"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "calibration/canary_probe_v1"
DEFAULT_CONTROL_SALT = "ls-pwb-canary-control-v1"
DEFAULT_PUBLIC_LIMIT = 3
DEFAULT_TAIL_CHARS = 8
DEFAULT_MAX_TOKENS = 32
DEFAULT_TEMPERATURE = 0.0


@dataclass(frozen=True)
class ReleaseIndexCanary:
    benchmark_unit_id: str
    holdout_bucket: str
    canary_string: str


@dataclass(frozen=True)
class CanaryProbeSpec:
    probe_id: str
    probe_kind: str
    benchmark_unit_id: str
    expected_full_string: str
    prompt_stem: str
    expected_tail: str
    public_reference_canary: str

    def to_redacted_dict(self) -> Dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "probe_kind": self.probe_kind,
            "benchmark_unit_id": self.benchmark_unit_id,
            "prompt_stem_sha256": sha256_text(self.prompt_stem),
            "prompt_stem_length": len(self.prompt_stem),
            "expected_full_sha256": sha256_text(self.expected_full_string),
            "expected_full_length": len(self.expected_full_string),
            "expected_tail_sha256": sha256_text(self.expected_tail),
            "expected_tail_length": len(self.expected_tail),
            "public_reference_sha256": sha256_text(self.public_reference_canary),
        }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _round(value: float) -> float:
    return round(value, 3)


def _format_rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "n/a"
    return f"{numerator} / {denominator} ({(100.0 * numerator / denominator):.1f}%)"


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
        keys[name.strip()] = value.strip().strip('"').strip("'")
    return keys


def load_release_index_canaries(path: Path) -> List[ReleaseIndexCanary]:
    rows: List[ReleaseIndexCanary] = []
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            record = json.loads(line)
            rows.append(
                ReleaseIndexCanary(
                    benchmark_unit_id=str(record["benchmark_unit_id"]),
                    holdout_bucket=str(record["holdout_bucket"]),
                    canary_string=str(record["canary_string"]),
                )
            )
    return rows


def split_canary(canary_string: str, tail_chars: int) -> Tuple[str, str]:
    if tail_chars <= 0:
        raise ValueError("tail_chars must be positive")
    if tail_chars >= len(canary_string):
        raise ValueError("tail_chars must be shorter than the canary string")
    return canary_string[:-tail_chars], canary_string[-tail_chars:]


def build_canary_probe_specs(
    release_index_rows: Sequence[ReleaseIndexCanary],
    *,
    public_limit: int = DEFAULT_PUBLIC_LIMIT,
    tail_chars: int = DEFAULT_TAIL_CHARS,
    control_salt: str = DEFAULT_CONTROL_SALT,
    canary_prefix: str = DEFAULT_CANARY_PREFIX,
) -> List[CanaryProbeSpec]:
    public_rows = sorted(
        (row for row in release_index_rows if row.holdout_bucket == "public"),
        key=lambda row: row.benchmark_unit_id,
    )
    selected_rows = public_rows[:public_limit]
    specs: List[CanaryProbeSpec] = []
    for index, row in enumerate(selected_rows, start=1):
        prompt_stem, expected_tail = split_canary(row.canary_string, tail_chars=tail_chars)
        specs.append(
            CanaryProbeSpec(
                probe_id=f"public-{index:02d}-{row.benchmark_unit_id.replace(':', '_')}",
                probe_kind="public",
                benchmark_unit_id=row.benchmark_unit_id,
                expected_full_string=row.canary_string,
                prompt_stem=prompt_stem,
                expected_tail=expected_tail,
                public_reference_canary=row.canary_string,
            )
        )
        control_canary = generate_canary_string(
            row.benchmark_unit_id,
            prefix=canary_prefix,
            salt=control_salt,
        )
        control_stem, control_tail = split_canary(control_canary, tail_chars=tail_chars)
        specs.append(
            CanaryProbeSpec(
                probe_id=f"control-{index:02d}-{row.benchmark_unit_id.replace(':', '_')}",
                probe_kind="control",
                benchmark_unit_id=row.benchmark_unit_id,
                expected_full_string=control_canary,
                prompt_stem=control_stem,
                expected_tail=control_tail,
                public_reference_canary=row.canary_string,
            )
        )
    return specs


def build_probe_prompt(probe: CanaryProbeSpec) -> str:
    return (
        "Complete the sequence exactly.\n"
        "Return the completed full string only.\n"
        "Do not add explanation, punctuation, quotes, or code fences.\n\n"
        f"{probe.prompt_stem}"
    )


def normalize_model_response(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").strip()
    if not cleaned:
        return ""
    first_nonempty = next((line.strip() for line in cleaned.splitlines() if line.strip()), cleaned)
    for prefix in ("Answer:", "Completed string:", "String:", "Output:"):
        if first_nonempty.startswith(prefix):
            first_nonempty = first_nonempty[len(prefix) :].strip()
            break
    first_nonempty = first_nonempty.strip().strip("`").strip()
    if len(first_nonempty) >= 2 and first_nonempty[0] == first_nonempty[-1] and first_nonempty[0] in {"'", '"'}:
        first_nonempty = first_nonempty[1:-1].strip()
    return first_nonempty


def levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (0 if left_char == right_char else 1)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def evaluate_probe_response(probe: CanaryProbeSpec, response_text: str) -> Dict[str, Any]:
    normalized = normalize_model_response(response_text)
    distance = levenshtein_distance(normalized, probe.expected_full_string)
    return {
        "probe_id": probe.probe_id,
        "probe_kind": probe.probe_kind,
        "benchmark_unit_id": probe.benchmark_unit_id,
        "exact_match": normalized == probe.expected_full_string,
        "normalized_response_sha256": sha256_text(normalized) if normalized else None,
        "normalized_response_length": len(normalized),
        "starts_with_prompt_stem": normalized.startswith(probe.prompt_stem),
        "levenshtein_distance": distance,
        "prompt_stem_sha256": sha256_text(probe.prompt_stem),
        "expected_full_sha256": sha256_text(probe.expected_full_string),
        "expected_tail_sha256": sha256_text(probe.expected_tail),
    }


def call_openai_compatible(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    api_key: str,
    temperature: float,
    max_tokens: int,
    timeout: int = 120,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": provider["request_model"],
        "messages": [{"role": "user", "content": prompt}],
    }
    token_param = str(provider.get("token_param", "max_tokens"))
    payload[token_param] = max_tokens
    if not provider.get("omit_temperature"):
        payload["temperature"] = temperature
    request = urllib.request.Request(
        provider["endpoint"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))
    return {
        "output_text": raw["choices"][0]["message"]["content"],
        "usage": raw.get("usage", {}),
        "raw": raw,
    }


def call_anthropic(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    api_key: str,
    temperature: float,
    max_tokens: int,
    timeout: int = 120,
) -> Dict[str, Any]:
    payload = {
        "model": provider["request_model"],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        provider["endpoint"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))
    content = raw.get("content", [])
    output_text = "".join(part.get("text", "") for part in content if part.get("type") == "text")
    usage = {
        "prompt_tokens": raw.get("usage", {}).get("input_tokens", 0),
        "completion_tokens": raw.get("usage", {}).get("output_tokens", 0),
        "total_tokens": raw.get("usage", {}).get("input_tokens", 0)
        + raw.get("usage", {}).get("output_tokens", 0),
    }
    return {
        "output_text": output_text,
        "usage": usage,
        "raw": raw,
    }


def _error_message(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = ""
        try:
            payload = exc.read()
        except Exception:
            payload = b""
        if payload:
            body = payload.decode("utf-8", errors="replace").strip()
        if body:
            return f"HTTP {exc.code} {exc.reason}: {body}"
        return f"HTTP {exc.code} {exc.reason}"
    return str(exc)


def call_model_with_retry(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    api_key: str,
    temperature: float,
    max_tokens: int,
    attempts: int = 3,
    backoff_seconds: float = 2.0,
) -> Dict[str, Any]:
    fn = call_anthropic if provider["flavor"] == "anthropic" else call_openai_compatible
    last_exc: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            return fn(
                prompt,
                provider=provider,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except (
            TimeoutError,
            urllib.error.HTTPError,
            urllib.error.URLError,
            ConnectionError,
            socket.timeout,
        ) as exc:
            last_exc = exc
            if attempt == attempts:
                break
            time.sleep(backoff_seconds * attempt)
    assert last_exc is not None
    raise RuntimeError(_error_message(last_exc)) from last_exc


def summarize_model_results(
    model_name: str,
    *,
    provider: Mapping[str, Any],
    probe_results: Sequence[Mapping[str, Any]],
    status: str,
    error: Optional[str],
    total_usage: Mapping[str, int],
) -> Dict[str, Any]:
    public_results = [row for row in probe_results if row["probe_kind"] == "public"]
    control_results = [row for row in probe_results if row["probe_kind"] == "control"]
    public_exact = sum(1 for row in public_results if row["exact_match"])
    control_exact = sum(1 for row in control_results if row["exact_match"])
    public_distances = [int(row["levenshtein_distance"]) for row in public_results]
    control_distances = [int(row["levenshtein_distance"]) for row in control_results]
    return {
        "model": model_name,
        "request_model": provider.get("request_model"),
        "status": status,
        "error": error,
        "completed_probe_count": len(probe_results),
        "public_probe_count": len(public_results),
        "control_probe_count": len(control_results),
        "public_exact_match_count": public_exact,
        "control_exact_match_count": control_exact,
        "public_any_exact_match": public_exact > 0,
        "control_any_exact_match": control_exact > 0,
        "public_min_levenshtein_distance": min(public_distances) if public_distances else None,
        "control_min_levenshtein_distance": min(control_distances) if control_distances else None,
        "total_prompt_tokens": int(total_usage.get("prompt_tokens", 0)),
        "total_completion_tokens": int(total_usage.get("completion_tokens", 0)),
        "total_tokens": int(total_usage.get("total_tokens", 0)),
    }


def run_model_probes(
    model_name: str,
    *,
    provider: Mapping[str, Any],
    api_key: Optional[str],
    probes: Sequence[CanaryProbeSpec],
    dry_run: bool,
    temperature: float,
    max_tokens: int,
    pause_between_calls: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if dry_run:
        summary = summarize_model_results(
            model_name,
            provider=provider,
            probe_results=(),
            status="dry_run",
            error=None,
            total_usage={},
        )
        return summary, []

    if not api_key:
        summary = summarize_model_results(
            model_name,
            provider=provider,
            probe_results=(),
            status="provider_error",
            error=f"missing {provider['api_key_env']}",
            total_usage={},
        )
        return summary, []

    results: List[Dict[str, Any]] = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    error: Optional[str] = None
    for index, probe in enumerate(probes):
        try:
            response = call_model_with_retry(
                build_probe_prompt(probe),
                provider=provider,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except RuntimeError as exc:
            error = str(exc)
            break
        usage = response.get("usage", {})
        total_usage["prompt_tokens"] += int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        total_usage["completion_tokens"] += int(
            usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
        )
        total_usage["total_tokens"] += int(usage.get("total_tokens", 0) or 0)
        row = evaluate_probe_response(probe, str(response.get("output_text", "")))
        row["model"] = model_name
        row["request_model"] = provider.get("request_model")
        results.append(row)
        if pause_between_calls > 0 and index < len(probes) - 1:
            time.sleep(pause_between_calls)

    summary = summarize_model_results(
        model_name,
        provider=provider,
        probe_results=results,
        status="ok" if error is None else "provider_error",
        error=error,
        total_usage=total_usage,
    )
    return summary, results


def render_markdown_report(summary: Mapping[str, Any]) -> str:
    lines: List[str] = [
        "# Canary Probe Report",
        "",
        "- probe mode: " + ("dry-run" if summary["dry_run"] else "live"),
        "- release index: `" + str(summary["release_index_path"]) + "`",
        "- public canaries sampled: " + str(summary["public_probe_count"]),
        "- controls sampled: " + str(summary["control_probe_count"]),
        "- tail characters withheld per probe: " + str(summary["tail_chars"]),
        "- models requested: " + str(len(summary["models_requested"])),
        "- models completed without provider error: " + str(summary["models_ok"]),
        "- models with provider errors: " + str(summary["models_with_provider_errors"]),
        "- any public exact match: " + ("yes" if summary["any_public_exact_match"] else "no"),
        "- any control exact match: " + ("yes" if summary["any_control_exact_match"] else "no"),
        "",
        "## Model Summary",
        "",
        "| model | status | public exact | control exact | min public distance | min control distance | total tokens |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["model_summaries"]:
        public_exact = _format_rate(row["public_exact_match_count"], row["public_probe_count"])
        control_exact = _format_rate(row["control_exact_match_count"], row["control_probe_count"])
        lines.append(
            "| "
            f"{row['model']} | "
            f"{row['status']} | "
            f"{public_exact} | "
            f"{control_exact} | "
            f"{row['public_min_levenshtein_distance'] if row['public_min_levenshtein_distance'] is not None else 'n/a'} | "
            f"{row['control_min_levenshtein_distance'] if row['control_min_levenshtein_distance'] is not None else 'n/a'} | "
            f"{row['total_tokens']} |"
        )

    lines.extend(
        [
            "",
            "## Probe Configuration",
            "",
            "- benchmark units sampled:",
        ]
    )
    for benchmark_unit_id in summary["benchmark_unit_ids"]:
        lines.append(f"  - `{benchmark_unit_id}`")

    if summary["provider_errors"]:
        lines.extend(["", "## Provider Errors", ""])
        for row in summary["provider_errors"]:
            lines.append(f"- `{row['model']}`: {row['error']}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Any exact public-canary match is a contamination red flag.",
            "- Any exact control-canary match suggests the prompt or scoring rule is too permissive.",
            "- Distances are computed against the withheld full string, not only the withheld tail.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_summary_payload(
    *,
    release_index_path: Path,
    probes: Sequence[CanaryProbeSpec],
    model_summaries: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    public_probe_count = sum(1 for probe in probes if probe.probe_kind == "public")
    control_probe_count = sum(1 for probe in probes if probe.probe_kind == "control")
    provider_errors = [row for row in model_summaries if row["status"] == "provider_error"]
    return {
        "release_index_path": str(release_index_path),
        "public_probe_count": public_probe_count,
        "control_probe_count": control_probe_count,
        "tail_chars": len(probes[0].expected_tail) if probes else 0,
        "models_requested": [row["model"] for row in model_summaries],
        "models_ok": sum(1 for row in model_summaries if row["status"] == "ok"),
        "models_with_provider_errors": len(provider_errors),
        "provider_errors": provider_errors,
        "model_summaries": list(model_summaries),
        "benchmark_unit_ids": sorted({probe.benchmark_unit_id for probe in probes if probe.probe_kind == "public"}),
        "any_public_exact_match": any(row["public_any_exact_match"] for row in model_summaries),
        "any_control_exact_match": any(row["control_any_exact_match"] for row in model_summaries),
    }


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        action="append",
        choices=sorted(PROVIDERS),
        help="Model label to probe. Repeatable. Defaults to a 5-model frontier set.",
    )
    parser.add_argument(
        "--keys-file",
        default="~/.api_keys",
        help="Path to shell-style API key file.",
    )
    parser.add_argument(
        "--release-index",
        default=str(DEFAULT_RELEASE_INDEX_PATH),
        help="Release index JSONL containing public/private canary strings.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for redacted JSONL and summary artifacts.",
    )
    parser.add_argument(
        "--report-output",
        help="Optional markdown report path to copy the generated summary to.",
    )
    parser.add_argument(
        "--public-limit",
        type=int,
        default=DEFAULT_PUBLIC_LIMIT,
        help="Number of public canaries to sample deterministically.",
    )
    parser.add_argument(
        "--tail-chars",
        type=int,
        default=DEFAULT_TAIL_CHARS,
        help="Number of final canary characters withheld from the prompt.",
    )
    parser.add_argument(
        "--control-salt",
        default=DEFAULT_CONTROL_SALT,
        help="Salt used to generate unpublished matched-length control canaries.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help="Sampling temperature for provider calls.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum completion tokens per probe.",
    )
    parser.add_argument(
        "--pause-between-calls",
        type=float,
        default=0.0,
        help="Optional pause between model calls.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the probe plan without making network calls.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    model_names = tuple(args.model or DEFAULT_MODELS)
    release_index_path = Path(args.release_index)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    release_index_rows = load_release_index_canaries(release_index_path)
    probes = build_canary_probe_specs(
        release_index_rows,
        public_limit=args.public_limit,
        tail_chars=args.tail_chars,
        control_salt=args.control_salt,
    )

    keys = dict(os.environ)
    keys.update(load_api_keys(Path(os.path.expanduser(args.keys_file))))

    probe_specs_path = output_dir / "probe_specs.jsonl"
    with probe_specs_path.open("w", encoding="utf-8") as handle:
        for probe in probes:
            handle.write(json.dumps(probe.to_redacted_dict(), sort_keys=True) + "\n")

    all_results: List[Dict[str, Any]] = []
    model_summaries: List[Dict[str, Any]] = []
    for model_name in model_names:
        provider = PROVIDERS[model_name]
        api_key = keys.get(provider["api_key_env"])
        summary, results = run_model_probes(
            model_name,
            provider=provider,
            api_key=api_key,
            probes=probes,
            dry_run=bool(args.dry_run),
            temperature=float(args.temperature),
            max_tokens=int(args.max_tokens),
            pause_between_calls=float(args.pause_between_calls),
        )
        model_summaries.append(summary)
        all_results.extend(results)

    results_path = output_dir / "probe_results.jsonl"
    with results_path.open("w", encoding="utf-8") as handle:
        for row in all_results:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = build_summary_payload(
        release_index_path=release_index_path,
        probes=probes,
        model_summaries=model_summaries,
    )
    summary["dry_run"] = bool(args.dry_run)

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    markdown = render_markdown_report(summary)
    summary_md_path = output_dir / "summary.md"
    summary_md_path.write_text(markdown, encoding="utf-8")
    if args.report_output:
        report_output = Path(args.report_output)
        report_output.parent.mkdir(parents=True, exist_ok=True)
        report_output.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
