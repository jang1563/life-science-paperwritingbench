#!/usr/bin/env python3
"""Run a frontier model as a judge over LLM submissions against source evidence.

Pairs with scripts/llm_smoke_eval.py. For each SubmissionRecord, the judge
sees the original source evidence (from the enriched source bundle) plus
the LLM's generated output and produces a structured rubric-axis score:

- writing_structure_compliance
- evidence_grounding
- factual_fidelity
- traceability
- hallucination_absence

Each axis is scored 0.0-1.0 with a short rationale. Any grounding issues
(claims the judge can't verify against source, suspected fabrications,
mismatched numbers, etc.) are listed separately so we can triage rather
than lose them in an aggregate score.

Usage (defaults operate on the 30-bundle DeepSeek run):

    PYTHONPATH=src python3 scripts/llm_judge_eval.py \\
        --submissions-path calibration/llm_public_slice_v1/submissions.jsonl \\
        --output-dir calibration/llm_public_slice_v1_judged

Judge model defaults to Claude Sonnet 4.6. See PROVIDERS for other choices.

Cost footprint on the 30-bundle run: ~132k input + ~15k output tokens,
~$0.62 at Claude Sonnet 4.6 rates (using raw-string style dollar notation). Use --limit N for a cheaper dev pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from life_science_paperwritingbench.io import (  # noqa: E402
    auto_review_source_bundle_from_dict,
    task_bundle_from_dict,
)


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


PROVIDERS: Dict[str, Dict[str, Any]] = {
    "claude-sonnet-4-6": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "request_model": "claude-sonnet-4-6",
        "flavor": "anthropic",
    },
    "claude-haiku-4-5": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "request_model": "claude-haiku-4-5-20251001",
        "flavor": "anthropic",
    },
    "claude-opus-4-6": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "request_model": "claude-opus-4-6",
        "flavor": "anthropic",
    },
    "gemini-2.5-pro": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key_env": "GEMINI_API_KEY",
        "request_model": "gemini-2.5-pro",
        "flavor": "openai",
    },
    "deepseek-reasoner": {
        "endpoint": "https://api.deepseek.com/chat/completions",
        "api_key_env": "DEEPSEEK_API_KEY",
        "request_model": "deepseek-reasoner",
        "flavor": "openai",
    },
}

DEFAULT_JUDGE = "claude-sonnet-4-6"

KB_ROOT = REPO_ROOT / "knowledge_base"
TASK_BUNDLES_PATH = (
    KB_ROOT
    / "released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl"
)
SOURCE_BUNDLES_PATH = (
    KB_ROOT
    / "enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v16.jsonl"
)
DEFAULT_SUBMISSIONS_PATH = REPO_ROOT / "calibration/llm_public_slice_v1/submissions.jsonl"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "calibration/llm_public_slice_v1_judged"

RUBRIC_AXES: Sequence[str] = (
    "writing_structure_compliance",
    "evidence_grounding",
    "factual_fidelity",
    "traceability",
    "hallucination_absence",
)

PASS_THRESHOLD = 0.6


# ---------------------------------------------------------------------------
# Key + I/O helpers (minor duplication with llm_smoke_eval.py — kept small)
# ---------------------------------------------------------------------------


def load_api_keys(path: Path) -> Dict[str, str]:
    keys: Dict[str, str] = {}
    if not path.exists():
        return keys
    for raw in path.read_text().splitlines():
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


def load_task_bundles(path: Path) -> Dict[str, Any]:
    bundles: Dict[str, Any] = {}
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                bundle = task_bundle_from_dict(json.loads(line))
                bundles[bundle.task_bundle_id] = bundle
    return bundles


def load_source_bundles(path: Path) -> Dict[str, Any]:
    bundles: Dict[str, Any] = {}
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            bundles[record["paper_id"]] = auto_review_source_bundle_from_dict(record)
    return bundles


def load_submissions(path: Path) -> List[Dict[str, Any]]:
    submissions: List[Dict[str, Any]] = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                submissions.append(json.loads(line))
    return submissions


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


TASK_FAMILY_TO_TARGET: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "methods_to_text": ("Methods", ("abstract_text", "results_text", "figure_captions", "table_snippets")),
    "results_to_text": ("Results", ("abstract_text", "methods_text", "figure_captions", "table_snippets")),
    "abstract_from_evidence": ("Abstract", ("methods_text", "results_text", "figure_captions", "table_snippets")),
}


def _clip(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_list(items: Sequence[str], limit_each: int = 600, max_items: int = 8) -> str:
    if not items:
        return "(none provided)"
    return "\n".join(
        f"{idx}. {_clip(item, limit_each)}"
        for idx, item in enumerate(items[:max_items], start=1)
    )


def build_evidence_block(task_family_value: str, source_bundle) -> str:
    _, include_fields = TASK_FAMILY_TO_TARGET[task_family_value]
    sections: List[Tuple[str, str]] = []
    if "abstract_text" in include_fields and source_bundle.abstract_text:
        sections.append(("Abstract", _clip(source_bundle.abstract_text, 2500)))
    if "methods_text" in include_fields and source_bundle.methods_text:
        sections.append(("Methods", _clip(source_bundle.methods_text, 4000)))
    if "results_text" in include_fields and source_bundle.results_text:
        sections.append(("Results", _clip(source_bundle.results_text, 4500)))
    if "figure_captions" in include_fields and source_bundle.figure_captions:
        sections.append(("Figure captions", _format_list(source_bundle.figure_captions)))
    if "table_snippets" in include_fields and source_bundle.table_snippets:
        sections.append(("Table snippets", _format_list(source_bundle.table_snippets)))
    return "\n\n".join(f"## {title}\n{content}" for title, content in sections)


def build_judge_prompt(task_bundle, source_bundle, submission_text: str) -> str:
    task_family_value = task_bundle.task_family.value
    section_title, _ = TASK_FAMILY_TO_TARGET[task_family_value]
    evidence_block = build_evidence_block(task_family_value, source_bundle)
    rubric_axes_listing = "\n".join(f"- `{axis}`" for axis in RUBRIC_AXES)

    return f"""You are an expert biomedical scientific-writing reviewer performing a rigorous peer-review-style evaluation.

Your job: score the candidate model's generated "{section_title}" section against the source evidence for a {task_family_value} task, using the rubric below. Be strict and specific. Punish invented numbers, invented experiments, misattributed figures, and claims that cannot be traced to the provided evidence. Reward outputs whose details are demonstrably present in the evidence.

## Rubric axes (score each 0.0 to 1.0)

{rubric_axes_listing}

Axis definitions:

- writing_structure_compliance: Does the output open with the expected section heading and follow a plausible section structure (appropriate level of detail, logical flow, typical subsections for the task family)?
- evidence_grounding: Is every non-trivial claim traceable to specific content in the source evidence? Penalize free-floating claims.
- factual_fidelity: Do quantitative values, qualifiers ("significantly", "modestly"), organisms, time points, sample sizes, and cited figures/tables exactly match the source? Any mismatch is a serious deduction.
- traceability: Are evidence identifiers, section pointers (e.g. "methods_section", "abstract_section"), figure/table references, or accessions cited where useful? 0.0 if there are zero references; 1.0 if they are pervasive and correct.
- hallucination_absence: Is the output free of fabricated content (made-up citations, phantom experiments, invented numerical values)? 1.0 = no hallucinations found; 0.0 = at least one clear fabrication.

## Pass threshold

An axis is considered passing at >= {PASS_THRESHOLD}. overall_pass is true if and only if every axis is at or above that threshold.

## Source evidence

{evidence_block}

## Candidate output (to be judged)

{submission_text}

## Output format

Respond with ONLY a single JSON object. No prose before or after. No markdown code fences. The JSON must match this schema exactly:

{{
  "axis_scores": {{
    "writing_structure_compliance": <float 0.0-1.0>,
    "evidence_grounding": <float 0.0-1.0>,
    "factual_fidelity": <float 0.0-1.0>,
    "traceability": <float 0.0-1.0>,
    "hallucination_absence": <float 0.0-1.0>
  }},
  "axis_rationales": {{
    "writing_structure_compliance": "<1-3 sentences>",
    "evidence_grounding": "<1-3 sentences>",
    "factual_fidelity": "<1-3 sentences>",
    "traceability": "<1-3 sentences>",
    "hallucination_absence": "<1-3 sentences>"
  }},
  "grounding_issues": [
    "<specific concern citing the exact claim and why it is unsupported or inconsistent with the evidence>"
  ],
  "overall_pass": <true or false>
}}"""


# ---------------------------------------------------------------------------
# API adapters
# ---------------------------------------------------------------------------


def call_anthropic(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, timeout: int = 180) -> Dict[str, Any]:
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
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        body = response.read()
    decoded = json.loads(body)
    output_text = "".join(
        part.get("text", "")
        for part in decoded.get("content", [])
        if isinstance(part, dict) and part.get("type") == "text"
    )
    usage = decoded.get("usage", {}) or {}
    return {
        "output_text": output_text,
        "usage": {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
        },
        "raw": decoded,
    }


def call_openai_compatible(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, timeout: int = 180) -> Dict[str, Any]:
    payload = {
        "model": provider["request_model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        provider["endpoint"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        body = response.read()
    decoded = json.loads(body)
    output_text = decoded["choices"][0]["message"]["content"]
    usage = decoded.get("usage", {}) or {}
    return {
        "output_text": output_text,
        "usage": {
            "input_tokens": usage.get("prompt_tokens"),
            "output_tokens": usage.get("completion_tokens"),
        },
        "raw": decoded,
    }


def call_judge_with_retry(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, attempts: int = 3, backoff_seconds: float = 2.0) -> Dict[str, Any]:
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
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError) as exc:
            last_exc = exc
            if attempt == attempts:
                break
            sleep_for = backoff_seconds * (2 ** (attempt - 1))
            print(f"    attempt {attempt} failed ({exc}); sleeping {sleep_for:.1f}s", file=sys.stderr)
            time.sleep(sleep_for)
    assert last_exc is not None
    raise last_exc


# ---------------------------------------------------------------------------
# Judge output parsing
# ---------------------------------------------------------------------------


def extract_json_object(text: str) -> Dict[str, Any]:
    """Robust-enough JSON extractor: strips ```json fences if present, then finds the outermost object."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    # If the judge prepended prose (against instruction), find the first { ... } balanced pair
    if not cleaned.lstrip().startswith("{"):
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first != -1 and last != -1 and last > first:
            cleaned = cleaned[first : last + 1]
    return json.loads(cleaned)


def _score_record_shape(payload: Mapping[str, Any]) -> Dict[str, Any]:
    axis_scores_raw = payload.get("axis_scores") or {}
    axis_rationales_raw = payload.get("axis_rationales") or {}
    axis_scores: Dict[str, float] = {}
    axis_rationales: Dict[str, str] = {}
    for axis in RUBRIC_AXES:
        raw = axis_scores_raw.get(axis, 0.0)
        try:
            score = float(raw)
        except (TypeError, ValueError):
            score = 0.0
        axis_scores[axis] = max(0.0, min(1.0, score))
        axis_rationales[axis] = str(axis_rationales_raw.get(axis, "")).strip()
    grounding_issues = [str(item) for item in (payload.get("grounding_issues") or [])]
    overall_pass = bool(payload.get("overall_pass"))
    all_axes_pass = all(axis_scores[axis] >= PASS_THRESHOLD for axis in RUBRIC_AXES)
    return {
        "axis_scores": axis_scores,
        "axis_rationales": axis_rationales,
        "grounding_issues": grounding_issues,
        "overall_pass": overall_pass,
        "all_axes_above_threshold": all_axes_pass,
    }


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:12].upper()}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge", default=DEFAULT_JUDGE, choices=sorted(PROVIDERS))
    parser.add_argument("--keys-file", default=str(Path.home() / ".api_keys"))
    parser.add_argument("--submissions-path", default=str(DEFAULT_SUBMISSIONS_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2000)
    parser.add_argument("--limit", type=int, default=None, help="only judge the first N submissions (dev)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pause-between-calls", type=float, default=0.3)
    args = parser.parse_args()

    provider = PROVIDERS[args.judge]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    keys = load_api_keys(Path(args.keys_file).expanduser())
    env_key = os.environ.get(provider["api_key_env"])
    api_key = env_key or keys.get(provider["api_key_env"])
    if not args.dry_run and not api_key:
        print(f"Missing {provider['api_key_env']} (checked env and {args.keys_file})", file=sys.stderr)
        return 2

    task_bundles = load_task_bundles(TASK_BUNDLES_PATH)
    source_bundles = load_source_bundles(SOURCE_BUNDLES_PATH)
    submissions = load_submissions(Path(args.submissions_path))
    if args.limit is not None:
        submissions = submissions[: args.limit]

    judgments: List[Dict[str, Any]] = []
    usage_rows: List[Dict[str, Any]] = []
    parse_failures: List[Dict[str, Any]] = []

    for idx, submission in enumerate(submissions, start=1):
        task_bundle_id = submission["task_bundle_id"]
        task_bundle = task_bundles.get(task_bundle_id)
        if task_bundle is None:
            print(f"[{idx}] skipping: no task bundle for {task_bundle_id}", file=sys.stderr)
            continue
        source_bundle = source_bundles.get(task_bundle.paper_id)
        if source_bundle is None:
            print(f"[{idx}] skipping: no source bundle for {task_bundle.paper_id}", file=sys.stderr)
            continue
        prompt = build_judge_prompt(task_bundle, source_bundle, submission["output_text"])
        prompt_path = output_dir / f"judge_prompt_{idx:02d}_{task_bundle_id.replace(':','_')}.md"
        prompt_path.write_text(prompt)

        if args.dry_run:
            print(f"[{idx}/{len(submissions)}] DRY RUN — wrote prompt to {prompt_path}")
            continue

        print(f"[{idx}/{len(submissions)}] judging {task_bundle_id} ({task_bundle.task_family.value})")
        started = time.time()
        response = call_judge_with_retry(
            prompt,
            provider=provider,
            api_key=api_key,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        elapsed = time.time() - started
        output_text = response["output_text"]
        usage = dict(response["usage"])
        usage["elapsed_seconds"] = round(elapsed, 2)
        print(f"    done in {elapsed:.1f}s  input_tokens={usage.get('input_tokens')} output_tokens={usage.get('output_tokens')}")

        try:
            parsed = extract_json_object(output_text)
            shape = _score_record_shape(parsed)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"    JSON parse failed: {exc}", file=sys.stderr)
            parse_failures.append({"task_bundle_id": task_bundle_id, "error": str(exc), "raw": output_text})
            shape = {
                "axis_scores": {axis: 0.0 for axis in RUBRIC_AXES},
                "axis_rationales": {axis: "" for axis in RUBRIC_AXES},
                "grounding_issues": [f"judge output did not parse as JSON: {exc}"],
                "overall_pass": False,
                "all_axes_above_threshold": False,
            }

        judgment_id = _stable_id(
            "JUDGE",
            {
                "submission_id": submission["submission_id"],
                "judge_model": provider["request_model"],
                "task_bundle_id": task_bundle_id,
            },
        )
        judgments.append(
            {
                "judgment_id": judgment_id,
                "submission_id": submission["submission_id"],
                "task_bundle_id": task_bundle_id,
                "paper_id": task_bundle.paper_id,
                "task_family": task_bundle.task_family.value,
                "study_class": task_bundle.study_class.value,
                "claim_mode": task_bundle.claim_mode.value,
                "judge_flavor": provider["flavor"],
                "judge_model": provider["request_model"],
                "judge_name": args.judge,
                "temperature": args.temperature,
                "pass_threshold": PASS_THRESHOLD,
                **shape,
                "raw_judge_output": output_text,
            }
        )
        usage_rows.append({"task_bundle_id": task_bundle_id, **usage})

        if args.pause_between_calls > 0 and idx < len(submissions):
            time.sleep(args.pause_between_calls)

    if args.dry_run:
        return 0

    # Persist judgments
    judgments_path = output_dir / "judgments.jsonl"
    with judgments_path.open("w") as handle:
        for record in judgments:
            handle.write(json.dumps(record) + "\n")

    if parse_failures:
        (output_dir / "parse_failures.jsonl").write_text(
            "\n".join(json.dumps(row) for row in parse_failures) + "\n"
        )

    # Aggregate
    def _avg(values: Sequence[float]) -> float:
        return round(sum(values) / len(values), 3) if values else 0.0

    per_axis: Dict[str, List[float]] = {axis: [] for axis in RUBRIC_AXES}
    per_family: Dict[str, Dict[str, Any]] = {}
    total_pass = 0
    total_axes_pass = 0
    all_issues: List[Tuple[str, str]] = []

    for record in judgments:
        for axis in RUBRIC_AXES:
            per_axis[axis].append(record["axis_scores"][axis])
        family = record["task_family"]
        bucket = per_family.setdefault(
            family,
            {"total": 0, "judge_pass": 0, "all_axes_above_threshold": 0, "axis_means": {axis: [] for axis in RUBRIC_AXES}},
        )
        bucket["total"] += 1
        if record["overall_pass"]:
            bucket["judge_pass"] += 1
            total_pass += 1
        if record["all_axes_above_threshold"]:
            bucket["all_axes_above_threshold"] += 1
            total_axes_pass += 1
        for axis in RUBRIC_AXES:
            bucket["axis_means"][axis].append(record["axis_scores"][axis])
        for issue in record.get("grounding_issues", []):
            all_issues.append((record["task_bundle_id"], issue))

    for family in per_family.values():
        family["axis_means"] = {axis: _avg(values) for axis, values in family["axis_means"].items()}

    total_input_tokens = sum((row.get("input_tokens") or 0) for row in usage_rows)
    total_output_tokens = sum((row.get("output_tokens") or 0) for row in usage_rows)

    summary = {
        "judge": args.judge,
        "judge_model": provider["request_model"],
        "temperature": args.temperature,
        "total_submissions_judged": len(judgments),
        "judge_overall_pass": total_pass,
        "all_axes_above_threshold": total_axes_pass,
        "pass_threshold": PASS_THRESHOLD,
        "per_axis_mean": {axis: _avg(per_axis[axis]) for axis in RUBRIC_AXES},
        "per_axis_min": {axis: round(min(per_axis[axis], default=0.0), 3) for axis in RUBRIC_AXES},
        "per_task_family": per_family,
        "total_grounding_issues": len(all_issues),
        "parse_failures": len(parse_failures),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "usage": usage_rows,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    md_lines = [
        "# LLM Judge Evaluation",
        "",
        f"- judge: `{args.judge}` (request model: `{provider['request_model']}`)",
        f"- temperature: {args.temperature}",
        f"- submissions judged: {len(judgments)}",
        f"- judge overall_pass: {total_pass} / {len(judgments)}",
        f"- all axes >= {PASS_THRESHOLD}: {total_axes_pass} / {len(judgments)}",
        f"- grounding issues reported: {len(all_issues)}",
        f"- parse failures: {len(parse_failures)}",
        f"- total tokens: input={total_input_tokens}, output={total_output_tokens}",
        "",
        "## Per-axis means",
        "",
        "| axis | mean | min |",
        "| --- | ---: | ---: |",
    ]
    for axis in RUBRIC_AXES:
        md_lines.append(
            f"| {axis} | {summary['per_axis_mean'][axis]:.3f} | {summary['per_axis_min'][axis]:.3f} |"
        )
    md_lines.extend(["", "## Per task family", "", "| family | pass / total | mean structure | mean grounding | mean fidelity | mean traceability | mean no_halluc |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for family, bucket in sorted(per_family.items()):
        means = bucket["axis_means"]
        md_lines.append(
            f"| {family} | {bucket['judge_pass']} / {bucket['total']} | "
            f"{means['writing_structure_compliance']:.3f} | {means['evidence_grounding']:.3f} | "
            f"{means['factual_fidelity']:.3f} | {means['traceability']:.3f} | "
            f"{means['hallucination_absence']:.3f} |"
        )
    if all_issues:
        md_lines.extend(["", "## Flagged grounding issues", ""])
        for tb_id, issue in all_issues:
            md_lines.append(f"- `{tb_id}`: {issue}")
    (output_dir / "summary.md").write_text("\n".join(md_lines) + "\n")

    print()
    print(json.dumps({k: v for k, v in summary.items() if k not in ("usage", "per_task_family")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
