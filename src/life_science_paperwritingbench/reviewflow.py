from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .calibration import PilotCalibrationSpec
from .policy import CandidateTier, ClaimMode, ReleaseTier, StudyClass


@dataclass(frozen=True)
class PilotReviewForm:
    calibration_id: str
    reviewer_id: str
    study_class: Optional[StudyClass] = None
    claim_mode: Optional[ClaimMode] = None
    candidate_tier: Optional[CandidateTier] = None
    unit_release_tier: Optional[ReleaseTier] = None
    completed: bool = False
    confidence: Optional[int] = None
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return {
            "calibration_id": self.calibration_id,
            "reviewer_id": self.reviewer_id,
            "study_class": self.study_class.value if self.study_class else None,
            "claim_mode": self.claim_mode.value if self.claim_mode else None,
            "candidate_tier": self.candidate_tier.value if self.candidate_tier else None,
            "unit_release_tier": self.unit_release_tier.value if self.unit_release_tier else None,
            "completed": self.completed,
            "confidence": self.confidence,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class PilotAdjudicationRecord:
    calibration_id: str
    adjudicator_id: str
    final_study_class: Optional[StudyClass] = None
    final_claim_mode: Optional[ClaimMode] = None
    final_candidate_tier: Optional[CandidateTier] = None
    final_unit_release_tier: Optional[ReleaseTier] = None
    finalized: bool = False
    rationale: Tuple[str, ...] = ()
    source_reviewer_ids: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return {
            "calibration_id": self.calibration_id,
            "adjudicator_id": self.adjudicator_id,
            "final_study_class": self.final_study_class.value if self.final_study_class else None,
            "final_claim_mode": self.final_claim_mode.value if self.final_claim_mode else None,
            "final_candidate_tier": self.final_candidate_tier.value if self.final_candidate_tier else None,
            "final_unit_release_tier": self.final_unit_release_tier.value if self.final_unit_release_tier else None,
            "finalized": self.finalized,
            "rationale": list(self.rationale),
            "source_reviewer_ids": list(self.source_reviewer_ids),
        }


@dataclass(frozen=True)
class AgreementMetric:
    label: str
    matches: int
    comparisons: int
    rate: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "label": self.label,
            "matches": self.matches,
            "comparisons": self.comparisons,
            "rate": self.rate,
        }


@dataclass(frozen=True)
class PilotAgreementSummary:
    study_class: AgreementMetric
    claim_mode: AgreementMetric
    candidate_tier: AgreementMetric
    unit_release_tier: AgreementMetric

    def to_dict(self) -> Dict[str, object]:
        return {
            "study_class": self.study_class.to_dict(),
            "claim_mode": self.claim_mode.to_dict(),
            "candidate_tier": self.candidate_tier.to_dict(),
            "unit_release_tier": self.unit_release_tier.to_dict(),
        }


@dataclass(frozen=True)
class AdjudicationQueueEntry:
    calibration_id: str
    status: str
    required_reviewer_count: int
    completed_reviewer_ids: Tuple[str, ...] = ()
    pending_reviewer_ids: Tuple[str, ...] = ()
    disagreement_fields: Tuple[str, ...] = ()
    has_final_adjudication: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return {
            "calibration_id": self.calibration_id,
            "status": self.status,
            "required_reviewer_count": self.required_reviewer_count,
            "completed_reviewer_ids": list(self.completed_reviewer_ids),
            "pending_reviewer_ids": list(self.pending_reviewer_ids),
            "disagreement_fields": list(self.disagreement_fields),
            "has_final_adjudication": self.has_final_adjudication,
            "notes": list(self.notes),
        }


def build_pilot_review_forms(
    specs: Sequence[PilotCalibrationSpec],
    reviewer_ids: Sequence[str],
) -> Tuple[PilotReviewForm, ...]:
    forms: List[PilotReviewForm] = []
    for spec in specs:
        for reviewer_id in reviewer_ids:
            forms.append(
                PilotReviewForm(
                    calibration_id=spec.calibration_id,
                    reviewer_id=reviewer_id,
                )
            )
    return tuple(forms)


def build_pilot_adjudication_shells(
    specs: Sequence[PilotCalibrationSpec],
    adjudicator_id: str,
    reviewer_ids: Sequence[str] = (),
) -> Tuple[PilotAdjudicationRecord, ...]:
    return tuple(
        PilotAdjudicationRecord(
            calibration_id=spec.calibration_id,
            adjudicator_id=adjudicator_id,
            source_reviewer_ids=tuple(reviewer_ids),
        )
        for spec in specs
    )


def _metric(label: str, matches: int, comparisons: int) -> AgreementMetric:
    rate = float(matches) / float(comparisons) if comparisons else 0.0
    return AgreementMetric(label=label, matches=matches, comparisons=comparisons, rate=rate)


def merge_review_forms(
    forms: Sequence[PilotReviewForm],
) -> Tuple[PilotReviewForm, ...]:
    merged: Dict[Tuple[str, str], PilotReviewForm] = {}
    for form in forms:
        merged[(form.calibration_id, form.reviewer_id)] = form
    return tuple(
        merged[key]
        for key in sorted(merged, key=lambda item: (item[0], item[1]))
    )


def _distinct_values(forms: Sequence[PilotReviewForm], field_name: str) -> Tuple[str, ...]:
    values = []
    seen = set()
    for form in forms:
        value = getattr(form, field_name)
        if value is None:
            continue
        normalized = value.value if hasattr(value, "value") else str(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        values.append(normalized)
    return tuple(values)


def build_adjudication_queue(
    specs: Sequence[PilotCalibrationSpec],
    forms: Sequence[PilotReviewForm],
    adjudications: Sequence[PilotAdjudicationRecord],
    reviewer_ids: Sequence[str],
) -> Tuple[AdjudicationQueueEntry, ...]:
    merged_forms = merge_review_forms(forms)
    forms_by_calibration: Dict[str, List[PilotReviewForm]] = {}
    for form in merged_forms:
        forms_by_calibration.setdefault(form.calibration_id, []).append(form)
    adjudication_map = {record.calibration_id: record for record in adjudications}

    queue = []
    required_reviewer_count = len(tuple(reviewer_ids))
    for spec in specs:
        calibration_forms = forms_by_calibration.get(spec.calibration_id, [])
        completed = tuple(sorted(form.reviewer_id for form in calibration_forms if form.completed))
        pending = tuple(reviewer_id for reviewer_id in reviewer_ids if reviewer_id not in completed)
        finalized = bool(
            adjudication_map.get(spec.calibration_id)
            and adjudication_map[spec.calibration_id].finalized
        )
        disagreement_fields = []
        for field_name in ("study_class", "claim_mode", "candidate_tier", "unit_release_tier"):
            if len(_distinct_values([form for form in calibration_forms if form.completed], field_name)) > 1:
                disagreement_fields.append(field_name)

        if finalized:
            status = "finalized"
        elif len(completed) < required_reviewer_count:
            status = "awaiting_reviews"
        else:
            status = "ready_for_adjudication"

        notes = []
        if disagreement_fields:
            notes.append("reviewer disagreement detected")
        if not calibration_forms:
            notes.append("no review forms submitted yet")

        queue.append(
            AdjudicationQueueEntry(
                calibration_id=spec.calibration_id,
                status=status,
                required_reviewer_count=required_reviewer_count,
                completed_reviewer_ids=completed,
                pending_reviewer_ids=pending,
                disagreement_fields=tuple(disagreement_fields),
                has_final_adjudication=finalized,
                notes=tuple(notes),
            )
        )
    return tuple(queue)


def summarize_calibration_progress(
    specs: Sequence[PilotCalibrationSpec],
    forms: Sequence[PilotReviewForm],
    adjudications: Sequence[PilotAdjudicationRecord],
    reviewer_ids: Sequence[str],
) -> Dict[str, object]:
    merged_forms = merge_review_forms(forms)
    queue = build_adjudication_queue(specs, merged_forms, adjudications, reviewer_ids=reviewer_ids)
    total_slots = len(specs) * len(tuple(reviewer_ids))
    completed_slots = sum(1 for form in merged_forms if form.completed)
    summary = {
        "total_specs": len(specs),
        "required_reviewer_count": len(tuple(reviewer_ids)),
        "review_slots_total": total_slots,
        "review_slots_completed": completed_slots,
        "review_completion_rate": float(completed_slots) / float(total_slots) if total_slots else 0.0,
        "queue_status_counts": {},
        "finalized_adjudications": sum(1 for entry in queue if entry.has_final_adjudication),
    }
    for entry in queue:
        summary["queue_status_counts"][entry.status] = summary["queue_status_counts"].get(entry.status, 0) + 1
    finalized_adjudications = [record for record in adjudications if record.finalized]
    if finalized_adjudications:
        agreement = compute_agreement_against_adjudication(merged_forms, finalized_adjudications)
        summary["agreement"] = agreement.to_dict()
        summary["agreement_issues"] = list(validate_pilot_agreement_thresholds(agreement))
    return summary


def compute_agreement_against_adjudication(
    forms: Sequence[PilotReviewForm],
    adjudications: Sequence[PilotAdjudicationRecord],
) -> PilotAgreementSummary:
    adjudication_map = {
        record.calibration_id: record
        for record in adjudications
        if record.finalized
    }

    counts = {
        "study_class": [0, 0],
        "claim_mode": [0, 0],
        "candidate_tier": [0, 0],
        "unit_release_tier": [0, 0],
    }

    for form in merge_review_forms(forms):
        if not form.completed:
            continue
        adjudication = adjudication_map.get(form.calibration_id)
        if adjudication is None:
            continue

        if form.study_class and adjudication.final_study_class:
            counts["study_class"][1] += 1
            if form.study_class == adjudication.final_study_class:
                counts["study_class"][0] += 1

        if form.claim_mode and adjudication.final_claim_mode:
            counts["claim_mode"][1] += 1
            if form.claim_mode == adjudication.final_claim_mode:
                counts["claim_mode"][0] += 1

        if form.candidate_tier and adjudication.final_candidate_tier:
            counts["candidate_tier"][1] += 1
            if form.candidate_tier == adjudication.final_candidate_tier:
                counts["candidate_tier"][0] += 1

        if form.unit_release_tier and adjudication.final_unit_release_tier:
            counts["unit_release_tier"][1] += 1
            if form.unit_release_tier == adjudication.final_unit_release_tier:
                counts["unit_release_tier"][0] += 1

    return PilotAgreementSummary(
        study_class=_metric("study_class", *counts["study_class"]),
        claim_mode=_metric("claim_mode", *counts["claim_mode"]),
        candidate_tier=_metric("candidate_tier", *counts["candidate_tier"]),
        unit_release_tier=_metric("unit_release_tier", *counts["unit_release_tier"]),
    )


def validate_pilot_agreement_thresholds(
    summary: PilotAgreementSummary,
    thresholds: Optional[Mapping[str, float]] = None,
) -> Tuple[str, ...]:
    thresholds = dict(thresholds or {})
    default_thresholds = {
        "study_class": 0.90,
        "claim_mode": 0.85,
        "candidate_tier": 0.80,
        "unit_release_tier": 0.85,
    }
    default_thresholds.update(thresholds)

    metrics = {
        "study_class": summary.study_class,
        "claim_mode": summary.claim_mode,
        "candidate_tier": summary.candidate_tier,
        "unit_release_tier": summary.unit_release_tier,
    }

    issues: List[str] = []
    for label, metric in metrics.items():
        threshold = default_thresholds[label]
        if metric.comparisons == 0:
            issues.append(f"{label} has no completed adjudicated comparisons")
            continue
        if metric.rate < threshold:
            issues.append(
                f"{label} agreement {metric.rate:.2%} is below threshold {threshold:.2%}"
            )
    return tuple(issues)
