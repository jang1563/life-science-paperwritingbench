#!/usr/bin/env python3
"""Smoke-test LLM evaluation on a handful of public shadow task bundles.

This script is deliberately minimal:

- Picks one task bundle per task family (methods_to_text, results_to_text,
  abstract_from_evidence) from the public shadow slice.
- Builds a grounded prompt from the paper's source bundle (title, abstract,
  other sections, figure captions, table snippets, trial-registry snippets).
- Calls a cost-effective model through an OpenAI-compatible endpoint.
- Writes SubmissionRecord JSONL, runs evaluate_submissions() from the
  package, and prints a deterministic-checks summary.

Usage:

    source ~/.api_keys
    PYTHONPATH=src python3 scripts/llm_smoke_eval.py

Or pass --keys-file to read keys from a specific file.

Pricing footprint: ~3 calls × (~3k input + ~600 output) tokens = negligible.
Intended as the first end-to-end LLM run to validate the pipeline before
scaling to the full 30-paper public slice or running judge validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from life_science_paperwritingbench.baselines import evaluate_submissions  # noqa: E402
from life_science_paperwritingbench.io import (  # noqa: E402
    auto_review_source_bundle_from_dict,
    task_bundle_from_dict,
)
from life_science_paperwritingbench.models import (  # noqa: E402
    SubmissionRecord,
    TaskFamily,
)


# ---------------------------------------------------------------------------
# Provider catalog
# ---------------------------------------------------------------------------

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "deepseek-chat": {
        "endpoint": "https://api.deepseek.com/chat/completions",
        "api_key_env": "DEEPSEEK_API_KEY",
        "request_model": "deepseek-chat",
    },
    "gemini-2.5-flash": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key_env": "GEMINI_API_KEY",
        "request_model": "gemini-2.5-flash",
    },
    "gpt-4o-mini": {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "request_model": "gpt-4o-mini",
    },
}

DEFAULT_MODEL = "deepseek-chat"

# ---------------------------------------------------------------------------
# Task selection
# ---------------------------------------------------------------------------

# One task bundle per task family — covers the main family axis in one run.
# Pins to specific bundles that are in the public shadow slice and whose
# source bundles have full methods/results/figures text (i.e. not the
# non-OA fulltext_acquisition_gap cohort).
DEFAULT_TASK_BUNDLE_IDS: Sequence[str] = (
    "TB:BU:EUAUTO:0647BFACA729",  # methods_to_text    — DOI:10.1111/cas.13569
    "TB:BU:EUAUTO:DE9706E77A3C",  # results_to_text    — DOI:10.1186/s13018-023-04496-9
    "TB:BU:EUAUTO:EFABE066E1CC",  # abstract_from_evidence — DOI:10.1128/mbio.00933-24
)

# Data locations (gitignored on disk)
KB_ROOT = REPO_ROOT / "knowledge_base"
TASK_BUNDLES_PATH = (
    KB_ROOT
    / "released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl"
)
SOURCE_BUNDLES_PATH = (
    KB_ROOT
    / "enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v16.jsonl"
)
INSPECTION_SLICE_PATH = (
    KB_ROOT
    / "released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v11.jsonl"
)
OUTPUT_DIR_SMOKE = REPO_ROOT / "calibration/llm_smoke_v1"
OUTPUT_DIR_SLICE = REPO_ROOT / "calibration/llm_public_slice_v1"


# ---------------------------------------------------------------------------
# API-key loading (supports `export FOO=bar` or `FOO=bar` per line)
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


# ---------------------------------------------------------------------------
# JSONL loaders
# ---------------------------------------------------------------------------


def load_task_bundles(path: Path) -> List[Any]:
    bundles = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                bundles.append(task_bundle_from_dict(json.loads(line)))
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


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


TASK_FAMILY_TO_TARGET: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "methods_to_text": ("Methods", ("abstract_text", "results_text", "figure_captions", "table_snippets")),
    "results_to_text": ("Results", ("abstract_text", "methods_text", "figure_captions", "table_snippets")),
    "abstract_from_evidence": ("Abstract", ("methods_text", "results_text", "figure_captions", "table_snippets")),
}


def _clip(text: str, limit: int = 6000) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_list(items: Sequence[str], limit_each: int = 800, max_items: int = 8) -> str:
    if not items:
        return "(none provided)"
    lines = []
    for idx, item in enumerate(items[:max_items], start=1):
        lines.append(f"{idx}. {_clip(item, limit_each)}")
    return "\n".join(lines)


def build_prompt(task_bundle, source_bundle, paper_title: str) -> str:
    task_family_value = task_bundle.task_family.value
    section_title, include_fields = TASK_FAMILY_TO_TARGET[task_family_value]

    artifacts = dict(task_bundle.input_artifacts)
    evidence_tokens: List[str] = []
    for key in ("evidence_pointers", "evidence_items", "evidence_types"):
        for value in artifacts.get(key, ()) or ():
            if isinstance(value, str) and value and value not in evidence_tokens:
                evidence_tokens.append(value)

    sections: List[Tuple[str, str]] = []
    if "abstract_text" in include_fields and source_bundle.abstract_text:
        sections.append(("Abstract", _clip(source_bundle.abstract_text)))
    if "methods_text" in include_fields and source_bundle.methods_text:
        sections.append(("Methods", _clip(source_bundle.methods_text)))
    if "results_text" in include_fields and source_bundle.results_text:
        sections.append(("Results", _clip(source_bundle.results_text)))
    if "figure_captions" in include_fields and source_bundle.figure_captions:
        sections.append(("Figure captions", _format_list(source_bundle.figure_captions)))
    if "table_snippets" in include_fields and source_bundle.table_snippets:
        sections.append(("Table snippets", _format_list(source_bundle.table_snippets)))

    sections_block = "\n\n".join(f"## {title}\n{content}" for title, content in sections)
    evidence_line = ", ".join(evidence_tokens) if evidence_tokens else "(none listed)"

    prompt = f"""You are a biomedical scientific-writing assistant. Draft the \"{section_title}\" section of a research paper, grounded strictly in the evidence provided below.

Hard requirements:
- Begin with a heading line that is exactly: {section_title}
- Explicitly mention the word \"evidence\" at least once in the body.
- Explicitly cite every one of the following evidence identifiers by name, spelled exactly as written, somewhere in the prose: {evidence_line}.
- Use at least 120 words and no more than 350 words.
- Do not copy sentences verbatim from the source paper; rephrase.
- Do not fabricate findings, quantities, or citations not present in the evidence.
- If a detail is missing, say so explicitly rather than inventing it.

Paper context:
- Paper title: {paper_title}
- Task family: {task_family_value}
- Study class: {task_bundle.study_class.value}
- Claim mode: {task_bundle.claim_mode.value}

Evidence:

{sections_block}

Write the \"{section_title}\" section now, starting with the required heading line and satisfying all hard requirements."""

    return prompt


# ---------------------------------------------------------------------------
# LLM call (OpenAI-compatible)
# ---------------------------------------------------------------------------


def call_llm(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float = 0.2, max_tokens: int = 1200, timeout: int = 120) -> Dict[str, Any]:
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
    return decoded


def call_llm_with_retry(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, attempts: int = 3, backoff_seconds: float = 2.0) -> Dict[str, Any]:
    last_exc: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            return call_llm(
                prompt,
                provider=provider,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_exc = exc
            if attempt == attempts:
                break
            sleep_for = backoff_seconds * (2 ** (attempt - 1))
            print(f"    attempt {attempt} failed ({exc}); sleeping {sleep_for:.1f}s", file=sys.stderr)
            time.sleep(sleep_for)
    assert last_exc is not None
    raise last_exc


# ---------------------------------------------------------------------------
# Submission writing + scoring
# ---------------------------------------------------------------------------


def _stable_submission_id(task_bundle_id: str, producer_id: str) -> str:
    digest = hashlib.sha256(f"{task_bundle_id}|{producer_id}".encode("utf-8")).hexdigest()
    return f"SUB:{digest[:12].upper()}"


def _fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_inspection_slice_bundle_ids(path: Path) -> List[str]:
    ids: List[str] = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("task_bundle_id"):
                ids.append(entry["task_bundle_id"])
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(PROVIDERS))
    parser.add_argument("--keys-file", default=str(Path.home() / ".api_keys"))
    parser.add_argument("--output-dir", default=None, help="defaults depend on --task-source")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--dry-run", action="store_true", help="print prompts only; do not call the model")
    parser.add_argument(
        "--task-source",
        choices=("smoke", "inspection-slice"),
        default="smoke",
        help="smoke: 3 pinned bundles (one per task family). inspection-slice: all 30 entries from shadow_public_inspection_v11.jsonl.",
    )
    parser.add_argument("--pause-between-calls", type=float, default=0.3, help="seconds to sleep between calls to be polite to the API")
    args = parser.parse_args()

    provider = PROVIDERS[args.model]
    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif args.task_source == "inspection-slice":
        output_dir = OUTPUT_DIR_SLICE
    else:
        output_dir = OUTPUT_DIR_SMOKE
    output_dir.mkdir(parents=True, exist_ok=True)

    keys = load_api_keys(Path(args.keys_file).expanduser())
    env_key = os.environ.get(provider["api_key_env"])
    api_key = env_key or keys.get(provider["api_key_env"])
    if not args.dry_run and not api_key:
        print(f"Missing {provider['api_key_env']} (checked env and {args.keys_file})", file=sys.stderr)
        return 2

    task_bundles = {bundle.task_bundle_id: bundle for bundle in load_task_bundles(TASK_BUNDLES_PATH)}
    source_bundles = load_source_bundles(SOURCE_BUNDLES_PATH)

    if args.task_source == "inspection-slice":
        selected_ids: Sequence[str] = _load_inspection_slice_bundle_ids(INSPECTION_SLICE_PATH)
    else:
        selected_ids = DEFAULT_TASK_BUNDLE_IDS

    picks = []
    for task_bundle_id in selected_ids:
        match = task_bundles.get(task_bundle_id)
        if match is None:
            print(f"No task bundle found for id={task_bundle_id}", file=sys.stderr)
            continue
        if match.paper_id not in source_bundles:
            print(f"No source bundle for paper_id={match.paper_id}", file=sys.stderr)
            continue
        picks.append(match)

    if not picks:
        print("No task bundles selected; aborting.", file=sys.stderr)
        return 3

    producer_id = f"llm:{args.model}@temp={args.temperature}"
    submissions: List[SubmissionRecord] = []
    usage_rows: List[Dict[str, Any]] = []

    for idx, bundle in enumerate(picks, start=1):
        source_bundle = source_bundles[bundle.paper_id]
        paper_title = str((source_bundle.provenance_fields or {}).get("title") or bundle.paper_id)
        prompt = build_prompt(bundle, source_bundle, paper_title)
        prompt_path = output_dir / f"prompt_{idx:02d}_{bundle.task_bundle_id.replace(':','_')}.md"
        prompt_path.write_text(prompt)

        if args.dry_run:
            print(f"[{idx}/{len(picks)}] DRY RUN — wrote prompt to {prompt_path}")
            output_text = "(dry run placeholder)"
            usage = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
        else:
            print(f"[{idx}/{len(picks)}] calling {args.model} on {bundle.task_bundle_id} ({bundle.task_family.value})")
            started = time.time()
            response = call_llm_with_retry(
                prompt,
                provider=provider,
                api_key=api_key,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            elapsed = time.time() - started
            output_text = response["choices"][0]["message"]["content"].strip()
            usage = dict(response.get("usage") or {})
            usage["elapsed_seconds"] = round(elapsed, 2)
            print(f"    done in {elapsed:.1f}s  prompt_tokens={usage.get('prompt_tokens')} completion_tokens={usage.get('completion_tokens')}")
            if args.pause_between_calls > 0 and idx < len(picks):
                time.sleep(args.pause_between_calls)

        submission_id = _stable_submission_id(bundle.task_bundle_id, producer_id)
        fingerprint = _fingerprint(
            {
                "model": args.model,
                "request_model": provider["request_model"],
                "temperature": args.temperature,
                "task_bundle_id": bundle.task_bundle_id,
                "producer_id": producer_id,
            }
        )
        submissions.append(
            SubmissionRecord(
                submission_id=submission_id,
                task_bundle_id=bundle.task_bundle_id,
                source="llm",
                producer_id=producer_id,
                output_text=output_text,
                config_fingerprint_sha256=fingerprint,
            )
        )
        usage_rows.append({"task_bundle_id": bundle.task_bundle_id, **usage})

    # Write submissions
    submissions_path = output_dir / "submissions.jsonl"
    with submissions_path.open("w") as handle:
        for submission in submissions:
            handle.write(json.dumps(submission.to_dict()) + "\n")

    # Evaluate via the package's deterministic checks
    evaluations = evaluate_submissions(picks, submissions)
    evaluations_path = output_dir / "evaluations.jsonl"
    with evaluations_path.open("w") as handle:
        for evaluation in evaluations:
            handle.write(json.dumps(evaluation.to_dict()) + "\n")

    # Summary
    rows: List[Dict[str, Any]] = []
    for bundle, submission, evaluation in zip(picks, submissions, evaluations):
        rows.append(
            {
                "paper_id": bundle.paper_id,
                "task_family": bundle.task_family.value,
                "task_bundle_id": bundle.task_bundle_id,
                "deterministic_checks_passed": evaluation.deterministic_checks_passed,
                "scores": dict(evaluation.scores),
                "notes": list(evaluation.notes),
                "output_word_count": len(submission.output_text.split()),
            }
        )
    # Per-task-family breakdown
    family_stats: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        family = row["task_family"]
        bucket = family_stats.setdefault(
            family,
            {"total": 0, "passed": 0, "failed_task_bundle_ids": [], "failure_note_counter": {}},
        )
        bucket["total"] += 1
        if row["deterministic_checks_passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed_task_bundle_ids"].append(row["task_bundle_id"])
            for note in row["notes"]:
                bucket["failure_note_counter"][note] = bucket["failure_note_counter"].get(note, 0) + 1

    # Total token usage
    total_prompt_tokens = sum((row.get("prompt_tokens") or 0) for row in usage_rows)
    total_completion_tokens = sum((row.get("completion_tokens") or 0) for row in usage_rows)

    summary = {
        "model": args.model,
        "request_model": provider["request_model"],
        "producer_id": producer_id,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "task_source": args.task_source,
        "num_tasks": len(picks),
        "pass_count": sum(1 for row in rows if row["deterministic_checks_passed"]),
        "by_task_family": family_stats,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "task_rows": rows,
        "usage": usage_rows,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    # Markdown brief
    md_lines = [
        "# LLM Evaluation",
        "",
        f"- model: `{args.model}` (request model: `{provider['request_model']}`)",
        f"- task source: `{args.task_source}`",
        f"- temperature: {args.temperature}",
        f"- tasks: {len(picks)}",
        f"- deterministic checks passed: {summary['pass_count']} / {len(picks)}",
        f"- total tokens: prompt={total_prompt_tokens}, completion={total_completion_tokens}",
        "",
        "## Per task family",
        "",
        "| task_family | passed / total | failure notes |",
        "| --- | ---: | --- |",
    ]
    for family in sorted(family_stats):
        bucket = family_stats[family]
        note_summary = ", ".join(f"{k} ({v})" for k, v in sorted(bucket["failure_note_counter"].items(), key=lambda kv: -kv[1]))
        md_lines.append(f"| {family} | {bucket['passed']} / {bucket['total']} | {note_summary or '—'} |")
    md_lines.extend(["", "## Per task", ""])
    for row in rows:
        md_lines.extend(
            [
                f"### {row['task_family']} — {row['paper_id']}",
                "",
                f"- task_bundle_id: `{row['task_bundle_id']}`",
                f"- deterministic_checks_passed: **{row['deterministic_checks_passed']}**",
                f"- output words: {row['output_word_count']}",
                f"- scores: `{row['scores']}`",
                f"- notes: {row['notes'] or '(none)'}",
                "",
            ]
        )
    (output_dir / "summary.md").write_text("\n".join(md_lines) + "\n")

    print()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
