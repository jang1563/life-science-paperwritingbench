from __future__ import annotations

import hashlib
import json
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .models import BaselineRunSpec, EvaluationRecord, SubmissionRecord, TaskBundle
from .policy import BaselineKind, EvaluationLayer, TaskFamily
from .program import LEAN_BASELINES


def _canonical_payload(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, payload: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_payload(payload).encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}:{digest}"


def _flatten_values(value: object) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        flattened: List[str] = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return tuple(flattened)
    return (str(value),)


def _dedupe_preserve_order(values: Iterable[str]) -> Tuple[str, ...]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


def _evidence_tokens(task_bundle: TaskBundle) -> Tuple[str, ...]:
    artifacts = dict(task_bundle.input_artifacts)
    tokens: List[str] = []
    for key in ("evidence_pointers", "evidence_items", "evidence_types"):
        tokens.extend(_flatten_values(artifacts.get(key)))
    return _dedupe_preserve_order(token for token in tokens if token)


def _section_title(task_family: TaskFamily) -> str:
    if task_family == TaskFamily.RESULTS_TO_TEXT:
        return "Results"
    if task_family == TaskFamily.METHODS_TO_TEXT:
        return "Methods"
    if task_family == TaskFamily.ABSTRACT_FROM_EVIDENCE:
        return "Abstract"
    if task_family == TaskFamily.REVIEW_REVISION_RESPONSE:
        return "Response"
    if task_family in {
        TaskFamily.LITERATURE_QA,
        TaskFamily.TRIAL_QA,
        TaskFamily.FIGURE_QA,
        TaskFamily.TABLE_QA,
    }:
        return "Answer"
    if task_family == TaskFamily.SOURCE_QUALITY_QA:
        return "Assessment"
    raise KeyError(f"unsupported task family: {task_family.value}")


def _render_reference_template(task_bundle: TaskBundle) -> str:
    title = _section_title(task_bundle.task_family)
    evidence = ", ".join(_evidence_tokens(task_bundle)[:4]) or "provided evidence items"
    question_prompt = str(task_bundle.input_artifacts.get("question_prompt", "")).strip()
    observation_texts = tuple(task_bundle.input_artifacts.get("supporting_observation_texts", ()))
    if question_prompt:
        response_text = " ".join(str(item) for item in observation_texts[:2]) or "The answer is grounded in the supplied evidence."
        return (
            f"{title}\n"
            f"Question: {question_prompt}\n"
            f"Evidence basis: {evidence}.\n"
            f"Response: {response_text}"
        )
    return (
        f"{title}\n"
        f"Evidence basis: {evidence}.\n"
        f"This template baseline summarizes the supplied {task_bundle.task_family.value} inputs "
        f"for a {task_bundle.study_class.value} / {task_bundle.claim_mode.value} task."
    )


def _render_retrieval_writer(task_bundle: TaskBundle) -> str:
    title = _section_title(task_bundle.task_family)
    evidence = _evidence_tokens(task_bundle)
    evidence_clause = ", ".join(evidence[:5]) if evidence else "the provided evidence items"
    question_prompt = str(task_bundle.input_artifacts.get("question_prompt", "")).strip()
    observation_texts = tuple(task_bundle.input_artifacts.get("supporting_observation_texts", ()))
    if question_prompt:
        response_text = " ".join(str(item) for item in observation_texts[:3]) or "The answer is grounded in the provided evidence."
        return (
            f"{title}\n"
            f"Question: {question_prompt}\n"
            f"Evidence basis: {evidence_clause}.\n"
            f"Response: {response_text}"
        )
    return (
        f"{title}\n"
        f"Grounded in {evidence_clause}, this retrieval-style baseline writes a concise draft for the "
        f"{task_bundle.task_family.value} task. Traceability is maintained by explicitly citing the "
        f"provided evidence identifiers throughout the response."
    )


def _render_section_wise_pipeline(task_bundle: TaskBundle) -> str:
    title = _section_title(task_bundle.task_family)
    evidence = ", ".join(_evidence_tokens(task_bundle)[:5]) or "provided evidence items"
    question_prompt = str(task_bundle.input_artifacts.get("question_prompt", "")).strip()
    observation_texts = tuple(task_bundle.input_artifacts.get("supporting_observation_texts", ()))
    if question_prompt:
        response_text = " ".join(str(item) for item in observation_texts[:3]) or "Supported by the provided evidence."
        return (
            f"{title}\n"
            f"Question: {question_prompt}\n"
            f"Evidence used: {evidence}.\n"
            f"Response: {response_text}"
        )
    return (
        f"{title}\n"
        f"Scope: {task_bundle.study_class.value} / {task_bundle.claim_mode.value}.\n"
        f"Evidence used: {evidence}.\n"
        f"Draft: This section-wise pipeline baseline organizes the requested content using only the "
        f"supplied benchmark evidence and keeps traceability visible in the prose."
    )


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def render_baseline_output(task_bundle: TaskBundle, baseline_kind: BaselineKind) -> str:
    if baseline_kind == BaselineKind.REFERENCE_TEMPLATE:
        return _render_reference_template(task_bundle)
    if baseline_kind == BaselineKind.RETRIEVAL_WRITER:
        return _render_retrieval_writer(task_bundle)
    if baseline_kind == BaselineKind.SECTION_WISE_PIPELINE:
        return _render_section_wise_pipeline(task_bundle)
    raise ValueError(
        "only lean baselines are currently implemented: "
        + ", ".join(sorted(item.value for item in LEAN_BASELINES))
    )


def run_baseline(
    task_bundles: Sequence[TaskBundle],
    baseline_kind: BaselineKind,
    producer_id: Optional[str] = None,
) -> Tuple[BaselineRunSpec, Tuple[SubmissionRecord, ...]]:
    if baseline_kind not in LEAN_BASELINES:
        raise ValueError(
            "run_baseline currently supports only lean baselines: "
            + ", ".join(sorted(item.value for item in LEAN_BASELINES))
        )

    normalized_producer_id = producer_id or f"baseline:{baseline_kind.value}"
    submissions: List[SubmissionRecord] = []
    for task_bundle in task_bundles:
        output_text = render_baseline_output(task_bundle, baseline_kind)
        submission_id = _stable_id(
            "SUB",
            {
                "task_bundle_id": task_bundle.task_bundle_id,
                "baseline_kind": baseline_kind.value,
                "producer_id": normalized_producer_id,
            },
        )
        config_fingerprint = hashlib.sha256(
            _canonical_payload(
                {
                    "baseline_kind": baseline_kind.value,
                    "task_bundle_id": task_bundle.task_bundle_id,
                    "producer_id": normalized_producer_id,
                }
            ).encode("utf-8")
        ).hexdigest()
        submissions.append(
            SubmissionRecord(
                submission_id=submission_id,
                task_bundle_id=task_bundle.task_bundle_id,
                source="baseline",
                producer_id=normalized_producer_id,
                output_text=output_text,
                config_fingerprint_sha256=config_fingerprint,
            )
        )

    run_spec = BaselineRunSpec(
        baseline_id=_stable_id(
            "BASE",
            {
                "baseline_kind": baseline_kind.value,
                "task_bundle_ids": tuple(bundle.task_bundle_id for bundle in task_bundles),
                "producer_id": normalized_producer_id,
            },
        ),
        baseline_kind=baseline_kind,
        task_bundle_ids=tuple(bundle.task_bundle_id for bundle in task_bundles),
        config_fingerprint_sha256=hashlib.sha256(
            _canonical_payload(
                {
                    "baseline_kind": baseline_kind.value,
                    "task_bundle_ids": tuple(bundle.task_bundle_id for bundle in task_bundles),
                    "producer_id": normalized_producer_id,
                }
            ).encode("utf-8")
        ).hexdigest(),
        replay_verified=True,
        notes=("deterministic lean baseline replay",),
    )
    return run_spec, tuple(submissions)


def evaluate_submission(task_bundle: TaskBundle, submission: SubmissionRecord) -> EvaluationRecord:
    if submission.task_bundle_id != task_bundle.task_bundle_id:
        raise ValueError("submission and task bundle must share the same task_bundle_id")

    normalized_output = " ".join(submission.output_text.lower().split())
    evidence_tokens = _evidence_tokens(task_bundle)
    traceable_matches = sum(
        1 for token in evidence_tokens if token.lower() in normalized_output
    )
    traceability_score = (
        traceable_matches / len(evidence_tokens)
        if evidence_tokens
        else 1.0
    )

    section_marker = _section_title(task_bundle.task_family).lower()
    structure_markers = {
        TaskFamily.RESULTS_TO_TEXT: ("results", "evidence"),
        TaskFamily.METHODS_TO_TEXT: ("methods", "evidence"),
        TaskFamily.ABSTRACT_FROM_EVIDENCE: ("abstract", "evidence"),
        TaskFamily.REVIEW_REVISION_RESPONSE: ("response", "evidence"),
        TaskFamily.LITERATURE_QA: ("answer", "question"),
        TaskFamily.TRIAL_QA: ("answer", "question"),
        TaskFamily.FIGURE_QA: ("answer", "question"),
        TaskFamily.TABLE_QA: ("answer", "question"),
        TaskFamily.SOURCE_QUALITY_QA: ("assessment", "question"),
    }[task_bundle.task_family]
    structure_score = 1.0 if all(marker in normalized_output for marker in structure_markers) else 0.0
    non_empty_score = 1.0 if submission.output_text.strip() else 0.0
    word_count = len(submission.output_text.split())
    length_floor_score = 1.0 if word_count >= 12 else 0.0
    expected_answer_texts = tuple(
        str(item) for item in task_bundle.input_artifacts.get("expected_answer_texts", ())
    )
    if expected_answer_texts:
        answer_support_score = 1.0 if any(
            _normalize_text(answer_text) in normalized_output
            for answer_text in expected_answer_texts
            if _normalize_text(answer_text)
        ) else 0.0
    else:
        answer_support_score = 1.0
    deterministic_checks_passed = (
        non_empty_score == 1.0
        and structure_score == 1.0
        and length_floor_score == 1.0
        and traceability_score >= 0.5
        and answer_support_score == 1.0
    )
    notes: List[str] = []
    if section_marker not in normalized_output:
        notes.append(f"missing expected section marker: {section_marker}")
    if traceability_score < 0.5:
        notes.append("traceability coverage below threshold")
    if word_count < 12:
        notes.append("output is shorter than the deterministic length floor")
    if answer_support_score < 1.0:
        notes.append("output does not sufficiently match expected supported answer text")

    return EvaluationRecord(
        evaluation_id=_stable_id(
            "EVAL",
            {
                "submission_id": submission.submission_id,
                "task_bundle_id": task_bundle.task_bundle_id,
            },
        ),
        submission_id=submission.submission_id,
        task_bundle_id=task_bundle.task_bundle_id,
        evaluation_layers=(EvaluationLayer.DETERMINISTIC_CHECKS,),
        deterministic_checks_passed=deterministic_checks_passed,
        scores={
            "traceability_coverage": round(traceability_score, 4),
            "structure_compliance": structure_score,
            "non_empty_output": non_empty_score,
            "length_floor": length_floor_score,
            "answer_support": answer_support_score,
        },
        notes=tuple(notes),
    )


def evaluate_submissions(
    task_bundles: Sequence[TaskBundle],
    submissions: Sequence[SubmissionRecord],
) -> Tuple[EvaluationRecord, ...]:
    task_bundle_map = {bundle.task_bundle_id: bundle for bundle in task_bundles}
    evaluations: List[EvaluationRecord] = []
    for submission in submissions:
        if submission.task_bundle_id not in task_bundle_map:
            raise KeyError(f"missing task bundle for submission {submission.submission_id}")
        evaluations.append(
            evaluate_submission(task_bundle_map[submission.task_bundle_id], submission)
        )
    return tuple(evaluations)
