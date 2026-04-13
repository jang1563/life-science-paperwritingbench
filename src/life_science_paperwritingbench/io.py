from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, TypeVar

from .calibration import (
    CalibrationDriftReport,
    PilotCalibrationSpec,
    pilot_calibration_spec_from_dict,
)
from .models import (
    AnswerRecord,
    AutoAggregatedPaperReviewRecord,
    AutoReviewEvidenceEnrichmentAuditReport,
    AutoReviewEvidenceEnrichmentRecord,
    AutoPanelVote,
    AutoQualificationRecord,
    AutoReviewBatchReport,
    AutoReviewRecoveryBatchEntry,
    AutoReviewRecoveryBatchReport,
    AutoReviewSourceBundle,
    AutoReviewSourceBundleAuditReport,
    ApiFetchRecord,
    ApiQuerySpec,
    AssertionRecord,
    BaselineRunSpec,
    BenchmarkUnitDecisionRecord,
    BenchmarkUnit,
    BundleVerificationReport,
    CollectionBatchReport,
    CollectionBatchSpec,
    CollectionCandidateRecord,
    ExecutionJobSpec,
    ExecutionProfile,
    EvaluationExtractionAuditReport,
    ExtractionAuditReport,
    EvidenceUnit,
    EvidenceExtractionRecord,
    EvidenceRecord,
    EvaluationRecord,
    IngestionAuditReport,
    IngestionRecord,
    IngestionVerificationReport,
    JudgeCandidateSelectionReport,
    JudgeAdjudicationQueueEntry,
    JudgeAdjudicationRecord,
    JudgeReviewForm,
    JudgeSliceAuditReport,
    JudgeValidationUnit,
    LineageInfo,
    MaintenanceLogEntry,
    MetadataSourceRecord,
    MetadataGovernanceHint,
    ObservationRecord,
    ShadowInspectionDeltaReport,
    ShadowInspectionBatchReport,
    ShadowInspectionEntry,
    ShadowInspectionTaxonomyCategory,
    ShadowInspectionTaxonomyReport,
    AdjudicatedPaperReviewRecord,
    PackagingReview,
    PaperPackagingReviewRecord,
    PaperReviewBatchEntry,
    PaperReviewAdjudicationRecord,
    PaperReviewBatchReport,
    PaperReviewProgressSummary,
    PaperReviewQueueEntry,
    PaperReviewerHandoffReport,
    PaperReviewerAssignment,
    PaperReviewWorkloadReport,
    PaperQualificationBatchReport,
    PaperQualificationRecord,
    PaperScientificReviewForm,
    PaperReviewPacket,
    PaperReviewPacketReport,
    PaperWritingReviewForm,
    PaperQualificationDecision,
    ParserAssistedExtractionReport,
    ProgramProgressReport,
    PmcFullTextFetchRecord,
    QuestionRecord,
    ReleaseArtifactChecksum,
    ReleaseProvenanceManifest,
    ScientificReview,
    SourcePaper,
    SourceQualityRecord,
    SplitSafetyViolation,
    SubmissionRecord,
    TaskBundle,
    TaskBundleInventoryReport,
    TruthManifest,
    TruthManifestBundle,
    TruthManifestVerificationReport,
    UnitQualificationDecision,
    WritingReview,
)
from .policy import (
    AnswerFormat,
    AutoReviewBundleCompleteness,
    AutoReviewConfidence,
    AutoReviewRole,
    AuditEvidenceDomain,
    BaselineKind,
    CandidateTier,
    ClaimMode,
    CrossmarkUpdateType,
    DomainOutcome,
    EvidenceUnitType,
    EvaluationLayer,
    IntegrityDisposition,
    IntegrityFlag,
    ModalityOverlay,
    ObservationType,
    PackagingDomain,
    PaperPackagingQualification,
    PaperScientificQualification,
    PaperWritingQualification,
    PublicationStatus,
    ReleaseTier,
    SafeDerivedArtifact,
    ScientificCriticalDomain,
    ScientificSupportingDomain,
    SplitSafetyViolationType,
    StandardId,
    SourceQualityConcernType,
    SourceQualitySeverity,
    StudyClass,
    TaskFamily,
    WritingCriticalDomain,
    WritingSupportingDomain,
)
from .reviewflow import (
    AdjudicationQueueEntry,
    AgreementMetric,
    PilotAdjudicationRecord,
    PilotAgreementSummary,
    PilotReviewForm,
)

T = TypeVar("T")


def _enum(enum_cls: Any, value: Any) -> Any:
    if isinstance(value, enum_cls):
        return value
    return enum_cls(str(value))


def _enum_tuple(enum_cls: Any, values: Sequence[Any]) -> Tuple[Any, ...]:
    return tuple(_enum(enum_cls, value) for value in values)


def _enum_mapping(enum_cls: Any, values: Mapping[str, Any]) -> Dict[Any, Any]:
    return {_enum(enum_cls, key): value for key, value in values.items()}


def _enum_to_outcome_mapping(enum_cls: Any, values: Mapping[str, Any]) -> Dict[Any, DomainOutcome]:
    return {
        _enum(enum_cls, key): _enum(DomainOutcome, value)
        for key, value in values.items()
    }


def _enum_to_optional_outcome_mapping(enum_cls: Any, values: Mapping[str, Any]) -> Dict[Any, Optional[DomainOutcome]]:
    return {
        _enum(enum_cls, key): (_enum(DomainOutcome, value) if value is not None else None)
        for key, value in values.items()
    }


def _lineage_from_dict(data: Mapping[str, Any]) -> LineageInfo:
    return LineageInfo(
        source_family=data.get("source_family"),
        consortium_lineages=tuple(str(item) for item in data.get("consortium_lineages", [])),
        dataset_lineages=tuple(str(item) for item in data.get("dataset_lineages", [])),
        lab_lineages=tuple(str(item) for item in data.get("lab_lineages", [])),
    )


def _serialize_record(record: Any) -> Dict[str, Any]:
    if hasattr(record, "to_dict"):
        return record.to_dict()
    if isinstance(record, Mapping):
        return dict(record)
    raise TypeError("record must provide to_dict() or be a mapping")


def write_jsonl(path: str, records: Iterable[Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_serialize_record(record), sort_keys=True))
            handle.write("\n")


def load_jsonl(
    path: str,
    loader: Optional[Callable[[Dict[str, Any]], T]] = None,
) -> List[T]:
    input_path = Path(path)
    loaded: List[Any] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            loaded.append(loader(payload) if loader else payload)
    return loaded


def source_paper_from_dict(data: Dict[str, Any]) -> SourcePaper:
    return SourcePaper(
        paper_id=str(data["paper_id"]),
        title=str(data["title"]),
        publication_year=int(data["publication_year"]),
        publication_status=_enum(PublicationStatus, data["publication_status"]),
        peer_reviewed=bool(data["peer_reviewed"]),
        study_class=_enum(StudyClass, data["study_class"]),
        claim_mode=_enum(ClaimMode, data["claim_mode"]),
        modality_overlays=_enum_tuple(ModalityOverlay, data.get("modality_overlays", [])),
        lineage=_lineage_from_dict(data.get("lineage", {})),
        crossmark_updates=_enum_tuple(CrossmarkUpdateType, data.get("crossmark_updates", [])),
        integrity_flags=_enum_tuple(IntegrityFlag, data.get("integrity_flags", [])),
        major_correction_affects_interpretation=bool(
            data.get("major_correction_affects_interpretation", False)
        ),
        partial_retraction_invalidates_core_claims=bool(
            data.get("partial_retraction_invalidates_core_claims", False)
        ),
        explicit_pre2018_exception=bool(data.get("explicit_pre2018_exception", False)),
        controlled_access_human_data=bool(data.get("controlled_access_human_data", False)),
        small_cell_risk=bool(data.get("small_cell_risk", False)),
        metadata={str(key): value for key, value in data.get("metadata", {}).items()},
    )


def ingestion_record_from_dict(data: Dict[str, Any]) -> IngestionRecord:
    return IngestionRecord(
        ingestion_id=str(data["ingestion_id"]),
        source_name=str(data["source_name"]),
        source_record_id=str(data["source_record_id"]),
        paper_id=str(data["paper_id"]),
        doi=data.get("doi"),
        pmid=data.get("pmid"),
        pmcid=data.get("pmcid"),
        normalized_title=str(data.get("normalized_title", "")),
        publication_year=int(data["publication_year"]) if data.get("publication_year") is not None else None,
        releaseability_precheck_passed=bool(data.get("releaseability_precheck_passed", False)),
        releaseability_flags=tuple(str(item) for item in data.get("releaseability_flags", [])),
        metadata_fingerprint_sha256=str(data.get("metadata_fingerprint_sha256", "")),
    )


def metadata_source_record_from_dict(data: Dict[str, Any]) -> MetadataSourceRecord:
    return MetadataSourceRecord(
        ingestion_id=str(data["ingestion_id"]),
        source_name=str(data["source_name"]),
        source_record_id=str(data["source_record_id"]),
        title=str(data["title"]),
        publication_year=int(data["publication_year"]) if data.get("publication_year") is not None else None,
        doi=data.get("doi"),
        pmid=data.get("pmid"),
        pmcid=data.get("pmcid"),
        publication_status=_enum(PublicationStatus, data.get("publication_status", PublicationStatus.UNKNOWN)),
        peer_reviewed=bool(data["peer_reviewed"]) if data.get("peer_reviewed") is not None else None,
        study_class=_enum(StudyClass, data["study_class"]) if data.get("study_class") else None,
        claim_mode=_enum(ClaimMode, data["claim_mode"]) if data.get("claim_mode") else None,
        modality_overlays=_enum_tuple(ModalityOverlay, data.get("modality_overlays", [])),
        lineage=_lineage_from_dict(data.get("lineage", {})),
        crossmark_updates=_enum_tuple(CrossmarkUpdateType, data.get("crossmark_updates", [])),
        integrity_flags=_enum_tuple(IntegrityFlag, data.get("integrity_flags", [])),
        explicit_pre2018_exception=bool(data.get("explicit_pre2018_exception", False)),
        controlled_access_human_data=bool(data.get("controlled_access_human_data", False)),
        small_cell_risk=bool(data.get("small_cell_risk", False)),
        metadata={str(key): value for key, value in data.get("metadata", {}).items()},
    )


def api_query_spec_from_dict(data: Dict[str, Any]) -> ApiQuerySpec:
    return ApiQuerySpec(
        batch_id=str(data["batch_id"]),
        study_class=_enum(StudyClass, data["study_class"]),
        lane=str(data["lane"]),
        source=str(data["source"]),
        query_text=str(data["query_text"]),
        retmax=int(data["retmax"]),
        year_start=int(data["year_start"]),
        year_end=int(data["year_end"]),
    )


def api_fetch_record_from_dict(data: Dict[str, Any]) -> ApiFetchRecord:
    return ApiFetchRecord(
        fetch_id=str(data["fetch_id"]),
        source=str(data["source"]),
        study_class=_enum(StudyClass, data["study_class"]),
        lane=str(data["lane"]),
        source_record_id=str(data["source_record_id"]),
        doi=data.get("doi"),
        pmid=data.get("pmid"),
        pmcid=data.get("pmcid"),
        title=str(data.get("title", "")),
        publication_year=int(data["publication_year"]) if data.get("publication_year") is not None else None,
        journal=str(data.get("journal", "")),
        abstract=str(data.get("abstract", "")),
        publication_status=_enum(PublicationStatus, data.get("publication_status", PublicationStatus.UNKNOWN)),
        peer_reviewed=bool(data["peer_reviewed"]) if data.get("peer_reviewed") is not None else None,
        raw_payload_path=str(data.get("raw_payload_path", "")),
        metadata={str(key): value for key, value in data.get("metadata", {}).items()},
    )


def collection_candidate_record_from_dict(data: Dict[str, Any]) -> CollectionCandidateRecord:
    return CollectionCandidateRecord(
        candidate_id=str(data["candidate_id"]),
        paper_key=str(data["paper_key"]),
        study_class_votes={str(key): int(value) for key, value in data.get("study_class_votes", {}).items()},
        selected_study_class=_enum(StudyClass, data["selected_study_class"])
        if data.get("selected_study_class")
        else None,
        shortlist_target_class=_enum(StudyClass, data["shortlist_target_class"])
        if data.get("shortlist_target_class")
        else None,
        doi=data.get("doi"),
        pmid=data.get("pmid"),
        pmcid=data.get("pmcid"),
        title=str(data.get("title", "")),
        publication_year=int(data["publication_year"]) if data.get("publication_year") is not None else None,
        journal=str(data.get("journal", "")),
        abstract=str(data.get("abstract", "")),
        publication_status=_enum(PublicationStatus, data.get("publication_status", PublicationStatus.UNKNOWN)),
        peer_reviewed=bool(data["peer_reviewed"]) if data.get("peer_reviewed") is not None else None,
        oa_fulltext_available=bool(data.get("oa_fulltext_available", False)),
        license=data.get("license"),
        crossmark_updates=_enum_tuple(CrossmarkUpdateType, data.get("crossmark_updates", [])),
        open_review_signal=bool(data.get("open_review_signal", False)),
        benchmark_ready_signal_count=int(data.get("benchmark_ready_signal_count", 0)),
        rank_tuple=tuple(data.get("rank_tuple", [])),
        source_names=tuple(str(item) for item in data.get("source_names", [])),
        source_record_ids=tuple(str(item) for item in data.get("source_record_ids", [])),
        metadata={str(key): value for key, value in data.get("metadata", {}).items()},
    )


def collection_batch_spec_from_dict(data: Dict[str, Any]) -> CollectionBatchSpec:
    return CollectionBatchSpec(
        batch_id=str(data["batch_id"]),
        year_start=int(data["year_start"]),
        year_end=int(data["year_end"]),
        primary_retmax=int(data["primary_retmax"]),
        reserve_retmax=int(data["reserve_retmax"]),
        target_candidates_per_class=int(data["target_candidates_per_class"]),
        seed_source=str(data["seed_source"]),
        enrichment_sources=tuple(str(item) for item in data.get("enrichment_sources", [])),
        oa_fulltext_policy=str(data.get("oa_fulltext_policy", "preferred")),
        query_specs=tuple(
            api_query_spec_from_dict(item) if not isinstance(item, ApiQuerySpec) else item
            for item in data.get("query_specs", [])
        ),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def collection_batch_report_from_dict(data: Dict[str, Any]) -> CollectionBatchReport:
    return CollectionBatchReport(
        generated_at=str(data["generated_at"]),
        batch_id=str(data["batch_id"]),
        total_queries=int(data.get("total_queries", 0)),
        total_raw_fetch_records=int(data.get("total_raw_fetch_records", 0)),
        total_candidates=int(data.get("total_candidates", 0)),
        source_counts={str(key): int(value) for key, value in data.get("source_counts", {}).items()},
        class_candidate_counts={
            str(key): int(value) for key, value in data.get("class_candidate_counts", {}).items()
        },
        class_shortlist_counts={
            str(key): int(value) for key, value in data.get("class_shortlist_counts", {}).items()
        },
        class_deficits={str(key): int(value) for key, value in data.get("class_deficits", {}).items()},
        identifier_coverage={
            str(key): int(value) for key, value in data.get("identifier_coverage", {}).items()
        },
        oa_fulltext_available_count=int(data.get("oa_fulltext_available_count", 0)),
        open_review_signal_count=int(data.get("open_review_signal_count", 0)),
        releaseability_precheck_passed=int(data.get("releaseability_precheck_passed", 0)),
        releaseability_precheck_failed=int(data.get("releaseability_precheck_failed", 0)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def ingestion_audit_report_from_dict(data: Dict[str, Any]) -> IngestionAuditReport:
    return IngestionAuditReport(
        generated_at=str(data["generated_at"]),
        raw_records=int(data["raw_records"]),
        normalized_papers=int(data["normalized_papers"]),
        merged_duplicates=int(data["merged_duplicates"]),
        releaseability_precheck_passed=int(data.get("releaseability_precheck_passed", 0)),
        releaseability_precheck_failed=int(data.get("releaseability_precheck_failed", 0)),
        source_counts={str(key): int(value) for key, value in data.get("source_counts", {}).items()},
        publication_status_counts={
            str(key): int(value) for key, value in data.get("publication_status_counts", {}).items()
        },
        identifier_coverage={str(key): int(value) for key, value in data.get("identifier_coverage", {}).items()},
        releaseability_flag_counts={
            str(key): int(value) for key, value in data.get("releaseability_flag_counts", {}).items()
        },
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def ingestion_verification_report_from_dict(data: Dict[str, Any]) -> IngestionVerificationReport:
    return IngestionVerificationReport(
        ok=bool(data.get("ok", False)),
        normalized_papers=int(data.get("normalized_papers", 0)),
        ingestion_records=int(data.get("ingestion_records", 0)),
        duplicate_paper_ids=tuple(str(item) for item in data.get("duplicate_paper_ids", [])),
        duplicate_ingestion_ids=tuple(str(item) for item in data.get("duplicate_ingestion_ids", [])),
        missing_normalized_titles=tuple(str(item) for item in data.get("missing_normalized_titles", [])),
        missing_metadata_fingerprints=tuple(str(item) for item in data.get("missing_metadata_fingerprints", [])),
        precedence_violations=tuple(str(item) for item in data.get("precedence_violations", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def auto_review_source_bundle_from_dict(data: Dict[str, Any]) -> AutoReviewSourceBundle:
    return AutoReviewSourceBundle(
        paper_id=str(data["paper_id"]),
        bundle_completeness=_enum(AutoReviewBundleCompleteness, data["bundle_completeness"]),
        abstract_text=str(data.get("abstract_text", "")),
        methods_text=str(data.get("methods_text", "")),
        results_text=str(data.get("results_text", "")),
        figure_captions=tuple(str(item) for item in data.get("figure_captions", [])),
        table_snippets=tuple(str(item) for item in data.get("table_snippets", [])),
        figure_reference_snippets=tuple(str(item) for item in data.get("figure_reference_snippets", [])),
        table_reference_snippets=tuple(str(item) for item in data.get("table_reference_snippets", [])),
        resource_identifiers=tuple(str(item) for item in data.get("resource_identifiers", [])),
        trial_registry_ids=tuple(str(item) for item in data.get("trial_registry_ids", [])),
        open_review_snippets=tuple(str(item) for item in data.get("open_review_snippets", [])),
        provenance_fields={str(key): str(value) for key, value in data.get("provenance_fields", {}).items()},
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def auto_review_source_bundle_audit_report_from_dict(data: Dict[str, Any]) -> AutoReviewSourceBundleAuditReport:
    return AutoReviewSourceBundleAuditReport(
        generated_at=str(data["generated_at"]),
        total_bundles=int(data.get("total_bundles", 0)),
        completeness_counts={str(key): int(value) for key, value in data.get("completeness_counts", {}).items()},
        methods_text_count=int(data.get("methods_text_count", 0)),
        results_text_count=int(data.get("results_text_count", 0)),
        figure_caption_count=int(data.get("figure_caption_count", 0)),
        table_snippet_count=int(data.get("table_snippet_count", 0)),
        figure_reference_snippet_count=int(data.get("figure_reference_snippet_count", 0)),
        table_reference_snippet_count=int(data.get("table_reference_snippet_count", 0)),
        resource_identifier_count=int(data.get("resource_identifier_count", 0)),
        trial_registry_count=int(data.get("trial_registry_count", 0)),
        open_review_snippet_count=int(data.get("open_review_snippet_count", 0)),
        provenance_warning_paper_ids=tuple(str(item) for item in data.get("provenance_warning_paper_ids", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def pmc_full_text_fetch_record_from_dict(data: Dict[str, Any]) -> PmcFullTextFetchRecord:
    return PmcFullTextFetchRecord(
        paper_id=str(data["paper_id"]),
        pmcid=data.get("pmcid"),
        fetch_url=str(data.get("fetch_url", "")),
        raw_payload_path=str(data.get("raw_payload_path", "")),
        fetch_ok=bool(data.get("fetch_ok", False)),
        used_cache=bool(data.get("used_cache", False)),
        content_sha256=str(data.get("content_sha256", "")),
        error=data.get("error"),
    )


def auto_review_evidence_enrichment_record_from_dict(
    data: Dict[str, Any]
) -> AutoReviewEvidenceEnrichmentRecord:
    return AutoReviewEvidenceEnrichmentRecord(
        paper_id=str(data["paper_id"]),
        pmcid=data.get("pmcid"),
        raw_payload_path=str(data.get("raw_payload_path", "")),
        methods_text=str(data.get("methods_text", "")),
        results_text=str(data.get("results_text", "")),
        figure_captions=tuple(str(item) for item in data.get("figure_captions", [])),
        table_snippets=tuple(str(item) for item in data.get("table_snippets", [])),
        figure_reference_snippets=tuple(str(item) for item in data.get("figure_reference_snippets", [])),
        table_reference_snippets=tuple(str(item) for item in data.get("table_reference_snippets", [])),
        resource_identifiers=tuple(str(item) for item in data.get("resource_identifiers", [])),
        trial_registry_ids=tuple(str(item) for item in data.get("trial_registry_ids", [])),
        provenance_fields={str(key): str(value) for key, value in data.get("provenance_fields", {}).items()},
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def auto_review_evidence_enrichment_audit_report_from_dict(
    data: Dict[str, Any]
) -> AutoReviewEvidenceEnrichmentAuditReport:
    return AutoReviewEvidenceEnrichmentAuditReport(
        generated_at=str(data["generated_at"]),
        total_records=int(data.get("total_records", 0)),
        methods_text_count=int(data.get("methods_text_count", 0)),
        results_text_count=int(data.get("results_text_count", 0)),
        figure_caption_count=int(data.get("figure_caption_count", 0)),
        table_snippet_count=int(data.get("table_snippet_count", 0)),
        figure_reference_snippet_count=int(data.get("figure_reference_snippet_count", 0)),
        table_reference_snippet_count=int(data.get("table_reference_snippet_count", 0)),
        resource_identifier_count=int(data.get("resource_identifier_count", 0)),
        trial_registry_count=int(data.get("trial_registry_count", 0)),
        fetch_ok_count=int(data.get("fetch_ok_count", 0)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def auto_panel_vote_from_dict(data: Dict[str, Any]) -> AutoPanelVote:
    return AutoPanelVote(
        paper_id=str(data["paper_id"]),
        role=_enum(AutoReviewRole, data["role"]),
        critical_domain_votes=_enum_to_outcome_mapping(
            ScientificCriticalDomain,
            data.get("critical_domain_votes", {}),
        ),
        supporting_domain_votes=_enum_to_outcome_mapping(
            ScientificSupportingDomain,
            data.get("supporting_domain_votes", {}),
        ),
        writing_domain_votes=_enum_to_outcome_mapping(
            WritingCriticalDomain,
            data.get("writing_domain_votes", {}),
        ),
        insufficient_evidence_flags=tuple(str(item) for item in data.get("insufficient_evidence_flags", [])),
        rationale=str(data.get("rationale", "")),
        prompt_fingerprint=str(data.get("prompt_fingerprint", "")),
        model_fingerprint=str(data.get("model_fingerprint", "")),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def scientific_review_from_dict(data: Dict[str, Any]) -> ScientificReview:
    return ScientificReview(
        critical_domains=_enum_to_outcome_mapping(
            ScientificCriticalDomain,
            data.get("critical_domains", {}),
        ),
        supporting_domains=_enum_to_outcome_mapping(
            ScientificSupportingDomain,
            data.get("supporting_domains", {}),
        ),
        applied_standards=_enum_tuple(StandardId, data.get("applied_standards", [])),
        standard_outcomes=_enum_to_outcome_mapping(
            StandardId,
            data.get("standard_outcomes", {}),
        ),
        standard_notes={
            _enum(StandardId, key): str(value)
            for key, value in data.get("standard_notes", {}).items()
        },
        audit_evidence={
            _enum(AuditEvidenceDomain, key): str(value)
            for key, value in data.get("audit_evidence", {}).items()
        },
        contemporary_bonus=tuple(str(item) for item in data.get("contemporary_bonus", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def writing_review_from_dict(data: Dict[str, Any]) -> WritingReview:
    return WritingReview(
        critical_domains=_enum_to_outcome_mapping(
            WritingCriticalDomain,
            data.get("critical_domains", {}),
        ),
        supporting_domains=_enum_to_outcome_mapping(
            WritingSupportingDomain,
            data.get("supporting_domains", {}),
        ),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def auto_aggregated_paper_review_record_from_dict(data: Dict[str, Any]) -> AutoAggregatedPaperReviewRecord:
    return AutoAggregatedPaperReviewRecord(
        paper_id=str(data["paper_id"]),
        scientific_review=scientific_review_from_dict(dict(data.get("scientific_review", {}))),
        writing_review=writing_review_from_dict(dict(data.get("writing_review", {}))),
        review_origin=str(data.get("review_origin", "auto_panel")),
        confidence=_enum(AutoReviewConfidence, data.get("confidence", AutoReviewConfidence.LOW)),
        skipped_writing_review=bool(data.get("skipped_writing_review", False)),
        auto_release_cap_reason=data.get("auto_release_cap_reason"),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def packaging_review_from_dict(data: Dict[str, Any]) -> PackagingReview:
    return PackagingReview(
        domain_outcomes=_enum_to_outcome_mapping(
            PackagingDomain,
            data.get("domain_outcomes", {}),
        ),
        safe_derived_artifacts=_enum_tuple(
            SafeDerivedArtifact,
            data.get("safe_derived_artifacts", []),
        ),
        artifact_inventory_id=data.get("artifact_inventory_id"),
        restricted_artifact_types=tuple(str(item) for item in data.get("restricted_artifact_types", [])),
        contains_private_row_level_data=bool(data.get("contains_private_row_level_data", False)),
        contains_recomputed_sensitive_aggregates=bool(
            data.get("contains_recomputed_sensitive_aggregates", False)
        ),
        redistributes_restricted_supplements=bool(
            data.get("redistributes_restricted_supplements", False)
        ),
        controlled_access_rule_satisfied=bool(data.get("controlled_access_rule_satisfied", True)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_packaging_review_record_from_dict(data: Dict[str, Any]) -> PaperPackagingReviewRecord:
    return PaperPackagingReviewRecord(
        paper_id=str(data["paper_id"]),
        packaging_review=packaging_review_from_dict(dict(data.get("packaging_review", {}))),
    )


def evidence_unit_from_dict(data: Dict[str, Any]) -> EvidenceUnit:
    return EvidenceUnit(
        unit_id=str(data["unit_id"]),
        paper_id=str(data["paper_id"]),
        unit_type=_enum(EvidenceUnitType, data["unit_type"]),
        evidence_pointers=tuple(str(item) for item in data.get("evidence_pointers", [])),
        locally_supported=bool(data["locally_supported"]),
        internally_coherent=bool(data["internally_coherent"]),
        depends_on_excluded_narrative=bool(data["depends_on_excluded_narrative"]),
        releasable=bool(data["releasable"]),
        description=str(data.get("description", "")),
        modality_overlays=_enum_tuple(ModalityOverlay, data.get("modality_overlays", [])),
    )


def assertion_record_from_dict(data: Dict[str, Any]) -> AssertionRecord:
    return AssertionRecord(
        assertion_id=str(data["assertion_id"]),
        paper_id=str(data["paper_id"]),
        text=str(data["text"]),
        claim_mode=_enum(ClaimMode, data["claim_mode"]) if data.get("claim_mode") else None,
        supported=bool(data.get("supported", True)),
        excluded=bool(data.get("excluded", False)),
        evidence_record_ids=tuple(str(item) for item in data.get("evidence_record_ids", [])),
    )


def evidence_record_from_dict(data: Dict[str, Any]) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(data["evidence_id"]),
        paper_id=str(data["paper_id"]),
        evidence_type=str(data["evidence_type"]),
        pointer=str(data["pointer"]),
        description=str(data.get("description", "")),
    )


def evidence_extraction_record_from_dict(data: Dict[str, Any]) -> EvidenceExtractionRecord:
    return EvidenceExtractionRecord(
        extraction_id=str(data["extraction_id"]),
        paper_id=str(data["paper_id"]),
        evidence_unit_id=str(data["evidence_unit_id"]),
        assertion_ids=tuple(str(item) for item in data.get("assertion_ids", [])),
        evidence_ids=tuple(str(item) for item in data.get("evidence_ids", [])),
        excluded_assertion_ids=tuple(str(item) for item in data.get("excluded_assertion_ids", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def observation_record_from_dict(data: Dict[str, Any]) -> ObservationRecord:
    return ObservationRecord(
        observation_id=str(data["observation_id"]),
        paper_id=str(data["paper_id"]),
        task_family=_enum(TaskFamily, data["task_family"]),
        observation_type=_enum(ObservationType, data["observation_type"]),
        text=str(data["text"]),
        evidence_unit_id=data.get("evidence_unit_id"),
        pointer=data.get("pointer"),
        evidence_record_ids=tuple(str(item) for item in data.get("evidence_record_ids", [])),
        provenance_note=str(data.get("provenance_note", "")),
    )


def question_record_from_dict(data: Dict[str, Any]) -> QuestionRecord:
    return QuestionRecord(
        question_id=str(data["question_id"]),
        paper_id=str(data["paper_id"]),
        task_family=_enum(TaskFamily, data["task_family"]),
        prompt=str(data["prompt"]),
        answer_format=_enum(AnswerFormat, data.get("answer_format", AnswerFormat.FREE_TEXT)),
        evidence_unit_id=data.get("evidence_unit_id"),
        supporting_observation_ids=tuple(str(item) for item in data.get("supporting_observation_ids", [])),
        supporting_evidence_pointers=tuple(str(item) for item in data.get("supporting_evidence_pointers", [])),
        expected_answer_ids=tuple(str(item) for item in data.get("expected_answer_ids", [])),
    )


def answer_record_from_dict(data: Dict[str, Any]) -> AnswerRecord:
    return AnswerRecord(
        answer_id=str(data["answer_id"]),
        paper_id=str(data["paper_id"]),
        question_id=str(data["question_id"]),
        answer_text=str(data["answer_text"]),
        rationale=str(data.get("rationale", "")),
        supporting_observation_ids=tuple(str(item) for item in data.get("supporting_observation_ids", [])),
        supporting_evidence_pointers=tuple(str(item) for item in data.get("supporting_evidence_pointers", [])),
    )


def source_quality_record_from_dict(data: Dict[str, Any]) -> SourceQualityRecord:
    return SourceQualityRecord(
        quality_record_id=str(data["quality_record_id"]),
        paper_id=str(data["paper_id"]),
        concern_type=_enum(SourceQualityConcernType, data["concern_type"]),
        severity=_enum(SourceQualitySeverity, data["severity"]),
        text=str(data["text"]),
        pointer=data.get("pointer"),
        evidence_unit_id=data.get("evidence_unit_id"),
        supporting_observation_ids=tuple(str(item) for item in data.get("supporting_observation_ids", [])),
        resolved=bool(data.get("resolved", False)),
    )


def extraction_audit_report_from_dict(data: Dict[str, Any]) -> ExtractionAuditReport:
    return ExtractionAuditReport(
        generated_at=str(data["generated_at"]),
        paper_count=int(data["paper_count"]),
        evidence_unit_count=int(data["evidence_unit_count"]),
        extraction_count=int(data["extraction_count"]),
        assertion_count=int(data["assertion_count"]),
        excluded_assertion_count=int(data.get("excluded_assertion_count", 0)),
        evidence_record_count=int(data.get("evidence_record_count", 0)),
        unit_type_counts={str(key): int(value) for key, value in data.get("unit_type_counts", {}).items()},
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def parser_assisted_extraction_report_from_dict(
    data: Dict[str, Any]
) -> ParserAssistedExtractionReport:
    return ParserAssistedExtractionReport(
        generated_at=str(data["generated_at"]),
        paper_count=int(data["paper_count"]),
        papers_with_suggestions=int(data["papers_with_suggestions"]),
        evidence_unit_count=int(data["evidence_unit_count"]),
        extraction_spec_count=int(data["extraction_spec_count"]),
        unit_type_counts={
            str(key): int(value) for key, value in data.get("unit_type_counts", {}).items()
        },
        skipped_paper_ids=tuple(str(item) for item in data.get("skipped_paper_ids", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def evaluation_extraction_audit_report_from_dict(
    data: Dict[str, Any]
) -> EvaluationExtractionAuditReport:
    return EvaluationExtractionAuditReport(
        generated_at=str(data["generated_at"]),
        paper_count=int(data["paper_count"]),
        observation_count=int(data["observation_count"]),
        question_count=int(data["question_count"]),
        answer_count=int(data["answer_count"]),
        source_quality_count=int(data["source_quality_count"]),
        task_family_counts={str(key): int(value) for key, value in data.get("task_family_counts", {}).items()},
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def benchmark_unit_from_dict(data: Dict[str, Any]) -> BenchmarkUnit:
    return BenchmarkUnit(
        benchmark_unit_id=str(data["benchmark_unit_id"]),
        paper_id=str(data["paper_id"]),
        evidence_unit_ids=tuple(str(item) for item in data.get("evidence_unit_ids", [])),
        split=data.get("split"),
        lineage=_lineage_from_dict(data.get("lineage", {})),
    )


def truth_manifest_from_dict(data: Dict[str, Any]) -> TruthManifest:
    return TruthManifest(
        manifest_id=str(data["manifest_id"]),
        paper_id=str(data["paper_id"]),
        assertion_ids=tuple(str(item) for item in data.get("assertion_ids", [])),
        assertion_texts=tuple(str(item) for item in data.get("assertion_texts", [])),
        evidence_items=tuple(str(item) for item in data.get("evidence_items", [])),
        evidence_types=tuple(str(item) for item in data.get("evidence_types", [])),
        excluded_assertions=tuple(str(item) for item in data.get("excluded_assertions", [])),
        caveats=tuple(str(item) for item in data.get("caveats", [])),
        provenance_entities=tuple(str(item) for item in data.get("provenance_entities", [])),
        provenance_activities=tuple(str(item) for item in data.get("provenance_activities", [])),
        provenance_agents=tuple(str(item) for item in data.get("provenance_agents", [])),
        applied_standards=_enum_tuple(StandardId, data.get("applied_standards", [])),
        study_class=_enum(StudyClass, data["study_class"]) if data.get("study_class") else None,
        modality_overlays=_enum_tuple(ModalityOverlay, data.get("modality_overlays", [])),
        frozen=bool(data.get("frozen", False)),
        frozen_at=data.get("frozen_at"),
        version=str(data.get("version", "v5")),
    )


def truth_manifest_bundle_from_dict(data: Dict[str, Any]) -> TruthManifestBundle:
    return TruthManifestBundle(
        bundle_id=str(data["bundle_id"]),
        paper_id=str(data["paper_id"]),
        manifest_id=str(data["manifest_id"]),
        evidence_unit_ids=tuple(str(item) for item in data.get("evidence_unit_ids", [])),
        assertion_ids=tuple(str(item) for item in data.get("assertion_ids", [])),
        evidence_ids=tuple(str(item) for item in data.get("evidence_ids", [])),
        provenance_manifest_id=data.get("provenance_manifest_id"),
        release_ready=bool(data.get("release_ready", False)),
        frozen_at=data.get("frozen_at"),
    )


def truth_manifest_verification_report_from_dict(data: Dict[str, Any]) -> TruthManifestVerificationReport:
    return TruthManifestVerificationReport(
        manifest_id=str(data["manifest_id"]),
        paper_id=str(data["paper_id"]),
        ok=bool(data.get("ok", False)),
        frozen=bool(data.get("frozen", False)),
        missing_assertion_ids=tuple(str(item) for item in data.get("missing_assertion_ids", [])),
        missing_evidence_ids=tuple(str(item) for item in data.get("missing_evidence_ids", [])),
        missing_extraction_ids=tuple(str(item) for item in data.get("missing_extraction_ids", [])),
        inconsistent_paper_ids=tuple(str(item) for item in data.get("inconsistent_paper_ids", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_qualification_decision_from_dict(data: Dict[str, Any]) -> PaperQualificationDecision:
    return PaperQualificationDecision(
        scientific=_enum(PaperScientificQualification, data["scientific"]),
        packaging=_enum(PaperPackagingQualification, data["packaging"]),
        candidate_tier=_enum(CandidateTier, data["candidate_tier"]),
        eligible_for_unit_extraction=bool(data["eligible_for_unit_extraction"]),
        required_standards=_enum_tuple(StandardId, data.get("required_standards", [])),
        writing=_enum(PaperWritingQualification, data.get("writing", PaperWritingQualification.W2)),
        public_writing_eligible=bool(data.get("public_writing_eligible", False)),
        missing_standards=_enum_tuple(StandardId, data.get("missing_standards", [])),
        integrity_disposition=_enum(IntegrityDisposition, data.get("integrity_disposition", IntegrityDisposition.CLEAR)),
        reasons=tuple(str(item) for item in data.get("reasons", [])),
    )


def paper_qualification_record_from_dict(data: Dict[str, Any]) -> PaperQualificationRecord:
    return PaperQualificationRecord(
        paper_id=str(data["paper_id"]),
        decision=paper_qualification_decision_from_dict(dict(data.get("decision", {}))),
    )


def auto_qualification_record_from_dict(data: Dict[str, Any]) -> AutoQualificationRecord:
    return AutoQualificationRecord(
        paper_id=str(data["paper_id"]),
        decision=paper_qualification_decision_from_dict(dict(data.get("decision", {}))),
        review_origin=str(data.get("review_origin", "auto_panel")),
        confidence=_enum(AutoReviewConfidence, data.get("confidence", AutoReviewConfidence.LOW)),
        auto_release_cap_reason=data.get("auto_release_cap_reason"),
        judge_validation_ready=bool(data.get("judge_validation_ready", False)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_qualification_batch_report_from_dict(data: Dict[str, Any]) -> PaperQualificationBatchReport:
    return PaperQualificationBatchReport(
        generated_at=str(data["generated_at"]),
        total_papers=int(data.get("total_papers", 0)),
        adjudicated_reviews_loaded=int(data.get("adjudicated_reviews_loaded", 0)),
        packaging_reviews_loaded=int(data.get("packaging_reviews_loaded", 0)),
        decisions_written=int(data.get("decisions_written", 0)),
        scientific_counts={str(key): int(value) for key, value in data.get("scientific_counts", {}).items()},
        writing_counts={str(key): int(value) for key, value in data.get("writing_counts", {}).items()},
        packaging_counts={str(key): int(value) for key, value in data.get("packaging_counts", {}).items()},
        candidate_tier_counts={str(key): int(value) for key, value in data.get("candidate_tier_counts", {}).items()},
        public_writing_eligible_count=int(data.get("public_writing_eligible_count", 0)),
        missing_adjudicated_review_paper_ids=tuple(
            str(item) for item in data.get("missing_adjudicated_review_paper_ids", [])
        ),
        missing_packaging_review_paper_ids=tuple(
            str(item) for item in data.get("missing_packaging_review_paper_ids", [])
        ),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def auto_review_batch_report_from_dict(data: Dict[str, Any]) -> AutoReviewBatchReport:
    return AutoReviewBatchReport(
        generated_at=str(data["generated_at"]),
        total_papers=int(data.get("total_papers", 0)),
        source_bundle_count=int(data.get("source_bundle_count", 0)),
        panel_vote_count=int(data.get("panel_vote_count", 0)),
        aggregated_review_count=int(data.get("aggregated_review_count", 0)),
        qualification_count=int(data.get("qualification_count", 0)),
        completeness_counts={str(key): int(value) for key, value in data.get("completeness_counts", {}).items()},
        scientific_counts={str(key): int(value) for key, value in data.get("scientific_counts", {}).items()},
        writing_counts={str(key): int(value) for key, value in data.get("writing_counts", {}).items()},
        packaging_counts={str(key): int(value) for key, value in data.get("packaging_counts", {}).items()},
        candidate_tier_counts={str(key): int(value) for key, value in data.get("candidate_tier_counts", {}).items()},
        confidence_counts={str(key): int(value) for key, value in data.get("confidence_counts", {}).items()},
        eligible_for_unit_extraction_count=int(data.get("eligible_for_unit_extraction_count", 0)),
        skipped_writing_review_count=int(data.get("skipped_writing_review_count", 0)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def auto_review_recovery_batch_entry_from_dict(data: Dict[str, Any]) -> AutoReviewRecoveryBatchEntry:
    return AutoReviewRecoveryBatchEntry(
        paper_id=str(data["paper_id"]),
        title=str(data.get("title", "")),
        study_class=_enum(StudyClass, data["study_class"]),
        claim_mode=_enum(ClaimMode, data["claim_mode"]),
        priority_bucket=str(data["priority_bucket"]),
        priority_rank=int(data.get("priority_rank", 0)),
        candidate_tier=_enum(CandidateTier, data["candidate_tier"]),
        scientific=_enum(PaperScientificQualification, data["scientific"]),
        writing=_enum(PaperWritingQualification, data["writing"]),
        packaging=_enum(PaperPackagingQualification, data["packaging"]),
        bundle_completeness=_enum(AutoReviewBundleCompleteness, data["bundle_completeness"]),
        confidence=_enum(AutoReviewConfidence, data["confidence"]),
        auto_release_cap_reason=data.get("auto_release_cap_reason"),
        selected=bool(data.get("selected", False)),
        selection_rank=int(data["selection_rank"]) if data.get("selection_rank") is not None else None,
        selection_reason=str(data["selection_reason"]) if data.get("selection_reason") else None,
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def auto_review_recovery_batch_report_from_dict(data: Dict[str, Any]) -> AutoReviewRecoveryBatchReport:
    return AutoReviewRecoveryBatchReport(
        generated_at=str(data["generated_at"]),
        total_candidates=int(data.get("total_candidates", 0)),
        target_total=int(data.get("target_total", 0)),
        selected_total=int(data.get("selected_total", 0)),
        preferred_buckets=tuple(str(item) for item in data.get("preferred_buckets", [])),
        per_class_target=int(data["per_class_target"]) if data.get("per_class_target") is not None else None,
        bucket_counts={str(key): int(value) for key, value in data.get("bucket_counts", {}).items()},
        selected_bucket_counts={
            str(key): int(value) for key, value in data.get("selected_bucket_counts", {}).items()
        },
        selected_study_class_counts={
            str(key): int(value) for key, value in data.get("selected_study_class_counts", {}).items()
        },
        selected_claim_mode_counts={
            str(key): int(value) for key, value in data.get("selected_claim_mode_counts", {}).items()
        },
        selected_confidence_counts={
            str(key): int(value) for key, value in data.get("selected_confidence_counts", {}).items()
        },
        selected_paper_ids=tuple(str(item) for item in data.get("selected_paper_ids", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def metadata_governance_hint_from_dict(data: Dict[str, Any]) -> MetadataGovernanceHint:
    return MetadataGovernanceHint(
        paper_id=str(data["paper_id"]),
        suggested_study_class=_enum(StudyClass, data["suggested_study_class"])
        if data.get("suggested_study_class")
        else None,
        suggested_claim_mode=_enum(ClaimMode, data["suggested_claim_mode"])
        if data.get("suggested_claim_mode")
        else None,
        suggested_modality_overlays=_enum_tuple(
            ModalityOverlay,
            data.get("suggested_modality_overlays", []),
        ),
        suggested_required_standards=_enum_tuple(
            StandardId,
            data.get("suggested_required_standards", []),
        ),
        matched_terms={
            str(key): tuple(str(item) for item in value)
            for key, value in data.get("matched_terms", {}).items()
        },
        warnings=tuple(str(item) for item in data.get("warnings", [])),
    )


def paper_review_batch_entry_from_dict(data: Dict[str, Any]) -> PaperReviewBatchEntry:
    return PaperReviewBatchEntry(
        batch_id=str(data["batch_id"]),
        paper_id=str(data["paper_id"]),
        title=str(data["title"]),
        publication_year=int(data["publication_year"]) if data.get("publication_year") is not None else None,
        publication_status=_enum(PublicationStatus, data["publication_status"]),
        peer_reviewed=bool(data["peer_reviewed"]) if data.get("peer_reviewed") is not None else None,
        candidate_study_class=_enum(StudyClass, data["candidate_study_class"])
        if data.get("candidate_study_class")
        else None,
        candidate_claim_mode=_enum(ClaimMode, data["candidate_claim_mode"])
        if data.get("candidate_claim_mode")
        else None,
        candidate_modality_overlays=_enum_tuple(
            ModalityOverlay,
            data.get("candidate_modality_overlays", []),
        ),
        metadata_hint_study_class=_enum(StudyClass, data["metadata_hint_study_class"])
        if data.get("metadata_hint_study_class")
        else None,
        metadata_hint_claim_mode=_enum(ClaimMode, data["metadata_hint_claim_mode"])
        if data.get("metadata_hint_claim_mode")
        else None,
        metadata_hint_overlays=_enum_tuple(ModalityOverlay, data.get("metadata_hint_overlays", [])),
        metadata_hint_warnings=tuple(str(item) for item in data.get("metadata_hint_warnings", [])),
        recommended_standards=_enum_tuple(StandardId, data.get("recommended_standards", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_review_packet_from_dict(data: Dict[str, Any]) -> PaperReviewPacket:
    return PaperReviewPacket(
        batch_id=str(data["batch_id"]),
        paper_id=str(data["paper_id"]),
        title=str(data["title"]),
        publication_year=int(data["publication_year"]) if data.get("publication_year") is not None else None,
        publication_status=_enum(PublicationStatus, data["publication_status"]),
        peer_reviewed=bool(data["peer_reviewed"]) if data.get("peer_reviewed") is not None else None,
        candidate_study_class=_enum(StudyClass, data["candidate_study_class"])
        if data.get("candidate_study_class")
        else None,
        candidate_claim_mode=_enum(ClaimMode, data["candidate_claim_mode"])
        if data.get("candidate_claim_mode")
        else None,
        candidate_modality_overlays=_enum_tuple(ModalityOverlay, data.get("candidate_modality_overlays", [])),
        metadata_hint_study_class=_enum(StudyClass, data["metadata_hint_study_class"])
        if data.get("metadata_hint_study_class")
        else None,
        metadata_hint_claim_mode=_enum(ClaimMode, data["metadata_hint_claim_mode"])
        if data.get("metadata_hint_claim_mode")
        else None,
        metadata_hint_overlays=_enum_tuple(ModalityOverlay, data.get("metadata_hint_overlays", [])),
        metadata_hint_warnings=tuple(str(item) for item in data.get("metadata_hint_warnings", [])),
        recommended_standards=_enum_tuple(StandardId, data.get("recommended_standards", [])),
        doi=data.get("doi"),
        pmid=data.get("pmid"),
        pmcid=data.get("pmcid"),
        journal=str(data.get("journal", "")),
        abstract=str(data.get("abstract", "")),
        oa_fulltext_available=bool(data.get("oa_fulltext_available", False)),
        license=data.get("license"),
        open_review_signal=bool(data.get("open_review_signal", False)),
        benchmark_ready_signal_count=int(data.get("benchmark_ready_signal_count", 0)),
        packaging_domain_outcomes=_enum_to_outcome_mapping(
            PackagingDomain,
            data.get("packaging_domain_outcomes", {}),
        ),
        safe_derived_artifacts=_enum_tuple(SafeDerivedArtifact, data.get("safe_derived_artifacts", [])),
        artifact_inventory_id=data.get("artifact_inventory_id"),
        restricted_artifact_types=tuple(str(item) for item in data.get("restricted_artifact_types", [])),
        review_priority=tuple(data.get("review_priority", [])),
        review_priority_rank=int(data.get("review_priority_rank", 0)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_review_packet_report_from_dict(data: Dict[str, Any]) -> PaperReviewPacketReport:
    return PaperReviewPacketReport(
        generated_at=str(data["generated_at"]),
        batch_id=str(data["batch_id"]),
        total_packets=int(data.get("total_packets", 0)),
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        claim_mode_counts={str(key): int(value) for key, value in data.get("claim_mode_counts", {}).items()},
        metadata_warning_count=int(data.get("metadata_warning_count", 0)),
        oa_fulltext_available_count=int(data.get("oa_fulltext_available_count", 0)),
        open_review_signal_count=int(data.get("open_review_signal_count", 0)),
        packaging_domain_pass_counts={
            str(key): int(value) for key, value in data.get("packaging_domain_pass_counts", {}).items()
        },
        top_priority_paper_ids=tuple(str(item) for item in data.get("top_priority_paper_ids", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_reviewer_assignment_from_dict(data: Dict[str, Any]) -> PaperReviewerAssignment:
    return PaperReviewerAssignment(
        batch_id=str(data["batch_id"]),
        reviewer_id=str(data["reviewer_id"]),
        paper_id=str(data["paper_id"]),
        review_priority_rank=int(data.get("review_priority_rank", 0)),
        packet=paper_review_packet_from_dict(dict(data.get("packet", {}))),
        scientific_review_form=paper_scientific_review_form_from_dict(dict(data.get("scientific_review_form", {}))),
        writing_review_form=paper_writing_review_form_from_dict(dict(data.get("writing_review_form", {}))),
    )


def paper_review_workload_report_from_dict(data: Dict[str, Any]) -> PaperReviewWorkloadReport:
    return PaperReviewWorkloadReport(
        generated_at=str(data["generated_at"]),
        batch_id=str(data["batch_id"]),
        reviewer_ids=tuple(str(item) for item in data.get("reviewer_ids", [])),
        reviewer_assignment_counts={
            str(key): int(value) for key, value in data.get("reviewer_assignment_counts", {}).items()
        },
        top_priority_paper_ids_by_reviewer={
            str(key): tuple(str(item) for item in value)
            for key, value in data.get("top_priority_paper_ids_by_reviewer", {}).items()
        },
        total_assignments=int(data.get("total_assignments", 0)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_reviewer_handoff_report_from_dict(data: Dict[str, Any]) -> PaperReviewerHandoffReport:
    return PaperReviewerHandoffReport(
        generated_at=str(data["generated_at"]),
        batch_id=str(data["batch_id"]),
        reviewer_id=str(data["reviewer_id"]),
        total_assignments=int(data.get("total_assignments", 0)),
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        claim_mode_counts={str(key): int(value) for key, value in data.get("claim_mode_counts", {}).items()},
        metadata_warning_count=int(data.get("metadata_warning_count", 0)),
        open_review_signal_count=int(data.get("open_review_signal_count", 0)),
        restricted_artifact_assignment_count=int(data.get("restricted_artifact_assignment_count", 0)),
        top_priority_paper_ids=tuple(str(item) for item in data.get("top_priority_paper_ids", [])),
        top_priority_warning_paper_ids=tuple(
            str(item) for item in data.get("top_priority_warning_paper_ids", [])
        ),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_scientific_review_form_from_dict(data: Dict[str, Any]) -> PaperScientificReviewForm:
    return PaperScientificReviewForm(
        batch_id=str(data["batch_id"]),
        paper_id=str(data["paper_id"]),
        reviewer_id=str(data["reviewer_id"]),
        study_class_override=_enum(StudyClass, data["study_class_override"])
        if data.get("study_class_override")
        else None,
        claim_mode_override=_enum(ClaimMode, data["claim_mode_override"])
        if data.get("claim_mode_override")
        else None,
        modality_overlay_overrides=_enum_tuple(ModalityOverlay, data.get("modality_overlay_overrides", [])),
        critical_domains=_enum_to_optional_outcome_mapping(
            ScientificCriticalDomain,
            data.get("critical_domains", {}),
        ),
        supporting_domains=_enum_to_optional_outcome_mapping(
            ScientificSupportingDomain,
            data.get("supporting_domains", {}),
        ),
        recommended_standards=_enum_tuple(StandardId, data.get("recommended_standards", [])),
        applied_standards=_enum_tuple(StandardId, data.get("applied_standards", [])),
        standard_outcomes=_enum_to_optional_outcome_mapping(
            StandardId,
            data.get("standard_outcomes", {}),
        ),
        completed=bool(data.get("completed", False)),
        confidence=int(data["confidence"]) if data.get("confidence") is not None else None,
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_writing_review_form_from_dict(data: Dict[str, Any]) -> PaperWritingReviewForm:
    return PaperWritingReviewForm(
        batch_id=str(data["batch_id"]),
        paper_id=str(data["paper_id"]),
        reviewer_id=str(data["reviewer_id"]),
        critical_domains=_enum_to_optional_outcome_mapping(
            WritingCriticalDomain,
            data.get("critical_domains", {}),
        ),
        supporting_domains=_enum_to_optional_outcome_mapping(
            WritingSupportingDomain,
            data.get("supporting_domains", {}),
        ),
        completed=bool(data.get("completed", False)),
        confidence=int(data["confidence"]) if data.get("confidence") is not None else None,
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_review_batch_report_from_dict(data: Dict[str, Any]) -> PaperReviewBatchReport:
    return PaperReviewBatchReport(
        generated_at=str(data["generated_at"]),
        batch_id=str(data["batch_id"]),
        total_papers=int(data.get("total_papers", 0)),
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        claim_mode_counts={str(key): int(value) for key, value in data.get("claim_mode_counts", {}).items()},
        metadata_warning_count=int(data.get("metadata_warning_count", 0)),
        peer_reviewed_count=int(data.get("peer_reviewed_count", 0)),
        publication_status_counts={
            str(key): int(value) for key, value in data.get("publication_status_counts", {}).items()
        },
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_review_adjudication_record_from_dict(data: Dict[str, Any]) -> PaperReviewAdjudicationRecord:
    return PaperReviewAdjudicationRecord(
        batch_id=str(data["batch_id"]),
        paper_id=str(data["paper_id"]),
        adjudicator_id=str(data["adjudicator_id"]),
        final_study_class=_enum(StudyClass, data["final_study_class"]) if data.get("final_study_class") else None,
        final_claim_mode=_enum(ClaimMode, data["final_claim_mode"]) if data.get("final_claim_mode") else None,
        final_modality_overlays=_enum_tuple(ModalityOverlay, data.get("final_modality_overlays", [])),
        scientific_critical_domains=_enum_to_optional_outcome_mapping(
            ScientificCriticalDomain,
            data.get("scientific_critical_domains", {}),
        ),
        scientific_supporting_domains=_enum_to_optional_outcome_mapping(
            ScientificSupportingDomain,
            data.get("scientific_supporting_domains", {}),
        ),
        applied_standards=_enum_tuple(StandardId, data.get("applied_standards", [])),
        standard_outcomes=_enum_to_optional_outcome_mapping(
            StandardId,
            data.get("standard_outcomes", {}),
        ),
        writing_critical_domains=_enum_to_optional_outcome_mapping(
            WritingCriticalDomain,
            data.get("writing_critical_domains", {}),
        ),
        writing_supporting_domains=_enum_to_optional_outcome_mapping(
            WritingSupportingDomain,
            data.get("writing_supporting_domains", {}),
        ),
        finalized=bool(data.get("finalized", False)),
        rationale=tuple(str(item) for item in data.get("rationale", [])),
        source_reviewer_ids=tuple(str(item) for item in data.get("source_reviewer_ids", [])),
    )


def paper_review_queue_entry_from_dict(data: Dict[str, Any]) -> PaperReviewQueueEntry:
    return PaperReviewQueueEntry(
        paper_id=str(data["paper_id"]),
        status=str(data["status"]),
        required_reviewer_count=int(data.get("required_reviewer_count", 0)),
        completed_scientific_reviewer_ids=tuple(str(item) for item in data.get("completed_scientific_reviewer_ids", [])),
        completed_writing_reviewer_ids=tuple(str(item) for item in data.get("completed_writing_reviewer_ids", [])),
        pending_scientific_reviewer_ids=tuple(str(item) for item in data.get("pending_scientific_reviewer_ids", [])),
        pending_writing_reviewer_ids=tuple(str(item) for item in data.get("pending_writing_reviewer_ids", [])),
        disagreement_fields=tuple(str(item) for item in data.get("disagreement_fields", [])),
        has_final_adjudication=bool(data.get("has_final_adjudication", False)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def paper_review_progress_summary_from_dict(data: Dict[str, Any]) -> PaperReviewProgressSummary:
    return PaperReviewProgressSummary(
        total_papers=int(data.get("total_papers", 0)),
        required_reviewer_count=int(data.get("required_reviewer_count", 0)),
        scientific_review_slots_total=int(data.get("scientific_review_slots_total", 0)),
        scientific_review_slots_completed=int(data.get("scientific_review_slots_completed", 0)),
        writing_review_slots_total=int(data.get("writing_review_slots_total", 0)),
        writing_review_slots_completed=int(data.get("writing_review_slots_completed", 0)),
        queue_status_counts={str(key): int(value) for key, value in data.get("queue_status_counts", {}).items()},
        finalized_adjudications=int(data.get("finalized_adjudications", 0)),
    )


def adjudicated_paper_review_record_from_dict(data: Dict[str, Any]) -> AdjudicatedPaperReviewRecord:
    return AdjudicatedPaperReviewRecord(
        batch_id=str(data["batch_id"]),
        paper_id=str(data["paper_id"]),
        scientific_review=scientific_review_from_dict(dict(data.get("scientific_review", {}))),
        writing_review=writing_review_from_dict(dict(data.get("writing_review", {}))),
        final_study_class=_enum(StudyClass, data["final_study_class"])
        if data.get("final_study_class")
        else None,
        final_claim_mode=_enum(ClaimMode, data["final_claim_mode"])
        if data.get("final_claim_mode")
        else None,
        final_modality_overlays=_enum_tuple(ModalityOverlay, data.get("final_modality_overlays", [])),
        adjudicator_id=str(data["adjudicator_id"]) if data.get("adjudicator_id") else None,
        finalized=bool(data.get("finalized", False)),
        rationale=tuple(str(item) for item in data.get("rationale", [])),
    )


def benchmark_unit_decision_record_from_dict(data: Dict[str, Any]) -> BenchmarkUnitDecisionRecord:
    return BenchmarkUnitDecisionRecord(
        benchmark_unit_id=str(data["benchmark_unit_id"]),
        release_tier=_enum(ReleaseTier, data["release_tier"]),
        gold_eligible=bool(data["gold_eligible"]),
        reasons=tuple(str(item) for item in data.get("reasons", [])),
    )


def task_bundle_from_dict(data: Dict[str, Any]) -> TaskBundle:
    return TaskBundle(
        task_bundle_id=str(data["task_bundle_id"]),
        benchmark_unit_id=str(data["benchmark_unit_id"]),
        task_family=_enum(TaskFamily, data["task_family"]),
        release_tier=_enum(ReleaseTier, data["release_tier"]),
        study_class=_enum(StudyClass, data["study_class"]),
        claim_mode=_enum(ClaimMode, data["claim_mode"]),
        input_artifacts=dict(data.get("input_artifacts", {})),
        authoring_constraints=dict(data.get("authoring_constraints", {})),
        truth_manifest_id=str(data.get("truth_manifest_id", "")),
        provenance_manifest_id=data.get("provenance_manifest_id"),
        scoring_profile=dict(data.get("scoring_profile", {})),
        paper_id=data.get("paper_id"),
        evidence_unit_ids=tuple(str(item) for item in data.get("evidence_unit_ids", [])),
        holdout_bucket=data.get("holdout_bucket"),
    )


def unit_qualification_decision_from_dict(data: Dict[str, Any]) -> UnitQualificationDecision:
    return UnitQualificationDecision(
        release_tier=_enum(ReleaseTier, data["release_tier"]),
        gold_eligible=bool(data["gold_eligible"]),
        reasons=tuple(str(item) for item in data.get("reasons", [])),
    )


def split_safety_violation_from_dict(data: Dict[str, Any]) -> SplitSafetyViolation:
    return SplitSafetyViolation(
        violation_type=_enum(SplitSafetyViolationType, data["violation_type"]),
        lineage_type=str(data["lineage_type"]),
        lineage_value=str(data["lineage_value"]),
        benchmark_unit_ids=tuple(str(item) for item in data.get("benchmark_unit_ids", [])),
        conflicting_splits=tuple(str(item) for item in data.get("conflicting_splits", [])),
        observed_count=int(data.get("observed_count", 0)),
        max_allowed=int(data["max_allowed"]) if data.get("max_allowed") is not None else None,
    )


def release_artifact_checksum_from_dict(data: Dict[str, Any]) -> ReleaseArtifactChecksum:
    return ReleaseArtifactChecksum(
        artifact_name=str(data["artifact_name"]),
        sha256=str(data["sha256"]),
        size_bytes=int(data["size_bytes"]),
        line_count=int(data["line_count"]) if data.get("line_count") is not None else None,
    )


def release_provenance_manifest_from_dict(data: Dict[str, Any]) -> ReleaseProvenanceManifest:
    return ReleaseProvenanceManifest(
        release_bundle_id=str(data["release_bundle_id"]),
        generated_at=str(data["generated_at"]),
        bundle_version=str(data.get("bundle_version", "release-bundle-v1")),
        units_fingerprint_sha256=str(data.get("units_fingerprint_sha256", "")),
        decisions_fingerprint_sha256=str(data.get("decisions_fingerprint_sha256", "")),
        input_record_counts={
            str(key): int(value)
            for key, value in data.get("input_record_counts", {}).items()
        },
        included_benchmark_unit_ids=tuple(
            str(item) for item in data.get("included_benchmark_unit_ids", [])
        ),
        excluded_benchmark_unit_ids=tuple(
            str(item) for item in data.get("excluded_benchmark_unit_ids", [])
        ),
        holdout_policy=dict(data.get("holdout_policy", {})),
        canary_policy=dict(data.get("canary_policy", {})),
        split_safety_policy=dict(data.get("split_safety_policy", {})),
        holdout_counts={
            str(key): int(value)
            for key, value in data.get("holdout_counts", {}).items()
        },
        tier_counts={
            str(key): int(value)
            for key, value in data.get("tier_counts", {}).items()
        },
        benchmark_split_counts={
            str(key): int(value)
            for key, value in data.get("benchmark_split_counts", {}).items()
        },
        split_safety_violation_count=int(data.get("split_safety_violation_count", 0)),
    )


def bundle_verification_report_from_dict(data: Dict[str, Any]) -> BundleVerificationReport:
    return BundleVerificationReport(
        bundle_dir=str(data["bundle_dir"]),
        release_bundle_id=data.get("release_bundle_id"),
        ok=bool(data.get("ok", False)),
        verified_artifacts=tuple(str(item) for item in data.get("verified_artifacts", [])),
        missing_artifacts=tuple(str(item) for item in data.get("missing_artifacts", [])),
        checksum_mismatches=tuple(str(item) for item in data.get("checksum_mismatches", [])),
        summary_consistent=bool(data.get("summary_consistent", False)),
        provenance_consistent=bool(data.get("provenance_consistent", False)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def baseline_run_spec_from_dict(data: Dict[str, Any]) -> BaselineRunSpec:
    return BaselineRunSpec(
        baseline_id=str(data["baseline_id"]),
        baseline_kind=_enum(BaselineKind, data["baseline_kind"]),
        task_bundle_ids=tuple(str(item) for item in data.get("task_bundle_ids", [])),
        config_fingerprint_sha256=str(data.get("config_fingerprint_sha256", "")),
        replay_verified=bool(data.get("replay_verified", False)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def submission_record_from_dict(data: Dict[str, Any]) -> SubmissionRecord:
    return SubmissionRecord(
        submission_id=str(data["submission_id"]),
        task_bundle_id=str(data["task_bundle_id"]),
        source=str(data["source"]),
        producer_id=str(data["producer_id"]),
        output_text=str(data["output_text"]),
        config_fingerprint_sha256=str(data.get("config_fingerprint_sha256", "")),
    )


def evaluation_record_from_dict(data: Dict[str, Any]) -> EvaluationRecord:
    return EvaluationRecord(
        evaluation_id=str(data["evaluation_id"]),
        submission_id=str(data["submission_id"]),
        task_bundle_id=str(data["task_bundle_id"]),
        evaluation_layers=_enum_tuple(EvaluationLayer, data.get("evaluation_layers", [])),
        deterministic_checks_passed=bool(data.get("deterministic_checks_passed", False)),
        scores={str(key): float(value) for key, value in data.get("scores", {}).items()},
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def judge_validation_unit_from_dict(data: Dict[str, Any]) -> JudgeValidationUnit:
    return JudgeValidationUnit(
        validation_unit_id=str(data["validation_unit_id"]),
        task_bundle_id=str(data["task_bundle_id"]),
        human_adjudicated=bool(data["human_adjudicated"]),
        rubric_labels=dict(data.get("rubric_labels", {})),
        frozen=bool(data.get("frozen", False)),
        rubric_version=str(data.get("rubric_version", "judge-rubric-v1")),
        adjudicator_id=data.get("adjudicator_id"),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def task_bundle_inventory_report_from_dict(data: Dict[str, Any]) -> TaskBundleInventoryReport:
    return TaskBundleInventoryReport(
        generated_at=str(data["generated_at"]),
        total_bundles=int(data["total_bundles"]),
        task_family_counts={str(key): int(value) for key, value in data.get("task_family_counts", {}).items()},
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        claim_mode_counts={str(key): int(value) for key, value in data.get("claim_mode_counts", {}).items()},
        release_tier_counts={str(key): int(value) for key, value in data.get("release_tier_counts", {}).items()},
        holdout_bucket_counts={str(key): int(value) for key, value in data.get("holdout_bucket_counts", {}).items()},
    )


def judge_candidate_selection_report_from_dict(data: Dict[str, Any]) -> JudgeCandidateSelectionReport:
    return JudgeCandidateSelectionReport(
        generated_at=str(data["generated_at"]),
        target_total=int(data["target_total"]),
        selected_total=int(data["selected_total"]),
        task_family_counts={str(key): int(value) for key, value in data.get("task_family_counts", {}).items()},
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        claim_mode_counts={str(key): int(value) for key, value in data.get("claim_mode_counts", {}).items()},
        release_tier_counts={str(key): int(value) for key, value in data.get("release_tier_counts", {}).items()},
        holdout_bucket_counts={str(key): int(value) for key, value in data.get("holdout_bucket_counts", {}).items()},
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def shadow_inspection_entry_from_dict(data: Dict[str, Any]) -> ShadowInspectionEntry:
    return ShadowInspectionEntry(
        inspection_id=str(data["inspection_id"]),
        task_bundle_id=str(data["task_bundle_id"]),
        benchmark_unit_id=str(data["benchmark_unit_id"]),
        paper_id=str(data["paper_id"]),
        title=str(data["title"]),
        publication_year=int(data["publication_year"]) if data.get("publication_year") is not None else None,
        task_family=_enum(TaskFamily, data["task_family"]),
        study_class=_enum(StudyClass, data["study_class"]),
        claim_mode=_enum(ClaimMode, data["claim_mode"]),
        release_tier=_enum(ReleaseTier, data["release_tier"]),
        holdout_bucket=str(data["holdout_bucket"]),
        writing=_enum(PaperWritingQualification, data["writing"]),
        confidence=_enum(AutoReviewConfidence, data["confidence"]),
        bundle_completeness=_enum(AutoReviewBundleCompleteness, data["bundle_completeness"]),
        modality_overlays=_enum_tuple(ModalityOverlay, data.get("modality_overlays", [])),
        focus_tags=tuple(str(item) for item in data.get("focus_tags", [])),
        evidence_snapshot={str(key): int(value) for key, value in data.get("evidence_snapshot", {}).items()},
        qualification_reasons=tuple(str(item) for item in data.get("qualification_reasons", [])),
        source_bundle_notes=tuple(str(item) for item in data.get("source_bundle_notes", [])),
    )


def shadow_inspection_batch_report_from_dict(data: Dict[str, Any]) -> ShadowInspectionBatchReport:
    return ShadowInspectionBatchReport(
        generated_at=str(data["generated_at"]),
        target_total=int(data["target_total"]),
        selected_total=int(data["selected_total"]),
        task_family_counts={str(key): int(value) for key, value in data.get("task_family_counts", {}).items()},
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        claim_mode_counts={str(key): int(value) for key, value in data.get("claim_mode_counts", {}).items()},
        writing_counts={str(key): int(value) for key, value in data.get("writing_counts", {}).items()},
        confidence_counts={str(key): int(value) for key, value in data.get("confidence_counts", {}).items()},
        completeness_counts={str(key): int(value) for key, value in data.get("completeness_counts", {}).items()},
        holdout_bucket_counts={str(key): int(value) for key, value in data.get("holdout_bucket_counts", {}).items()},
        focus_tag_counts={str(key): int(value) for key, value in data.get("focus_tag_counts", {}).items()},
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def shadow_inspection_taxonomy_category_from_dict(data: Dict[str, Any]) -> ShadowInspectionTaxonomyCategory:
    return ShadowInspectionTaxonomyCategory(
        category_id=str(data["category_id"]),
        label=str(data["label"]),
        priority=str(data["priority"]),
        entry_count=int(data["entry_count"]),
        task_family_counts={str(key): int(value) for key, value in data.get("task_family_counts", {}).items()},
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        claim_mode_counts={str(key): int(value) for key, value in data.get("claim_mode_counts", {}).items()},
        writing_counts={str(key): int(value) for key, value in data.get("writing_counts", {}).items()},
        confidence_counts={str(key): int(value) for key, value in data.get("confidence_counts", {}).items()},
        focus_tag_counts={str(key): int(value) for key, value in data.get("focus_tag_counts", {}).items()},
        representative_inspection_ids=tuple(str(item) for item in data.get("representative_inspection_ids", [])),
        representative_task_bundle_ids=tuple(str(item) for item in data.get("representative_task_bundle_ids", [])),
        recommended_actions=tuple(str(item) for item in data.get("recommended_actions", [])),
    )


def shadow_inspection_taxonomy_report_from_dict(data: Dict[str, Any]) -> ShadowInspectionTaxonomyReport:
    return ShadowInspectionTaxonomyReport(
        generated_at=str(data["generated_at"]),
        total_entries=int(data["total_entries"]),
        category_count=int(data["category_count"]),
        priority_counts={str(key): int(value) for key, value in data.get("priority_counts", {}).items()},
        categories=tuple(
            shadow_inspection_taxonomy_category_from_dict(item)
            for item in data.get("categories", [])
        ),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def shadow_inspection_delta_report_from_dict(data: Dict[str, Any]) -> ShadowInspectionDeltaReport:
    return ShadowInspectionDeltaReport(
        generated_at=str(data["generated_at"]),
        previous_label=str(data["previous_label"]),
        current_label=str(data["current_label"]),
        previous_selected_total=int(data["previous_selected_total"]),
        current_selected_total=int(data["current_selected_total"]),
        confidence_count_delta={str(key): int(value) for key, value in data.get("confidence_count_delta", {}).items()},
        writing_count_delta={str(key): int(value) for key, value in data.get("writing_count_delta", {}).items()},
        focus_tag_delta={str(key): int(value) for key, value in data.get("focus_tag_delta", {}).items()},
        taxonomy_category_entry_delta={
            str(key): int(value) for key, value in data.get("taxonomy_category_entry_delta", {}).items()
        },
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def judge_slice_audit_report_from_dict(data: Dict[str, Any]) -> JudgeSliceAuditReport:
    return JudgeSliceAuditReport(
        generated_at=str(data["generated_at"]),
        total_units=int(data["total_units"]),
        human_adjudicated_units=int(data["human_adjudicated_units"]),
        frozen_units=int(data["frozen_units"]),
        ready_units=int(data["ready_units"]),
        linked_task_bundles=int(data["linked_task_bundles"]),
        task_family_counts={str(key): int(value) for key, value in data.get("task_family_counts", {}).items()},
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        release_tier_counts={str(key): int(value) for key, value in data.get("release_tier_counts", {}).items()},
        missing_task_bundle_ids=tuple(str(item) for item in data.get("missing_task_bundle_ids", [])),
        duplicate_validation_unit_ids=tuple(
            str(item) for item in data.get("duplicate_validation_unit_ids", [])
        ),
        duplicate_task_bundle_ids=tuple(str(item) for item in data.get("duplicate_task_bundle_ids", [])),
        missing_rubric_axes={
            str(key): tuple(str(item) for item in value)
            for key, value in data.get("missing_rubric_axes", {}).items()
        },
        issues=tuple(str(item) for item in data.get("issues", [])),
        ok=bool(data.get("ok", False)),
    )


def judge_review_form_from_dict(data: Dict[str, Any]) -> JudgeReviewForm:
    return JudgeReviewForm(
        validation_unit_id=str(data["validation_unit_id"]),
        reviewer_id=str(data["reviewer_id"]),
        completed=bool(data.get("completed", False)),
        rubric_labels=dict(data.get("rubric_labels", {})),
        confidence=int(data["confidence"]) if data.get("confidence") is not None else None,
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def judge_adjudication_record_from_dict(data: Dict[str, Any]) -> JudgeAdjudicationRecord:
    return JudgeAdjudicationRecord(
        validation_unit_id=str(data["validation_unit_id"]),
        adjudicator_id=str(data["adjudicator_id"]),
        final_rubric_labels=dict(data.get("final_rubric_labels", {})),
        finalized=bool(data.get("finalized", False)),
        rationale=tuple(str(item) for item in data.get("rationale", [])),
        source_reviewer_ids=tuple(str(item) for item in data.get("source_reviewer_ids", [])),
    )


def judge_adjudication_queue_entry_from_dict(data: Dict[str, Any]) -> JudgeAdjudicationQueueEntry:
    return JudgeAdjudicationQueueEntry(
        validation_unit_id=str(data["validation_unit_id"]),
        status=str(data["status"]),
        required_reviewer_count=int(data["required_reviewer_count"]),
        completed_reviewer_ids=tuple(str(item) for item in data.get("completed_reviewer_ids", [])),
        pending_reviewer_ids=tuple(str(item) for item in data.get("pending_reviewer_ids", [])),
        disagreement_axes=tuple(str(item) for item in data.get("disagreement_axes", [])),
        has_final_adjudication=bool(data.get("has_final_adjudication", False)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def maintenance_log_entry_from_dict(data: Dict[str, Any]) -> MaintenanceLogEntry:
    return MaintenanceLogEntry(
        entry_id=str(data["entry_id"]),
        created_at=str(data["created_at"]),
        phase=str(data["phase"]),
        summary=str(data["summary"]),
        release_bundle_id=data.get("release_bundle_id"),
        artifacts=tuple(str(item) for item in data.get("artifacts", [])),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def program_progress_report_from_dict(data: Dict[str, Any]) -> ProgramProgressReport:
    return ProgramProgressReport(
        generated_at=str(data["generated_at"]),
        source_candidates=int(data["source_candidates"]),
        paper_qualified=int(data["paper_qualified"]),
        task_bundles_total=int(data["task_bundles_total"]),
        public_units=int(data["public_units"]),
        private_units=int(data["private_units"]),
        hybrid_overlay_units=int(data.get("hybrid_overlay_units", 0)),
        controlled_access_qualified_papers=int(data.get("controlled_access_qualified_papers", 0)),
        judge_validation_units=int(data.get("judge_validation_units", 0)),
        replayable_baselines=int(data.get("replayable_baselines", 0)),
        study_class_counts={str(key): int(value) for key, value in data.get("study_class_counts", {}).items()},
        task_family_counts={str(key): int(value) for key, value in data.get("task_family_counts", {}).items()},
        claim_mode_counts={str(key): int(value) for key, value in data.get("claim_mode_counts", {}).items()},
        v1_core_gate_passed=bool(data.get("v1_core_gate_passed", False)),
        leaderboard_gate_passed=bool(data.get("leaderboard_gate_passed", False)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def calibration_drift_report_from_dict(data: Dict[str, Any]) -> CalibrationDriftReport:
    return CalibrationDriftReport(
        baseline_total_specs=int(data["baseline_total_specs"]),
        updated_total_specs=int(data["updated_total_specs"]),
        added_calibration_ids=tuple(str(item) for item in data.get("added_calibration_ids", [])),
        removed_calibration_ids=tuple(str(item) for item in data.get("removed_calibration_ids", [])),
        study_class_count_delta={str(key): int(value) for key, value in data.get("study_class_count_delta", {}).items()},
        candidate_tier_count_delta={
            str(key): int(value) for key, value in data.get("candidate_tier_count_delta", {}).items()
        },
        hybrid_overlay_delta=int(data.get("hybrid_overlay_delta", 0)),
        quarantine_delta=int(data.get("quarantine_delta", 0)),
        controlled_access_delta=int(data.get("controlled_access_delta", 0)),
        preprint_delta=int(data.get("preprint_delta", 0)),
        negative_or_descriptive_delta=int(data.get("negative_or_descriptive_delta", 0)),
        changed_target_labels=tuple(str(item) for item in data.get("changed_target_labels", [])),
    )


def execution_profile_from_dict(data: Dict[str, Any]) -> ExecutionProfile:
    return ExecutionProfile(
        profile_id=str(data["profile_id"]),
        profile_name=str(data["profile_name"]),
        backend=str(data["backend"]),
        root_path=str(data["root_path"]),
        repo_root=str(data["repo_root"]),
        working_directory=str(data["working_directory"]),
        python_bin=str(data.get("python_bin", "python3")),
        launch_prefix=tuple(str(item) for item in data.get("launch_prefix", [])),
        environment_exports={
            str(key): str(value) for key, value in data.get("environment_exports", {}).items()
        },
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def execution_job_spec_from_dict(data: Dict[str, Any]) -> ExecutionJobSpec:
    return ExecutionJobSpec(
        job_id=str(data["job_id"]),
        job_name=str(data["job_name"]),
        profile_id=str(data["profile_id"]),
        job_kind=str(data["job_kind"]),
        backend=str(data["backend"]),
        working_directory=str(data["working_directory"]),
        command_sequence=tuple(str(item) for item in data.get("command_sequence", [])),
        environment_exports={
            str(key): str(value) for key, value in data.get("environment_exports", {}).items()
        },
        output_artifacts={
            str(key): str(value) for key, value in data.get("output_artifacts", {}).items()
        },
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def adjudication_queue_entry_from_dict(data: Dict[str, Any]) -> AdjudicationQueueEntry:
    return AdjudicationQueueEntry(
        calibration_id=str(data["calibration_id"]),
        status=str(data["status"]),
        required_reviewer_count=int(data["required_reviewer_count"]),
        completed_reviewer_ids=tuple(str(item) for item in data.get("completed_reviewer_ids", [])),
        pending_reviewer_ids=tuple(str(item) for item in data.get("pending_reviewer_ids", [])),
        disagreement_fields=tuple(str(item) for item in data.get("disagreement_fields", [])),
        has_final_adjudication=bool(data.get("has_final_adjudication", False)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def pilot_review_form_from_dict(data: Dict[str, Any]) -> PilotReviewForm:
    return PilotReviewForm(
        calibration_id=str(data["calibration_id"]),
        reviewer_id=str(data["reviewer_id"]),
        study_class=_enum(StudyClass, data["study_class"]) if data.get("study_class") else None,
        claim_mode=_enum(ClaimMode, data["claim_mode"]) if data.get("claim_mode") else None,
        candidate_tier=_enum(CandidateTier, data["candidate_tier"]) if data.get("candidate_tier") else None,
        unit_release_tier=_enum(ReleaseTier, data["unit_release_tier"])
        if data.get("unit_release_tier")
        else None,
        completed=bool(data.get("completed", False)),
        confidence=int(data["confidence"]) if data.get("confidence") is not None else None,
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


def pilot_adjudication_record_from_dict(data: Dict[str, Any]) -> PilotAdjudicationRecord:
    return PilotAdjudicationRecord(
        calibration_id=str(data["calibration_id"]),
        adjudicator_id=str(data["adjudicator_id"]),
        final_study_class=_enum(StudyClass, data["final_study_class"])
        if data.get("final_study_class")
        else None,
        final_claim_mode=_enum(ClaimMode, data["final_claim_mode"])
        if data.get("final_claim_mode")
        else None,
        final_candidate_tier=_enum(CandidateTier, data["final_candidate_tier"])
        if data.get("final_candidate_tier")
        else None,
        final_unit_release_tier=_enum(ReleaseTier, data["final_unit_release_tier"])
        if data.get("final_unit_release_tier")
        else None,
        finalized=bool(data.get("finalized", False)),
        rationale=tuple(str(item) for item in data.get("rationale", [])),
        source_reviewer_ids=tuple(str(item) for item in data.get("source_reviewer_ids", [])),
    )


def agreement_metric_from_dict(data: Dict[str, Any]) -> AgreementMetric:
    return AgreementMetric(
        label=str(data["label"]),
        matches=int(data["matches"]),
        comparisons=int(data["comparisons"]),
        rate=float(data["rate"]),
    )


def pilot_agreement_summary_from_dict(data: Dict[str, Any]) -> PilotAgreementSummary:
    return PilotAgreementSummary(
        study_class=agreement_metric_from_dict(data["study_class"]),
        claim_mode=agreement_metric_from_dict(data["claim_mode"]),
        candidate_tier=agreement_metric_from_dict(data["candidate_tier"]),
        unit_release_tier=agreement_metric_from_dict(data["unit_release_tier"]),
    )


MODEL_LOADERS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "agreement_metric": agreement_metric_from_dict,
    "adjudication_queue_entry": adjudication_queue_entry_from_dict,
    "adjudicated_paper_review_record": adjudicated_paper_review_record_from_dict,
    "answer_record": answer_record_from_dict,
    "auto_aggregated_paper_review_record": auto_aggregated_paper_review_record_from_dict,
    "auto_review_evidence_enrichment_audit_report": auto_review_evidence_enrichment_audit_report_from_dict,
    "auto_review_evidence_enrichment_record": auto_review_evidence_enrichment_record_from_dict,
    "auto_panel_vote": auto_panel_vote_from_dict,
    "auto_qualification_record": auto_qualification_record_from_dict,
    "auto_review_batch_report": auto_review_batch_report_from_dict,
    "auto_review_recovery_batch_entry": auto_review_recovery_batch_entry_from_dict,
    "auto_review_recovery_batch_report": auto_review_recovery_batch_report_from_dict,
    "auto_review_source_bundle": auto_review_source_bundle_from_dict,
    "auto_review_source_bundle_audit_report": auto_review_source_bundle_audit_report_from_dict,
    "api_fetch_record": api_fetch_record_from_dict,
    "api_query_spec": api_query_spec_from_dict,
    "assertion_record": assertion_record_from_dict,
    "baseline_run_spec": baseline_run_spec_from_dict,
    "benchmark_unit_decision_record": benchmark_unit_decision_record_from_dict,
    "benchmark_unit": benchmark_unit_from_dict,
    "bundle_verification_report": bundle_verification_report_from_dict,
    "calibration_drift_report": calibration_drift_report_from_dict,
    "collection_batch_report": collection_batch_report_from_dict,
    "collection_batch_spec": collection_batch_spec_from_dict,
    "collection_candidate_record": collection_candidate_record_from_dict,
    "evaluation_record": evaluation_record_from_dict,
    "evaluation_extraction_audit_report": evaluation_extraction_audit_report_from_dict,
    "execution_job_spec": execution_job_spec_from_dict,
    "execution_profile": execution_profile_from_dict,
    "extraction_audit_report": extraction_audit_report_from_dict,
    "evidence_extraction_record": evidence_extraction_record_from_dict,
    "evidence_record": evidence_record_from_dict,
    "evidence_unit": evidence_unit_from_dict,
    "ingestion_audit_report": ingestion_audit_report_from_dict,
    "ingestion_record": ingestion_record_from_dict,
    "ingestion_verification_report": ingestion_verification_report_from_dict,
    "judge_candidate_selection_report": judge_candidate_selection_report_from_dict,
    "judge_slice_audit_report": judge_slice_audit_report_from_dict,
    "judge_review_form": judge_review_form_from_dict,
    "judge_adjudication_record": judge_adjudication_record_from_dict,
    "judge_adjudication_queue_entry": judge_adjudication_queue_entry_from_dict,
    "judge_validation_unit": judge_validation_unit_from_dict,
    "maintenance_log_entry": maintenance_log_entry_from_dict,
    "metadata_source_record": metadata_source_record_from_dict,
    "metadata_governance_hint": metadata_governance_hint_from_dict,
    "observation_record": observation_record_from_dict,
    "paper_review_batch_entry": paper_review_batch_entry_from_dict,
    "paper_review_adjudication_record": paper_review_adjudication_record_from_dict,
    "paper_review_batch_report": paper_review_batch_report_from_dict,
    "paper_review_packet": paper_review_packet_from_dict,
    "paper_review_packet_report": paper_review_packet_report_from_dict,
    "paper_review_progress_summary": paper_review_progress_summary_from_dict,
    "paper_review_queue_entry": paper_review_queue_entry_from_dict,
    "paper_reviewer_handoff_report": paper_reviewer_handoff_report_from_dict,
    "paper_review_workload_report": paper_review_workload_report_from_dict,
    "paper_reviewer_assignment": paper_reviewer_assignment_from_dict,
    "paper_packaging_review_record": paper_packaging_review_record_from_dict,
    "paper_qualification_batch_report": paper_qualification_batch_report_from_dict,
    "paper_qualification_record": paper_qualification_record_from_dict,
    "paper_scientific_review_form": paper_scientific_review_form_from_dict,
    "paper_writing_review_form": paper_writing_review_form_from_dict,
    "parser_assisted_extraction_report": parser_assisted_extraction_report_from_dict,
    "packaging_review": packaging_review_from_dict,
    "paper_qualification_decision": paper_qualification_decision_from_dict,
    "pilot_adjudication_record": pilot_adjudication_record_from_dict,
    "pilot_agreement_summary": pilot_agreement_summary_from_dict,
    "pilot_calibration_spec": pilot_calibration_spec_from_dict,
    "pilot_review_form": pilot_review_form_from_dict,
    "pmc_full_text_fetch_record": pmc_full_text_fetch_record_from_dict,
    "question_record": question_record_from_dict,
    "release_artifact_checksum": release_artifact_checksum_from_dict,
    "release_provenance_manifest": release_provenance_manifest_from_dict,
    "scientific_review": scientific_review_from_dict,
    "shadow_inspection_batch_report": shadow_inspection_batch_report_from_dict,
    "shadow_inspection_delta_report": shadow_inspection_delta_report_from_dict,
    "shadow_inspection_entry": shadow_inspection_entry_from_dict,
    "shadow_inspection_taxonomy_category": shadow_inspection_taxonomy_category_from_dict,
    "shadow_inspection_taxonomy_report": shadow_inspection_taxonomy_report_from_dict,
    "source_paper": source_paper_from_dict,
    "source_quality_record": source_quality_record_from_dict,
    "split_safety_violation": split_safety_violation_from_dict,
    "submission_record": submission_record_from_dict,
    "task_bundle": task_bundle_from_dict,
    "task_bundle_inventory_report": task_bundle_inventory_report_from_dict,
    "truth_manifest": truth_manifest_from_dict,
    "truth_manifest_bundle": truth_manifest_bundle_from_dict,
    "truth_manifest_verification_report": truth_manifest_verification_report_from_dict,
    "unit_qualification_decision": unit_qualification_decision_from_dict,
    "writing_review": writing_review_from_dict,
    "program_progress_report": program_progress_report_from_dict,
}
