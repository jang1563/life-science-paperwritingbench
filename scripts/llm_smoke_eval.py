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
import re
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


PROMPT_VERSION = "v2"


def build_prompt(task_bundle, source_bundle, paper_title: str) -> str:
    task_family_value = task_bundle.task_family.value
    section_title, include_fields = TASK_FAMILY_TO_TARGET[task_family_value]

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

    if task_family_value == "abstract_from_evidence":
        length_guidance = "Use 150-300 words. Abstracts should be compact."
        citation_guidance = (
            "Abstracts do NOT cite figure or table numbers. Instead, name the specific entities, "
            "sample sizes, p-values, effect sizes, and accession identifiers as they appear in the "
            "evidence. Do not write 'as shown in Fig. 1' in an abstract."
        )
    else:
        length_guidance = "Use 200-400 words."
        citation_guidance = (
            "Cite specific figures and tables from the evidence using the exact label as it appears "
            "(e.g. 'Fig. 1', 'Figure 2B', 'Table 3'). Cite accession identifiers, trial-registry IDs, "
            "or repository URLs when they appear in the evidence. Quote quantitative values exactly "
            "as given (sample sizes, p-values, fold changes, time points, organism strains)."
        )

    prompt = f"""You are a biomedical scientific-writing assistant. Draft the "{section_title}" section of a research paper using ONLY the evidence provided below.

Hard requirements:
- Begin with a heading line that is exactly: {section_title}
- {length_guidance}
- Ground every substantive claim in a specific piece of the evidence.
- {citation_guidance}
- If a detail is not in the evidence, state that explicitly rather than inventing it. Do not speculate.
- Do not copy sentences verbatim from the evidence; paraphrase while preserving specific values and entities.

Forbidden patterns (these are automatic quality failures — do NOT do any of them):
- Inventing numerical values, p-values, sample sizes, organism names, or citations that are not in the evidence.
- Citing placeholder pointer labels like "methods_section", "abstract_section", "results_section", or "section_text". These are internal artifact names; they are not real scientific citations and must never appear in the output.
- Self-referential meta-commentary such as "this abstract" or "the methods_section of this paper".

Paper context:
- Paper title: {paper_title}
- Task family: {task_family_value}
- Study class: {task_bundle.study_class.value}
- Claim mode: {task_bundle.claim_mode.value}

Evidence:

{sections_block}

Write the "{section_title}" section now, starting with the required heading line and satisfying all requirements."""

    return prompt


# ---------------------------------------------------------------------------
# Citation-specificity metric — measures real citation patterns in the output
# to complement the existing traceability_coverage deterministic check, which
# is a token-overlap heuristic that is satisfied by placeholder pointer labels.
# ---------------------------------------------------------------------------


_FIGURE_REF_RE = re.compile(r"\b(?:Fig(?:ure)?s?\.?|FIG\.?)\s*\d+[A-Za-z]?(?:[-,\s]+\d+[A-Za-z]?)*\b")
_TABLE_REF_RE = re.compile(r"\bTable[s]?\s*\d+[A-Za-z]?(?:[-,\s]+\d+[A-Za-z]?)*\b", re.IGNORECASE)
_PVALUE_RE = re.compile(r"\b[pP]\s*[<>=]\s*0?\.\d+\b")
_NUMERIC_MAGNITUDE_RE = re.compile(r"\b\d[\d,]*\.?\d*\s*(?:%|-fold|fold|mg|kg|nm|μm|µm|mm|cm|ml|kb|bp|nM|µM|mM|mg/kg|mg/mL|ml/kg)\b", re.IGNORECASE)
_ACCESSION_RE = re.compile(
    r"\b(?:"
    r"GSE\d+|GSM\d+|SRR\d+|ERR\d+|PRJNA\d+|PXD\d+|"
    r"PDB[:\s]?[A-Za-z0-9]{4}|RRID:[A-Za-z0-9:_-]+|"
    r"NCT\d{8}|ISRCTN\d+|ACTRN\d+|"
    r"E-(?:MTAB|GEOD)-\d+"
    r")\b",
    re.IGNORECASE,
)
_REPO_URL_RE = re.compile(r"https?://(?:github\.com|github(?:\.[\w\-]+)+\.edu|gitlab\.com|bitbucket\.org|zenodo\.org|osf\.io|figshare\.com)/[\w\-./]+", re.IGNORECASE)

_FORBIDDEN_POINTER_TOKENS = (
    "methods_section",
    "results_section",
    "abstract_section",
    "section_text",
    "methods_evidence",
    "results_evidence",
)


def citation_specificity(output_text: str) -> Dict[str, Any]:
    """Return citation-specificity scoring for a generated section.

    - figure_refs / table_refs / pvalues / numeric_magnitudes / accessions / repo_urls:
      lists of unique matches.
    - forbidden_pointer_hits: placeholder tokens like "methods_section" found in the
      text (should be zero).
    - citation_count: total unique real-citation tokens.
    - citation_specificity_score: 1.0 if citation_count >= 3 and no forbidden hits;
      0.0 if citation_count == 0 or any forbidden hits; linear in between.
    - forbidden_pointer_free: bool.
    """
    def _uniq(pattern: "re.Pattern[str]") -> List[str]:
        seen = []
        for match in pattern.finditer(output_text):
            token = match.group(0)
            if token not in seen:
                seen.append(token)
        return seen

    figure_refs = _uniq(_FIGURE_REF_RE)
    table_refs = _uniq(_TABLE_REF_RE)
    pvalues = _uniq(_PVALUE_RE)
    numeric_magnitudes = _uniq(_NUMERIC_MAGNITUDE_RE)
    accessions = _uniq(_ACCESSION_RE)
    repo_urls = _uniq(_REPO_URL_RE)

    forbidden_hits = [token for token in _FORBIDDEN_POINTER_TOKENS if token in output_text]

    citation_count = (
        len(figure_refs) + len(table_refs) + len(pvalues)
        + len(numeric_magnitudes) + len(accessions) + len(repo_urls)
    )
    if forbidden_hits:
        score = 0.0
    elif citation_count == 0:
        score = 0.0
    elif citation_count >= 3:
        score = 1.0
    else:
        score = citation_count / 3.0

    return {
        "figure_refs": figure_refs,
        "table_refs": table_refs,
        "pvalues": pvalues,
        "numeric_magnitudes": numeric_magnitudes,
        "accessions": accessions,
        "repo_urls": repo_urls,
        "forbidden_pointer_hits": forbidden_hits,
        "citation_count": citation_count,
        "citation_specificity_score": round(score, 3),
        "forbidden_pointer_free": not forbidden_hits,
    }


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
    # Citation-specificity metric (supplementary to deterministic checks)
    for row, submission in zip(rows, submissions):
        row["citation"] = citation_specificity(submission.output_text)

    # Per-task-family breakdown
    family_stats: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        family = row["task_family"]
        bucket = family_stats.setdefault(
            family,
            {
                "total": 0,
                "passed": 0,
                "failed_task_bundle_ids": [],
                "failure_note_counter": {},
                "mean_citation_score": 0.0,
                "forbidden_pointer_free_count": 0,
                "_citation_scores": [],
            },
        )
        bucket["total"] += 1
        if row["deterministic_checks_passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed_task_bundle_ids"].append(row["task_bundle_id"])
            for note in row["notes"]:
                bucket["failure_note_counter"][note] = bucket["failure_note_counter"].get(note, 0) + 1
        bucket["_citation_scores"].append(row["citation"]["citation_specificity_score"])
        if row["citation"]["forbidden_pointer_free"]:
            bucket["forbidden_pointer_free_count"] += 1
    for bucket in family_stats.values():
        scores = bucket.pop("_citation_scores")
        bucket["mean_citation_score"] = round(sum(scores) / len(scores), 3) if scores else 0.0

    # Total token usage
    total_prompt_tokens = sum((row.get("prompt_tokens") or 0) for row in usage_rows)
    total_completion_tokens = sum((row.get("completion_tokens") or 0) for row in usage_rows)

    overall_mean_citation_score = (
        round(sum(row["citation"]["citation_specificity_score"] for row in rows) / len(rows), 3)
        if rows
        else 0.0
    )
    overall_forbidden_pointer_free = sum(
        1 for row in rows if row["citation"]["forbidden_pointer_free"]
    )

    summary = {
        "model": args.model,
        "request_model": provider["request_model"],
        "producer_id": producer_id,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "task_source": args.task_source,
        "prompt_version": PROMPT_VERSION,
        "num_tasks": len(picks),
        "pass_count": sum(1 for row in rows if row["deterministic_checks_passed"]),
        "mean_citation_specificity_score": overall_mean_citation_score,
        "forbidden_pointer_free_count": overall_forbidden_pointer_free,
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
        f"- prompt version: `{PROMPT_VERSION}`",
        f"- temperature: {args.temperature}",
        f"- tasks: {len(picks)}",
        f"- deterministic checks passed: {summary['pass_count']} / {len(picks)}",
        f"- mean citation_specificity score: {overall_mean_citation_score:.3f}",
        f"- forbidden-pointer-free outputs: {overall_forbidden_pointer_free} / {len(picks)}",
        f"- total tokens: prompt={total_prompt_tokens}, completion={total_completion_tokens}",
        "",
        "## Per task family",
        "",
        "| task_family | det. passed / total | mean citation | pointer-free / total | failure notes |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for family in sorted(family_stats):
        bucket = family_stats[family]
        note_summary = ", ".join(f"{k} ({v})" for k, v in sorted(bucket["failure_note_counter"].items(), key=lambda kv: -kv[1]))
        md_lines.append(
            f"| {family} | {bucket['passed']} / {bucket['total']} | {bucket['mean_citation_score']:.3f} | {bucket['forbidden_pointer_free_count']} / {bucket['total']} | {note_summary or '—'} |"
        )
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
