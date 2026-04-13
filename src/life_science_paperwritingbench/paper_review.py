from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .models import (
    MetadataGovernanceHint,
    PaperPackagingReviewRecord,
    PaperReviewBatchEntry,
    PaperReviewBatchReport,
    PaperReviewPacket,
    PaperReviewPacketReport,
    PaperScientificReviewForm,
    PaperWritingReviewForm,
    SourcePaper,
)
from .policy import (
    CRITICAL_SCIENTIFIC_DOMAINS,
    CRITICAL_WRITING_DOMAINS,
    DomainOutcome,
    PackagingDomain,
    SUPPORTING_SCIENTIFIC_DOMAINS,
    SUPPORTING_WRITING_DOMAINS,
)
from .qualification import required_standards_for_paper


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _count_by(values: Sequence[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _domain_priority(outcome: Optional[DomainOutcome]) -> int:
    if outcome == DomainOutcome.PASS:
        return 0
    if outcome == DomainOutcome.BORDERLINE:
        return 1
    if outcome == DomainOutcome.FAIL:
        return 2
    return 3


def _metadata_text(paper: SourcePaper, key: str) -> str:
    value = paper.metadata.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _metadata_bool(paper: SourcePaper, key: str) -> bool:
    value = paper.metadata.get(key)
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _metadata_int(paper: SourcePaper, key: str) -> int:
    value = paper.metadata.get(key)
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def build_paper_review_batch_entries(
    papers: Sequence[SourcePaper],
    metadata_hints: Sequence[MetadataGovernanceHint] = (),
    batch_id: str = "paper_review_v1",
) -> Tuple[PaperReviewBatchEntry, ...]:
    hints_by_paper = {hint.paper_id: hint for hint in metadata_hints}
    entries: List[PaperReviewBatchEntry] = []
    for paper in sorted(
        papers,
        key=lambda item: (
            item.study_class.value,
            -(item.publication_year or 0),
            item.paper_id,
        ),
    ):
        hint = hints_by_paper.get(paper.paper_id)
        notes: List[str] = []
        if hint and hint.suggested_study_class and hint.suggested_study_class != paper.study_class:
            notes.append("metadata hint disagrees with paper study_class")
        if hint and hint.suggested_claim_mode and hint.suggested_claim_mode != paper.claim_mode:
            notes.append("metadata hint disagrees with paper claim_mode")
        entries.append(
            PaperReviewBatchEntry(
                batch_id=batch_id,
                paper_id=paper.paper_id,
                title=paper.title,
                publication_year=paper.publication_year,
                publication_status=paper.publication_status,
                peer_reviewed=paper.peer_reviewed,
                candidate_study_class=paper.study_class,
                candidate_claim_mode=paper.claim_mode,
                candidate_modality_overlays=paper.modality_overlays,
                metadata_hint_study_class=hint.suggested_study_class if hint else None,
                metadata_hint_claim_mode=hint.suggested_claim_mode if hint else None,
                metadata_hint_overlays=hint.suggested_modality_overlays if hint else (),
                metadata_hint_warnings=hint.warnings if hint else (),
                recommended_standards=required_standards_for_paper(paper),
                notes=tuple(notes),
            )
        )
    return tuple(entries)


def build_paper_review_batch_report(
    entries: Sequence[PaperReviewBatchEntry],
    generated_at: Optional[str] = None,
) -> PaperReviewBatchReport:
    study_class_counts = _count_by(
        [entry.candidate_study_class.value for entry in entries if entry.candidate_study_class]
    )
    claim_mode_counts = _count_by(
        [entry.candidate_claim_mode.value for entry in entries if entry.candidate_claim_mode]
    )
    publication_status_counts = _count_by([entry.publication_status.value for entry in entries])
    metadata_warning_count = sum(1 for entry in entries if entry.metadata_hint_warnings)
    peer_reviewed_count = sum(1 for entry in entries if entry.peer_reviewed)
    return PaperReviewBatchReport(
        generated_at=generated_at or _utc_timestamp(),
        batch_id=entries[0].batch_id if entries else "paper_review_v1",
        total_papers=len(entries),
        study_class_counts=study_class_counts,
        claim_mode_counts=claim_mode_counts,
        metadata_warning_count=metadata_warning_count,
        peer_reviewed_count=peer_reviewed_count,
        publication_status_counts=publication_status_counts,
        notes=(),
    )


def build_paper_review_packets(
    entries: Sequence[PaperReviewBatchEntry],
    papers: Sequence[SourcePaper],
    packaging_review_records: Sequence[PaperPackagingReviewRecord],
) -> Tuple[PaperReviewPacket, ...]:
    papers_by_id = {paper.paper_id: paper for paper in papers}
    packaging_by_paper = {
        record.paper_id: record.packaging_review
        for record in packaging_review_records
    }

    unsorted_packets: List[PaperReviewPacket] = []
    for entry in entries:
        paper = papers_by_id.get(entry.paper_id)
        if paper is None:
            raise ValueError(f"missing SourcePaper for review entry {entry.paper_id}")
        packaging_review = packaging_by_paper.get(entry.paper_id)
        if packaging_review is None:
            raise ValueError(f"missing PackagingReview for review entry {entry.paper_id}")

        abstract = _metadata_text(paper, "abstract")
        journal = _metadata_text(paper, "journal")
        doi = _metadata_text(paper, "doi") or None
        pmid = _metadata_text(paper, "pmid") or None
        pmcid = _metadata_text(paper, "pmcid") or None
        oa_fulltext_available = _metadata_bool(paper, "oa_fulltext_available")
        license_text = _metadata_text(paper, "license") or None
        open_review_signal = _metadata_bool(paper, "open_review_signal")
        benchmark_ready_signal_count = _metadata_int(paper, "benchmark_ready_signal_count")

        releaseability_priority = _domain_priority(
            packaging_review.domain_outcomes.get(PackagingDomain.RELEASEABILITY)
        )
        artifact_access_priority = _domain_priority(
            packaging_review.domain_outcomes.get(PackagingDomain.ARTIFACT_ACCESS)
        )
        provenance_priority = _domain_priority(
            packaging_review.domain_outcomes.get(PackagingDomain.PROVENANCE_COMPLETENESS)
        )
        review_priority = (
            releaseability_priority,
            artifact_access_priority,
            provenance_priority,
            -benchmark_ready_signal_count,
            len(entry.metadata_hint_warnings),
            -(entry.publication_year or 0),
            entry.paper_id,
        )

        notes = list(entry.notes)
        if packaging_review.notes:
            notes.extend(packaging_review.notes)

        unsorted_packets.append(
            PaperReviewPacket(
                batch_id=entry.batch_id,
                paper_id=entry.paper_id,
                title=entry.title,
                publication_year=entry.publication_year,
                publication_status=entry.publication_status,
                peer_reviewed=entry.peer_reviewed,
                candidate_study_class=entry.candidate_study_class,
                candidate_claim_mode=entry.candidate_claim_mode,
                candidate_modality_overlays=entry.candidate_modality_overlays,
                metadata_hint_study_class=entry.metadata_hint_study_class,
                metadata_hint_claim_mode=entry.metadata_hint_claim_mode,
                metadata_hint_overlays=entry.metadata_hint_overlays,
                metadata_hint_warnings=entry.metadata_hint_warnings,
                recommended_standards=entry.recommended_standards,
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
                journal=journal,
                abstract=abstract,
                oa_fulltext_available=oa_fulltext_available,
                license=license_text,
                open_review_signal=open_review_signal,
                benchmark_ready_signal_count=benchmark_ready_signal_count,
                packaging_domain_outcomes=packaging_review.domain_outcomes,
                safe_derived_artifacts=packaging_review.safe_derived_artifacts,
                artifact_inventory_id=packaging_review.artifact_inventory_id,
                restricted_artifact_types=packaging_review.restricted_artifact_types,
                review_priority=review_priority,
                notes=tuple(notes),
            )
        )

    sorted_packets = sorted(
        unsorted_packets,
        key=lambda packet: packet.review_priority,
    )
    return tuple(
        replace(
            packet,
            review_priority_rank=index + 1,
        )
        for index, packet in enumerate(sorted_packets)
    )


def build_paper_review_packet_report(
    packets: Sequence[PaperReviewPacket],
    generated_at: Optional[str] = None,
    top_priority_count: int = 20,
) -> PaperReviewPacketReport:
    packaging_domain_pass_counts: Dict[str, int] = {}
    for domain in PackagingDomain:
        packaging_domain_pass_counts[domain.value] = sum(
            1
            for packet in packets
            if packet.packaging_domain_outcomes.get(domain) == DomainOutcome.PASS
        )
    return PaperReviewPacketReport(
        generated_at=generated_at or _utc_timestamp(),
        batch_id=packets[0].batch_id if packets else "paper_review_v1",
        total_packets=len(packets),
        study_class_counts=_count_by(
            [packet.candidate_study_class.value for packet in packets if packet.candidate_study_class]
        ),
        claim_mode_counts=_count_by(
            [packet.candidate_claim_mode.value for packet in packets if packet.candidate_claim_mode]
        ),
        metadata_warning_count=sum(1 for packet in packets if packet.metadata_hint_warnings),
        oa_fulltext_available_count=sum(1 for packet in packets if packet.oa_fulltext_available),
        open_review_signal_count=sum(1 for packet in packets if packet.open_review_signal),
        packaging_domain_pass_counts=packaging_domain_pass_counts,
        top_priority_paper_ids=tuple(packet.paper_id for packet in packets[:top_priority_count]),
        notes=(),
    )


def build_paper_scientific_review_forms(
    entries: Sequence[PaperReviewBatchEntry],
    reviewer_ids: Sequence[str],
) -> Tuple[PaperScientificReviewForm, ...]:
    forms: List[PaperScientificReviewForm] = []
    for entry in entries:
        for reviewer_id in reviewer_ids:
            forms.append(
                PaperScientificReviewForm(
                    batch_id=entry.batch_id,
                    paper_id=entry.paper_id,
                    reviewer_id=reviewer_id,
                    critical_domains={domain: None for domain in CRITICAL_SCIENTIFIC_DOMAINS},
                    supporting_domains={domain: None for domain in SUPPORTING_SCIENTIFIC_DOMAINS},
                    recommended_standards=entry.recommended_standards,
                    applied_standards=(),
                    standard_outcomes={standard: None for standard in entry.recommended_standards},
                )
            )
    return tuple(forms)


def build_paper_writing_review_forms(
    entries: Sequence[PaperReviewBatchEntry],
    reviewer_ids: Sequence[str],
) -> Tuple[PaperWritingReviewForm, ...]:
    forms: List[PaperWritingReviewForm] = []
    for entry in entries:
        for reviewer_id in reviewer_ids:
            forms.append(
                PaperWritingReviewForm(
                    batch_id=entry.batch_id,
                    paper_id=entry.paper_id,
                    reviewer_id=reviewer_id,
                    critical_domains={domain: None for domain in CRITICAL_WRITING_DOMAINS},
                    supporting_domains={domain: None for domain in SUPPORTING_WRITING_DOMAINS},
                )
            )
    return tuple(forms)
