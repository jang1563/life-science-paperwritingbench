#!/usr/bin/env python3
"""Run a frontier model as a judge over LLM submissions against source evidence.

Pairs with scripts/llm_smoke_eval.py. For each SubmissionRecord, the judge
sees the original source evidence (from the enriched source bundle) plus
the LLM's generated output and produces a structured rubric-axis score:

- writing_structure_compliance
- evidence_grounding
- factual_fidelity
- traceability or quantitative_specificity
- hallucination_absence

Rubric version `v3` is the default:

- 4-point anchored ordinal (`0`-`3` integer)
- mean-axis pass rule (`mean(axis_scores) >= 2.0`)
- family-aware abstract axis (`quantitative_specificity` replaces
  `traceability`)

Legacy rubric version `v2` preserves the original 0.0-1.0 continuous scale
and all-axes pass rule for historical reproducibility.

Any grounding issues (claims the judge can't verify against source,
suspected fabrications, mismatched numbers, etc.) are listed separately so
we can triage rather than lose them in an aggregate score.

Usage (defaults operate on the 30-bundle DeepSeek v2 run with rubric v3):

    PYTHONPATH=src python3 scripts/llm_judge_eval.py \\
        --submissions-path calibration/llm_public_slice_v2/submissions.jsonl \\
        --output-dir calibration/llm_public_slice_v2_judged_v3

Judge model defaults to Claude Sonnet 4.6. See PROVIDERS for other choices.

Cost footprint on the 30-bundle run: ~132k input + ~15k output tokens,
~$0.62 at Claude Sonnet 4.6 rates (using raw-string style dollar notation). Use --limit N for a cheaper dev pass.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
import re
import socket
import sys
import time
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from life_science_paperwritingbench.io import (  # noqa: E402
    auto_review_source_bundle_from_dict,
    task_bundle_from_dict,
)
from life_science_paperwritingbench.frontier_runtime import (  # noqa: E402
    call_anthropic as shared_call_anthropic,
    call_openai_compatible as shared_call_openai_compatible,
    default_model_label_for_role,
    default_frontier_registry_path,
    load_api_keys,
    load_frontier_model,
    load_frontier_registry,
    registry_entry_provenance,
    resolve_api_key,
)


DEFAULT_REGISTRY_PATH = default_frontier_registry_path()
PROVIDERS: Dict[str, Dict[str, Any]] = load_frontier_registry(DEFAULT_REGISTRY_PATH, role="judge")

DEFAULT_JUDGE = default_model_label_for_role(
    "judge",
    preferred_label="claude-sonnet-4-6",
    registry_path=DEFAULT_REGISTRY_PATH,
)

KB_ROOT = REPO_ROOT / "knowledge_base"
TASK_BUNDLES_PATH = (
    KB_ROOT
    / "released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl"
)
SOURCE_BUNDLES_PATH = (
    KB_ROOT
    / "enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v16.jsonl"
)
DEFAULT_SUBMISSIONS_PATH = REPO_ROOT / "calibration/llm_public_slice_v2/submissions.jsonl"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "calibration/llm_public_slice_v2_judged_v3"
DEFAULT_RUBRIC_VERSION = "v3"

LEGACY_RUBRIC_AXES: Tuple[str, ...] = (
    "writing_structure_compliance",
    "evidence_grounding",
    "factual_fidelity",
    "traceability",
    "hallucination_absence",
)
V3_ABSTRACT_AXES: Tuple[str, ...] = (
    "writing_structure_compliance",
    "evidence_grounding",
    "factual_fidelity",
    "quantitative_specificity",
    "hallucination_absence",
)
SUMMARY_AXIS_ORDER: Tuple[str, ...] = (
    "writing_structure_compliance",
    "evidence_grounding",
    "factual_fidelity",
    "traceability",
    "quantitative_specificity",
    "hallucination_absence",
)
LEGACY_PASS_THRESHOLD = 0.6
V3_PASS_THRESHOLD = 2.0
PASS_RULE_ALL_AXES = "all_axes_gte_threshold"
PASS_RULE_MEAN = "mean_axis_score_gte_threshold"


@dataclass(frozen=True)
class RubricConfig:
    rubric_version: str
    axes: Tuple[str, ...]
    axis_min: float
    axis_max: float
    pass_threshold: float
    pass_rule: str
    score_type: str


V2_AXIS_DEFINITIONS: Dict[str, str] = {
    "writing_structure_compliance": (
        "Does the output open with the expected section heading and follow a plausible section structure "
        "(appropriate level of detail, logical flow, typical subsections for the task family)?"
    ),
    "evidence_grounding": (
        "Is every non-trivial claim traceable to specific content in the source evidence? Penalize "
        "free-floating claims."
    ),
    "factual_fidelity": (
        'Do quantitative values, qualifiers ("significantly", "modestly"), organisms, time points, '
        "sample sizes, and cited figures/tables exactly match the source? Any mismatch is a serious deduction."
    ),
    "traceability": (
        'Are evidence identifiers, section pointers (e.g. "methods_section", "abstract_section"), '
        "figure/table references, or accessions cited where useful? 0.0 if there are zero references; "
        "1.0 if they are pervasive and correct."
    ),
    "hallucination_absence": (
        "Is the output free of fabricated content (made-up citations, phantom experiments, invented "
        "numerical values)? 1.0 = no hallucinations found; 0.0 = at least one clear fabrication."
    ),
}

V3_AXIS_ANCHORS: Dict[str, Dict[int, str]] = {
    "writing_structure_compliance": {
        0: "The output is missing the expected section heading, uses the wrong section type, or is so disorganized that it is not usable as the requested section.",
        1: "The output partially resembles the requested section, but the heading, ordering, or section-appropriate detail is substantially off.",
        2: "The output mostly fits the requested section and is readable, with only minor structure or emphasis problems.",
        3: "The output cleanly matches the requested section, uses an appropriate heading, and follows a strong scientific-writing structure throughout.",
    },
    "evidence_grounding": {
        0: "Many claims cannot be tied back to the provided evidence, or the response relies heavily on unsupported assertions.",
        1: "Some major claims are grounded, but there are still important unsupported or weakly supported statements.",
        2: "Most substantive claims are grounded in the evidence, with only minor stretches or missing local support.",
        3: "Nearly every non-trivial claim is directly and convincingly grounded in the supplied evidence.",
    },
    "factual_fidelity": {
        0: "The output contains major factual errors, incorrect numbers, or incorrect study details relative to the source.",
        1: "The output captures some facts correctly, but there are still notable inaccuracies in values, qualifiers, organisms, timepoints, or references.",
        2: "The output is largely factually faithful, with only minor slips that do not materially distort the study.",
        3: "The output is factually precise and consistent with the source evidence, including quantitative details and scientific qualifiers.",
    },
    "traceability": {
        0: "The output provides no useful evidence pointers, or its citations and section references are clearly wrong.",
        1: "The output includes a few evidence pointers, but they are sparse, generic, or only partly correct.",
        2: "The output includes useful and mostly correct evidence pointers, figure/table references, or accessions where they help the reader verify claims.",
        3: "The output consistently provides correct, specific evidence pointers that make claim verification straightforward.",
    },
    "quantitative_specificity": {
        0: "The abstract stays generic and omits key quantitative or biological specifics that are available in the evidence. Do not require figure or table citations for this axis.",
        1: "The abstract includes a little specificity, but it still misses important p-values, sample sizes, effect sizes, accessions, organism names, or similarly concrete anchors that the evidence supports.",
        2: "The abstract is mostly specific and includes several appropriate quantitative or biological anchors, with only modest opportunities for more precision.",
        3: "The abstract is richly specific, using the strongest available quantitative and biological anchors from the evidence without inventing new detail.",
    },
    "hallucination_absence": {
        0: "The output contains at least one clear fabrication such as an invented experiment, number, dataset, citation, or unsupported conclusion.",
        1: "The output is mostly grounded, but there are still suspicious or weakly supported details that read like likely hallucinations.",
        2: "The output is effectively free of clear hallucinations, with only minor ambiguity that does not amount to fabrication.",
        3: "The output is fully free of fabricated content and stays tightly within the evidence boundary.",
    },
}


# ---------------------------------------------------------------------------
# Key + I/O helpers (minor duplication with llm_smoke_eval.py — kept small)
# ---------------------------------------------------------------------------
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


def rubric_config_for_task_family(task_family_value: str, rubric_version: str) -> RubricConfig:
    if rubric_version == "v2":
        return RubricConfig(
            rubric_version="v2",
            axes=LEGACY_RUBRIC_AXES,
            axis_min=0.0,
            axis_max=1.0,
            pass_threshold=LEGACY_PASS_THRESHOLD,
            pass_rule=PASS_RULE_ALL_AXES,
            score_type="float",
        )
    if rubric_version == "v3":
        return RubricConfig(
            rubric_version="v3",
            axes=V3_ABSTRACT_AXES if task_family_value == "abstract_from_evidence" else LEGACY_RUBRIC_AXES,
            axis_min=0.0,
            axis_max=3.0,
            pass_threshold=V3_PASS_THRESHOLD,
            pass_rule=PASS_RULE_MEAN,
            score_type="integer",
        )
    raise ValueError(f"Unsupported rubric version: {rubric_version}")


def _score_placeholder(config: RubricConfig) -> str:
    if config.score_type == "integer":
        return "<integer 0-3>"
    return "<float 0.0-1.0>"


def _pass_rule_description(config: RubricConfig) -> str:
    if config.pass_rule == PASS_RULE_MEAN:
        return (
            f"The mean axis score is the pass rule. overall_pass must be true if and only if the mean of "
            f"all axis scores is >= {config.pass_threshold:.1f}."
        )
    return (
        f"An axis is considered passing at >= {config.pass_threshold}. overall_pass must be true if and "
        f"only if every axis is at or above that threshold."
    )


def _format_axis_guidance(axis: str, config: RubricConfig) -> str:
    if config.rubric_version == "v2":
        return f"- {axis}: {V2_AXIS_DEFINITIONS[axis]}"
    anchors = [f"- {axis}:"]
    for level in range(4):
        anchors.append(f"  - {level}: {V3_AXIS_ANCHORS[axis][level]}")
    return "\n".join(anchors)


def _output_schema_block(config: RubricConfig) -> str:
    axis_scores = ",\n".join(
        f'    "{axis}": {_score_placeholder(config)}'
        for axis in config.axes
    )
    axis_rationales = ",\n".join(
        f'    "{axis}": "<1-3 sentences>"'
        for axis in config.axes
    )
    return f"""{{
  "axis_scores": {{
{axis_scores}
  }},
  "axis_rationales": {{
{axis_rationales}
  }},
  "grounding_issues": [
    "<specific concern citing the exact claim and why it is unsupported or inconsistent with the evidence>"
  ],
  "overall_pass": <true or false>
}}"""


def build_judge_prompt(task_bundle, source_bundle, submission_text: str, *, rubric_version: str = DEFAULT_RUBRIC_VERSION) -> str:
    task_family_value = task_bundle.task_family.value
    section_title, _ = TASK_FAMILY_TO_TARGET[task_family_value]
    config = rubric_config_for_task_family(task_family_value, rubric_version)
    evidence_block = build_evidence_block(task_family_value, source_bundle)
    rubric_axes_listing = "\n".join(f"- `{axis}`" for axis in config.axes)
    axis_guidance = "\n".join(_format_axis_guidance(axis, config) for axis in config.axes)
    score_descriptor = "as an integer 0, 1, 2, or 3" if config.score_type == "integer" else "0.0 to 1.0"
    family_note = ""
    if config.rubric_version == "v3" and task_family_value == "abstract_from_evidence":
        family_note = (
            "\nFor `abstract_from_evidence`, use `quantitative_specificity` instead of `traceability`. "
            "Reward concrete p-values, sample sizes, effect sizes, accessions, organism names, and similar "
            "evidence-backed specifics. Do not require figure or table citations for abstracts.\n"
        )

    return f"""You are an expert biomedical scientific-writing reviewer performing a rigorous peer-review-style evaluation.

Your job: score the candidate model's generated "{section_title}" section against the source evidence for the `{task_family_value}` task family, using the rubric below. Be strict and specific. Punish invented numbers, invented experiments, misattributed figures, and claims that cannot be traced to the provided evidence. Reward outputs whose details are demonstrably present in the evidence.

## Rubric axes (score each {score_descriptor})

{rubric_axes_listing}

{family_note}Axis definitions:

{axis_guidance}

## Pass threshold

{_pass_rule_description(config)}

## Source evidence

{evidence_block}

## Candidate output (to be judged)

{submission_text}

## Output format

Respond with ONLY a single JSON object. No prose before or after. No markdown code fences. The JSON must match this schema exactly:

{_output_schema_block(config)}"""


# ---------------------------------------------------------------------------
# API adapters
# ---------------------------------------------------------------------------


def call_anthropic(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, timeout: int = 300) -> Dict[str, Any]:
    return shared_call_anthropic(
        prompt,
        provider=provider,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


def call_openai_compatible(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, timeout: int = 300) -> Dict[str, Any]:
    return shared_call_openai_compatible(
        prompt,
        provider=provider,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


def _error_message(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            body = ""
        body = re.sub(r"\s+", " ", body)
        if body:
            if len(body) > 500:
                body = body[:500] + "..."
            return f"{exc}; body={body}"
    return str(exc)


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
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            ConnectionError,
            socket.timeout,
        ) as exc:
            last_exc = exc
            if attempt == attempts:
                break
            sleep_for = backoff_seconds * (2 ** (attempt - 1))
            print(
                f"    attempt {attempt} failed ({_error_message(exc)}); sleeping {sleep_for:.1f}s",
                file=sys.stderr,
            )
            time.sleep(sleep_for)
    assert last_exc is not None
    raise RuntimeError(_error_message(last_exc)) from last_exc


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


def _coerce_axis_score(raw: Any, config: RubricConfig) -> float | int:
    try:
        score = float(raw)
    except (TypeError, ValueError):
        score = config.axis_min
    if config.score_type == "integer":
        score = float(int(score + 0.5))
    score = max(config.axis_min, min(config.axis_max, score))
    if config.score_type == "integer":
        return int(score)
    return round(score, 3)


def _coerce_bool(raw: Any, *, default: bool = False) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False
    return bool(raw)


def _passes_threshold_rule(axis_scores: Mapping[str, float | int], config: RubricConfig) -> bool:
    values = [float(axis_scores[axis]) for axis in config.axes]
    if not values:
        return False
    if config.pass_rule == PASS_RULE_MEAN:
        return (sum(values) / len(values)) >= config.pass_threshold
    return all(value >= config.pass_threshold for value in values)


def _blank_score_shape(config: RubricConfig, issue: str) -> Dict[str, Any]:
    zero = 0 if config.score_type == "integer" else 0.0
    return {
        "axis_scores": {axis: zero for axis in config.axes},
        "axis_rationales": {axis: "" for axis in config.axes},
        "grounding_issues": [issue],
        "overall_pass": False,
        "mean_axis_score": 0.0,
        "passes_threshold_rule": False,
        "all_axes_above_threshold": False,
        "judge_reported_pass_matches_rule": True,
    }


def _score_record_shape(payload: Mapping[str, Any], config: RubricConfig) -> Dict[str, Any]:
    axis_scores_raw = payload.get("axis_scores") or {}
    axis_rationales_raw = payload.get("axis_rationales") or {}
    axis_scores: Dict[str, float | int] = {}
    axis_rationales: Dict[str, str] = {}
    for axis in config.axes:
        raw = axis_scores_raw.get(axis, config.axis_min)
        axis_scores[axis] = _coerce_axis_score(raw, config)
        axis_rationales[axis] = str(axis_rationales_raw.get(axis, "")).strip()
    grounding_issues = [str(item) for item in (payload.get("grounding_issues") or [])]
    overall_pass = _coerce_bool(payload.get("overall_pass"))
    mean_axis_score = round(
        sum(float(axis_scores[axis]) for axis in config.axes) / len(config.axes),
        3,
    )
    threshold_rule_pass = _passes_threshold_rule(axis_scores, config)
    all_axes_pass = all(float(axis_scores[axis]) >= config.pass_threshold for axis in config.axes)
    return {
        "axis_scores": axis_scores,
        "axis_rationales": axis_rationales,
        "grounding_issues": grounding_issues,
        "overall_pass": overall_pass,
        "mean_axis_score": mean_axis_score,
        "passes_threshold_rule": threshold_rule_pass,
        "all_axes_above_threshold": all_axes_pass,
        "judge_reported_pass_matches_rule": overall_pass == threshold_rule_pass,
    }


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:12].upper()}"


def _pass_rule_label(config: RubricConfig) -> str:
    if config.pass_rule == PASS_RULE_MEAN:
        return f"mean axis score >= {config.pass_threshold:.1f}"
    return f"all axes >= {config.pass_threshold}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge", default=None)
    parser.add_argument("--registry-path", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--rubric-version", default=DEFAULT_RUBRIC_VERSION, choices=("v2", "v3"))
    parser.add_argument("--keys-file", default=str(Path.home() / ".api_keys"))
    parser.add_argument("--submissions-path", default=str(DEFAULT_SUBMISSIONS_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2000)
    parser.add_argument("--limit", type=int, default=None, help="only judge the first N submissions (dev)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pause-between-calls", type=float, default=0.3)
    args = parser.parse_args()

    judge_label = args.judge or default_model_label_for_role(
        "judge",
        preferred_label="claude-sonnet-4-6",
        registry_path=args.registry_path,
    )
    try:
        provider = load_frontier_model(judge_label, registry_path=args.registry_path, role="judge")
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    default_config = rubric_config_for_task_family("methods_to_text", args.rubric_version)

    keys = load_api_keys(Path(args.keys_file).expanduser())
    api_key = resolve_api_key(provider, keys)
    if not args.dry_run and provider.get("api_key_env") and not api_key:
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
        config = rubric_config_for_task_family(task_bundle.task_family.value, args.rubric_version)
        prompt = build_judge_prompt(
            task_bundle,
            source_bundle,
            submission["output_text"],
            rubric_version=args.rubric_version,
        )
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
            shape = _score_record_shape(parsed, config)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"    JSON parse failed: {exc}", file=sys.stderr)
            parse_failures.append({"task_bundle_id": task_bundle_id, "error": str(exc), "raw": output_text})
            shape = _blank_score_shape(config, f"judge output did not parse as JSON: {exc}")

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
                "judge_name": judge_label,
                "temperature": args.temperature,
                "rubric_version": config.rubric_version,
                "rubric_axes": list(config.axes),
                "pass_threshold": config.pass_threshold,
                "pass_rule": config.pass_rule,
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

    summary_axes = [
        axis
        for axis in SUMMARY_AXIS_ORDER
        if any(axis in record.get("axis_scores", {}) for record in judgments)
    ]
    per_axis: Dict[str, List[float]] = {axis: [] for axis in summary_axes}
    per_family: Dict[str, Dict[str, Any]] = {}
    total_judge_reported_pass = 0
    total_threshold_rule_pass = 0
    total_axes_pass = 0
    total_judge_threshold_agreement = 0
    mean_axis_scores: List[float] = []
    all_issues: List[Tuple[str, str]] = []

    for record in judgments:
        record_axes = tuple(record.get("rubric_axes") or tuple(record.get("axis_scores", {}).keys()))
        for axis in record_axes:
            per_axis.setdefault(axis, []).append(float(record["axis_scores"][axis]))
        family = record["task_family"]
        family_specific_axis = "quantitative_specificity" if "quantitative_specificity" in record_axes else "traceability"
        bucket = per_family.setdefault(
            family,
            {
                "total": 0,
                "judge_reported_pass": 0,
                "passes_threshold_rule": 0,
                "all_axes_above_threshold": 0,
                "judge_threshold_agreement": 0,
                "mean_axis_scores": [],
                "family_specific_axis": family_specific_axis,
                "axis_means": {axis: [] for axis in record_axes},
            },
        )
        bucket["total"] += 1
        bucket["family_specific_axis"] = family_specific_axis
        if record["overall_pass"]:
            bucket["judge_reported_pass"] += 1
            total_judge_reported_pass += 1
        if record["passes_threshold_rule"]:
            bucket["passes_threshold_rule"] += 1
            total_threshold_rule_pass += 1
        if record["all_axes_above_threshold"]:
            bucket["all_axes_above_threshold"] += 1
            total_axes_pass += 1
        if record["judge_reported_pass_matches_rule"]:
            bucket["judge_threshold_agreement"] += 1
            total_judge_threshold_agreement += 1
        bucket["mean_axis_scores"].append(float(record["mean_axis_score"]))
        mean_axis_scores.append(float(record["mean_axis_score"]))
        for axis in record_axes:
            bucket["axis_means"].setdefault(axis, []).append(float(record["axis_scores"][axis]))
        for issue in record.get("grounding_issues", []):
            all_issues.append((record["task_bundle_id"], issue))

    for family in per_family.values():
        family["mean_axis_score"] = _avg(family.pop("mean_axis_scores"))
        family["axis_means"] = {axis: _avg(values) for axis, values in family["axis_means"].items()}

    total_input_tokens = sum((row.get("input_tokens") or 0) for row in usage_rows)
    total_output_tokens = sum((row.get("output_tokens") or 0) for row in usage_rows)

    summary = {
        "judge": judge_label,
        "judge_model": provider["request_model"],
        "registry_path": str(Path(args.registry_path).expanduser()),
        "rubric_version": args.rubric_version,
        "pass_rule": default_config.pass_rule,
        "pass_rule_label": _pass_rule_label(default_config),
        "temperature": args.temperature,
        "total_submissions_judged": len(judgments),
        "judge_overall_pass": total_judge_reported_pass,
        "passes_threshold_rule": total_threshold_rule_pass,
        "all_axes_above_threshold": total_axes_pass,
        "judge_reported_pass_matches_rule": total_judge_threshold_agreement,
        "pass_threshold": default_config.pass_threshold,
        "mean_axis_score": _avg(mean_axis_scores),
        "per_axis_mean": {axis: _avg(per_axis[axis]) for axis in summary_axes},
        "per_axis_min": {axis: round(min(per_axis[axis], default=0.0), 3) for axis in summary_axes},
        "per_task_family": per_family,
        "total_grounding_issues": len(all_issues),
        "parse_failures": len(parse_failures),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "usage": usage_rows,
    }
    summary.update(
        {
            f"judge_{key}" if key != "request_model" else "judge_request_model": value
            for key, value in registry_entry_provenance(provider).items()
        }
    )
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    md_lines = [
        "# LLM Judge Evaluation",
        "",
        f"- judge: `{judge_label}` (request model: `{provider['request_model']}`)",
        f"- rubric version: `{args.rubric_version}`",
        f"- pass rule: `{summary['pass_rule_label']}`",
        f"- temperature: {args.temperature}",
        f"- submissions judged: {len(judgments)}",
        f"- threshold-rule pass: {total_threshold_rule_pass} / {len(judgments)}",
        f"- judge-reported overall_pass: {total_judge_reported_pass} / {len(judgments)}",
        f"- judge/rule agreement: {total_judge_threshold_agreement} / {len(judgments)}",
        f"- strict all-axes >= threshold: {total_axes_pass} / {len(judgments)}",
        f"- mean axis score: {summary['mean_axis_score']:.3f}",
        f"- grounding issues reported: {len(all_issues)}",
        f"- parse failures: {len(parse_failures)}",
        f"- total tokens: input={total_input_tokens}, output={total_output_tokens}",
        "",
        "## Per-axis means",
        "",
        "| axis | mean | min |",
        "| --- | ---: | ---: |",
    ]
    for axis in summary_axes:
        md_lines.append(
            f"| {axis} | {summary['per_axis_mean'][axis]:.3f} | {summary['per_axis_min'][axis]:.3f} |"
        )
    md_lines.extend(
        [
            "",
            "## Per task family",
            "",
            "| family | threshold pass / total | judge bool / total | mean axis score | mean structure | mean grounding | mean fidelity | specific axis | specific mean | mean no_halluc |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for family, bucket in sorted(per_family.items()):
        means = bucket["axis_means"]
        specific_axis = bucket["family_specific_axis"]
        md_lines.append(
            f"| {family} | {bucket['passes_threshold_rule']} / {bucket['total']} | "
            f"{bucket['judge_reported_pass']} / {bucket['total']} | "
            f"{bucket['mean_axis_score']:.3f} | "
            f"{means['writing_structure_compliance']:.3f} | {means['evidence_grounding']:.3f} | "
            f"{means['factual_fidelity']:.3f} | {specific_axis} | {means.get(specific_axis, 0.0):.3f} | "
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
