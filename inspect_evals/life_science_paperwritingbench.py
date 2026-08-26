from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from life_science_paperwritingbench.baselines import evaluate_submissions
from life_science_paperwritingbench.frontier_runtime import (
    call_model_with_retry,
    default_frontier_registry_path,
    default_model_label_for_role,
    load_api_keys,
    load_frontier_model,
    resolve_api_key,
)
from life_science_paperwritingbench.frontier_writing import (
    FRONTIER_SINGLE_PASS_PROMPT_VERSION,
    build_frontier_single_pass_prompt,
    frontier_submission_fingerprint,
    frontier_submission_id,
)
from life_science_paperwritingbench.io import (
    auto_review_source_bundle_from_dict,
    submission_record_from_dict,
    task_bundle_from_dict,
)
from life_science_paperwritingbench.models import SubmissionRecord, TaskBundle
from life_science_paperwritingbench.policy import TaskFamily


REPO_ROOT = Path(__file__).resolve().parent.parent
KB_ROOT = REPO_ROOT / "knowledge_base"
DEFAULT_TASK_BUNDLES_PATH = (
    KB_ROOT
    / "released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl"
)
DEFAULT_SOURCE_BUNDLES_PATH = (
    KB_ROOT
    / "enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v16.jsonl"
)
WRITING_FAMILIES: Tuple[TaskFamily, ...] = (
    TaskFamily.METHODS_TO_TEXT,
    TaskFamily.RESULTS_TO_TEXT,
    TaskFamily.ABSTRACT_FROM_EVIDENCE,
)
DEFAULT_FRONTIER_REGISTRY_PATH = default_frontier_registry_path()


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_writing_task_bundles(
    path: Path = DEFAULT_TASK_BUNDLES_PATH,
    *,
    task_families: Sequence[TaskFamily] = WRITING_FAMILIES,
    limit: Optional[int] = None,
) -> Tuple[TaskBundle, ...]:
    allowed = {task_family.value for task_family in task_families}
    bundles = [
        task_bundle_from_dict(row)
        for row in _load_jsonl(path)
        if str(row.get("task_family")) in allowed
    ]
    if limit is not None:
        bundles = bundles[:limit]
    return tuple(bundles)


def load_source_bundle_lookup(
    path: Path = DEFAULT_SOURCE_BUNDLES_PATH,
) -> Dict[str, Any]:
    return {
        row["paper_id"]: auto_review_source_bundle_from_dict(row)
        for row in _load_jsonl(path)
    }


def build_inspect_records(
    *,
    task_bundles_path: Path = DEFAULT_TASK_BUNDLES_PATH,
    source_bundles_path: Path = DEFAULT_SOURCE_BUNDLES_PATH,
    submissions_path: Optional[Path] = None,
    judgments_path: Optional[Path] = None,
    include_submission_scores: bool = False,
    limit: Optional[int] = None,
) -> Tuple[Dict[str, Any], ...]:
    bundles = load_writing_task_bundles(task_bundles_path, limit=limit)
    source_lookup = load_source_bundle_lookup(source_bundles_path)
    submission_lookup = load_submission_lookup(submissions_path) if submissions_path else {}
    judgment_lookup = load_judgment_lookup(judgments_path) if judgments_path else {}
    records = []
    for bundle in bundles:
        source_bundle = source_lookup.get(bundle.paper_id)
        metadata: Dict[str, Any] = {
            "task_bundle": bundle.to_dict(),
            "source_bundle": (
                source_bundle.to_dict()
                if source_bundle is not None and hasattr(source_bundle, "to_dict")
                else None
            ),
        }
        submission = submission_lookup.get(bundle.task_bundle_id)
        if submission is not None:
            metadata["submission_record"] = submission.to_dict()
            if include_submission_scores:
                metadata["submission_deterministic_evaluation"] = deterministic_score_text(
                    bundle,
                    submission.output_text,
                    producer_id=submission.producer_id,
                )
        judgment = judgment_lookup.get(bundle.task_bundle_id)
        if judgment is not None:
            metadata["judge_result"] = judgment
        records.append(
            {
                "id": bundle.task_bundle_id,
                "input": {
                    "task_bundle_id": bundle.task_bundle_id,
                    "task_family": bundle.task_family.value,
                    "study_class": bundle.study_class.value,
                    "claim_mode": bundle.claim_mode.value,
                    "paper_id": bundle.paper_id,
                },
                "metadata": metadata,
            }
        )
    return tuple(records)


def deterministic_score_text(
    task_bundle: TaskBundle,
    output_text: str,
    *,
    producer_id: str = "inspect",
    scoring_version: str = "v2",
) -> Dict[str, Any]:
    submission = SubmissionRecord(
        submission_id=f"inspect:{task_bundle.task_bundle_id}",
        task_bundle_id=task_bundle.task_bundle_id,
        source="inspect",
        producer_id=producer_id,
        output_text=output_text,
    )
    evaluation = evaluate_submissions((task_bundle,), (submission,), version=scoring_version)[0]
    return evaluation.to_dict()


def replay_submission_scores(
    submissions_path: Path,
    *,
    task_bundles_path: Path = DEFAULT_TASK_BUNDLES_PATH,
    scoring_version: str = "v2",
) -> Tuple[Dict[str, Any], ...]:
    bundle_lookup = {
        bundle.task_bundle_id: bundle
        for bundle in load_writing_task_bundles(task_bundles_path)
    }
    scored = []
    for row in _load_jsonl(submissions_path):
        submission = submission_record_from_dict(row)
        bundle = bundle_lookup.get(submission.task_bundle_id)
        if bundle is None:
            continue
        scored.append(deterministic_score_text(bundle, submission.output_text, producer_id=submission.producer_id, scoring_version=scoring_version))
    return tuple(scored)


def load_submission_lookup(submissions_path: Path) -> Dict[str, SubmissionRecord]:
    return {
        submission.task_bundle_id: submission
        for submission in (
            submission_record_from_dict(row)
            for row in _load_jsonl(submissions_path)
        )
    }


def load_judgment_lookup(judgments_path: Path) -> Dict[str, Dict[str, Any]]:
    return {
        str(row["task_bundle_id"]): row
        for row in _load_jsonl(judgments_path)
        if row.get("task_bundle_id")
    }


def replay_judge_results(
    judgments_path: Path,
    *,
    task_bundles_path: Path = DEFAULT_TASK_BUNDLES_PATH,
    limit: Optional[int] = None,
) -> Tuple[Dict[str, Any], ...]:
    bundle_lookup = {
        bundle.task_bundle_id: bundle
        for bundle in load_writing_task_bundles(task_bundles_path, limit=limit)
    }
    replayed = []
    for row in _load_jsonl(judgments_path):
        task_bundle_id = str(row.get("task_bundle_id") or "")
        bundle = bundle_lookup.get(task_bundle_id)
        if bundle is None:
            continue
        replayed.append(
            {
                "task_bundle_id": task_bundle_id,
                "task_family": bundle.task_family.value,
                "study_class": bundle.study_class.value,
                "claim_mode": bundle.claim_mode.value,
                **row,
            }
        )
    return tuple(replayed)


def generate_submission_records(
    *,
    model_label: Optional[str] = None,
    registry_path: Path = DEFAULT_FRONTIER_REGISTRY_PATH,
    keys_file: Path = Path.home() / ".api_keys",
    task_bundles_path: Path = DEFAULT_TASK_BUNDLES_PATH,
    source_bundles_path: Path = DEFAULT_SOURCE_BUNDLES_PATH,
    limit: Optional[int] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    pause_between_calls: float = 0.0,
    producer_namespace: str = "inspect",
    dry_run: bool = False,
    scoring_version: str = "v2",
) -> Tuple[Dict[str, Any], ...]:
    resolved_registry_path = Path(registry_path)
    resolved_model_label = model_label or default_model_label_for_role(
        "submitter",
        preferred_label="deepseek-chat",
        registry_path=resolved_registry_path,
    )
    provider = load_frontier_model(
        resolved_model_label,
        registry_path=resolved_registry_path,
        role="submitter",
    )
    effective_temperature = provider["temperature"] if temperature is None else temperature
    effective_max_tokens = provider["max_tokens"] if max_tokens is None else max_tokens

    keys = dict(os.environ)
    keys.update(load_api_keys(Path(keys_file).expanduser()))
    api_key = resolve_api_key(provider, keys)
    if not dry_run and provider.get("api_key_env") and not api_key:
        raise ValueError(f"missing {provider['api_key_env']} for model {resolved_model_label}")

    bundles = load_writing_task_bundles(task_bundles_path, limit=limit)
    source_lookup = load_source_bundle_lookup(source_bundles_path)
    producer_id = f"{producer_namespace}:{resolved_model_label}@temp={effective_temperature}"

    rows = []
    for index, bundle in enumerate(bundles, start=1):
        source_bundle = source_lookup.get(bundle.paper_id)
        if source_bundle is None:
            continue
        paper_title = str((source_bundle.provenance_fields or {}).get("title") or bundle.paper_id)
        prompt = build_frontier_single_pass_prompt(bundle, source_bundle, paper_title)
        if dry_run:
            output_text = "(dry run placeholder)"
            usage = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
        else:
            response = call_model_with_retry(
                prompt,
                provider=provider,
                api_key=api_key,
                temperature=float(effective_temperature),
                max_tokens=int(effective_max_tokens),
            )
            output_text = str(response["output_text"])
            usage = dict(response.get("usage") or {})
            if pause_between_calls > 0 and index < len(bundles):
                time.sleep(pause_between_calls)

        submission = SubmissionRecord(
            submission_id=frontier_submission_id(bundle.task_bundle_id, producer_id),
            task_bundle_id=bundle.task_bundle_id,
            source="inspect",
            producer_id=producer_id,
            output_text=output_text,
            config_fingerprint_sha256=frontier_submission_fingerprint(
                {
                    "model": resolved_model_label,
                    "request_model": provider["request_model"],
                    "temperature": effective_temperature,
                    "max_tokens": effective_max_tokens,
                    "task_bundle_id": bundle.task_bundle_id,
                    "prompt_version": FRONTIER_SINGLE_PASS_PROMPT_VERSION,
                    "producer_id": producer_id,
                }
            ),
        )
        rows.append(
            {
                "task_bundle_id": bundle.task_bundle_id,
                "model": resolved_model_label,
                "request_model": provider["request_model"],
                "backend_type": provider.get("backend_type"),
                "provider_name": provider.get("provider_name"),
                "execution_target": provider.get("execution_target"),
                "model_version_note": provider.get("model_version_note"),
                "registry_path": str(resolved_registry_path),
                "temperature": effective_temperature,
                "max_tokens": effective_max_tokens,
                "prompt_version": FRONTIER_SINGLE_PASS_PROMPT_VERSION,
                "prompt": prompt,
                "submission_record": submission.to_dict(),
                "usage": usage,
                "deterministic_evaluation": deterministic_score_text(
                    bundle,
                    output_text,
                    producer_id=submission.producer_id,
                    scoring_version=scoring_version,
                ),
            }
        )
    return tuple(rows)


def inspect_task(
    *,
    limit: Optional[int] = None,
    submissions_path: Optional[Path] = None,
    judgments_path: Optional[Path] = None,
    include_submission_scores: bool = False,
):
    try:
        from inspect_ai import Task, task
        from inspect_ai.dataset import MemoryDataset, Sample
    except ImportError as exc:
        raise ImportError("inspect_ai is required to construct the Inspect task wrapper") from exc

    records = build_inspect_records(
        limit=limit,
        submissions_path=submissions_path,
        judgments_path=judgments_path,
        include_submission_scores=include_submission_scores,
    )
    dataset = MemoryDataset(
        samples=[
            Sample(
                id=record["id"],
                input=record["input"],
                metadata=record["metadata"],
            )
            for record in records
        ]
    )

    @task
    def life_science_paperwritingbench_task():
        return Task(dataset=dataset)

    return life_science_paperwritingbench_task
