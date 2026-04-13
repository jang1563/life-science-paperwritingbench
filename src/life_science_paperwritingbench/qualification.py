from __future__ import annotations

from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

from .models import (
    EvidenceUnit,
    PackagingReview,
    PaperQualificationDecision,
    ScientificReview,
    SourcePaper,
    TruthManifest,
    UnitQualificationDecision,
    WritingReview,
)
from .policy import (
    CRITICAL_SCIENTIFIC_DOMAINS,
    CRITICAL_WRITING_DOMAINS,
    OVERLAY_REQUIRED_STANDARDS,
    PACKAGING_DOMAINS,
    PRIMARY_CLASS_REQUIRED_STANDARDS,
    PUBLIC_GOLD_START_YEAR,
    SUPPORTING_SCIENTIFIC_DOMAINS,
    SUPPORTING_WRITING_DOMAINS,
    CandidateTier,
    CrossmarkUpdateType,
    DomainOutcome,
    IntegrityDisposition,
    IntegrityFlag,
    PackagingDomain,
    PackagingPolicy,
    PaperPackagingQualification,
    PaperScientificQualification,
    PaperWritingQualification,
    PublicationStatus,
    ReleaseTier,
    SafeDerivedArtifact,
    ScientificCriticalDomain,
    StandardId,
)


def _count_outcomes(values: Iterable[DomainOutcome], target: DomainOutcome) -> int:
    return sum(1 for value in values if value == target)


def _collect_missing_domains(review_mapping: Mapping, expected_domains: Sequence) -> List[str]:
    missing = []
    for domain in expected_domains:
        if domain not in review_mapping:
            missing.append(str(domain))
    return missing


def required_standards_for_configuration(
    study_class,
    modality_overlays: Sequence,
) -> Tuple[StandardId, ...]:
    ordered: List[StandardId] = list(PRIMARY_CLASS_REQUIRED_STANDARDS[study_class])
    for overlay in modality_overlays:
        ordered.extend(OVERLAY_REQUIRED_STANDARDS.get(overlay, ()))
    deduped: List[StandardId] = []
    seen = set()
    for item in ordered:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return tuple(deduped)


def required_standards_for_paper(paper: SourcePaper) -> Tuple[StandardId, ...]:
    return required_standards_for_configuration(
        paper.study_class,
        paper.modality_overlays,
    )


def determine_integrity_disposition(
    paper: SourcePaper,
) -> Tuple[IntegrityDisposition, Optional[PaperScientificQualification], List[str]]:
    reasons: List[str] = []
    terminal_updates = {
        CrossmarkUpdateType.RETRACTION,
        CrossmarkUpdateType.WITHDRAWAL,
        CrossmarkUpdateType.REMOVAL,
    }
    quarantine_flags = {
        IntegrityFlag.PAPER_MILL_PATTERN,
        IntegrityFlag.MANIPULATION_ALLEGATION,
        IntegrityFlag.IMAGE_REUSE_PATTERN,
        IntegrityFlag.MAJOR_CORRECTION_INTERPRETATION,
    }

    if paper.publication_status in {
        PublicationStatus.RETRACTED,
        PublicationStatus.WITHDRAWN,
        PublicationStatus.REMOVED,
    }:
        reasons.append(f"paper publication status is {paper.publication_status.value}")
        return IntegrityDisposition.EXCLUDED, PaperScientificQualification.C, reasons

    if any(update in terminal_updates for update in paper.crossmark_updates):
        reasons.append("paper has a terminal Crossmark/Crossref update")
        return IntegrityDisposition.EXCLUDED, PaperScientificQualification.C, reasons

    if CrossmarkUpdateType.PARTIAL_RETRACTION in paper.crossmark_updates:
        if paper.partial_retraction_invalidates_core_claims:
            reasons.append("partial retraction invalidates core claims")
            return IntegrityDisposition.EXCLUDED, PaperScientificQualification.C, reasons
        reasons.append("paper has a partial retraction that requires quarantine review")
        return IntegrityDisposition.QUARANTINE, PaperScientificQualification.Q, reasons

    if CrossmarkUpdateType.EXPRESSION_OF_CONCERN in paper.crossmark_updates:
        reasons.append("paper has an expression of concern")
        return IntegrityDisposition.QUARANTINE, PaperScientificQualification.Q, reasons

    if paper.major_correction_affects_interpretation:
        reasons.append("paper has a major correction that may alter interpretation")
        return IntegrityDisposition.QUARANTINE, PaperScientificQualification.Q, reasons

    if any(flag in quarantine_flags for flag in paper.integrity_flags):
        reasons.append("paper has unresolved integrity red flags")
        return IntegrityDisposition.QUARANTINE, PaperScientificQualification.Q, reasons

    return IntegrityDisposition.CLEAR, None, reasons


def _standards_review_status(
    paper: SourcePaper,
    review: ScientificReview,
) -> Tuple[Tuple[StandardId, ...], Tuple[StandardId, ...], Tuple[StandardId, ...], List[str]]:
    required_standards = required_standards_for_paper(paper)
    applied = set(review.applied_standards)
    missing = tuple(
        standard for standard in required_standards if standard not in review.standard_outcomes or standard not in applied
    )
    failed = tuple(
        standard
        for standard in required_standards
        if review.standard_outcomes.get(standard) == DomainOutcome.FAIL
    )
    borderline = tuple(
        standard
        for standard in required_standards
        if review.standard_outcomes.get(standard) == DomainOutcome.BORDERLINE
    )
    reasons: List[str] = []
    if missing:
        reasons.append("required standards are missing review coverage: " + ", ".join(item.value for item in missing))
    if failed:
        reasons.append("required standards failed review: " + ", ".join(item.value for item in failed))
    if borderline:
        reasons.append(
            "required standards are borderline and block top-tier qualification: "
            + ", ".join(item.value for item in borderline)
        )
    return required_standards, missing, failed + borderline, reasons


def qualify_scientific(
    paper: SourcePaper,
    review: ScientificReview,
) -> Tuple[PaperScientificQualification, IntegrityDisposition, Tuple[StandardId, ...], Tuple[StandardId, ...], List[str]]:
    reasons: List[str] = []
    integrity_disposition, override, override_reasons = determine_integrity_disposition(paper)
    reasons.extend(override_reasons)

    required_standards, missing_standards, blocked_standards, standards_reasons = _standards_review_status(
        paper,
        review,
    )
    reasons.extend(standards_reasons)

    if override is not None:
        return override, integrity_disposition, required_standards, missing_standards, reasons

    missing_critical = _collect_missing_domains(review.critical_domains, CRITICAL_SCIENTIFIC_DOMAINS)
    if missing_critical:
        reasons.append(
            "scientific review is missing critical domain ratings: " + ", ".join(sorted(missing_critical))
        )
        return PaperScientificQualification.C, integrity_disposition, required_standards, missing_standards, reasons

    missing_supporting = _collect_missing_domains(review.supporting_domains, SUPPORTING_SCIENTIFIC_DOMAINS)
    if missing_supporting:
        reasons.append(
            "scientific review is missing supporting domain ratings: " + ", ".join(sorted(missing_supporting))
        )
        return PaperScientificQualification.C, integrity_disposition, required_standards, missing_standards, reasons

    critical_values = [review.critical_domains[domain] for domain in CRITICAL_SCIENTIFIC_DOMAINS]
    supporting_values = [review.supporting_domains[domain] for domain in SUPPORTING_SCIENTIFIC_DOMAINS]

    if _count_outcomes(critical_values, DomainOutcome.FAIL):
        reasons.append("one or more critical scientific domains failed")
        return PaperScientificQualification.C, integrity_disposition, required_standards, missing_standards, reasons

    critical_borderlines = _count_outcomes(critical_values, DomainOutcome.BORDERLINE)
    supporting_borderlines = _count_outcomes(supporting_values, DomainOutcome.BORDERLINE)
    supporting_fails = _count_outcomes(supporting_values, DomainOutcome.FAIL)

    if critical_borderlines > 1:
        reasons.append("more than one critical scientific domain is borderline")
        return PaperScientificQualification.C, integrity_disposition, required_standards, missing_standards, reasons

    scientific = PaperScientificQualification.B
    if critical_borderlines == 0 and supporting_fails == 0 and supporting_borderlines <= 2:
        scientific = PaperScientificQualification.A

    if blocked_standards:
        scientific = PaperScientificQualification.B if scientific == PaperScientificQualification.A else scientific
    if any(review.standard_outcomes.get(standard) == DomainOutcome.FAIL for standard in required_standards):
        scientific = PaperScientificQualification.C

    if scientific == PaperScientificQualification.A and missing_standards:
        scientific = PaperScientificQualification.B

    if scientific == PaperScientificQualification.B and not reasons:
        reasons.append("paper meets shadow/stress scientific criteria")
    elif scientific == PaperScientificQualification.B and "paper meets shadow/stress scientific criteria" not in reasons:
        reasons.append("paper does not satisfy full A-level scientific criteria")

    return scientific, integrity_disposition, required_standards, missing_standards, reasons


def qualify_writing(
    review: WritingReview,
) -> Tuple[PaperWritingQualification, List[str]]:
    reasons: List[str] = []
    missing_critical = _collect_missing_domains(review.critical_domains, CRITICAL_WRITING_DOMAINS)
    if missing_critical:
        reasons.append(
            "writing review is missing critical domain ratings: " + ", ".join(sorted(missing_critical))
        )
        return PaperWritingQualification.W3, reasons

    missing_supporting = _collect_missing_domains(review.supporting_domains, SUPPORTING_WRITING_DOMAINS)
    if missing_supporting:
        reasons.append(
            "writing review is missing supporting domain ratings: " + ", ".join(sorted(missing_supporting))
        )
        return PaperWritingQualification.W3, reasons

    critical_values = [review.critical_domains[domain] for domain in CRITICAL_WRITING_DOMAINS]
    supporting_values = [review.supporting_domains[domain] for domain in SUPPORTING_WRITING_DOMAINS]

    if _count_outcomes(critical_values, DomainOutcome.FAIL):
        reasons.append("one or more critical writing domains failed")
        return PaperWritingQualification.W3, reasons

    critical_borderlines = _count_outcomes(critical_values, DomainOutcome.BORDERLINE)
    supporting_borderlines = _count_outcomes(supporting_values, DomainOutcome.BORDERLINE)
    supporting_fails = _count_outcomes(supporting_values, DomainOutcome.FAIL)

    if critical_borderlines > 1:
        reasons.append("more than one critical writing domain is borderline")
        return PaperWritingQualification.W3, reasons

    if critical_borderlines == 0 and supporting_fails == 0 and supporting_borderlines == 0:
        return PaperWritingQualification.W1, reasons

    reasons.append("paper is usable but not strong enough as a writing exemplar")
    return PaperWritingQualification.W2, reasons


def qualify_packaging(
    paper: SourcePaper,
    review: PackagingReview,
    policy: Optional[PackagingPolicy] = None,
) -> Tuple[PaperPackagingQualification, List[str]]:
    policy = policy or PackagingPolicy()
    reasons: List[str] = []

    missing_domains = _collect_missing_domains(review.domain_outcomes, PACKAGING_DOMAINS)
    if missing_domains:
        reasons.append(
            "packaging review is missing domain ratings: " + ", ".join(sorted(missing_domains))
        )
        return PaperPackagingQualification.P3, reasons

    if review.contains_private_row_level_data:
        reasons.append("row-level human data cannot be redistributed")
        return PaperPackagingQualification.P2, reasons

    if review.redistributes_restricted_supplements:
        reasons.append("restricted supplements cannot be redistributed")
        return PaperPackagingQualification.P2, reasons

    if review.contains_recomputed_sensitive_aggregates:
        reasons.append("recomputed sensitive aggregates are not allowed in release artifacts")
        return PaperPackagingQualification.P2, reasons

    if review.restricted_artifact_types and review.domain_outcomes[PackagingDomain.RELEASEABILITY] == DomainOutcome.PASS:
        reasons.append("restricted artifact types block direct public release")
        return PaperPackagingQualification.P2, reasons

    if paper.controlled_access_human_data:
        if not review.controlled_access_rule_satisfied:
            reasons.append("controlled-access rule is not satisfied for this paper")
            return PaperPackagingQualification.P2, reasons
        allowed_safe_artifacts = [
            artifact for artifact in review.safe_derived_artifacts if artifact in policy.allowed_safe_artifacts
        ]
        if len(allowed_safe_artifacts) < policy.min_safe_artifacts_for_controlled_access:
            reasons.append("controlled-access paper is missing the minimum safe derived artifacts")
            return PaperPackagingQualification.P2, reasons
        if not review.artifact_inventory_id:
            reasons.append("controlled-access paper requires an artifact inventory for release review")
            return PaperPackagingQualification.P2, reasons

    if paper.small_cell_risk and SafeDerivedArtifact.PUBLISHED_AGGREGATE_STATISTICS not in review.safe_derived_artifacts:
        reasons.append("small-cell-risk paper requires published aggregate statistics for safe release")
        return PaperPackagingQualification.P2, reasons

    values = [review.domain_outcomes[domain] for domain in PACKAGING_DOMAINS]
    if review.domain_outcomes[PackagingDomain.RELEASEABILITY] == DomainOutcome.FAIL:
        reasons.append("benchmark artifacts are not releasable")
        return PaperPackagingQualification.P3, reasons
    if review.domain_outcomes[PackagingDomain.EVIDENCE_PACK_RECONSTRUCTABILITY] == DomainOutcome.FAIL:
        reasons.append("evidence pack is not reconstructable")
        return PaperPackagingQualification.P3, reasons
    if review.domain_outcomes[PackagingDomain.PROVENANCE_COMPLETENESS] == DomainOutcome.FAIL:
        reasons.append("provenance is incomplete")
        return PaperPackagingQualification.P3, reasons
    if review.domain_outcomes[PackagingDomain.SPLIT_SAFETY] == DomainOutcome.FAIL:
        reasons.append("split-safety requirements failed")
        return PaperPackagingQualification.P3, reasons
    if review.domain_outcomes[PackagingDomain.ARTIFACT_ACCESS] == DomainOutcome.FAIL:
        reasons.append("artifact access is insufficient for public packaging")
        return PaperPackagingQualification.P2, reasons

    if any(value == DomainOutcome.BORDERLINE for value in values):
        reasons.append("packaging is usable but not clean enough for top-tier public release")
        return PaperPackagingQualification.P2, reasons

    return PaperPackagingQualification.P1, reasons


def determine_candidate_tier(
    paper: SourcePaper,
    scientific: PaperScientificQualification,
    packaging: PaperPackagingQualification,
    integrity_disposition: IntegrityDisposition,
) -> Tuple[CandidateTier, bool, List[str]]:
    reasons: List[str] = []

    if integrity_disposition != IntegrityDisposition.CLEAR:
        reasons.append("paper is blocked by non-clear integrity disposition")
        return CandidateTier.EXCLUDED, False, reasons

    if scientific in {PaperScientificQualification.C, PaperScientificQualification.Q} or packaging == PaperPackagingQualification.P3:
        reasons.append("paper is excluded at the paper-governance stage")
        return CandidateTier.EXCLUDED, False, reasons

    is_public_window = (
        paper.publication_status == PublicationStatus.PUBLISHED
        and paper.peer_reviewed
        and (paper.publication_year >= PUBLIC_GOLD_START_YEAR or paper.explicit_pre2018_exception)
    )

    if scientific == PaperScientificQualification.A and packaging == PaperPackagingQualification.P1 and is_public_window:
        return CandidateTier.PUBLIC_GOLD_CANDIDATE, True, reasons

    if paper.publication_status == PublicationStatus.PREPRINT:
        reasons.append("preprints are shadow-only candidates")
        return CandidateTier.SHADOW_CANDIDATE, True, reasons

    if scientific == PaperScientificQualification.A and packaging in {
        PaperPackagingQualification.P1,
        PaperPackagingQualification.P2,
    }:
        reasons.append("paper is a shadow candidate because it misses at least one public-release prerequisite")
        return CandidateTier.SHADOW_CANDIDATE, True, reasons

    if scientific == PaperScientificQualification.B and packaging in {
        PaperPackagingQualification.P1,
        PaperPackagingQualification.P2,
    }:
        reasons.append("paper is stress-only because scientific qualification is B")
        return CandidateTier.STRESS_CANDIDATE, True, reasons

    reasons.append("paper does not qualify for unit extraction")
    return CandidateTier.EXCLUDED, False, reasons


def determine_public_writing_eligibility(
    writing: PaperWritingQualification,
    candidate_tier: CandidateTier,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    if candidate_tier != CandidateTier.PUBLIC_GOLD_CANDIDATE:
        reasons.append("paper is not a public-gold source candidate")
        return False, reasons
    if writing != PaperWritingQualification.W1:
        reasons.append("paper does not satisfy W1 writing-exemplar criteria")
        return False, reasons
    return True, reasons


def qualify_paper(
    paper: SourcePaper,
    scientific_review: ScientificReview,
    packaging_review: PackagingReview,
    writing_review: Optional[WritingReview] = None,
    policy: Optional[PackagingPolicy] = None,
) -> PaperQualificationDecision:
    scientific, integrity_disposition, required_standards, missing_standards, scientific_reasons = qualify_scientific(
        paper,
        scientific_review,
    )
    writing, writing_reasons = qualify_writing(writing_review or WritingReview(critical_domains={}, supporting_domains={}))
    packaging, packaging_reasons = qualify_packaging(paper, packaging_review, policy=policy)
    candidate_tier, eligible_for_unit_extraction, candidate_reasons = determine_candidate_tier(
        paper,
        scientific,
        packaging,
        integrity_disposition,
    )
    public_writing_eligible, writing_gate_reasons = determine_public_writing_eligibility(writing, candidate_tier)
    reasons = tuple(scientific_reasons + writing_reasons + packaging_reasons + candidate_reasons + writing_gate_reasons)
    return PaperQualificationDecision(
        scientific=scientific,
        packaging=packaging,
        candidate_tier=candidate_tier,
        eligible_for_unit_extraction=eligible_for_unit_extraction,
        required_standards=required_standards,
        writing=writing,
        public_writing_eligible=public_writing_eligible,
        missing_standards=missing_standards,
        integrity_disposition=integrity_disposition,
        reasons=reasons,
    )


def qualify_unit(
    paper_decision: PaperQualificationDecision,
    evidence_unit: EvidenceUnit,
    truth_manifest: TruthManifest,
) -> UnitQualificationDecision:
    reasons: List[str] = []
    release_tier = ReleaseTier.EXCLUDED

    if not paper_decision.eligible_for_unit_extraction:
        reasons.append("parent paper is not eligible for unit extraction")
    if evidence_unit.paper_id != truth_manifest.paper_id:
        reasons.append("evidence unit and truth manifest refer to different papers")
    if not evidence_unit.evidence_pointers:
        reasons.append("evidence unit has no local evidence pointers")
    if not evidence_unit.locally_supported:
        reasons.append("evidence unit lacks local evidence support")
    if not evidence_unit.internally_coherent:
        reasons.append("evidence unit is not internally coherent")
    if evidence_unit.depends_on_excluded_narrative:
        reasons.append("evidence unit depends on excluded unsupported narrative")
    if not evidence_unit.releasable:
        reasons.append("evidence unit is not releasable under packaging policy")
    if not truth_manifest.frozen:
        reasons.append("truth manifest must be frozen before release")

    if reasons:
        return UnitQualificationDecision(
            release_tier=release_tier,
            gold_eligible=False,
            reasons=tuple(reasons),
        )

    candidate_to_release = {
        CandidateTier.PUBLIC_GOLD_CANDIDATE: ReleaseTier.PUBLIC_GOLD,
        CandidateTier.SHADOW_CANDIDATE: ReleaseTier.SHADOW_GOLD,
        CandidateTier.STRESS_CANDIDATE: ReleaseTier.STRESS_ONLY,
        CandidateTier.EXCLUDED: ReleaseTier.EXCLUDED,
    }
    release_tier = candidate_to_release[paper_decision.candidate_tier]
    return UnitQualificationDecision(
        release_tier=release_tier,
        gold_eligible=release_tier == ReleaseTier.PUBLIC_GOLD,
        reasons=tuple(reasons),
    )
