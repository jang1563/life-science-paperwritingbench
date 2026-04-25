from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .frontier_runtime import (
    default_canary_models,
    default_frontier_registry_path,
    load_frontier_registry,
)
from .judge import build_judge_validation_units
from .models import JudgeValidationUnit, TaskBundle
from .policy import ReleaseTier, TaskFamily


FRONTIER_WRITING_TASK_FAMILIES: Tuple[TaskFamily, ...] = (
    TaskFamily.METHODS_TO_TEXT,
    TaskFamily.RESULTS_TO_TEXT,
    TaskFamily.ABSTRACT_FROM_EVIDENCE,
)
DEFAULT_PUBLICATION_TARGET_PER_FAMILY = 20
DEFAULT_PUBLICATION_REVIEWER_COUNT = 2
DEFAULT_PUBLICATION_ADJUDICATOR_COUNT = 1
PRE_ADJUDICATION_KAPPA_THRESHOLD = 0.4
POST_ADJUDICATION_KAPPA_THRESHOLD = 0.6
JURY_VS_ADJUDICATOR_ICC_THRESHOLD = 0.5


def _eligible_publication_bundles(
    task_bundles: Sequence[TaskBundle],
    *,
    task_family: TaskFamily,
    include_holdout_buckets: Optional[Sequence[str]] = None,
) -> Tuple[TaskBundle, ...]:
    allowed_holdouts = {str(bucket) for bucket in include_holdout_buckets} if include_holdout_buckets else None
    eligible = []
    for bundle in task_bundles:
        if bundle.release_tier == ReleaseTier.EXCLUDED:
            continue
        if bundle.task_family != task_family:
            continue
        if allowed_holdouts is not None and (bundle.holdout_bucket or "unassigned") not in allowed_holdouts:
            continue
        eligible.append(bundle)
    return tuple(
        sorted(
            eligible,
            key=lambda item: (
                item.study_class.value,
                item.release_tier.value,
                item.task_bundle_id,
            ),
        )
    )


def _balanced_study_class_targets(
    bundles: Sequence[TaskBundle],
    *,
    target_total: int,
) -> Dict[str, int]:
    available_counts = Counter(bundle.study_class.value for bundle in bundles)
    if target_total <= 0 or not available_counts:
        return {}
    targets = {study_class: 0 for study_class in sorted(available_counts)}
    total_assigned = 0
    while total_assigned < target_total:
        progressed = False
        for study_class in sorted(targets):
            if targets[study_class] >= available_counts[study_class]:
                continue
            targets[study_class] += 1
            total_assigned += 1
            progressed = True
            if total_assigned >= target_total:
                break
        if not progressed:
            break
    return {study_class: count for study_class, count in targets.items() if count > 0}


def _select_publication_family_bundles(
    task_bundles: Sequence[TaskBundle],
    *,
    task_family: TaskFamily,
    target_total: int,
    include_holdout_buckets: Optional[Sequence[str]] = None,
) -> Tuple[TaskBundle, ...]:
    eligible = _eligible_publication_bundles(
        task_bundles,
        task_family=task_family,
        include_holdout_buckets=include_holdout_buckets,
    )
    if not eligible:
        return ()
    targets = _balanced_study_class_targets(eligible, target_total=target_total)
    groups: Dict[str, list[TaskBundle]] = {}
    for bundle in eligible:
        groups.setdefault(bundle.study_class.value, []).append(bundle)

    selected = []
    taken = {study_class: 0 for study_class in targets}
    while len(selected) < sum(targets.values()):
        progressed = False
        for study_class in sorted(targets):
            if taken[study_class] >= targets[study_class]:
                continue
            candidates = groups.get(study_class, [])
            if not candidates:
                continue
            selected.append(candidates.pop(0))
            taken[study_class] += 1
            progressed = True
        if not progressed:
            break
    return tuple(selected)


def build_publication_validation_slice(
    task_bundles: Sequence[TaskBundle],
    *,
    target_per_family: int = DEFAULT_PUBLICATION_TARGET_PER_FAMILY,
    include_holdout_buckets: Optional[Sequence[str]] = None,
    human_adjudicated: bool = False,
    frozen: bool = False,
    adjudicator_id: Optional[str] = None,
    rubric_version: str = "judge-rubric-v1",
) -> Tuple[JudgeValidationUnit, ...]:
    selected_bundles = []
    seen_task_bundle_ids = set()
    for task_family in FRONTIER_WRITING_TASK_FAMILIES:
        family_selected = _select_publication_family_bundles(
            task_bundles,
            task_family=task_family,
            target_total=target_per_family,
            include_holdout_buckets=include_holdout_buckets,
        )
        for bundle in family_selected:
            if bundle.task_bundle_id in seen_task_bundle_ids:
                continue
            selected_bundles.append(bundle)
            seen_task_bundle_ids.add(bundle.task_bundle_id)
    return build_judge_validation_units(
        tuple(selected_bundles),
        human_adjudicated=human_adjudicated,
        frozen=frozen,
        adjudicator_id=adjudicator_id,
        rubric_version=rubric_version,
    )


def summarize_publication_validation_slice(
    task_bundles: Sequence[TaskBundle],
    judge_units: Sequence[JudgeValidationUnit],
    *,
    target_per_family: int = DEFAULT_PUBLICATION_TARGET_PER_FAMILY,
    include_holdout_buckets: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    bundle_map = {bundle.task_bundle_id: bundle for bundle in task_bundles}
    task_family_counts: Counter[str] = Counter()
    study_class_counts: Counter[str] = Counter()
    per_family_study_class_counts: Dict[str, Counter[str]] = {
        task_family.value: Counter() for task_family in FRONTIER_WRITING_TASK_FAMILIES
    }
    missing_task_bundle_ids = []
    for unit in judge_units:
        bundle = bundle_map.get(unit.task_bundle_id)
        if bundle is None:
            missing_task_bundle_ids.append(unit.task_bundle_id)
            continue
        task_family_counts[bundle.task_family.value] += 1
        study_class_counts[bundle.study_class.value] += 1
        per_family_study_class_counts.setdefault(bundle.task_family.value, Counter())[bundle.study_class.value] += 1

    per_family_study_class_targets: Dict[str, Dict[str, int]] = {}
    per_family_study_class_deficits: Dict[str, Dict[str, int]] = {}
    per_family_stratification_ready: Dict[str, bool] = {}
    per_family_available_study_classes: Dict[str, Tuple[str, ...]] = {}
    for task_family in FRONTIER_WRITING_TASK_FAMILIES:
        family_bundles = _eligible_publication_bundles(
            task_bundles,
            task_family=task_family,
            include_holdout_buckets=include_holdout_buckets,
        )
        family_targets = _balanced_study_class_targets(
            family_bundles,
            target_total=target_per_family,
        )
        family_counts = per_family_study_class_counts.get(task_family.value, Counter())
        deficits = {
            study_class: max(target_count - int(family_counts.get(study_class, 0)), 0)
            for study_class, target_count in family_targets.items()
        }
        per_family_study_class_targets[task_family.value] = family_targets
        per_family_study_class_deficits[task_family.value] = deficits
        per_family_available_study_classes[task_family.value] = tuple(sorted(family_targets))
        per_family_stratification_ready[task_family.value] = all(value == 0 for value in deficits.values())

    target_total = target_per_family * len(FRONTIER_WRITING_TASK_FAMILIES)
    task_family_targets = {
        task_family.value: target_per_family for task_family in FRONTIER_WRITING_TASK_FAMILIES
    }
    per_family_ready = {
        family: task_family_counts.get(family, 0) >= target
        for family, target in task_family_targets.items()
    }
    return {
        "target_per_family": target_per_family,
        "target_total": target_total,
        "selected_total": len(judge_units),
        "task_family_counts": dict(task_family_counts),
        "study_class_counts": dict(study_class_counts),
        "per_family_study_class_counts": {
            family: dict(counter)
            for family, counter in per_family_study_class_counts.items()
        },
        "task_family_targets": task_family_targets,
        "per_family_study_class_targets": per_family_study_class_targets,
        "per_family_study_class_deficits": per_family_study_class_deficits,
        "per_family_available_study_classes": per_family_available_study_classes,
        "per_family_ready": per_family_ready,
        "per_family_stratification_ready": per_family_stratification_ready,
        "study_class_stratification_ready": all(per_family_stratification_ready.values()),
        "missing_task_bundle_ids": tuple(sorted(missing_task_bundle_ids)),
        "reviewer_plan": {
            "reviewers_required": DEFAULT_PUBLICATION_REVIEWER_COUNT,
            "adjudicators_required": DEFAULT_PUBLICATION_ADJUDICATOR_COUNT,
        },
        "agreement_thresholds": {
            "pre_adjudication_kappa": PRE_ADJUDICATION_KAPPA_THRESHOLD,
            "post_adjudication_kappa": POST_ADJUDICATION_KAPPA_THRESHOLD,
            "jury_vs_adjudicator_icc": JURY_VS_ADJUDICATOR_ICC_THRESHOLD,
        },
        "ready": (
            len(judge_units) >= target_total
            and all(per_family_ready.values())
            and all(per_family_stratification_ready.values())
            and not missing_task_bundle_ids
        ),
    }


def summarize_publication_readiness(
    *,
    matrix_summary: Mapping[str, Any],
    canary_summary: Mapping[str, Any],
    validation_summary: Mapping[str, Any],
    agreement_metrics: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    def _resolve_registry_path() -> Path:
        for summary in (matrix_summary, canary_summary):
            raw = str(summary.get("registry_path", "")).strip()
            if raw:
                return Path(raw)
        return default_frontier_registry_path()

    def _required_registry_targets(
        registry: Mapping[str, Mapping[str, Any]],
    ) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
        official_judges = []
        hosted_submitters = []
        for label, entry in registry.items():
            role_eligibility = str(entry.get("role_eligibility", "")).strip()
            if (
                role_eligibility in {"judge", "both"}
                and entry.get("judge_policy") == "official"
                and entry.get("execution_target") == "hosted_api"
            ):
                official_judges.append(label)
            if (
                role_eligibility in {"submitter", "both"}
                and entry.get("submitter_track") == "hosted_frontier"
            ):
                hosted_submitters.append(label)
        return tuple(sorted(official_judges)), tuple(sorted(hosted_submitters))

    def _summarize_hosted_official_matrix(
        *,
        registry: Mapping[str, Mapping[str, Any]],
        required_official_judges: Sequence[str],
        required_hosted_submitters: Sequence[str],
    ) -> Dict[str, Any]:
        submitter_runs = matrix_summary.get("submitter_runs", ())
        matrix_cells = matrix_summary.get("matrix_cells", ())
        declared_official_judges = {
            str(label) for label in matrix_summary.get("official_judge_labels", ())
        }
        submitter_labels_by_model: Dict[str, list[str]] = {}
        for run in submitter_runs:
            submitter_label = str(run.get("label", "")).strip()
            if not submitter_label:
                continue
            model_keys = []
            for key in ("model", "model_label", "submitter_model_label", "request_model"):
                model_key = str(run.get(key, "")).strip()
                if model_key and model_key not in model_keys:
                    model_keys.append(model_key)
            for model_key in model_keys:
                labels = submitter_labels_by_model.setdefault(model_key, [])
                if submitter_label not in labels:
                    labels.append(submitter_label)
        cell_status_lookup = {
            (str(cell.get("submitter_label", "")), str(cell.get("judge_label", ""))): str(
                cell.get("status", "missing")
            )
            for cell in matrix_cells
        }
        counts = {
            "expected_cells": 0,
            "completed_cells": 0,
            "blocked_cells": 0,
            "missing_cells": 0,
            "excluded_family_bias_cells": 0,
        }
        missing_submitter_models = []
        cell_details = []
        for submitter_model in required_hosted_submitters:
            submitter_entry = registry.get(submitter_model, {})
            submitter_bias = str(submitter_entry.get("family_bias_group", "")).strip()
            submitter_labels = tuple(sorted(submitter_labels_by_model.get(submitter_model, ())))
            if not submitter_labels:
                missing_submitter_models.append(submitter_model)
            for judge_label in required_official_judges:
                judge_entry = registry.get(judge_label, {})
                judge_bias = str(judge_entry.get("family_bias_group", "")).strip()
                if submitter_bias and judge_bias and submitter_bias == judge_bias:
                    status = "excluded_family_bias"
                    reason = f"same family_bias_group={submitter_bias}"
                    counts["excluded_family_bias_cells"] += 1
                else:
                    counts["expected_cells"] += 1
                    if not submitter_labels:
                        status = "missing"
                        reason = "no submitter run registered for required hosted submitter model"
                        counts["missing_cells"] += 1
                    else:
                        statuses = [
                            cell_status_lookup.get((submitter_label, judge_label), "missing")
                            for submitter_label in submitter_labels
                        ]
                        if "completed" in statuses:
                            status = "completed"
                            reason = ""
                            counts["completed_cells"] += 1
                        elif "blocked" in statuses:
                            status = "blocked"
                            reason = "all registered submitter runs are blocked for this judge"
                            counts["blocked_cells"] += 1
                        else:
                            status = "missing"
                            reason = "no completed judge artifact registered for this required cell"
                            counts["missing_cells"] += 1
                cell_details.append(
                    {
                        "submitter_model_label": submitter_model,
                        "submitter_labels": list(submitter_labels),
                        "judge_label": judge_label,
                        "status": status,
                        "reason": reason,
                    }
                )
        return {
            "required_official_judge_labels": list(required_official_judges),
            "required_hosted_submitter_models": list(required_hosted_submitters),
            "declared_official_judge_labels": sorted(declared_official_judges),
            "all_required_official_judges_declared": set(required_official_judges).issubset(
                declared_official_judges
            ),
            "missing_submitter_models": sorted(missing_submitter_models),
            "counts": counts,
            "cells": cell_details,
            "ready": (
                bool(required_official_judges)
                and bool(required_hosted_submitters)
                and set(required_official_judges).issubset(declared_official_judges)
                and counts["expected_cells"] > 0
                and counts["blocked_cells"] == 0
                and counts["missing_cells"] == 0
            ),
        }

    def _summarize_canary_coverage(
        expected_models: Sequence[str],
    ) -> Dict[str, Any]:
        model_aliases: Dict[str, str] = {}
        for label, entry in registry.items():
            for raw in (label, entry.get("model_label"), entry.get("request_model")):
                alias = str(raw or "").strip()
                if alias:
                    model_aliases[alias] = label

        def _canonical_model_label(raw: Any) -> Optional[str]:
            value = str(raw or "").strip()
            if not value:
                return None
            return model_aliases.get(value, value)

        expected = tuple(expected_models)
        requested = tuple(
            label
            for label in (
                _canonical_model_label(raw)
                for raw in (
                    canary_summary.get("production_models_requested")
                    or canary_summary.get("models_requested")
                    or ()
                )
            )
            if label
        )
        ok_label_set = {
            label
            for label in (
                _canonical_model_label(raw)
                for raw in canary_summary.get("production_models_ok", ())
            )
            if label
        }
        for row in canary_summary.get("model_summaries", ()):
            if str(row.get("status", "")) != "ok":
                continue
            for key in ("model", "model_label", "request_model"):
                label = _canonical_model_label(row.get(key))
                if label:
                    ok_label_set.add(label)
        ok_labels = tuple(sorted(ok_label_set))
        expected_set = set(expected)
        requested_set = set(requested)
        ok_set = set(ok_labels)
        missing_requested = sorted(expected_set - requested_set)
        missing_ok = sorted(expected_set - ok_set)
        return {
            "expected_models": list(expected),
            "requested_models": list(requested),
            "ok_models": list(sorted(ok_set)),
            "missing_requested_models": missing_requested,
            "missing_ok_models": missing_ok,
            "ready": (
                bool(expected)
                and not missing_requested
                and not missing_ok
                and not _safe_bool(canary_summary.get("any_public_exact_match", False))
                and not _safe_bool(canary_summary.get("any_control_exact_match", False))
            ),
        }

    agreement_metrics = dict(agreement_metrics or {})

    def _safe_metric_float(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(numeric):
            return 0.0
        return numeric

    def _safe_bool(value: Any, *, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return default
            if not math.isfinite(numeric):
                return default
            return numeric != 0.0
        text = str(value).strip().lower()
        if text in {"true", "1", "yes", "y"}:
            return True
        if text in {"false", "0", "no", "n", ""}:
            return False
        return default

    registry_path = _resolve_registry_path()
    registry = load_frontier_registry(registry_path)
    required_official_judges, required_hosted_submitters = _required_registry_targets(registry)
    hosted_official_matrix = _summarize_hosted_official_matrix(
        registry=registry,
        required_official_judges=required_official_judges,
        required_hosted_submitters=required_hosted_submitters,
    )
    expected_canary_models = default_canary_models(registry_path=registry_path)
    canary_coverage = _summarize_canary_coverage(expected_canary_models)
    submitter_tracks = tuple(
        str(track).strip()
        for track in matrix_summary.get("submitter_tracks_present", ())
        if str(track).strip()
    )
    if not submitter_tracks:
        submitter_tracks = tuple(
            sorted(
                {
                    str(run.get("submitter_track", "")).strip()
                    for run in matrix_summary.get("submitter_runs", ())
                    if str(run.get("submitter_track", "")).strip()
                }
            )
        )
    required_submitter_tracks = ("hosted_frontier", "open_weight")
    missing_required_submitter_tracks = tuple(
        sorted(set(required_submitter_tracks) - set(submitter_tracks))
    )
    track_summary = {
        "required_submitter_tracks": list(required_submitter_tracks),
        "submitter_tracks_present": list(submitter_tracks),
        "missing_required_submitter_tracks": list(missing_required_submitter_tracks),
        "hosted_frontier_policy": (
            "Hosted-frontier submitters define the official hosted matrix gate."
        ),
        "open_weight_policy": (
            "Open-weight/VLLM submitters are tracked separately and do not satisfy "
            "hosted-frontier submitter cells."
        ),
    }
    pre_kappa = _safe_metric_float(agreement_metrics.get("pre_adjudication_kappa", 0.0))
    post_kappa = _safe_metric_float(agreement_metrics.get("post_adjudication_kappa", 0.0))
    jury_icc = _safe_metric_float(agreement_metrics.get("jury_vs_adjudicator_icc", 0.0))
    gates = {
        "validation_slice_ready": _safe_bool(validation_summary.get("ready", False)),
        "study_class_stratification_ready": _safe_bool(
            validation_summary.get("study_class_stratification_ready", False)
        ),
        "official_judges_present": hosted_official_matrix["all_required_official_judges_declared"],
        "official_hosted_matrix_complete": hosted_official_matrix["ready"],
        "hosted_and_open_weight_submitters_present": not missing_required_submitter_tracks,
        "full_canary_report_ready": canary_coverage["ready"],
        "pre_adjudication_kappa_ok": pre_kappa >= PRE_ADJUDICATION_KAPPA_THRESHOLD,
        "post_adjudication_kappa_ok": post_kappa >= POST_ADJUDICATION_KAPPA_THRESHOLD,
        "jury_vs_adjudicator_icc_ok": jury_icc >= JURY_VS_ADJUDICATOR_ICC_THRESHOLD,
    }
    return {
        "leaderboard_gate_passed": all(gates.values()),
        "gates": gates,
        "agreement_metrics": {
            "pre_adjudication_kappa": pre_kappa,
            "post_adjudication_kappa": post_kappa,
            "jury_vs_adjudicator_icc": jury_icc,
        },
        "registry_path": str(registry_path),
        "track_summary": track_summary,
        "hosted_official_matrix": hosted_official_matrix,
        "canary_coverage": canary_coverage,
    }
