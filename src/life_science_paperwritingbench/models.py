from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

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


def _primitive(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_primitive(item) for item in value]
    if isinstance(value, list):
        return [_primitive(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _primitive(item) for key, item in value.items()}
    if hasattr(value, "value"):
        return value.value
    if is_dataclass(value):
        return {key: _primitive(item) for key, item in asdict(value).items()}
    return value


@dataclass(frozen=True)
class LineageInfo:
    source_family: Optional[str] = None
    consortium_lineages: Tuple[str, ...] = ()
    dataset_lineages: Tuple[str, ...] = ()
    lab_lineages: Tuple[str, ...] = ()

    def tokens(self) -> Mapping[str, Tuple[str, ...]]:
        return {
            "source_family": (self.source_family,) if self.source_family else (),
            "consortium_lineage": self.consortium_lineages,
            "dataset_lineage": self.dataset_lineages,
            "lab_lineage": self.lab_lineages,
        }


@dataclass(frozen=True)
class SourcePaper:
    paper_id: str
    title: str
    publication_year: int
    publication_status: PublicationStatus
    peer_reviewed: bool
    study_class: StudyClass
    claim_mode: ClaimMode
    modality_overlays: Tuple[ModalityOverlay, ...] = ()
    lineage: LineageInfo = field(default_factory=LineageInfo)
    crossmark_updates: Tuple[CrossmarkUpdateType, ...] = ()
    integrity_flags: Tuple[IntegrityFlag, ...] = ()
    major_correction_affects_interpretation: bool = False
    partial_retraction_invalidates_core_claims: bool = False
    explicit_pre2018_exception: bool = False
    controlled_access_human_data: bool = False
    small_cell_risk: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class IngestionRecord:
    ingestion_id: str
    source_name: str
    source_record_id: str
    paper_id: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    normalized_title: str = ""
    publication_year: Optional[int] = None
    releaseability_precheck_passed: bool = False
    releaseability_flags: Tuple[str, ...] = ()
    metadata_fingerprint_sha256: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class MetadataSourceRecord:
    ingestion_id: str
    source_name: str
    source_record_id: str
    title: str
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    publication_status: PublicationStatus = PublicationStatus.UNKNOWN
    peer_reviewed: Optional[bool] = None
    study_class: Optional[StudyClass] = None
    claim_mode: Optional[ClaimMode] = None
    modality_overlays: Tuple[ModalityOverlay, ...] = ()
    lineage: LineageInfo = field(default_factory=LineageInfo)
    crossmark_updates: Tuple[CrossmarkUpdateType, ...] = ()
    integrity_flags: Tuple[IntegrityFlag, ...] = ()
    explicit_pre2018_exception: bool = False
    controlled_access_human_data: bool = False
    small_cell_risk: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ApiQuerySpec:
    batch_id: str
    study_class: StudyClass
    lane: str
    source: str
    query_text: str
    retmax: int
    year_start: int
    year_end: int

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ApiFetchRecord:
    fetch_id: str
    source: str
    study_class: StudyClass
    lane: str
    source_record_id: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    title: str = ""
    publication_year: Optional[int] = None
    journal: str = ""
    abstract: str = ""
    publication_status: PublicationStatus = PublicationStatus.UNKNOWN
    peer_reviewed: Optional[bool] = None
    raw_payload_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class CollectionCandidateRecord:
    candidate_id: str
    paper_key: str
    study_class_votes: Mapping[str, int] = field(default_factory=dict)
    selected_study_class: Optional[StudyClass] = None
    shortlist_target_class: Optional[StudyClass] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    title: str = ""
    publication_year: Optional[int] = None
    journal: str = ""
    abstract: str = ""
    publication_status: PublicationStatus = PublicationStatus.UNKNOWN
    peer_reviewed: Optional[bool] = None
    oa_fulltext_available: bool = False
    license: Optional[str] = None
    crossmark_updates: Tuple[CrossmarkUpdateType, ...] = ()
    open_review_signal: bool = False
    benchmark_ready_signal_count: int = 0
    rank_tuple: Tuple[Any, ...] = ()
    source_names: Tuple[str, ...] = ()
    source_record_ids: Tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class CollectionBatchSpec:
    batch_id: str
    year_start: int
    year_end: int
    primary_retmax: int
    reserve_retmax: int
    target_candidates_per_class: int
    seed_source: str
    enrichment_sources: Tuple[str, ...] = ()
    oa_fulltext_policy: str = "preferred"
    query_specs: Tuple[ApiQuerySpec, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class CollectionBatchReport:
    generated_at: str
    batch_id: str
    total_queries: int
    total_raw_fetch_records: int
    total_candidates: int
    source_counts: Mapping[str, int] = field(default_factory=dict)
    class_candidate_counts: Mapping[str, int] = field(default_factory=dict)
    class_shortlist_counts: Mapping[str, int] = field(default_factory=dict)
    class_deficits: Mapping[str, int] = field(default_factory=dict)
    identifier_coverage: Mapping[str, int] = field(default_factory=dict)
    oa_fulltext_available_count: int = 0
    open_review_signal_count: int = 0
    releaseability_precheck_passed: int = 0
    releaseability_precheck_failed: int = 0
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PmcFullTextFetchRecord:
    paper_id: str
    pmcid: Optional[str] = None
    fetch_url: str = ""
    raw_payload_path: str = ""
    fetch_ok: bool = False
    used_cache: bool = False
    content_sha256: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoReviewEvidenceEnrichmentRecord:
    paper_id: str
    pmcid: Optional[str] = None
    raw_payload_path: str = ""
    methods_text: str = ""
    results_text: str = ""
    figure_captions: Tuple[str, ...] = ()
    table_snippets: Tuple[str, ...] = ()
    figure_reference_snippets: Tuple[str, ...] = ()
    table_reference_snippets: Tuple[str, ...] = ()
    resource_identifiers: Tuple[str, ...] = ()
    trial_registry_ids: Tuple[str, ...] = ()
    trial_registry_reference_snippets: Tuple[str, ...] = ()
    provenance_fields: Mapping[str, str] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoReviewEvidenceEnrichmentAuditReport:
    generated_at: str
    total_records: int
    methods_text_count: int = 0
    results_text_count: int = 0
    figure_caption_count: int = 0
    table_snippet_count: int = 0
    figure_reference_snippet_count: int = 0
    table_reference_snippet_count: int = 0
    resource_identifier_count: int = 0
    trial_registry_count: int = 0
    trial_registry_reference_snippet_count: int = 0
    fetch_ok_count: int = 0
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class IngestionAuditReport:
    generated_at: str
    raw_records: int
    normalized_papers: int
    merged_duplicates: int
    releaseability_precheck_passed: int = 0
    releaseability_precheck_failed: int = 0
    source_counts: Mapping[str, int] = field(default_factory=dict)
    publication_status_counts: Mapping[str, int] = field(default_factory=dict)
    identifier_coverage: Mapping[str, int] = field(default_factory=dict)
    releaseability_flag_counts: Mapping[str, int] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class IngestionVerificationReport:
    ok: bool
    normalized_papers: int
    ingestion_records: int
    duplicate_paper_ids: Tuple[str, ...] = ()
    duplicate_ingestion_ids: Tuple[str, ...] = ()
    missing_normalized_titles: Tuple[str, ...] = ()
    missing_metadata_fingerprints: Tuple[str, ...] = ()
    precedence_violations: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoReviewSourceBundle:
    paper_id: str
    bundle_completeness: AutoReviewBundleCompleteness
    abstract_text: str = ""
    methods_text: str = ""
    results_text: str = ""
    figure_captions: Tuple[str, ...] = ()
    table_snippets: Tuple[str, ...] = ()
    figure_reference_snippets: Tuple[str, ...] = ()
    table_reference_snippets: Tuple[str, ...] = ()
    resource_identifiers: Tuple[str, ...] = ()
    trial_registry_ids: Tuple[str, ...] = ()
    trial_registry_reference_snippets: Tuple[str, ...] = ()
    open_review_snippets: Tuple[str, ...] = ()
    provenance_fields: Mapping[str, str] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoReviewSourceBundleAuditReport:
    generated_at: str
    total_bundles: int
    completeness_counts: Mapping[str, int] = field(default_factory=dict)
    methods_text_count: int = 0
    results_text_count: int = 0
    figure_caption_count: int = 0
    table_snippet_count: int = 0
    figure_reference_snippet_count: int = 0
    table_reference_snippet_count: int = 0
    resource_identifier_count: int = 0
    trial_registry_count: int = 0
    trial_registry_reference_snippet_count: int = 0
    open_review_snippet_count: int = 0
    provenance_warning_paper_ids: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoPanelVote:
    paper_id: str
    role: AutoReviewRole
    critical_domain_votes: Mapping[ScientificCriticalDomain, DomainOutcome] = field(default_factory=dict)
    supporting_domain_votes: Mapping[ScientificSupportingDomain, DomainOutcome] = field(default_factory=dict)
    writing_domain_votes: Mapping[WritingCriticalDomain, DomainOutcome] = field(default_factory=dict)
    insufficient_evidence_flags: Tuple[str, ...] = ()
    rationale: str = ""
    prompt_fingerprint: str = ""
    model_fingerprint: str = ""
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ScientificReview:
    critical_domains: Mapping[ScientificCriticalDomain, DomainOutcome]
    supporting_domains: Mapping[ScientificSupportingDomain, DomainOutcome]
    applied_standards: Tuple[StandardId, ...] = ()
    standard_outcomes: Mapping[StandardId, DomainOutcome] = field(default_factory=dict)
    standard_notes: Mapping[StandardId, str] = field(default_factory=dict)
    audit_evidence: Mapping[AuditEvidenceDomain, str] = field(default_factory=dict)
    contemporary_bonus: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class WritingReview:
    critical_domains: Mapping[WritingCriticalDomain, DomainOutcome]
    supporting_domains: Mapping[WritingSupportingDomain, DomainOutcome]
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoAggregatedPaperReviewRecord:
    paper_id: str
    scientific_review: ScientificReview
    writing_review: WritingReview
    review_origin: str = "auto_panel"
    confidence: AutoReviewConfidence = AutoReviewConfidence.LOW
    skipped_writing_review: bool = False
    auto_release_cap_reason: Optional[str] = None
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PackagingReview:
    domain_outcomes: Mapping[PackagingDomain, DomainOutcome]
    safe_derived_artifacts: Tuple[SafeDerivedArtifact, ...] = ()
    artifact_inventory_id: Optional[str] = None
    restricted_artifact_types: Tuple[str, ...] = ()
    contains_private_row_level_data: bool = False
    contains_recomputed_sensitive_aggregates: bool = False
    redistributes_restricted_supplements: bool = False
    controlled_access_rule_satisfied: bool = True
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperPackagingReviewRecord:
    paper_id: str
    packaging_review: PackagingReview

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class EvidenceUnit:
    unit_id: str
    paper_id: str
    unit_type: EvidenceUnitType
    evidence_pointers: Tuple[str, ...]
    locally_supported: bool
    internally_coherent: bool
    depends_on_excluded_narrative: bool
    releasable: bool
    description: str = ""
    modality_overlays: Tuple[ModalityOverlay, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AssertionRecord:
    assertion_id: str
    paper_id: str
    text: str
    claim_mode: Optional[ClaimMode] = None
    supported: bool = True
    excluded: bool = False
    evidence_record_ids: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    paper_id: str
    evidence_type: str
    pointer: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    paper_id: str
    task_family: TaskFamily
    observation_type: ObservationType
    text: str
    evidence_unit_id: Optional[str] = None
    pointer: Optional[str] = None
    evidence_record_ids: Tuple[str, ...] = ()
    provenance_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class QuestionRecord:
    question_id: str
    paper_id: str
    task_family: TaskFamily
    prompt: str
    answer_format: AnswerFormat = AnswerFormat.FREE_TEXT
    evidence_unit_id: Optional[str] = None
    supporting_observation_ids: Tuple[str, ...] = ()
    supporting_evidence_pointers: Tuple[str, ...] = ()
    expected_answer_ids: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AnswerRecord:
    answer_id: str
    paper_id: str
    question_id: str
    answer_text: str
    rationale: str = ""
    supporting_observation_ids: Tuple[str, ...] = ()
    supporting_evidence_pointers: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class SourceQualityRecord:
    quality_record_id: str
    paper_id: str
    concern_type: SourceQualityConcernType
    severity: SourceQualitySeverity
    text: str
    pointer: Optional[str] = None
    evidence_unit_id: Optional[str] = None
    supporting_observation_ids: Tuple[str, ...] = ()
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class EvidenceExtractionRecord:
    extraction_id: str
    paper_id: str
    evidence_unit_id: str
    assertion_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()
    excluded_assertion_ids: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ExtractionAuditReport:
    generated_at: str
    paper_count: int
    evidence_unit_count: int
    extraction_count: int
    assertion_count: int
    excluded_assertion_count: int = 0
    evidence_record_count: int = 0
    unit_type_counts: Mapping[str, int] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ParserAssistedExtractionReport:
    generated_at: str
    paper_count: int
    papers_with_suggestions: int
    evidence_unit_count: int
    extraction_spec_count: int
    unit_type_counts: Mapping[str, int] = field(default_factory=dict)
    skipped_paper_ids: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class EvaluationExtractionAuditReport:
    generated_at: str
    paper_count: int
    observation_count: int
    question_count: int
    answer_count: int
    source_quality_count: int
    task_family_counts: Mapping[str, int] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class BenchmarkUnit:
    benchmark_unit_id: str
    paper_id: str
    evidence_unit_ids: Tuple[str, ...]
    split: Optional[str] = None
    lineage: LineageInfo = field(default_factory=LineageInfo)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class TruthManifest:
    manifest_id: str
    paper_id: str
    assertion_ids: Tuple[str, ...]
    assertion_texts: Tuple[str, ...]
    evidence_items: Tuple[str, ...]
    evidence_types: Tuple[str, ...]
    excluded_assertions: Tuple[str, ...] = ()
    caveats: Tuple[str, ...] = ()
    provenance_entities: Tuple[str, ...] = ()
    provenance_activities: Tuple[str, ...] = ()
    provenance_agents: Tuple[str, ...] = ()
    applied_standards: Tuple[StandardId, ...] = ()
    study_class: Optional[StudyClass] = None
    modality_overlays: Tuple[ModalityOverlay, ...] = ()
    frozen: bool = False
    frozen_at: Optional[str] = None
    version: str = "v5"

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class TruthManifestBundle:
    bundle_id: str
    paper_id: str
    manifest_id: str
    evidence_unit_ids: Tuple[str, ...] = ()
    assertion_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()
    provenance_manifest_id: Optional[str] = None
    release_ready: bool = False
    frozen_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class TruthManifestVerificationReport:
    manifest_id: str
    paper_id: str
    ok: bool
    frozen: bool
    missing_assertion_ids: Tuple[str, ...] = ()
    missing_evidence_ids: Tuple[str, ...] = ()
    missing_extraction_ids: Tuple[str, ...] = ()
    inconsistent_paper_ids: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperQualificationDecision:
    scientific: PaperScientificQualification
    packaging: PaperPackagingQualification
    candidate_tier: CandidateTier
    eligible_for_unit_extraction: bool
    required_standards: Tuple[StandardId, ...]
    writing: PaperWritingQualification = PaperWritingQualification.W2
    public_writing_eligible: bool = False
    missing_standards: Tuple[StandardId, ...] = ()
    integrity_disposition: IntegrityDisposition = IntegrityDisposition.CLEAR
    reasons: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperQualificationRecord:
    paper_id: str
    decision: PaperQualificationDecision

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoQualificationRecord:
    paper_id: str
    decision: PaperQualificationDecision
    review_origin: str = "auto_panel"
    confidence: AutoReviewConfidence = AutoReviewConfidence.LOW
    auto_release_cap_reason: Optional[str] = None
    judge_validation_ready: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperQualificationBatchReport:
    generated_at: str
    total_papers: int
    adjudicated_reviews_loaded: int
    packaging_reviews_loaded: int
    decisions_written: int
    scientific_counts: Mapping[str, int] = field(default_factory=dict)
    writing_counts: Mapping[str, int] = field(default_factory=dict)
    packaging_counts: Mapping[str, int] = field(default_factory=dict)
    candidate_tier_counts: Mapping[str, int] = field(default_factory=dict)
    public_writing_eligible_count: int = 0
    missing_adjudicated_review_paper_ids: Tuple[str, ...] = ()
    missing_packaging_review_paper_ids: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoReviewBatchReport:
    generated_at: str
    total_papers: int
    source_bundle_count: int = 0
    panel_vote_count: int = 0
    aggregated_review_count: int = 0
    qualification_count: int = 0
    completeness_counts: Mapping[str, int] = field(default_factory=dict)
    scientific_counts: Mapping[str, int] = field(default_factory=dict)
    writing_counts: Mapping[str, int] = field(default_factory=dict)
    packaging_counts: Mapping[str, int] = field(default_factory=dict)
    candidate_tier_counts: Mapping[str, int] = field(default_factory=dict)
    confidence_counts: Mapping[str, int] = field(default_factory=dict)
    eligible_for_unit_extraction_count: int = 0
    skipped_writing_review_count: int = 0
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoReviewRecoveryBatchEntry:
    paper_id: str
    title: str
    study_class: StudyClass
    claim_mode: ClaimMode
    priority_bucket: str
    priority_rank: int
    candidate_tier: CandidateTier
    scientific: PaperScientificQualification
    writing: PaperWritingQualification
    packaging: PaperPackagingQualification
    bundle_completeness: AutoReviewBundleCompleteness
    confidence: AutoReviewConfidence
    auto_release_cap_reason: Optional[str] = None
    selected: bool = False
    selection_rank: Optional[int] = None
    selection_reason: Optional[str] = None
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AutoReviewRecoveryBatchReport:
    generated_at: str
    total_candidates: int
    target_total: int
    selected_total: int
    preferred_buckets: Tuple[str, ...] = ()
    per_class_target: Optional[int] = None
    bucket_counts: Mapping[str, int] = field(default_factory=dict)
    selected_bucket_counts: Mapping[str, int] = field(default_factory=dict)
    selected_study_class_counts: Mapping[str, int] = field(default_factory=dict)
    selected_claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    selected_confidence_counts: Mapping[str, int] = field(default_factory=dict)
    selected_paper_ids: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class MetadataGovernanceHint:
    paper_id: str
    suggested_study_class: Optional[StudyClass] = None
    suggested_claim_mode: Optional[ClaimMode] = None
    suggested_modality_overlays: Tuple[ModalityOverlay, ...] = ()
    suggested_required_standards: Tuple[StandardId, ...] = ()
    matched_terms: Mapping[str, Tuple[str, ...]] = field(default_factory=dict)
    warnings: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewBatchEntry:
    batch_id: str
    paper_id: str
    title: str
    publication_year: Optional[int]
    publication_status: PublicationStatus
    peer_reviewed: Optional[bool]
    candidate_study_class: Optional[StudyClass] = None
    candidate_claim_mode: Optional[ClaimMode] = None
    candidate_modality_overlays: Tuple[ModalityOverlay, ...] = ()
    metadata_hint_study_class: Optional[StudyClass] = None
    metadata_hint_claim_mode: Optional[ClaimMode] = None
    metadata_hint_overlays: Tuple[ModalityOverlay, ...] = ()
    metadata_hint_warnings: Tuple[str, ...] = ()
    recommended_standards: Tuple[StandardId, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperScientificReviewForm:
    batch_id: str
    paper_id: str
    reviewer_id: str
    study_class_override: Optional[StudyClass] = None
    claim_mode_override: Optional[ClaimMode] = None
    modality_overlay_overrides: Tuple[ModalityOverlay, ...] = ()
    critical_domains: Mapping[ScientificCriticalDomain, Optional[DomainOutcome]] = field(default_factory=dict)
    supporting_domains: Mapping[ScientificSupportingDomain, Optional[DomainOutcome]] = field(default_factory=dict)
    recommended_standards: Tuple[StandardId, ...] = ()
    applied_standards: Tuple[StandardId, ...] = ()
    standard_outcomes: Mapping[StandardId, Optional[DomainOutcome]] = field(default_factory=dict)
    completed: bool = False
    confidence: Optional[int] = None
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperWritingReviewForm:
    batch_id: str
    paper_id: str
    reviewer_id: str
    critical_domains: Mapping[WritingCriticalDomain, Optional[DomainOutcome]] = field(default_factory=dict)
    supporting_domains: Mapping[WritingSupportingDomain, Optional[DomainOutcome]] = field(default_factory=dict)
    completed: bool = False
    confidence: Optional[int] = None
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewBatchReport:
    generated_at: str
    batch_id: str
    total_papers: int
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    metadata_warning_count: int = 0
    peer_reviewed_count: int = 0
    publication_status_counts: Mapping[str, int] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewPacket:
    batch_id: str
    paper_id: str
    title: str
    publication_year: Optional[int]
    publication_status: PublicationStatus
    peer_reviewed: Optional[bool]
    candidate_study_class: Optional[StudyClass] = None
    candidate_claim_mode: Optional[ClaimMode] = None
    candidate_modality_overlays: Tuple[ModalityOverlay, ...] = ()
    metadata_hint_study_class: Optional[StudyClass] = None
    metadata_hint_claim_mode: Optional[ClaimMode] = None
    metadata_hint_overlays: Tuple[ModalityOverlay, ...] = ()
    metadata_hint_warnings: Tuple[str, ...] = ()
    recommended_standards: Tuple[StandardId, ...] = ()
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    journal: str = ""
    abstract: str = ""
    oa_fulltext_available: bool = False
    license: Optional[str] = None
    open_review_signal: bool = False
    benchmark_ready_signal_count: int = 0
    packaging_domain_outcomes: Mapping[PackagingDomain, DomainOutcome] = field(default_factory=dict)
    safe_derived_artifacts: Tuple[SafeDerivedArtifact, ...] = ()
    artifact_inventory_id: Optional[str] = None
    restricted_artifact_types: Tuple[str, ...] = ()
    review_priority: Tuple[Any, ...] = ()
    review_priority_rank: int = 0
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewPacketReport:
    generated_at: str
    batch_id: str
    total_packets: int
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    metadata_warning_count: int = 0
    oa_fulltext_available_count: int = 0
    open_review_signal_count: int = 0
    packaging_domain_pass_counts: Mapping[str, int] = field(default_factory=dict)
    top_priority_paper_ids: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewerAssignment:
    batch_id: str
    reviewer_id: str
    paper_id: str
    review_priority_rank: int
    packet: PaperReviewPacket
    scientific_review_form: PaperScientificReviewForm
    writing_review_form: PaperWritingReviewForm

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewWorkloadReport:
    generated_at: str
    batch_id: str
    reviewer_ids: Tuple[str, ...] = ()
    reviewer_assignment_counts: Mapping[str, int] = field(default_factory=dict)
    top_priority_paper_ids_by_reviewer: Mapping[str, Tuple[str, ...]] = field(default_factory=dict)
    total_assignments: int = 0
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewerHandoffReport:
    generated_at: str
    batch_id: str
    reviewer_id: str
    total_assignments: int
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    metadata_warning_count: int = 0
    open_review_signal_count: int = 0
    restricted_artifact_assignment_count: int = 0
    top_priority_paper_ids: Tuple[str, ...] = ()
    top_priority_warning_paper_ids: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewAdjudicationRecord:
    batch_id: str
    paper_id: str
    adjudicator_id: str
    final_study_class: Optional[StudyClass] = None
    final_claim_mode: Optional[ClaimMode] = None
    final_modality_overlays: Tuple[ModalityOverlay, ...] = ()
    scientific_critical_domains: Mapping[ScientificCriticalDomain, Optional[DomainOutcome]] = field(default_factory=dict)
    scientific_supporting_domains: Mapping[ScientificSupportingDomain, Optional[DomainOutcome]] = field(default_factory=dict)
    applied_standards: Tuple[StandardId, ...] = ()
    standard_outcomes: Mapping[StandardId, Optional[DomainOutcome]] = field(default_factory=dict)
    writing_critical_domains: Mapping[WritingCriticalDomain, Optional[DomainOutcome]] = field(default_factory=dict)
    writing_supporting_domains: Mapping[WritingSupportingDomain, Optional[DomainOutcome]] = field(default_factory=dict)
    finalized: bool = False
    rationale: Tuple[str, ...] = ()
    source_reviewer_ids: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewQueueEntry:
    paper_id: str
    status: str
    required_reviewer_count: int
    completed_scientific_reviewer_ids: Tuple[str, ...] = ()
    completed_writing_reviewer_ids: Tuple[str, ...] = ()
    pending_scientific_reviewer_ids: Tuple[str, ...] = ()
    pending_writing_reviewer_ids: Tuple[str, ...] = ()
    disagreement_fields: Tuple[str, ...] = ()
    has_final_adjudication: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class PaperReviewProgressSummary:
    total_papers: int
    required_reviewer_count: int
    scientific_review_slots_total: int
    scientific_review_slots_completed: int
    writing_review_slots_total: int
    writing_review_slots_completed: int
    queue_status_counts: Mapping[str, int] = field(default_factory=dict)
    finalized_adjudications: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class AdjudicatedPaperReviewRecord:
    batch_id: str
    paper_id: str
    scientific_review: ScientificReview
    writing_review: WritingReview
    final_study_class: Optional[StudyClass] = None
    final_claim_mode: Optional[ClaimMode] = None
    final_modality_overlays: Tuple[ModalityOverlay, ...] = ()
    adjudicator_id: Optional[str] = None
    finalized: bool = False
    rationale: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class UnitQualificationDecision:
    release_tier: ReleaseTier
    gold_eligible: bool
    reasons: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class BenchmarkUnitDecisionRecord:
    benchmark_unit_id: str
    release_tier: ReleaseTier
    gold_eligible: bool
    reasons: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class TaskBundle:
    task_bundle_id: str
    benchmark_unit_id: str
    task_family: TaskFamily
    release_tier: ReleaseTier
    study_class: StudyClass
    claim_mode: ClaimMode
    input_artifacts: Mapping[str, Any] = field(default_factory=dict)
    authoring_constraints: Mapping[str, Any] = field(default_factory=dict)
    truth_manifest_id: str = ""
    provenance_manifest_id: Optional[str] = None
    scoring_profile: Mapping[str, Any] = field(default_factory=dict)
    paper_id: Optional[str] = None
    evidence_unit_ids: Tuple[str, ...] = ()
    holdout_bucket: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class TaskBundleInventoryReport:
    generated_at: str
    total_bundles: int
    task_family_counts: Mapping[str, int] = field(default_factory=dict)
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    release_tier_counts: Mapping[str, int] = field(default_factory=dict)
    holdout_bucket_counts: Mapping[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class JudgeCandidateSelectionReport:
    generated_at: str
    target_total: int
    selected_total: int
    task_family_counts: Mapping[str, int] = field(default_factory=dict)
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    release_tier_counts: Mapping[str, int] = field(default_factory=dict)
    holdout_bucket_counts: Mapping[str, int] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ShadowInspectionEntry:
    inspection_id: str
    task_bundle_id: str
    benchmark_unit_id: str
    paper_id: str
    title: str
    publication_year: Optional[int]
    task_family: TaskFamily
    study_class: StudyClass
    claim_mode: ClaimMode
    release_tier: ReleaseTier
    holdout_bucket: str
    writing: PaperWritingQualification
    confidence: AutoReviewConfidence
    bundle_completeness: AutoReviewBundleCompleteness
    modality_overlays: Tuple[ModalityOverlay, ...] = ()
    focus_tags: Tuple[str, ...] = ()
    evidence_snapshot: Mapping[str, int] = field(default_factory=dict)
    qualification_reasons: Tuple[str, ...] = ()
    source_bundle_notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ShadowInspectionBatchReport:
    generated_at: str
    target_total: int
    selected_total: int
    task_family_counts: Mapping[str, int] = field(default_factory=dict)
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    writing_counts: Mapping[str, int] = field(default_factory=dict)
    confidence_counts: Mapping[str, int] = field(default_factory=dict)
    completeness_counts: Mapping[str, int] = field(default_factory=dict)
    holdout_bucket_counts: Mapping[str, int] = field(default_factory=dict)
    focus_tag_counts: Mapping[str, int] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ShadowInspectionTaxonomyCategory:
    category_id: str
    label: str
    priority: str
    entry_count: int
    task_family_counts: Mapping[str, int] = field(default_factory=dict)
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    writing_counts: Mapping[str, int] = field(default_factory=dict)
    confidence_counts: Mapping[str, int] = field(default_factory=dict)
    focus_tag_counts: Mapping[str, int] = field(default_factory=dict)
    representative_inspection_ids: Tuple[str, ...] = ()
    representative_task_bundle_ids: Tuple[str, ...] = ()
    recommended_actions: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ShadowInspectionTaxonomyReport:
    generated_at: str
    total_entries: int
    category_count: int
    priority_counts: Mapping[str, int] = field(default_factory=dict)
    categories: Tuple[ShadowInspectionTaxonomyCategory, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ShadowInspectionDeltaReport:
    generated_at: str
    previous_label: str
    current_label: str
    previous_selected_total: int
    current_selected_total: int
    confidence_count_delta: Mapping[str, int] = field(default_factory=dict)
    writing_count_delta: Mapping[str, int] = field(default_factory=dict)
    focus_tag_delta: Mapping[str, int] = field(default_factory=dict)
    taxonomy_category_entry_delta: Mapping[str, int] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ReleaseArtifactChecksum:
    artifact_name: str
    sha256: str
    size_bytes: int
    line_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ReleaseProvenanceManifest:
    release_bundle_id: str
    generated_at: str
    bundle_version: str = "release-bundle-v1"
    units_fingerprint_sha256: str = ""
    decisions_fingerprint_sha256: str = ""
    input_record_counts: Mapping[str, int] = field(default_factory=dict)
    included_benchmark_unit_ids: Tuple[str, ...] = ()
    excluded_benchmark_unit_ids: Tuple[str, ...] = ()
    holdout_policy: Mapping[str, object] = field(default_factory=dict)
    canary_policy: Mapping[str, object] = field(default_factory=dict)
    split_safety_policy: Mapping[str, object] = field(default_factory=dict)
    holdout_counts: Mapping[str, int] = field(default_factory=dict)
    tier_counts: Mapping[str, int] = field(default_factory=dict)
    benchmark_split_counts: Mapping[str, int] = field(default_factory=dict)
    split_safety_violation_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class BundleVerificationReport:
    bundle_dir: str
    release_bundle_id: Optional[str]
    ok: bool
    verified_artifacts: Tuple[str, ...] = ()
    missing_artifacts: Tuple[str, ...] = ()
    checksum_mismatches: Tuple[str, ...] = ()
    summary_consistent: bool = False
    provenance_consistent: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class BaselineRunSpec:
    baseline_id: str
    baseline_kind: BaselineKind
    task_bundle_ids: Tuple[str, ...] = ()
    config_fingerprint_sha256: str = ""
    replay_verified: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class SubmissionRecord:
    submission_id: str
    task_bundle_id: str
    source: str
    producer_id: str
    output_text: str
    config_fingerprint_sha256: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class EvaluationRecord:
    evaluation_id: str
    submission_id: str
    task_bundle_id: str
    evaluation_layers: Tuple[EvaluationLayer, ...] = ()
    deterministic_checks_passed: bool = False
    scores: Mapping[str, float] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class JudgeValidationUnit:
    validation_unit_id: str
    task_bundle_id: str
    human_adjudicated: bool
    rubric_labels: Mapping[str, Any] = field(default_factory=dict)
    frozen: bool = False
    rubric_version: str = "judge-rubric-v1"
    adjudicator_id: Optional[str] = None
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class JudgeSliceAuditReport:
    generated_at: str
    total_units: int
    human_adjudicated_units: int
    frozen_units: int
    ready_units: int
    linked_task_bundles: int
    task_family_counts: Mapping[str, int] = field(default_factory=dict)
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    release_tier_counts: Mapping[str, int] = field(default_factory=dict)
    missing_task_bundle_ids: Tuple[str, ...] = ()
    duplicate_validation_unit_ids: Tuple[str, ...] = ()
    duplicate_task_bundle_ids: Tuple[str, ...] = ()
    missing_rubric_axes: Mapping[str, Tuple[str, ...]] = field(default_factory=dict)
    issues: Tuple[str, ...] = ()
    ok: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class JudgeReviewForm:
    validation_unit_id: str
    reviewer_id: str
    completed: bool = False
    rubric_labels: Mapping[str, Any] = field(default_factory=dict)
    confidence: Optional[int] = None
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class JudgeAdjudicationRecord:
    validation_unit_id: str
    adjudicator_id: str
    final_rubric_labels: Mapping[str, Any] = field(default_factory=dict)
    finalized: bool = False
    rationale: Tuple[str, ...] = ()
    source_reviewer_ids: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class JudgeAdjudicationQueueEntry:
    validation_unit_id: str
    status: str
    required_reviewer_count: int
    completed_reviewer_ids: Tuple[str, ...] = ()
    pending_reviewer_ids: Tuple[str, ...] = ()
    disagreement_axes: Tuple[str, ...] = ()
    has_final_adjudication: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class MaintenanceLogEntry:
    entry_id: str
    created_at: str
    phase: str
    summary: str
    release_bundle_id: Optional[str] = None
    artifacts: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ProgramProgressReport:
    generated_at: str
    source_candidates: int
    paper_qualified: int
    task_bundles_total: int
    public_units: int
    private_units: int
    hybrid_overlay_units: int = 0
    controlled_access_qualified_papers: int = 0
    judge_validation_units: int = 0
    replayable_baselines: int = 0
    study_class_counts: Mapping[str, int] = field(default_factory=dict)
    task_family_counts: Mapping[str, int] = field(default_factory=dict)
    claim_mode_counts: Mapping[str, int] = field(default_factory=dict)
    v1_core_gate_passed: bool = False
    leaderboard_gate_passed: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ExecutionProfile:
    profile_id: str
    profile_name: str
    backend: str
    root_path: str
    repo_root: str
    working_directory: str
    python_bin: str = "python3"
    launch_prefix: Tuple[str, ...] = ()
    environment_exports: Mapping[str, str] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class ExecutionJobSpec:
    job_id: str
    job_name: str
    profile_id: str
    job_kind: str
    backend: str
    working_directory: str
    command_sequence: Tuple[str, ...] = ()
    environment_exports: Mapping[str, str] = field(default_factory=dict)
    output_artifacts: Mapping[str, str] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass(frozen=True)
class SplitSafetyViolation:
    violation_type: SplitSafetyViolationType
    lineage_type: str
    lineage_value: str
    benchmark_unit_ids: Tuple[str, ...]
    conflicting_splits: Tuple[str, ...] = ()
    observed_count: int = 0
    max_allowed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)
