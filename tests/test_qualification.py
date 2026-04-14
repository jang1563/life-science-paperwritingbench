import os
import sys
import tempfile
import unittest
import json
import hashlib
import urllib.error
from pathlib import Path


ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


from life_science_paperwritingbench import (  # noqa: E402
    AgreementMetric,
    adjudication_queue_entry_from_dict,
    adjudicated_paper_review_record_from_dict,
    AdjudicatedPaperReviewRecord,
    aggregate_auto_paper_reviews,
    annotate_task_bundles_with_release_index,
    audit_auto_review_evidence_enrichments,
    audit_auto_review_source_bundles,
    AutoAggregatedPaperReviewRecord,
    AutoReviewEvidenceEnrichmentRecord,
    auto_aggregated_paper_review_record_from_dict,
    AutoPanelVote,
    auto_panel_vote_from_dict,
    AutoQualificationRecord,
    auto_qualification_record_from_dict,
    AutoReviewBatchReport,
    auto_review_batch_report_from_dict,
    AutoReviewRecoveryBatchEntry,
    auto_review_recovery_batch_entry_from_dict,
    auto_review_recovery_batch_report_from_dict,
    AutoReviewBundleCompleteness,
    AutoReviewConfidence,
    AutoReviewRole,
    AutoReviewSourceBundle,
    auto_review_source_bundle_audit_report_from_dict,
    auto_review_source_bundle_from_dict,
    BaselineKind,
    BaselineRunSpec,
    BenchmarkUnitDecisionRecord,
    BenchmarkUnit,
    benchmark_unit_decision_record_from_dict,
    build_adjudication_queue,
    build_baseline_replay_job_spec,
    build_cayuga_execution_profile,
    build_collection_batch,
    build_auto_paper_qualification_records,
    build_auto_review_recovery_batch,
    build_auto_review_recovery_batch_report,
    build_auto_review_recovery_job_spec,
    build_auto_review_evidence_enrichments,
    build_auto_review_source_bundles,
    build_benchmark_unit_decisions_from_auto_qualifications,
    build_benchmark_units_from_evidence_units,
    build_judge_adjudication_queue,
    build_judge_adjudication_shells,
    build_judge_review_forms,
    build_judge_validation_slice,
    build_packaging_review_priors,
    build_paper_qualification_batch_report,
    build_paper_qualification_records,
    build_paper_review_packet_report,
    build_paper_review_packets,
    build_evaluation_extraction_artifacts,
    build_evaluation_task_bundles,
    build_extraction_records,
    build_full_calibration_scaffold,
    build_paper_review_adjudication_shells,
    build_parser_assisted_extraction_drafts,
    build_paper_review_queue,
    build_paper_reviewer_assignments,
    build_paper_reviewer_handoff_report,
    build_paper_review_workload_report,
    CandidateTier,
    CalibrationDriftReport,
    ClaimMode,
    CrossmarkUpdateType,
    DomainOutcome,
    EvaluationLayer,
    EvaluationExtractionAuditReport,
    EvidenceUnit,
    EvidenceUnitType,
    ExecutionJobSpec,
    ExecutionProfile,
    ExtractionAuditReport,
    IngestionAuditReport,
    IngestionRecord,
    IntegrityDisposition,
    JudgeValidationUnit,
    LineageInfo,
    MetadataSourceRecord,
    ModalityOverlay,
    PackagingDomain,
    PackagingReview,
    PaperPackagingQualification,
    PaperPackagingReviewRecord,
    PaperQualificationBatchReport,
    PaperQualificationRecord,
    PaperReviewAdjudicationRecord,
    PaperReviewBatchEntry,
    PaperReviewBatchReport,
    PaperReviewPacket,
    PaperReviewPacketReport,
    PaperReviewProgressSummary,
    PaperReviewQueueEntry,
    PaperReviewerHandoffReport,
    PaperReviewerAssignment,
    PaperReviewWorkloadReport,
    PaperQualificationDecision,
    PaperScientificReviewForm,
    PaperScientificQualification,
    PaperWritingQualification,
    PaperWritingReviewForm,
    PilotAdjudicationRecord,
    PilotAgreementSummary,
    PilotCalibrationSpec,
    PilotReviewForm,
    PublicationStatus,
    PUBLIC_HOLDOUT_BUCKET,
    QuestionRecord,
    ReleaseTier,
    ReleaseIndexEntry,
    SafeDerivedArtifact,
    ScientificCriticalDomain,
    ScientificReview,
    ShadowInspectionEntry,
    ShadowInspectionTaxonomyReport,
    ScientificSupportingDomain,
    SourceQualityRecord,
    SourcePaper,
    SplitSafetyPolicy,
    SplitSafetyViolationType,
    StandardId,
    StudyClass,
    TaskFamily,
    TaskBundle,
    TruthManifest,
    assign_holdout_bucket,
    build_maintenance_log_entry,
    build_pilot_adjudication_shells,
    build_pilot_review_forms,
    build_release_manifest_bundle,
    build_release_index,
    build_shadow_inspection_batch,
    build_shadow_inspection_taxonomy,
    compare_shadow_inspection_reports,
    build_task_bundle,
    build_task_bundles,
    build_truth_manifest_from_extractions,
    build_truth_manifest_bundle,
    collection_batch_spec_from_dict,
    collection_candidate_record_from_dict,
    audit_ingestion_artifacts,
    audit_collection_batch,
    audit_calibration_drift,
    audit_judge_validation_slice,
    answer_record_from_dict,
    compute_agreement_against_adjudication,
    evaluation_extraction_audit_report_from_dict,
    extraction_audit_report_from_dict,
    evaluate_submissions,
    evidence_unit_from_dict,
    execution_job_spec_from_dict,
    fetch_pubmed_batch,
    freeze_truth_manifest,
    generate_canary_string,
    ingest_metadata_records,
    initialize_knowledge_base_layout,
    judge_adjudication_queue_entry_from_dict,
    judge_adjudication_record_from_dict,
    judge_review_form_from_dict,
    judge_slice_audit_report_from_dict,
    judge_validation_unit_from_dict,
    judge_validation_unit_ready,
    load_jsonl,
    merge_collection_candidates,
    merge_judge_review_forms,
    merge_paper_scientific_review_forms,
    merge_paper_writing_review_forms,
    merge_review_forms,
    materialize_enriched_source_papers,
    metadata_source_record_from_dict,
    metadata_governance_hint_from_dict,
    observation_record_from_dict,
    normalize_metadata_records,
    paper_packaging_review_record_from_dict,
    paper_qualification_batch_report_from_dict,
    paper_qualification_record_from_dict,
    paper_review_batch_entry_from_dict,
    paper_review_adjudication_record_from_dict,
    paper_review_batch_report_from_dict,
    paper_review_packet_from_dict,
    paper_review_progress_summary_from_dict,
    paper_review_queue_entry_from_dict,
    paper_reviewer_assignment_from_dict,
    paper_reviewer_handoff_report_from_dict,
    paper_scientific_review_form_from_dict,
    paper_writing_review_form_from_dict,
    parser_assisted_extraction_report_from_dict,
    pilot_adjudication_record_from_dict,
    pilot_calibration_spec_from_dict,
    pilot_coverage_summary,
    pilot_review_form_from_dict,
    question_record_from_dict,
    qualify_paper,
    qualify_unit,
    qualify_writing,
    rank_collection_candidates,
    render_baseline_output,
    render_execution_job_script,
    render_shadow_inspection_markdown,
    render_shadow_inspection_taxonomy_markdown,
    release_artifact_checksum_from_dict,
    release_provenance_manifest_from_dict,
    render_release_bundle_artifacts,
    required_standards_for_paper,
    run_baseline,
    run_auto_paper_reviews,
    shortlist_collection_candidates,
    summarize_program_progress,
    suggest_governance_metadata_hints,
    source_paper_from_dict,
    source_quality_record_from_dict,
    select_judge_candidate_task_bundles,
    select_recovery_batch_packaging_reviews,
    select_recovery_batch_papers,
    build_paper_review_batch_entries,
    build_paper_review_batch_report,
    build_paper_scientific_review_forms,
    build_paper_writing_review_forms,
    summarize_judge_candidate_selection,
    summarize_auto_review_batch,
    summarize_shadow_inspection_batch,
    summarize_shadow_inspection_taxonomy,
    summarize_paper_review_progress,
    summarize_task_bundles,
    task_bundle_from_dict,
    task_family_for_evidence_unit_type,
    truth_manifest_from_dict,
    truth_manifest_verification_report_from_dict,
    UnitQualificationDecision,
    validate_pilot_agreement_thresholds,
    validate_full_calibration_set,
    validate_pilot_calibration_set,
    validate_split_safety,
    verify_ingestion_artifacts,
    verify_truth_manifest,
    verify_release_bundle_directory,
    WritingCriticalDomain,
    WritingReview,
    WritingSupportingDomain,
    write_jsonl,
    finalize_paper_adjudications,
    finalize_judge_validation_units,
    enrich_candidates_with_crossref,
    enrich_candidates_with_europepmc,
    api_fetch_record_from_dict,
    auto_review_evidence_enrichment_record_from_dict,
)
from life_science_paperwritingbench.cli import main as cli_main  # noqa: E402


def make_source_paper(**overrides):
    base = dict(
        paper_id="PMID:1",
        title="Example",
        publication_year=2024,
        publication_status=PublicationStatus.PUBLISHED,
        peer_reviewed=True,
        study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
        claim_mode=ClaimMode.EXPLORATORY,
    )
    base.update(overrides)
    return SourcePaper(**base)


def make_scientific_review(**overrides):
    critical = {
        ScientificCriticalDomain.INTEGRITY_STATUS: DomainOutcome.PASS,
        ScientificCriticalDomain.DESIGN_ANALYSIS_CREDIBILITY: DomainOutcome.PASS,
        ScientificCriticalDomain.MINIMAL_INTERPRETABLE_CORE: DomainOutcome.PASS,
        ScientificCriticalDomain.REQUIRED_TRACEABILITY: DomainOutcome.PASS,
        ScientificCriticalDomain.CLAIM_MODE_ALIGNMENT: DomainOutcome.PASS,
    }
    supporting = {
        ScientificSupportingDomain.REPRODUCIBILITY_SUPPORT: DomainOutcome.PASS,
        ScientificSupportingDomain.RESOURCE_SPECIFICITY: DomainOutcome.PASS,
    }
    critical.update(overrides.get("critical_domains", {}))
    supporting.update(overrides.get("supporting_domains", {}))
    applied_standards = overrides.get("applied_standards")
    standard_outcomes = overrides.get("standard_outcomes")
    if applied_standards is None or standard_outcomes is None:
        required = overrides.get("required_standards", (StandardId.MDAR,))
        applied_standards = applied_standards if applied_standards is not None else required
        standard_outcomes = (
            standard_outcomes
            if standard_outcomes is not None
            else {standard: DomainOutcome.PASS for standard in required}
        )
    return ScientificReview(
        critical_domains=critical,
        supporting_domains=supporting,
        applied_standards=tuple(applied_standards),
        standard_outcomes=standard_outcomes,
        standard_notes=overrides.get("standard_notes", {}),
    )


def make_full_calibration_specs():
    return list(build_full_calibration_scaffold())


def make_packaging_review(**overrides):
    domains = {
        PackagingDomain.RELEASEABILITY: DomainOutcome.PASS,
        PackagingDomain.EVIDENCE_PACK_RECONSTRUCTABILITY: DomainOutcome.PASS,
        PackagingDomain.ARTIFACT_ACCESS: DomainOutcome.PASS,
        PackagingDomain.PROVENANCE_COMPLETENESS: DomainOutcome.PASS,
        PackagingDomain.SPLIT_SAFETY: DomainOutcome.PASS,
    }
    domains.update(overrides.get("domain_outcomes", {}))
    payload = dict(
        domain_outcomes=domains,
        safe_derived_artifacts=overrides.get("safe_derived_artifacts", ()),
        artifact_inventory_id=overrides.get("artifact_inventory_id"),
        restricted_artifact_types=overrides.get("restricted_artifact_types", ()),
        contains_private_row_level_data=overrides.get("contains_private_row_level_data", False),
        contains_recomputed_sensitive_aggregates=overrides.get("contains_recomputed_sensitive_aggregates", False),
        redistributes_restricted_supplements=overrides.get("redistributes_restricted_supplements", False),
        controlled_access_rule_satisfied=overrides.get("controlled_access_rule_satisfied", True),
    )
    return PackagingReview(**payload)


def make_writing_review(**overrides):
    critical = {
        WritingCriticalDomain.ABSTRACT_RESULT_ALIGNMENT: DomainOutcome.PASS,
        WritingCriticalDomain.NARRATIVE_COHERENCE: DomainOutcome.PASS,
        WritingCriticalDomain.METHODS_CLARITY: DomainOutcome.PASS,
        WritingCriticalDomain.FIGURE_TABLE_GROUNDING: DomainOutcome.PASS,
        WritingCriticalDomain.LIMITATION_UNCERTAINTY_DISCLOSURE: DomainOutcome.PASS,
    }
    supporting = {
        WritingSupportingDomain.TITLE_SCOPE_ALIGNMENT: DomainOutcome.PASS,
        WritingSupportingDomain.CITATION_CONTEXTUALIZATION: DomainOutcome.PASS,
    }
    critical.update(overrides.get("critical_domains", {}))
    supporting.update(overrides.get("supporting_domains", {}))
    return WritingReview(
        critical_domains=critical,
        supporting_domains=supporting,
        notes=tuple(overrides.get("notes", ())),
    )


def make_truth_manifest(paper, **overrides):
    base = dict(
        manifest_id="TM:1",
        paper_id=paper.paper_id,
        assertion_ids=("A1",),
        assertion_texts=("Claim 1",),
        evidence_items=("fig1",),
        evidence_types=("figure_panel",),
        applied_standards=required_standards_for_paper(paper),
        study_class=paper.study_class,
        modality_overlays=paper.modality_overlays,
        frozen=True,
        frozen_at="2026-04-09T21:30:00Z",
    )
    base.update(overrides)
    return TruthManifest(**base)


def make_paper_decision(**overrides):
    payload = dict(
        scientific=PaperScientificQualification.A,
        packaging=PaperPackagingQualification.P1,
        candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
        eligible_for_unit_extraction=True,
        required_standards=(StandardId.MDAR,),
        writing=PaperWritingQualification.W1,
        public_writing_eligible=True,
        missing_standards=(),
        integrity_disposition=IntegrityDisposition.CLEAR,
        reasons=(),
    )
    payload.update(overrides)
    return PaperQualificationDecision(**payload)


def make_task_bundle(index=1, **overrides):
    payload = dict(
        task_bundle_id=f"TB:{index}",
        benchmark_unit_id=f"BU:{index}",
        task_family=TaskFamily.RESULTS_TO_TEXT,
        release_tier=ReleaseTier.PUBLIC_GOLD,
        study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
        claim_mode=ClaimMode.EXPLORATORY,
        truth_manifest_id=f"TM:{index}",
        provenance_manifest_id="PMAN:v1",
        paper_id=f"PMID:{index}",
        evidence_unit_ids=(f"EU:{index}",),
        holdout_bucket="public",
    )
    payload.update(overrides)
    return TaskBundle(**payload)


def make_auto_review_recovery_entry(index=1, **overrides):
    classes = tuple(StudyClass)
    claim_modes = tuple(ClaimMode)
    payload = dict(
        paper_id=f"PMID:{index}",
        title=f"Recovery Paper {index}",
        study_class=classes[(index - 1) % len(classes)],
        claim_mode=claim_modes[(index - 1) % len(claim_modes)],
        priority_bucket="near_shadow_scientific_borderline",
        priority_rank=1,
        candidate_tier=CandidateTier.STRESS_CANDIDATE,
        scientific=PaperScientificQualification.B,
        writing=PaperWritingQualification.W2,
        packaging=PaperPackagingQualification.P1,
        bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
        confidence=AutoReviewConfidence.LOW,
        auto_release_cap_reason="scientific_b",
    )
    payload.update(overrides)
    return AutoReviewRecoveryBatchEntry(**payload)


def make_evidence_unit(paper, **overrides):
    base = dict(
        unit_id="EU:1",
        paper_id=paper.paper_id,
        unit_type=EvidenceUnitType.CLAIM_CLUSTER,
        evidence_pointers=("fig1",),
        locally_supported=True,
        internally_coherent=True,
        depends_on_excluded_narrative=False,
        releasable=True,
    )
    base.update(overrides)
    return EvidenceUnit(**base)


class QualificationTests(unittest.TestCase):
    def test_writing_review_all_pass_yields_w1(self):
        writing, reasons = qualify_writing(make_writing_review())
        self.assertEqual(writing, PaperWritingQualification.W1)
        self.assertEqual(reasons, [])

    def test_writing_review_borderline_yields_w2(self):
        writing, reasons = qualify_writing(
            make_writing_review(
                supporting_domains={
                    WritingSupportingDomain.CITATION_CONTEXTUALIZATION: DomainOutcome.BORDERLINE
                }
            )
        )
        self.assertEqual(writing, PaperWritingQualification.W2)
        self.assertTrue(reasons)

    def test_writing_review_critical_fail_yields_w3(self):
        writing, reasons = qualify_writing(
            make_writing_review(
                critical_domains={
                    WritingCriticalDomain.ABSTRACT_RESULT_ALIGNMENT: DomainOutcome.FAIL
                }
            )
        )
        self.assertEqual(writing, PaperWritingQualification.W3)
        self.assertTrue(reasons)

    def test_public_writing_eligibility_requires_w1(self):
        paper = make_source_paper()
        decision = qualify_paper(
            paper,
            make_scientific_review(),
            make_packaging_review(),
            writing_review=make_writing_review(
                supporting_domains={
                    WritingSupportingDomain.CITATION_CONTEXTUALIZATION: DomainOutcome.BORDERLINE
                }
            ),
        )
        self.assertEqual(decision.candidate_tier, CandidateTier.PUBLIC_GOLD_CANDIDATE)
        self.assertEqual(decision.writing, PaperWritingQualification.W2)
        self.assertFalse(decision.public_writing_eligible)

    def test_retracted_paper_is_always_scientific_c(self):
        paper = make_source_paper(publication_status=PublicationStatus.RETRACTED)
        decision = qualify_paper(paper, make_scientific_review(), make_packaging_review())
        self.assertEqual(decision.scientific, PaperScientificQualification.C)
        self.assertEqual(decision.integrity_disposition, IntegrityDisposition.EXCLUDED)
        self.assertEqual(decision.candidate_tier, CandidateTier.EXCLUDED)

    def test_expression_of_concern_is_quarantine(self):
        paper = make_source_paper(crossmark_updates=(CrossmarkUpdateType.EXPRESSION_OF_CONCERN,))
        decision = qualify_paper(paper, make_scientific_review(), make_packaging_review())
        self.assertEqual(decision.scientific, PaperScientificQualification.Q)
        self.assertEqual(decision.integrity_disposition, IntegrityDisposition.QUARANTINE)
        self.assertEqual(decision.candidate_tier, CandidateTier.EXCLUDED)

    def test_partial_retraction_invalidating_core_claims_is_c(self):
        paper = make_source_paper(
            crossmark_updates=(CrossmarkUpdateType.PARTIAL_RETRACTION,),
            partial_retraction_invalidates_core_claims=True,
        )
        decision = qualify_paper(paper, make_scientific_review(), make_packaging_review())
        self.assertEqual(decision.scientific, PaperScientificQualification.C)
        self.assertEqual(decision.integrity_disposition, IntegrityDisposition.EXCLUDED)

    def test_partial_retraction_without_core_invalidation_is_q(self):
        paper = make_source_paper(
            crossmark_updates=(CrossmarkUpdateType.PARTIAL_RETRACTION,),
            partial_retraction_invalidates_core_claims=False,
        )
        decision = qualify_paper(paper, make_scientific_review(), make_packaging_review())
        self.assertEqual(decision.scientific, PaperScientificQualification.Q)
        self.assertEqual(decision.integrity_disposition, IntegrityDisposition.QUARANTINE)

    def test_preprint_is_shadow_candidate_not_public_candidate(self):
        paper = make_source_paper(publication_status=PublicationStatus.PREPRINT, peer_reviewed=False)
        decision = qualify_paper(paper, make_scientific_review(), make_packaging_review())
        self.assertEqual(decision.candidate_tier, CandidateTier.SHADOW_CANDIDATE)
        self.assertTrue(decision.eligible_for_unit_extraction)

    def test_human_interventional_missing_consort_blocks_a(self):
        paper = make_source_paper(study_class=StudyClass.HUMAN_INTERVENTIONAL)
        review = make_scientific_review(
            required_standards=(StandardId.MDAR,),
            applied_standards=(StandardId.MDAR,),
            standard_outcomes={StandardId.MDAR: DomainOutcome.PASS},
        )
        decision = qualify_paper(paper, review, make_packaging_review())
        self.assertEqual(decision.scientific, PaperScientificQualification.B)
        self.assertIn(StandardId.CONSORT_2025, decision.missing_standards)

    def test_overlay_missing_miame_blocks_a(self):
        paper = make_source_paper(
            modality_overlays=(ModalityOverlay.OMICS_TRANSCRIPTOMICS,),
        )
        review = make_scientific_review(
            required_standards=(StandardId.MDAR,),
            applied_standards=(StandardId.MDAR,),
            standard_outcomes={StandardId.MDAR: DomainOutcome.PASS},
        )
        decision = qualify_paper(paper, review, make_packaging_review())
        self.assertEqual(decision.scientific, PaperScientificQualification.B)
        self.assertIn(StandardId.MIAME_MINSEQE, decision.missing_standards)

    def test_methods_resource_missing_reuse_traceability_is_at_least_b(self):
        paper = make_source_paper(study_class=StudyClass.METHODS_RESOURCE)
        review = make_scientific_review(
            required_standards=(StandardId.MDAR,),
            applied_standards=(StandardId.MDAR,),
            standard_outcomes={StandardId.MDAR: DomainOutcome.PASS},
        )
        decision = qualify_paper(paper, review, make_packaging_review())
        self.assertEqual(decision.scientific, PaperScientificQualification.B)
        self.assertIn(StandardId.REUSE_TRACEABILITY, decision.missing_standards)

    def test_controlled_access_requires_safe_artifact_inventory_for_p1(self):
        paper = make_source_paper(
            study_class=StudyClass.HUMAN_OBSERVATIONAL,
            controlled_access_human_data=True,
        )
        packaging = make_packaging_review(
            safe_derived_artifacts=(),
            artifact_inventory_id=None,
            controlled_access_rule_satisfied=True,
        )
        decision = qualify_paper(paper, make_scientific_review(
            required_standards=(StandardId.STROBE, StandardId.MDAR),
            applied_standards=(StandardId.STROBE, StandardId.MDAR),
            standard_outcomes={
                StandardId.STROBE: DomainOutcome.PASS,
                StandardId.MDAR: DomainOutcome.PASS,
            },
        ), packaging)
        self.assertEqual(decision.packaging, PaperPackagingQualification.P2)

    def test_row_level_human_data_forces_packaging_p2(self):
        paper = make_source_paper(controlled_access_human_data=True, study_class=StudyClass.HUMAN_OBSERVATIONAL)
        decision = qualify_paper(
            paper,
            make_scientific_review(
                required_standards=(StandardId.STROBE, StandardId.MDAR),
                applied_standards=(StandardId.STROBE, StandardId.MDAR),
                standard_outcomes={
                    StandardId.STROBE: DomainOutcome.PASS,
                    StandardId.MDAR: DomainOutcome.PASS,
                },
            ),
            make_packaging_review(contains_private_row_level_data=True),
        )
        self.assertEqual(decision.packaging, PaperPackagingQualification.P2)

    def test_a_plus_p2_maps_to_shadow_gold(self):
        paper = make_source_paper()
        paper_decision = qualify_paper(
            paper,
            make_scientific_review(),
            make_packaging_review(
                domain_outcomes={PackagingDomain.ARTIFACT_ACCESS: DomainOutcome.BORDERLINE}
            ),
        )
        unit_decision = qualify_unit(paper_decision, make_evidence_unit(paper), make_truth_manifest(paper))
        self.assertEqual(paper_decision.candidate_tier, CandidateTier.SHADOW_CANDIDATE)
        self.assertEqual(unit_decision.release_tier, ReleaseTier.SHADOW_GOLD)
        self.assertFalse(unit_decision.gold_eligible)

    def test_b_plus_p1_maps_to_stress_only(self):
        paper = make_source_paper()
        paper_decision = qualify_paper(
            paper,
            make_scientific_review(
                critical_domains={
                    ScientificCriticalDomain.DESIGN_ANALYSIS_CREDIBILITY: DomainOutcome.BORDERLINE
                }
            ),
            make_packaging_review(),
        )
        unit_decision = qualify_unit(paper_decision, make_evidence_unit(paper), make_truth_manifest(paper))
        self.assertEqual(paper_decision.candidate_tier, CandidateTier.STRESS_CANDIDATE)
        self.assertEqual(unit_decision.release_tier, ReleaseTier.STRESS_ONLY)

    def test_frozen_manifest_required_for_release(self):
        paper = make_source_paper()
        paper_decision = qualify_paper(paper, make_scientific_review(), make_packaging_review())
        manifest = make_truth_manifest(paper, frozen=False, frozen_at=None)
        unit_decision = qualify_unit(paper_decision, make_evidence_unit(paper), manifest)
        self.assertEqual(unit_decision.release_tier, ReleaseTier.EXCLUDED)
        self.assertIn("truth manifest must be frozen before release", unit_decision.reasons)

    def test_cross_split_lineage_is_violation(self):
        lineage = LineageInfo(consortium_lineages=("TCGA",))
        train_unit = BenchmarkUnit(
            benchmark_unit_id="BU:train",
            paper_id="PMID:1",
            evidence_unit_ids=("EU:1",),
            split="train",
            lineage=lineage,
        )
        test_unit = BenchmarkUnit(
            benchmark_unit_id="BU:test",
            paper_id="PMID:2",
            evidence_unit_ids=("EU:2",),
            split="test",
            lineage=lineage,
        )
        violations = validate_split_safety([train_unit, test_unit])
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].violation_type, SplitSafetyViolationType.CROSS_SPLIT_LEAKAGE)

    def test_lineage_dominance_cap_is_violation(self):
        lineage = LineageInfo(dataset_lineages=("GEO_SERIES_1",))
        units = [
            BenchmarkUnit(
                benchmark_unit_id=f"BU:{index}",
                paper_id=f"PMID:{index}",
                evidence_unit_ids=(f"EU:{index}",),
                split="train",
                lineage=lineage,
            )
            for index in range(4)
        ]
        violations = validate_split_safety(units, policy=SplitSafetyPolicy(max_units_per_lineage=3))
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].violation_type, SplitSafetyViolationType.LINEAGE_DOMINANCE)
        self.assertEqual(violations[0].observed_count, 4)

    def test_jsonl_round_trip_preserves_source_paper_and_manifest(self):
        paper = make_source_paper(
            modality_overlays=(ModalityOverlay.OMICS_TRANSCRIPTOMICS,),
            metadata={"doi": "10.1000/example"},
        )
        manifest = make_truth_manifest(
            paper,
            provenance_entities=("pmid:1", "doi:10.1000/example"),
            provenance_activities=("manual_adjudication",),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_path = os.path.join(tmpdir, "papers.jsonl")
            manifest_path = os.path.join(tmpdir, "manifests.jsonl")
            write_jsonl(paper_path, [paper])
            write_jsonl(manifest_path, [manifest])

            loaded_papers = load_jsonl(paper_path, loader=source_paper_from_dict)
            loaded_manifests = load_jsonl(manifest_path, loader=truth_manifest_from_dict)

        self.assertEqual(loaded_papers[0], paper)
        self.assertEqual(loaded_manifests[0], manifest)

    def test_release_index_is_deterministic_and_skips_excluded_units(self):
        lineage = LineageInfo(source_family="family-1")
        units = [
            BenchmarkUnit(
                benchmark_unit_id="BU:1",
                paper_id="PMID:1",
                evidence_unit_ids=("EU:1",),
                split="test",
                lineage=lineage,
            ),
            BenchmarkUnit(
                benchmark_unit_id="BU:2",
                paper_id="PMID:2",
                evidence_unit_ids=("EU:2",),
                split="test",
                lineage=lineage,
            ),
        ]
        decisions = {
            "BU:1": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:1",
                release_tier=ReleaseTier.PUBLIC_GOLD,
                gold_eligible=True,
                reasons=(),
            ),
            "BU:2": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:2",
                release_tier=ReleaseTier.EXCLUDED,
                gold_eligible=False,
                reasons=(),
            ),
        }
        first = build_release_index(units, decisions, holdout_salt="salt-1", canary_salt="salt-2")
        second = build_release_index(units, decisions, holdout_salt="salt-1", canary_salt="salt-2")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].benchmark_unit_id, "BU:1")
        self.assertIn(first[0].holdout_bucket, {PUBLIC_HOLDOUT_BUCKET, "private"})
        self.assertTrue(first[0].canary_string.startswith("LS-PWB-CANARY-BU_1-"))
        self.assertEqual(first[0].benchmark_split, "test")

    def test_release_index_enforces_split_safety_on_holdout_buckets(self):
        public_family = None
        private_family = None
        for index in range(200):
            family = f"family-{index}"
            bucket = assign_holdout_bucket(
                f"source_family:{family}",
                public_ratio=0.5,
                private_ratio=0.5,
                salt="holdout-test",
            )
            if bucket == "public" and public_family is None:
                public_family = family
            if bucket == "private" and private_family is None:
                private_family = family
            if public_family and private_family:
                break
        self.assertIsNotNone(public_family)
        self.assertIsNotNone(private_family)

        units = [
            BenchmarkUnit(
                benchmark_unit_id="BU:public-family",
                paper_id="P1",
                evidence_unit_ids=("E1",),
                split="test",
                lineage=LineageInfo(
                    source_family=public_family,
                    consortium_lineages=("shared-consortium",),
                ),
            ),
            BenchmarkUnit(
                benchmark_unit_id="BU:private-family",
                paper_id="P2",
                evidence_unit_ids=("E2",),
                split="test",
                lineage=LineageInfo(
                    source_family=private_family,
                    consortium_lineages=("shared-consortium",),
                ),
            ),
        ]
        decisions = {
            "BU:public-family": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:public-family",
                release_tier=ReleaseTier.PUBLIC_GOLD,
                gold_eligible=True,
                reasons=(),
            ),
            "BU:private-family": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:private-family",
                release_tier=ReleaseTier.PUBLIC_GOLD,
                gold_eligible=True,
                reasons=(),
            ),
        }

        with self.assertRaises(ValueError):
            build_release_index(
                units,
                decisions,
                public_ratio=0.5,
                private_ratio=0.5,
                holdout_salt="holdout-test",
            )

    def test_release_index_keeps_same_paper_units_in_same_holdout_bucket(self):
        units = [
            BenchmarkUnit(
                benchmark_unit_id="BU:paper-1:abstract",
                paper_id="PMID:paper-1",
                evidence_unit_ids=("EU:1",),
                split="test",
                lineage=LineageInfo(),
            ),
            BenchmarkUnit(
                benchmark_unit_id="BU:paper-1:methods",
                paper_id="PMID:paper-1",
                evidence_unit_ids=("EU:2",),
                split="test",
                lineage=LineageInfo(),
            ),
            BenchmarkUnit(
                benchmark_unit_id="BU:paper-1:results",
                paper_id="PMID:paper-1",
                evidence_unit_ids=("EU:3",),
                split="test",
                lineage=LineageInfo(),
            ),
        ]
        decisions = {
            unit.benchmark_unit_id: BenchmarkUnitDecisionRecord(
                benchmark_unit_id=unit.benchmark_unit_id,
                release_tier=ReleaseTier.SHADOW_GOLD,
                gold_eligible=False,
                reasons=(),
            )
            for unit in units
        }

        entries = build_release_index(units, decisions, holdout_salt="same-paper-holdout")
        self.assertEqual(len(entries), 3)
        self.assertEqual(len({entry.holdout_bucket for entry in entries}), 1)

    def test_release_bundle_ignores_excluded_units_for_split_safety(self):
        units = [
            BenchmarkUnit(
                benchmark_unit_id="BU:included",
                paper_id="PMID:included",
                evidence_unit_ids=("EU:included",),
                split="test",
                lineage=LineageInfo(source_family="shared-family"),
            ),
            BenchmarkUnit(
                benchmark_unit_id="BU:excluded",
                paper_id="PMID:excluded",
                evidence_unit_ids=("EU:excluded",),
                split="test",
                lineage=LineageInfo(source_family="shared-family"),
            ),
        ]
        decisions = {
            "BU:included": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:included",
                release_tier=ReleaseTier.SHADOW_GOLD,
                gold_eligible=False,
                reasons=(),
            ),
            "BU:excluded": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:excluded",
                release_tier=ReleaseTier.EXCLUDED,
                gold_eligible=False,
                reasons=(),
            ),
        }

        bundle = build_release_manifest_bundle(
            units,
            decisions,
            split_policy=SplitSafetyPolicy(max_units_per_lineage=1),
        )
        self.assertEqual(len(bundle.release_index), 1)
        self.assertEqual(bundle.release_index[0].benchmark_unit_id, "BU:included")

    def test_release_manifest_bundle_includes_summary(self):
        units = [
            BenchmarkUnit(
                benchmark_unit_id="BU:bundle",
                paper_id="PMID:bundle",
                evidence_unit_ids=("EU:bundle",),
                split="test",
                lineage=LineageInfo(source_family="bundle-family"),
            )
        ]
        decisions = {
            "BU:bundle": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:bundle",
                release_tier=ReleaseTier.PUBLIC_GOLD,
                gold_eligible=True,
                reasons=(),
            )
        }
        bundle = build_release_manifest_bundle(
            units,
            decisions,
            holdout_salt="bundle-salt",
            enforce_split_safety=False,
        )
        summary = bundle.summary()
        self.assertEqual(summary["entries"], 1)
        self.assertEqual(summary["tier_counts"]["public_gold"], 1)
        self.assertEqual(summary["split_safety_violations"], 0)
        self.assertIsNotNone(bundle.provenance_manifest)
        self.assertEqual(bundle.provenance_manifest.input_record_counts["benchmark_units"], 1)
        self.assertEqual(bundle.provenance_manifest.input_record_counts["unit_decisions"], 1)
        self.assertEqual(bundle.provenance_manifest.included_benchmark_unit_ids, ("BU:bundle",))
        self.assertEqual(len(bundle.artifact_checksums), 4)

    def test_release_manifest_bundle_checksums_match_rendered_artifacts(self):
        units = [
            BenchmarkUnit(
                benchmark_unit_id="BU:checksum",
                paper_id="PMID:checksum",
                evidence_unit_ids=("EU:checksum",),
                split="test",
                lineage=LineageInfo(source_family="checksum-family"),
            )
        ]
        decisions = {
            "BU:checksum": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:checksum",
                release_tier=ReleaseTier.PUBLIC_GOLD,
                gold_eligible=True,
                reasons=(),
            )
        }
        bundle = build_release_manifest_bundle(
            units,
            decisions,
            holdout_salt="checksum-salt",
            canary_salt="checksum-canary",
            generated_at="2026-04-10T00:00:00Z",
            enforce_split_safety=False,
        )
        payloads = render_release_bundle_artifacts(bundle, include_checksums=False)
        checksum_map = {
            item.artifact_name: item
            for item in bundle.artifact_checksums
        }

        self.assertIn("release_index.jsonl", payloads)
        self.assertIn("provenance_manifest.json", payloads)
        self.assertEqual(
            set(checksum_map),
            {
                "release_index.jsonl",
                "split_safety_violations.jsonl",
                "release_summary.json",
                "provenance_manifest.json",
            },
        )
        for artifact_name, payload in payloads.items():
            self.assertEqual(
                checksum_map[artifact_name].sha256,
                hashlib.sha256(payload).hexdigest(),
            )

    def test_verify_release_bundle_directory_returns_ok(self):
        units = [
            BenchmarkUnit(
                benchmark_unit_id="BU:verify",
                paper_id="PMID:verify",
                evidence_unit_ids=("EU:verify",),
                split="test",
                lineage=LineageInfo(source_family="verify-family"),
            )
        ]
        decisions = {
            "BU:verify": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:verify",
                release_tier=ReleaseTier.PUBLIC_GOLD,
                gold_eligible=True,
                reasons=(),
            )
        }
        bundle = build_release_manifest_bundle(
            units,
            decisions,
            generated_at="2026-04-10T00:00:00Z",
            enforce_split_safety=False,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            payloads = render_release_bundle_artifacts(bundle)
            for artifact_name, payload in payloads.items():
                with open(os.path.join(tmpdir, artifact_name), "wb") as handle:
                    handle.write(payload)
            report = verify_release_bundle_directory(tmpdir)
        self.assertTrue(report.ok)
        self.assertTrue(report.summary_consistent)
        self.assertTrue(report.provenance_consistent)

    def test_verify_release_bundle_directory_detects_checksum_mismatch(self):
        units = [
            BenchmarkUnit(
                benchmark_unit_id="BU:verify-bad",
                paper_id="PMID:verify-bad",
                evidence_unit_ids=("EU:verify-bad",),
                split="test",
                lineage=LineageInfo(source_family="verify-bad-family"),
            )
        ]
        decisions = {
            "BU:verify-bad": BenchmarkUnitDecisionRecord(
                benchmark_unit_id="BU:verify-bad",
                release_tier=ReleaseTier.PUBLIC_GOLD,
                gold_eligible=True,
                reasons=(),
            )
        }
        bundle = build_release_manifest_bundle(
            units,
            decisions,
            generated_at="2026-04-10T00:00:00Z",
            enforce_split_safety=False,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            payloads = render_release_bundle_artifacts(bundle)
            for artifact_name, payload in payloads.items():
                with open(os.path.join(tmpdir, artifact_name), "wb") as handle:
                    handle.write(payload)
            with open(os.path.join(tmpdir, "release_summary.json"), "w", encoding="utf-8") as handle:
                handle.write("{\"corrupted\": true}\n")
            report = verify_release_bundle_directory(tmpdir)
        self.assertFalse(report.ok)
        self.assertIn("release_summary.json:sha256", report.checksum_mismatches)

    def test_task_family_mapping_and_task_bundle_construction(self):
        paper = make_source_paper()
        evidence_unit = make_evidence_unit(
            paper,
            unit_id="EU:figure",
            unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
            evidence_pointers=("fig1", "tbl1"),
        )
        benchmark_unit = BenchmarkUnit(
            benchmark_unit_id="BU:task",
            paper_id=paper.paper_id,
            evidence_unit_ids=("EU:figure",),
            split="test",
        )
        manifest = make_truth_manifest(paper)
        bundle = build_task_bundle(
            benchmark_unit=benchmark_unit,
            source_paper=paper,
            evidence_units=(evidence_unit,),
            truth_manifest=manifest,
            release_tier=ReleaseTier.PUBLIC_GOLD,
            provenance_manifest_id="PMAN:1",
            holdout_bucket="public",
        )
        self.assertEqual(task_family_for_evidence_unit_type(EvidenceUnitType.FIGURE_TABLE_RESULT), TaskFamily.RESULTS_TO_TEXT)
        self.assertEqual(bundle.task_family, TaskFamily.RESULTS_TO_TEXT)
        self.assertEqual(bundle.provenance_manifest_id, "PMAN:1")
        self.assertEqual(bundle.holdout_bucket, "public")
        self.assertIn("evidence_fidelity", bundle.scoring_profile["deterministic_checks"])

    def test_build_task_bundle_rejects_mixed_task_families(self):
        paper = make_source_paper()
        benchmark_unit = BenchmarkUnit(
            benchmark_unit_id="BU:mixed",
            paper_id=paper.paper_id,
            evidence_unit_ids=("EU:claim", "EU:methods"),
        )
        manifest = make_truth_manifest(paper)
        evidence_units = (
            make_evidence_unit(
                paper,
                unit_id="EU:claim",
                unit_type=EvidenceUnitType.CLAIM_CLUSTER,
            ),
            make_evidence_unit(
                paper,
                unit_id="EU:methods",
                unit_type=EvidenceUnitType.METHODS_PROTOCOL_BLOCK,
            ),
        )
        with self.assertRaises(ValueError):
            build_task_bundle(
                benchmark_unit=benchmark_unit,
                source_paper=paper,
                evidence_units=evidence_units,
                truth_manifest=manifest,
                release_tier=ReleaseTier.PUBLIC_GOLD,
            )

    def test_build_truth_manifest_bundle_marks_release_ready(self):
        paper = make_source_paper()
        manifest = make_truth_manifest(paper, manifest_id="TM:bundle")
        evidence_units = (
            make_evidence_unit(paper, unit_id="EU:1"),
            make_evidence_unit(paper, unit_id="EU:2"),
        )
        bundle = build_truth_manifest_bundle(
            truth_manifest=manifest,
            evidence_units=evidence_units,
            provenance_manifest_id="PMAN:bundle",
        )
        self.assertTrue(bundle.release_ready)
        self.assertEqual(bundle.bundle_id, "TMB:TM:bundle")
        self.assertEqual(bundle.provenance_manifest_id, "PMAN:bundle")

    def test_build_task_bundles_skips_excluded_release_tiers(self):
        paper = make_source_paper()
        bundles = build_task_bundles(
            benchmark_units=(
                BenchmarkUnit(
                    benchmark_unit_id="BU:excluded",
                    paper_id=paper.paper_id,
                    evidence_unit_ids=("EU:excluded",),
                ),
            ),
            papers={paper.paper_id: paper},
            evidence_units={
                "EU:excluded": make_evidence_unit(
                    paper,
                    unit_id="EU:excluded",
                    unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
                )
            },
            truth_manifests={paper.paper_id: make_truth_manifest(paper)},
            release_tiers={"BU:excluded": ReleaseTier.EXCLUDED},
        )
        self.assertEqual(bundles, ())

    def test_build_benchmark_units_from_evidence_units_inherits_lineage(self):
        paper = make_source_paper(
            lineage=LineageInfo(
                source_family="family-1",
                consortium_lineages=("consortium-a",),
                dataset_lineages=("dataset-a",),
                lab_lineages=("lab-a",),
            )
        )
        evidence_units = (
            make_evidence_unit(
                paper,
                unit_id="EU:1",
                unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
            ),
            make_evidence_unit(
                paper,
                unit_id="EU:2",
                unit_type=EvidenceUnitType.METHODS_PROTOCOL_BLOCK,
            ),
        )
        benchmark_units = build_benchmark_units_from_evidence_units(
            evidence_units,
            papers={paper.paper_id: paper},
        )
        self.assertEqual(len(benchmark_units), 2)
        self.assertEqual(benchmark_units[0].benchmark_unit_id, "BU:EU:1")
        self.assertEqual(benchmark_units[0].lineage.source_family, "family-1")

    def test_build_benchmark_unit_decisions_from_auto_qualifications(self):
        paper = make_source_paper()
        auto_record = AutoQualificationRecord(
            paper_id=paper.paper_id,
            decision=PaperQualificationDecision(
                scientific=PaperScientificQualification.A,
                packaging=PaperPackagingQualification.P1,
                candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                eligible_for_unit_extraction=True,
                required_standards=(),
                writing=PaperWritingQualification.W2,
            ),
            confidence=AutoReviewConfidence.MEDIUM,
        )
        benchmark_units = (
            BenchmarkUnit(
                benchmark_unit_id="BU:EU:1",
                paper_id=paper.paper_id,
                evidence_unit_ids=("EU:1",),
            ),
        )
        decisions = build_benchmark_unit_decisions_from_auto_qualifications(
            benchmark_units,
            {paper.paper_id: auto_record},
        )
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].release_tier, ReleaseTier.SHADOW_GOLD)

    def test_build_evaluation_task_bundles(self):
        paper = make_source_paper(
            paper_id="PMID:qa-bundle",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            metadata={
                "results_text": "Figure 1 shows reduced biomarker levels. Table 1 reports the endpoint.",
                "methods_text": "Patients were randomized to intervention or placebo.",
                "review_response_text": "We added a validation experiment after review.",
                "figure_captions": [{"pointer": "Fig1", "text": "Biomarker levels decreased after intervention."}],
                "table_rows": [{"pointer": "Table1", "text": "Primary endpoint improved at week 12."}],
                "trial_registry_summary": [{"pointer": "NCT01234567", "text": "Phase 2 randomized placebo-controlled trial."}],
                "review_comments": [{"pointer": "R1", "text": "Major concern: add a validation experiment."}],
            },
        )
        evidence_units, specs, _ = build_parser_assisted_extraction_drafts((paper,), max_assertions_per_unit=2)
        observations, questions, answers, quality_records, _ = build_evaluation_extraction_artifacts(
            source_papers=(paper,),
            evidence_units=evidence_units,
            extraction_specs=specs,
            max_questions_per_unit=2,
        )
        bundles = build_evaluation_task_bundles(
            questions=questions,
            answers=answers,
            observations=observations,
            papers={paper.paper_id: paper},
            truth_manifests={paper.paper_id: make_truth_manifest(paper)},
            default_release_tier=ReleaseTier.SHADOW_GOLD,
            source_quality_records=quality_records,
        )
        self.assertGreaterEqual(len(bundles), 2)
        self.assertTrue(any(bundle.task_family == TaskFamily.TRIAL_QA for bundle in bundles))
        self.assertTrue(any(bundle.task_family == TaskFamily.SOURCE_QUALITY_QA for bundle in bundles))
        qa_bundle = next(bundle for bundle in bundles if bundle.task_family == TaskFamily.TRIAL_QA)
        self.assertIn("question_prompt", qa_bundle.input_artifacts)
        self.assertIn("expected_answer_texts", qa_bundle.input_artifacts)
        self.assertEqual(qa_bundle.release_tier, ReleaseTier.SHADOW_GOLD)

    def test_annotate_task_bundles_with_release_index(self):
        paper = make_source_paper()
        evidence_unit = make_evidence_unit(
            paper,
            unit_id="EU:annotate",
            unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
        )
        benchmark_unit = BenchmarkUnit(
            benchmark_unit_id="BU:annotate",
            paper_id=paper.paper_id,
            evidence_unit_ids=("EU:annotate",),
        )
        task_bundle = build_task_bundle(
            benchmark_unit=benchmark_unit,
            source_paper=paper,
            evidence_units=(evidence_unit,),
            truth_manifest=make_truth_manifest(paper),
            release_tier=ReleaseTier.SHADOW_GOLD,
        )
        annotated = annotate_task_bundles_with_release_index(
            (task_bundle,),
            {
                benchmark_unit.benchmark_unit_id: ReleaseIndexEntry(
                    benchmark_unit_id=benchmark_unit.benchmark_unit_id,
                    paper_id=paper.paper_id,
                    release_tier=ReleaseTier.SHADOW_GOLD,
                    holdout_bucket="public",
                    canary_string="TEST-CANARY",
                    benchmark_split="test",
                )
            },
        )
        self.assertEqual(len(annotated), 1)
        self.assertEqual(annotated[0].holdout_bucket, "public")
        self.assertEqual(annotated[0].release_tier, ReleaseTier.SHADOW_GOLD)

    def test_run_baseline_and_evaluate_submissions(self):
        paper = make_source_paper()
        evidence_unit = make_evidence_unit(
            paper,
            unit_id="EU:baseline",
            unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
            evidence_pointers=("Fig1", "Table1"),
        )
        benchmark_unit = BenchmarkUnit(
            benchmark_unit_id="BU:baseline",
            paper_id=paper.paper_id,
            evidence_unit_ids=("EU:baseline",),
            split="test",
        )
        task_bundle = build_task_bundle(
            benchmark_unit=benchmark_unit,
            source_paper=paper,
            evidence_units=(evidence_unit,),
            truth_manifest=make_truth_manifest(paper),
            release_tier=ReleaseTier.PUBLIC_GOLD,
        )
        rendered = render_baseline_output(task_bundle, BaselineKind.RETRIEVAL_WRITER)
        self.assertIn("Fig1", rendered)
        run_spec, submissions = run_baseline(
            task_bundles=(task_bundle,),
            baseline_kind=BaselineKind.SECTION_WISE_PIPELINE,
        )
        self.assertTrue(run_spec.replay_verified)
        self.assertEqual(len(submissions), 1)
        evaluations = evaluate_submissions((task_bundle,), submissions)
        self.assertEqual(len(evaluations), 1)
        self.assertTrue(evaluations[0].deterministic_checks_passed)
        self.assertEqual(evaluations[0].evaluation_layers, (EvaluationLayer.DETERMINISTIC_CHECKS,))

    def test_run_baseline_and_evaluate_submissions_for_qa_bundle(self):
        paper = make_source_paper(
            paper_id="PMID:qa-baseline",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            metadata={
                "results_text": "Figure 2 shows lower response values.",
                "figure_captions": [{"pointer": "Fig2", "text": "Response values were lower in the intervention arm."}],
            },
        )
        evidence_units, specs, _ = build_parser_assisted_extraction_drafts((paper,), max_assertions_per_unit=1)
        observations, questions, answers, quality_records, _ = build_evaluation_extraction_artifacts(
            source_papers=(paper,),
            evidence_units=evidence_units,
            extraction_specs=specs,
            max_questions_per_unit=1,
        )
        bundles = build_evaluation_task_bundles(
            questions=questions,
            answers=answers,
            observations=observations,
            papers={paper.paper_id: paper},
            truth_manifests={paper.paper_id: make_truth_manifest(paper)},
            default_release_tier=ReleaseTier.PUBLIC_GOLD,
            source_quality_records=quality_records,
        )
        qa_bundle = bundles[0]
        rendered = render_baseline_output(qa_bundle, BaselineKind.RETRIEVAL_WRITER)
        self.assertIn("Question:", rendered)
        run_spec, submissions = run_baseline(
            task_bundles=(qa_bundle,),
            baseline_kind=BaselineKind.RETRIEVAL_WRITER,
        )
        self.assertTrue(run_spec.replay_verified)
        evaluations = evaluate_submissions((qa_bundle,), submissions)
        self.assertEqual(len(evaluations), 1)
        self.assertTrue(evaluations[0].deterministic_checks_passed)
        self.assertEqual(evaluations[0].scores["answer_support"], 1.0)

    def test_holdout_and_canary_helpers_are_stable(self):
        bucket_one = assign_holdout_bucket("BU:alpha", salt="stable-salt")
        bucket_two = assign_holdout_bucket("BU:alpha", salt="stable-salt")
        canary_one = generate_canary_string("BU:alpha", salt="stable-canary")
        canary_two = generate_canary_string("BU:alpha", salt="stable-canary")

        self.assertEqual(bucket_one, bucket_two)
        self.assertEqual(canary_one, canary_two)

    def test_pilot_manifest_meets_coverage_requirements(self):
        manifest_path = os.path.join(
            ROOT,
            "calibration",
            "pilot_v1",
            "pilot_manifest.jsonl",
        )
        specs = load_jsonl(manifest_path, loader=pilot_calibration_spec_from_dict)
        self.assertEqual(validate_pilot_calibration_set(specs), ())
        summary = pilot_coverage_summary(specs)
        self.assertEqual(summary["total_specs"], 12)
        self.assertGreaterEqual(summary["hybrid_overlay_specs"], 3)

    def test_invalid_pilot_calibration_set_reports_missing_coverage(self):
        specs = [
            PilotCalibrationSpec(
                calibration_id="pilot-small",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
            )
        ]
        issues = validate_pilot_calibration_set(specs)
        self.assertTrue(issues)
        self.assertIn("pilot calibration set must contain at least 12 papers", issues)

    def test_full_calibration_set_meets_targets(self):
        specs = make_full_calibration_specs()
        self.assertEqual(validate_full_calibration_set(specs), ())
        summary = pilot_coverage_summary(specs)
        self.assertEqual(summary["total_specs"], 60)
        self.assertGreaterEqual(summary["hybrid_overlay_specs"], 15)
        self.assertGreaterEqual(summary["controlled_access_specs"], 8)

    def test_build_full_calibration_scaffold_honors_prefix(self):
        specs = build_full_calibration_scaffold(prefix="cal")
        self.assertEqual(len(specs), 60)
        self.assertTrue(all(spec.calibration_id.startswith("cal-") for spec in specs))
        self.assertEqual(validate_full_calibration_set(specs), ())

    def test_merge_review_forms_keeps_latest_duplicate(self):
        forms = (
            PilotReviewForm(
                calibration_id="full-01",
                reviewer_id="reviewer_a",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                completed=False,
            ),
            PilotReviewForm(
                calibration_id="full-01",
                reviewer_id="reviewer_a",
                study_class=StudyClass.HUMAN_OBSERVATIONAL,
                completed=True,
            ),
        )
        merged = merge_review_forms(forms)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].study_class, StudyClass.HUMAN_OBSERVATIONAL)
        self.assertTrue(merged[0].completed)

    def test_build_adjudication_queue_marks_ready_items(self):
        specs = (
            PilotCalibrationSpec(
                calibration_id="queue-01",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
            ),
        )
        forms = (
            PilotReviewForm(
                calibration_id="queue-01",
                reviewer_id="reviewer_a",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                completed=True,
            ),
            PilotReviewForm(
                calibration_id="queue-01",
                reviewer_id="reviewer_b",
                study_class=StudyClass.HUMAN_OBSERVATIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                completed=True,
            ),
        )
        queue = build_adjudication_queue(
            specs,
            forms,
            adjudications=(),
            reviewer_ids=("reviewer_a", "reviewer_b"),
        )
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0].status, "ready_for_adjudication")
        self.assertIn("study_class", queue[0].disagreement_fields)

    def test_audit_calibration_drift_detects_added_and_changed_specs(self):
        baseline = (
            PilotCalibrationSpec(
                calibration_id="drift-01",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
            ),
        )
        updated = (
            PilotCalibrationSpec(
                calibration_id="drift-01",
                study_class=StudyClass.HUMAN_OBSERVATIONAL,
                claim_mode=ClaimMode.EXPLORATORY,
                target_candidate_tier=CandidateTier.SHADOW_CANDIDATE,
            ),
            PilotCalibrationSpec(
                calibration_id="drift-02",
                study_class=StudyClass.METHODS_RESOURCE,
                claim_mode=ClaimMode.RESOURCE_RELEASE,
            ),
        )
        report = audit_calibration_drift(baseline, updated)
        self.assertIsInstance(report, CalibrationDriftReport)
        self.assertEqual(report.added_calibration_ids, ("drift-02",))
        self.assertIn("drift-01", report.changed_target_labels)

    def test_metadata_hint_detects_trial_mismatch_and_consort(self):
        paper = make_source_paper(
            study_class=StudyClass.HUMAN_OBSERVATIONAL,
            claim_mode=ClaimMode.EXPLORATORY,
            title="Randomized placebo-controlled biomarker trial",
            metadata={
                "article_type": "Randomized clinical trial",
                "trial_registration": "NCT01234567",
                "keywords": "placebo, primary endpoint, biomarker",
            },
        )
        hint = suggest_governance_metadata_hints(paper)
        self.assertEqual(hint.suggested_study_class, StudyClass.HUMAN_INTERVENTIONAL)
        self.assertEqual(hint.suggested_claim_mode, ClaimMode.CONFIRMATORY)
        self.assertIn(StandardId.CONSORT_2025, hint.suggested_required_standards)
        self.assertTrue(
            any("metadata suggests study_class human_interventional" in warning for warning in hint.warnings)
        )

    def test_metadata_hint_suggests_missing_omics_and_qpcr_overlays(self):
        paper = make_source_paper(
            title="Mechanistic RNA-seq and RT-qPCR profiling",
            metadata={
                "assay_types": "RNA-seq; RT-qPCR",
                "repositories": "GEO accession",
            },
        )
        hint = suggest_governance_metadata_hints(paper)
        self.assertIn(ModalityOverlay.OMICS_TRANSCRIPTOMICS, hint.suggested_modality_overlays)
        self.assertIn(ModalityOverlay.QPCR, hint.suggested_modality_overlays)
        self.assertIn(StandardId.MIAME_MINSEQE, hint.suggested_required_standards)
        self.assertIn(StandardId.MIQE_2_0, hint.suggested_required_standards)
        self.assertTrue(
            any("metadata suggests missing modality overlays" in warning for warning in hint.warnings)
        )

    def test_metadata_hint_keeps_configured_overlay_standards_even_if_not_detected(self):
        paper = make_source_paper(
            modality_overlays=(ModalityOverlay.OMICS_TRANSCRIPTOMICS, ModalityOverlay.QPCR),
            title="Mechanistic RT_qPCR profiling",
            metadata={
                "assay_types": "RT_qPCR",
            },
        )
        hint = suggest_governance_metadata_hints(paper)
        self.assertIn(StandardId.MIAME_MINSEQE, hint.suggested_required_standards)
        self.assertIn(StandardId.MIQE_2_0, hint.suggested_required_standards)

    def test_metadata_hint_normalizes_underscores_and_hyphens(self):
        paper = make_source_paper(
            title="RNA_seq and RT_qPCR atlas resource",
            metadata={"article_type": "resource-paper"},
        )
        hint = suggest_governance_metadata_hints(paper)
        self.assertIn(ModalityOverlay.OMICS_TRANSCRIPTOMICS, hint.suggested_modality_overlays)
        self.assertIn(ModalityOverlay.QPCR, hint.suggested_modality_overlays)
        self.assertEqual(hint.suggested_claim_mode, ClaimMode.RESOURCE_RELEASE)

    def test_metadata_hint_suggests_methods_resource_and_resource_release(self):
        paper = make_source_paper(
            study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
            claim_mode=ClaimMode.EXPLORATORY,
            title="A benchmark atlas resource for microbial communities",
            metadata={
                "article_type": "Resource and benchmark paper",
                "keywords": "atlas, benchmark, software tool",
            },
        )
        hint = suggest_governance_metadata_hints(paper)
        self.assertEqual(hint.suggested_study_class, StudyClass.METHODS_RESOURCE)
        self.assertEqual(hint.suggested_claim_mode, ClaimMode.RESOURCE_RELEASE)
        self.assertIn(StandardId.REUSE_TRACEABILITY, hint.suggested_required_standards)

    def test_build_pilot_review_and_adjudication_templates(self):
        specs = load_jsonl(
            os.path.join(ROOT, "calibration", "pilot_v1", "pilot_manifest.jsonl"),
            loader=pilot_calibration_spec_from_dict,
        )
        forms = build_pilot_review_forms(specs, reviewer_ids=("reviewer_a", "reviewer_b"))
        adjudications = build_pilot_adjudication_shells(
            specs,
            adjudicator_id="adjudicator_1",
            reviewer_ids=("reviewer_a", "reviewer_b"),
        )
        self.assertEqual(len(forms), 24)
        self.assertEqual(len(adjudications), 12)
        self.assertIsInstance(forms[0], PilotReviewForm)
        self.assertIsInstance(adjudications[0], PilotAdjudicationRecord)

    def test_template_files_round_trip(self):
        reviewer_forms = load_jsonl(
            os.path.join(ROOT, "calibration", "pilot_v1", "reviewer_forms_template.jsonl"),
            loader=pilot_review_form_from_dict,
        )
        adjudications = load_jsonl(
            os.path.join(ROOT, "calibration", "pilot_v1", "adjudication_template.jsonl"),
            loader=pilot_adjudication_record_from_dict,
        )
        self.assertEqual(len(reviewer_forms), 24)
        self.assertEqual(len(adjudications), 12)
        self.assertFalse(reviewer_forms[0].completed)
        self.assertFalse(adjudications[0].finalized)

    def test_agreement_summary_matches_thresholds(self):
        forms = (
            PilotReviewForm(
                calibration_id="pilot-01",
                reviewer_id="reviewer_a",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                completed=True,
            ),
            PilotReviewForm(
                calibration_id="pilot-01",
                reviewer_id="reviewer_b",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                completed=True,
            ),
        )
        adjudications = (
            PilotAdjudicationRecord(
                calibration_id="pilot-01",
                adjudicator_id="adj-1",
                final_study_class=StudyClass.HUMAN_INTERVENTIONAL,
                final_claim_mode=ClaimMode.CONFIRMATORY,
                final_candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                final_unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                finalized=True,
            ),
        )
        summary = compute_agreement_against_adjudication(forms, adjudications)
        self.assertIsInstance(summary, PilotAgreementSummary)
        self.assertEqual(summary.study_class.rate, 1.0)
        self.assertEqual(validate_pilot_agreement_thresholds(summary), ())

    def test_agreement_thresholds_report_failures(self):
        summary = PilotAgreementSummary(
            study_class=AgreementMetric("study_class", 1, 2, 0.50),
            claim_mode=AgreementMetric("claim_mode", 1, 2, 0.50),
            candidate_tier=AgreementMetric("candidate_tier", 1, 2, 0.50),
            unit_release_tier=AgreementMetric("unit_release_tier", 1, 2, 0.50),
        )
        issues = validate_pilot_agreement_thresholds(summary)
        self.assertTrue(issues)
        self.assertIn("study_class agreement 50.00% is below threshold 90.00%", issues)

    def test_agreement_deduplicates_duplicate_reviewer_forms(self):
        forms = (
            PilotReviewForm(
                calibration_id="pilot-dup",
                reviewer_id="reviewer_a",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                completed=True,
            ),
            PilotReviewForm(
                calibration_id="pilot-dup",
                reviewer_id="reviewer_a",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                completed=True,
            ),
        )
        adjudications = (
            PilotAdjudicationRecord(
                calibration_id="pilot-dup",
                adjudicator_id="adj-1",
                final_study_class=StudyClass.HUMAN_INTERVENTIONAL,
                final_claim_mode=ClaimMode.CONFIRMATORY,
                final_candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                final_unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                finalized=True,
            ),
        )
        summary = compute_agreement_against_adjudication(forms, adjudications)
        self.assertEqual(summary.study_class.comparisons, 1)
        self.assertEqual(summary.claim_mode.comparisons, 1)

    def test_program_progress_summary_hits_gates(self):
        papers = [
            make_source_paper(
                paper_id=f"PMID:{index}",
                controlled_access_human_data=index < 12,
            )
            for index in range(180)
        ]
        paper_decisions = [make_paper_decision() for _ in range(180)]
        task_bundles = [
            TaskBundle(
                task_bundle_id=f"TB:{index}",
                benchmark_unit_id=f"BU:{index}",
                task_family=TaskFamily.RESULTS_TO_TEXT if index < 40 else TaskFamily.METHODS_TO_TEXT,
                release_tier=ReleaseTier.PUBLIC_GOLD,
                study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                claim_mode=ClaimMode.EXPLORATORY,
                truth_manifest_id=f"TM:{index}",
                provenance_manifest_id="PMAN:v1",
                paper_id=f"PMID:{index % 180}",
                evidence_unit_ids=(f"EU:{index}",),
                holdout_bucket="public" if index < 120 else "private",
            )
            for index in range(150)
        ]
        judge_units = [
            JudgeValidationUnit(
                validation_unit_id=f"JV:{index}",
                task_bundle_id=f"TB:{index}",
                human_adjudicated=True,
                rubric_labels={
                    "evidence_fidelity": 1.0,
                    "traceability": 1.0,
                    "provenance_completeness": 1.0,
                    "writing_structure_compliance": 1.0,
                },
                frozen=True,
            )
            for index in range(30)
        ]
        baseline_runs = [
            BaselineRunSpec(
                baseline_id="baseline-reference",
                baseline_kind=BaselineKind.REFERENCE_TEMPLATE,
                replay_verified=True,
            ),
            BaselineRunSpec(
                baseline_id="baseline-retrieval",
                baseline_kind=BaselineKind.RETRIEVAL_WRITER,
                replay_verified=True,
            ),
            BaselineRunSpec(
                baseline_id="baseline-section",
                baseline_kind=BaselineKind.SECTION_WISE_PIPELINE,
                replay_verified=True,
            ),
            BaselineRunSpec(
                baseline_id="baseline-single-agent",
                baseline_kind=BaselineKind.SINGLE_AGENT_WRITER,
                replay_verified=True,
            ),
            BaselineRunSpec(
                baseline_id="baseline-multi-agent",
                baseline_kind=BaselineKind.MULTI_AGENT_ORCHESTRATION,
                replay_verified=True,
            ),
        ]
        report = summarize_program_progress(
            source_papers=papers,
            paper_decisions=paper_decisions,
            task_bundles=task_bundles,
            judge_validation_units=judge_units,
            baseline_runs=baseline_runs,
            generated_at="2026-04-10T00:00:00Z",
        )
        self.assertTrue(report.v1_core_gate_passed)
        self.assertTrue(report.leaderboard_gate_passed)
        self.assertEqual(report.public_units, 120)
        self.assertEqual(report.private_units, 30)

    def test_program_progress_summary_reports_missing_gates(self):
        report = summarize_program_progress(
            source_papers=[make_source_paper()],
            paper_decisions=[make_paper_decision()],
            task_bundles=[],
            judge_validation_units=[],
            baseline_runs=[],
            generated_at="2026-04-10T00:00:00Z",
        )
        self.assertFalse(report.v1_core_gate_passed)
        self.assertFalse(report.leaderboard_gate_passed)

    def test_build_judge_validation_slice_creates_non_ready_templates(self):
        task_families = (
            TaskFamily.RESULTS_TO_TEXT,
            TaskFamily.METHODS_TO_TEXT,
            TaskFamily.ABSTRACT_FROM_EVIDENCE,
            TaskFamily.FIGURE_QA,
        )
        task_bundles = [
            make_task_bundle(
                index=index,
                task_family=task_families[(index - 1) % len(task_families)],
                paper_id=f"PMID:{index}",
            )
            for index in range(1, 13)
        ]
        judge_units = build_judge_validation_slice(task_bundles, target_total=8)
        self.assertEqual(len(judge_units), 8)
        selected_task_bundle_ids = {unit.task_bundle_id for unit in judge_units}
        selected_task_families = {
            bundle.task_family
            for bundle in task_bundles
            if bundle.task_bundle_id in selected_task_bundle_ids
        }
        self.assertEqual(selected_task_families, set(task_families))
        self.assertTrue(all(not judge_validation_unit_ready(unit) for unit in judge_units))

    def test_build_judge_validation_slice_respects_holdout_bucket_filter(self):
        task_bundles = [
            make_task_bundle(index=index, holdout_bucket="public" if index <= 2 else "private")
            for index in range(1, 5)
        ]
        judge_units = build_judge_validation_slice(
            task_bundles,
            target_total=2,
            include_holdout_buckets=("public",),
        )
        self.assertEqual(len(judge_units), 2)
        self.assertEqual({unit.task_bundle_id for unit in judge_units}, {"TB:1", "TB:2"})

    def test_summarize_task_bundles_and_select_judge_candidates(self):
        task_bundles = [
            make_task_bundle(
                index=index,
                task_family=(
                    TaskFamily.RESULTS_TO_TEXT
                    if index % 3 == 0
                    else TaskFamily.FIGURE_QA
                    if index % 3 == 1
                    else TaskFamily.TABLE_QA
                ),
                study_class=(
                    StudyClass.MECHANISTIC_EXPERIMENTAL
                    if index % 2
                    else StudyClass.HUMAN_OBSERVATIONAL
                ),
                holdout_bucket="public" if index <= 9 else "private",
            )
            for index in range(1, 13)
        ]
        inventory = summarize_task_bundles(task_bundles)
        self.assertEqual(inventory.total_bundles, 12)
        self.assertEqual(inventory.holdout_bucket_counts["public"], 9)
        selected = select_judge_candidate_task_bundles(task_bundles, target_total=6)
        self.assertEqual(len(selected), 6)
        report = summarize_judge_candidate_selection(selected, target_total=6)
        self.assertEqual(report.selected_total, 6)
        self.assertIn(TaskFamily.RESULTS_TO_TEXT.value, report.task_family_counts)
        self.assertIn(StudyClass.HUMAN_OBSERVATIONAL.value, report.study_class_counts)

    def test_build_shadow_inspection_batch_prefers_unique_papers_and_reports_focus(self):
        papers = {
            f"PMID:{index}": make_source_paper(
                paper_id=f"PMID:{index}",
                title=f"Paper {index}",
                study_class=StudyClass.MECHANISTIC_EXPERIMENTAL if index % 2 else StudyClass.HUMAN_OBSERVATIONAL,
                claim_mode=ClaimMode.RESOURCE_RELEASE if index == 1 else ClaimMode.EXPLORATORY,
                modality_overlays=(ModalityOverlay.PROTEOMICS_MASSSPEC, ModalityOverlay.QPCR)
                if index == 1
                else (),
            )
            for index in range(1, 5)
        }
        task_bundles = [
            make_task_bundle(
                index=1,
                paper_id="PMID:1",
                task_family=TaskFamily.RESULTS_TO_TEXT,
                study_class=papers["PMID:1"].study_class,
                claim_mode=papers["PMID:1"].claim_mode,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
            ),
            make_task_bundle(
                index=2,
                paper_id="PMID:1",
                task_family=TaskFamily.METHODS_TO_TEXT,
                study_class=papers["PMID:1"].study_class,
                claim_mode=papers["PMID:1"].claim_mode,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
            ),
            make_task_bundle(
                index=3,
                paper_id="PMID:2",
                task_family=TaskFamily.ABSTRACT_FROM_EVIDENCE,
                study_class=papers["PMID:2"].study_class,
                claim_mode=papers["PMID:2"].claim_mode,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
            ),
            make_task_bundle(
                index=4,
                paper_id="PMID:3",
                task_family=TaskFamily.RESULTS_TO_TEXT,
                study_class=papers["PMID:3"].study_class,
                claim_mode=papers["PMID:3"].claim_mode,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
            ),
        ]
        auto_records = {
            "PMID:1": AutoQualificationRecord(
                paper_id="PMID:1",
                decision=make_paper_decision(
                    candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                    writing=PaperWritingQualification.W3,
                    public_writing_eligible=False,
                ),
                confidence=AutoReviewConfidence.LOW,
            ),
            "PMID:2": AutoQualificationRecord(
                paper_id="PMID:2",
                decision=make_paper_decision(
                    candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                    writing=PaperWritingQualification.W2,
                    public_writing_eligible=False,
                ),
                confidence=AutoReviewConfidence.MEDIUM,
            ),
            "PMID:3": AutoQualificationRecord(
                paper_id="PMID:3",
                decision=make_paper_decision(
                    candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                    writing=PaperWritingQualification.W1,
                ),
                confidence=AutoReviewConfidence.LOW,
            ),
        }
        source_bundles = {
            "PMID:1": AutoReviewSourceBundle(
                paper_id="PMID:1",
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                abstract_text="abstract",
                methods_text="methods",
                results_text="results",
                figure_captions=("fig1",),
                resource_identifiers=("PXD1",),
            ),
            "PMID:2": AutoReviewSourceBundle(
                paper_id="PMID:2",
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                abstract_text="abstract",
                methods_text="methods",
                results_text="results",
            ),
            "PMID:3": AutoReviewSourceBundle(
                paper_id="PMID:3",
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                abstract_text="abstract",
                methods_text="methods",
                results_text="results",
                table_snippets=("tbl1",),
            ),
        }
        entries = build_shadow_inspection_batch(
            task_bundles=task_bundles,
            papers=papers,
            auto_qualification_records=auto_records,
            source_bundles=source_bundles,
            target_total=3,
            include_holdout_buckets=("public",),
        )
        self.assertEqual(len(entries), 3)
        self.assertEqual(len({entry.paper_id for entry in entries}), 3)
        entry_by_paper = {entry.paper_id: entry for entry in entries}
        self.assertIn("PMID:1", entry_by_paper)
        self.assertIn("low_confidence", entry_by_paper["PMID:1"].focus_tags)
        self.assertIn("hybrid_overlay", entry_by_paper["PMID:1"].focus_tags)
        report = summarize_shadow_inspection_batch(entries, target_total=3)
        self.assertEqual(report.selected_total, 3)
        self.assertEqual(report.focus_tag_counts["low_confidence"], 2)
        markdown = render_shadow_inspection_markdown(entries, report)
        self.assertIn("# Shadow Inspection Batch", markdown)
        self.assertIn("PMID:1", markdown)

    def test_cli_build_shadow_inspection_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            auto_records_path = os.path.join(tmpdir, "auto_records.jsonl")
            source_bundles_path = os.path.join(tmpdir, "source_bundles.jsonl")
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            output_path = os.path.join(tmpdir, "inspection.jsonl")
            summary_path = os.path.join(tmpdir, "inspection_summary.json")
            markdown_path = os.path.join(tmpdir, "inspection.md")

            paper = make_source_paper(paper_id="PMID:1", title="Inspection Paper")
            auto_record = AutoQualificationRecord(
                paper_id=paper.paper_id,
                decision=make_paper_decision(
                    candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                    writing=PaperWritingQualification.W2,
                    public_writing_eligible=False,
                ),
                confidence=AutoReviewConfidence.LOW,
            )
            source_bundle = AutoReviewSourceBundle(
                paper_id=paper.paper_id,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                abstract_text="abstract",
                methods_text="methods",
                results_text="results",
                figure_captions=("fig1",),
            )
            task_bundle = make_task_bundle(
                index=1,
                paper_id=paper.paper_id,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
            )
            write_jsonl(papers_path, [paper])
            write_jsonl(auto_records_path, [auto_record])
            write_jsonl(source_bundles_path, [source_bundle])
            write_jsonl(task_bundles_path, [task_bundle])

            self.assertEqual(
                cli_main(
                    [
                        "build-shadow-inspection-batch",
                        "--task-bundles",
                        task_bundles_path,
                        "--papers",
                        papers_path,
                        "--auto-qualification-records",
                        auto_records_path,
                        "--source-bundles",
                        source_bundles_path,
                        "--output",
                        output_path,
                        "--summary-output",
                        summary_path,
                        "--markdown-output",
                        markdown_path,
                        "--target-total",
                        "1",
                        "--holdout-bucket",
                        "public",
                    ]
                ),
                0,
            )
            entries = load_jsonl(output_path)
            self.assertEqual(len(entries), 1)
            with open(summary_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["selected_total"], 1)
            self.assertTrue(os.path.exists(markdown_path))

    def test_build_shadow_inspection_taxonomy_groups_overlap_categories(self):
        entries = (
            ShadowInspectionEntry(
                inspection_id="INSPECT:001",
                task_bundle_id="TB:1",
                benchmark_unit_id="BU:1",
                paper_id="PMID:1",
                title="Paper 1",
                publication_year=2024,
                task_family=TaskFamily.RESULTS_TO_TEXT,
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.RESOURCE_RELEASE,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W3,
                confidence=AutoReviewConfidence.LOW,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=("low_confidence", "figure_rich", "table_rich", "resource_release_claim"),
                evidence_snapshot={"resource_identifiers": 0, "trial_registry_ids": 0},
                qualification_reasons=(
                    "paper is shadow-ready under auto-only rules",
                    "one or more critical writing domains failed",
                ),
            ),
            ShadowInspectionEntry(
                inspection_id="INSPECT:002",
                task_bundle_id="TB:2",
                benchmark_unit_id="BU:2",
                paper_id="PMID:2",
                title="Paper 2",
                publication_year=2023,
                task_family=TaskFamily.METHODS_TO_TEXT,
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W2,
                confidence=AutoReviewConfidence.MEDIUM,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=("trial_registry", "figure_rich"),
                evidence_snapshot={"resource_identifiers": 0, "trial_registry_ids": 1},
                qualification_reasons=("paper is shadow-ready under auto-only rules",),
            ),
            ShadowInspectionEntry(
                inspection_id="INSPECT:003",
                task_bundle_id="TB:3",
                benchmark_unit_id="BU:3",
                paper_id="PMID:3",
                title="Paper 3",
                publication_year=2022,
                task_family=TaskFamily.ABSTRACT_FROM_EVIDENCE,
                study_class=StudyClass.ANIMAL_PRECLINICAL,
                claim_mode=ClaimMode.EXPLORATORY,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W2,
                confidence=AutoReviewConfidence.MEDIUM,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=(),
                evidence_snapshot={"resource_identifiers": 1, "trial_registry_ids": 0},
                qualification_reasons=("paper is shadow-ready under auto-only rules",),
            ),
        )

        categories = build_shadow_inspection_taxonomy(entries)
        category_ids = [category.category_id for category in categories]
        self.assertIn("low_confidence_shadow", category_ids)
        self.assertIn("writing_quality_risk", category_ids)
        self.assertIn("resource_release_specificity", category_ids)
        self.assertIn("stable_shadow_controls", category_ids)

        report = summarize_shadow_inspection_taxonomy(entries, categories)
        self.assertIsInstance(report, ShadowInspectionTaxonomyReport)
        self.assertEqual(report.total_entries, 3)
        self.assertEqual(report.priority_counts["high"], 4)
        markdown = render_shadow_inspection_taxonomy_markdown(report)
        self.assertIn("# Shadow Inspection Taxonomy", markdown)
        self.assertIn("Low-confidence shadow decisions", markdown)

    def test_build_shadow_inspection_taxonomy_skips_grounded_figure_table_entries(self):
        entries = (
            ShadowInspectionEntry(
                inspection_id="INSPECT:GROUND:001",
                task_bundle_id="TB:GROUND:001",
                benchmark_unit_id="BU:GROUND:001",
                paper_id="PMID:GROUND:001",
                title="Grounded figure entry",
                publication_year=2024,
                task_family=TaskFamily.RESULTS_TO_TEXT,
                study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                claim_mode=ClaimMode.EXPLORATORY,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W2,
                confidence=AutoReviewConfidence.MEDIUM,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=("figure_rich", "figure_grounded", "writing_w2"),
                evidence_snapshot={
                    "figure_captions": 1,
                    "figure_reference_snippets": 1,
                    "resource_identifiers": 0,
                    "trial_registry_ids": 0,
                },
                qualification_reasons=("paper is shadow-ready under auto-only rules",),
            ),
        )
        categories = build_shadow_inspection_taxonomy(entries)
        category_ids = {category.category_id for category in categories}
        self.assertNotIn("figure_table_grounding", category_ids)

    def test_build_shadow_inspection_taxonomy_skips_grounded_trial_registry_entries(self):
        entries = (
            ShadowInspectionEntry(
                inspection_id="INSPECT:TRIAL:001",
                task_bundle_id="TB:TRIAL:001",
                benchmark_unit_id="BU:TRIAL:001",
                paper_id="PMID:TRIAL:001",
                title="Grounded trial registry entry",
                publication_year=2024,
                task_family=TaskFamily.METHODS_TO_TEXT,
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W2,
                confidence=AutoReviewConfidence.MEDIUM,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=("trial_registry", "trial_registry_grounded", "writing_w2"),
                evidence_snapshot={
                    "resource_identifiers": 0,
                    "trial_registry_ids": 1,
                    "trial_registry_reference_snippets": 1,
                },
                qualification_reasons=("paper is shadow-ready under auto-only rules",),
            ),
        )
        categories = build_shadow_inspection_taxonomy(entries)
        category_ids = {category.category_id for category in categories}
        self.assertNotIn("trial_registry_traceability", category_ids)

    def test_build_shadow_inspection_taxonomy_skips_grounded_resource_release_entries(self):
        entries = (
            ShadowInspectionEntry(
                inspection_id="INSPECT:RESOURCE:001",
                task_bundle_id="TB:RESOURCE:001",
                benchmark_unit_id="BU:RESOURCE:001",
                paper_id="PMID:RESOURCE:001",
                title="Grounded resource release entry",
                publication_year=2024,
                task_family=TaskFamily.METHODS_TO_TEXT,
                study_class=StudyClass.METHODS_RESOURCE,
                claim_mode=ClaimMode.RESOURCE_RELEASE,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W2,
                confidence=AutoReviewConfidence.MEDIUM,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=(
                    "resource_release_claim",
                    "resource_release_grounded",
                    "figure_grounded",
                    "writing_w2",
                ),
                evidence_snapshot={
                    "methods_text": 1,
                    "results_text": 1,
                    "figure_captions": 1,
                    "figure_reference_snippets": 1,
                    "resource_identifiers": 0,
                    "trial_registry_ids": 0,
                },
                qualification_reasons=("paper is shadow-ready under auto-only rules",),
            ),
        )
        categories = build_shadow_inspection_taxonomy(entries)
        category_ids = {category.category_id for category in categories}
        self.assertNotIn("resource_release_specificity", category_ids)

    def test_build_shadow_inspection_batch_flags_abstract_inferred_only(self):
        paper = make_source_paper(
            paper_id="PMID:FTGAP:1",
            title="Fulltext-gap paper",
            claim_mode=ClaimMode.RESOURCE_RELEASE,
        )
        auto_record = AutoQualificationRecord(
            paper_id=paper.paper_id,
            decision=make_paper_decision(
                candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                writing=PaperWritingQualification.W2,
                public_writing_eligible=False,
            ),
            confidence=AutoReviewConfidence.LOW,
        )
        source_bundle = AutoReviewSourceBundle(
            paper_id=paper.paper_id,
            bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
            abstract_text="abstract describing a released resource",
            methods_text="abstract describing a released resource",
            results_text="abstract describing a released resource",
            notes=(
                "fetch_error:HTTPError 403",
                "methods inferred from abstract for auto-review bundling",
                "results inferred from abstract for auto-review bundling",
            ),
        )
        task_bundle = make_task_bundle(
            index=1,
            paper_id=paper.paper_id,
            task_family=TaskFamily.METHODS_TO_TEXT,
            study_class=paper.study_class,
            claim_mode=paper.claim_mode,
            release_tier=ReleaseTier.SHADOW_GOLD,
            holdout_bucket="public",
        )
        entries = build_shadow_inspection_batch(
            task_bundles=[task_bundle],
            papers={paper.paper_id: paper},
            auto_qualification_records={paper.paper_id: auto_record},
            source_bundles={paper.paper_id: source_bundle},
            target_total=1,
            include_holdout_buckets=("public",),
        )
        self.assertEqual(len(entries), 1)
        self.assertIn("abstract_inferred_only", entries[0].focus_tags)

    def test_build_shadow_inspection_batch_does_not_flag_abstract_inferred_only_when_identifiers_present(self):
        paper = make_source_paper(
            paper_id="PMID:FTGAP:2",
            claim_mode=ClaimMode.RESOURCE_RELEASE,
        )
        auto_record = AutoQualificationRecord(
            paper_id=paper.paper_id,
            decision=make_paper_decision(
                candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                writing=PaperWritingQualification.W2,
                public_writing_eligible=False,
            ),
            confidence=AutoReviewConfidence.LOW,
        )
        source_bundle = AutoReviewSourceBundle(
            paper_id=paper.paper_id,
            bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
            abstract_text="abstract describing a released resource",
            methods_text="abstract describing a released resource",
            results_text="abstract describing a released resource",
            resource_identifiers=("PXD999999",),
            notes=(
                "fetch_error:HTTPError 403",
                "methods inferred from abstract for auto-review bundling",
            ),
        )
        task_bundle = make_task_bundle(
            index=1,
            paper_id=paper.paper_id,
            task_family=TaskFamily.METHODS_TO_TEXT,
            study_class=paper.study_class,
            claim_mode=paper.claim_mode,
            release_tier=ReleaseTier.SHADOW_GOLD,
            holdout_bucket="public",
        )
        entries = build_shadow_inspection_batch(
            task_bundles=[task_bundle],
            papers={paper.paper_id: paper},
            auto_qualification_records={paper.paper_id: auto_record},
            source_bundles={paper.paper_id: source_bundle},
            target_total=1,
            include_holdout_buckets=("public",),
        )
        self.assertEqual(len(entries), 1)
        self.assertNotIn("abstract_inferred_only", entries[0].focus_tags)

    def test_build_shadow_inspection_taxonomy_emits_fulltext_acquisition_gap(self):
        entries = (
            ShadowInspectionEntry(
                inspection_id="INSPECT:FTGAP:001",
                task_bundle_id="TB:FTGAP:001",
                benchmark_unit_id="BU:FTGAP:001",
                paper_id="PMID:FTGAP:001",
                title="Full-text gap entry",
                publication_year=2024,
                task_family=TaskFamily.METHODS_TO_TEXT,
                study_class=StudyClass.METHODS_RESOURCE,
                claim_mode=ClaimMode.RESOURCE_RELEASE,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W2,
                confidence=AutoReviewConfidence.LOW,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=(
                    "low_confidence",
                    "writing_w2",
                    "resource_release_claim",
                    "abstract_inferred_only",
                ),
                evidence_snapshot={
                    "abstract_text": 1,
                    "methods_text": 1,
                    "results_text": 1,
                    "figure_captions": 0,
                    "table_snippets": 0,
                    "resource_identifiers": 0,
                    "trial_registry_ids": 0,
                },
                qualification_reasons=("paper is shadow-ready under auto-only rules",),
                source_bundle_notes=(
                    "fetch_error:HTTPError 403",
                    "methods inferred from abstract for auto-review bundling",
                ),
            ),
        )
        categories = build_shadow_inspection_taxonomy(entries)
        category_ids = {category.category_id for category in categories}
        self.assertIn("fulltext_acquisition_gap", category_ids)
        self.assertNotIn("resource_release_specificity", category_ids)
        gap_category = next(
            category for category in categories if category.category_id == "fulltext_acquisition_gap"
        )
        self.assertEqual(gap_category.priority, "high")
        self.assertEqual(gap_category.entry_count, 1)

    def test_build_shadow_inspection_batch_flags_blocked_upstream_on_http_4xx(self):
        paper = make_source_paper(
            paper_id="PMID:FTGAP:BLOCKED:1",
            title="Non-OA paper with 404 from OA service",
            claim_mode=ClaimMode.RESOURCE_RELEASE,
        )
        auto_record = AutoQualificationRecord(
            paper_id=paper.paper_id,
            decision=make_paper_decision(
                candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                writing=PaperWritingQualification.W2,
                public_writing_eligible=False,
            ),
            confidence=AutoReviewConfidence.LOW,
        )
        source_bundle = AutoReviewSourceBundle(
            paper_id=paper.paper_id,
            bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
            abstract_text="abstract describing a non-OA resource",
            methods_text="abstract describing a non-OA resource",
            results_text="abstract describing a non-OA resource",
            notes=(
                "fetch_error:HTTP Error 404: Not Found",
                "methods inferred from abstract for auto-review bundling",
                "results inferred from abstract for auto-review bundling",
            ),
        )
        task_bundle = make_task_bundle(
            index=1,
            paper_id=paper.paper_id,
            task_family=TaskFamily.METHODS_TO_TEXT,
            study_class=paper.study_class,
            claim_mode=paper.claim_mode,
            release_tier=ReleaseTier.SHADOW_GOLD,
            holdout_bucket="public",
        )
        entries = build_shadow_inspection_batch(
            task_bundles=[task_bundle],
            papers={paper.paper_id: paper},
            auto_qualification_records={paper.paper_id: auto_record},
            source_bundles={paper.paper_id: source_bundle},
            target_total=1,
            include_holdout_buckets=("public",),
        )
        self.assertEqual(len(entries), 1)
        self.assertIn("abstract_inferred_only", entries[0].focus_tags)
        self.assertIn("fulltext_acquisition_blocked_upstream", entries[0].focus_tags)
        categories = build_shadow_inspection_taxonomy(entries)
        category_ids = {category.category_id for category in categories}
        self.assertIn("fulltext_acquisition_gap", category_ids)
        self.assertIn("fulltext_acquisition_blocked_upstream", category_ids)

    def test_build_shadow_inspection_batch_does_not_flag_blocked_upstream_on_transient_error(self):
        paper = make_source_paper(
            paper_id="PMID:FTGAP:TRANSIENT:1",
            title="Paper whose enrichment hit a DNS error",
            claim_mode=ClaimMode.RESOURCE_RELEASE,
        )
        auto_record = AutoQualificationRecord(
            paper_id=paper.paper_id,
            decision=make_paper_decision(
                candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                writing=PaperWritingQualification.W2,
                public_writing_eligible=False,
            ),
            confidence=AutoReviewConfidence.LOW,
        )
        source_bundle = AutoReviewSourceBundle(
            paper_id=paper.paper_id,
            bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
            abstract_text="abstract describing a released resource",
            methods_text="abstract describing a released resource",
            results_text="abstract describing a released resource",
            notes=(
                "fetch_error:<urlopen error [Errno 8] nodename nor servname provided, or not known>",
                "methods inferred from abstract for auto-review bundling",
            ),
        )
        task_bundle = make_task_bundle(
            index=1,
            paper_id=paper.paper_id,
            task_family=TaskFamily.METHODS_TO_TEXT,
            study_class=paper.study_class,
            claim_mode=paper.claim_mode,
            release_tier=ReleaseTier.SHADOW_GOLD,
            holdout_bucket="public",
        )
        entries = build_shadow_inspection_batch(
            task_bundles=[task_bundle],
            papers={paper.paper_id: paper},
            auto_qualification_records={paper.paper_id: auto_record},
            source_bundles={paper.paper_id: source_bundle},
            target_total=1,
            include_holdout_buckets=("public",),
        )
        self.assertEqual(len(entries), 1)
        self.assertIn("abstract_inferred_only", entries[0].focus_tags)
        self.assertNotIn("fulltext_acquisition_blocked_upstream", entries[0].focus_tags)
        categories = build_shadow_inspection_taxonomy(entries)
        category_ids = {category.category_id for category in categories}
        self.assertIn("fulltext_acquisition_gap", category_ids)
        self.assertNotIn("fulltext_acquisition_blocked_upstream", category_ids)

    def test_build_shadow_inspection_taxonomy_suppresses_identifier_sparse_when_fulltext_gap(self):
        gap_entry = ShadowInspectionEntry(
            inspection_id="INSPECT:FTGAP:ID:001",
            task_bundle_id="TB:FTGAP:ID:001",
            benchmark_unit_id="BU:FTGAP:ID:001",
            paper_id="PMID:FTGAP:ID:001",
            title="Identifier-sparse entry with full-text gap",
            publication_year=2024,
            task_family=TaskFamily.METHODS_TO_TEXT,
            study_class=StudyClass.HUMAN_OBSERVATIONAL,
            claim_mode=ClaimMode.DESCRIPTIVE,
            release_tier=ReleaseTier.SHADOW_GOLD,
            holdout_bucket="public",
            writing=PaperWritingQualification.W3,
            confidence=AutoReviewConfidence.LOW,
            bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
            focus_tags=("low_confidence", "writing_w3", "abstract_inferred_only"),
            evidence_snapshot={
                "abstract_text": 1,
                "methods_text": 1,
                "results_text": 1,
                "figure_captions": 0,
                "table_snippets": 0,
                "resource_identifiers": 0,
                "trial_registry_ids": 0,
            },
            qualification_reasons=("paper is shadow-ready under auto-only rules",),
            source_bundle_notes=(
                "fetch_error:HTTPError 403",
                "methods inferred from abstract for auto-review bundling",
                "results inferred from abstract for auto-review bundling",
            ),
        )
        genuine_entry = ShadowInspectionEntry(
            inspection_id="INSPECT:ID:ONLY:001",
            task_bundle_id="TB:ID:ONLY:001",
            benchmark_unit_id="BU:ID:ONLY:001",
            paper_id="PMID:ID:ONLY:001",
            title="Genuine identifier-sparse entry without fetch errors",
            publication_year=2024,
            task_family=TaskFamily.METHODS_TO_TEXT,
            study_class=StudyClass.HUMAN_OBSERVATIONAL,
            claim_mode=ClaimMode.DESCRIPTIVE,
            release_tier=ReleaseTier.SHADOW_GOLD,
            holdout_bucket="public",
            writing=PaperWritingQualification.W2,
            confidence=AutoReviewConfidence.LOW,
            bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
            focus_tags=("low_confidence", "writing_w2", "figure_rich", "figure_grounded"),
            evidence_snapshot={
                "abstract_text": 1,
                "methods_text": 1,
                "results_text": 1,
                "figure_captions": 2,
                "figure_reference_snippets": 2,
                "resource_identifiers": 0,
                "trial_registry_ids": 0,
            },
            qualification_reasons=("paper is shadow-ready under auto-only rules",),
            source_bundle_notes=(),
        )
        categories = build_shadow_inspection_taxonomy((gap_entry, genuine_entry))
        category_entries = {
            category.category_id: category.entry_count for category in categories
        }
        self.assertEqual(category_entries.get("fulltext_acquisition_gap"), 1)
        self.assertEqual(category_entries.get("identifier_sparse_low_confidence"), 1)
        identifier_sparse = next(
            category for category in categories if category.category_id == "identifier_sparse_low_confidence"
        )
        self.assertEqual(identifier_sparse.representative_inspection_ids, ("INSPECT:ID:ONLY:001",))

    def test_cli_summarize_shadow_inspection_taxonomy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries_path = os.path.join(tmpdir, "inspection.jsonl")
            output_path = os.path.join(tmpdir, "taxonomy.json")
            markdown_path = os.path.join(tmpdir, "taxonomy.md")
            entries = [
                ShadowInspectionEntry(
                    inspection_id="INSPECT:001",
                    task_bundle_id="TB:1",
                    benchmark_unit_id="BU:1",
                    paper_id="PMID:1",
                    title="Paper 1",
                    publication_year=2024,
                    task_family=TaskFamily.RESULTS_TO_TEXT,
                    study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                    claim_mode=ClaimMode.EXPLORATORY,
                    release_tier=ReleaseTier.SHADOW_GOLD,
                    holdout_bucket="public",
                    writing=PaperWritingQualification.W2,
                    confidence=AutoReviewConfidence.LOW,
                    bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                    focus_tags=("low_confidence", "figure_rich"),
                    evidence_snapshot={"resource_identifiers": 0, "trial_registry_ids": 0},
                    qualification_reasons=("paper is shadow-ready under auto-only rules",),
                )
            ]
            write_jsonl(entries_path, entries)
            self.assertEqual(
                cli_main(
                    [
                        "summarize-shadow-inspection-taxonomy",
                        "--inspection-entries",
                        entries_path,
                        "--output",
                        output_path,
                        "--markdown-output",
                        markdown_path,
                    ]
                ),
                0,
            )
            with open(output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["total_entries"], 1)
            self.assertGreaterEqual(payload["category_count"], 1)
            self.assertTrue(os.path.exists(markdown_path))

    def test_compare_shadow_inspection_reports_and_cli(self):
        previous_entries = (
            ShadowInspectionEntry(
                inspection_id="INSPECT:001",
                task_bundle_id="TB:1",
                benchmark_unit_id="BU:1",
                paper_id="PMID:1",
                title="Paper 1",
                publication_year=2024,
                task_family=TaskFamily.RESULTS_TO_TEXT,
                study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                claim_mode=ClaimMode.EXPLORATORY,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W2,
                confidence=AutoReviewConfidence.LOW,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=("low_confidence", "figure_rich"),
                evidence_snapshot={"resource_identifiers": 0, "trial_registry_ids": 0},
                qualification_reasons=("paper is shadow-ready under auto-only rules",),
            ),
        )
        current_entries = (
            ShadowInspectionEntry(
                inspection_id="INSPECT:001",
                task_bundle_id="TB:1",
                benchmark_unit_id="BU:1",
                paper_id="PMID:1",
                title="Paper 1",
                publication_year=2024,
                task_family=TaskFamily.RESULTS_TO_TEXT,
                study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                claim_mode=ClaimMode.EXPLORATORY,
                release_tier=ReleaseTier.SHADOW_GOLD,
                holdout_bucket="public",
                writing=PaperWritingQualification.W1,
                confidence=AutoReviewConfidence.MEDIUM,
                bundle_completeness=AutoReviewBundleCompleteness.REVIEW_READY,
                focus_tags=("figure_rich", "resource_ids"),
                evidence_snapshot={"resource_identifiers": 1, "trial_registry_ids": 0},
                qualification_reasons=("paper is shadow-ready under auto-only rules",),
            ),
        )
        previous_report = summarize_shadow_inspection_batch(previous_entries, target_total=1)
        current_report = summarize_shadow_inspection_batch(current_entries, target_total=1)
        previous_taxonomy = summarize_shadow_inspection_taxonomy(
            previous_entries,
            build_shadow_inspection_taxonomy(previous_entries),
        )
        current_taxonomy = summarize_shadow_inspection_taxonomy(
            current_entries,
            build_shadow_inspection_taxonomy(current_entries),
        )
        delta = compare_shadow_inspection_reports(
            previous_report,
            current_report,
            previous_taxonomy,
            current_taxonomy,
            previous_label="v1",
            current_label="v2",
        )
        self.assertEqual(delta.previous_label, "v1")
        self.assertEqual(delta.current_label, "v2")
        self.assertEqual(delta.focus_tag_delta["resource_ids"], 1)
        self.assertEqual(delta.confidence_count_delta["low"], -1)
        self.assertIn("inspection slice gained 1 entries with resource identifiers", delta.notes)

        with tempfile.TemporaryDirectory() as tmpdir:
            prev_summary_path = os.path.join(tmpdir, "prev_summary.json")
            curr_summary_path = os.path.join(tmpdir, "curr_summary.json")
            prev_taxonomy_path = os.path.join(tmpdir, "prev_taxonomy.json")
            curr_taxonomy_path = os.path.join(tmpdir, "curr_taxonomy.json")
            output_path = os.path.join(tmpdir, "delta.json")
            Path(prev_summary_path).write_text(json.dumps(previous_report.to_dict()), encoding="utf-8")
            Path(curr_summary_path).write_text(json.dumps(current_report.to_dict()), encoding="utf-8")
            Path(prev_taxonomy_path).write_text(json.dumps(previous_taxonomy.to_dict()), encoding="utf-8")
            Path(curr_taxonomy_path).write_text(json.dumps(current_taxonomy.to_dict()), encoding="utf-8")
            self.assertEqual(
                cli_main(
                    [
                        "compare-shadow-inspection-runs",
                        "--previous-summary",
                        prev_summary_path,
                        "--current-summary",
                        curr_summary_path,
                        "--previous-taxonomy",
                        prev_taxonomy_path,
                        "--current-taxonomy",
                        curr_taxonomy_path,
                        "--previous-label",
                        "v1",
                        "--current-label",
                        "v2",
                        "--output",
                        output_path,
                    ]
                ),
                0,
            )
            with open(output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["previous_label"], "v1")
            self.assertEqual(payload["current_label"], "v2")

    def test_audit_judge_validation_slice_passes_for_ready_units(self):
        task_bundles = [
            make_task_bundle(
                index=index,
                task_family=TaskFamily.FIGURE_QA if index % 2 else TaskFamily.RESULTS_TO_TEXT,
                study_class=StudyClass.MECHANISTIC_EXPERIMENTAL if index % 3 else StudyClass.HUMAN_OBSERVATIONAL,
                release_tier=ReleaseTier.PUBLIC_GOLD if index <= 20 else ReleaseTier.SHADOW_GOLD,
                paper_id=f"PMID:{index}",
            )
            for index in range(1, 31)
        ]
        judge_units = [
            JudgeValidationUnit(
                validation_unit_id=f"JV:TB:{index}",
                task_bundle_id=f"TB:{index}",
                human_adjudicated=True,
                rubric_labels={
                    "evidence_fidelity": 1.0,
                    "traceability": 1.0,
                    "provenance_completeness": 1.0,
                    "writing_structure_compliance": 1.0,
                },
                frozen=True,
                adjudicator_id="adj-1",
            )
            for index in range(1, 31)
        ]
        report = audit_judge_validation_slice(task_bundles, judge_units)
        self.assertTrue(report.ok)
        self.assertEqual(report.ready_units, 30)
        self.assertEqual(report.human_adjudicated_units, 30)
        self.assertEqual(report.frozen_units, 30)
        loaded = judge_slice_audit_report_from_dict(report.to_dict())
        self.assertTrue(loaded.ok)
        self.assertEqual(loaded.task_family_counts[TaskFamily.FIGURE_QA.value], 15)

    def test_audit_judge_validation_slice_detects_missing_axes_duplicates_and_missing_bundle(self):
        task_bundles = [make_task_bundle(index=1)]
        judge_units = [
            JudgeValidationUnit(
                validation_unit_id="JV:1",
                task_bundle_id="TB:1",
                human_adjudicated=True,
                rubric_labels={"evidence_fidelity": 1.0},
                frozen=False,
            ),
            JudgeValidationUnit(
                validation_unit_id="JV:1",
                task_bundle_id="TB:missing",
                human_adjudicated=False,
                rubric_labels={},
                frozen=False,
            ),
        ]
        report = audit_judge_validation_slice(task_bundles, judge_units, minimum_total=2)
        self.assertFalse(report.ok)
        self.assertIn("judge validation slice references unknown task bundles", report.issues)
        self.assertIn("judge validation slice contains duplicate validation_unit_id values", report.issues)
        self.assertIn("JV:1", report.missing_rubric_axes)
        self.assertEqual(report.missing_task_bundle_ids, ("TB:missing",))

    def test_program_progress_counts_only_ready_judge_units(self):
        papers = [make_source_paper(paper_id=f"PMID:{index}") for index in range(180)]
        paper_decisions = [make_paper_decision() for _ in range(180)]
        task_bundles = [
            make_task_bundle(
                index=index,
                task_family=TaskFamily.LITERATURE_QA if index % 2 else TaskFamily.RESULTS_TO_TEXT,
                paper_id=f"PMID:{index % 180}",
                holdout_bucket="public" if index < 120 else "private",
            )
            for index in range(150)
        ]
        blank_judge_units = build_judge_validation_slice(task_bundles, target_total=30)
        baseline_runs = [
            BaselineRunSpec(baseline_id="baseline-reference", baseline_kind=BaselineKind.REFERENCE_TEMPLATE, replay_verified=True),
            BaselineRunSpec(baseline_id="baseline-retrieval", baseline_kind=BaselineKind.RETRIEVAL_WRITER, replay_verified=True),
            BaselineRunSpec(baseline_id="baseline-section", baseline_kind=BaselineKind.SECTION_WISE_PIPELINE, replay_verified=True),
            BaselineRunSpec(baseline_id="baseline-single-agent", baseline_kind=BaselineKind.SINGLE_AGENT_WRITER, replay_verified=True),
            BaselineRunSpec(baseline_id="baseline-multi-agent", baseline_kind=BaselineKind.MULTI_AGENT_ORCHESTRATION, replay_verified=True),
        ]
        report = summarize_program_progress(
            source_papers=papers,
            paper_decisions=paper_decisions,
            task_bundles=task_bundles,
            judge_validation_units=blank_judge_units,
            baseline_runs=baseline_runs,
            generated_at="2026-04-10T00:00:00Z",
        )
        self.assertEqual(report.judge_validation_units, 0)
        self.assertFalse(report.leaderboard_gate_passed)

    def test_program_progress_accepts_auto_qualification_records(self):
        paper = make_source_paper()
        task_bundle = make_task_bundle(index=1, paper_id=paper.paper_id, holdout_bucket="public")
        auto_record = AutoQualificationRecord(
            paper_id=paper.paper_id,
            decision=make_paper_decision(
                candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                eligible_for_unit_extraction=True,
            ),
        )
        report = summarize_program_progress(
            source_papers=[paper],
            paper_decisions=[auto_record],
            task_bundles=[task_bundle],
            baseline_runs=[
                BaselineRunSpec(
                    baseline_id="baseline-reference",
                    baseline_kind=BaselineKind.REFERENCE_TEMPLATE,
                    replay_verified=True,
                )
            ],
            generated_at="2026-04-10T00:00:00Z",
        )
        self.assertEqual(report.paper_qualified, 1)
        self.assertEqual(report.public_units, 1)
        self.assertEqual(report.replayable_baselines, 1)

    def test_cli_build_and_audit_judge_slice(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            task_bundles = [
                make_task_bundle(
                    index=index,
                    task_family=TaskFamily.TABLE_QA if index % 2 else TaskFamily.RESULTS_TO_TEXT,
                    paper_id=f"PMID:{index}",
                )
                for index in range(1, 31)
            ]
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            judge_units_path = os.path.join(tmpdir, "judge_units.jsonl")
            audit_output_path = os.path.join(tmpdir, "judge_audit.json")
            write_jsonl(task_bundles_path, task_bundles)
            exit_code = cli_main(
                [
                    "build-judge-slice",
                    "--task-bundles",
                    task_bundles_path,
                    "--output",
                    judge_units_path,
                    "--target-total",
                    "30",
                ]
            )
            self.assertEqual(exit_code, 0)
            judge_units_payload = load_jsonl(judge_units_path)
            self.assertEqual(len(judge_units_payload), 30)
            for unit in judge_units_payload:
                unit["human_adjudicated"] = True
                unit["frozen"] = True
                unit["adjudicator_id"] = "adj-1"
                unit["rubric_labels"] = {
                    "evidence_fidelity": 1.0,
                    "traceability": 1.0,
                    "provenance_completeness": 1.0,
                    "writing_structure_compliance": 1.0,
                }
            _ = write_jsonl(judge_units_path, [judge_validation_unit_from_dict(unit) for unit in judge_units_payload])
            exit_code = cli_main(
                [
                    "audit-judge-slice",
                    "--task-bundles",
                    task_bundles_path,
                    "--judge-units",
                    judge_units_path,
                    "--output",
                    audit_output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            with open(audit_output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["ready_units"], 30)

    def test_judge_review_workflow_build_merge_queue_and_finalize(self):
        judge_units = build_judge_validation_slice(
            [
                make_task_bundle(index=1, task_family=TaskFamily.RESULTS_TO_TEXT),
                make_task_bundle(index=2, task_family=TaskFamily.FIGURE_QA),
            ],
            target_total=2,
        )
        forms = build_judge_review_forms(judge_units, reviewer_ids=("rev_a", "rev_b"))
        self.assertEqual(len(forms), 4)
        self.assertEqual(forms[0].rubric_labels["evidence_fidelity"], None)
        deduped = merge_judge_review_forms(
            forms
            + (
                judge_review_form_from_dict(
                    {
                        "validation_unit_id": judge_units[0].validation_unit_id,
                        "reviewer_id": "rev_a",
                        "completed": True,
                        "rubric_labels": {
                            "evidence_fidelity": 1.0,
                            "traceability": 1.0,
                            "provenance_completeness": 1.0,
                            "writing_structure_compliance": 1.0,
                        },
                        "confidence": 5,
                    }
                ),
            )
        )
        self.assertEqual(len(deduped), 4)
        adjudications = build_judge_adjudication_shells(
            judge_units,
            adjudicator_id="adj_1",
            reviewer_ids=("rev_a", "rev_b"),
        )
        queue = build_judge_adjudication_queue(
            judge_units,
            deduped,
            adjudications,
            reviewer_ids=("rev_a", "rev_b"),
        )
        self.assertEqual(queue[0].status, "awaiting_reviews")
        queue_entry = judge_adjudication_queue_entry_from_dict(queue[0].to_dict())
        self.assertEqual(queue_entry.validation_unit_id, judge_units[0].validation_unit_id)

        finalized_adjudications = [
            judge_adjudication_record_from_dict(
                {
                    "validation_unit_id": judge_units[0].validation_unit_id,
                    "adjudicator_id": "adj_1",
                    "finalized": True,
                    "final_rubric_labels": {
                        "evidence_fidelity": 1.0,
                        "traceability": 1.0,
                        "provenance_completeness": 1.0,
                        "writing_structure_compliance": 1.0,
                    },
                    "source_reviewer_ids": ["rev_a", "rev_b"],
                }
            )
        ]
        finalized_units = finalize_judge_validation_units(judge_units, finalized_adjudications)
        self.assertTrue(finalized_units[0].human_adjudicated)
        self.assertTrue(finalized_units[0].frozen)
        self.assertEqual(finalized_units[0].adjudicator_id, "adj_1")
        self.assertFalse(finalized_units[1].human_adjudicated)

    def test_cli_build_and_finalize_judge_review_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            task_bundles = [
                make_task_bundle(index=1, task_family=TaskFamily.RESULTS_TO_TEXT),
                make_task_bundle(index=2, task_family=TaskFamily.FIGURE_QA),
            ]
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            judge_units_path = os.path.join(tmpdir, "judge_units.jsonl")
            forms_path = os.path.join(tmpdir, "judge_forms.jsonl")
            adjudications_path = os.path.join(tmpdir, "judge_adjudications.jsonl")
            queue_path = os.path.join(tmpdir, "judge_queue.jsonl")
            finalized_path = os.path.join(tmpdir, "judge_units_finalized.jsonl")
            write_jsonl(task_bundles_path, task_bundles)

            self.assertEqual(
                cli_main(
                    [
                        "build-judge-slice",
                        "--task-bundles",
                        task_bundles_path,
                        "--output",
                        judge_units_path,
                        "--target-total",
                        "2",
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-judge-review-templates",
                        "--judge-units",
                        judge_units_path,
                        "--forms-output",
                        forms_path,
                        "--adjudication-output",
                        adjudications_path,
                        "--adjudicator",
                        "adj_1",
                        "--reviewers",
                        "rev_a",
                        "rev_b",
                    ]
                ),
                0,
            )
            forms_payload = load_jsonl(forms_path)
            forms_payload[0]["completed"] = True
            forms_payload[0]["rubric_labels"] = {
                "evidence_fidelity": 1.0,
                "traceability": 1.0,
                "provenance_completeness": 1.0,
                "writing_structure_compliance": 1.0,
            }
            write_jsonl(forms_path, [judge_review_form_from_dict(item) for item in forms_payload])

            self.assertEqual(
                cli_main(
                    [
                        "build-judge-adjudication-queue",
                        "--judge-units",
                        judge_units_path,
                        "--forms",
                        forms_path,
                        "--adjudications",
                        adjudications_path,
                        "--reviewers",
                        "rev_a",
                        "rev_b",
                        "--output",
                        queue_path,
                    ]
                ),
                0,
            )
            queue_entries = load_jsonl(queue_path)
            self.assertEqual(queue_entries[0]["status"], "awaiting_reviews")

            adjudications_payload = load_jsonl(adjudications_path)
            adjudications_payload[0]["finalized"] = True
            adjudications_payload[0]["final_rubric_labels"] = {
                "evidence_fidelity": 1.0,
                "traceability": 1.0,
                "provenance_completeness": 1.0,
                "writing_structure_compliance": 1.0,
            }
            write_jsonl(
                adjudications_path,
                [judge_adjudication_record_from_dict(item) for item in adjudications_payload],
            )
            self.assertEqual(
                cli_main(
                    [
                        "finalize-judge-slice",
                        "--judge-units",
                        judge_units_path,
                        "--adjudications",
                        adjudications_path,
                        "--output",
                        finalized_path,
                    ]
                ),
                0,
            )
            finalized_units = load_jsonl(finalized_path, loader=judge_validation_unit_from_dict)
            self.assertTrue(finalized_units[0].human_adjudicated)
            self.assertTrue(finalized_units[0].frozen)

    def test_cli_build_judge_batch_and_summarize_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            task_bundles = [
                make_task_bundle(index=index, task_family=TaskFamily.FIGURE_QA if index % 2 else TaskFamily.RESULTS_TO_TEXT)
                for index in range(1, 7)
            ]
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            batch_dir = os.path.join(tmpdir, "judge_batch")
            summary_path = os.path.join(tmpdir, "judge_progress.json")
            write_jsonl(task_bundles_path, task_bundles)

            self.assertEqual(
                cli_main(
                    [
                        "build-judge-batch",
                        "--task-bundles",
                        task_bundles_path,
                        "--output-dir",
                        batch_dir,
                        "--target-total",
                        "6",
                        "--adjudicator",
                        "adj_1",
                        "--reviewers",
                        "rev_a",
                        "rev_b",
                    ]
                ),
                0,
            )
            judge_units_path = os.path.join(batch_dir, "judge_units.jsonl")
            forms_path = os.path.join(batch_dir, "judge_review_forms.jsonl")
            adjudications_path = os.path.join(batch_dir, "judge_adjudications.jsonl")
            selected_bundles_path = os.path.join(batch_dir, "selected_task_bundles.jsonl")
            selection_summary_path = os.path.join(batch_dir, "judge_candidate_selection.json")
            self.assertTrue(os.path.exists(judge_units_path))
            self.assertTrue(os.path.exists(forms_path))
            self.assertTrue(os.path.exists(adjudications_path))
            self.assertTrue(os.path.exists(selected_bundles_path))
            self.assertTrue(os.path.exists(selection_summary_path))

            forms_payload = load_jsonl(forms_path)
            for item in forms_payload[:2]:
                item["completed"] = True
                item["rubric_labels"] = {
                    "evidence_fidelity": 1.0,
                    "traceability": 1.0,
                    "provenance_completeness": 1.0,
                    "writing_structure_compliance": 1.0,
                }
            write_jsonl(forms_path, [judge_review_form_from_dict(item) for item in forms_payload])

            self.assertEqual(
                cli_main(
                    [
                        "summarize-judge-progress",
                        "--task-bundles",
                        task_bundles_path,
                        "--judge-units",
                        judge_units_path,
                        "--forms",
                        forms_path,
                        "--adjudications",
                        adjudications_path,
                        "--reviewers",
                        "rev_a",
                        "rev_b",
                        "--minimum-total",
                        "6",
                        "--output",
                        summary_path,
                    ]
                ),
                0,
            )
            with open(summary_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertIn("slice_audit", payload)
            self.assertIn("progress_summary", payload)
            self.assertEqual(payload["progress_summary"]["total_judge_units"], 6)
            self.assertEqual(payload["progress_summary"]["review_slots_completed"], 2)

    def test_cli_build_judge_batch_respects_holdout_filter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            task_bundles = [
                make_task_bundle(
                    index=index,
                    task_family=TaskFamily.FIGURE_QA if index % 2 else TaskFamily.RESULTS_TO_TEXT,
                    holdout_bucket="public" if index <= 4 else "private",
                )
                for index in range(1, 7)
            ]
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            batch_dir = os.path.join(tmpdir, "judge_batch_public")
            write_jsonl(task_bundles_path, task_bundles)

            self.assertEqual(
                cli_main(
                    [
                        "build-judge-batch",
                        "--task-bundles",
                        task_bundles_path,
                        "--output-dir",
                        batch_dir,
                        "--target-total",
                        "4",
                        "--holdout-bucket",
                        "public",
                        "--adjudicator",
                        "adj_1",
                        "--reviewers",
                        "rev_a",
                        "rev_b",
                    ]
                ),
                0,
            )
            selected_bundles = load_jsonl(
                os.path.join(batch_dir, "selected_task_bundles.jsonl"),
                loader=task_bundle_from_dict,
            )
            self.assertEqual(len(selected_bundles), 4)
            self.assertTrue(all(bundle.holdout_bucket == "public" for bundle in selected_bundles))

    def test_cli_summarize_task_bundles_and_select_judge_candidates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            task_bundles = [
                make_task_bundle(
                    index=index,
                    task_family=TaskFamily.RESULTS_TO_TEXT if index % 2 else TaskFamily.FIGURE_QA,
                    holdout_bucket="public" if index <= 8 else "private",
                )
                for index in range(1, 11)
            ]
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            summary_path = os.path.join(tmpdir, "task_bundle_summary.json")
            selected_path = os.path.join(tmpdir, "judge_candidates.jsonl")
            selection_summary_path = os.path.join(tmpdir, "judge_candidates_summary.json")
            write_jsonl(task_bundles_path, task_bundles)

            self.assertEqual(
                cli_main(
                    [
                        "summarize-task-bundles",
                        "--task-bundles",
                        task_bundles_path,
                        "--output",
                        summary_path,
                    ]
                ),
                0,
            )
            with open(summary_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["total_bundles"], 10)
            self.assertEqual(payload["holdout_bucket_counts"]["public"], 8)

            self.assertEqual(
                cli_main(
                    [
                        "select-judge-candidates",
                        "--task-bundles",
                        task_bundles_path,
                        "--output",
                        selected_path,
                        "--summary-output",
                        selection_summary_path,
                        "--target-total",
                        "4",
                        "--holdout-bucket",
                        "public",
                    ]
                ),
                0,
            )
            selected = load_jsonl(selected_path, loader=task_bundle_from_dict)
            self.assertEqual(len(selected), 4)
            self.assertTrue(all(bundle.holdout_bucket == "public" for bundle in selected))
            with open(selection_summary_path, "r", encoding="utf-8") as handle:
                selection_payload = json.load(handle)
            self.assertEqual(selection_payload["selected_total"], 4)

    def test_cli_validate_pilot_writes_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "pilot_summary.json")
            exit_code = cli_main(
                [
                    "validate-pilot",
                    "--manifest",
                    os.path.join(ROOT, "calibration", "pilot_v1", "pilot_manifest.jsonl"),
                    "--output",
                    output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["summary"]["total_specs"], 12)

    def test_cli_suggest_metadata_hints(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            hints_path = os.path.join(tmpdir, "hints.jsonl")
            summary_path = os.path.join(tmpdir, "summary.json")
            write_jsonl(
                papers_path,
                [
                    make_source_paper(
                        title="Randomized placebo-controlled biomarker trial",
                        metadata={
                            "article_type": "Randomized clinical trial",
                            "trial_registration": "NCT01234567",
                            "keywords": "placebo, primary endpoint, biomarker",
                        },
                    )
                ],
            )
            exit_code = cli_main(
                [
                    "suggest-metadata-hints",
                    "--papers",
                    papers_path,
                    "--output",
                    hints_path,
                    "--summary-output",
                    summary_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            hints = load_jsonl(hints_path, loader=metadata_governance_hint_from_dict)
            self.assertEqual(len(hints), 1)
            self.assertIn(StandardId.CONSORT_2025, hints[0].suggested_required_standards)
            with open(summary_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["papers_processed"], 1)

    def test_cli_build_pilot_templates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            forms_path = os.path.join(tmpdir, "forms.jsonl")
            adjudications_path = os.path.join(tmpdir, "adjudications.jsonl")
            exit_code = cli_main(
                [
                    "build-pilot-templates",
                    "--manifest",
                    os.path.join(ROOT, "calibration", "pilot_v1", "pilot_manifest.jsonl"),
                    "--forms-output",
                    forms_path,
                    "--adjudication-output",
                    adjudications_path,
                    "--adjudicator",
                    "adj-1",
                    "--reviewers",
                    "reviewer_a",
                    "reviewer_b",
                ]
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(load_jsonl(forms_path)), 24)
            self.assertEqual(len(load_jsonl(adjudications_path)), 12)

    def test_cli_summarize_pilot_agreement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            forms_path = os.path.join(tmpdir, "forms.jsonl")
            adjudications_path = os.path.join(tmpdir, "adjudications.jsonl")
            output_path = os.path.join(tmpdir, "agreement.json")
            write_jsonl(
                forms_path,
                [
                    PilotReviewForm(
                        calibration_id="pilot-01",
                        reviewer_id="reviewer_a",
                        study_class=StudyClass.HUMAN_INTERVENTIONAL,
                        claim_mode=ClaimMode.CONFIRMATORY,
                        candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                        unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                        completed=True,
                    )
                ],
            )
            write_jsonl(
                adjudications_path,
                [
                    PilotAdjudicationRecord(
                        calibration_id="pilot-01",
                        adjudicator_id="adj-1",
                        final_study_class=StudyClass.HUMAN_INTERVENTIONAL,
                        final_claim_mode=ClaimMode.CONFIRMATORY,
                        final_candidate_tier=CandidateTier.PUBLIC_GOLD_CANDIDATE,
                        final_unit_release_tier=ReleaseTier.PUBLIC_GOLD,
                        finalized=True,
                    )
                ],
            )
            exit_code = cli_main(
                [
                    "summarize-pilot-agreement",
                    "--forms",
                    forms_path,
                    "--adjudications",
                    adjudications_path,
                    "--output",
                    output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertTrue(payload["ok"])

    def test_cli_validate_full_calibration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "full_manifest.jsonl")
            output_path = os.path.join(tmpdir, "full_validation.json")
            write_jsonl(manifest_path, make_full_calibration_specs())
            exit_code = cli_main(
                [
                    "validate-calibration",
                    "--manifest",
                    manifest_path,
                    "--mode",
                    "full",
                    "--output",
                    output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["summary"]["total_specs"], 60)

    def test_cli_write_full_calibration_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "full_manifest.jsonl")
            summary_path = os.path.join(tmpdir, "full_summary.json")
            exit_code = cli_main(
                [
                    "write-full-calibration-scaffold",
                    "--output",
                    manifest_path,
                    "--prefix",
                    "batch",
                    "--summary-output",
                    summary_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            specs = load_jsonl(manifest_path, loader=pilot_calibration_spec_from_dict)
            self.assertEqual(len(specs), 60)
            self.assertTrue(all(spec.calibration_id.startswith("batch-") for spec in specs))
            with open(summary_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["total_specs"], 60)

    def test_cli_build_and_queue_calibration_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "manifest.jsonl")
            forms_output = os.path.join(tmpdir, "forms.jsonl")
            merged_forms_output = os.path.join(tmpdir, "forms_merged.jsonl")
            adjudication_output = os.path.join(tmpdir, "adjudications.jsonl")
            queue_output = os.path.join(tmpdir, "queue.jsonl")
            write_jsonl(manifest_path, make_full_calibration_specs())
            exit_code = cli_main(
                [
                    "build-calibration-batch",
                    "--manifest",
                    manifest_path,
                    "--forms-output",
                    forms_output,
                    "--adjudication-output",
                    adjudication_output,
                    "--adjudicator",
                    "adjudicator_1",
                    "--reviewers",
                    "reviewer_a",
                    "reviewer_b",
                    "--mode",
                    "full",
                ]
            )
            self.assertEqual(exit_code, 0)

            forms = load_jsonl(forms_output)
            forms.append(
                {
                    "calibration_id": "full-01",
                    "reviewer_id": "reviewer_a",
                    "study_class": "human_interventional",
                    "claim_mode": "confirmatory",
                    "candidate_tier": "public_gold_candidate",
                    "unit_release_tier": "public_gold",
                    "completed": True,
                    "confidence": 4,
                    "notes": [],
                }
            )
            write_jsonl(forms_output, forms)
            exit_code = cli_main(
                [
                    "merge-review-forms",
                    "--inputs",
                    forms_output,
                    "--output",
                    merged_forms_output,
                ]
            )
            self.assertEqual(exit_code, 0)
            exit_code = cli_main(
                [
                    "build-adjudication-queue",
                    "--manifest",
                    manifest_path,
                    "--forms",
                    merged_forms_output,
                    "--adjudications",
                    adjudication_output,
                    "--reviewers",
                    "reviewer_a",
                    "reviewer_b",
                    "--output",
                    queue_output,
                ]
            )
            self.assertEqual(exit_code, 0)
            queue = load_jsonl(queue_output, loader=adjudication_queue_entry_from_dict)
            self.assertEqual(len(queue), 60)

    def test_cli_audit_calibration_drift(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = os.path.join(tmpdir, "baseline.jsonl")
            updated_path = os.path.join(tmpdir, "updated.jsonl")
            output_path = os.path.join(tmpdir, "drift.json")
            write_jsonl(
                baseline_path,
                [
                    PilotCalibrationSpec(
                        calibration_id="drift-01",
                        study_class=StudyClass.HUMAN_INTERVENTIONAL,
                        claim_mode=ClaimMode.CONFIRMATORY,
                    )
                ],
            )
            write_jsonl(
                updated_path,
                [
                    PilotCalibrationSpec(
                        calibration_id="drift-01",
                        study_class=StudyClass.HUMAN_OBSERVATIONAL,
                        claim_mode=ClaimMode.EXPLORATORY,
                    ),
                    PilotCalibrationSpec(
                        calibration_id="drift-02",
                        study_class=StudyClass.METHODS_RESOURCE,
                        claim_mode=ClaimMode.RESOURCE_RELEASE,
                    ),
                ],
            )
            exit_code = cli_main(
                [
                    "audit-calibration-drift",
                    "--baseline-manifest",
                    baseline_path,
                    "--updated-manifest",
                    updated_path,
                    "--output",
                    output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertIn("drift-02", payload["added_calibration_ids"])
            self.assertIn("drift-01", payload["changed_target_labels"])
            self.assertEqual(payload["updated_total_specs"], 2)

    def test_cli_build_release_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            units_path = os.path.join(tmpdir, "units.jsonl")
            decisions_path = os.path.join(tmpdir, "decisions.jsonl")
            output_path = os.path.join(tmpdir, "release_index.jsonl")
            write_jsonl(
                units_path,
                [
                    BenchmarkUnit(
                        benchmark_unit_id="BU:1",
                        paper_id="PMID:1",
                        evidence_unit_ids=("EU:1",),
                        split="test",
                        lineage=LineageInfo(source_family="fam-1"),
                    )
                ],
            )
            write_jsonl(
                decisions_path,
                [
                    BenchmarkUnitDecisionRecord(
                        benchmark_unit_id="BU:1",
                        release_tier=ReleaseTier.PUBLIC_GOLD,
                        gold_eligible=True,
                        reasons=(),
                    )
                ],
            )
            exit_code = cli_main(
                [
                    "build-release-index",
                    "--units",
                    units_path,
                    "--decisions",
                    decisions_path,
                    "--output",
                    output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            entries = load_jsonl(output_path)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["benchmark_unit_id"], "BU:1")
            self.assertEqual(entries[0]["benchmark_split"], "test")

    def test_cli_build_release_bundle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            units_path = os.path.join(tmpdir, "units.jsonl")
            decisions_path = os.path.join(tmpdir, "decisions.jsonl")
            output_dir = os.path.join(tmpdir, "release_bundle")
            write_jsonl(
                units_path,
                [
                    BenchmarkUnit(
                        benchmark_unit_id="BU:bundle-cli",
                        paper_id="PMID:bundle-cli",
                        evidence_unit_ids=("EU:bundle-cli",),
                        split="test",
                        lineage=LineageInfo(source_family="bundle-cli-family"),
                    )
                ],
            )
            write_jsonl(
                decisions_path,
                [
                    BenchmarkUnitDecisionRecord(
                        benchmark_unit_id="BU:bundle-cli",
                        release_tier=ReleaseTier.PUBLIC_GOLD,
                        gold_eligible=True,
                        reasons=(),
                    )
                ],
            )
            exit_code = cli_main(
                [
                    "build-release-bundle",
                    "--units",
                    units_path,
                    "--decisions",
                    decisions_path,
                    "--output-dir",
                    output_dir,
                    "--allow-split-safety-violations",
                ]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.exists(os.path.join(output_dir, "release_index.jsonl")))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "release_summary.json")))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "provenance_manifest.json")))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "checksums.json")))
            with open(
                os.path.join(output_dir, "provenance_manifest.json"),
                "r",
                encoding="utf-8",
            ) as handle:
                provenance_payload = json.load(handle)
            with open(
                os.path.join(output_dir, "checksums.json"),
                "r",
                encoding="utf-8",
            ) as handle:
                checksums_payload = json.load(handle)
            provenance = release_provenance_manifest_from_dict(provenance_payload)
            checksum_records = tuple(
                release_artifact_checksum_from_dict(item)
                for item in checksums_payload["artifacts"]
            )
            self.assertTrue(provenance.release_bundle_id.startswith("LS-PWB-BUNDLE-"))
            self.assertEqual(len(checksum_records), 4)
            self.assertEqual(
                checksums_payload["release_bundle_id"],
                provenance.release_bundle_id,
            )
            self.assertTrue(os.path.exists(os.path.join(output_dir, "bundle_verify_report.json")))

    def test_cli_verify_release_bundle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            units_path = os.path.join(tmpdir, "units.jsonl")
            decisions_path = os.path.join(tmpdir, "decisions.jsonl")
            output_dir = os.path.join(tmpdir, "release_bundle")
            write_jsonl(
                units_path,
                [
                    BenchmarkUnit(
                        benchmark_unit_id="BU:verify-cli",
                        paper_id="PMID:verify-cli",
                        evidence_unit_ids=("EU:verify-cli",),
                        split="test",
                        lineage=LineageInfo(source_family="verify-cli-family"),
                    )
                ],
            )
            write_jsonl(
                decisions_path,
                [
                    BenchmarkUnitDecisionRecord(
                        benchmark_unit_id="BU:verify-cli",
                        release_tier=ReleaseTier.PUBLIC_GOLD,
                        gold_eligible=True,
                        reasons=(),
                    )
                ],
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-release-bundle",
                        "--units",
                        units_path,
                        "--decisions",
                        decisions_path,
                        "--output-dir",
                        output_dir,
                        "--allow-split-safety-violations",
                    ]
                ),
                0,
            )
            verify_output = os.path.join(tmpdir, "verify_report.json")
            exit_code = cli_main(
                [
                    "verify-release-bundle",
                    "--bundle-dir",
                    output_dir,
                    "--output",
                    verify_output,
                ]
            )
            self.assertEqual(exit_code, 0)
            with open(verify_output, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertTrue(payload["ok"])

    def test_cli_init_knowledge_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_root = os.path.join(tmpdir, "knowledge_base")
            exit_code = cli_main(
                [
                    "init-knowledge-base",
                    "--root",
                    kb_root,
                ]
            )
            self.assertEqual(exit_code, 0)
            for subdirectory in ("raw", "normalized", "enriched", "qualified", "released"):
                self.assertTrue(os.path.isdir(os.path.join(kb_root, subdirectory)))
                self.assertTrue(os.path.exists(os.path.join(kb_root, subdirectory, "README.md")))

    def test_cli_build_task_bundles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            evidence_units_path = os.path.join(tmpdir, "evidence_units.jsonl")
            benchmark_units_path = os.path.join(tmpdir, "benchmark_units.jsonl")
            truth_manifests_path = os.path.join(tmpdir, "truth_manifests.jsonl")
            decisions_path = os.path.join(tmpdir, "decisions.jsonl")
            output_path = os.path.join(tmpdir, "task_bundles.jsonl")
            truth_bundle_output = os.path.join(tmpdir, "truth_manifest_bundles.jsonl")
            paper = make_source_paper()
            write_jsonl(papers_path, [paper])
            write_jsonl(
                evidence_units_path,
                [
                    make_evidence_unit(
                        paper,
                        unit_id="EU:task-cli",
                        unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
                    )
                ],
            )
            write_jsonl(
                benchmark_units_path,
                [
                    BenchmarkUnit(
                        benchmark_unit_id="BU:task-cli",
                        paper_id=paper.paper_id,
                        evidence_unit_ids=("EU:task-cli",),
                    )
                ],
            )
            write_jsonl(truth_manifests_path, [make_truth_manifest(paper)])
            write_jsonl(
                decisions_path,
                [
                    BenchmarkUnitDecisionRecord(
                        benchmark_unit_id="BU:task-cli",
                        release_tier=ReleaseTier.PUBLIC_GOLD,
                        gold_eligible=True,
                        reasons=(),
                    )
                ],
            )
            exit_code = cli_main(
                [
                    "build-task-bundles",
                    "--papers",
                    papers_path,
                    "--evidence-units",
                    evidence_units_path,
                    "--benchmark-units",
                    benchmark_units_path,
                    "--truth-manifests",
                    truth_manifests_path,
                    "--decisions",
                    decisions_path,
                    "--output",
                    output_path,
                    "--truth-manifest-bundles-output",
                    truth_bundle_output,
                    "--provenance-manifest-id",
                    "PMAN:cli",
                ]
            )
            self.assertEqual(exit_code, 0)
            bundles = load_jsonl(output_path)
            self.assertEqual(len(bundles), 1)
            self.assertEqual(bundles[0]["task_family"], "results_to_text")

    def test_cli_build_benchmark_units_and_auto_review_decisions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            evidence_units_path = os.path.join(tmpdir, "evidence_units.jsonl")
            benchmark_units_path = os.path.join(tmpdir, "benchmark_units.jsonl")
            auto_qualifications_path = os.path.join(tmpdir, "auto_qualifications.jsonl")
            decisions_path = os.path.join(tmpdir, "decisions.jsonl")
            paper = make_source_paper()
            write_jsonl(papers_path, [paper])
            write_jsonl(
                evidence_units_path,
                [
                    make_evidence_unit(
                        paper,
                        unit_id="EU:auto-cli",
                        unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
                    )
                ],
            )
            write_jsonl(
                auto_qualifications_path,
                [
                    AutoQualificationRecord(
                        paper_id=paper.paper_id,
                        decision=PaperQualificationDecision(
                            scientific=PaperScientificQualification.A,
                            packaging=PaperPackagingQualification.P1,
                            candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                            eligible_for_unit_extraction=True,
                            required_standards=(),
                            writing=PaperWritingQualification.W2,
                        ),
                        confidence=AutoReviewConfidence.MEDIUM,
                    )
                ],
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-benchmark-units-from-evidence",
                        "--papers",
                        papers_path,
                        "--evidence-units",
                        evidence_units_path,
                        "--output",
                        benchmark_units_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-benchmark-unit-decisions-from-auto-review",
                        "--benchmark-units",
                        benchmark_units_path,
                        "--auto-qualifications",
                        auto_qualifications_path,
                        "--output",
                        decisions_path,
                    ]
                ),
                0,
            )
            decisions = load_jsonl(decisions_path, loader=benchmark_unit_decision_record_from_dict)
            self.assertEqual(len(decisions), 1)
            self.assertEqual(decisions[0].release_tier, ReleaseTier.SHADOW_GOLD)

    def test_cli_build_evaluation_task_bundles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            evidence_units_path = os.path.join(tmpdir, "evidence_units.jsonl")
            specs_path = os.path.join(tmpdir, "specs.jsonl")
            observations_path = os.path.join(tmpdir, "observations.jsonl")
            questions_path = os.path.join(tmpdir, "questions.jsonl")
            answers_path = os.path.join(tmpdir, "answers.jsonl")
            quality_path = os.path.join(tmpdir, "quality.jsonl")
            truth_manifests_path = os.path.join(tmpdir, "truth_manifests.jsonl")
            output_path = os.path.join(tmpdir, "evaluation_task_bundles.jsonl")
            paper = make_source_paper(
                paper_id="PMID:eval-bundle-cli",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
                metadata={
                    "results_text": "Figure 3 shows lower marker levels. Table 4 reports endpoint values.",
                    "review_response_text": "We added a validation experiment.",
                    "figure_captions": [{"pointer": "Fig3", "text": "Marker levels were lower in the intervention arm."}],
                    "review_comments": [{"pointer": "R3", "text": "Major concern: strengthen validation evidence."}],
                },
            )
            evidence_units, specs, _ = build_parser_assisted_extraction_drafts((paper,), max_assertions_per_unit=2)
            observations, questions, answers, quality_records, _ = build_evaluation_extraction_artifacts(
                source_papers=(paper,),
                evidence_units=evidence_units,
                extraction_specs=specs,
                max_questions_per_unit=2,
            )
            write_jsonl(papers_path, [paper])
            write_jsonl(evidence_units_path, evidence_units)
            write_jsonl(specs_path, specs)
            write_jsonl(observations_path, observations)
            write_jsonl(questions_path, questions)
            write_jsonl(answers_path, answers)
            write_jsonl(quality_path, quality_records)
            write_jsonl(truth_manifests_path, [make_truth_manifest(paper)])
            exit_code = cli_main(
                [
                    "build-evaluation-task-bundles",
                    "--papers",
                    papers_path,
                    "--observations",
                    observations_path,
                    "--questions",
                    questions_path,
                    "--answers",
                    answers_path,
                    "--truth-manifests",
                    truth_manifests_path,
                    "--source-quality-records",
                    quality_path,
                    "--default-release-tier",
                    ReleaseTier.SHADOW_GOLD.value,
                    "--output",
                    output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            bundles = load_jsonl(output_path)
            self.assertGreaterEqual(len(bundles), 1)
            self.assertTrue(any(bundle["task_family"].endswith("_qa") for bundle in bundles))

    def test_cli_annotate_task_bundles_with_release_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            release_index_path = os.path.join(tmpdir, "release_index.jsonl")
            output_path = os.path.join(tmpdir, "annotated_task_bundles.jsonl")
            summary_path = os.path.join(tmpdir, "annotated_summary.json")
            paper = make_source_paper()
            evidence_unit = make_evidence_unit(
                paper,
                unit_id="EU:annotate-cli",
                unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
            )
            task_bundle = build_task_bundle(
                benchmark_unit=BenchmarkUnit(
                    benchmark_unit_id="BU:annotate-cli",
                    paper_id=paper.paper_id,
                    evidence_unit_ids=("EU:annotate-cli",),
                ),
                source_paper=paper,
                evidence_units=(evidence_unit,),
                truth_manifest=make_truth_manifest(paper),
                release_tier=ReleaseTier.SHADOW_GOLD,
            )
            write_jsonl(task_bundles_path, [task_bundle])
            write_jsonl(
                release_index_path,
                [
                    ReleaseIndexEntry(
                        benchmark_unit_id="BU:annotate-cli",
                        paper_id=paper.paper_id,
                        release_tier=ReleaseTier.SHADOW_GOLD,
                        holdout_bucket="private",
                        canary_string="LS-PWB-CANARY-BU-ANNOTATE",
                        benchmark_split="test",
                    )
                ],
            )
            self.assertEqual(
                cli_main(
                    [
                        "annotate-task-bundles-with-release-index",
                        "--task-bundles",
                        task_bundles_path,
                        "--release-index",
                        release_index_path,
                        "--output",
                        output_path,
                        "--summary-output",
                        summary_path,
                    ]
                ),
                0,
            )
            annotated = load_jsonl(output_path, loader=task_bundle_from_dict)
            self.assertEqual(len(annotated), 1)
            self.assertEqual(annotated[0].holdout_bucket, "private")

    def test_cli_run_baseline_and_score_submissions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            submissions_path = os.path.join(tmpdir, "submissions.jsonl")
            run_spec_path = os.path.join(tmpdir, "baseline_run.jsonl")
            evaluations_path = os.path.join(tmpdir, "evaluations.jsonl")
            paper = make_source_paper()
            evidence_unit = make_evidence_unit(
                paper,
                unit_id="EU:cli-baseline",
                unit_type=EvidenceUnitType.METHODS_PROTOCOL_BLOCK,
                evidence_pointers=("Methods1", "ProtocolA"),
            )
            task_bundle = build_task_bundle(
                benchmark_unit=BenchmarkUnit(
                    benchmark_unit_id="BU:cli-baseline",
                    paper_id=paper.paper_id,
                    evidence_unit_ids=("EU:cli-baseline",),
                    split="test",
                ),
                source_paper=paper,
                evidence_units=(evidence_unit,),
                truth_manifest=make_truth_manifest(paper),
                release_tier=ReleaseTier.PUBLIC_GOLD,
            )
            write_jsonl(task_bundles_path, [task_bundle])

            exit_code = cli_main(
                [
                    "run-baseline",
                    "--task-bundles",
                    task_bundles_path,
                    "--baseline-kind",
                    BaselineKind.REFERENCE_TEMPLATE.value,
                    "--submissions-output",
                    submissions_path,
                    "--run-spec-output",
                    run_spec_path,
                ]
            )
            self.assertEqual(exit_code, 0)

            exit_code = cli_main(
                [
                    "score-submissions",
                    "--task-bundles",
                    task_bundles_path,
                    "--submissions",
                    submissions_path,
                    "--output",
                    evaluations_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            submissions = load_jsonl(submissions_path)
            run_specs = load_jsonl(run_spec_path)
            evaluations = load_jsonl(evaluations_path)
            self.assertEqual(len(submissions), 1)
            self.assertEqual(len(run_specs), 1)
            self.assertEqual(len(evaluations), 1)
            self.assertTrue(evaluations[0]["deterministic_checks_passed"])

    def test_cli_build_maintenance_log_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "maintenance_log.jsonl")
            exit_code = cli_main(
                [
                    "build-maintenance-log-entry",
                    "--phase",
                    "v1-core",
                    "--summary",
                    "initial release rehearsal",
                    "--release-bundle-id",
                    "LS-PWB-BUNDLE-TEST",
                    "--artifacts",
                    "release_index.jsonl",
                    "provenance_manifest.json",
                    "--output",
                    output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            entries = load_jsonl(output_path)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["phase"], "v1-core")

    def test_cli_build_baseline_run_inventory_and_summarize_program_progress_with_auto_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            auto_records_path = os.path.join(tmpdir, "auto_records.jsonl")
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            run_spec_json = os.path.join(tmpdir, "reference_run.json")
            run_spec_jsonl = os.path.join(tmpdir, "retrieval_runs.jsonl")
            baseline_inventory_path = os.path.join(tmpdir, "baseline_runs.jsonl")
            progress_output_path = os.path.join(tmpdir, "program_progress.json")

            paper = make_source_paper()
            task_bundle = make_task_bundle(index=1, paper_id=paper.paper_id, holdout_bucket="public")
            auto_record = AutoQualificationRecord(
                paper_id=paper.paper_id,
                decision=make_paper_decision(
                    candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                    eligible_for_unit_extraction=True,
                ),
            )
            write_jsonl(papers_path, [paper])
            write_jsonl(auto_records_path, [auto_record])
            write_jsonl(task_bundles_path, [task_bundle])
            with open(run_spec_json, "w", encoding="utf-8") as handle:
                json.dump(
                    BaselineRunSpec(
                        baseline_id="baseline-reference",
                        baseline_kind=BaselineKind.REFERENCE_TEMPLATE,
                        replay_verified=True,
                    ).to_dict(),
                    handle,
                )
            write_jsonl(
                run_spec_jsonl,
                [
                    BaselineRunSpec(
                        baseline_id="baseline-retrieval",
                        baseline_kind=BaselineKind.RETRIEVAL_WRITER,
                        replay_verified=True,
                    )
                ],
            )

            self.assertEqual(
                cli_main(
                    [
                        "build-baseline-run-inventory",
                        "--run-spec",
                        run_spec_json,
                        "--run-spec",
                        run_spec_jsonl,
                        "--output",
                        baseline_inventory_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "summarize-program-progress",
                        "--papers",
                        papers_path,
                        "--paper-decisions",
                        auto_records_path,
                        "--task-bundles",
                        task_bundles_path,
                        "--baseline-runs",
                        baseline_inventory_path,
                        "--output",
                        progress_output_path,
                    ]
                ),
                0,
            )
            inventory = load_jsonl(baseline_inventory_path)
            self.assertEqual(len(inventory), 2)
            with open(progress_output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["paper_qualified"], 1)
            self.assertEqual(payload["public_units"], 1)
            self.assertEqual(payload["replayable_baselines"], 2)

    def test_cli_returns_nonzero_for_missing_input(self):
        exit_code = cli_main(
            [
                "suggest-metadata-hints",
                "--papers",
                os.path.join(ROOT, "missing.jsonl"),
                "--output",
                os.path.join(ROOT, "tmp_should_not_exist.jsonl"),
            ]
        )
        self.assertEqual(exit_code, 1)

    def test_ingest_and_normalize_metadata_records_uses_identifier_precedence(self):
        raw_records = [
            {
                "source_name": "crossref",
                "id": "CR-1",
                "title": "RNA-seq atlas of cell states",
                "doi": "https://doi.org/10.1000/XYZ",
                "year": "2024",
                "modality_overlays": ["omics_transcriptomics"],
                "study_class": "mechanistic_experimental",
            },
            {
                "source_name": "pubmed",
                "id": "PM-1",
                "title": "RNA seq atlas of cell states",
                "pmid": "12345",
                "year": 2024,
                "peer_reviewed": True,
            },
        ]
        standardized = ingest_metadata_records(raw_records)
        self.assertEqual(len(standardized), 2)
        self.assertIsInstance(standardized[0], MetadataSourceRecord)

        papers, ingestion_records, audit = normalize_metadata_records(standardized)
        self.assertEqual(len(papers), 1)
        self.assertEqual(len(ingestion_records), 2)
        self.assertIsInstance(audit, IngestionAuditReport)
        paper = papers[0]
        self.assertEqual(paper.paper_id, "DOI:10.1000/xyz")
        self.assertIn(ModalityOverlay.OMICS_TRANSCRIPTOMICS, paper.modality_overlays)
        self.assertTrue(all(record.paper_id == paper.paper_id for record in ingestion_records))
        self.assertTrue(all(record.releaseability_precheck_passed for record in ingestion_records))
        self.assertEqual(audit.merged_duplicates, 1)

    def test_verify_ingestion_artifacts_flags_precedence_violation(self):
        paper = make_source_paper(paper_id="PMID:123")
        record = IngestionRecord(
            ingestion_id="ING:BAD",
            source_name="crossref",
            source_record_id="CR-1",
            paper_id="PMID:123",
            doi="10.1000/xyz",
            pmid="123",
            pmcid=None,
            normalized_title="example",
            publication_year=2024,
            releaseability_precheck_passed=True,
            releaseability_flags=(),
            metadata_fingerprint_sha256="abc123",
        )
        report = verify_ingestion_artifacts([paper], [record])
        self.assertFalse(report.ok)
        self.assertIn("PMID:123:expected DOI precedence", report.precedence_violations)

    def test_audit_ingestion_artifacts_summarizes_outputs(self):
        paper = make_source_paper(
            paper_id="DOI:10.1000/xyz",
            controlled_access_human_data=True,
            metadata={"license": "restricted"},
        )
        records = [
            IngestionRecord(
                ingestion_id="ING:1",
                source_name="crossref",
                source_record_id="CR-1",
                paper_id=paper.paper_id,
                doi="10.1000/xyz",
                pmid=None,
                pmcid=None,
                normalized_title="example",
                publication_year=2024,
                releaseability_precheck_passed=True,
                releaseability_flags=("controlled_access_human_data", "license_unclear_or_restricted"),
                metadata_fingerprint_sha256="hash1",
            )
        ]
        report = audit_ingestion_artifacts([paper], records)
        self.assertEqual(report.normalized_papers, 1)
        self.assertEqual(report.identifier_coverage["doi"], 1)
        self.assertEqual(report.releaseability_flag_counts["controlled_access_human_data"], 1)

    def test_cli_ingest_normalize_and_verify_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_input = os.path.join(tmpdir, "raw.jsonl")
            standardized_output = os.path.join(tmpdir, "standardized.jsonl")
            papers_output = os.path.join(tmpdir, "papers.jsonl")
            ingestion_output = os.path.join(tmpdir, "ingestion.jsonl")
            verify_output = os.path.join(tmpdir, "verify.json")
            raw_records = [
                {
                    "source_name": "europepmc",
                    "id": "EPMC-1",
                    "title": "qPCR study of response",
                    "pmcid": "pmc12345",
                    "publication_year": 2023,
                    "peer_reviewed": True,
                    "modality_overlays": ["qPCR"],
                }
            ]
            with open(raw_input, "w", encoding="utf-8") as handle:
                for record in raw_records:
                    handle.write(json.dumps(record))
                    handle.write("\n")

            self.assertEqual(
                cli_main(
                    [
                        "ingest-metadata",
                        "--input",
                        raw_input,
                        "--output",
                        standardized_output,
                    ]
                ),
                0,
            )
            standardized = load_jsonl(standardized_output, loader=metadata_source_record_from_dict)
            self.assertEqual(len(standardized), 1)
            self.assertEqual(
                cli_main(
                    [
                        "normalize-papers",
                        "--input",
                        standardized_output,
                        "--papers-output",
                        papers_output,
                        "--ingestion-output",
                        ingestion_output,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "verify-ingestion",
                        "--papers",
                        papers_output,
                        "--ingestion-records",
                        ingestion_output,
                        "--output",
                        verify_output,
                    ]
                ),
                0,
            )
            with open(verify_output, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertTrue(payload["ok"])

    def test_build_cayuga_execution_profile(self):
        profile = build_cayuga_execution_profile(
            "/tmp/cayuga",
            ROOT,
        )
        self.assertIsInstance(profile, ExecutionProfile)
        self.assertEqual(profile.profile_name, "cayuga")
        self.assertEqual(profile.backend, "slurm")
        self.assertEqual(profile.launch_prefix, ("sbatch",))
        self.assertIn("LSPWB_CAYUGA_ROOT", profile.environment_exports)

    def test_cli_write_cayuga_execution_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "cayuga_profile.json")
            exit_code = cli_main(
                [
                    "write-execution-profile",
                    "--profile",
                    "cayuga",
                    "--repo-root",
                    ROOT,
                    "--cayuga-root",
                    "/tmp/cayuga",
                    "--output",
                    output_path,
                ]
            )
            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["profile_name"], "cayuga")
            self.assertEqual(payload["backend"], "slurm")

    def test_build_baseline_replay_job_spec_and_script(self):
        profile = build_cayuga_execution_profile(
            "/tmp/cayuga",
            ROOT,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            write_jsonl(task_bundles_path, [make_task_bundle(index=1)])
            spec = build_baseline_replay_job_spec(
                profile,
                task_bundles_path=task_bundles_path,
                baseline_kind=BaselineKind.REFERENCE_TEMPLATE,
                output_dir=os.path.join(tmpdir, "baseline_replay"),
                producer_id="runner_a",
            )
            self.assertIsInstance(spec, ExecutionJobSpec)
            self.assertEqual(spec.backend, "slurm")
            self.assertEqual(spec.job_kind, "baseline_replay")
            self.assertIn("submissions", spec.output_artifacts)
            script = render_execution_job_script(spec, profile)
            self.assertIn("#SBATCH --job-name=", script)
            self.assertIn("run-baseline", script)
            self.assertIn("score-submissions", script)
            self.assertIn("runner_a", script)

    def test_cli_write_baseline_replay_job(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = os.path.join(tmpdir, "cayuga_profile.json")
            task_bundles_path = os.path.join(tmpdir, "task_bundles.jsonl")
            script_output = os.path.join(tmpdir, "jobs", "baseline_replay.sh")
            spec_output = os.path.join(tmpdir, "jobs", "baseline_replay_spec.json")
            output_dir = os.path.join(tmpdir, "baseline_replay")
            write_jsonl(task_bundles_path, [make_task_bundle(index=1)])
            self.assertEqual(
                cli_main(
                    [
                        "write-execution-profile",
                        "--profile",
                        "cayuga",
                        "--repo-root",
                        ROOT,
                        "--cayuga-root",
                        "/tmp/cayuga",
                        "--output",
                        profile_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "write-baseline-replay-job",
                        "--execution-profile",
                        profile_path,
                        "--task-bundles",
                        task_bundles_path,
                        "--baseline-kind",
                        BaselineKind.RETRIEVAL_WRITER.value,
                        "--output-dir",
                        output_dir,
                        "--script-output",
                        script_output,
                        "--spec-output",
                        spec_output,
                    ]
                ),
                0,
            )
            self.assertTrue(os.path.exists(script_output))
            self.assertTrue(os.path.exists(spec_output))
            with open(script_output, "r", encoding="utf-8") as handle:
                script = handle.read()
            self.assertIn("score-submissions", script)
            with open(spec_output, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            spec = execution_job_spec_from_dict(payload)
            self.assertEqual(spec.job_kind, "baseline_replay")
            self.assertEqual(spec.output_artifacts["output_dir"], output_dir)

    def test_build_auto_review_recovery_batch_balanced_selection(self):
        entries = [
            make_auto_review_recovery_entry(index=index, priority_rank=1)
            for index in range(1, 13)
        ]
        selected = build_auto_review_recovery_batch(
            entries,
            target_total=6,
            preferred_buckets=("near_shadow_scientific_borderline",),
            per_class_target=1,
        )
        self.assertEqual(len(selected), 6)
        self.assertEqual(
            {entry.study_class for entry in selected},
            set(StudyClass),
        )
        self.assertTrue(all(entry.selected for entry in selected))
        self.assertTrue(all(entry.selection_rank is not None for entry in selected))
        report = build_auto_review_recovery_batch_report(
            entries,
            selected,
            target_total=6,
            preferred_buckets=("near_shadow_scientific_borderline",),
            per_class_target=1,
        )
        self.assertEqual(report.selected_total, 6)
        self.assertEqual(report.selected_bucket_counts["near_shadow_scientific_borderline"], 6)

    def test_build_auto_review_recovery_batch_excludes_prior_selected_papers(self):
        entries = [
            make_auto_review_recovery_entry(index=index, priority_rank=index)
            for index in range(1, 13)
        ]
        excluded_ids = tuple(entry.paper_id for entry in entries[:6])
        selected = build_auto_review_recovery_batch(
            entries,
            target_total=6,
            preferred_buckets=("near_shadow_scientific_borderline",),
            per_class_target=1,
            excluded_paper_ids=excluded_ids,
        )
        self.assertEqual(len(selected), 6)
        self.assertTrue(all(entry.paper_id not in excluded_ids for entry in selected))

    def test_build_auto_review_recovery_batch_strict_preferred_buckets(self):
        entries = [
            make_auto_review_recovery_entry(index=index)
            for index in range(1, 7)
        ]
        entries.extend(
            [
                make_auto_review_recovery_entry(
                    index=7,
                    priority_bucket="already_shadow_candidate",
                    priority_rank=6,
                    candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                    scientific=PaperScientificQualification.A,
                    writing=PaperWritingQualification.W1,
                    confidence=AutoReviewConfidence.MEDIUM,
                    auto_release_cap_reason=None,
                ),
                make_auto_review_recovery_entry(
                    index=8,
                    priority_bucket="already_shadow_candidate",
                    priority_rank=6,
                    candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                    scientific=PaperScientificQualification.A,
                    writing=PaperWritingQualification.W1,
                    confidence=AutoReviewConfidence.MEDIUM,
                    auto_release_cap_reason=None,
                ),
            ]
        )
        selected = build_auto_review_recovery_batch(
            entries,
            target_total=8,
            preferred_buckets=("near_shadow_scientific_borderline",),
            per_class_target=2,
            strict_preferred_buckets=True,
        )
        self.assertEqual(len(selected), 6)
        self.assertTrue(
            all(entry.priority_bucket == "near_shadow_scientific_borderline" for entry in selected)
        )

    def test_build_auto_review_recovery_job_spec_and_script(self):
        profile = build_cayuga_execution_profile(
            "/tmp/cayuga",
            ROOT,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "recovery_papers.jsonl")
            packaging_reviews_path = os.path.join(tmpdir, "recovery_packaging_reviews.jsonl")
            write_jsonl(papers_path, [make_source_paper()])
            write_jsonl(
                packaging_reviews_path,
                [PaperPackagingReviewRecord(paper_id="PMID:1", packaging_review=make_packaging_review())],
            )
            spec = build_auto_review_recovery_job_spec(
                profile,
                execution_profile_path=os.path.join(tmpdir, "cayuga_profile.json"),
                papers_path=papers_path,
                packaging_reviews_path=packaging_reviews_path,
                output_dir=os.path.join(tmpdir, "recovery_run"),
                model_id="local-shadow-panel-v1",
            )
            self.assertEqual(spec.job_kind, "auto_review_recovery")
            self.assertIn("qualification_records", spec.output_artifacts)
            script = render_execution_job_script(spec, profile)
            self.assertIn("build-auto-review-evidence-enrichments", script)
            self.assertIn("run-auto-paper-reviews", script)
            self.assertIn("build-auto-paper-qualification-decisions", script)

    def test_cli_build_auto_review_recovery_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, "recovery_queue.jsonl")
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            packaging_reviews_path = os.path.join(tmpdir, "packaging_reviews.jsonl")
            output_path = os.path.join(tmpdir, "selected_entries.jsonl")
            summary_path = os.path.join(tmpdir, "selected_summary.json")
            selected_papers_path = os.path.join(tmpdir, "selected_papers.jsonl")
            selected_packaging_path = os.path.join(tmpdir, "selected_packaging_reviews.jsonl")
            entries = [make_auto_review_recovery_entry(index=index) for index in range(1, 13)]
            papers = [make_source_paper(paper_id=f"PMID:{index}", study_class=entry.study_class, claim_mode=entry.claim_mode) for index, entry in enumerate(entries, start=1)]
            packaging_reviews = [
                PaperPackagingReviewRecord(
                    paper_id=f"PMID:{index}",
                    packaging_review=make_packaging_review(),
                )
                for index in range(1, 13)
            ]
            write_jsonl(queue_path, entries)
            write_jsonl(papers_path, papers)
            write_jsonl(packaging_reviews_path, packaging_reviews)
            self.assertEqual(
                cli_main(
                    [
                        "build-auto-review-recovery-batch",
                        "--recovery-queue",
                        queue_path,
                        "--papers",
                        papers_path,
                        "--packaging-reviews",
                        packaging_reviews_path,
                        "--output",
                        output_path,
                        "--summary-output",
                        summary_path,
                        "--selected-papers-output",
                        selected_papers_path,
                        "--selected-packaging-reviews-output",
                        selected_packaging_path,
                        "--target-total",
                        "6",
                        "--per-class-target",
                        "1",
                    ]
                ),
                0,
            )
            selected = load_jsonl(output_path, loader=auto_review_recovery_batch_entry_from_dict)
            self.assertEqual(len(selected), 6)
            self.assertEqual(len(load_jsonl(selected_papers_path, loader=source_paper_from_dict)), 6)
            self.assertEqual(
                len(load_jsonl(selected_packaging_path, loader=paper_packaging_review_record_from_dict)),
                6,
            )
            summary = auto_review_recovery_batch_report_from_dict(json.loads(Path(summary_path).read_text()))
            self.assertEqual(summary.selected_total, 6)

    def test_cli_build_auto_review_recovery_batch_excludes_prior_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, "recovery_queue.jsonl")
            excluded_path = os.path.join(tmpdir, "excluded.jsonl")
            output_path = os.path.join(tmpdir, "selected_entries.jsonl")
            entries = [make_auto_review_recovery_entry(index=index) for index in range(1, 13)]
            write_jsonl(queue_path, entries)
            write_jsonl(excluded_path, entries[:6])
            self.assertEqual(
                cli_main(
                    [
                        "build-auto-review-recovery-batch",
                        "--recovery-queue",
                        queue_path,
                        "--exclude-selected-entries",
                        excluded_path,
                        "--output",
                        output_path,
                        "--target-total",
                        "6",
                        "--per-class-target",
                        "1",
                    ]
                ),
                0,
            )
            selected = load_jsonl(output_path, loader=auto_review_recovery_batch_entry_from_dict)
            excluded_ids = {entry.paper_id for entry in entries[:6]}
            self.assertEqual(len(selected), 6)
            self.assertTrue(all(entry.paper_id not in excluded_ids for entry in selected))

    def test_cli_build_auto_review_recovery_batch_strict_preferred_buckets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, "recovery_queue.jsonl")
            output_path = os.path.join(tmpdir, "selected_entries.jsonl")
            entries = [make_auto_review_recovery_entry(index=index) for index in range(1, 7)]
            entries.extend(
                [
                    make_auto_review_recovery_entry(
                        index=7,
                        priority_bucket="already_shadow_candidate",
                        priority_rank=6,
                        candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                        scientific=PaperScientificQualification.A,
                        writing=PaperWritingQualification.W1,
                        confidence=AutoReviewConfidence.MEDIUM,
                        auto_release_cap_reason=None,
                    ),
                    make_auto_review_recovery_entry(
                        index=8,
                        priority_bucket="already_shadow_candidate",
                        priority_rank=6,
                        candidate_tier=CandidateTier.SHADOW_CANDIDATE,
                        scientific=PaperScientificQualification.A,
                        writing=PaperWritingQualification.W1,
                        confidence=AutoReviewConfidence.MEDIUM,
                        auto_release_cap_reason=None,
                    ),
                ]
            )
            write_jsonl(queue_path, entries)
            self.assertEqual(
                cli_main(
                    [
                        "build-auto-review-recovery-batch",
                        "--recovery-queue",
                        queue_path,
                        "--output",
                        output_path,
                        "--target-total",
                        "8",
                        "--per-class-target",
                        "2",
                        "--strict-preferred-buckets",
                    ]
                ),
                0,
            )
            selected = load_jsonl(output_path, loader=auto_review_recovery_batch_entry_from_dict)
            self.assertEqual(len(selected), 6)
            self.assertTrue(
                all(entry.priority_bucket == "near_shadow_scientific_borderline" for entry in selected)
            )

    def test_cli_write_auto_review_recovery_job(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = os.path.join(tmpdir, "cayuga_profile.json")
            papers_path = os.path.join(tmpdir, "recovery_papers.jsonl")
            packaging_reviews_path = os.path.join(tmpdir, "recovery_packaging_reviews.jsonl")
            output_dir = os.path.join(tmpdir, "recovery_run")
            script_output = os.path.join(tmpdir, "jobs", "recovery_job.sh")
            spec_output = os.path.join(tmpdir, "jobs", "recovery_job_spec.json")
            write_jsonl(papers_path, [make_source_paper()])
            write_jsonl(
                packaging_reviews_path,
                [PaperPackagingReviewRecord(paper_id="PMID:1", packaging_review=make_packaging_review())],
            )
            self.assertEqual(
                cli_main(
                    [
                        "write-execution-profile",
                        "--profile",
                        "cayuga",
                        "--repo-root",
                        ROOT,
                        "--cayuga-root",
                        "/tmp/cayuga",
                        "--output",
                        profile_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "write-auto-review-recovery-job",
                        "--execution-profile",
                        profile_path,
                        "--papers",
                        papers_path,
                        "--packaging-reviews",
                        packaging_reviews_path,
                        "--output-dir",
                        output_dir,
                        "--job-spec-output",
                        spec_output,
                        "--script-output",
                        script_output,
                        "--model-id",
                        "local-shadow-panel-v1",
                    ]
                ),
                0,
            )
            self.assertTrue(os.path.exists(script_output))
            self.assertTrue(os.path.exists(spec_output))
            spec = execution_job_spec_from_dict(json.loads(Path(spec_output).read_text()))
            self.assertEqual(spec.job_kind, "auto_review_recovery")
            self.assertEqual(spec.output_artifacts["output_dir"], output_dir)

    def test_build_extraction_records_and_truth_manifest(self):
        paper = make_source_paper(
            paper_id="PMID:extract-1",
            study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
            claim_mode=ClaimMode.EXPLORATORY,
        )
        evidence_unit = make_evidence_unit(
            paper,
            unit_id="EU:extract-1",
            unit_type=EvidenceUnitType.FIGURE_TABLE_RESULT,
            evidence_pointers=("Fig1", "Table1"),
        )
        specs = [
            {
                "paper_id": paper.paper_id,
                "evidence_unit_id": evidence_unit.unit_id,
                "assertions": [
                    {"text": "Treatment increased marker expression.", "claim_mode": "exploratory"}
                ],
                "evidence_items": [
                    {"pointer": "Fig1", "evidence_type": "figure"},
                    {"pointer": "Table1", "evidence_type": "table"},
                ],
                "excluded_assertions": ["Causality is fully established."],
            }
        ]
        assertions, evidence_records, extraction_records, audit = build_extraction_records(
            {paper.paper_id: paper},
            {evidence_unit.unit_id: evidence_unit},
            specs,
        )
        self.assertIsInstance(audit, ExtractionAuditReport)
        self.assertEqual(len(assertions), 2)
        self.assertEqual(len(evidence_records), 2)
        self.assertEqual(len(extraction_records), 1)

        manifest = build_truth_manifest_from_extractions(
            paper=paper,
            evidence_units=(evidence_unit,),
            assertion_records=assertions,
            evidence_records=evidence_records,
            extraction_records=extraction_records,
        )
        self.assertEqual(manifest.paper_id, paper.paper_id)
        self.assertEqual(len(manifest.assertion_ids), 1)
        self.assertIn("Causality is fully established.", manifest.excluded_assertions)
        self.assertIn(StandardId.MDAR, manifest.applied_standards)

        frozen_manifest = freeze_truth_manifest(manifest, frozen_at="2026-04-10T00:00:00Z")
        self.assertTrue(frozen_manifest.frozen)
        report = verify_truth_manifest(
            truth_manifest=frozen_manifest,
            paper=paper,
            evidence_units=(evidence_unit,),
            assertion_records=assertions,
            evidence_records=evidence_records,
            extraction_records=extraction_records,
        )
        self.assertTrue(report.ok)

    def test_build_parser_assisted_extraction_drafts(self):
        paper = make_source_paper(
            paper_id="PMID:parser-1",
            study_class=StudyClass.METHODS_RESOURCE,
            claim_mode=ClaimMode.RESOURCE_RELEASE,
            metadata={
                "abstract": "We release a curated plasmid resource. The benchmark includes validated annotations.",
                "results_text": "Figure 1 shows benchmark coverage improved. Table 1 summarizes released resources.",
                "figure_pointers": "Fig1;Table1",
                "methods_text": "We assembled resources from published studies. We normalized each record manually.",
                "resource_description": "The release includes plasmids, metadata, and accession mappings.",
                "review_response_text": "We added a validation experiment. We clarified the provenance.",
            },
        )
        evidence_units, specs, report = build_parser_assisted_extraction_drafts((paper,), max_assertions_per_unit=2)
        self.assertEqual(len(evidence_units), 5)
        self.assertEqual(len(specs), 5)
        self.assertEqual(report.paper_count, 1)
        self.assertEqual(report.papers_with_suggestions, 1)
        self.assertEqual(report.evidence_unit_count, 5)
        self.assertEqual(report.extraction_spec_count, 5)
        unit_types = {unit.unit_type for unit in evidence_units}
        self.assertEqual(
            unit_types,
            {
                EvidenceUnitType.CLAIM_CLUSTER,
                EvidenceUnitType.FIGURE_TABLE_RESULT,
                EvidenceUnitType.METHODS_PROTOCOL_BLOCK,
                EvidenceUnitType.RESOURCE_DESCRIPTION_BLOCK,
                EvidenceUnitType.REVIEW_REVISION_BLOCK,
            },
        )
        results_spec = next(
            spec for spec in specs if spec["evidence_unit_id"] == next(
                unit.unit_id for unit in evidence_units if unit.unit_type == EvidenceUnitType.FIGURE_TABLE_RESULT
            )
        )
        result_pointers = tuple(item["pointer"] for item in results_spec["evidence_items"])
        self.assertIn("results_section", result_pointers)
        self.assertIn("Fig1", result_pointers)
        self.assertIn("Table1", result_pointers)
        self.assertEqual(len(results_spec["assertions"]), 2)
        round_tripped = parser_assisted_extraction_report_from_dict(report.to_dict())
        self.assertEqual(round_tripped, report)

    def test_source_paper_from_dict_preserves_structured_metadata(self):
        payload = make_source_paper(
            paper_id="PMID:structured",
            metadata={
                "figure_captions": [{"pointer": "Fig1", "text": "Signal increased after treatment."}],
                "table_rows": [{"pointer": "Table1", "text": "Cohort A had n=12"}],
            },
        ).to_dict()
        paper = source_paper_from_dict(payload)
        self.assertIsInstance(paper.metadata["figure_captions"], list)
        self.assertEqual(paper.metadata["figure_captions"][0]["pointer"], "Fig1")

    def test_build_evaluation_extraction_artifacts(self):
        paper = make_source_paper(
            paper_id="PMID:eval-1",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            metadata={
                "results_text": "Figure 1 shows biomarker reduction. Table 1 reports the primary endpoint.",
                "methods_text": "Participants were randomized to intervention or placebo.",
                "review_response_text": "We added a validation experiment and clarified assay provenance.",
                "figure_captions": [{"pointer": "Fig1", "text": "Biomarker levels decreased in the intervention arm."}],
                "table_rows": [{"pointer": "Table1", "text": "Primary endpoint improved at week 12."}],
                "trial_registry_summary": [{"pointer": "NCT01234567", "text": "Randomized placebo-controlled phase 2 trial."}],
                "review_comments": [
                    {"pointer": "R1", "text": "Major concern: add a validation experiment for the biomarker assay."}
                ],
            },
        )
        evidence_units, specs, _ = build_parser_assisted_extraction_drafts(
            (paper,),
            max_assertions_per_unit=2,
        )
        observations, questions, answers, quality_records, audit = build_evaluation_extraction_artifacts(
            source_papers=(paper,),
            evidence_units=evidence_units,
            extraction_specs=specs,
            max_questions_per_unit=2,
        )
        self.assertIsInstance(audit, EvaluationExtractionAuditReport)
        self.assertTrue(any(record.task_family == TaskFamily.FIGURE_QA for record in observations))
        self.assertTrue(any(record.task_family == TaskFamily.TABLE_QA for record in observations))
        self.assertTrue(any(record.task_family == TaskFamily.TRIAL_QA for record in questions))
        self.assertTrue(any(record.task_family == TaskFamily.SOURCE_QUALITY_QA for record in questions))
        self.assertTrue(all(isinstance(record, QuestionRecord) for record in questions))
        self.assertTrue(all(answer.answer_text for answer in answers))
        self.assertTrue(all(isinstance(record, SourceQualityRecord) for record in quality_records))
        round_tripped = evaluation_extraction_audit_report_from_dict(audit.to_dict())
        self.assertEqual(round_tripped, audit)

    def test_verify_truth_manifest_detects_unfrozen_manifest(self):
        paper = make_source_paper(paper_id="PMID:extract-2")
        evidence_unit = make_evidence_unit(
            paper,
            unit_id="EU:extract-2",
            unit_type=EvidenceUnitType.METHODS_PROTOCOL_BLOCK,
        )
        specs = [
            {
                "paper_id": paper.paper_id,
                "evidence_unit_id": evidence_unit.unit_id,
                "assertions": [{"text": "Protocol used triplicate replicates."}],
                "evidence_items": [{"pointer": "Methods paragraph 2", "evidence_type": "methods"}],
            }
        ]
        assertions, evidence_records, extraction_records, _ = build_extraction_records(
            {paper.paper_id: paper},
            {evidence_unit.unit_id: evidence_unit},
            specs,
        )
        manifest = build_truth_manifest_from_extractions(
            paper=paper,
            evidence_units=(evidence_unit,),
            assertion_records=assertions,
            evidence_records=evidence_records,
            extraction_records=extraction_records,
        )
        report = verify_truth_manifest(
            truth_manifest=manifest,
            paper=paper,
            evidence_units=(evidence_unit,),
            assertion_records=assertions,
            evidence_records=evidence_records,
            extraction_records=extraction_records,
        )
        self.assertFalse(report.ok)
        self.assertIn("truth manifest is not frozen", report.notes)

    def test_cli_build_parser_assisted_extraction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            evidence_units_path = os.path.join(tmpdir, "evidence_units.jsonl")
            specs_path = os.path.join(tmpdir, "extraction_specs.jsonl")
            audit_path = os.path.join(tmpdir, "parser_audit.json")
            paper = make_source_paper(
                paper_id="PMID:parser-cli",
                metadata={
                    "abstract": "Cells responded to treatment. The response was reproducible.",
                    "methods_text": "We cultured cells for 48 hours. We measured viability in triplicate.",
                    "results_text": "Figure 2 shows reduced viability. Table 3 reports replicate counts.",
                    "figure_pointers": "Fig2;Table3",
                },
            )
            write_jsonl(papers_path, [paper])
            self.assertEqual(
                cli_main(
                    [
                        "build-parser-assisted-extraction",
                        "--papers",
                        papers_path,
                        "--evidence-units-output",
                        evidence_units_path,
                        "--specs-output",
                        specs_path,
                        "--audit-output",
                        audit_path,
                        "--max-assertions-per-unit",
                        "2",
                    ]
                ),
                0,
            )
            evidence_units = load_jsonl(evidence_units_path, loader=evidence_unit_from_dict)
            specs = load_jsonl(specs_path)
            with open(audit_path, "r", encoding="utf-8") as handle:
                audit = json.load(handle)
            self.assertEqual(len(evidence_units), 3)
            self.assertEqual(len(specs), 3)
            self.assertEqual(audit["papers_with_suggestions"], 1)
            self.assertEqual(audit["evidence_unit_count"], 3)

    def test_cli_build_evaluation_extraction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            evidence_units_path = os.path.join(tmpdir, "evidence_units.jsonl")
            specs_path = os.path.join(tmpdir, "extraction_specs.jsonl")
            observations_path = os.path.join(tmpdir, "observations.jsonl")
            questions_path = os.path.join(tmpdir, "questions.jsonl")
            answers_path = os.path.join(tmpdir, "answers.jsonl")
            quality_path = os.path.join(tmpdir, "source_quality.jsonl")
            audit_path = os.path.join(tmpdir, "evaluation_audit.json")
            paper = make_source_paper(
                paper_id="PMID:eval-cli",
                study_class=StudyClass.HUMAN_INTERVENTIONAL,
                metadata={
                    "results_text": "Figure 2 shows reduced viability. Table 3 reports endpoint counts.",
                    "figure_pointers": "Fig2;Table3",
                    "figure_captions": [{"pointer": "Fig2", "text": "Intervention reduced viability."}],
                    "review_comments": [{"pointer": "R2", "text": "Major concern: clarify endpoint selection."}],
                },
            )
            evidence_units, specs, _ = build_parser_assisted_extraction_drafts((paper,), max_assertions_per_unit=2)
            write_jsonl(papers_path, [paper])
            write_jsonl(evidence_units_path, evidence_units)
            write_jsonl(specs_path, specs)
            self.assertEqual(
                cli_main(
                    [
                        "build-evaluation-extraction",
                        "--papers",
                        papers_path,
                        "--evidence-units",
                        evidence_units_path,
                        "--specs",
                        specs_path,
                        "--observations-output",
                        observations_path,
                        "--questions-output",
                        questions_path,
                        "--answers-output",
                        answers_path,
                        "--source-quality-output",
                        quality_path,
                        "--audit-output",
                        audit_path,
                    ]
                ),
                0,
            )
            observations = load_jsonl(observations_path, loader=observation_record_from_dict)
            questions = load_jsonl(questions_path, loader=question_record_from_dict)
            answers = load_jsonl(answers_path, loader=answer_record_from_dict)
            quality_records = load_jsonl(quality_path, loader=source_quality_record_from_dict)
            with open(audit_path, "r", encoding="utf-8") as handle:
                audit = json.load(handle)
            self.assertGreaterEqual(len(observations), 2)
            self.assertGreaterEqual(len(questions), 1)
            self.assertGreaterEqual(len(answers), 1)
            self.assertGreaterEqual(len(quality_records), 1)
            self.assertGreaterEqual(audit["source_quality_count"], 1)

    def test_cli_extract_build_freeze_and_verify_truth_manifests(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            evidence_units_path = os.path.join(tmpdir, "evidence_units.jsonl")
            specs_path = os.path.join(tmpdir, "extraction_specs.jsonl")
            assertions_path = os.path.join(tmpdir, "assertions.jsonl")
            evidence_records_path = os.path.join(tmpdir, "evidence_records.jsonl")
            extractions_path = os.path.join(tmpdir, "extractions.jsonl")
            manifests_path = os.path.join(tmpdir, "truth_manifests.jsonl")
            frozen_path = os.path.join(tmpdir, "truth_manifests_frozen.jsonl")
            verify_path = os.path.join(tmpdir, "truth_manifest_verify.jsonl")
            audit_path = os.path.join(tmpdir, "extraction_audit.json")

            paper = make_source_paper(paper_id="PMID:extract-cli")
            evidence_unit = make_evidence_unit(
                paper,
                unit_id="EU:extract-cli",
                unit_type=EvidenceUnitType.CLAIM_CLUSTER,
            )
            write_jsonl(papers_path, [paper])
            write_jsonl(evidence_units_path, [evidence_unit])
            with open(specs_path, "w", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "paper_id": paper.paper_id,
                            "evidence_unit_id": evidence_unit.unit_id,
                            "assertions": [{"text": "Cells responded to treatment."}],
                            "evidence_items": [{"pointer": "Abstract sentence 2", "evidence_type": "abstract"}],
                        }
                    )
                )
                handle.write("\n")

            self.assertEqual(
                cli_main(
                    [
                        "extract-evidence-records",
                        "--papers",
                        papers_path,
                        "--evidence-units",
                        evidence_units_path,
                        "--input",
                        specs_path,
                        "--assertions-output",
                        assertions_path,
                        "--evidence-records-output",
                        evidence_records_path,
                        "--extractions-output",
                        extractions_path,
                        "--audit-output",
                        audit_path,
                    ]
                ),
                0,
            )
            with open(audit_path, "r", encoding="utf-8") as handle:
                audit = json.load(handle)
            self.assertEqual(audit["extraction_count"], 1)

            self.assertEqual(
                cli_main(
                    [
                        "build-truth-manifests",
                        "--papers",
                        papers_path,
                        "--evidence-units",
                        evidence_units_path,
                        "--assertions",
                        assertions_path,
                        "--evidence-records",
                        evidence_records_path,
                        "--extractions",
                        extractions_path,
                        "--output",
                        manifests_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "freeze-truth-manifests",
                        "--input",
                        manifests_path,
                        "--output",
                        frozen_path,
                        "--frozen-at",
                        "2026-04-10T00:00:00Z",
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "verify-truth-manifests",
                        "--papers",
                        papers_path,
                        "--evidence-units",
                        evidence_units_path,
                        "--assertions",
                        assertions_path,
                        "--evidence-records",
                        evidence_records_path,
                        "--extractions",
                        extractions_path,
                        "--manifests",
                        frozen_path,
                        "--output",
                        verify_path,
                    ]
                ),
                0,
            )
            reports = load_jsonl(verify_path, loader=truth_manifest_verification_report_from_dict)
            self.assertEqual(len(reports), 1)
            self.assertTrue(reports[0].ok)

    def _pubmed_article_xml(
        self,
        pmid,
        *,
        title=None,
        abstract="Abstract text.",
        journal="Test Journal",
        year=2024,
        doi=None,
        pmcid=None,
        publication_types=(),
    ):
        title = title or f"Title {pmid}"
        publication_type_xml = "".join(
            f"<PublicationType>{item}</PublicationType>" for item in publication_types
        )
        article_ids = [f'<ArticleId IdType="pubmed">{pmid}</ArticleId>']
        if doi:
            article_ids.append(f'<ArticleId IdType="doi">{doi}</ArticleId>')
        if pmcid:
            article_ids.append(f'<ArticleId IdType="pmc">{pmcid}</ArticleId>')
        return (
            "<PubmedArticle>"
            "<MedlineCitation>"
            f"<PMID>{pmid}</PMID>"
            "<Article>"
            f"<ArticleTitle>{title}</ArticleTitle>"
            f"<Abstract><AbstractText>{abstract}</AbstractText></Abstract>"
            f"<Journal><Title>{journal}</Title><JournalIssue><PubDate><Year>{year}</Year></PubDate></JournalIssue></Journal>"
            f"<PublicationTypeList>{publication_type_xml}</PublicationTypeList>"
            "</Article>"
            "</MedlineCitation>"
            f"<PubmedData><ArticleIdList>{''.join(article_ids)}</ArticleIdList></PubmedData>"
            "</PubmedArticle>"
        )

    def _pubmed_xml_payload(self, pmids, **kwargs):
        return (
            "<PubmedArticleSet>"
            + "".join(self._pubmed_article_xml(pmid, **kwargs) for pmid in pmids)
            + "</PubmedArticleSet>"
        ).encode("utf-8")

    def test_build_collection_batch_has_expected_query_specs(self):
        batch = build_collection_batch()
        self.assertEqual(batch.batch_id, "collection_v1_2018_present")
        self.assertEqual(len(batch.query_specs), 12)
        lanes = {(spec.study_class, spec.lane) for spec in batch.query_specs}
        for study_class in StudyClass:
            self.assertIn((study_class, "primary"), lanes)
            self.assertIn((study_class, "reserve"), lanes)

    def test_fetch_pubmed_batch_uses_reserve_when_primary_underfilled(self):
        batch = collection_batch_spec_from_dict(
            {
                "batch_id": "batch",
                "year_start": 2018,
                "year_end": 3000,
                "primary_retmax": 120,
                "reserve_retmax": 80,
                "target_candidates_per_class": 50,
                "seed_source": "pubmed",
                "enrichment_sources": ["europepmc", "crossref"],
                "oa_fulltext_policy": "preferred",
                "query_specs": [
                    {
                        "batch_id": "batch",
                        "study_class": StudyClass.HUMAN_INTERVENTIONAL.value,
                        "lane": "primary",
                        "source": "pubmed",
                        "query_text": "primary-query",
                        "retmax": 120,
                        "year_start": 2018,
                        "year_end": 3000,
                    },
                    {
                        "batch_id": "batch",
                        "study_class": StudyClass.HUMAN_INTERVENTIONAL.value,
                        "lane": "reserve",
                        "source": "pubmed",
                        "query_text": "reserve-query",
                        "retmax": 80,
                        "year_start": 2018,
                        "year_end": 3000,
                    },
                ],
            }
        )

        def fetcher(url, headers=None):
            if "esearch.fcgi" in url and "primary-query" in url:
                return json.dumps({"esearchresult": {"idlist": ["1001", "1002"]}}).encode("utf-8")
            if "esearch.fcgi" in url and "reserve-query" in url:
                return json.dumps({"esearchresult": {"idlist": ["2001"]}}).encode("utf-8")
            if "efetch.fcgi" in url and "1001%2C1002" in url:
                return self._pubmed_xml_payload(["1001", "1002"])
            if "efetch.fcgi" in url and "2001" in url:
                return self._pubmed_xml_payload(["2001"])
            raise AssertionError(f"unexpected url: {url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            records = fetch_pubmed_batch(batch, tmpdir, fetcher=fetcher)
        self.assertEqual(len(records), 3)
        self.assertEqual({record.lane for record in records}, {"primary", "reserve"})

    def test_fetch_pubmed_batch_skips_reserve_when_primary_has_60_unique(self):
        batch = collection_batch_spec_from_dict(
            {
                "batch_id": "batch",
                "year_start": 2018,
                "year_end": 3000,
                "primary_retmax": 120,
                "reserve_retmax": 80,
                "target_candidates_per_class": 50,
                "seed_source": "pubmed",
                "enrichment_sources": ["europepmc", "crossref"],
                "oa_fulltext_policy": "preferred",
                "query_specs": [
                    {
                        "batch_id": "batch",
                        "study_class": StudyClass.HUMAN_INTERVENTIONAL.value,
                        "lane": "primary",
                        "source": "pubmed",
                        "query_text": "primary-query",
                        "retmax": 120,
                        "year_start": 2018,
                        "year_end": 3000,
                    },
                    {
                        "batch_id": "batch",
                        "study_class": StudyClass.HUMAN_INTERVENTIONAL.value,
                        "lane": "reserve",
                        "source": "pubmed",
                        "query_text": "reserve-query",
                        "retmax": 80,
                        "year_start": 2018,
                        "year_end": 3000,
                    },
                ],
            }
        )
        primary_ids = [str(1000 + index) for index in range(60)]
        seen_urls = []

        def fetcher(url, headers=None):
            seen_urls.append(url)
            if "esearch.fcgi" in url and "primary-query" in url:
                return json.dumps({"esearchresult": {"idlist": primary_ids}}).encode("utf-8")
            if "esearch.fcgi" in url and "reserve-query" in url:
                raise AssertionError("reserve query should not run when primary has >= 60 unique candidates")
            if "efetch.fcgi" in url:
                return self._pubmed_xml_payload(primary_ids)
            raise AssertionError(f"unexpected url: {url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            records = fetch_pubmed_batch(batch, tmpdir, fetcher=fetcher)
        self.assertEqual(len(records), 60)
        self.assertFalse(any("reserve-query" in url for url in seen_urls))

    def test_fetch_pubmed_batch_marks_preprints(self):
        batch = collection_batch_spec_from_dict(
            {
                "batch_id": "batch",
                "year_start": 2018,
                "year_end": 3000,
                "primary_retmax": 120,
                "reserve_retmax": 80,
                "target_candidates_per_class": 50,
                "seed_source": "pubmed",
                "enrichment_sources": [],
                "oa_fulltext_policy": "preferred",
                "query_specs": [
                    {
                        "batch_id": "batch",
                        "study_class": StudyClass.MECHANISTIC_EXPERIMENTAL.value,
                        "lane": "primary",
                        "source": "pubmed",
                        "query_text": "mechanistic-query",
                        "retmax": 120,
                        "year_start": 2018,
                        "year_end": 3000,
                    }
                ],
            }
        )

        def fetcher(url, headers=None):
            if "esearch.fcgi" in url:
                return json.dumps({"esearchresult": {"idlist": ["5001"]}}).encode("utf-8")
            if "efetch.fcgi" in url:
                return self._pubmed_xml_payload(["5001"], publication_types=("Preprint",))
            raise AssertionError(f"unexpected url: {url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            records = fetch_pubmed_batch(batch, tmpdir, fetcher=fetcher)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].publication_status, PublicationStatus.PREPRINT)
        self.assertFalse(records[0].peer_reviewed)

    def test_merge_collection_candidates_handles_multi_class_votes(self):
        records = [
            api_fetch_record_from_dict(
                {
                    "fetch_id": "F1",
                    "source": "pubmed",
                    "study_class": StudyClass.MECHANISTIC_EXPERIMENTAL.value,
                    "lane": "primary",
                    "source_record_id": "1",
                    "doi": "10.1/example",
                    "title": "Shared paper",
                    "publication_year": 2024,
                    "publication_status": PublicationStatus.PUBLISHED.value,
                    "peer_reviewed": True,
                }
            ),
            api_fetch_record_from_dict(
                {
                    "fetch_id": "F2",
                    "source": "pubmed",
                    "study_class": StudyClass.METHODS_RESOURCE.value,
                    "lane": "primary",
                    "source_record_id": "2",
                    "doi": "10.1/example",
                    "title": "Shared paper",
                    "publication_year": 2024,
                    "publication_status": PublicationStatus.PUBLISHED.value,
                    "peer_reviewed": True,
                }
            ),
        ]
        candidates = merge_collection_candidates(records)
        self.assertEqual(len(candidates), 1)
        self.assertIsNone(candidates[0].selected_study_class)
        self.assertEqual(candidates[0].study_class_votes, {"mechanistic_experimental": 1, "methods_resource": 1})
        self.assertEqual(candidates[0].shortlist_target_class, StudyClass.MECHANISTIC_EXPERIMENTAL)

    def test_europepmc_and_crossref_enrichment_update_candidate_fields(self):
        candidate = collection_candidate_record_from_dict(
            {
                "candidate_id": "C1",
                "paper_key": "DOI:10.1/example",
                "study_class_votes": {"human_observational": 1},
                "selected_study_class": StudyClass.HUMAN_OBSERVATIONAL.value,
                "shortlist_target_class": StudyClass.HUMAN_OBSERVATIONAL.value,
                "doi": "10.1/example",
                "pmid": "1234",
                "title": "Candidate",
                "publication_year": 2024,
                "journal": "Journal",
                "abstract": "Abstract.",
                "publication_status": PublicationStatus.PUBLISHED.value,
                "peer_reviewed": True,
                "source_names": ["pubmed"],
                "source_record_ids": ["1234"],
            }
        )

        def europepmc_fetcher(url, headers=None):
            return json.dumps(
                {
                    "resultList": {
                        "result": [
                            {
                                "id": "1234",
                                "pmid": "1234",
                                "pmcid": "PMC999",
                                "doi": "10.1/example",
                                "title": "Candidate",
                                "journalTitle": "eLife",
                                "abstractText": "Expanded abstract.",
                                "pubYear": "2024",
                                "isOpenAccess": "Y",
                                "inEPMC": "Y",
                            }
                        ]
                    }
                }
            ).encode("utf-8")

        def crossref_fetcher(url, headers=None):
            return json.dumps(
                {
                    "message": {
                        "DOI": "10.1/example",
                        "title": ["Candidate revised"],
                        "container-title": ["eLife"],
                        "license": [{"URL": "https://creativecommons.org/licenses/by/4.0/"}],
                        "relation": {"is-corrected-by": [{"id-type": "doi", "id": "10.1/correction"}]},
                    }
                }
            ).encode("utf-8")

        with tempfile.TemporaryDirectory() as tmpdir:
            enriched, epmc_fetch_records = enrich_candidates_with_europepmc(
                [candidate],
                os.path.join(tmpdir, "epmc"),
                fetcher=europepmc_fetcher,
            )
            final_candidates, crossref_fetch_records = enrich_candidates_with_crossref(
                enriched,
                os.path.join(tmpdir, "crossref"),
                fetcher=crossref_fetcher,
            )
        self.assertEqual(len(epmc_fetch_records), 1)
        self.assertEqual(len(crossref_fetch_records), 1)
        self.assertTrue(final_candidates[0].oa_fulltext_available)
        self.assertEqual(final_candidates[0].pmcid, "PMC999")
        self.assertTrue(final_candidates[0].open_review_signal)
        self.assertIn("creativecommons.org/licenses/by/4.0/", final_candidates[0].license)
        self.assertIn(CrossmarkUpdateType.CORRECTION, final_candidates[0].crossmark_updates)

    def test_crossref_enrichment_tolerates_missing_records(self):
        candidate = collection_candidate_record_from_dict(
            {
                "candidate_id": "C404",
                "paper_key": "DOI:10.1/missing",
                "study_class_votes": {"methods_resource": 1},
                "selected_study_class": StudyClass.METHODS_RESOURCE.value,
                "shortlist_target_class": StudyClass.METHODS_RESOURCE.value,
                "doi": "10.1/missing",
                "title": "Missing Crossref",
                "publication_year": 2024,
                "journal": "Journal",
                "abstract": "Abstract.",
                "publication_status": PublicationStatus.PUBLISHED.value,
                "peer_reviewed": True,
                "source_names": ["pubmed"],
                "source_record_ids": ["C404"],
            }
        )

        def crossref_fetcher(url, headers=None):
            raise urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            final_candidates, fetch_records = enrich_candidates_with_crossref(
                [candidate],
                os.path.join(tmpdir, "crossref"),
                fetcher=crossref_fetcher,
            )
        self.assertEqual(len(fetch_records), 0)
        self.assertEqual(len(final_candidates), 1)
        self.assertIn("crossref_error", final_candidates[0].metadata)

    def test_shortlist_collection_candidates_preserves_per_class_caps_and_metadata(self):
        candidates = [
            collection_candidate_record_from_dict(
                {
                    "candidate_id": f"C{i}",
                    "paper_key": f"PMID:{i}",
                    "study_class_votes": {"mechanistic_experimental": 1},
                    "selected_study_class": StudyClass.MECHANISTIC_EXPERIMENTAL.value,
                    "shortlist_target_class": StudyClass.MECHANISTIC_EXPERIMENTAL.value,
                    "pmid": str(i),
                    "title": f"Mechanistic {i}",
                    "publication_year": 2024,
                    "journal": "Journal",
                    "abstract": "Methods and results with Figure 1 and GSE1.",
                    "publication_status": PublicationStatus.PUBLISHED.value,
                    "peer_reviewed": True,
                    "oa_fulltext_available": i != 3,
                    "source_names": ["pubmed"],
                    "source_record_ids": [str(i)],
                }
            )
            for i in (1, 2, 3)
        ]
        candidates.append(
            collection_candidate_record_from_dict(
                {
                    "candidate_id": "C4",
                    "paper_key": "PMID:4",
                    "study_class_votes": {"methods_resource": 1},
                    "selected_study_class": StudyClass.METHODS_RESOURCE.value,
                    "shortlist_target_class": StudyClass.METHODS_RESOURCE.value,
                    "pmid": "4",
                    "title": "Methods 4",
                    "publication_year": 2024,
                    "journal": "Journal",
                    "abstract": "Protocol benchmark.",
                    "publication_status": PublicationStatus.PUBLISHED.value,
                    "peer_reviewed": True,
                    "source_names": ["pubmed"],
                    "source_record_ids": ["4"],
                }
            )
        )

        shortlisted, metadata_records, report = shortlist_collection_candidates(
            candidates,
            target_candidates_per_class=2,
            batch_id="batch",
        )
        self.assertEqual(len(shortlisted), 3)
        self.assertEqual(report.class_shortlist_counts["mechanistic_experimental"], 2)
        self.assertEqual(report.class_shortlist_counts["methods_resource"], 1)
        self.assertEqual(len(metadata_records), len(shortlisted))
        papers, ingestion_records, _ = normalize_metadata_records(metadata_records)
        self.assertEqual(len(papers), 3)
        self.assertEqual(len(ingestion_records), 3)

    def test_collection_cli_build_fetch_rank_shortlist_and_audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_path = os.path.join(tmpdir, "batch.json")
            queries_path = os.path.join(tmpdir, "queries.jsonl")
            self.assertEqual(
                cli_main(
                    [
                        "build-collection-batch",
                        "--output",
                        batch_path,
                        "--queries-output",
                        queries_path,
                    ]
                ),
                0,
            )
            with open(batch_path, "r", encoding="utf-8") as handle:
                batch = collection_batch_spec_from_dict(json.loads(handle.read()))
            hi_primary = next(
                spec for spec in batch.query_specs
                if spec.study_class == StudyClass.HUMAN_INTERVENTIONAL and spec.lane == "primary"
            )
            hi_reserve = next(
                spec for spec in batch.query_specs
                if spec.study_class == StudyClass.HUMAN_INTERVENTIONAL and spec.lane == "reserve"
            )
            raw_dir = os.path.join(tmpdir, "raw")
            os.makedirs(raw_dir, exist_ok=True)
            with open(os.path.join(raw_dir, "pubmed__human_interventional__primary__esearch.json"), "w", encoding="utf-8") as handle:
                json.dump({"esearchresult": {"idlist": ["101", "102"]}}, handle)
            Path(os.path.join(raw_dir, "pubmed__human_interventional__primary__efetch_01.xml")).write_bytes(
                self._pubmed_xml_payload(["101", "102"])
            )
            with open(os.path.join(raw_dir, "pubmed__human_interventional__reserve__esearch.json"), "w", encoding="utf-8") as handle:
                json.dump({"esearchresult": {"idlist": ["201"]}}, handle)
            Path(os.path.join(raw_dir, "pubmed__human_interventional__reserve__efetch_01.xml")).write_bytes(
                self._pubmed_xml_payload(["201"], publication_types=("Preprint",))
            )

            custom_batch = collection_batch_spec_from_dict(
                {
                    **batch.to_dict(),
                    "query_specs": [hi_primary.to_dict(), hi_reserve.to_dict()],
                }
            )
            with open(batch_path, "w", encoding="utf-8") as handle:
                json.dump(custom_batch.to_dict(), handle, indent=2, sort_keys=True)
                handle.write("\n")

            fetch_output = os.path.join(tmpdir, "pubmed_fetch.jsonl")
            self.assertEqual(
                cli_main(
                    [
                        "fetch-pubmed-batch",
                        "--batch-spec",
                        batch_path,
                        "--raw-dir",
                        raw_dir,
                        "--output",
                        fetch_output,
                    ]
                ),
                0,
            )
            fetch_records = load_jsonl(fetch_output, loader=api_fetch_record_from_dict)
            self.assertEqual(len(fetch_records), 3)

            candidates_path = os.path.join(tmpdir, "candidates.jsonl")
            ranked_path = os.path.join(tmpdir, "ranked.jsonl")
            shortlisted_path = os.path.join(tmpdir, "shortlisted.jsonl")
            metadata_path = os.path.join(tmpdir, "metadata.jsonl")
            audit_path = os.path.join(tmpdir, "collection_audit.json")

            self.assertEqual(
                cli_main(
                    [
                        "merge-collection-candidates",
                        "--input",
                        fetch_output,
                        "--output",
                        candidates_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "rank-collection-candidates",
                        "--input",
                        candidates_path,
                        "--output",
                        ranked_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "shortlist-collection-candidates",
                        "--input",
                        ranked_path,
                        "--output",
                        shortlisted_path,
                        "--metadata-output",
                        metadata_path,
                        "--target-per-class",
                        "1",
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "audit-collection-batch",
                        "--batch-spec",
                        batch_path,
                        "--candidates",
                        candidates_path,
                        "--shortlisted-candidates",
                        shortlisted_path,
                        "--total-raw-fetch-records",
                        "3",
                        "--output",
                        audit_path,
                    ]
                ),
                0,
            )
            audit_payload = json.loads(Path(audit_path).read_text(encoding="utf-8"))
            self.assertEqual(audit_payload["total_raw_fetch_records"], 3)
            self.assertEqual(
                audit_payload["notes"],
                ["releaseability_precheck counts are zero until normalize-papers has been run"],
            )
            shortlisted = load_jsonl(shortlisted_path, loader=collection_candidate_record_from_dict)
            self.assertEqual(len(shortlisted), 1)


class PaperReviewBatchTests(unittest.TestCase):
    def test_build_paper_review_batch_entries_and_forms(self):
        papers = [
            make_source_paper(paper_id="PMID:1", study_class=StudyClass.HUMAN_OBSERVATIONAL, claim_mode=ClaimMode.CONFIRMATORY),
            make_source_paper(paper_id="PMID:2", study_class=StudyClass.MECHANISTIC_EXPERIMENTAL, claim_mode=ClaimMode.EXPLORATORY),
        ]
        hints = [suggest_governance_metadata_hints(papers[0]), suggest_governance_metadata_hints(papers[1])]
        entries = build_paper_review_batch_entries(papers, hints, batch_id="paper_review_v1")
        report = build_paper_review_batch_report(entries)
        scientific_forms = build_paper_scientific_review_forms(entries, reviewer_ids=("r1", "r2"))
        writing_forms = build_paper_writing_review_forms(entries, reviewer_ids=("r1", "r2"))

        self.assertEqual(len(entries), 2)
        self.assertIsInstance(entries[0], PaperReviewBatchEntry)
        self.assertEqual(report.total_papers, 2)
        self.assertIsInstance(report, PaperReviewBatchReport)
        self.assertEqual(len(scientific_forms), 4)
        self.assertEqual(len(writing_forms), 4)
        self.assertIsInstance(scientific_forms[0], PaperScientificReviewForm)
        self.assertIsInstance(writing_forms[0], PaperWritingReviewForm)
        self.assertTrue(all(value is None for value in scientific_forms[0].critical_domains.values()))
        self.assertTrue(all(value is None for value in writing_forms[0].critical_domains.values()))

    def test_build_paper_review_batch_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            hints_path = os.path.join(tmpdir, "hints.jsonl")
            entries_path = os.path.join(tmpdir, "entries.jsonl")
            scientific_path = os.path.join(tmpdir, "scientific.jsonl")
            writing_path = os.path.join(tmpdir, "writing.jsonl")
            summary_path = os.path.join(tmpdir, "summary.json")

            papers = [
                make_source_paper(paper_id="PMID:1"),
                make_source_paper(paper_id="PMID:2", study_class=StudyClass.METHODS_RESOURCE),
            ]
            hints = [suggest_governance_metadata_hints(paper) for paper in papers]
            write_jsonl(papers_path, papers)
            write_jsonl(hints_path, hints)

            self.assertEqual(
                cli_main(
                    [
                        "build-paper-review-batch",
                        "--papers",
                        papers_path,
                        "--metadata-hints",
                        hints_path,
                        "--entries-output",
                        entries_path,
                        "--scientific-forms-output",
                        scientific_path,
                        "--writing-forms-output",
                        writing_path,
                        "--summary-output",
                        summary_path,
                        "--batch-id",
                        "paper_review_v1",
                        "--reviewers",
                        "r1",
                        "r2",
                    ]
                ),
                0,
            )

            entries = load_jsonl(entries_path, loader=paper_review_batch_entry_from_dict)
            scientific_forms = load_jsonl(scientific_path, loader=paper_scientific_review_form_from_dict)
            writing_forms = load_jsonl(writing_path, loader=paper_writing_review_form_from_dict)
            summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))

            self.assertEqual(len(entries), 2)
            self.assertEqual(len(scientific_forms), 4)
            self.assertEqual(len(writing_forms), 4)
            self.assertEqual(summary["total_papers"], 2)


class PaperReviewFlowTests(unittest.TestCase):
    def test_paper_review_flow_helpers(self):
        papers = [
            make_source_paper(
                paper_id="PMID:1",
                study_class=StudyClass.HUMAN_OBSERVATIONAL,
                claim_mode=ClaimMode.CONFIRMATORY,
            ),
            make_source_paper(
                paper_id="PMID:2",
                study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                claim_mode=ClaimMode.EXPLORATORY,
            ),
        ]
        hints = [suggest_governance_metadata_hints(paper) for paper in papers]
        entries = build_paper_review_batch_entries(papers, hints, batch_id="paper_review_v1")
        scientific_forms = list(build_paper_scientific_review_forms(entries, reviewer_ids=("r1", "r2")))
        writing_forms = list(build_paper_writing_review_forms(entries, reviewer_ids=("r1", "r2")))

        scientific_forms.append(
            PaperScientificReviewForm(
                batch_id="paper_review_v1",
                paper_id="PMID:1",
                reviewer_id="r1",
                study_class_override=StudyClass.HUMAN_INTERVENTIONAL,
                critical_domains={
                    domain: DomainOutcome.PASS for domain in ScientificCriticalDomain
                },
                supporting_domains={
                    domain: DomainOutcome.PASS for domain in ScientificSupportingDomain
                },
                recommended_standards=(StandardId.STROBE, StandardId.MDAR),
                applied_standards=(StandardId.STROBE, StandardId.MDAR),
                standard_outcomes={
                    StandardId.STROBE: DomainOutcome.PASS,
                    StandardId.MDAR: DomainOutcome.PASS,
                },
                completed=True,
            )
        )
        writing_forms.append(
            PaperWritingReviewForm(
                batch_id="paper_review_v1",
                paper_id="PMID:1",
                reviewer_id="r1",
                critical_domains={
                    domain: DomainOutcome.PASS for domain in WritingCriticalDomain
                },
                supporting_domains={
                    domain: DomainOutcome.PASS for domain in WritingSupportingDomain
                },
                completed=True,
            )
        )
        merged_scientific = merge_paper_scientific_review_forms(scientific_forms)
        merged_writing = merge_paper_writing_review_forms(writing_forms)
        self.assertEqual(len(merged_scientific), 4)
        self.assertEqual(len(merged_writing), 4)
        scientific_lookup = {(form.paper_id, form.reviewer_id): form for form in merged_scientific}
        writing_lookup = {(form.paper_id, form.reviewer_id): form for form in merged_writing}
        self.assertEqual(
            scientific_lookup[("PMID:1", "r1")].study_class_override,
            StudyClass.HUMAN_INTERVENTIONAL,
        )
        self.assertTrue(writing_lookup[("PMID:1", "r1")].completed)

        adjudications = build_paper_review_adjudication_shells(
            entries,
            adjudicator_id="adj1",
            reviewer_ids=("r1", "r2"),
        )
        self.assertEqual(len(adjudications), 2)

        completed_scientific = []
        completed_writing = []
        for form in merged_scientific:
            if form.paper_id == "PMID:1":
                completed_scientific.append(
                    PaperScientificReviewForm(
                        batch_id=form.batch_id,
                        paper_id=form.paper_id,
                        reviewer_id=form.reviewer_id,
                        study_class_override=form.study_class_override,
                        claim_mode_override=form.claim_mode_override,
                        modality_overlay_overrides=form.modality_overlay_overrides,
                        critical_domains={
                            domain: DomainOutcome.PASS for domain in ScientificCriticalDomain
                        },
                        supporting_domains={
                            domain: DomainOutcome.PASS for domain in ScientificSupportingDomain
                        },
                        recommended_standards=form.recommended_standards,
                        applied_standards=form.recommended_standards,
                        standard_outcomes={
                            standard: DomainOutcome.PASS for standard in form.recommended_standards
                        },
                        completed=True,
                    )
                )
            else:
                completed_scientific.append(form)
        for form in merged_writing:
            if form.paper_id == "PMID:1":
                completed_writing.append(
                    PaperWritingReviewForm(
                        batch_id=form.batch_id,
                        paper_id=form.paper_id,
                        reviewer_id=form.reviewer_id,
                        critical_domains={
                            domain: DomainOutcome.PASS for domain in WritingCriticalDomain
                        },
                        supporting_domains={
                            domain: DomainOutcome.PASS for domain in WritingSupportingDomain
                        },
                        completed=True,
                    )
                )
            else:
                completed_writing.append(form)

        queue = build_paper_review_queue(
            entries,
            completed_scientific,
            completed_writing,
            adjudications,
            reviewer_ids=("r1", "r2"),
        )
        self.assertIsInstance(queue[0], PaperReviewQueueEntry)
        queue_lookup = {entry.paper_id: entry for entry in queue}
        self.assertEqual(queue_lookup["PMID:1"].status, "ready_for_adjudication")
        self.assertEqual(queue_lookup["PMID:2"].status, "awaiting_reviews")

        progress = summarize_paper_review_progress(
            entries,
            completed_scientific,
            completed_writing,
            adjudications,
            reviewer_ids=("r1", "r2"),
        )
        self.assertIsInstance(progress, PaperReviewProgressSummary)
        self.assertEqual(progress.queue_status_counts["ready_for_adjudication"], 1)

        finalized_adjudications = (
            PaperReviewAdjudicationRecord(
                batch_id="paper_review_v1",
                paper_id="PMID:1",
                adjudicator_id="adj1",
                final_study_class=StudyClass.HUMAN_OBSERVATIONAL,
                final_claim_mode=ClaimMode.CONFIRMATORY,
                scientific_critical_domains={
                    domain: DomainOutcome.PASS for domain in ScientificCriticalDomain
                },
                scientific_supporting_domains={
                    domain: DomainOutcome.PASS for domain in ScientificSupportingDomain
                },
                applied_standards=(StandardId.STROBE, StandardId.MDAR),
                standard_outcomes={
                    StandardId.STROBE: DomainOutcome.PASS,
                    StandardId.MDAR: DomainOutcome.PASS,
                },
                writing_critical_domains={
                    domain: DomainOutcome.PASS for domain in WritingCriticalDomain
                },
                writing_supporting_domains={
                    domain: DomainOutcome.PASS for domain in WritingSupportingDomain
                },
                finalized=True,
                rationale=("looks good",),
                source_reviewer_ids=("r1", "r2"),
            ),
        )
        finalized_records = finalize_paper_adjudications(finalized_adjudications)
        self.assertEqual(len(finalized_records), 1)
        self.assertIsInstance(finalized_records[0], AdjudicatedPaperReviewRecord)
        self.assertEqual(finalized_records[0].scientific_review.notes, ("looks good",))

    def test_paper_review_flow_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            hints_path = os.path.join(tmpdir, "hints.jsonl")
            entries_path = os.path.join(tmpdir, "entries.jsonl")
            scientific_path = os.path.join(tmpdir, "scientific.jsonl")
            writing_path = os.path.join(tmpdir, "writing.jsonl")
            adjudications_path = os.path.join(tmpdir, "adjudications.jsonl")
            queue_path = os.path.join(tmpdir, "queue.jsonl")
            progress_path = os.path.join(tmpdir, "progress.json")
            finalized_path = os.path.join(tmpdir, "finalized.jsonl")

            papers = [
                make_source_paper(paper_id="PMID:1"),
                make_source_paper(paper_id="PMID:2", study_class=StudyClass.METHODS_RESOURCE),
            ]
            hints = [suggest_governance_metadata_hints(paper) for paper in papers]
            write_jsonl(papers_path, papers)
            write_jsonl(hints_path, hints)

            self.assertEqual(
                cli_main(
                    [
                        "build-paper-review-batch",
                        "--papers",
                        papers_path,
                        "--metadata-hints",
                        hints_path,
                        "--entries-output",
                        entries_path,
                        "--scientific-forms-output",
                        scientific_path,
                        "--writing-forms-output",
                        writing_path,
                        "--batch-id",
                        "paper_review_v1",
                        "--reviewers",
                        "r1",
                        "r2",
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-paper-review-adjudication-shells",
                        "--entries",
                        entries_path,
                        "--output",
                        adjudications_path,
                        "--adjudicator",
                        "adj1",
                        "--reviewers",
                        "r1",
                        "r2",
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-paper-review-queue",
                        "--entries",
                        entries_path,
                        "--scientific-forms",
                        scientific_path,
                        "--writing-forms",
                        writing_path,
                        "--adjudications",
                        adjudications_path,
                        "--reviewers",
                        "r1",
                        "r2",
                        "--output",
                        queue_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "summarize-paper-review-progress",
                        "--entries",
                        entries_path,
                        "--scientific-forms",
                        scientific_path,
                        "--writing-forms",
                        writing_path,
                        "--adjudications",
                        adjudications_path,
                        "--reviewers",
                        "r1",
                        "r2",
                        "--output",
                        progress_path,
                    ]
                ),
                0,
            )

            queue = load_jsonl(queue_path, loader=paper_review_queue_entry_from_dict)
            progress = paper_review_progress_summary_from_dict(
                json.loads(Path(progress_path).read_text(encoding="utf-8"))
            )
            self.assertTrue(all(entry.status == "awaiting_reviews" for entry in queue))
            self.assertEqual(progress.queue_status_counts["awaiting_reviews"], 2)

            adjudications = load_jsonl(adjudications_path, loader=paper_review_adjudication_record_from_dict)
            finalized_records = [
                PaperReviewAdjudicationRecord(
                    batch_id=record.batch_id,
                    paper_id=record.paper_id,
                    adjudicator_id=record.adjudicator_id,
                    final_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                    final_claim_mode=ClaimMode.EXPLORATORY,
                    scientific_critical_domains={
                        domain: DomainOutcome.PASS for domain in ScientificCriticalDomain
                    },
                    scientific_supporting_domains={
                        domain: DomainOutcome.PASS for domain in ScientificSupportingDomain
                    },
                    applied_standards=(StandardId.MDAR,),
                    standard_outcomes={StandardId.MDAR: DomainOutcome.PASS},
                    writing_critical_domains={
                        domain: DomainOutcome.PASS for domain in WritingCriticalDomain
                    },
                    writing_supporting_domains={
                        domain: DomainOutcome.PASS for domain in WritingSupportingDomain
                    },
                    finalized=(record.paper_id == "PMID:1"),
                    rationale=("finalized",) if record.paper_id == "PMID:1" else (),
                    source_reviewer_ids=record.source_reviewer_ids,
                )
                for record in adjudications
            ]
            write_jsonl(adjudications_path, finalized_records)

            self.assertEqual(
                cli_main(
                    [
                        "finalize-paper-adjudications",
                        "--adjudications",
                        adjudications_path,
                        "--output",
                        finalized_path,
                    ]
                ),
                0,
            )
            finalized = load_jsonl(finalized_path, loader=adjudicated_paper_review_record_from_dict)
            self.assertEqual(len(finalized), 1)
            self.assertEqual(finalized[0].paper_id, "PMID:1")


class PaperQualificationFlowTests(unittest.TestCase):
    def test_build_paper_review_packets(self):
        papers = [
            make_source_paper(
                paper_id="PMID:1",
                title="Paper one",
                publication_year=2024,
                metadata={
                    "abstract": "Figure 1 shows the result.",
                    "journal": "eLife",
                    "doi": "10.1000/example1",
                    "pmid": "1",
                    "pmcid": "PMC1",
                    "oa_fulltext_available": "true",
                    "license": "https://creativecommons.org/licenses/by/4.0/",
                    "open_review_signal": "true",
                    "benchmark_ready_signal_count": "4",
                },
            ),
            make_source_paper(
                paper_id="PMID:2",
                title="Paper two",
                publication_year=2022,
                metadata={
                    "abstract": "Minimal abstract.",
                    "journal": "Journal",
                    "doi": "10.1000/example2",
                    "pmid": "2",
                    "benchmark_ready_signal_count": "1",
                },
            ),
        ]
        entries = (
            PaperReviewBatchEntry(
                batch_id="paper_review_v1",
                paper_id="PMID:1",
                title="Paper one",
                publication_year=2024,
                publication_status=PublicationStatus.PUBLISHED,
                peer_reviewed=True,
                candidate_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                candidate_claim_mode=ClaimMode.EXPLORATORY,
                metadata_hint_warnings=(),
                recommended_standards=(StandardId.MDAR,),
            ),
            PaperReviewBatchEntry(
                batch_id="paper_review_v1",
                paper_id="PMID:2",
                title="Paper two",
                publication_year=2022,
                publication_status=PublicationStatus.PUBLISHED,
                peer_reviewed=True,
                candidate_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                candidate_claim_mode=ClaimMode.EXPLORATORY,
                metadata_hint_warnings=("hint warning",),
                recommended_standards=(StandardId.MDAR,),
            ),
        )
        packaging_records = build_packaging_review_priors(papers)
        packets = build_paper_review_packets(entries, papers, packaging_records)
        self.assertEqual(len(packets), 2)
        self.assertIsInstance(packets[0], PaperReviewPacket)
        self.assertEqual(packets[0].paper_id, "PMID:1")
        self.assertEqual(packets[0].review_priority_rank, 1)
        self.assertEqual(packets[1].review_priority_rank, 2)
        self.assertTrue(packets[0].oa_fulltext_available)
        self.assertIn(SafeDerivedArtifact.CITATION_METADATA, packets[0].safe_derived_artifacts)

        report = build_paper_review_packet_report(packets)
        self.assertIsInstance(report, PaperReviewPacketReport)
        self.assertEqual(report.total_packets, 2)
        self.assertEqual(report.top_priority_paper_ids[0], "PMID:1")

    def test_build_paper_review_packets_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            entries_path = os.path.join(tmpdir, "entries.jsonl")
            packaging_path = os.path.join(tmpdir, "packaging.jsonl")
            packets_path = os.path.join(tmpdir, "packets.jsonl")
            summary_path = os.path.join(tmpdir, "packet_summary.json")

            papers = [
                make_source_paper(
                    paper_id="PMID:1",
                    metadata={
                        "abstract": "Figure 1 shows the result.",
                        "journal": "eLife",
                        "doi": "10.1000/example1",
                        "pmid": "1",
                        "pmcid": "PMC1",
                        "oa_fulltext_available": "true",
                        "license": "https://creativecommons.org/licenses/by/4.0/",
                        "benchmark_ready_signal_count": "4",
                    },
                )
            ]
            entries = [
                PaperReviewBatchEntry(
                    batch_id="paper_review_v1",
                    paper_id="PMID:1",
                    title="Example",
                    publication_year=2024,
                    publication_status=PublicationStatus.PUBLISHED,
                    peer_reviewed=True,
                    candidate_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                    candidate_claim_mode=ClaimMode.EXPLORATORY,
                    recommended_standards=(StandardId.MDAR,),
                )
            ]
            write_jsonl(papers_path, papers)
            write_jsonl(entries_path, entries)
            write_jsonl(packaging_path, build_packaging_review_priors(papers))

            self.assertEqual(
                cli_main(
                    [
                        "build-paper-review-packets",
                        "--entries",
                        entries_path,
                        "--papers",
                        papers_path,
                        "--packaging-reviews",
                        packaging_path,
                        "--output",
                        packets_path,
                        "--summary-output",
                        summary_path,
                    ]
                ),
                0,
            )
            packets = load_jsonl(packets_path, loader=paper_review_packet_from_dict)
            summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
            self.assertEqual(len(packets), 1)
            self.assertEqual(packets[0].review_priority_rank, 1)
            self.assertEqual(summary["total_packets"], 1)

    def test_build_paper_review_workloads(self):
        papers = [
            make_source_paper(
                paper_id="PMID:1",
                metadata={
                    "abstract": "Figure 1 shows the result.",
                    "journal": "eLife",
                    "doi": "10.1000/example1",
                    "pmid": "1",
                    "pmcid": "PMC1",
                    "oa_fulltext_available": "true",
                    "license": "https://creativecommons.org/licenses/by/4.0/",
                    "benchmark_ready_signal_count": "4",
                },
            )
        ]
        entries = (
            PaperReviewBatchEntry(
                batch_id="paper_review_v1",
                paper_id="PMID:1",
                title="Example",
                publication_year=2024,
                publication_status=PublicationStatus.PUBLISHED,
                peer_reviewed=True,
                candidate_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                candidate_claim_mode=ClaimMode.EXPLORATORY,
                recommended_standards=(StandardId.MDAR,),
            ),
        )
        packets = build_paper_review_packets(entries, papers, build_packaging_review_priors(papers))
        scientific_forms = build_paper_scientific_review_forms(entries, reviewer_ids=("rev_a", "rev_b"))
        writing_forms = build_paper_writing_review_forms(entries, reviewer_ids=("rev_a", "rev_b"))
        assignments = build_paper_reviewer_assignments(
            packets=packets,
            scientific_forms=scientific_forms,
            writing_forms=writing_forms,
            reviewer_ids=("rev_a", "rev_b"),
        )
        self.assertEqual(len(assignments), 2)
        self.assertIsInstance(assignments[0], PaperReviewerAssignment)
        self.assertEqual(assignments[0].review_priority_rank, 1)
        self.assertEqual(assignments[0].scientific_review_form.reviewer_id, assignments[0].reviewer_id)

        report = build_paper_review_workload_report(assignments)
        self.assertIsInstance(report, PaperReviewWorkloadReport)
        self.assertEqual(report.total_assignments, 2)
        self.assertEqual(report.reviewer_assignment_counts["rev_a"], 1)

    def test_build_paper_review_workloads_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            entries_path = os.path.join(tmpdir, "entries.jsonl")
            packaging_path = os.path.join(tmpdir, "packaging.jsonl")
            packets_path = os.path.join(tmpdir, "packets.jsonl")
            scientific_path = os.path.join(tmpdir, "scientific.jsonl")
            writing_path = os.path.join(tmpdir, "writing.jsonl")
            output_dir = os.path.join(tmpdir, "workloads")

            papers = [
                make_source_paper(
                    paper_id="PMID:1",
                    metadata={
                        "abstract": "Figure 1 shows the result.",
                        "journal": "eLife",
                        "doi": "10.1000/example1",
                        "pmid": "1",
                        "pmcid": "PMC1",
                        "oa_fulltext_available": "true",
                        "license": "https://creativecommons.org/licenses/by/4.0/",
                        "benchmark_ready_signal_count": "4",
                    },
                )
            ]
            entries = [
                PaperReviewBatchEntry(
                    batch_id="paper_review_v1",
                    paper_id="PMID:1",
                    title="Example",
                    publication_year=2024,
                    publication_status=PublicationStatus.PUBLISHED,
                    peer_reviewed=True,
                    candidate_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                    candidate_claim_mode=ClaimMode.EXPLORATORY,
                    recommended_standards=(StandardId.MDAR,),
                )
            ]
            write_jsonl(papers_path, papers)
            write_jsonl(entries_path, entries)
            write_jsonl(packaging_path, build_packaging_review_priors(papers))
            write_jsonl(packets_path, build_paper_review_packets(entries, papers, build_packaging_review_priors(papers)))
            write_jsonl(scientific_path, build_paper_scientific_review_forms(entries, reviewer_ids=("rev_a", "rev_b")))
            write_jsonl(writing_path, build_paper_writing_review_forms(entries, reviewer_ids=("rev_a", "rev_b")))

            self.assertEqual(
                cli_main(
                    [
                        "build-paper-review-workloads",
                        "--packets",
                        packets_path,
                        "--scientific-forms",
                        scientific_path,
                        "--writing-forms",
                        writing_path,
                        "--reviewers",
                        "rev_a",
                        "rev_b",
                        "--output-dir",
                        output_dir,
                    ]
                ),
                0,
            )
            reviewer_a_path = os.path.join(output_dir, "rev_a_paper_review_assignments.jsonl")
            reviewer_b_path = os.path.join(output_dir, "rev_b_paper_review_assignments.jsonl")
            summary_path = os.path.join(output_dir, "paper_review_workload_summary.json")
            reviewer_a = load_jsonl(reviewer_a_path, loader=paper_reviewer_assignment_from_dict)
            reviewer_b = load_jsonl(reviewer_b_path, loader=paper_reviewer_assignment_from_dict)
            summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
            self.assertEqual(len(reviewer_a), 1)
            self.assertEqual(len(reviewer_b), 1)
            self.assertEqual(summary["total_assignments"], 2)
            self.assertEqual(summary["reviewer_assignment_counts"]["rev_a"], 1)

    def test_build_paper_review_handoff_report(self):
        papers = [
            make_source_paper(
                paper_id="PMID:1",
                metadata={
                    "abstract": "Figure 1 shows the result.",
                    "journal": "eLife",
                    "doi": "10.1000/example1",
                    "pmid": "1",
                    "pmcid": "PMC1",
                    "oa_fulltext_available": "true",
                    "license": "https://creativecommons.org/licenses/by/4.0/",
                    "benchmark_ready_signal_count": "4",
                    "open_review_signal": "true",
                },
            )
        ]
        entries = (
            PaperReviewBatchEntry(
                batch_id="paper_review_v1",
                paper_id="PMID:1",
                title="Example",
                publication_year=2024,
                publication_status=PublicationStatus.PUBLISHED,
                peer_reviewed=True,
                candidate_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                candidate_claim_mode=ClaimMode.EXPLORATORY,
                metadata_hint_warnings=("warning",),
                recommended_standards=(StandardId.MDAR,),
            ),
        )
        packets = build_paper_review_packets(entries, papers, build_packaging_review_priors(papers))
        assignments = build_paper_reviewer_assignments(
            packets=packets,
            scientific_forms=build_paper_scientific_review_forms(entries, reviewer_ids=("rev_a",)),
            writing_forms=build_paper_writing_review_forms(entries, reviewer_ids=("rev_a",)),
            reviewer_ids=("rev_a",),
        )
        report = build_paper_reviewer_handoff_report(assignments, reviewer_id="rev_a", top_priority_count=5)
        self.assertIsInstance(report, PaperReviewerHandoffReport)
        self.assertEqual(report.total_assignments, 1)
        self.assertEqual(report.metadata_warning_count, 1)
        self.assertEqual(report.open_review_signal_count, 1)
        self.assertEqual(report.top_priority_paper_ids, ("PMID:1",))

    def test_build_paper_review_handoff_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = [
                make_source_paper(
                    paper_id="PMID:1",
                    metadata={
                        "abstract": "Figure 1 shows the result.",
                        "journal": "eLife",
                        "doi": "10.1000/example1",
                        "pmid": "1",
                        "pmcid": "PMC1",
                        "oa_fulltext_available": "true",
                        "license": "https://creativecommons.org/licenses/by/4.0/",
                        "benchmark_ready_signal_count": "4",
                    },
                )
            ]
            entries = [
                PaperReviewBatchEntry(
                    batch_id="paper_review_v1",
                    paper_id="PMID:1",
                    title="Example",
                    publication_year=2024,
                    publication_status=PublicationStatus.PUBLISHED,
                    peer_reviewed=True,
                    candidate_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                    candidate_claim_mode=ClaimMode.EXPLORATORY,
                    recommended_standards=(StandardId.MDAR,),
                )
            ]
            packets = build_paper_review_packets(entries, papers, build_packaging_review_priors(papers))
            assignments = build_paper_reviewer_assignments(
                packets=packets,
                scientific_forms=build_paper_scientific_review_forms(entries, reviewer_ids=("rev_a", "rev_b")),
                writing_forms=build_paper_writing_review_forms(entries, reviewer_ids=("rev_a", "rev_b")),
                reviewer_ids=("rev_a", "rev_b"),
            )
            assignments_a_path = os.path.join(tmpdir, "rev_a_assignments.jsonl")
            assignments_b_path = os.path.join(tmpdir, "rev_b_assignments.jsonl")
            output_dir = os.path.join(tmpdir, "handoff")
            write_jsonl(assignments_a_path, [item for item in assignments if item.reviewer_id == "rev_a"])
            write_jsonl(assignments_b_path, [item for item in assignments if item.reviewer_id == "rev_b"])

            self.assertEqual(
                cli_main(
                    [
                        "build-paper-review-handoff",
                        "--assignments",
                        assignments_a_path,
                        assignments_b_path,
                        "--reviewers",
                        "rev_a",
                        "rev_b",
                        "--output-dir",
                        output_dir,
                    ]
                ),
                0,
            )
            summary = paper_reviewer_handoff_report_from_dict(
                json.loads(Path(os.path.join(output_dir, "rev_a_handoff_summary.json")).read_text(encoding="utf-8"))
            )
            markdown = Path(os.path.join(output_dir, "rev_a_handoff.md")).read_text(encoding="utf-8")
            self.assertEqual(summary.total_assignments, 1)
            self.assertIn("Paper Review Handoff: rev_a", markdown)
            self.assertIn("PMID:1", markdown)

    def test_build_packaging_review_priors_and_qualification_records(self):
        papers = [
            make_source_paper(
                paper_id="DOI:10.1000/example",
                metadata={
                    "abstract": "Results showed a significant reduction in tumor burden. ClinicalTrials.gov NCT01234567.",
                    "benchmark_ready_signal_count": "3",
                    "doi": "10.1000/example",
                    "pmid": "12345",
                    "pmcid": "PMC12345",
                    "oa_fulltext_available": "true",
                    "license": "https://creativecommons.org/licenses/by/4.0/",
                },
            )
        ]
        packaging_records = build_packaging_review_priors(papers)
        self.assertEqual(len(packaging_records), 1)
        self.assertIsInstance(packaging_records[0], PaperPackagingReviewRecord)
        self.assertEqual(
            packaging_records[0].packaging_review.domain_outcomes[PackagingDomain.RELEASEABILITY],
            DomainOutcome.PASS,
        )
        self.assertIn(
            SafeDerivedArtifact.CITATION_METADATA,
            packaging_records[0].packaging_review.safe_derived_artifacts,
        )

        adjudicated_reviews = (
            AdjudicatedPaperReviewRecord(
                batch_id="paper_review_v1",
                paper_id="DOI:10.1000/example",
                scientific_review=make_scientific_review(),
                writing_review=make_writing_review(),
                final_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                final_claim_mode=ClaimMode.EXPLORATORY,
                adjudicator_id="adj1",
                finalized=True,
                rationale=("approved",),
            ),
        )
        records = build_paper_qualification_records(
            papers=papers,
            adjudicated_reviews=adjudicated_reviews,
            packaging_reviews=packaging_records,
        )
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], PaperQualificationRecord)
        self.assertEqual(records[0].decision.candidate_tier, CandidateTier.PUBLIC_GOLD_CANDIDATE)

        report = build_paper_qualification_batch_report(
            papers=papers,
            adjudicated_reviews=adjudicated_reviews,
            packaging_reviews=packaging_records,
            records=records,
        )
        self.assertIsInstance(report, PaperQualificationBatchReport)
        self.assertEqual(report.decisions_written, 1)
        self.assertEqual(report.public_writing_eligible_count, 1)

    def test_build_packaging_review_priors_uses_enriched_evidence_for_reconstructability(self):
        papers = [
            make_source_paper(
                paper_id="DOI:10.1000/enriched",
                metadata={
                    "abstract": "A murine model paper with structured methods and results.",
                    "benchmark_ready_signal_count": "1",
                    "doi": "10.1000/enriched",
                    "pmid": "22222",
                    "pmcid": "PMC22222",
                    "oa_fulltext_available": "true",
                    "license": "https://creativecommons.org/licenses/by/4.0/",
                    "methods_text": "Mice were randomized into treatment arms and assayed weekly.",
                    "results_text": "Treatment reduced lesion burden compared with vehicle.",
                    "figure_captions": [
                        "Figure 1 shows lesion burden across treatment groups."
                    ],
                },
            )
        ]
        packaging_records = build_packaging_review_priors(papers)
        review = packaging_records[0].packaging_review
        self.assertEqual(
            review.domain_outcomes[PackagingDomain.EVIDENCE_PACK_RECONSTRUCTABILITY],
            DomainOutcome.PASS,
        )
        self.assertIn(
            SafeDerivedArtifact.PUBLISHED_AGGREGATE_STATISTICS,
            review.safe_derived_artifacts,
        )
        self.assertIn(
            SafeDerivedArtifact.PUBLISHED_FIGURE_TABLE_OBSERVATIONS,
            review.safe_derived_artifacts,
        )

    def test_build_packaging_review_priors_and_qualification_records_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            packaging_path = os.path.join(tmpdir, "packaging.jsonl")
            packaging_summary_path = os.path.join(tmpdir, "packaging_summary.json")
            adjudicated_path = os.path.join(tmpdir, "adjudicated_reviews.jsonl")
            decisions_path = os.path.join(tmpdir, "paper_decisions.jsonl")
            decisions_summary_path = os.path.join(tmpdir, "paper_decisions_summary.json")

            papers = [
                make_source_paper(
                    paper_id="DOI:10.1000/example",
                    metadata={
                        "abstract": "Table 1 reports the effect size. ClinicalTrials.gov NCT01234567.",
                        "benchmark_ready_signal_count": "3",
                        "doi": "10.1000/example",
                        "pmid": "12345",
                        "pmcid": "PMC12345",
                        "oa_fulltext_available": "true",
                        "license": "https://creativecommons.org/licenses/by/4.0/",
                    },
                ),
                make_source_paper(
                    paper_id="DOI:10.1000/missing",
                    metadata={"doi": "10.1000/missing"},
                ),
            ]
            adjudicated_reviews = [
                AdjudicatedPaperReviewRecord(
                    batch_id="paper_review_v1",
                    paper_id="DOI:10.1000/example",
                    scientific_review=make_scientific_review(),
                    writing_review=make_writing_review(),
                    final_study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                    final_claim_mode=ClaimMode.EXPLORATORY,
                    adjudicator_id="adj1",
                    finalized=True,
                    rationale=("approved",),
                )
            ]
            write_jsonl(papers_path, papers)
            write_jsonl(adjudicated_path, adjudicated_reviews)

            self.assertEqual(
                cli_main(
                    [
                        "build-packaging-review-priors",
                        "--papers",
                        papers_path,
                        "--output",
                        packaging_path,
                        "--summary-output",
                        packaging_summary_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-paper-qualification-decisions",
                        "--papers",
                        papers_path,
                        "--adjudicated-reviews",
                        adjudicated_path,
                        "--packaging-reviews",
                        packaging_path,
                        "--output",
                        decisions_path,
                        "--summary-output",
                        decisions_summary_path,
                    ]
                ),
                0,
            )
            packaging_records = load_jsonl(packaging_path, loader=paper_packaging_review_record_from_dict)
            decisions = load_jsonl(decisions_path, loader=paper_qualification_record_from_dict)
            summary = paper_qualification_batch_report_from_dict(
                json.loads(Path(decisions_summary_path).read_text(encoding="utf-8"))
            )
            self.assertEqual(len(packaging_records), 2)
            self.assertEqual(len(decisions), 1)
            self.assertEqual(decisions[0].paper_id, "DOI:10.1000/example")
            self.assertEqual(summary.decisions_written, 1)
            self.assertIn("DOI:10.1000/missing", summary.missing_adjudicated_review_paper_ids)

    def test_build_auto_review_source_bundles_metadata_only(self):
        paper = make_source_paper(
            paper_id="PMID:auto-meta",
            metadata={
                "abstract": "This abstract mentions ClinicalTrials.gov NCT01234567 but has no methods or results sections.",
                "doi": "10.1000/auto-meta",
                "pmid": "100",
            },
        )
        bundles = build_auto_review_source_bundles((paper,))
        self.assertEqual(len(bundles), 1)
        bundle = bundles[0]
        self.assertEqual(bundle.bundle_completeness, AutoReviewBundleCompleteness.METADATA_ONLY)
        self.assertIn("NCT01234567", bundle.trial_registry_ids)
        audit = audit_auto_review_source_bundles(bundles)
        self.assertEqual(audit.total_bundles, 1)
        self.assertEqual(audit.completeness_counts["metadata_only"], 1)

    def test_build_auto_review_source_bundles_infers_methods_from_abstract(self):
        paper = make_source_paper(
            paper_id="PMID:auto-infer-methods",
            study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
            claim_mode=ClaimMode.EXPLORATORY,
            metadata={
                "abstract": (
                    "We used CRISPR perturbation in metastatic cell lines and profiled pathway activity. "
                    "The results show reduced migration in Figure 2."
                ),
                "results_text": "Figure 2 shows reduced migration and pathway inhibition after perturbation.",
                "figure_captions": [{"pointer": "Fig2", "text": "Reduced migration after CRISPR perturbation."}],
                "doi": "10.1000/auto-infer-methods",
                "pmid": "111",
            },
        )
        bundle = build_auto_review_source_bundles((paper,))[0]
        self.assertIn("CRISPR perturbation", bundle.methods_text)
        self.assertEqual(bundle.provenance_fields["methods_text"], "metadata.abstract:derived_methods")
        self.assertEqual(bundle.bundle_completeness, AutoReviewBundleCompleteness.REVIEW_READY)

    def test_build_auto_review_source_bundles_infers_results_from_abstract(self):
        paper = make_source_paper(
            paper_id="PMID:auto-infer-results",
            study_class=StudyClass.METHODS_RESOURCE,
            claim_mode=ClaimMode.RESOURCE_RELEASE,
            metadata={
                "abstract": (
                    "This article presents a visualization toolkit for volumetric biology data. "
                    "The results show benchmark rendering performance and support for multiple database entries."
                ),
                "methods_text": "We implemented the toolkit on a local server and documented the workflow.",
                "figure_captions": [{"pointer": "Fig1", "text": "Toolkit rendering benchmark."}],
                "table_snippets": [{"pointer": "Table1", "text": "Database entry support matrix."}],
                "doi": "10.1000/auto-infer-results",
                "pmid": "112",
            },
        )
        bundle = build_auto_review_source_bundles((paper,))[0]
        self.assertIn("benchmark rendering performance", bundle.results_text)
        self.assertEqual(bundle.provenance_fields["results_text"], "metadata.abstract:derived_results")
        self.assertEqual(bundle.bundle_completeness, AutoReviewBundleCompleteness.REVIEW_READY)

    def test_build_auto_review_evidence_enrichments_upgrades_bundle(self):
        paper = make_source_paper(
            paper_id="PMID:auto-enrich",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            metadata={
                "abstract": "Randomized trial abstract.",
                "doi": "10.1000/auto-enrich",
                "pmid": "301",
                "pmcid": "PMC301",
            },
        )
        xml_payload = b"""
<article>
  <body>
    <sec>
      <title>Methods</title>
      <p>We randomized patients and registered the study as NCT12345678 using RRID:AB_123456.</p>
    </sec>
    <sec>
      <title>Results</title>
      <p>The intervention improved the primary endpoint.</p>
    </sec>
    <fig><caption><p>Figure 1. Primary outcome improved in the intervention arm.</p></caption></fig>
    <table-wrap>
      <caption><p>Table 1. Baseline characteristics.</p></caption>
      <table><tr><th>Arm</th><th>N</th></tr><tr><td>Control</td><td>10</td></tr></table>
    </table-wrap>
  </body>
</article>
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetch_records, enrichments = build_auto_review_evidence_enrichments(
                (paper,),
                raw_dir=tmpdir,
                fetcher=lambda url, headers=None: xml_payload,
            )
            self.assertEqual(len(fetch_records), 1)
            self.assertTrue(fetch_records[0].fetch_ok)
            self.assertEqual(len(enrichments), 1)
            enrichment = enrichments[0]
            self.assertIn("randomized patients", enrichment.methods_text.lower())
            self.assertIn("primary endpoint", enrichment.results_text.lower())
            self.assertTrue(enrichment.figure_captions)
            self.assertTrue(enrichment.table_snippets)
            self.assertIn("NCT12345678", enrichment.trial_registry_ids)
            self.assertTrue(
                any("NCT12345678" in snippet for snippet in enrichment.trial_registry_reference_snippets)
            )
            self.assertIn("RRID:AB_123456", enrichment.resource_identifiers)
            audit = audit_auto_review_evidence_enrichments(fetch_records, enrichments)
            self.assertEqual(audit.fetch_ok_count, 1)
            bundles = build_auto_review_source_bundles((paper,), evidence_enrichments=enrichments)
            self.assertEqual(bundles[0].bundle_completeness, AutoReviewBundleCompleteness.REVIEW_READY)

    def test_build_auto_review_evidence_enrichments_uses_data_availability_and_xrefs(self):
        paper = make_source_paper(
            paper_id="PMID:auto-enrich-rich",
            study_class=StudyClass.METHODS_RESOURCE,
            claim_mode=ClaimMode.RESOURCE_RELEASE,
            metadata={
                "abstract": "Resource paper abstract.",
                "doi": "10.1000/auto-enrich-rich",
                "pmid": "302",
                "pmcid": "PMC302",
            },
        )
        xml_payload = b"""
<article>
  <body>
    <sec>
      <title>Methods</title>
      <p>We developed a workflow for atlas generation.</p>
    </sec>
    <sec>
      <title>Results</title>
      <p>As shown in <xref ref-type="fig">Figure 2</xref>, retrieval improved across cohorts.</p>
      <p>Table-guided evidence in <xref ref-type="table">Table 1</xref> summarizes performance.</p>
    </sec>
    <sec>
      <title>Data Availability</title>
      <p>Data are available under GSM123456 and SRR234567. Trial registration: ACTRN12624000000000.</p>
    </sec>
    <fig>
      <label>Figure 2</label>
      <caption><p>Retrieval improved across cohorts.</p></caption>
    </fig>
    <table-wrap>
      <label>Table 1</label>
      <caption><p>Performance summary.</p></caption>
      <table><tr><th>Split</th><th>Score</th></tr><tr><td>Validation</td><td>0.91</td></tr></table>
    </table-wrap>
  </body>
</article>
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, enrichments = build_auto_review_evidence_enrichments(
                (paper,),
                raw_dir=tmpdir,
                fetcher=lambda url, headers=None: xml_payload,
            )
            enrichment = enrichments[0]
            self.assertTrue(any("Figure 2" in caption for caption in enrichment.figure_captions))
            self.assertTrue(any("Table 1" in snippet for snippet in enrichment.table_snippets))
            self.assertTrue(any("As shown in Figure 2" in snippet for snippet in enrichment.figure_reference_snippets))
            self.assertTrue(any("Table-guided evidence in Table 1" in snippet for snippet in enrichment.table_reference_snippets))
            self.assertIn("GSM123456", enrichment.resource_identifiers)
            self.assertIn("SRR234567", enrichment.resource_identifiers)
            self.assertIn("ACTRN12624000000000", enrichment.trial_registry_ids)
            self.assertTrue(
                any("ACTRN12624000000000" in snippet for snippet in enrichment.trial_registry_reference_snippets)
            )
            self.assertIn("data_availability", enrichment.provenance_fields)
            self.assertIn("figure_reference_snippets", enrichment.provenance_fields)
            self.assertIn("table_reference_snippets", enrichment.provenance_fields)
            self.assertIn("trial_registry_reference_snippets", enrichment.provenance_fields)
            self.assertIn("data_availability_section_used_for_identifier_scan", enrichment.notes)

    def test_build_auto_review_evidence_enrichments_falls_back_to_ncbi_on_http_404(self):
        paper = make_source_paper(
            paper_id="PMID:auto-enrich-ncbi-fallback",
            study_class=StudyClass.METHODS_RESOURCE,
            claim_mode=ClaimMode.RESOURCE_RELEASE,
            metadata={
                "abstract": "Non-OA paper abstract.",
                "pmcid": "PMC11179667",
            },
        )
        ncbi_payload = b"""
<pmc-articleset>
  <article>
    <body>
      <sec><title>Methods</title><p>We described an optimized workflow.</p></sec>
      <sec><title>Results</title><p>Performance improved across cohorts.</p></sec>
    </body>
  </article>
</pmc-articleset>
"""

        def fetcher(url, headers=None):
            if "ebi.ac.uk" in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            if "eutils.ncbi.nlm.nih.gov" in url:
                return ncbi_payload
            raise AssertionError(f"unexpected url: {url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            fetch_records, enrichments = build_auto_review_evidence_enrichments(
                (paper,),
                raw_dir=tmpdir,
                fetcher=fetcher,
            )
            self.assertEqual(len(fetch_records), 1)
            self.assertTrue(fetch_records[0].fetch_ok)
            self.assertIn("eutils.ncbi.nlm.nih.gov", fetch_records[0].fetch_url)
            self.assertTrue(fetch_records[0].raw_payload_path.endswith("PMC11179667.ncbi.xml"))
            self.assertEqual(len(enrichments), 1)
            self.assertIn("pmc_source:ncbi_efetch_fallback", enrichments[0].notes)
            self.assertIn("optimized workflow", enrichments[0].methods_text.lower())
            self.assertIn("cohorts", enrichments[0].results_text.lower())

    def test_build_auto_review_evidence_enrichments_records_both_errors_when_ncbi_also_fails(self):
        paper = make_source_paper(
            paper_id="PMID:auto-enrich-both-fail",
            study_class=StudyClass.METHODS_RESOURCE,
            claim_mode=ClaimMode.RESOURCE_RELEASE,
            metadata={"abstract": "x", "pmcid": "PMC99999999"},
        )

        def fetcher(url, headers=None):
            if "ebi.ac.uk" in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            if "eutils.ncbi.nlm.nih.gov" in url:
                raise urllib.error.HTTPError(url, 500, "Internal Server Error", {}, None)
            raise AssertionError(f"unexpected url: {url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            fetch_records, enrichments = build_auto_review_evidence_enrichments(
                (paper,),
                raw_dir=tmpdir,
                fetcher=fetcher,
            )
            self.assertEqual(len(fetch_records), 1)
            self.assertFalse(fetch_records[0].fetch_ok)
            self.assertIn("HTTP Error 404", fetch_records[0].error)
            self.assertIn("ncbi_fallback_error", fetch_records[0].error)
            self.assertIn("HTTP Error 500", fetch_records[0].error)
            self.assertEqual(len(enrichments), 1)
            self.assertTrue(
                any("fetch_error" in note and "404" in note for note in enrichments[0].notes)
            )
            self.assertTrue(
                any("ncbi_fallback_error" in note for note in enrichments[0].notes)
            )

    def test_build_auto_review_evidence_enrichments_does_not_fall_back_on_transient_error(self):
        paper = make_source_paper(
            paper_id="PMID:auto-enrich-transient",
            study_class=StudyClass.METHODS_RESOURCE,
            claim_mode=ClaimMode.RESOURCE_RELEASE,
            metadata={"abstract": "x", "pmcid": "PMC88888888"},
        )
        calls: list = []

        def fetcher(url, headers=None):
            calls.append(url)
            if "ebi.ac.uk" in url:
                raise urllib.error.URLError("DNS resolution failed")
            raise AssertionError(f"unexpected url: {url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            fetch_records, enrichments = build_auto_review_evidence_enrichments(
                (paper,),
                raw_dir=tmpdir,
                fetcher=fetcher,
            )
            self.assertEqual(len(calls), 1)
            self.assertIn("ebi.ac.uk", calls[0])
            self.assertEqual(len(fetch_records), 1)
            self.assertFalse(fetch_records[0].fetch_ok)
            self.assertNotIn("ncbi_fallback_error", fetch_records[0].error)
            self.assertEqual(len(enrichments), 1)
            self.assertFalse(
                any("ncbi_fallback_error" in note for note in enrichments[0].notes)
            )

    def test_cli_auto_review_evidence_enrichment_from_cached_xml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            raw_dir = os.path.join(tmpdir, "raw")
            enrichments_path = os.path.join(tmpdir, "enrichments.jsonl")
            fetch_records_path = os.path.join(tmpdir, "fetch_records.jsonl")
            summary_path = os.path.join(tmpdir, "summary.json")
            bundles_path = os.path.join(tmpdir, "bundles.jsonl")
            bundles_summary_path = os.path.join(tmpdir, "bundles_summary.json")

            paper = make_source_paper(
                paper_id="PMID:auto-cli-enrich",
                study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                claim_mode=ClaimMode.EXPLORATORY,
                metadata={
                    "abstract": "Mechanistic abstract.",
                    "pmcid": "PMC999001",
                    "pmid": "999001",
                    "doi": "10.1000/auto-cli-enrich",
                },
            )
            write_jsonl(papers_path, [paper])
            Path(raw_dir).mkdir(parents=True, exist_ok=True)
            Path(raw_dir, "PMC999001.xml").write_text(
                """<article><body>
                <sec><title>Methods</title><p>CRISPR perturbation with RRID:AB_999999.</p></sec>
                <sec><title>Results</title><p>Figure 2 shows pathway inhibition.</p></sec>
                <fig><caption><p>Figure 2. Pathway inhibition after perturbation.</p></caption></fig>
                </body></article>""",
                encoding="utf-8",
            )

            self.assertEqual(
                cli_main(
                    [
                        "build-auto-review-evidence-enrichments",
                        "--papers",
                        papers_path,
                        "--raw-dir",
                        raw_dir,
                        "--output",
                        enrichments_path,
                        "--fetch-records-output",
                        fetch_records_path,
                        "--summary-output",
                        summary_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-auto-review-source-bundles",
                        "--papers",
                        papers_path,
                        "--evidence-enrichments",
                        enrichments_path,
                        "--output",
                        bundles_path,
                        "--summary-output",
                        bundles_summary_path,
                    ]
                ),
                0,
            )
            enrichments = load_jsonl(
                enrichments_path,
                loader=auto_review_evidence_enrichment_record_from_dict,
            )
            bundles = load_jsonl(bundles_path, loader=auto_review_source_bundle_from_dict)
            self.assertEqual(len(enrichments), 1)
            self.assertEqual(len(bundles), 1)
            self.assertEqual(bundles[0].bundle_completeness, AutoReviewBundleCompleteness.REVIEW_READY)

    def test_materialize_enriched_source_papers(self):
        paper = make_source_paper(
            paper_id="PMID:auto-materialize",
            metadata={
                "abstract": "Short abstract.",
                "pmcid": "PMC12345",
            },
        )
        enrichment = AutoReviewEvidenceEnrichmentRecord(
            paper_id="PMID:auto-materialize",
            pmcid="PMC12345",
            raw_payload_path="/tmp/PMC12345.xml",
            methods_text="Methods section text.",
            results_text="Results section text.",
            figure_captions=("Figure 1 caption.",),
            table_snippets=("Table 1 snippet.",),
            figure_reference_snippets=("Figure 1 is referenced in the results.",),
            table_reference_snippets=("Table 1 summarizes the measured outcomes.",),
            resource_identifiers=("RRID:AB_123456",),
            trial_registry_ids=("NCT00000001",),
            trial_registry_reference_snippets=("Registered under NCT00000001 with primary endpoint change at week 12.",),
            provenance_fields={"methods_text": "pmc_fulltext_xml:sec[methods]"},
            notes=("cached enrichment",),
        )
        enriched = materialize_enriched_source_papers((paper,), (enrichment,))
        self.assertEqual(len(enriched), 1)
        metadata = enriched[0].metadata
        self.assertEqual(metadata["methods_text"], "Methods section text.")
        self.assertEqual(metadata["results_text"], "Results section text.")
        self.assertEqual(metadata["figure_captions"], ["Figure 1 caption."])
        self.assertEqual(metadata["table_snippets"], ["Table 1 snippet."])
        self.assertEqual(metadata["figure_reference_snippets"], ["Figure 1 is referenced in the results."])
        self.assertEqual(metadata["table_reference_snippets"], ["Table 1 summarizes the measured outcomes."])
        self.assertEqual(metadata["resource_identifiers"], ["RRID:AB_123456"])
        self.assertEqual(metadata["trial_registry_ids"], ["NCT00000001"])
        self.assertEqual(
            metadata["trial_registry_reference_snippets"],
            ["Registered under NCT00000001 with primary endpoint change at week 12."],
        )

    def test_auto_review_pipeline_caps_public_release(self):
        review_ready_paper = make_source_paper(
            paper_id="PMID:auto-ready",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            metadata={
                "abstract": "Randomized trial with improved primary outcome and confidence interval.",
                "methods_text": "We randomized patients into two arms and registered the trial as NCT01234567.",
                "results_text": "The intervention improved the primary endpoint. Figure 2 summarizes the outcome.",
                "figure_captions": [{"pointer": "Fig2", "text": "Primary endpoint improved in the intervention arm."}],
                "resource_identifiers": ["NCT01234567"],
                "doi": "10.1000/auto-ready",
                "pmid": "101",
                "pmcid": "PMC101",
                "oa_fulltext_available": True,
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "benchmark_ready_signal_count": 4,
            },
        )
        metadata_only_paper = make_source_paper(
            paper_id="PMID:auto-stress",
            publication_status=PublicationStatus.PREPRINT,
            peer_reviewed=False,
            metadata={
                "abstract": "Preprint abstract only.",
                "doi": "10.1000/auto-stress",
                "pmid": "102",
            },
        )
        papers = (review_ready_paper, metadata_only_paper)
        bundles = build_auto_review_source_bundles(papers)
        packaging_reviews = build_packaging_review_priors(papers)
        profile = build_cayuga_execution_profile(
            cayuga_root="/tmp/cayuga",
            repo_root=ROOT,
        )
        votes = run_auto_paper_reviews(
            papers,
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        self.assertEqual(len(votes), 6)
        aggregated = aggregate_auto_paper_reviews(papers, bundles, votes)
        records = build_auto_paper_qualification_records(
            papers,
            bundles,
            aggregated,
            packaging_reviews,
        )
        record_by_id = {record.paper_id: record for record in records}
        self.assertEqual(
            record_by_id["PMID:auto-ready"].decision.candidate_tier,
            CandidateTier.SHADOW_CANDIDATE,
        )
        self.assertTrue(record_by_id["PMID:auto-ready"].decision.eligible_for_unit_extraction)
        self.assertFalse(record_by_id["PMID:auto-ready"].decision.public_writing_eligible)
        self.assertEqual(record_by_id["PMID:auto-ready"].review_origin, "auto_panel")
        self.assertFalse(record_by_id["PMID:auto-ready"].judge_validation_ready)
        self.assertEqual(
            record_by_id["PMID:auto-stress"].decision.candidate_tier,
            CandidateTier.EXCLUDED,
        )
        report = summarize_auto_review_batch(
            papers,
            bundles=bundles,
            panel_votes=votes,
            aggregated_reviews=aggregated,
            qualification_records=records,
        )
        self.assertEqual(report.qualification_count, 2)
        self.assertEqual(report.candidate_tier_counts["shadow_candidate"], 1)
        self.assertEqual(report.candidate_tier_counts["excluded"], 1)

    def test_auto_review_observational_review_ready_without_registry_can_still_reach_shadow(self):
        paper = make_source_paper(
            paper_id="PMID:auto-observational",
            study_class=StudyClass.HUMAN_OBSERVATIONAL,
            claim_mode=ClaimMode.DESCRIPTIVE,
            metadata={
                "abstract": "Prospective cohort study reporting biomarker associations and outcome differences.",
                "methods_text": "We enrolled a longitudinal cohort and measured the biomarker at baseline and follow-up.",
                "results_text": "Table 1 summarizes the association estimates and Figure 2 shows outcome stratification.",
                "figure_captions": [{"pointer": "Fig2", "text": "Outcome stratification by biomarker level."}],
                "table_snippets": [{"pointer": "Table1", "text": "Association estimates by subgroup."}],
                "doi": "10.1000/auto-observational",
                "pmid": "201",
            },
        )
        papers = (paper,)
        bundles = build_auto_review_source_bundles(papers)
        packaging_reviews = build_packaging_review_priors(papers)
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            papers,
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews(papers, bundles, votes)
        records = build_auto_paper_qualification_records(papers, bundles, aggregated, packaging_reviews)
        self.assertEqual(
            aggregated[0].scientific_review.critical_domains[
                ScientificCriticalDomain.REQUIRED_TRACEABILITY
            ],
            DomainOutcome.PASS,
        )
        self.assertIn(
            records[0].decision.scientific,
            {PaperScientificQualification.A, PaperScientificQualification.B},
        )

    def test_auto_review_limitation_only_insufficiency_does_not_force_low_confidence(self):
        paper = make_source_paper(
            paper_id="PMID:auto-confidence-calibrated",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            metadata={
                "abstract": "Randomized placebo-controlled trial with primary endpoint improvement.",
                "methods_text": "We randomized participants, registered the study as NCT01234567, and assessed the primary endpoint at week 12.",
                "results_text": "The intervention arm improved the primary endpoint and Table 1 and Figure 2 summarize the outcomes.",
                "figure_captions": [{"pointer": "Fig2", "text": "Primary endpoint improved in the intervention arm."}],
                "table_snippets": [{"pointer": "Table1", "text": "Primary endpoint estimates by study arm."}],
                "figure_reference_snippets": ["Figure 2 shows the intervention arm improvement over placebo."],
                "table_reference_snippets": ["Table 1 reports the primary endpoint estimates by study arm."],
                "trial_registry_ids": ["NCT01234567"],
                "trial_registry_reference_snippets": ["Registered under NCT01234567 with a primary endpoint at week 12."],
                "doi": "10.1000/auto-confidence-calibrated",
                "pmid": "203",
            },
        )
        bundles = build_auto_review_source_bundles((paper,))
        packaging_reviews = build_packaging_review_priors((paper,))
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            (paper,),
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews((paper,), bundles, votes)
        self.assertEqual(aggregated[0].confidence, AutoReviewConfidence.MEDIUM)
        self.assertTrue(
            any(
                note == "insufficient_flags=limitation_uncertainty_disclosure"
                for note in aggregated[0].notes
            )
        )
        self.assertFalse(
            any(note.startswith("confidence_disqualifying_flags=") for note in aggregated[0].notes)
        )

    def test_auto_review_biomarker_observational_structured_evidence_passes_remark(self):
        paper = make_source_paper(
            paper_id="PMID:auto-biomarker-remark",
            study_class=StudyClass.HUMAN_OBSERVATIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            modality_overlays=(ModalityOverlay.BIOMARKER_PROGNOSTIC,),
            metadata={
                "abstract": "Retrospective cohort study of serum marker levels and mortality risk.",
                "methods_text": "We analyzed a retrospective cohort and fit Cox regression models for 30-day mortality.",
                "results_text": "Higher marker values were associated with mortality, with hazard ratios reported in Table 1 and Figure 2.",
                "figure_captions": [{"pointer": "Fig2", "text": "Hazard ratio curves by biomarker strata."}],
                "table_snippets": [{"pointer": "Table1", "text": "Adjusted hazard ratios for mortality by biomarker quintile."}],
                "doi": "10.1000/auto-biomarker-remark",
                "pmid": "301",
            },
        )
        papers = (paper,)
        bundles = build_auto_review_source_bundles(papers)
        packaging_reviews = build_packaging_review_priors(papers)
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            papers,
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews(papers, bundles, votes)
        records = build_auto_paper_qualification_records(papers, bundles, aggregated, packaging_reviews)
        self.assertEqual(
            aggregated[0].scientific_review.standard_outcomes[StandardId.REMARK],
            DomainOutcome.PASS,
        )
        self.assertEqual(
            aggregated[0].scientific_review.critical_domains[
                ScientificCriticalDomain.REQUIRED_TRACEABILITY
            ],
            DomainOutcome.PASS,
        )
        self.assertEqual(records[0].decision.scientific, PaperScientificQualification.A)
        self.assertEqual(records[0].decision.packaging, PaperPackagingQualification.P2)
        self.assertEqual(records[0].decision.candidate_tier, CandidateTier.STRESS_CANDIDATE)

    def test_auto_review_methods_resource_proteomics_structured_evidence_passes_miape(self):
        paper = make_source_paper(
            paper_id="PMID:auto-proteomics-miape",
            study_class=StudyClass.METHODS_RESOURCE,
            claim_mode=ClaimMode.RESOURCE_RELEASE,
            modality_overlays=(ModalityOverlay.PROTEOMICS_MASSSPEC,),
            metadata={
                "abstract": "Open atlas and retrieval toolkit for human protein complexes from mass spectrometry data.",
                "methods_text": "We benchmarked a mass spectrometry-derived atlas and retrieval pipeline across multiple datasets.",
                "results_text": "Results show protein complex retrieval accuracy, atlas coverage, and benchmark comparisons in Figure 1 and Table 1.",
                "figure_captions": [{"pointer": "Fig1", "text": "Proteomics atlas benchmark across datasets."}],
                "table_snippets": [{"pointer": "Table1", "text": "Retrieval performance and protein complex coverage."}],
                "doi": "10.1000/auto-proteomics-miape",
                "pmid": "302",
            },
        )
        papers = (paper,)
        bundles = build_auto_review_source_bundles(papers)
        packaging_reviews = build_packaging_review_priors(papers)
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            papers,
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews(papers, bundles, votes)
        records = build_auto_paper_qualification_records(papers, bundles, aggregated, packaging_reviews)
        self.assertEqual(
            aggregated[0].scientific_review.standard_outcomes[StandardId.MIAPE_PROTEOMEXCHANGE],
            DomainOutcome.PASS,
        )
        self.assertEqual(
            aggregated[0].scientific_review.critical_domains[
                ScientificCriticalDomain.REQUIRED_TRACEABILITY
            ],
            DomainOutcome.PASS,
        )
        self.assertEqual(records[0].decision.scientific, PaperScientificQualification.A)
        self.assertEqual(records[0].decision.packaging, PaperPackagingQualification.P2)
        self.assertEqual(records[0].decision.candidate_tier, CandidateTier.STRESS_CANDIDATE)

    def test_auto_review_methods_resource_protocol_abstract_can_reach_shadow(self):
        paper = make_source_paper(
            paper_id="PMID:auto-resource-abstract",
            title="Optimized Workflow for Proteomics and Phosphoproteomics With Limited Tissue Samples",
            study_class=StudyClass.METHODS_RESOURCE,
            claim_mode=ClaimMode.RESOURCE_RELEASE,
            modality_overlays=(ModalityOverlay.PROTEOMICS_MASSSPEC,),
            metadata={
                "abstract": (
                    "We developed a comprehensive workflow for small-scale proteomics and phosphoproteomics samples. "
                    "Our proposed workflow consists of seven steps for sample preparation and LC-MS/MS analysis. "
                    "This innovative workflow establishes a new benchmark for precision and efficiency in proteomic investigations."
                ),
                "doi": "10.1000/auto-resource-abstract",
                "pmid": "401",
                "pmcid": "PMC401",
                "oa_fulltext_available": True,
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "benchmark_ready_signal_count": 4,
            },
        )
        papers = (paper,)
        bundles = build_auto_review_source_bundles(papers)
        self.assertEqual(bundles[0].bundle_completeness, AutoReviewBundleCompleteness.REVIEW_READY)
        packaging_reviews = build_packaging_review_priors(papers)
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            papers,
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews(papers, bundles, votes)
        records = build_auto_paper_qualification_records(papers, bundles, aggregated, packaging_reviews)
        self.assertEqual(records[0].decision.scientific, PaperScientificQualification.A)
        self.assertEqual(records[0].decision.candidate_tier, CandidateTier.SHADOW_CANDIDATE)

    def test_auto_review_observational_quantitative_abstract_only_can_reach_shadow(self):
        paper = make_source_paper(
            paper_id="PMID:auto-observational-abstract-only",
            study_class=StudyClass.HUMAN_OBSERVATIONAL,
            claim_mode=ClaimMode.DESCRIPTIVE,
            metadata={
                "abstract": (
                    "A retrospective observational study was conducted in 614 hospitalized adults receiving parenteral nutrition. "
                    "Morphofunctional assessments included bioelectrical impedance and handgrip dynamometry. "
                    "Survival analysis used Cox proportional hazards models and receiver operating characteristic curve analysis. "
                    "Higher phase angle and handgrip strength were associated with lower 12-month mortality, with odds ratio 0.6 and 95% CI 0.5-0.7."
                ),
                "doi": "10.1000/auto-observational-abstract-only",
                "pmid": "402",
                "pmcid": "PMC402",
            },
        )
        bundles = build_auto_review_source_bundles((paper,))
        self.assertEqual(bundles[0].bundle_completeness, AutoReviewBundleCompleteness.REVIEW_READY)
        self.assertTrue(bundles[0].methods_text)
        self.assertTrue(bundles[0].results_text)
        packaging_reviews = build_packaging_review_priors((paper,))
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            (paper,),
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews((paper,), bundles, votes)
        records = build_auto_paper_qualification_records((paper,), bundles, aggregated, packaging_reviews)
        self.assertEqual(records[0].decision.scientific, PaperScientificQualification.A)
        self.assertEqual(records[0].decision.candidate_tier, CandidateTier.STRESS_CANDIDATE)

    def test_auto_review_figure_caption_empirical_paper_can_reach_shadow(self):
        paper = make_source_paper(
            paper_id="PMID:auto-figure-caption-rescue",
            title="Validation of CRISPR targeting control genes in AML cells",
            study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
            claim_mode=ClaimMode.EXPLORATORY,
            metadata={
                "abstract": (
                    "MOLM-13 acute myeloid leukemia cells were used in CRISPR experiments to identify disease drivers. "
                    "We validated sgRNAs for TP53 knockdown and DCK knockdown with downstream leukemic phenotype analyses. "
                    "We also provided a detailed CRISPR protocol applicable to gene knockdown and activation experiments."
                ),
                "figure_captions": [
                    {
                        "pointer": "Fig1",
                        "text": (
                            "Perturbation of control genes expression induces enhanced leukemia phenotypes. "
                            "Western blot validated p53 and DCK knockdown, and representative results show increased EdU incorporation and cytarabine resistance."
                        ),
                    }
                ],
                "doi": "10.1000/auto-figure-caption-rescue",
                "pmid": "403",
                "pmcid": "PMC403",
            },
        )
        bundles = build_auto_review_source_bundles((paper,))
        self.assertEqual(bundles[0].bundle_completeness, AutoReviewBundleCompleteness.REVIEW_READY)
        self.assertTrue(bundles[0].methods_text)
        self.assertTrue(bundles[0].results_text)
        self.assertTrue(
            "results inferred from figure captions for auto-review bundling" in bundles[0].notes
            or "results inferred from abstract for auto-review bundling" in bundles[0].notes
        )
        packaging_reviews = build_packaging_review_priors((paper,))
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            (paper,),
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews((paper,), bundles, votes)
        records = build_auto_paper_qualification_records((paper,), bundles, aggregated, packaging_reviews)
        self.assertEqual(records[0].decision.scientific, PaperScientificQualification.A)
        self.assertEqual(records[0].decision.candidate_tier, CandidateTier.STRESS_CANDIDATE)

    def test_auto_review_interventional_without_registry_or_structured_results_stays_stress(self):
        paper = make_source_paper(
            paper_id="PMID:auto-interventional-weak",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            metadata={
                "abstract": "Clinical trial abstract with limited details.",
                "methods_text": "Patients received the intervention or standard of care.",
                "results_text": "The intervention improved outcomes.",
                "doi": "10.1000/auto-interventional-weak",
                "pmid": "202",
            },
        )
        papers = (paper,)
        bundles = build_auto_review_source_bundles(papers)
        packaging_reviews = build_packaging_review_priors(papers)
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            papers,
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews(papers, bundles, votes)
        records = build_auto_paper_qualification_records(papers, bundles, aggregated, packaging_reviews)
        self.assertEqual(
            aggregated[0].scientific_review.critical_domains[
                ScientificCriticalDomain.REQUIRED_TRACEABILITY
            ],
            DomainOutcome.BORDERLINE,
        )
        self.assertEqual(records[0].decision.scientific, PaperScientificQualification.C)
        self.assertEqual(records[0].decision.candidate_tier, CandidateTier.EXCLUDED)

    def test_metadata_hints_do_not_infer_enzymology_from_travel_km(self):
        paper = make_source_paper(
            paper_id="PMID:auto-no-enzyme-overlay",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            metadata={
                "abstract": (
                    "Randomized trial with pain and function outcomes. "
                    "The intervention saved 266.4 km of travel and 1325.6 minutes."
                ),
            },
        )
        hint = suggest_governance_metadata_hints(paper)
        self.assertNotIn(ModalityOverlay.ENZYMOLOGY, hint.suggested_modality_overlays)

    def test_auto_review_ignores_unsupported_enzymology_overlay(self):
        paper = make_source_paper(
            paper_id="PMID:auto-false-enzyme-overlay",
            study_class=StudyClass.HUMAN_INTERVENTIONAL,
            claim_mode=ClaimMode.CONFIRMATORY,
            modality_overlays=(ModalityOverlay.ENZYMOLOGY,),
            metadata={
                "abstract": "Randomized trial with remote follow-up and reduced travel distance.",
                "methods_text": (
                    "This randomized controlled trial enrolled 90 participants and used "
                    "remote follow-up, predefined outcomes, and intention-to-treat analysis."
                ),
                "results_text": (
                    "Results showed non-inferior pain outcomes, improved adherence, and "
                    "266.4 km of travel saved per unit of improvement."
                ),
                "figure_captions": [{"pointer": "Fig1", "text": "CONSORT diagram and outcome curves."}],
                "table_snippets": [{"pointer": "Table1", "text": "Pain and adherence outcomes by study arm."}],
                "trial_registry_ids": ["NCT06194435"],
                "doi": "10.1000/auto-false-enzyme-overlay",
                "pmid": "99901",
            },
        )
        papers = (paper,)
        bundles = build_auto_review_source_bundles(papers)
        packaging_reviews = build_packaging_review_priors(papers)
        profile = build_cayuga_execution_profile(cayuga_root="/tmp/cayuga", repo_root=ROOT)
        votes = run_auto_paper_reviews(
            papers,
            bundles,
            execution_profile=profile,
            model_id="mock-panel",
            packaging_reviews=packaging_reviews,
        )
        aggregated = aggregate_auto_paper_reviews(papers, bundles, votes)
        records = build_auto_paper_qualification_records(papers, bundles, aggregated, packaging_reviews)
        self.assertNotIn(StandardId.STRENDA, aggregated[0].scientific_review.applied_standards)
        self.assertEqual(records[0].decision.scientific, PaperScientificQualification.A)
        self.assertEqual(records[0].decision.candidate_tier, CandidateTier.STRESS_CANDIDATE)

    def test_cli_auto_review_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_path = os.path.join(tmpdir, "papers.jsonl")
            bundles_path = os.path.join(tmpdir, "bundles.jsonl")
            bundles_summary_path = os.path.join(tmpdir, "bundles_summary.json")
            profile_path = os.path.join(tmpdir, "profile.json")
            votes_path = os.path.join(tmpdir, "votes.jsonl")
            votes_summary_path = os.path.join(tmpdir, "votes_summary.json")
            aggregated_path = os.path.join(tmpdir, "aggregated.jsonl")
            aggregated_summary_path = os.path.join(tmpdir, "aggregated_summary.json")
            packaging_path = os.path.join(tmpdir, "packaging.jsonl")
            decisions_path = os.path.join(tmpdir, "auto_decisions.jsonl")
            decisions_summary_path = os.path.join(tmpdir, "auto_decisions_summary.json")
            final_summary_path = os.path.join(tmpdir, "auto_review_batch_summary.json")

            papers = [
                make_source_paper(
                    paper_id="PMID:auto-cli-1",
                    study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
                    claim_mode=ClaimMode.EXPLORATORY,
                    metadata={
                        "abstract": "Mechanistic study abstract.",
                        "methods_text": "We used CRISPR perturbation and measured signaling changes.",
                        "results_text": "Results showed pathway inhibition. Figure 1 shows the signal.",
                        "figure_captions": [{"pointer": "Fig1", "text": "Signal decreased after perturbation."}],
                        "resource_identifiers": ["RRID:AB_123456"],
                        "doi": "10.1000/auto-cli-1",
                        "pmid": "201",
                        "pmcid": "PMC201",
                        "oa_fulltext_available": True,
                        "license": "https://creativecommons.org/licenses/by/4.0/",
                        "benchmark_ready_signal_count": 4,
                    },
                ),
                make_source_paper(
                    paper_id="PMID:auto-cli-2",
                    metadata={
                        "abstract": "Abstract only paper.",
                        "doi": "10.1000/auto-cli-2",
                        "pmid": "202",
                    },
                ),
            ]
            write_jsonl(papers_path, papers)
            write_jsonl(packaging_path, build_packaging_review_priors(papers))
            _write_profile = {
                "profile_id": "EXEC:TEST",
                "profile_name": "cayuga",
                "backend": "slurm",
                "root_path": "/tmp/cayuga",
                "repo_root": ROOT,
                "working_directory": "/tmp/cayuga/lspwb",
                "python_bin": "python3",
                "launch_prefix": ["sbatch"],
                "environment_exports": {},
                "notes": [],
            }
            Path(profile_path).write_text(json.dumps(_write_profile), encoding="utf-8")

            self.assertEqual(
                cli_main(
                    [
                        "build-auto-review-source-bundles",
                        "--papers",
                        papers_path,
                        "--output",
                        bundles_path,
                        "--summary-output",
                        bundles_summary_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "run-auto-paper-reviews",
                        "--papers",
                        papers_path,
                        "--source-bundles",
                        bundles_path,
                        "--execution-profile",
                        profile_path,
                        "--model-id",
                        "mock-panel",
                        "--packaging-reviews",
                        packaging_path,
                        "--output",
                        votes_path,
                        "--summary-output",
                        votes_summary_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "aggregate-auto-paper-reviews",
                        "--papers",
                        papers_path,
                        "--source-bundles",
                        bundles_path,
                        "--panel-votes",
                        votes_path,
                        "--output",
                        aggregated_path,
                        "--summary-output",
                        aggregated_summary_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "build-auto-paper-qualification-decisions",
                        "--papers",
                        papers_path,
                        "--source-bundles",
                        bundles_path,
                        "--aggregated-reviews",
                        aggregated_path,
                        "--packaging-reviews",
                        packaging_path,
                        "--output",
                        decisions_path,
                        "--summary-output",
                        decisions_summary_path,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "summarize-auto-review-batch",
                        "--papers",
                        papers_path,
                        "--source-bundles",
                        bundles_path,
                        "--panel-votes",
                        votes_path,
                        "--aggregated-reviews",
                        aggregated_path,
                        "--qualifications",
                        decisions_path,
                        "--output",
                        final_summary_path,
                    ]
                ),
                0,
            )

            bundles = load_jsonl(bundles_path, loader=auto_review_source_bundle_from_dict)
            votes = load_jsonl(votes_path, loader=auto_panel_vote_from_dict)
            aggregated = load_jsonl(aggregated_path, loader=auto_aggregated_paper_review_record_from_dict)
            decisions = load_jsonl(decisions_path, loader=auto_qualification_record_from_dict)
            final_summary = auto_review_batch_report_from_dict(
                json.loads(Path(final_summary_path).read_text(encoding="utf-8"))
            )

            self.assertEqual(len(bundles), 2)
            self.assertEqual(len(votes), 6)
            self.assertEqual(len(aggregated), 2)
            self.assertEqual(len(decisions), 2)
            self.assertIn(final_summary.candidate_tier_counts["shadow_candidate"], {0, 1, 2})
            self.assertTrue(all(not record.decision.public_writing_eligible for record in decisions))
            self.assertTrue(all(not record.judge_validation_ready for record in decisions))


if __name__ == "__main__":
    unittest.main()
