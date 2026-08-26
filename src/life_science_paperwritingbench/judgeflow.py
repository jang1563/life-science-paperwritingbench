from __future__ import annotations

from typing import Dict, List, Mapping, Sequence, Tuple

from .judge import DEFAULT_JUDGE_RUBRIC_AXES, _is_missing_rubric_value, _numeric_judge_rubric_score
from .models import (
    JudgeAdjudicationQueueEntry,
    JudgeAdjudicationRecord,
    JudgeReviewForm,
    JudgeValidationUnit,
)


def _rubric_template_from_unit(judge_unit: JudgeValidationUnit) -> Dict[str, object]:
    labels = dict(judge_unit.rubric_labels)
    if not labels:
        labels = {axis: None for axis in DEFAULT_JUDGE_RUBRIC_AXES}
    return labels


def _required_rubric_axes(judge_unit: JudgeValidationUnit) -> Tuple[str, ...]:
    axes = tuple(str(axis).strip() for axis in _rubric_template_from_unit(judge_unit) if str(axis).strip())
    return axes or tuple(DEFAULT_JUDGE_RUBRIC_AXES)


def _rubric_value_is_scored(value: object) -> bool:
    return _numeric_judge_rubric_score(value) is not None


def _missing_completed_form_axes(
    form: JudgeReviewForm,
    judge_unit: JudgeValidationUnit,
) -> Tuple[str, ...]:
    labels = dict(form.rubric_labels)
    return tuple(
        axis
        for axis in _required_rubric_axes(judge_unit)
        if axis not in labels or not _rubric_value_is_scored(labels[axis])
    )


def build_judge_review_forms(
    judge_units: Sequence[JudgeValidationUnit],
    reviewer_ids: Sequence[str],
) -> Tuple[JudgeReviewForm, ...]:
    forms: List[JudgeReviewForm] = []
    for judge_unit in judge_units:
        template = _rubric_template_from_unit(judge_unit)
        for reviewer_id in reviewer_ids:
            forms.append(
                JudgeReviewForm(
                    validation_unit_id=judge_unit.validation_unit_id,
                    reviewer_id=reviewer_id,
                    rubric_labels=dict(template),
                )
            )
    return tuple(forms)


def build_judge_adjudication_shells(
    judge_units: Sequence[JudgeValidationUnit],
    adjudicator_id: str,
    reviewer_ids: Sequence[str] = (),
) -> Tuple[JudgeAdjudicationRecord, ...]:
    return tuple(
        JudgeAdjudicationRecord(
            validation_unit_id=judge_unit.validation_unit_id,
            adjudicator_id=adjudicator_id,
            final_rubric_labels=_rubric_template_from_unit(judge_unit),
            source_reviewer_ids=tuple(reviewer_ids),
        )
        for judge_unit in judge_units
    )


def merge_judge_review_forms(forms: Sequence[JudgeReviewForm]) -> Tuple[JudgeReviewForm, ...]:
    merged: Dict[Tuple[str, str], JudgeReviewForm] = {}
    for form in forms:
        merged[(form.validation_unit_id, form.reviewer_id)] = form
    return tuple(
        merged[key]
        for key in sorted(merged, key=lambda item: (item[0], item[1]))
    )


def _distinct_axis_values(forms: Sequence[JudgeReviewForm], axis: str) -> Tuple[str, ...]:
    values = []
    seen = set()
    for form in forms:
        numeric_value = _numeric_judge_rubric_score(form.rubric_labels.get(axis))
        if numeric_value is None:
            continue
        normalized = repr(numeric_value)
        if normalized in seen:
            continue
        seen.add(normalized)
        values.append(normalized)
    return tuple(values)


def build_judge_adjudication_queue(
    judge_units: Sequence[JudgeValidationUnit],
    forms: Sequence[JudgeReviewForm],
    adjudications: Sequence[JudgeAdjudicationRecord],
    reviewer_ids: Sequence[str],
) -> Tuple[JudgeAdjudicationQueueEntry, ...]:
    merged_forms = merge_judge_review_forms(forms)
    forms_by_validation_unit: Dict[str, List[JudgeReviewForm]] = {}
    for form in merged_forms:
        forms_by_validation_unit.setdefault(form.validation_unit_id, []).append(form)
    adjudication_map = {record.validation_unit_id: record for record in adjudications}

    queue = []
    required_reviewer_count = len(tuple(reviewer_ids))
    for judge_unit in judge_units:
        unit_forms = forms_by_validation_unit.get(judge_unit.validation_unit_id, [])
        incomplete_completed_forms = {
            form.reviewer_id: _missing_completed_form_axes(form, judge_unit)
            for form in unit_forms
            if form.completed and _missing_completed_form_axes(form, judge_unit)
        }
        completed_forms = [
            form
            for form in unit_forms
            if form.completed and not _missing_completed_form_axes(form, judge_unit)
        ]
        completed = tuple(sorted(form.reviewer_id for form in completed_forms))
        pending = tuple(reviewer_id for reviewer_id in reviewer_ids if reviewer_id not in completed)
        finalized = bool(
            adjudication_map.get(judge_unit.validation_unit_id)
            and adjudication_map[judge_unit.validation_unit_id].finalized
        )

        disagreement_axes = []
        for axis in _rubric_template_from_unit(judge_unit):
            if len(_distinct_axis_values(completed_forms, axis)) > 1:
                disagreement_axes.append(axis)

        if finalized:
            status = "finalized"
        elif len(completed) < required_reviewer_count:
            status = "awaiting_reviews"
        else:
            status = "ready_for_adjudication"

        notes = []
        if not unit_forms:
            notes.append("no judge review forms submitted yet")
        if incomplete_completed_forms:
            details = ", ".join(
                f"{reviewer_id}={';'.join(missing_axes)}"
                for reviewer_id, missing_axes in sorted(incomplete_completed_forms.items())
            )
            notes.append("completed reviewer forms missing rubric axes: " + details)
        if disagreement_axes:
            notes.append("reviewer disagreement detected")

        queue.append(
            JudgeAdjudicationQueueEntry(
                validation_unit_id=judge_unit.validation_unit_id,
                status=status,
                required_reviewer_count=required_reviewer_count,
                completed_reviewer_ids=completed,
                pending_reviewer_ids=pending,
                disagreement_axes=tuple(disagreement_axes),
                has_final_adjudication=finalized,
                notes=tuple(notes),
            )
        )
    return tuple(queue)


def finalize_judge_validation_units(
    judge_units: Sequence[JudgeValidationUnit],
    adjudications: Sequence[JudgeAdjudicationRecord],
) -> Tuple[JudgeValidationUnit, ...]:
    adjudication_map = {
        record.validation_unit_id: record
        for record in adjudications
        if record.finalized
    }
    finalized_units = []
    for judge_unit in judge_units:
        adjudication = adjudication_map.get(judge_unit.validation_unit_id)
        if adjudication is None:
            finalized_units.append(judge_unit)
            continue
        finalized_units.append(
            JudgeValidationUnit(
                validation_unit_id=judge_unit.validation_unit_id,
                task_bundle_id=judge_unit.task_bundle_id,
                human_adjudicated=True,
                rubric_labels=dict(adjudication.final_rubric_labels),
                frozen=True,
                rubric_version=judge_unit.rubric_version,
                adjudicator_id=adjudication.adjudicator_id,
                notes=tuple(judge_unit.notes) + ("judge_adjudication_finalized",),
            )
        )
    return tuple(finalized_units)


def summarize_judge_progress(
    judge_units: Sequence[JudgeValidationUnit],
    forms: Sequence[JudgeReviewForm],
    adjudications: Sequence[JudgeAdjudicationRecord],
    reviewer_ids: Sequence[str],
) -> Dict[str, object]:
    merged_forms = merge_judge_review_forms(forms)
    queue = build_judge_adjudication_queue(
        judge_units,
        merged_forms,
        adjudications,
        reviewer_ids=reviewer_ids,
    )
    total_slots = len(judge_units) * len(tuple(reviewer_ids))
    completed_slots = sum(len(entry.completed_reviewer_ids) for entry in queue)
    summary = {
        "total_judge_units": len(judge_units),
        "required_reviewer_count": len(tuple(reviewer_ids)),
        "review_slots_total": total_slots,
        "review_slots_completed": completed_slots,
        "review_completion_rate": float(completed_slots) / float(total_slots) if total_slots else 0.0,
        "queue_status_counts": {},
        "finalized_adjudications": sum(1 for record in adjudications if record.finalized),
    }
    for entry in queue:
        summary["queue_status_counts"][entry.status] = summary["queue_status_counts"].get(entry.status, 0) + 1
    return summary
