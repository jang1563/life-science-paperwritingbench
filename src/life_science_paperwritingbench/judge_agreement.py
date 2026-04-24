from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .judge import DEFAULT_JUDGE_RUBRIC_AXES, _numeric_judge_rubric_score
from .judgeflow import merge_judge_review_forms
from .models import JudgeAdjudicationRecord, JudgeAgreementReport, JudgeReviewForm, JudgeValidationUnit


def _required_axes_for_unit(judge_unit: JudgeValidationUnit) -> Tuple[str, ...]:
    axes = tuple(str(axis).strip() for axis in judge_unit.rubric_labels if str(axis).strip())
    return axes or tuple(DEFAULT_JUDGE_RUBRIC_AXES)


def _numeric_rubric_value(value: object) -> Optional[float]:
    return _numeric_judge_rubric_score(value)


def _numeric_rubric_labels(labels: Mapping[str, object]) -> Dict[str, float]:
    numeric: Dict[str, float] = {}
    for axis, value in labels.items():
        normalized = str(axis).strip()
        if not normalized:
            continue
        numeric_value = _numeric_rubric_value(value)
        if numeric_value is None:
            continue
        numeric[normalized] = numeric_value
    return numeric


def _missing_numeric_axes(
    labels: Mapping[str, object],
    required_axes: Sequence[str],
) -> Tuple[str, ...]:
    numeric = _numeric_rubric_labels(labels)
    return tuple(axis for axis in required_axes if axis not in numeric)


def _mean_axis_score(
    labels: Mapping[str, object],
    required_axes: Optional[Sequence[str]] = None,
) -> Optional[float]:
    numeric_labels = _numeric_rubric_labels(labels)
    if required_axes is not None:
        axes = tuple(required_axes)
        if _missing_numeric_axes(labels, axes):
            return None
        numeric = tuple(numeric_labels[axis] for axis in axes)
    else:
        numeric = tuple(numeric_labels.values())
    if not numeric:
        return None
    return sum(numeric) / float(len(numeric))


def _cohen_kappa_binary(pairs: Sequence[Tuple[bool, bool]]) -> Optional[float]:
    if not pairs:
        return None
    total = float(len(pairs))
    agreement = sum(1 for left, right in pairs if left == right) / total
    left_true = sum(1 for left, _ in pairs if left) / total
    right_true = sum(1 for _, right in pairs if right) / total
    left_false = 1.0 - left_true
    right_false = 1.0 - right_true
    expected = (left_true * right_true) + (left_false * right_false)
    if expected >= 1.0:
        return 1.0 if agreement >= 1.0 else 0.0
    return (agreement - expected) / (1.0 - expected)


def _icc_2_1(score_pairs: Sequence[Tuple[float, float]]) -> Optional[float]:
    if len(score_pairs) < 2:
        return None
    matrix = [(float(left), float(right)) for left, right in score_pairs]
    n = len(matrix)
    k = 2
    grand_mean = sum(left + right for left, right in matrix) / float(n * k)
    row_means = [sum(row) / float(k) for row in matrix]
    col_means = [
        sum(row[column] for row in matrix) / float(n)
        for column in range(k)
    ]
    ss_rows = float(k) * sum((row_mean - grand_mean) ** 2 for row_mean in row_means)
    ss_cols = float(n) * sum((col_mean - grand_mean) ** 2 for col_mean in col_means)
    ss_error = 0.0
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            ss_error += (value - row_means[row_index] - col_means[column_index] + grand_mean) ** 2
    ms_rows = ss_rows / float(n - 1)
    ms_cols = ss_cols / float(k - 1)
    ms_error = ss_error / float((n - 1) * (k - 1))
    denominator = ms_rows + ((k - 1) * ms_error) + ((float(k) * (ms_cols - ms_error)) / float(n))
    if denominator == 0.0:
        return 1.0 if ms_rows == ms_error == ms_cols == 0.0 else 0.0
    return (ms_rows - ms_error) / denominator


def _ordinal_distance(
    left: float,
    right: float,
    *,
    ranks: Mapping[float, int],
    max_rank: int,
) -> float:
    if max_rank <= 0:
        return 0.0
    return ((ranks[left] - ranks[right]) / float(max_rank)) ** 2


def _krippendorff_alpha_ordinal(items: Mapping[str, Sequence[float]]) -> Tuple[Optional[float], int]:
    category_values = sorted(
        {
            float(value)
            for ratings in items.values()
            for value in ratings
        }
    )
    comparable_items = sum(1 for ratings in items.values() if len(tuple(ratings)) >= 2)
    if comparable_items == 0:
        return None, 0
    if len(category_values) == 1:
        return 1.0, comparable_items

    ranks = {value: index for index, value in enumerate(category_values)}
    max_rank = max(ranks.values())
    coincidence: Dict[Tuple[float, float], float] = Counter()
    total_value_count = 0

    for ratings in items.values():
        rating_values = tuple(float(value) for value in ratings)
        if len(rating_values) < 2:
            continue
        total_value_count += len(rating_values)
        counts = Counter(rating_values)
        denominator = float(len(rating_values) - 1)
        for left_value, left_count in counts.items():
            coincidence[(left_value, left_value)] += (
                float(left_count) * float(left_count - 1)
            ) / denominator
            for right_value, right_count in counts.items():
                if left_value == right_value:
                    continue
                coincidence[(left_value, right_value)] += (
                    float(left_count) * float(right_count)
                ) / denominator

    if total_value_count <= 1:
        return None, comparable_items

    marginals: Counter[float] = Counter()
    for (left_value, right_value), count in coincidence.items():
        marginals[left_value] += count
        if left_value != right_value:
            marginals[right_value] += 0.0

    observed = 0.0
    for (left_value, right_value), count in coincidence.items():
        observed += count * _ordinal_distance(
            left_value,
            right_value,
            ranks=ranks,
            max_rank=max_rank,
        )
    observed /= float(total_value_count - 1)

    expected = 0.0
    for left_value, left_count in marginals.items():
        for right_value, right_count in marginals.items():
            expected += (
                float(left_count)
                * float(right_count)
                * _ordinal_distance(
                    left_value,
                    right_value,
                    ranks=ranks,
                    max_rank=max_rank,
                )
            )
    expected /= float(total_value_count * (total_value_count - 1))
    if expected == 0.0:
        return (1.0 if observed == 0.0 else 0.0), comparable_items
    return 1.0 - (observed / expected), comparable_items


def _sorted_reviewer_ids(forms: Sequence[JudgeReviewForm]) -> Tuple[str, ...]:
    return tuple(sorted({form.reviewer_id for form in forms}))


def _axis_labels(
    judge_units: Sequence[JudgeValidationUnit],
    forms: Sequence[JudgeReviewForm],
    adjudications: Sequence[JudgeAdjudicationRecord],
) -> Tuple[str, ...]:
    labels = set()
    for unit in judge_units:
        labels.update(str(axis) for axis in unit.rubric_labels)
    for form in forms:
        labels.update(str(axis) for axis in form.rubric_labels)
    for record in adjudications:
        labels.update(str(axis) for axis in record.final_rubric_labels)
    return tuple(sorted(label for label in labels if label.strip()))


def _reviewer_mean_scores_by_unit(
    forms: Sequence[JudgeReviewForm],
    required_axes_by_unit: Mapping[str, Sequence[str]],
) -> Dict[str, Dict[str, float]]:
    merged_forms = merge_judge_review_forms(forms)
    by_unit: Dict[str, Dict[str, float]] = {}
    for form in merged_forms:
        if not form.completed:
            continue
        mean_score = _mean_axis_score(
            form.rubric_labels,
            required_axes=required_axes_by_unit.get(form.validation_unit_id),
        )
        if mean_score is None:
            continue
        by_unit.setdefault(form.validation_unit_id, {})[form.reviewer_id] = mean_score
    return by_unit


def _adjudicator_mean_scores_by_unit(
    adjudications: Sequence[JudgeAdjudicationRecord],
    required_axes_by_unit: Mapping[str, Sequence[str]],
) -> Dict[str, float]:
    by_unit: Dict[str, float] = {}
    for record in adjudications:
        if not record.finalized:
            continue
        mean_score = _mean_axis_score(
            record.final_rubric_labels,
            required_axes=required_axes_by_unit.get(record.validation_unit_id),
        )
        if mean_score is None:
            continue
        by_unit[record.validation_unit_id] = mean_score
    return by_unit


def _ordinal_items_from_forms(
    forms: Iterable[JudgeReviewForm],
    required_axes_by_unit: Mapping[str, Sequence[str]],
) -> Dict[str, Tuple[float, ...]]:
    items: Dict[str, List[float]] = {}
    for form in forms:
        if not form.completed:
            continue
        numeric = _numeric_rubric_labels(form.rubric_labels)
        required_axes = required_axes_by_unit.get(form.validation_unit_id, tuple(numeric))
        if _missing_numeric_axes(form.rubric_labels, required_axes):
            continue
        for axis in required_axes:
            value = numeric[axis]
            items.setdefault(f"{form.validation_unit_id}:{axis}", []).append(value)
    return {
        item_id: tuple(values)
        for item_id, values in items.items()
    }


def _ordinal_items_with_adjudication(
    forms_by_unit: Mapping[str, Sequence[JudgeReviewForm]],
    adjudications: Mapping[str, JudgeAdjudicationRecord],
    required_axes_by_unit: Mapping[str, Sequence[str]],
) -> Dict[str, Tuple[float, ...]]:
    items: Dict[str, List[float]] = {}
    for validation_unit_id, record in adjudications.items():
        numeric_final = _numeric_rubric_labels(record.final_rubric_labels)
        required_axes = required_axes_by_unit.get(validation_unit_id, tuple(numeric_final))
        if not numeric_final or _missing_numeric_axes(record.final_rubric_labels, required_axes):
            continue
        reviewer_forms = [form for form in forms_by_unit.get(validation_unit_id, ()) if form.completed]
        for axis in required_axes:
            final_value = numeric_final[axis]
            ratings = []
            for form in reviewer_forms:
                numeric_form = _numeric_rubric_labels(form.rubric_labels)
                if _missing_numeric_axes(form.rubric_labels, required_axes):
                    continue
                ratings.append(numeric_form[axis])
            ratings.append(final_value)
            items[f"{validation_unit_id}:{axis}"] = ratings
    return {
        item_id: tuple(values)
        for item_id, values in items.items()
    }


def compute_judge_agreement(
    judge_units: Sequence[JudgeValidationUnit],
    forms: Sequence[JudgeReviewForm],
    adjudications: Sequence[JudgeAdjudicationRecord],
    *,
    pass_threshold: float = 2.0,
    minimum_reviewers: int = 2,
) -> JudgeAgreementReport:
    expected_validation_unit_ids = {unit.validation_unit_id for unit in judge_units}
    required_axes_by_unit = {
        unit.validation_unit_id: _required_axes_for_unit(unit)
        for unit in judge_units
    }
    merged_forms = merge_judge_review_forms(forms)
    unexpected_form_validation_unit_ids = tuple(
        sorted(
            {
                form.validation_unit_id
                for form in merged_forms
                if form.validation_unit_id not in expected_validation_unit_ids
            }
        )
    )
    filtered_forms = tuple(
        form
        for form in merged_forms
        if form.validation_unit_id in expected_validation_unit_ids
    )
    reviewer_ids = _sorted_reviewer_ids(filtered_forms)
    unexpected_adjudication_validation_unit_ids = tuple(
        sorted(
            {
                record.validation_unit_id
                for record in adjudications
                if record.validation_unit_id not in expected_validation_unit_ids
            }
        )
    )
    adjudication_map = {
        record.validation_unit_id: record
        for record in adjudications
        if record.finalized
        and record.validation_unit_id in expected_validation_unit_ids
    }
    completed_forms_by_unit: Dict[str, List[JudgeReviewForm]] = {}
    for form in filtered_forms:
        if form.completed:
            completed_forms_by_unit.setdefault(form.validation_unit_id, []).append(form)

    reviewer_scores_by_unit = _reviewer_mean_scores_by_unit(
        filtered_forms,
        required_axes_by_unit,
    )
    adjudicator_scores_by_unit = _adjudicator_mean_scores_by_unit(
        tuple(adjudication_map.values()),
        required_axes_by_unit,
    )

    reviewer_pairwise_kappa: Dict[str, float] = {}
    reviewer_pairwise_icc: Dict[str, float] = {}
    pre_kappa_weighted_total = 0.0
    pre_kappa_weight = 0
    pre_icc_weighted_total = 0.0
    pre_icc_weight = 0
    comparable_pre_units = set()

    for reviewer_left, reviewer_right in combinations(reviewer_ids, 2):
        binary_pairs = []
        score_pairs = []
        for validation_unit_id, reviewer_scores in reviewer_scores_by_unit.items():
            if reviewer_left not in reviewer_scores or reviewer_right not in reviewer_scores:
                continue
            comparable_pre_units.add(validation_unit_id)
            left_score = reviewer_scores[reviewer_left]
            right_score = reviewer_scores[reviewer_right]
            binary_pairs.append((left_score >= pass_threshold, right_score >= pass_threshold))
            score_pairs.append((left_score, right_score))
        pair_key = f"{reviewer_left}__{reviewer_right}"
        if binary_pairs:
            pair_kappa = _cohen_kappa_binary(binary_pairs)
            if pair_kappa is not None:
                reviewer_pairwise_kappa[pair_key] = pair_kappa
                pre_kappa_weighted_total += pair_kappa * len(binary_pairs)
                pre_kappa_weight += len(binary_pairs)
        pair_icc = _icc_2_1(score_pairs)
        if pair_icc is not None:
            reviewer_pairwise_icc[pair_key] = pair_icc
            pre_icc_weighted_total += pair_icc * len(score_pairs)
            pre_icc_weight += len(score_pairs)

    pre_adjudication_kappa = (
        pre_kappa_weighted_total / float(pre_kappa_weight)
        if pre_kappa_weight
        else 0.0
    )
    pre_adjudication_icc = (
        pre_icc_weighted_total / float(pre_icc_weight)
        if pre_icc_weight
        else 0.0
    )

    post_binary_pairs = []
    post_score_pairs = []
    reviewer_vs_adjudicator_pairs: Dict[str, List[Tuple[float, float]]] = {}
    comparable_post_units = set()
    for validation_unit_id, adjudicator_score in adjudicator_scores_by_unit.items():
        reviewer_scores = reviewer_scores_by_unit.get(validation_unit_id, {})
        if len(reviewer_scores) < minimum_reviewers:
            continue
        jury_mean = sum(reviewer_scores.values()) / float(len(reviewer_scores))
        post_binary_pairs.append((jury_mean >= pass_threshold, adjudicator_score >= pass_threshold))
        post_score_pairs.append((jury_mean, adjudicator_score))
        comparable_post_units.add(validation_unit_id)
        for reviewer_id, reviewer_score in reviewer_scores.items():
            reviewer_vs_adjudicator_pairs.setdefault(reviewer_id, []).append(
                (reviewer_score, adjudicator_score)
            )

    reviewer_vs_adjudicator_icc = {
        reviewer_id: icc_value
        for reviewer_id, icc_value in (
            (reviewer_id, _icc_2_1(score_pairs))
            for reviewer_id, score_pairs in reviewer_vs_adjudicator_pairs.items()
        )
        if icc_value is not None
    }

    post_adjudication_kappa = _cohen_kappa_binary(post_binary_pairs) or 0.0
    jury_vs_adjudicator_icc = _icc_2_1(post_score_pairs) or 0.0

    pre_alpha, comparable_ordinal_items_pre = _krippendorff_alpha_ordinal(
        _ordinal_items_from_forms(filtered_forms, required_axes_by_unit)
    )
    post_alpha, comparable_ordinal_items_post = _krippendorff_alpha_ordinal(
        _ordinal_items_with_adjudication(
            completed_forms_by_unit,
            adjudication_map,
            required_axes_by_unit,
        )
    )

    issues = list(
        validate_judge_agreement_thresholds(
            pre_adjudication_kappa=pre_adjudication_kappa,
            post_adjudication_kappa=post_adjudication_kappa,
            jury_vs_adjudicator_icc=jury_vs_adjudicator_icc,
            comparable_pre_units=len(comparable_pre_units),
            comparable_post_units=len(comparable_post_units),
            comparable_ordinal_items_pre=comparable_ordinal_items_pre,
            comparable_ordinal_items_post=comparable_ordinal_items_post,
        )
    )
    if unexpected_form_validation_unit_ids:
        issues.append(
            "ignored judge review forms for unknown validation units: "
            + ", ".join(unexpected_form_validation_unit_ids)
        )
    if unexpected_adjudication_validation_unit_ids:
        issues.append(
            "ignored judge adjudications for unknown validation units: "
            + ", ".join(unexpected_adjudication_validation_unit_ids)
        )
    incomplete_forms = []
    for form in filtered_forms:
        if not form.completed:
            continue
        missing_axes = _missing_numeric_axes(
            form.rubric_labels,
            required_axes_by_unit.get(form.validation_unit_id, ()),
        )
        if missing_axes:
            incomplete_forms.append(
                f"{form.validation_unit_id}/{form.reviewer_id}:"
                + ",".join(missing_axes)
            )
    if incomplete_forms:
        issues.append(
            "ignored completed judge review forms with incomplete rubric labels: "
            + "; ".join(sorted(incomplete_forms))
        )

    return JudgeAgreementReport(
        total_judge_units=len(judge_units),
        merged_review_forms=len(filtered_forms),
        finalized_adjudications=len(adjudication_map),
        reviewer_ids=reviewer_ids,
        axis_labels=_axis_labels(judge_units, filtered_forms, tuple(adjudication_map.values())),
        pass_threshold=float(pass_threshold),
        minimum_reviewers=int(minimum_reviewers),
        unexpected_form_validation_unit_ids=unexpected_form_validation_unit_ids,
        unexpected_adjudication_validation_unit_ids=unexpected_adjudication_validation_unit_ids,
        comparable_pre_adjudication_units=len(comparable_pre_units),
        comparable_post_adjudication_units=len(comparable_post_units),
        comparable_pre_adjudication_pairs=pre_kappa_weight,
        comparable_ordinal_items_pre=comparable_ordinal_items_pre,
        comparable_ordinal_items_post=comparable_ordinal_items_post,
        pre_adjudication_kappa=pre_adjudication_kappa,
        post_adjudication_kappa=post_adjudication_kappa,
        pre_adjudication_ordinal_alpha=pre_alpha if pre_alpha is not None else 0.0,
        post_adjudication_ordinal_alpha=post_alpha if post_alpha is not None else 0.0,
        pre_adjudication_icc=pre_adjudication_icc,
        post_adjudication_icc=jury_vs_adjudicator_icc,
        jury_vs_adjudicator_icc=jury_vs_adjudicator_icc,
        reviewer_pairwise_kappa=reviewer_pairwise_kappa,
        reviewer_pairwise_icc=reviewer_pairwise_icc,
        reviewer_vs_adjudicator_icc=reviewer_vs_adjudicator_icc,
        issues=tuple(issues),
        ok=not issues,
    )


def validate_judge_agreement_thresholds(
    *,
    pre_adjudication_kappa: float,
    post_adjudication_kappa: float,
    jury_vs_adjudicator_icc: float,
    comparable_pre_units: int,
    comparable_post_units: int,
    comparable_ordinal_items_pre: int,
    comparable_ordinal_items_post: int,
) -> Tuple[str, ...]:
    from .publication import (
        JURY_VS_ADJUDICATOR_ICC_THRESHOLD,
        POST_ADJUDICATION_KAPPA_THRESHOLD,
        PRE_ADJUDICATION_KAPPA_THRESHOLD,
    )

    issues = []
    if comparable_pre_units == 0:
        issues.append("no overlapping completed reviewer judgments for pre-adjudication agreement")
    if comparable_post_units == 0:
        issues.append("no finalized adjudications with sufficient reviewer coverage for post-adjudication agreement")
    if comparable_ordinal_items_pre == 0:
        issues.append("no comparable ordinal rubric items for pre-adjudication alpha")
    if comparable_ordinal_items_post == 0:
        issues.append("no comparable ordinal rubric items for post-adjudication alpha")
    if comparable_pre_units and pre_adjudication_kappa < PRE_ADJUDICATION_KAPPA_THRESHOLD:
        issues.append(
            f"pre_adjudication_kappa {pre_adjudication_kappa:.3f} is below threshold "
            f"{PRE_ADJUDICATION_KAPPA_THRESHOLD:.3f}"
        )
    if comparable_post_units and post_adjudication_kappa < POST_ADJUDICATION_KAPPA_THRESHOLD:
        issues.append(
            f"post_adjudication_kappa {post_adjudication_kappa:.3f} is below threshold "
            f"{POST_ADJUDICATION_KAPPA_THRESHOLD:.3f}"
        )
    if comparable_post_units and jury_vs_adjudicator_icc < JURY_VS_ADJUDICATOR_ICC_THRESHOLD:
        issues.append(
            f"jury_vs_adjudicator_icc {jury_vs_adjudicator_icc:.3f} is below threshold "
            f"{JURY_VS_ADJUDICATOR_ICC_THRESHOLD:.3f}"
        )
    return tuple(issues)
