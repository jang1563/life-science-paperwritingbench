from __future__ import annotations

import hashlib
import json
from typing import Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple

from .models import BaselineRunSpec, EvaluationRecord, SubmissionRecord, TaskBundle
from .policy import BaselineKind, EvaluationLayer, TaskFamily
from .program import LEAN_BASELINES
from .scoring import citation_specificity


SubmissionScoringVersion = Literal["v1", "v2"]
DEFAULT_SCORING_VERSION: SubmissionScoringVersion = "v2"


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


_STRUCTURE_MARKERS: Mapping[TaskFamily, Tuple[str, ...]] = {
    TaskFamily.LITERATURE_QA: ("answer", "question"),
    TaskFamily.TRIAL_QA: ("answer", "question"),
    TaskFamily.FIGURE_QA: ("answer", "question"),
    TaskFamily.TABLE_QA: ("answer", "question"),
    TaskFamily.SOURCE_QUALITY_QA: ("assessment", "question"),
}

_HEADING_STRUCTURE_FAMILIES = {
    TaskFamily.RESULTS_TO_TEXT,
    TaskFamily.METHODS_TO_TEXT,
    TaskFamily.ABSTRACT_FROM_EVIDENCE,
    TaskFamily.REVIEW_REVISION_RESPONSE,
}


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _matches_expected_heading(line: str, expected_title: str) -> bool:
    if not line.strip():
        return False
    normalized_line = line.strip()
    while normalized_line.startswith("#"):
        normalized_line = normalized_line[1:].lstrip()
    normalized_line = normalized_line.rstrip(":").strip().casefold()
    return normalized_line == expected_title.casefold()


def _structure_compliance_score(
    task_bundle: TaskBundle,
    output_text: str,
    normalized_output: str,
) -> Tuple[float, Optional[str]]:
    section_marker = _section_title(task_bundle.task_family).lower()
    if task_bundle.task_family in _HEADING_STRUCTURE_FAMILIES:
        first_line = _first_non_empty_line(output_text)
        expected_title = _section_title(task_bundle.task_family)
        if _matches_expected_heading(first_line, expected_title):
            return 1.0, None
        return 0.0, f"missing expected section heading on first line: {section_marker}"

    structure_markers = _STRUCTURE_MARKERS[task_bundle.task_family]
    missing_markers = [marker for marker in structure_markers if marker not in normalized_output]
    if not missing_markers:
        return 1.0, None
    return 0.0, "missing expected structure markers: " + ", ".join(missing_markers)


def _answer_support_score(task_bundle: TaskBundle, normalized_output: str) -> float:
    expected_answer_texts = tuple(
        str(item) for item in task_bundle.input_artifacts.get("expected_answer_texts", ())
    )
    if not expected_answer_texts:
        return 1.0
    return 1.0 if any(
        _normalize_text(answer_text) in normalized_output
        for answer_text in expected_answer_texts
        if _normalize_text(answer_text)
    ) else 0.0


def evaluate_submission_v1(task_bundle: TaskBundle, submission: SubmissionRecord) -> EvaluationRecord:
    """Original deterministic scoring (v1).

    Traceability is computed as the fraction of the task bundle's internal
    pointer tokens (``evidence_pointers`` / ``evidence_items`` /
    ``evidence_types``) that appear in the output. This preserves
    reproducibility of pre-v2 release artifacts; it is not the recommended
    check for new evaluations. See :func:`evaluate_submission_v2` and
    ``docs/strategic_review_2026-04-13.md`` for why.
    """
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

    structure_score, structure_note = _structure_compliance_score(
        task_bundle,
        submission.output_text,
        normalized_output,
    )
    non_empty_score = 1.0 if submission.output_text.strip() else 0.0
    word_count = len(submission.output_text.split())
    length_floor_score = 1.0 if word_count >= 12 else 0.0
    answer_support_score = _answer_support_score(task_bundle, normalized_output)
    deterministic_checks_passed = (
        non_empty_score == 1.0
        and structure_score == 1.0
        and length_floor_score == 1.0
        and traceability_score >= 0.5
        and answer_support_score == 1.0
    )
    notes: List[str] = []
    if structure_note:
        notes.append(structure_note)
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
                "scoring_version": "v1",
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


def evaluate_submission_v2(task_bundle: TaskBundle, submission: SubmissionRecord) -> EvaluationRecord:
    """Citation-specificity-aware deterministic scoring (v2).

    Replaces v1's pointer-token traceability heuristic with the content-
    aware citation-specificity score from
    :mod:`life_science_paperwritingbench.scoring`. Rewards real figure /
    table / accession / p-value / repository-URL citations in the output
    and penalizes forbidden placeholder pointers (``methods_section``,
    ``abstract_section``, ...).

    Threshold semantics:
      - ``citation_specificity_score >= 0.5`` passes the traceability axis
        (equivalent to "at least 2 distinct real citation tokens").
      - Any forbidden pointer token immediately zeros the score and fails
        the axis, regardless of other content.
    """
    if submission.task_bundle_id != task_bundle.task_bundle_id:
        raise ValueError("submission and task bundle must share the same task_bundle_id")

    output_text = submission.output_text
    normalized_output = " ".join(output_text.lower().split())

    citation_report = citation_specificity(output_text)
    citation_score = float(citation_report["citation_specificity_score"])

    structure_score, structure_note = _structure_compliance_score(
        task_bundle,
        output_text,
        normalized_output,
    )
    non_empty_score = 1.0 if output_text.strip() else 0.0
    word_count = len(output_text.split())
    length_floor_score = 1.0 if word_count >= 12 else 0.0
    answer_support_score = _answer_support_score(task_bundle, normalized_output)

    deterministic_checks_passed = (
        non_empty_score == 1.0
        and structure_score == 1.0
        and length_floor_score == 1.0
        and citation_score >= 0.5
        and answer_support_score == 1.0
    )
    notes: List[str] = []
    if structure_note:
        notes.append(structure_note)
    if citation_report["forbidden_pointer_hits"]:
        notes.append(
            "forbidden pointer tokens present: "
            + ", ".join(citation_report["forbidden_pointer_hits"])
        )
    if citation_score < 0.5:
        notes.append("citation specificity below threshold")
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
                "scoring_version": "v2",
            },
        ),
        submission_id=submission.submission_id,
        task_bundle_id=task_bundle.task_bundle_id,
        evaluation_layers=(EvaluationLayer.DETERMINISTIC_CHECKS,),
        deterministic_checks_passed=deterministic_checks_passed,
        scores={
            "citation_specificity_score": round(citation_score, 4),
            "citation_count": float(citation_report["citation_count"]),
            "structure_compliance": structure_score,
            "non_empty_output": non_empty_score,
            "length_floor": length_floor_score,
            "answer_support": answer_support_score,
        },
        notes=tuple(notes),
    )


def evaluate_submission(
    task_bundle: TaskBundle,
    submission: SubmissionRecord,
    *,
    version: SubmissionScoringVersion = DEFAULT_SCORING_VERSION,
) -> EvaluationRecord:
    """Evaluate a single submission under the selected deterministic scoring version.

    Defaults to v2 (citation-specificity). Pass ``version="v1"`` to
    reproduce pre-v2 release-artifact scoring.
    """
    if version == "v1":
        return evaluate_submission_v1(task_bundle, submission)
    if version == "v2":
        return evaluate_submission_v2(task_bundle, submission)
    raise ValueError(f"unsupported scoring version: {version!r}; choose 'v1' or 'v2'")


def evaluate_submissions(
    task_bundles: Sequence[TaskBundle],
    submissions: Sequence[SubmissionRecord],
    *,
    version: SubmissionScoringVersion = DEFAULT_SCORING_VERSION,
) -> Tuple[EvaluationRecord, ...]:
    """Evaluate a batch of submissions under the selected scoring version."""
    task_bundle_map = {bundle.task_bundle_id: bundle for bundle in task_bundles}
    evaluations: List[EvaluationRecord] = []
    for submission in submissions:
        if submission.task_bundle_id not in task_bundle_map:
            raise KeyError(f"missing task bundle for submission {submission.submission_id}")
        evaluations.append(
            evaluate_submission(
                task_bundle_map[submission.task_bundle_id],
                submission,
                version=version,
            )
        )
    return tuple(evaluations)
