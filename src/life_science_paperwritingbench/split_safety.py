from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

from .models import BenchmarkUnit, SplitSafetyViolation
from .policy import SplitSafetyPolicy, SplitSafetyViolationType


def validate_split_safety(
    units: Sequence[BenchmarkUnit],
    policy: Optional[SplitSafetyPolicy] = None,
) -> List[SplitSafetyViolation]:
    policy = policy or SplitSafetyPolicy()
    lineage_index: Dict[Tuple[str, str], Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

    for unit in units:
        if not unit.split:
            continue
        for lineage_type, tokens in unit.lineage.tokens().items():
            if lineage_type not in policy.lineage_types:
                continue
            for token in tokens:
                lineage_index[(lineage_type, token)][unit.split].append(unit.benchmark_unit_id)

    violations: List[SplitSafetyViolation] = []
    for (lineage_type, lineage_value), split_map in lineage_index.items():
        total_count = sum(len(ids) for ids in split_map.values())
        if len(split_map) > 1:
            unit_ids: List[str] = []
            for ids in split_map.values():
                unit_ids.extend(ids)
            violations.append(
                SplitSafetyViolation(
                    violation_type=SplitSafetyViolationType.CROSS_SPLIT_LEAKAGE,
                    lineage_type=lineage_type,
                    lineage_value=lineage_value,
                    conflicting_splits=tuple(sorted(split_map.keys())),
                    benchmark_unit_ids=tuple(sorted(unit_ids)),
                    observed_count=total_count,
                )
            )
        if total_count > policy.max_units_per_lineage:
            unit_ids = []
            for ids in split_map.values():
                unit_ids.extend(ids)
            violations.append(
                SplitSafetyViolation(
                    violation_type=SplitSafetyViolationType.LINEAGE_DOMINANCE,
                    lineage_type=lineage_type,
                    lineage_value=lineage_value,
                    conflicting_splits=tuple(sorted(split_map.keys())),
                    benchmark_unit_ids=tuple(sorted(unit_ids)),
                    observed_count=total_count,
                    max_allowed=policy.max_units_per_lineage,
                )
            )

    return sorted(
        violations,
        key=lambda item: (item.violation_type.value, item.lineage_type, item.lineage_value),
    )


def lineage_dominance_counts(units: Sequence[BenchmarkUnit], lineage_type: str) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for unit in units:
        for current_type, tokens in unit.lineage.tokens().items():
            if current_type != lineage_type:
                continue
            for token in tokens:
                counts[token] += 1
    return dict(sorted(counts.items()))
