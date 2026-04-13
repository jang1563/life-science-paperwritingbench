from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from typing import List, Mapping, Optional, Sequence, Tuple

from .models import (
    AutoReviewRecoveryBatchEntry,
    AutoReviewRecoveryBatchReport,
    PaperPackagingReviewRecord,
    SourcePaper,
)
from .policy import (
    AutoReviewBundleCompleteness,
    AutoReviewConfidence,
    CandidateTier,
    ClaimMode,
    PaperPackagingQualification,
    PaperScientificQualification,
    PaperWritingQualification,
    StudyClass,
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def auto_review_recovery_batch_entry_from_queue_record(
    data: Mapping[str, object],
) -> AutoReviewRecoveryBatchEntry:
    return AutoReviewRecoveryBatchEntry(
        paper_id=str(data["paper_id"]),
        title=str(data.get("title", "")),
        study_class=StudyClass(str(data["study_class"])),
        claim_mode=ClaimMode(str(data["claim_mode"])),
        priority_bucket=str(data["priority_bucket"]),
        priority_rank=int(data.get("priority_rank", 999999)),
        candidate_tier=CandidateTier(str(data["candidate_tier"])),
        scientific=PaperScientificQualification(str(data["scientific"])),
        writing=PaperWritingQualification(str(data["writing"])),
        packaging=PaperPackagingQualification(str(data["packaging"])),
        bundle_completeness=AutoReviewBundleCompleteness(str(data["bundle_completeness"])),
        confidence=AutoReviewConfidence(str(data["confidence"])),
        auto_release_cap_reason=str(data["auto_release_cap_reason"])
        if data.get("auto_release_cap_reason") is not None
        else None,
        selected=bool(data.get("selected", False)),
        selection_rank=int(data["selection_rank"]) if data.get("selection_rank") is not None else None,
        selection_reason=str(data["selection_reason"]) if data.get("selection_reason") else None,
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def _bundle_rank(value: AutoReviewBundleCompleteness) -> int:
    order = {
        AutoReviewBundleCompleteness.REVIEW_READY: 0,
        AutoReviewBundleCompleteness.PARTIAL: 1,
        AutoReviewBundleCompleteness.METADATA_ONLY: 2,
    }
    return order[value]


def _confidence_rank(value: AutoReviewConfidence) -> int:
    order = {
        AutoReviewConfidence.MEDIUM: 0,
        AutoReviewConfidence.LOW: 1,
    }
    return order[value]


def _packaging_rank(value: PaperPackagingQualification) -> int:
    order = {
        PaperPackagingQualification.P1: 0,
        PaperPackagingQualification.P2: 1,
        PaperPackagingQualification.P3: 2,
    }
    return order[value]


def _selection_sort_key(
    entry: AutoReviewRecoveryBatchEntry,
    preferred_buckets: Sequence[str],
) -> Tuple[int, int, int, int, int, str]:
    bucket_rank = (
        preferred_buckets.index(entry.priority_bucket)
        if entry.priority_bucket in preferred_buckets
        else len(preferred_buckets)
    )
    return (
        bucket_rank,
        entry.priority_rank,
        _bundle_rank(entry.bundle_completeness),
        _packaging_rank(entry.packaging),
        _confidence_rank(entry.confidence),
        entry.paper_id,
    )


def build_auto_review_recovery_batch(
    entries: Sequence[AutoReviewRecoveryBatchEntry],
    *,
    target_total: int = 30,
    preferred_buckets: Sequence[str] = ("near_shadow_scientific_borderline",),
    per_class_target: Optional[int] = None,
    excluded_paper_ids: Sequence[str] = (),
    strict_preferred_buckets: bool = False,
) -> Tuple[AutoReviewRecoveryBatchEntry, ...]:
    if target_total <= 0 or not entries:
        return ()
    excluded_ids = {paper_id for paper_id in excluded_paper_ids}
    eligible_entries = tuple(entry for entry in entries if entry.paper_id not in excluded_ids)
    if strict_preferred_buckets:
        eligible_entries = tuple(
            entry for entry in eligible_entries if entry.priority_bucket in preferred_buckets
        )
    if not eligible_entries:
        return ()
    classes = tuple(
        study_class
        for study_class in StudyClass
        if any(entry.study_class == study_class for entry in eligible_entries)
    )
    quota = per_class_target
    if quota is None and classes:
        quota = max(1, target_total // len(classes))

    ordered = sorted(eligible_entries, key=lambda item: _selection_sort_key(item, preferred_buckets))
    selected_ids = set()
    selected: List[AutoReviewRecoveryBatchEntry] = []

    if quota and classes:
        for study_class in classes:
            class_entries = [entry for entry in ordered if entry.study_class == study_class]
            for entry in class_entries[:quota]:
                selected_ids.add(entry.paper_id)
                selected.append(
                    replace(
                        entry,
                        selected=True,
                        selection_rank=len(selected) + 1,
                        selection_reason=f"class_quota:{study_class.value}",
                    )
                )
                if len(selected) >= target_total:
                    return tuple(selected)

    for entry in ordered:
        if entry.paper_id in selected_ids:
            continue
        selected_ids.add(entry.paper_id)
        selected.append(
            replace(
                entry,
                selected=True,
                selection_rank=len(selected) + 1,
                selection_reason="global_fill",
            )
        )
        if len(selected) >= target_total:
            break
    return tuple(selected)


def build_auto_review_recovery_batch_report(
    entries: Sequence[AutoReviewRecoveryBatchEntry],
    selected_entries: Sequence[AutoReviewRecoveryBatchEntry],
    *,
    target_total: int,
    preferred_buckets: Sequence[str],
    per_class_target: Optional[int],
) -> AutoReviewRecoveryBatchReport:
    notes: List[str] = []
    if len(selected_entries) < target_total:
        notes.append("selected batch is smaller than target_total")
    if per_class_target is not None:
        selected_by_class = Counter(entry.study_class.value for entry in selected_entries)
        underfilled_classes = [
            study_class.value
            for study_class in StudyClass
            if any(entry.study_class == study_class for entry in entries)
            and selected_by_class.get(study_class.value, 0) < per_class_target
        ]
        if underfilled_classes:
            notes.append("underfilled_classes=" + ",".join(sorted(underfilled_classes)))
    return AutoReviewRecoveryBatchReport(
        generated_at=_utc_timestamp(),
        total_candidates=len(entries),
        target_total=target_total,
        selected_total=len(selected_entries),
        preferred_buckets=tuple(str(item) for item in preferred_buckets),
        per_class_target=per_class_target,
        bucket_counts=dict(Counter(entry.priority_bucket for entry in entries)),
        selected_bucket_counts=dict(Counter(entry.priority_bucket for entry in selected_entries)),
        selected_study_class_counts=dict(Counter(entry.study_class.value for entry in selected_entries)),
        selected_claim_mode_counts=dict(Counter(entry.claim_mode.value for entry in selected_entries)),
        selected_confidence_counts=dict(Counter(entry.confidence.value for entry in selected_entries)),
        selected_paper_ids=tuple(entry.paper_id for entry in selected_entries),
        notes=tuple(notes),
    )


def select_recovery_batch_papers(
    papers: Sequence[SourcePaper],
    selected_entries: Sequence[AutoReviewRecoveryBatchEntry],
) -> Tuple[SourcePaper, ...]:
    selected_ids = {entry.paper_id for entry in selected_entries}
    return tuple(paper for paper in papers if paper.paper_id in selected_ids)


def select_recovery_batch_packaging_reviews(
    packaging_reviews: Sequence[PaperPackagingReviewRecord],
    selected_entries: Sequence[AutoReviewRecoveryBatchEntry],
) -> Tuple[PaperPackagingReviewRecord, ...]:
    selected_ids = {entry.paper_id for entry in selected_entries}
    return tuple(record for record in packaging_reviews if record.paper_id in selected_ids)
