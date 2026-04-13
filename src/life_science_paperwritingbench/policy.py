from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class PaperScientificQualification(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    Q = "Q"


class PaperPackagingQualification(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class PaperWritingQualification(StrEnum):
    W1 = "W1"
    W2 = "W2"
    W3 = "W3"


class ReleaseTier(StrEnum):
    PUBLIC_GOLD = "public_gold"
    SHADOW_GOLD = "shadow_gold"
    STRESS_ONLY = "stress_only"
    EXCLUDED = "excluded"


class CandidateTier(StrEnum):
    PUBLIC_GOLD_CANDIDATE = "public_gold_candidate"
    SHADOW_CANDIDATE = "shadow_candidate"
    STRESS_CANDIDATE = "stress_candidate"
    EXCLUDED = "excluded"


class AutoReviewBundleCompleteness(StrEnum):
    METADATA_ONLY = "metadata_only"
    PARTIAL = "partial"
    REVIEW_READY = "review_ready"


class AutoReviewRole(StrEnum):
    SCIENTIFIC_REVIEWER = "scientific_reviewer"
    WRITING_REVIEWER = "writing_reviewer"
    EVIDENCE_SKEPTIC = "evidence_skeptic"


class AutoReviewConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"


class IntegrityDisposition(StrEnum):
    CLEAR = "clear"
    QUARANTINE = "quarantine"
    EXCLUDED = "excluded"


class SplitSafetyViolationType(StrEnum):
    CROSS_SPLIT_LEAKAGE = "cross_split_leakage"
    LINEAGE_DOMINANCE = "lineage_dominance"


class DomainOutcome(StrEnum):
    PASS = "pass"
    BORDERLINE = "borderline"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


class PublicationStatus(StrEnum):
    PUBLISHED = "published"
    PREPRINT = "preprint"
    RETRACTED = "retracted"
    WITHDRAWN = "withdrawn"
    REMOVED = "removed"
    UNKNOWN = "unknown"


class StudyClass(StrEnum):
    HUMAN_INTERVENTIONAL = "human_interventional"
    HUMAN_OBSERVATIONAL = "human_observational"
    SYSTEMATIC_REVIEW_META_ANALYSIS = "systematic_review_meta_analysis"
    ANIMAL_PRECLINICAL = "animal_preclinical"
    MECHANISTIC_EXPERIMENTAL = "mechanistic_experimental"
    METHODS_RESOURCE = "methods_resource"


class ModalityOverlay(StrEnum):
    BIOMARKER_PROGNOSTIC = "biomarker_prognostic"
    OMICS_TRANSCRIPTOMICS = "omics_transcriptomics"
    SEQUENCE_METAGENOMICS = "sequence_metagenomics"
    PROTEOMICS_MASSSPEC = "proteomics_massspec"
    STRUCTURAL_BIOPHYSICS = "structural_biophysics"
    ECOLOGY_BIODIVERSITY = "ecology_biodiversity"
    QPCR = "qPCR"
    ENZYMOLOGY = "enzymology"


class ClaimMode(StrEnum):
    CONFIRMATORY = "confirmatory"
    EXPLORATORY = "exploratory"
    DESCRIPTIVE = "descriptive"
    RESOURCE_RELEASE = "resource_release"
    NEGATIVE_RESULT = "negative_result"


class EvidenceUnitType(StrEnum):
    CLAIM_CLUSTER = "claim_cluster"
    FIGURE_TABLE_RESULT = "figure_table_result"
    METHODS_PROTOCOL_BLOCK = "methods_protocol_block"
    REVIEW_REVISION_BLOCK = "review_revision_block"
    RESOURCE_DESCRIPTION_BLOCK = "resource_description_block"


class TaskFamily(StrEnum):
    RESULTS_TO_TEXT = "results_to_text"
    METHODS_TO_TEXT = "methods_to_text"
    ABSTRACT_FROM_EVIDENCE = "abstract_from_evidence"
    REVIEW_REVISION_RESPONSE = "review_revision_response"
    LITERATURE_QA = "literature_qa"
    TRIAL_QA = "trial_qa"
    FIGURE_QA = "figure_qa"
    TABLE_QA = "table_qa"
    SOURCE_QUALITY_QA = "source_quality_qa"


class ObservationType(StrEnum):
    LITERATURE_STATEMENT = "literature_statement"
    FIGURE_OBSERVATION = "figure_observation"
    TABLE_OBSERVATION = "table_observation"
    METHODS_OBSERVATION = "methods_observation"
    TRIAL_OBSERVATION = "trial_observation"
    REVIEW_OBSERVATION = "review_observation"
    RESOURCE_OBSERVATION = "resource_observation"
    SOURCE_QUALITY_SIGNAL = "source_quality_signal"


class AnswerFormat(StrEnum):
    FREE_TEXT = "free_text"
    EXTRACTIVE = "extractive"
    LIST = "list"


class SourceQualitySeverity(StrEnum):
    MAJOR = "major"
    MINOR = "minor"
    OPTIONAL = "optional"


class SourceQualityConcernType(StrEnum):
    DESIGN_FLAW = "design_flaw"
    STATISTICAL_METHODOLOGY = "statistical_methodology"
    MISSING_EXPERIMENT = "missing_experiment"
    PRIOR_ART_NOVELTY = "prior_art_novelty"
    WRITING_CLARITY = "writing_clarity"
    REAGENT_METHOD_SPECIFICITY = "reagent_method_specificity"
    INTERPRETATION = "interpretation"
    OTHER = "other"


class BaselineKind(StrEnum):
    REFERENCE_TEMPLATE = "reference_template"
    RETRIEVAL_WRITER = "retrieval_writer"
    SECTION_WISE_PIPELINE = "section_wise_pipeline"
    SINGLE_AGENT_WRITER = "single_agent_manuscript_writer"
    MULTI_AGENT_ORCHESTRATION = "multi_agent_orchestration_writer"


class EvaluationLayer(StrEnum):
    DETERMINISTIC_CHECKS = "deterministic_checks"
    RUBRIC_SCORING = "rubric_scoring"


class ScientificCriticalDomain(StrEnum):
    INTEGRITY_STATUS = "integrity_status"
    DESIGN_ANALYSIS_CREDIBILITY = "design_analysis_credibility"
    MINIMAL_INTERPRETABLE_CORE = "minimal_interpretable_core"
    REQUIRED_TRACEABILITY = "required_traceability"
    CLAIM_MODE_ALIGNMENT = "claim_mode_alignment"


class ScientificSupportingDomain(StrEnum):
    REPRODUCIBILITY_SUPPORT = "reproducibility_support"
    RESOURCE_SPECIFICITY = "resource_specificity"


class WritingCriticalDomain(StrEnum):
    ABSTRACT_RESULT_ALIGNMENT = "abstract_result_alignment"
    NARRATIVE_COHERENCE = "narrative_coherence"
    METHODS_CLARITY = "methods_clarity"
    FIGURE_TABLE_GROUNDING = "figure_table_grounding"
    LIMITATION_UNCERTAINTY_DISCLOSURE = "limitation_uncertainty_disclosure"


class WritingSupportingDomain(StrEnum):
    TITLE_SCOPE_ALIGNMENT = "title_scope_alignment"
    CITATION_CONTEXTUALIZATION = "citation_contextualization"


class AuditEvidenceDomain(StrEnum):
    EDITORIAL_REVIEW_SIGNAL = "editorial_review_signal"
    COMMUNITY_INTEGRITY_SIGNAL = "community_integrity_signal"
    POST_PUBLICATION_DISCUSSION_SIGNAL = "post_publication_discussion_signal"


class PackagingDomain(StrEnum):
    RELEASEABILITY = "releaseability"
    EVIDENCE_PACK_RECONSTRUCTABILITY = "evidence_pack_reconstructability"
    ARTIFACT_ACCESS = "artifact_access"
    PROVENANCE_COMPLETENESS = "provenance_completeness"
    SPLIT_SAFETY = "split_safety"


class CrossmarkUpdateType(StrEnum):
    CORRECTION = "correction"
    RETRACTION = "retraction"
    WITHDRAWAL = "withdrawal"
    REMOVAL = "removal"
    PARTIAL_RETRACTION = "partial_retraction"
    EXPRESSION_OF_CONCERN = "expression_of_concern"


class IntegrityFlag(StrEnum):
    PAPER_MILL_PATTERN = "paper_mill_pattern"
    MANIPULATION_ALLEGATION = "manipulation_allegation"
    IMAGE_REUSE_PATTERN = "image_reuse_pattern"
    MAJOR_CORRECTION_INTERPRETATION = "major_correction_interpretation"


class SafeDerivedArtifact(StrEnum):
    PUBLISHED_AGGREGATE_STATISTICS = "published_aggregate_statistics"
    PUBLISHED_FIGURE_TABLE_OBSERVATIONS = "published_figure_table_observations"
    DEIDENTIFIED_METHOD_SUMMARIES = "deidentified_method_summaries"
    CITATION_METADATA = "citation_metadata"
    ACCESSION_METADATA = "accession_metadata"


class StandardId(StrEnum):
    MDAR = "MDAR"
    CONSORT_2025 = "CONSORT_2025"
    STROBE = "STROBE"
    PRISMA_2020 = "PRISMA_2020"
    AMSTAR_2 = "AMSTAR_2"
    ARRIVE_2_0 = "ARRIVE_2_0"
    REUSE_TRACEABILITY = "REUSE_TRACEABILITY"
    REMARK = "REMARK"
    MIAME_MINSEQE = "MIAME_MINSEQE"
    MIXS_MIMARKS = "MIxS_MIMARKS"
    MIAPE_PROTEOMEXCHANGE = "MIAPE_PROTEOMEXCHANGE"
    WWPDB_TRACEABILITY = "wwPDB_EMDB_BMRB"
    EML_DARWIN_CORE = "EML_DARWIN_CORE"
    MIQE_2_0 = "MIQE_2_0"
    STRENDA = "STRENDA"


CRITICAL_SCIENTIFIC_DOMAINS = (
    ScientificCriticalDomain.INTEGRITY_STATUS,
    ScientificCriticalDomain.DESIGN_ANALYSIS_CREDIBILITY,
    ScientificCriticalDomain.MINIMAL_INTERPRETABLE_CORE,
    ScientificCriticalDomain.REQUIRED_TRACEABILITY,
    ScientificCriticalDomain.CLAIM_MODE_ALIGNMENT,
)

SUPPORTING_SCIENTIFIC_DOMAINS = (
    ScientificSupportingDomain.REPRODUCIBILITY_SUPPORT,
    ScientificSupportingDomain.RESOURCE_SPECIFICITY,
)

CRITICAL_WRITING_DOMAINS = (
    WritingCriticalDomain.ABSTRACT_RESULT_ALIGNMENT,
    WritingCriticalDomain.NARRATIVE_COHERENCE,
    WritingCriticalDomain.METHODS_CLARITY,
    WritingCriticalDomain.FIGURE_TABLE_GROUNDING,
    WritingCriticalDomain.LIMITATION_UNCERTAINTY_DISCLOSURE,
)

SUPPORTING_WRITING_DOMAINS = (
    WritingSupportingDomain.TITLE_SCOPE_ALIGNMENT,
    WritingSupportingDomain.CITATION_CONTEXTUALIZATION,
)

PACKAGING_DOMAINS = (
    PackagingDomain.RELEASEABILITY,
    PackagingDomain.EVIDENCE_PACK_RECONSTRUCTABILITY,
    PackagingDomain.ARTIFACT_ACCESS,
    PackagingDomain.PROVENANCE_COMPLETENESS,
    PackagingDomain.SPLIT_SAFETY,
)

PRIMARY_CLASS_REQUIRED_STANDARDS = {
    StudyClass.HUMAN_INTERVENTIONAL: (
        StandardId.CONSORT_2025,
        StandardId.MDAR,
    ),
    StudyClass.HUMAN_OBSERVATIONAL: (
        StandardId.STROBE,
        StandardId.MDAR,
    ),
    StudyClass.SYSTEMATIC_REVIEW_META_ANALYSIS: (
        StandardId.PRISMA_2020,
        StandardId.AMSTAR_2,
    ),
    StudyClass.ANIMAL_PRECLINICAL: (
        StandardId.ARRIVE_2_0,
        StandardId.MDAR,
    ),
    StudyClass.MECHANISTIC_EXPERIMENTAL: (StandardId.MDAR,),
    StudyClass.METHODS_RESOURCE: (
        StandardId.MDAR,
        StandardId.REUSE_TRACEABILITY,
    ),
}

OVERLAY_REQUIRED_STANDARDS = {
    ModalityOverlay.BIOMARKER_PROGNOSTIC: (StandardId.REMARK,),
    ModalityOverlay.OMICS_TRANSCRIPTOMICS: (StandardId.MIAME_MINSEQE,),
    ModalityOverlay.SEQUENCE_METAGENOMICS: (StandardId.MIXS_MIMARKS,),
    ModalityOverlay.PROTEOMICS_MASSSPEC: (StandardId.MIAPE_PROTEOMEXCHANGE,),
    ModalityOverlay.STRUCTURAL_BIOPHYSICS: (StandardId.WWPDB_TRACEABILITY,),
    ModalityOverlay.ECOLOGY_BIODIVERSITY: (StandardId.EML_DARWIN_CORE,),
    ModalityOverlay.QPCR: (StandardId.MIQE_2_0,),
    ModalityOverlay.ENZYMOLOGY: (StandardId.STRENDA,),
}

PUBLIC_GOLD_START_YEAR = 2018
DEFAULT_PUBLIC_HOLDOUT_RATIO = 0.8
DEFAULT_PRIVATE_HOLDOUT_RATIO = 0.2
DEFAULT_CANARY_PREFIX = "LS-PWB-CANARY"


@dataclass(frozen=True)
class PackagingPolicy:
    """Controls release constraints for benchmark-ready artifacts."""

    small_cell_release_threshold: int = 11
    allowed_safe_artifacts: FrozenSet[SafeDerivedArtifact] = field(
        default_factory=lambda: frozenset(
            {
                SafeDerivedArtifact.PUBLISHED_AGGREGATE_STATISTICS,
                SafeDerivedArtifact.PUBLISHED_FIGURE_TABLE_OBSERVATIONS,
                SafeDerivedArtifact.DEIDENTIFIED_METHOD_SUMMARIES,
                SafeDerivedArtifact.CITATION_METADATA,
                SafeDerivedArtifact.ACCESSION_METADATA,
            }
        )
    )
    min_safe_artifacts_for_controlled_access: int = 1


@dataclass(frozen=True)
class SplitSafetyPolicy:
    max_units_per_lineage: int = 3
    lineage_types: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {
                "source_family",
                "consortium_lineage",
                "dataset_lineage",
                "lab_lineage",
            }
        )
    )
