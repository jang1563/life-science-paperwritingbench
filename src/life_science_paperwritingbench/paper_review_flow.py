from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple

from .models import (
    AdjudicatedPaperReviewRecord,
    PaperReviewAdjudicationRecord,
    PaperReviewBatchEntry,
    PaperReviewerHandoffReport,
    PaperReviewPacket,
    PaperReviewProgressSummary,
    PaperReviewQueueEntry,
    PaperReviewWorkloadReport,
    PaperReviewerAssignment,
    PaperScientificReviewForm,
    PaperWritingReviewForm,
    ScientificReview,
    WritingReview,
)
from .policy import (
    CRITICAL_SCIENTIFIC_DOMAINS,
    CRITICAL_WRITING_DOMAINS,
    SUPPORTING_SCIENTIFIC_DOMAINS,
    SUPPORTING_WRITING_DOMAINS,
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _count_by(values: Sequence[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def merge_paper_scientific_review_forms(
    forms: Sequence[PaperScientificReviewForm],
) -> Tuple[PaperScientificReviewForm, ...]:
    merged: Dict[Tuple[str, str], PaperScientificReviewForm] = {}
    for form in forms:
        merged[(form.paper_id, form.reviewer_id)] = form
    return tuple(merged[key] for key in sorted(merged, key=lambda item: (item[0], item[1])))


def merge_paper_writing_review_forms(
    forms: Sequence[PaperWritingReviewForm],
) -> Tuple[PaperWritingReviewForm, ...]:
    merged: Dict[Tuple[str, str], PaperWritingReviewForm] = {}
    for form in forms:
        merged[(form.paper_id, form.reviewer_id)] = form
    return tuple(merged[key] for key in sorted(merged, key=lambda item: (item[0], item[1])))


def build_paper_review_adjudication_shells(
    entries: Sequence[PaperReviewBatchEntry],
    adjudicator_id: str,
    reviewer_ids: Sequence[str] = (),
) -> Tuple[PaperReviewAdjudicationRecord, ...]:
    return tuple(
        PaperReviewAdjudicationRecord(
            batch_id=entry.batch_id,
            paper_id=entry.paper_id,
            adjudicator_id=adjudicator_id,
            final_study_class=entry.candidate_study_class,
            final_claim_mode=entry.candidate_claim_mode,
            final_modality_overlays=entry.candidate_modality_overlays,
            scientific_critical_domains={domain: None for domain in CRITICAL_SCIENTIFIC_DOMAINS},
            scientific_supporting_domains={domain: None for domain in SUPPORTING_SCIENTIFIC_DOMAINS},
            applied_standards=entry.recommended_standards,
            standard_outcomes={standard: None for standard in entry.recommended_standards},
            writing_critical_domains={domain: None for domain in CRITICAL_WRITING_DOMAINS},
            writing_supporting_domains={domain: None for domain in SUPPORTING_WRITING_DOMAINS},
            source_reviewer_ids=tuple(reviewer_ids),
        )
        for entry in entries
    )


def _distinct_non_null_values(items: Sequence, attr_name: str) -> Tuple[str, ...]:
    values = []
    seen = set()
    for item in items:
        value = getattr(item, attr_name)
        if value is None:
            continue
        if hasattr(value, "value"):
            normalized = value.value
        else:
            normalized = str(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        values.append(normalized)
    return tuple(values)


def _domain_disagreements(forms: Sequence, mapping_attr: str) -> Tuple[str, ...]:
    disagreements: List[str] = []
    if not forms:
        return ()
    first_mapping = getattr(forms[0], mapping_attr)
    for domain in first_mapping:
        distinct = set()
        for form in forms:
            value = getattr(form, mapping_attr).get(domain)
            if value is None:
                continue
            distinct.add(value.value if hasattr(value, "value") else str(value))
        if len(distinct) > 1:
            disagreements.append(f"{mapping_attr}.{domain.value}")
    return tuple(disagreements)


def build_paper_review_queue(
    entries: Sequence[PaperReviewBatchEntry],
    scientific_forms: Sequence[PaperScientificReviewForm],
    writing_forms: Sequence[PaperWritingReviewForm],
    adjudications: Sequence[PaperReviewAdjudicationRecord],
    reviewer_ids: Sequence[str],
) -> Tuple[PaperReviewQueueEntry, ...]:
    merged_scientific = merge_paper_scientific_review_forms(scientific_forms)
    merged_writing = merge_paper_writing_review_forms(writing_forms)
    scientific_by_paper: Dict[str, List[PaperScientificReviewForm]] = {}
    writing_by_paper: Dict[str, List[PaperWritingReviewForm]] = {}
    for form in merged_scientific:
        scientific_by_paper.setdefault(form.paper_id, []).append(form)
    for form in merged_writing:
        writing_by_paper.setdefault(form.paper_id, []).append(form)
    adjudication_map = {record.paper_id: record for record in adjudications}

    queue: List[PaperReviewQueueEntry] = []
    required_reviewer_count = len(tuple(reviewer_ids))
    for entry in entries:
        paper_scientific = scientific_by_paper.get(entry.paper_id, [])
        paper_writing = writing_by_paper.get(entry.paper_id, [])
        completed_scientific = tuple(sorted(form.reviewer_id for form in paper_scientific if form.completed))
        completed_writing = tuple(sorted(form.reviewer_id for form in paper_writing if form.completed))
        pending_scientific = tuple(reviewer_id for reviewer_id in reviewer_ids if reviewer_id not in completed_scientific)
        pending_writing = tuple(reviewer_id for reviewer_id in reviewer_ids if reviewer_id not in completed_writing)
        finalized = bool(adjudication_map.get(entry.paper_id) and adjudication_map[entry.paper_id].finalized)

        disagreement_fields = list(_domain_disagreements([form for form in paper_scientific if form.completed], "critical_domains"))
        disagreement_fields.extend(_domain_disagreements([form for form in paper_scientific if form.completed], "supporting_domains"))
        disagreement_fields.extend(_domain_disagreements([form for form in paper_writing if form.completed], "critical_domains"))
        disagreement_fields.extend(_domain_disagreements([form for form in paper_writing if form.completed], "supporting_domains"))
        if len(_distinct_non_null_values([form for form in paper_scientific if form.completed], "study_class_override")) > 1:
            disagreement_fields.append("study_class_override")
        if len(_distinct_non_null_values([form for form in paper_scientific if form.completed], "claim_mode_override")) > 1:
            disagreement_fields.append("claim_mode_override")

        if finalized:
            status = "finalized"
        elif len(completed_scientific) < required_reviewer_count or len(completed_writing) < required_reviewer_count:
            status = "awaiting_reviews"
        else:
            status = "ready_for_adjudication"

        notes: List[str] = []
        if not paper_scientific:
            notes.append("no scientific review forms submitted yet")
        if not paper_writing:
            notes.append("no writing review forms submitted yet")
        if disagreement_fields:
            notes.append("reviewer disagreement detected")

        queue.append(
            PaperReviewQueueEntry(
                paper_id=entry.paper_id,
                status=status,
                required_reviewer_count=required_reviewer_count,
                completed_scientific_reviewer_ids=completed_scientific,
                completed_writing_reviewer_ids=completed_writing,
                pending_scientific_reviewer_ids=pending_scientific,
                pending_writing_reviewer_ids=pending_writing,
                disagreement_fields=tuple(disagreement_fields),
                has_final_adjudication=finalized,
                notes=tuple(notes),
            )
        )
    return tuple(queue)


def summarize_paper_review_progress(
    entries: Sequence[PaperReviewBatchEntry],
    scientific_forms: Sequence[PaperScientificReviewForm],
    writing_forms: Sequence[PaperWritingReviewForm],
    adjudications: Sequence[PaperReviewAdjudicationRecord],
    reviewer_ids: Sequence[str],
) -> PaperReviewProgressSummary:
    merged_scientific = merge_paper_scientific_review_forms(scientific_forms)
    merged_writing = merge_paper_writing_review_forms(writing_forms)
    queue = build_paper_review_queue(entries, merged_scientific, merged_writing, adjudications, reviewer_ids=reviewer_ids)
    queue_status_counts: Dict[str, int] = {}
    for entry in queue:
        queue_status_counts[entry.status] = queue_status_counts.get(entry.status, 0) + 1
    return PaperReviewProgressSummary(
        total_papers=len(entries),
        required_reviewer_count=len(tuple(reviewer_ids)),
        scientific_review_slots_total=len(entries) * len(tuple(reviewer_ids)),
        scientific_review_slots_completed=sum(1 for form in merged_scientific if form.completed),
        writing_review_slots_total=len(entries) * len(tuple(reviewer_ids)),
        writing_review_slots_completed=sum(1 for form in merged_writing if form.completed),
        queue_status_counts=queue_status_counts,
        finalized_adjudications=sum(1 for record in adjudications if record.finalized),
    )


def finalize_paper_adjudications(
    adjudications: Sequence[PaperReviewAdjudicationRecord],
) -> Tuple[AdjudicatedPaperReviewRecord, ...]:
    finalized_records: List[AdjudicatedPaperReviewRecord] = []
    for record in adjudications:
        if not record.finalized:
            continue
        scientific_review = ScientificReview(
            critical_domains={key: value for key, value in record.scientific_critical_domains.items() if value is not None},
            supporting_domains={key: value for key, value in record.scientific_supporting_domains.items() if value is not None},
            applied_standards=record.applied_standards,
            standard_outcomes={key: value for key, value in record.standard_outcomes.items() if value is not None},
            notes=record.rationale,
        )
        writing_review = WritingReview(
            critical_domains={key: value for key, value in record.writing_critical_domains.items() if value is not None},
            supporting_domains={key: value for key, value in record.writing_supporting_domains.items() if value is not None},
            notes=record.rationale,
        )
        finalized_records.append(
            AdjudicatedPaperReviewRecord(
                batch_id=record.batch_id,
                paper_id=record.paper_id,
                scientific_review=scientific_review,
                writing_review=writing_review,
                final_study_class=record.final_study_class,
                final_claim_mode=record.final_claim_mode,
                final_modality_overlays=record.final_modality_overlays,
                adjudicator_id=record.adjudicator_id,
                finalized=True,
                rationale=record.rationale,
            )
        )
    return tuple(finalized_records)


def build_paper_reviewer_assignments(
    packets: Sequence[PaperReviewPacket],
    scientific_forms: Sequence[PaperScientificReviewForm],
    writing_forms: Sequence[PaperWritingReviewForm],
    reviewer_ids: Sequence[str],
) -> Tuple[PaperReviewerAssignment, ...]:
    merged_scientific = merge_paper_scientific_review_forms(scientific_forms)
    merged_writing = merge_paper_writing_review_forms(writing_forms)
    scientific_lookup = {
        (form.paper_id, form.reviewer_id): form
        for form in merged_scientific
    }
    writing_lookup = {
        (form.paper_id, form.reviewer_id): form
        for form in merged_writing
    }

    assignments: List[PaperReviewerAssignment] = []
    for reviewer_id in reviewer_ids:
        for packet in packets:
            scientific_form = scientific_lookup.get((packet.paper_id, reviewer_id))
            writing_form = writing_lookup.get((packet.paper_id, reviewer_id))
            if scientific_form is None:
                raise ValueError(f"missing scientific review form for paper {packet.paper_id} reviewer {reviewer_id}")
            if writing_form is None:
                raise ValueError(f"missing writing review form for paper {packet.paper_id} reviewer {reviewer_id}")
            assignments.append(
                PaperReviewerAssignment(
                    batch_id=packet.batch_id,
                    reviewer_id=reviewer_id,
                    paper_id=packet.paper_id,
                    review_priority_rank=packet.review_priority_rank,
                    packet=packet,
                    scientific_review_form=scientific_form,
                    writing_review_form=writing_form,
                )
            )
    return tuple(assignments)


def build_paper_review_workload_report(
    assignments: Sequence[PaperReviewerAssignment],
    generated_at: Optional[str] = None,
    top_priority_count: int = 10,
) -> PaperReviewWorkloadReport:
    reviewer_ids = tuple(sorted({assignment.reviewer_id for assignment in assignments}))
    reviewer_assignment_counts: Dict[str, int] = {}
    top_priority_paper_ids_by_reviewer: Dict[str, Tuple[str, ...]] = {}
    for reviewer_id in reviewer_ids:
        reviewer_assignments = sorted(
            [assignment for assignment in assignments if assignment.reviewer_id == reviewer_id],
            key=lambda item: (item.review_priority_rank, item.paper_id),
        )
        reviewer_assignment_counts[reviewer_id] = len(reviewer_assignments)
        top_priority_paper_ids_by_reviewer[reviewer_id] = tuple(
            assignment.paper_id for assignment in reviewer_assignments[:top_priority_count]
        )
    batch_id = assignments[0].batch_id if assignments else "paper_review_v1"
    return PaperReviewWorkloadReport(
        generated_at=generated_at or _utc_timestamp(),
        batch_id=batch_id,
        reviewer_ids=reviewer_ids,
        reviewer_assignment_counts=reviewer_assignment_counts,
        top_priority_paper_ids_by_reviewer=top_priority_paper_ids_by_reviewer,
        total_assignments=len(assignments),
        notes=(),
    )


def build_paper_reviewer_handoff_report(
    assignments: Sequence[PaperReviewerAssignment],
    reviewer_id: str,
    generated_at: Optional[str] = None,
    top_priority_count: int = 20,
) -> PaperReviewerHandoffReport:
    reviewer_assignments = sorted(
        [assignment for assignment in assignments if assignment.reviewer_id == reviewer_id],
        key=lambda item: (item.review_priority_rank, item.paper_id),
    )
    batch_id = reviewer_assignments[0].batch_id if reviewer_assignments else "paper_review_v1"
    top_priority = reviewer_assignments[:top_priority_count]
    top_priority_warning_papers = tuple(
        assignment.paper_id
        for assignment in top_priority
        if assignment.packet.metadata_hint_warnings
    )
    return PaperReviewerHandoffReport(
        generated_at=generated_at or _utc_timestamp(),
        batch_id=batch_id,
        reviewer_id=reviewer_id,
        total_assignments=len(reviewer_assignments),
        study_class_counts=_count_by(
            [
                assignment.packet.candidate_study_class.value
                for assignment in reviewer_assignments
                if assignment.packet.candidate_study_class
            ]
        ),
        claim_mode_counts=_count_by(
            [
                assignment.packet.candidate_claim_mode.value
                for assignment in reviewer_assignments
                if assignment.packet.candidate_claim_mode
            ]
        ),
        metadata_warning_count=sum(
            1 for assignment in reviewer_assignments if assignment.packet.metadata_hint_warnings
        ),
        open_review_signal_count=sum(
            1 for assignment in reviewer_assignments if assignment.packet.open_review_signal
        ),
        restricted_artifact_assignment_count=sum(
            1 for assignment in reviewer_assignments if assignment.packet.restricted_artifact_types
        ),
        top_priority_paper_ids=tuple(assignment.paper_id for assignment in top_priority),
        top_priority_warning_paper_ids=top_priority_warning_papers,
        notes=(),
    )


def render_paper_reviewer_handoff_markdown(
    assignments: Sequence[PaperReviewerAssignment],
    reviewer_id: str,
    top_priority_count: int = 20,
) -> str:
    report = build_paper_reviewer_handoff_report(
        assignments=assignments,
        reviewer_id=reviewer_id,
        top_priority_count=top_priority_count,
    )
    reviewer_assignments = sorted(
        [assignment for assignment in assignments if assignment.reviewer_id == reviewer_id],
        key=lambda item: (item.review_priority_rank, item.paper_id),
    )
    top_priority = reviewer_assignments[:top_priority_count]
    lines: List[str] = []
    lines.append(f"# Paper Review Handoff: {reviewer_id}")
    lines.append("")
    lines.append(f"- Batch: `{report.batch_id}`")
    lines.append(f"- Total assignments: `{report.total_assignments}`")
    lines.append(f"- Metadata-warning papers: `{report.metadata_warning_count}`")
    lines.append(f"- Open-review-signal papers: `{report.open_review_signal_count}`")
    lines.append(f"- Restricted-artifact papers: `{report.restricted_artifact_assignment_count}`")
    lines.append("")
    lines.append("## Top Priority")
    lines.append("")
    for assignment in top_priority:
        packet = assignment.packet
        warning_suffix = " [warning]" if packet.metadata_hint_warnings else ""
        lines.append(
            f"- `{assignment.review_priority_rank}` {packet.paper_id}: {packet.title}{warning_suffix}"
        )
        lines.append(
            f"  - class=`{packet.candidate_study_class.value if packet.candidate_study_class else 'unknown'}` "
            f"claim_mode=`{packet.candidate_claim_mode.value if packet.candidate_claim_mode else 'unknown'}` "
            f"standards={', '.join(standard.value for standard in packet.recommended_standards) or 'none'}"
        )
    lines.append("")
    lines.append("## Workflow")
    lines.append("")
    lines.append("- Fill the embedded scientific review form for each assignment.")
    lines.append("- Fill the embedded writing review form for each assignment.")
    lines.append("- Return updated reviewer copies for merge and adjudication.")
    lines.append("")
    return "\n".join(lines)
