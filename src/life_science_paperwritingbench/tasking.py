from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .models import (
    AnswerRecord,
    AutoQualificationRecord,
    BenchmarkUnit,
    BenchmarkUnitDecisionRecord,
    JudgeCandidateSelectionReport,
    EvidenceUnit,
    LineageInfo,
    ObservationRecord,
    QuestionRecord,
    SourcePaper,
    SourceQualityRecord,
    TaskBundle,
    TaskBundleInventoryReport,
    TruthManifest,
    TruthManifestBundle,
)
from .policy import EvidenceUnitType, ReleaseTier, TaskFamily
from .release import ReleaseIndexEntry


EVIDENCE_UNIT_TASK_FAMILY = {
    EvidenceUnitType.FIGURE_TABLE_RESULT: TaskFamily.RESULTS_TO_TEXT,
    EvidenceUnitType.METHODS_PROTOCOL_BLOCK: TaskFamily.METHODS_TO_TEXT,
    EvidenceUnitType.CLAIM_CLUSTER: TaskFamily.ABSTRACT_FROM_EVIDENCE,
    EvidenceUnitType.REVIEW_REVISION_BLOCK: TaskFamily.REVIEW_REVISION_RESPONSE,
}


def task_family_for_evidence_unit_type(
    unit_type: EvidenceUnitType,
    resource_description_default: TaskFamily = TaskFamily.METHODS_TO_TEXT,
) -> TaskFamily:
    if unit_type == EvidenceUnitType.RESOURCE_DESCRIPTION_BLOCK:
        return resource_description_default
    return EVIDENCE_UNIT_TASK_FAMILY[unit_type]


def build_truth_manifest_bundle(
    truth_manifest: TruthManifest,
    evidence_units: Sequence[EvidenceUnit],
    provenance_manifest_id: Optional[str] = None,
) -> TruthManifestBundle:
    if any(unit.paper_id != truth_manifest.paper_id for unit in evidence_units):
        raise ValueError("all evidence units in a truth manifest bundle must belong to the same paper")
    return TruthManifestBundle(
        bundle_id=f"TMB:{truth_manifest.manifest_id}",
        paper_id=truth_manifest.paper_id,
        manifest_id=truth_manifest.manifest_id,
        evidence_unit_ids=tuple(unit.unit_id for unit in evidence_units),
        assertion_ids=truth_manifest.assertion_ids,
        evidence_ids=truth_manifest.evidence_items,
        provenance_manifest_id=provenance_manifest_id,
        release_ready=truth_manifest.frozen and all(unit.releasable for unit in evidence_units),
        frozen_at=truth_manifest.frozen_at,
    )


def _default_authoring_constraints(task_family: TaskFamily) -> Dict[str, object]:
    constraints = {
        "evidence_only": True,
        "no_copy_from_source_manuscript": True,
        "task_family": task_family.value,
    }
    if task_family in {
        TaskFamily.LITERATURE_QA,
        TaskFamily.TRIAL_QA,
        TaskFamily.FIGURE_QA,
        TaskFamily.TABLE_QA,
        TaskFamily.SOURCE_QUALITY_QA,
    }:
        constraints.update(
            {
                "must_answer_question": True,
                "task_mode": "qa",
            }
        )
    else:
        constraints["task_mode"] = "writing"
    return constraints


def _default_scoring_profile(task_family: TaskFamily) -> Dict[str, object]:
    deterministic_checks = ["traceability", "provenance_completeness"]
    rubric_axes = ["writing_structure_compliance"]
    if task_family == TaskFamily.RESULTS_TO_TEXT:
        deterministic_checks.append("evidence_fidelity")
        rubric_axes.append("results_grounding")
    elif task_family == TaskFamily.METHODS_TO_TEXT:
        deterministic_checks.append("resource_specificity")
        rubric_axes.append("methods_specificity")
    elif task_family == TaskFamily.ABSTRACT_FROM_EVIDENCE:
        deterministic_checks.append("claim_alignment")
        rubric_axes.append("abstract_coverage")
    elif task_family == TaskFamily.REVIEW_REVISION_RESPONSE:
        deterministic_checks.append("revision_traceability")
        rubric_axes.append("response_completeness")
    elif task_family == TaskFamily.LITERATURE_QA:
        deterministic_checks.append("answer_support")
        rubric_axes.append("literature_grounding")
    elif task_family == TaskFamily.TRIAL_QA:
        deterministic_checks.extend(["trial_design_alignment", "answer_support"])
        rubric_axes.append("trial_grounding")
    elif task_family == TaskFamily.FIGURE_QA:
        deterministic_checks.extend(["figure_grounding", "answer_support"])
        rubric_axes.append("figure_observation_fidelity")
    elif task_family == TaskFamily.TABLE_QA:
        deterministic_checks.extend(["table_grounding", "answer_support"])
        rubric_axes.append("table_observation_fidelity")
    elif task_family == TaskFamily.SOURCE_QUALITY_QA:
        deterministic_checks.extend(["concern_traceability", "answer_support"])
        rubric_axes.append("quality_issue_fidelity")
    return {
        "deterministic_checks": deterministic_checks,
        "rubric_axes": rubric_axes,
    }


def build_task_bundle(
    benchmark_unit: BenchmarkUnit,
    source_paper: SourcePaper,
    evidence_units: Sequence[EvidenceUnit],
    truth_manifest: TruthManifest,
    release_tier: ReleaseTier,
    provenance_manifest_id: Optional[str] = None,
    authoring_constraints: Optional[Mapping[str, object]] = None,
    scoring_profile: Optional[Mapping[str, object]] = None,
    resource_description_default: TaskFamily = TaskFamily.METHODS_TO_TEXT,
    holdout_bucket: Optional[str] = None,
) -> TaskBundle:
    if source_paper.paper_id != benchmark_unit.paper_id or truth_manifest.paper_id != benchmark_unit.paper_id:
        raise ValueError("task bundle inputs must all reference the same paper")

    unit_map = {unit.unit_id: unit for unit in evidence_units}
    missing_unit_ids = [unit_id for unit_id in benchmark_unit.evidence_unit_ids if unit_id not in unit_map]
    if missing_unit_ids:
        raise KeyError("missing evidence units for benchmark unit: " + ", ".join(sorted(missing_unit_ids)))

    ordered_units = tuple(unit_map[unit_id] for unit_id in benchmark_unit.evidence_unit_ids)
    task_families = {
        task_family_for_evidence_unit_type(
            unit.unit_type,
            resource_description_default=resource_description_default,
        )
        for unit in ordered_units
    }
    if len(task_families) != 1:
        raise ValueError("benchmark unit maps to multiple task families and must be split before bundling")
    task_family = next(iter(task_families))

    input_artifacts = {
        "evidence_unit_ids": tuple(unit.unit_id for unit in ordered_units),
        "evidence_pointers": tuple(pointer for unit in ordered_units for pointer in unit.evidence_pointers),
        "assertion_ids": truth_manifest.assertion_ids,
        "evidence_items": truth_manifest.evidence_items,
        "evidence_types": truth_manifest.evidence_types,
    }

    bundle_authoring_constraints = dict(_default_authoring_constraints(task_family))
    if authoring_constraints:
        bundle_authoring_constraints.update(authoring_constraints)

    bundle_scoring_profile = dict(_default_scoring_profile(task_family))
    if scoring_profile:
        bundle_scoring_profile.update(scoring_profile)

    return TaskBundle(
        task_bundle_id=f"TB:{benchmark_unit.benchmark_unit_id}",
        benchmark_unit_id=benchmark_unit.benchmark_unit_id,
        task_family=task_family,
        release_tier=release_tier,
        study_class=source_paper.study_class,
        claim_mode=source_paper.claim_mode,
        input_artifacts=input_artifacts,
        authoring_constraints=bundle_authoring_constraints,
        truth_manifest_id=truth_manifest.manifest_id,
        provenance_manifest_id=provenance_manifest_id,
        scoring_profile=bundle_scoring_profile,
        paper_id=source_paper.paper_id,
        evidence_unit_ids=benchmark_unit.evidence_unit_ids,
        holdout_bucket=holdout_bucket,
    )


def build_task_bundles(
    benchmark_units: Sequence[BenchmarkUnit],
    papers: Mapping[str, SourcePaper],
    evidence_units: Mapping[str, EvidenceUnit],
    truth_manifests: Mapping[str, TruthManifest],
    release_tiers: Mapping[str, ReleaseTier],
    provenance_manifest_id: Optional[str] = None,
    resource_description_default: TaskFamily = TaskFamily.METHODS_TO_TEXT,
) -> Tuple[TaskBundle, ...]:
    bundles = []
    for benchmark_unit in benchmark_units:
        if benchmark_unit.paper_id not in papers:
            raise KeyError(f"missing source paper for {benchmark_unit.benchmark_unit_id}")
        if benchmark_unit.paper_id not in truth_manifests:
            raise KeyError(f"missing truth manifest for {benchmark_unit.paper_id}")
        if benchmark_unit.benchmark_unit_id not in release_tiers:
            raise KeyError(f"missing release tier for {benchmark_unit.benchmark_unit_id}")
        if release_tiers[benchmark_unit.benchmark_unit_id] == ReleaseTier.EXCLUDED:
            continue
        bundles.append(
            build_task_bundle(
                benchmark_unit=benchmark_unit,
                source_paper=papers[benchmark_unit.paper_id],
                evidence_units=tuple(evidence_units[unit_id] for unit_id in benchmark_unit.evidence_unit_ids),
                truth_manifest=truth_manifests[benchmark_unit.paper_id],
                release_tier=release_tiers[benchmark_unit.benchmark_unit_id],
                provenance_manifest_id=provenance_manifest_id,
                resource_description_default=resource_description_default,
            )
        )
    return tuple(bundles)


def build_benchmark_units_from_evidence_units(
    evidence_units: Sequence[EvidenceUnit],
    *,
    papers: Optional[Mapping[str, SourcePaper]] = None,
    benchmark_unit_id_prefix: str = "BU",
    default_split: Optional[str] = None,
) -> Tuple[BenchmarkUnit, ...]:
    benchmark_units = []
    for evidence_unit in sorted(evidence_units, key=lambda item: (item.paper_id, item.unit_id)):
        lineage = (
            papers[evidence_unit.paper_id].lineage
            if papers and evidence_unit.paper_id in papers
            else LineageInfo()
        )
        benchmark_units.append(
            BenchmarkUnit(
                benchmark_unit_id=f"{benchmark_unit_id_prefix}:{evidence_unit.unit_id}",
                paper_id=evidence_unit.paper_id,
                evidence_unit_ids=(evidence_unit.unit_id,),
                split=default_split,
                lineage=lineage,
            )
        )
    return tuple(benchmark_units)


def build_benchmark_unit_decisions_from_auto_qualifications(
    benchmark_units: Sequence[BenchmarkUnit],
    auto_qualification_records: Mapping[str, AutoQualificationRecord],
    *,
    include_stress_candidates: bool = False,
) -> Tuple[BenchmarkUnitDecisionRecord, ...]:
    decisions = []
    for benchmark_unit in sorted(benchmark_units, key=lambda item: item.benchmark_unit_id):
        if benchmark_unit.paper_id not in auto_qualification_records:
            raise KeyError(
                f"missing auto qualification record for benchmark unit paper {benchmark_unit.paper_id}"
            )
        record = auto_qualification_records[benchmark_unit.paper_id]
        candidate_tier = record.decision.candidate_tier
        release_tier = ReleaseTier.EXCLUDED
        reasons = [f"candidate_tier={candidate_tier.value}", f"confidence={record.confidence.value}"]
        if record.auto_release_cap_reason:
            reasons.append(f"cap={record.auto_release_cap_reason}")
        if candidate_tier.value == "shadow_candidate" and record.decision.eligible_for_unit_extraction:
            release_tier = ReleaseTier.SHADOW_GOLD
        elif include_stress_candidates and candidate_tier.value == "stress_candidate":
            release_tier = ReleaseTier.STRESS_ONLY
        decisions.append(
            BenchmarkUnitDecisionRecord(
                benchmark_unit_id=benchmark_unit.benchmark_unit_id,
                release_tier=release_tier,
                gold_eligible=release_tier == ReleaseTier.PUBLIC_GOLD,
                reasons=tuple(reasons),
            )
        )
    return tuple(decisions)


def annotate_task_bundles_with_release_index(
    task_bundles: Sequence[TaskBundle],
    release_index: Mapping[str, ReleaseIndexEntry],
    *,
    strict: bool = True,
) -> Tuple[TaskBundle, ...]:
    annotated = []
    for bundle in task_bundles:
        if bundle.benchmark_unit_id not in release_index:
            if strict:
                raise KeyError(
                    f"missing release index entry for task bundle benchmark unit {bundle.benchmark_unit_id}"
                )
            annotated.append(bundle)
            continue
        entry = release_index[bundle.benchmark_unit_id]
        annotated.append(
            replace(
                bundle,
                release_tier=entry.release_tier,
                holdout_bucket=entry.holdout_bucket,
            )
        )
    return tuple(annotated)


def build_evaluation_task_bundle(
    question: QuestionRecord,
    *,
    source_paper: SourcePaper,
    truth_manifest: TruthManifest,
    observations: Sequence[ObservationRecord],
    answers: Sequence[AnswerRecord],
    release_tier: ReleaseTier,
    provenance_manifest_id: Optional[str] = None,
    authoring_constraints: Optional[Mapping[str, object]] = None,
    scoring_profile: Optional[Mapping[str, object]] = None,
    source_quality_records: Sequence[SourceQualityRecord] = (),
    holdout_bucket: Optional[str] = None,
) -> TaskBundle:
    if source_paper.paper_id != question.paper_id or truth_manifest.paper_id != question.paper_id:
        raise ValueError("evaluation task bundle inputs must all reference the same paper")

    observation_map = {
        observation.observation_id: observation
        for observation in observations
        if observation.paper_id == question.paper_id
    }
    missing_observation_ids = [
        observation_id
        for observation_id in question.supporting_observation_ids
        if observation_id not in observation_map
    ]
    if missing_observation_ids:
        raise KeyError("missing supporting observations: " + ", ".join(sorted(missing_observation_ids)))

    answer_map = {
        answer.answer_id: answer
        for answer in answers
        if answer.paper_id == question.paper_id and answer.question_id == question.question_id
    }
    missing_answer_ids = [
        answer_id for answer_id in question.expected_answer_ids if answer_id not in answer_map
    ]
    if missing_answer_ids:
        raise KeyError("missing expected answers: " + ", ".join(sorted(missing_answer_ids)))

    ordered_observations = tuple(
        observation_map[observation_id]
        for observation_id in question.supporting_observation_ids
    )
    ordered_answers = tuple(
        answer_map[answer_id]
        for answer_id in question.expected_answer_ids
    )
    linked_quality_records = tuple(
        record
        for record in source_quality_records
        if record.paper_id == question.paper_id
        and set(record.supporting_observation_ids).intersection(question.supporting_observation_ids)
    )

    input_artifacts = {
        "question_id": question.question_id,
        "question_prompt": question.prompt,
        "answer_format": question.answer_format.value,
        "supporting_observation_ids": question.supporting_observation_ids,
        "supporting_observation_texts": tuple(observation.text for observation in ordered_observations),
        "evidence_pointers": question.supporting_evidence_pointers,
        "evidence_items": tuple(observation.text for observation in ordered_observations),
        "evidence_types": tuple(observation.observation_type.value for observation in ordered_observations),
        "expected_answer_ids": question.expected_answer_ids,
        "expected_answer_texts": tuple(answer.answer_text for answer in ordered_answers),
        "source_quality_record_ids": tuple(record.quality_record_id for record in linked_quality_records),
        "source_quality_concerns": tuple(record.concern_type.value for record in linked_quality_records),
    }

    bundle_authoring_constraints = dict(_default_authoring_constraints(question.task_family))
    if authoring_constraints:
        bundle_authoring_constraints.update(authoring_constraints)

    bundle_scoring_profile = dict(_default_scoring_profile(question.task_family))
    if scoring_profile:
        bundle_scoring_profile.update(scoring_profile)

    evidence_unit_ids = tuple(
        observation.evidence_unit_id
        for observation in ordered_observations
        if observation.evidence_unit_id
    )

    return TaskBundle(
        task_bundle_id=f"TBQ:{question.question_id}",
        benchmark_unit_id=f"Q:{question.question_id}",
        task_family=question.task_family,
        release_tier=release_tier,
        study_class=source_paper.study_class,
        claim_mode=source_paper.claim_mode,
        input_artifacts=input_artifacts,
        authoring_constraints=bundle_authoring_constraints,
        truth_manifest_id=truth_manifest.manifest_id,
        provenance_manifest_id=provenance_manifest_id,
        scoring_profile=bundle_scoring_profile,
        paper_id=source_paper.paper_id,
        evidence_unit_ids=evidence_unit_ids,
        holdout_bucket=holdout_bucket,
    )


def build_evaluation_task_bundles(
    *,
    questions: Sequence[QuestionRecord],
    answers: Sequence[AnswerRecord],
    observations: Sequence[ObservationRecord],
    papers: Mapping[str, SourcePaper],
    truth_manifests: Mapping[str, TruthManifest],
    default_release_tier: ReleaseTier = ReleaseTier.SHADOW_GOLD,
    release_tiers_by_question: Optional[Mapping[str, ReleaseTier]] = None,
    provenance_manifest_id: Optional[str] = None,
    source_quality_records: Sequence[SourceQualityRecord] = (),
) -> Tuple[TaskBundle, ...]:
    answer_map: Dict[str, Tuple[AnswerRecord, ...]] = {}
    for answer in answers:
        answer_map.setdefault(answer.question_id, ())
        answer_map[answer.question_id] = answer_map[answer.question_id] + (answer,)

    observation_map: Dict[str, Tuple[ObservationRecord, ...]] = {}
    for observation in observations:
        observation_map.setdefault(observation.paper_id, ())
        observation_map[observation.paper_id] = observation_map[observation.paper_id] + (observation,)

    bundles = []
    for question in questions:
        if question.paper_id not in papers:
            raise KeyError(f"missing source paper for question {question.question_id}")
        if question.paper_id not in truth_manifests:
            raise KeyError(f"missing truth manifest for question {question.question_id}")
        release_tier = (
            release_tiers_by_question[question.question_id]
            if release_tiers_by_question and question.question_id in release_tiers_by_question
            else default_release_tier
        )
        if release_tier == ReleaseTier.EXCLUDED:
            continue
        bundles.append(
            build_evaluation_task_bundle(
                question,
                source_paper=papers[question.paper_id],
                truth_manifest=truth_manifests[question.paper_id],
                observations=observation_map.get(question.paper_id, ()),
                answers=answer_map.get(question.question_id, ()),
                release_tier=release_tier,
                provenance_manifest_id=provenance_manifest_id,
                source_quality_records=source_quality_records,
            )
        )
    return tuple(bundles)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def summarize_task_bundles(task_bundles: Iterable[TaskBundle]) -> TaskBundleInventoryReport:
    bundles = tuple(task_bundles)
    task_family_counts = Counter(bundle.task_family.value for bundle in bundles)
    study_class_counts = Counter(bundle.study_class.value for bundle in bundles)
    claim_mode_counts = Counter(bundle.claim_mode.value for bundle in bundles)
    release_tier_counts = Counter(bundle.release_tier.value for bundle in bundles)
    holdout_bucket_counts = Counter(bundle.holdout_bucket or "unassigned" for bundle in bundles)
    return TaskBundleInventoryReport(
        generated_at=_utc_timestamp(),
        total_bundles=len(bundles),
        task_family_counts=dict(task_family_counts),
        study_class_counts=dict(study_class_counts),
        claim_mode_counts=dict(claim_mode_counts),
        release_tier_counts=dict(release_tier_counts),
        holdout_bucket_counts=dict(holdout_bucket_counts),
    )


def select_judge_candidate_task_bundles(
    task_bundles: Sequence[TaskBundle],
    *,
    target_total: int,
    include_task_families: Optional[Sequence[TaskFamily]] = None,
    include_release_tiers: Optional[Sequence[ReleaseTier]] = None,
    include_holdout_buckets: Optional[Sequence[str]] = None,
) -> Tuple[TaskBundle, ...]:
    if target_total <= 0:
        raise ValueError("target_total must be positive")

    eligible = [
        bundle
        for bundle in task_bundles
        if bundle.release_tier != ReleaseTier.EXCLUDED
    ]
    if include_task_families:
        allowed = {task_family.value for task_family in include_task_families}
        eligible = [bundle for bundle in eligible if bundle.task_family.value in allowed]
    if include_release_tiers:
        allowed = {release_tier.value for release_tier in include_release_tiers}
        eligible = [bundle for bundle in eligible if bundle.release_tier.value in allowed]
    if include_holdout_buckets:
        allowed = {str(bucket) for bucket in include_holdout_buckets}
        eligible = [bundle for bundle in eligible if (bundle.holdout_bucket or "unassigned") in allowed]
    if not eligible:
        return ()

    groups: Dict[Tuple[str, str], List[TaskBundle]] = {}
    for bundle in sorted(
        eligible,
        key=lambda item: (
            item.task_family.value,
            item.study_class.value,
            item.release_tier.value,
            item.task_bundle_id,
        ),
    ):
        groups.setdefault((bundle.task_family.value, bundle.study_class.value), []).append(bundle)

    selected: List[TaskBundle] = []
    selected_ids = set()
    group_order = sorted(groups)
    while len(selected) < target_total:
        progressed = False
        for key in group_order:
            candidates = groups[key]
            while candidates and candidates[0].task_bundle_id in selected_ids:
                candidates.pop(0)
            if not candidates:
                continue
            bundle = candidates.pop(0)
            selected.append(bundle)
            selected_ids.add(bundle.task_bundle_id)
            progressed = True
            if len(selected) >= target_total:
                break
        if not progressed:
            break
    return tuple(selected)


def summarize_judge_candidate_selection(
    selected_task_bundles: Sequence[TaskBundle],
    *,
    target_total: int,
) -> JudgeCandidateSelectionReport:
    inventory = summarize_task_bundles(selected_task_bundles)
    notes = []
    if len(selected_task_bundles) < target_total:
        notes.append(
            f"selected bundle count {len(selected_task_bundles)} is below requested target_total {target_total}"
        )
    return JudgeCandidateSelectionReport(
        generated_at=inventory.generated_at,
        target_total=target_total,
        selected_total=len(selected_task_bundles),
        task_family_counts=inventory.task_family_counts,
        study_class_counts=inventory.study_class_counts,
        claim_mode_counts=inventory.claim_mode_counts,
        release_tier_counts=inventory.release_tier_counts,
        holdout_bucket_counts=inventory.holdout_bucket_counts,
        notes=tuple(notes),
    )
