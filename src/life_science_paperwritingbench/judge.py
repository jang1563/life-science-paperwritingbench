from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .models import JudgeSliceAuditReport, JudgeValidationUnit, TaskBundle
from .policy import ReleaseTier, TaskFamily
from .tasking import select_judge_candidate_task_bundles


DEFAULT_JUDGE_RUBRIC_AXES = (
    "evidence_fidelity",
    "traceability",
    "provenance_completeness",
    "writing_structure_compliance",
)

DEFAULT_JUDGE_SLICE_SIZE = 30


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rubric_template(rubric_axes: Sequence[str]) -> Dict[str, Optional[float]]:
    template: Dict[str, Optional[float]] = {}
    for axis in rubric_axes:
        normalized = str(axis).strip()
        if not normalized:
            continue
        template[normalized] = None
    return template


def build_judge_validation_units(
    task_bundles: Sequence[TaskBundle],
    *,
    rubric_axes: Sequence[str] = DEFAULT_JUDGE_RUBRIC_AXES,
    human_adjudicated: bool = False,
    frozen: bool = False,
    adjudicator_id: Optional[str] = None,
    rubric_version: str = "judge-rubric-v1",
) -> Tuple[JudgeValidationUnit, ...]:
    rubric_template = _rubric_template(rubric_axes)
    judge_units = []
    for bundle in task_bundles:
        judge_units.append(
            JudgeValidationUnit(
                validation_unit_id=f"JV:{bundle.task_bundle_id}",
                task_bundle_id=bundle.task_bundle_id,
                human_adjudicated=human_adjudicated,
                rubric_labels=dict(rubric_template),
                frozen=frozen,
                rubric_version=rubric_version,
                adjudicator_id=adjudicator_id if human_adjudicated else None,
                notes=(
                    "judge_validation_template",
                    f"task_family={bundle.task_family.value}",
                    f"release_tier={bundle.release_tier.value}",
                ),
            )
        )
    return tuple(judge_units)


def _is_missing_rubric_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (tuple, list, dict)):
        return len(value) == 0
    return False


def missing_required_rubric_axes(
    judge_unit: JudgeValidationUnit,
    *,
    required_axes: Sequence[str] = DEFAULT_JUDGE_RUBRIC_AXES,
) -> Tuple[str, ...]:
    missing = []
    for axis in required_axes:
        normalized = str(axis).strip()
        if not normalized:
            continue
        if normalized not in judge_unit.rubric_labels:
            missing.append(normalized)
            continue
        if _is_missing_rubric_value(judge_unit.rubric_labels[normalized]):
            missing.append(normalized)
    return tuple(missing)


def judge_validation_unit_ready(
    judge_unit: JudgeValidationUnit,
    *,
    required_axes: Sequence[str] = DEFAULT_JUDGE_RUBRIC_AXES,
) -> bool:
    return (
        judge_unit.human_adjudicated
        and judge_unit.frozen
        and not missing_required_rubric_axes(judge_unit, required_axes=required_axes)
    )


def build_judge_validation_slice(
    task_bundles: Sequence[TaskBundle],
    *,
    target_total: int = DEFAULT_JUDGE_SLICE_SIZE,
    include_task_families: Optional[Sequence[TaskFamily]] = None,
    include_release_tiers: Optional[Sequence[ReleaseTier]] = None,
    include_holdout_buckets: Optional[Sequence[str]] = None,
    rubric_axes: Sequence[str] = DEFAULT_JUDGE_RUBRIC_AXES,
    human_adjudicated: bool = False,
    frozen: bool = False,
    adjudicator_id: Optional[str] = None,
    rubric_version: str = "judge-rubric-v1",
) -> Tuple[JudgeValidationUnit, ...]:
    selected = select_judge_candidate_task_bundles(
        task_bundles,
        target_total=target_total,
        include_task_families=include_task_families,
        include_release_tiers=include_release_tiers,
        include_holdout_buckets=include_holdout_buckets,
    )
    if not selected:
        return ()
    return build_judge_validation_units(
        selected,
        rubric_axes=rubric_axes,
        human_adjudicated=human_adjudicated,
        frozen=frozen,
        adjudicator_id=adjudicator_id,
        rubric_version=rubric_version,
    )


def audit_judge_validation_slice(
    task_bundles: Sequence[TaskBundle],
    judge_units: Sequence[JudgeValidationUnit],
    *,
    minimum_total: int = DEFAULT_JUDGE_SLICE_SIZE,
    required_axes: Sequence[str] = DEFAULT_JUDGE_RUBRIC_AXES,
) -> JudgeSliceAuditReport:
    task_bundle_map = {bundle.task_bundle_id: bundle for bundle in task_bundles}
    validation_counter = Counter(unit.validation_unit_id for unit in judge_units)
    task_bundle_counter = Counter(unit.task_bundle_id for unit in judge_units)

    missing_task_bundle_ids = tuple(
        sorted({unit.task_bundle_id for unit in judge_units if unit.task_bundle_id not in task_bundle_map})
    )
    duplicate_validation_unit_ids = tuple(
        sorted(validation_unit_id for validation_unit_id, count in validation_counter.items() if count > 1)
    )
    duplicate_task_bundle_ids = tuple(
        sorted(task_bundle_id for task_bundle_id, count in task_bundle_counter.items() if count > 1)
    )

    human_adjudicated_units = sum(1 for unit in judge_units if unit.human_adjudicated)
    frozen_units = sum(1 for unit in judge_units if unit.frozen)
    ready_units = 0
    task_family_counts: Dict[str, int] = {}
    study_class_counts: Dict[str, int] = {}
    release_tier_counts: Dict[str, int] = {}
    missing_rubric_axes: Dict[str, Tuple[str, ...]] = {}

    linked_task_bundle_ids = set()
    for unit in judge_units:
        bundle = task_bundle_map.get(unit.task_bundle_id)
        if bundle is None:
            continue
        linked_task_bundle_ids.add(bundle.task_bundle_id)
        task_family_counts[bundle.task_family.value] = task_family_counts.get(bundle.task_family.value, 0) + 1
        study_class_counts[bundle.study_class.value] = study_class_counts.get(bundle.study_class.value, 0) + 1
        release_tier_counts[bundle.release_tier.value] = release_tier_counts.get(bundle.release_tier.value, 0) + 1
        missing_axes = missing_required_rubric_axes(unit, required_axes=required_axes)
        if missing_axes:
            missing_rubric_axes[unit.validation_unit_id] = missing_axes
        if judge_validation_unit_ready(unit, required_axes=required_axes):
            ready_units += 1

    issues: List[str] = []
    if len(judge_units) < minimum_total:
        issues.append(f"judge validation slice must contain at least {minimum_total} units")
    if human_adjudicated_units < minimum_total:
        issues.append(f"judge validation slice must contain at least {minimum_total} human-adjudicated units")
    if frozen_units < minimum_total:
        issues.append(f"judge validation slice must contain at least {minimum_total} frozen units")
    if ready_units < minimum_total:
        issues.append(
            "judge validation slice must contain at least "
            f"{minimum_total} ready units with required rubric axes"
        )
    if missing_task_bundle_ids:
        issues.append("judge validation slice references unknown task bundles")
    if duplicate_validation_unit_ids:
        issues.append("judge validation slice contains duplicate validation_unit_id values")
    if duplicate_task_bundle_ids:
        issues.append("judge validation slice contains duplicate task_bundle_id values")

    return JudgeSliceAuditReport(
        generated_at=_utc_timestamp(),
        total_units=len(judge_units),
        human_adjudicated_units=human_adjudicated_units,
        frozen_units=frozen_units,
        ready_units=ready_units,
        linked_task_bundles=len(linked_task_bundle_ids),
        task_family_counts=task_family_counts,
        study_class_counts=study_class_counts,
        release_tier_counts=release_tier_counts,
        missing_task_bundle_ids=missing_task_bundle_ids,
        duplicate_validation_unit_ids=duplicate_validation_unit_ids,
        duplicate_task_bundle_ids=duplicate_task_bundle_ids,
        missing_rubric_axes=missing_rubric_axes,
        issues=tuple(issues),
        ok=not issues,
    )
