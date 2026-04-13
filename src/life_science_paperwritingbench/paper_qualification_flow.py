from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .models import (
    AdjudicatedPaperReviewRecord,
    PackagingReview,
    PaperPackagingReviewRecord,
    PaperQualificationBatchReport,
    PaperQualificationRecord,
    SourcePaper,
)
from .policy import (
    DomainOutcome,
    PackagingDomain,
    PackagingPolicy,
    SafeDerivedArtifact,
)
from .qualification import qualify_paper


_ACCESSION_PATTERN = re.compile(
    r"\b(?:NCT\d{8}|GSE\d+|SRP\d+|PRJNA\d+|PDB[:\s]?[A-Za-z0-9]{4}|PROSPERO|E-MTAB-\d+)\b",
    re.IGNORECASE,
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "y", "yes"}


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_text_sequence(value: object) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            text = _coerce_text(item)
            if text:
                items.append(text)
        return tuple(items)
    text = _coerce_text(value)
    return (text,) if text else ()


def _coerce_int(value: object) -> int:
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


def _packaging_inventory_id(paper: SourcePaper) -> str:
    digest = hashlib.sha256(paper.paper_id.encode("utf-8")).hexdigest().upper()[:12]
    return f"PACKINV:{digest}"


def _is_open_license(license_text: str) -> bool:
    normalized = license_text.lower()
    return (
        "creativecommons.org/licenses/" in normalized
        or "creativecommons.org/publicdomain/" in normalized
        or "cc-by" in normalized
        or "cc by" in normalized
        or "cc0" in normalized
    )


def _safe_artifacts_for_paper(paper: SourcePaper) -> Tuple[SafeDerivedArtifact, ...]:
    metadata = paper.metadata
    abstract = _coerce_text(metadata.get("abstract"))
    results_text = _coerce_text(metadata.get("results_text"))
    benchmark_ready_signal_count = _coerce_int(metadata.get("benchmark_ready_signal_count"))
    doi = _coerce_text(metadata.get("doi"))
    pmid = _coerce_text(metadata.get("pmid"))
    pmcid = _coerce_text(metadata.get("pmcid"))
    figure_captions = _coerce_text_sequence(metadata.get("figure_captions"))
    table_snippets = _coerce_text_sequence(metadata.get("table_snippets"))
    combined_text = " ".join(
        value
        for value in (
            paper.title,
            abstract,
        )
        if value
    )

    artifacts: List[SafeDerivedArtifact] = []
    if abstract:
        artifacts.append(SafeDerivedArtifact.DEIDENTIFIED_METHOD_SUMMARIES)
    if doi or pmid or pmcid:
        artifacts.append(SafeDerivedArtifact.CITATION_METADATA)
    if _ACCESSION_PATTERN.search(combined_text):
        artifacts.append(SafeDerivedArtifact.ACCESSION_METADATA)
    if benchmark_ready_signal_count >= 2 or results_text:
        artifacts.append(SafeDerivedArtifact.PUBLISHED_AGGREGATE_STATISTICS)
    if (
        benchmark_ready_signal_count >= 3
        or figure_captions
        or table_snippets
        or "figure" in combined_text.lower()
        or "table" in combined_text.lower()
    ):
        artifacts.append(SafeDerivedArtifact.PUBLISHED_FIGURE_TABLE_OBSERVATIONS)

    ordered: List[SafeDerivedArtifact] = []
    seen = set()
    for artifact in artifacts:
        if artifact in seen:
            continue
        seen.add(artifact)
        ordered.append(artifact)
    return tuple(ordered)


def build_packaging_review_prior(
    paper: SourcePaper,
    policy: Optional[PackagingPolicy] = None,
) -> PackagingReview:
    policy = policy or PackagingPolicy()
    metadata = paper.metadata
    abstract = _coerce_text(metadata.get("abstract"))
    benchmark_ready_signal_count = _coerce_int(metadata.get("benchmark_ready_signal_count"))
    doi = _coerce_text(metadata.get("doi"))
    pmid = _coerce_text(metadata.get("pmid"))
    pmcid = _coerce_text(metadata.get("pmcid"))
    oa_fulltext_available = _coerce_bool(metadata.get("oa_fulltext_available"))
    license_text = _coerce_text(metadata.get("license"))
    methods_text = _coerce_text(metadata.get("methods_text"))
    results_text = _coerce_text(metadata.get("results_text"))
    figure_captions = _coerce_text_sequence(metadata.get("figure_captions"))
    table_snippets = _coerce_text_sequence(metadata.get("table_snippets"))
    resource_identifiers = _coerce_text_sequence(metadata.get("resource_identifiers"))
    trial_registry_ids = _coerce_text_sequence(metadata.get("trial_registry_ids"))
    open_license = _is_open_license(license_text)
    safe_artifacts = _safe_artifacts_for_paper(paper)

    releaseability = DomainOutcome.PASS
    if not (paper.publication_status.value == "published" and paper.peer_reviewed):
        releaseability = DomainOutcome.FAIL
    elif not (oa_fulltext_available or open_license or pmcid or doi):
        releaseability = DomainOutcome.BORDERLINE

    evidence_pack_reconstructability = DomainOutcome.PASS
    if not abstract:
        evidence_pack_reconstructability = DomainOutcome.FAIL
    else:
        structured_support_count = sum(
            1
            for supported in (
                bool(methods_text),
                bool(results_text),
                bool(figure_captions or table_snippets),
                bool(resource_identifiers or trial_registry_ids),
            )
            if supported
        )
        if structured_support_count >= 2:
            evidence_pack_reconstructability = DomainOutcome.PASS
        elif benchmark_ready_signal_count < 2:
            evidence_pack_reconstructability = DomainOutcome.BORDERLINE

    artifact_access = DomainOutcome.PASS
    if not (oa_fulltext_available or pmcid):
        artifact_access = DomainOutcome.BORDERLINE if doi else DomainOutcome.FAIL

    provenance_completeness = DomainOutcome.PASS
    if not (doi and (pmid or pmcid)):
        provenance_completeness = DomainOutcome.BORDERLINE if (doi or pmid or pmcid) else DomainOutcome.FAIL

    restricted_artifact_types: List[str] = []
    if paper.controlled_access_human_data:
        restricted_artifact_types.append("controlled_access_human_data")

    notes: List[str] = []
    if artifact_access == DomainOutcome.BORDERLINE:
        notes.append("artifact access relies on DOI-level access rather than OA full text or PMCID")
    if evidence_pack_reconstructability == DomainOutcome.BORDERLINE:
        notes.append("evidence-pack reconstructability is only partially supported by current metadata")
    if not open_license and license_text:
        notes.append("license is present but not clearly open")

    allowed_artifacts = tuple(
        artifact for artifact in safe_artifacts if artifact in policy.allowed_safe_artifacts
    )

    return PackagingReview(
        domain_outcomes={
            PackagingDomain.RELEASEABILITY: releaseability,
            PackagingDomain.EVIDENCE_PACK_RECONSTRUCTABILITY: evidence_pack_reconstructability,
            PackagingDomain.ARTIFACT_ACCESS: artifact_access,
            PackagingDomain.PROVENANCE_COMPLETENESS: provenance_completeness,
            PackagingDomain.SPLIT_SAFETY: DomainOutcome.PASS,
        },
        safe_derived_artifacts=allowed_artifacts,
        artifact_inventory_id=_packaging_inventory_id(paper),
        restricted_artifact_types=tuple(restricted_artifact_types),
        contains_private_row_level_data=False,
        contains_recomputed_sensitive_aggregates=False,
        redistributes_restricted_supplements=False,
        controlled_access_rule_satisfied=(
            len(allowed_artifacts) >= policy.min_safe_artifacts_for_controlled_access
            if paper.controlled_access_human_data
            else True
        ),
        notes=tuple(notes),
    )


def build_packaging_review_priors(
    papers: Sequence[SourcePaper],
    policy: Optional[PackagingPolicy] = None,
) -> Tuple[PaperPackagingReviewRecord, ...]:
    return tuple(
        PaperPackagingReviewRecord(
            paper_id=paper.paper_id,
            packaging_review=build_packaging_review_prior(paper, policy=policy),
        )
        for paper in papers
    )


def build_paper_qualification_records(
    papers: Sequence[SourcePaper],
    adjudicated_reviews: Sequence[AdjudicatedPaperReviewRecord],
    packaging_reviews: Sequence[PaperPackagingReviewRecord],
    policy: Optional[PackagingPolicy] = None,
) -> Tuple[PaperQualificationRecord, ...]:
    papers_by_id = {paper.paper_id: paper for paper in papers}
    packaging_by_paper = {
        record.paper_id: record.packaging_review
        for record in packaging_reviews
    }
    records: List[PaperQualificationRecord] = []
    for adjudicated in adjudicated_reviews:
        if not adjudicated.finalized:
            continue
        paper = papers_by_id.get(adjudicated.paper_id)
        packaging_review = packaging_by_paper.get(adjudicated.paper_id)
        if paper is None or packaging_review is None:
            continue
        decision = qualify_paper(
            paper=paper,
            scientific_review=adjudicated.scientific_review,
            packaging_review=packaging_review,
            writing_review=adjudicated.writing_review,
            policy=policy,
        )
        records.append(
            PaperQualificationRecord(
                paper_id=adjudicated.paper_id,
                decision=decision,
            )
        )
    return tuple(records)


def build_paper_qualification_batch_report(
    papers: Sequence[SourcePaper],
    adjudicated_reviews: Sequence[AdjudicatedPaperReviewRecord],
    packaging_reviews: Sequence[PaperPackagingReviewRecord],
    records: Sequence[PaperQualificationRecord],
) -> PaperQualificationBatchReport:
    scientific_counts: Dict[str, int] = {}
    writing_counts: Dict[str, int] = {}
    packaging_counts: Dict[str, int] = {}
    candidate_tier_counts: Dict[str, int] = {}
    for record in records:
        scientific_counts[record.decision.scientific.value] = scientific_counts.get(record.decision.scientific.value, 0) + 1
        writing_counts[record.decision.writing.value] = writing_counts.get(record.decision.writing.value, 0) + 1
        packaging_counts[record.decision.packaging.value] = packaging_counts.get(record.decision.packaging.value, 0) + 1
        candidate_tier_counts[record.decision.candidate_tier.value] = (
            candidate_tier_counts.get(record.decision.candidate_tier.value, 0) + 1
        )

    finalized_ids = {review.paper_id for review in adjudicated_reviews if review.finalized}
    packaging_available_ids = {record.paper_id for record in packaging_reviews}
    all_paper_ids = tuple(paper.paper_id for paper in papers)
    missing_adjudicated = tuple(paper_id for paper_id in all_paper_ids if paper_id not in finalized_ids)
    missing_packaging = tuple(paper_id for paper_id in all_paper_ids if paper_id not in packaging_available_ids)

    return PaperQualificationBatchReport(
        generated_at=_utc_timestamp(),
        total_papers=len(papers),
        adjudicated_reviews_loaded=len(adjudicated_reviews),
        packaging_reviews_loaded=len(packaging_reviews),
        decisions_written=len(records),
        scientific_counts=scientific_counts,
        writing_counts=writing_counts,
        packaging_counts=packaging_counts,
        candidate_tier_counts=candidate_tier_counts,
        public_writing_eligible_count=sum(1 for record in records if record.decision.public_writing_eligible),
        missing_adjudicated_review_paper_ids=missing_adjudicated,
        missing_packaging_review_paper_ids=missing_packaging,
        notes=(),
    )
