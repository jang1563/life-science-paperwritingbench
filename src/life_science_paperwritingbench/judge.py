from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .models import EvaluationRecord, JudgeSliceAuditReport, JudgeValidationUnit, LLMJudgeAlignmentReport, TaskBundle
from .policy import ReleaseTier, TaskFamily
from .tasking import select_judge_candidate_task_bundles


DEFAULT_JUDGE_RUBRIC_AXES = (
    "evidence_fidelity",
    "traceability",
    "provenance_completeness",
    "writing_structure_compliance",
)

MIN_JUDGE_RUBRIC_SCORE = 0.0
MAX_JUDGE_RUBRIC_SCORE = 3.0
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


def _numeric_judge_rubric_score(value: object) -> Optional[float]:
    if _is_missing_rubric_value(value) or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    if numeric < MIN_JUDGE_RUBRIC_SCORE or numeric > MAX_JUDGE_RUBRIC_SCORE:
        return None
    return numeric


def _bool(value: object, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False
    return bool(value)


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
        if _numeric_judge_rubric_score(judge_unit.rubric_labels[normalized]) is None:
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


def audit_llm_judge_alignment(
    task_bundles: Sequence[TaskBundle],
    evaluations: Sequence[EvaluationRecord],
    judgments: Sequence[Mapping[str, Any]],
) -> LLMJudgeAlignmentReport:
    """Audit agreement between deterministic submission scoring and judge pass/fail.

    The count-based A1 gate is intentionally preserved, but the stronger
    condition for internal consistency is whether the judge-pass set is a
    subset of the deterministic-pass set. A count match alone can still hide
    judge-only failures where the deterministic layer is stricter than the
    judge on specific bundles.
    """

    task_bundle_map = {bundle.task_bundle_id: bundle for bundle in task_bundles}
    expected_task_bundle_ids = set(task_bundle_map)

    evaluation_counter = Counter(record.task_bundle_id for record in evaluations)
    judgment_counter = Counter(
        str(record.get("task_bundle_id", "")).strip()
        for record in judgments
        if str(record.get("task_bundle_id", "")).strip()
    )

    evaluation_map: Dict[str, EvaluationRecord] = {}
    for record in evaluations:
        evaluation_map.setdefault(record.task_bundle_id, record)

    judgment_map: Dict[str, Mapping[str, Any]] = {}
    for record in judgments:
        task_bundle_id = str(record.get("task_bundle_id", "")).strip()
        if not task_bundle_id:
            continue
        judgment_map.setdefault(task_bundle_id, record)

    evaluation_ids = set(evaluation_map)
    judgment_ids = set(judgment_map)
    duplicate_evaluation_ids = tuple(
        sorted(task_bundle_id for task_bundle_id, count in evaluation_counter.items() if count > 1)
    )
    duplicate_judgment_ids = tuple(
        sorted(task_bundle_id for task_bundle_id, count in judgment_counter.items() if count > 1)
    )
    missing_evaluation_ids = tuple(sorted(expected_task_bundle_ids - evaluation_ids))
    missing_judgment_ids = tuple(sorted(expected_task_bundle_ids - judgment_ids))
    extra_evaluation_ids = tuple(sorted(evaluation_ids - expected_task_bundle_ids))
    extra_judgment_ids = tuple(sorted(judgment_ids - expected_task_bundle_ids))

    comparable_ids = tuple(sorted(expected_task_bundle_ids & evaluation_ids & judgment_ids))
    deterministic_pass_ids = {
        task_bundle_id
        for task_bundle_id in comparable_ids
        if evaluation_map[task_bundle_id].deterministic_checks_passed
    }
    judge_pass_ids = {
        task_bundle_id
        for task_bundle_id in comparable_ids
        if _bool(judgment_map[task_bundle_id].get("overall_pass", False))
    }

    overlap_pass_ids = tuple(sorted(deterministic_pass_ids & judge_pass_ids))
    deterministic_only_ids = tuple(sorted(deterministic_pass_ids - judge_pass_ids))
    judge_only_ids = tuple(sorted(judge_pass_ids - deterministic_pass_ids))
    agreement_count = 0
    disagreement_count = 0
    per_task_family: Dict[str, Dict[str, int]] = {}

    for task_bundle_id in comparable_ids:
        bundle = task_bundle_map[task_bundle_id]
        family = bundle.task_family.value
        deterministic_pass = task_bundle_id in deterministic_pass_ids
        judge_pass = task_bundle_id in judge_pass_ids
        bucket = per_task_family.setdefault(
            family,
            {
                "total": 0,
                "deterministic_pass": 0,
                "judge_pass": 0,
                "overlap_pass": 0,
                "deterministic_only": 0,
                "judge_only": 0,
                "agreement": 0,
                "disagreement": 0,
                "true_positive": 0,
                "true_negative": 0,
                "false_positive": 0,
                "false_negative": 0,
            },
        )
        bucket["total"] += 1
        bucket["deterministic_pass"] += int(deterministic_pass)
        bucket["judge_pass"] += int(judge_pass)
        bucket["overlap_pass"] += int(deterministic_pass and judge_pass)
        bucket["deterministic_only"] += int(deterministic_pass and not judge_pass)
        bucket["judge_only"] += int((not deterministic_pass) and judge_pass)
        if deterministic_pass == judge_pass:
            agreement_count += 1
            bucket["agreement"] += 1
        else:
            disagreement_count += 1
            bucket["disagreement"] += 1
        if deterministic_pass and judge_pass:
            bucket["true_positive"] += 1
        elif (not deterministic_pass) and (not judge_pass):
            bucket["true_negative"] += 1
        elif deterministic_pass and not judge_pass:
            bucket["false_positive"] += 1
        else:
            bucket["false_negative"] += 1

    deterministic_pass_count = sum(
        1
        for task_bundle_id in expected_task_bundle_ids & evaluation_ids
        if evaluation_map[task_bundle_id].deterministic_checks_passed
    )
    judge_pass_count = sum(
        1
        for task_bundle_id in expected_task_bundle_ids & judgment_ids
        if _bool(judgment_map[task_bundle_id].get("overall_pass", False))
    )

    comparable_complete = len(comparable_ids) == len(expected_task_bundle_ids)
    gate_a1_count_ok = comparable_complete and deterministic_pass_count >= judge_pass_count
    judge_pass_subset_ok = comparable_complete and not judge_only_ids
    exact_pass_set_match = comparable_complete and not deterministic_only_ids and not judge_only_ids

    issues: List[str] = []
    if duplicate_evaluation_ids:
        issues.append("deterministic evaluation artifact contains duplicate task_bundle_id values")
    if duplicate_judgment_ids:
        issues.append("judge artifact contains duplicate task_bundle_id values")
    if missing_evaluation_ids:
        issues.append("deterministic evaluation artifact is missing expected task bundles")
    if missing_judgment_ids:
        issues.append("judge artifact is missing expected task bundles")
    if extra_evaluation_ids:
        issues.append("deterministic evaluation artifact references unknown task bundles")
    if extra_judgment_ids:
        issues.append("judge artifact references unknown task bundles")
    if comparable_complete and deterministic_pass_count < judge_pass_count:
        issues.append("deterministic pass count is lower than judge pass count")
    if comparable_complete and judge_only_ids:
        issues.append("judge-pass set is not a subset of the deterministic-pass set")
    if comparable_complete and gate_a1_count_ok and (deterministic_only_ids or judge_only_ids):
        issues.append("count gate passes, but bundle-level pass sets do not fully align")

    agreement_rate = round(agreement_count / len(comparable_ids), 3) if comparable_ids else 0.0
    return LLMJudgeAlignmentReport(
        generated_at=_utc_timestamp(),
        total_task_bundles=len(expected_task_bundle_ids),
        evaluated_bundles=len(expected_task_bundle_ids & evaluation_ids),
        judged_bundles=len(expected_task_bundle_ids & judgment_ids),
        comparable_bundles=len(comparable_ids),
        deterministic_pass_count=deterministic_pass_count,
        judge_pass_count=judge_pass_count,
        overlap_pass_count=len(overlap_pass_ids),
        deterministic_only_count=len(deterministic_only_ids),
        judge_only_count=len(judge_only_ids),
        agreement_count=agreement_count,
        disagreement_count=disagreement_count,
        agreement_rate=agreement_rate,
        gate_a1_count_ok=gate_a1_count_ok,
        judge_pass_subset_ok=judge_pass_subset_ok,
        exact_pass_set_match=exact_pass_set_match,
        duplicate_evaluation_task_bundle_ids=duplicate_evaluation_ids,
        duplicate_judgment_task_bundle_ids=duplicate_judgment_ids,
        missing_evaluation_task_bundle_ids=missing_evaluation_ids,
        missing_judgment_task_bundle_ids=missing_judgment_ids,
        extra_evaluation_task_bundle_ids=extra_evaluation_ids,
        extra_judgment_task_bundle_ids=extra_judgment_ids,
        deterministic_only_task_bundle_ids=deterministic_only_ids,
        judge_only_task_bundle_ids=judge_only_ids,
        per_task_family=per_task_family,
        issues=tuple(issues),
        ok=(
            not duplicate_evaluation_ids
            and not duplicate_judgment_ids
            and not missing_evaluation_ids
            and not missing_judgment_ids
            and not extra_evaluation_ids
            and not extra_judgment_ids
            and gate_a1_count_ok
            and judge_pass_subset_ok
        ),
    )


def render_llm_judge_alignment_markdown(report: LLMJudgeAlignmentReport) -> str:
    lines: List[str] = []
    lines.append("# LLM Evaluation Alignment Audit")
    lines.append("")
    lines.append(f"- task bundles: `{report.total_task_bundles}`")
    lines.append(f"- evaluated bundles: `{report.evaluated_bundles}`")
    lines.append(f"- judged bundles: `{report.judged_bundles}`")
    lines.append(f"- comparable bundles: `{report.comparable_bundles}`")
    lines.append(f"- deterministic pass count: `{report.deterministic_pass_count}`")
    lines.append(f"- judge pass count: `{report.judge_pass_count}`")
    lines.append(f"- overlap pass count: `{report.overlap_pass_count}`")
    lines.append(f"- deterministic-only passes: `{report.deterministic_only_count}`")
    lines.append(f"- judge-only passes: `{report.judge_only_count}`")
    lines.append(f"- agreement rate: `{report.agreement_rate:.3f}`")
    lines.append(f"- Gate A1 count check (`det >= judge`): `{report.gate_a1_count_ok}`")
    lines.append(
        "- Judge-pass subset check (`judge_pass_set ⊆ deterministic_pass_set`): "
        f"`{report.judge_pass_subset_ok}`"
    )
    lines.append(f"- Exact pass-set match: `{report.exact_pass_set_match}`")
    lines.append(f"- audit ok: `{report.ok}`")
    lines.append("")
    lines.append("## Per Task Family")
    lines.append("")
    lines.append(
        "| task_family | total | det pass | judge pass | overlap | det-only | judge-only | agreement | disagreement |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for family in sorted(report.per_task_family):
        metrics = report.per_task_family[family]
        lines.append(
            f"| {family} | {metrics['total']} | {metrics['deterministic_pass']} | {metrics['judge_pass']} | "
            f"{metrics['overlap_pass']} | {metrics['deterministic_only']} | {metrics['judge_only']} | "
            f"{metrics['agreement']} | {metrics['disagreement']} |"
        )
    if report.deterministic_only_task_bundle_ids:
        lines.append("")
        lines.append("## Deterministic-Only Passes")
        lines.append("")
        for task_bundle_id in report.deterministic_only_task_bundle_ids:
            lines.append(f"- `{task_bundle_id}`")
    if report.judge_only_task_bundle_ids:
        lines.append("")
        lines.append("## Judge-Only Passes")
        lines.append("")
        for task_bundle_id in report.judge_only_task_bundle_ids:
            lines.append(f"- `{task_bundle_id}`")
    if report.issues:
        lines.append("")
        lines.append("## Issues")
        lines.append("")
        for issue in report.issues:
            lines.append(f"- {issue}")
    return "\n".join(lines)
