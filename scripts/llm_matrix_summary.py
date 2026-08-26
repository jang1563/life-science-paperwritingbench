#!/usr/bin/env python3
"""Aggregate submitter and judge calibration summaries into a matrix report.

This script is intentionally file-contract based: it reads the existing
`summary.json` artifacts emitted by `llm_agentic_eval.py` and
`llm_judge_eval.py`, then writes a reproducible matrix summary without
re-running any model calls.

Example:

    PYTHONPATH=src python3 scripts/llm_matrix_summary.py \
        --submitter-run deepseek-chat-agentic-rerun5=calibration/llm_agentic_public_slice_v1_rerun5 \
        --submitter-run gpt-4o-mini-agentic-v1=calibration/llm_agentic_public_slice_gpt4omini_v1 \
        --judge-label claude-sonnet-4-6 \
        --judge-label gpt-5.4-mini \
        --judge-label gpt-5-mini \
        --judge-cell deepseek-chat-agentic-rerun5:claude-sonnet-4-6=calibration/llm_agentic_public_slice_v1_rerun5_judged_v3 \
        --judge-cell deepseek-chat-agentic-rerun5:gpt-5.4-mini=calibration/llm_agentic_public_slice_v1_rerun5_judged_v3_gpt54mini \
        --judge-cell deepseek-chat-agentic-rerun5:gpt-5-mini=calibration/llm_agentic_public_slice_v1_rerun5_judged_v3_gpt5mini \
        --judge-cell gpt-4o-mini-agentic-v1:gpt-5.4-mini=calibration/llm_agentic_public_slice_gpt4omini_v1_judged_v3_gpt54mini \
        --judge-cell gpt-4o-mini-agentic-v1:gpt-5-mini=calibration/llm_agentic_public_slice_gpt4omini_v1_judged_v3_gpt5mini \
        --blocked-cell gpt-4o-mini-agentic-v1:claude-sonnet-4-6=Anthropic API key currently invalid in local ~/.api_keys on 2026-04-21 \
        --output-dir calibration/llm_public_slice_matrix_v1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


AXIS_ORDER: Tuple[str, ...] = (
    "writing_structure_compliance",
    "evidence_grounding",
    "factual_fidelity",
    "traceability",
    "quantitative_specificity",
    "hallucination_absence",
)


def _round(value: float) -> float:
    return round(value, 3)


def _mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / float(len(values))


def _pct(count: int, total: int) -> Optional[float]:
    if total <= 0:
        return None
    return (100.0 * float(count)) / float(total)


def _format_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}%"


def _format_float(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def _split_once(value: str, delimiter: str, kind: str) -> Tuple[str, str]:
    if delimiter not in value:
        raise ValueError(f"Expected {kind} formatted as '<left>{delimiter}<right>', got: {value}")
    left, right = value.split(delimiter, 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        raise ValueError(f"Expected non-empty {kind}, got: {value}")
    return left, right


def parse_labeled_path_arg(value: str) -> Tuple[str, Path]:
    label, raw_path = _split_once(value, "=", "labeled path")
    return label, Path(raw_path)


def parse_judge_cell_arg(value: str) -> Tuple[str, str, Path]:
    left, raw_path = _split_once(value, "=", "judge cell")
    submitter_label, judge_label = _split_once(left, ":", "judge cell label")
    return submitter_label, judge_label, Path(raw_path)


def parse_blocked_cell_arg(value: str) -> Tuple[str, str, str]:
    left, reason = _split_once(value, "=", "blocked cell")
    submitter_label, judge_label = _split_once(left, ":", "blocked cell label")
    return submitter_label, judge_label, reason


def _resolve_summary_path(path: Path) -> Path:
    if path.is_dir():
        return path / "summary.json"
    return path


def _load_json(path: Path) -> Dict[str, Any]:
    summary_path = _resolve_summary_path(path)
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary.json at {summary_path}")
    return json.loads(summary_path.read_text(encoding="utf-8"))


def load_submitter_run(label: str, path: Path) -> Dict[str, Any]:
    summary = _load_json(path)
    num_tasks = int(summary["num_tasks"])
    final_pass_count = int(summary["final_pass_count"])
    final_citation_score = float(summary["final_mean_citation_specificity_score"])
    raw_selection_overrides = summary.get("selection_overrides", 0)
    if isinstance(raw_selection_overrides, list):
        selection_overrides = len(raw_selection_overrides)
    else:
        selection_overrides = int(raw_selection_overrides)
    return {
        "label": label,
        "run_dir": str(path),
        "summary_path": str(_resolve_summary_path(path)),
        "model": summary.get("model"),
        "request_model": summary.get("request_model"),
        "num_tasks": num_tasks,
        "final_pass_count": final_pass_count,
        "final_pass_rate_pct": _round(_pct(final_pass_count, num_tasks) or 0.0),
        "draft_pass_count": int(summary.get("draft_pass_count", 0)),
        "reviser_pass_count": int(summary.get("reviser_pass_count", 0)),
        "final_mean_citation_specificity_score": _round(final_citation_score),
        "selection_policy": summary.get("selection_policy"),
        "selection_overrides": selection_overrides,
    }


def load_judge_cell(submitter_label: str, judge_label: str, path: Path) -> Dict[str, Any]:
    summary = _load_json(path)
    total = int(summary["total_submissions_judged"])
    overall_pass = int(summary["judge_overall_pass"])
    threshold_pass = int(summary["passes_threshold_rule"])
    per_axis_mean = {
        axis: _round(float(value))
        for axis, value in summary.get("per_axis_mean", {}).items()
    }
    return {
        "submitter_label": submitter_label,
        "judge_label": judge_label,
        "run_dir": str(path),
        "summary_path": str(_resolve_summary_path(path)),
        "judge": summary.get("judge"),
        "judge_model": summary.get("judge_model"),
        "rubric_version": summary.get("rubric_version"),
        "total_submissions_judged": total,
        "judge_overall_pass": overall_pass,
        "judge_overall_pass_rate_pct": _round(_pct(overall_pass, total) or 0.0),
        "passes_threshold_rule": threshold_pass,
        "threshold_pass_rate_pct": _round(_pct(threshold_pass, total) or 0.0),
        "mean_axis_score": _round(float(summary["mean_axis_score"])),
        "all_axes_above_threshold": int(summary.get("all_axes_above_threshold", 0)),
        "total_grounding_issues": int(summary.get("total_grounding_issues", 0)),
        "parse_failures": int(summary.get("parse_failures", 0)),
        "per_axis_mean": per_axis_mean,
    }


def build_matrix_report(
    submitter_runs: Mapping[str, Dict[str, Any]],
    judge_labels: Sequence[str],
    judge_cells: Sequence[Dict[str, Any]],
    blocked_cells: Mapping[Tuple[str, str], str],
) -> Dict[str, Any]:
    judge_labels = list(judge_labels)
    if len(set(judge_labels)) != len(judge_labels):
        raise ValueError("Duplicate --judge-label values are not allowed")
    if not submitter_runs:
        raise ValueError("At least one --submitter-run is required")
    if not judge_labels:
        raise ValueError("At least one --judge-label is required")

    matrix_lookup: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for cell in judge_cells:
        key = (cell["submitter_label"], cell["judge_label"])
        if key in matrix_lookup:
            raise ValueError(f"Duplicate judge cell provided for {key[0]} x {key[1]}")
        if cell["submitter_label"] not in submitter_runs:
            raise ValueError(f"Unknown submitter label in judge cell: {cell['submitter_label']}")
        if cell["judge_label"] not in judge_labels:
            raise ValueError(f"Unknown judge label in judge cell: {cell['judge_label']}")
        matrix_lookup[key] = cell

    for submitter_label, judge_label in blocked_cells:
        if submitter_label not in submitter_runs:
            raise ValueError(f"Unknown submitter label in blocked cell: {submitter_label}")
        if judge_label not in judge_labels:
            raise ValueError(f"Unknown judge label in blocked cell: {judge_label}")
        if (submitter_label, judge_label) in matrix_lookup:
            raise ValueError(
                f"Cell {submitter_label} x {judge_label} cannot be both completed and blocked"
            )

    matrix_rows: List[Dict[str, Any]] = []
    completed_cells = 0
    blocked_count = 0
    missing_count = 0
    for submitter_label in submitter_runs:
        for judge_label in judge_labels:
            key = (submitter_label, judge_label)
            if key in matrix_lookup:
                row = dict(matrix_lookup[key])
                row["status"] = "completed"
                completed_cells += 1
            elif key in blocked_cells:
                row = {
                    "submitter_label": submitter_label,
                    "judge_label": judge_label,
                    "status": "blocked",
                    "reason": blocked_cells[key],
                }
                blocked_count += 1
            else:
                row = {
                    "submitter_label": submitter_label,
                    "judge_label": judge_label,
                    "status": "missing",
                    "reason": "no summary artifact registered",
                }
                missing_count += 1
            matrix_rows.append(row)

    aggregated_submitters: List[Dict[str, Any]] = []
    for submitter_label, submitter in submitter_runs.items():
        completed = [
            row
            for row in matrix_rows
            if row["submitter_label"] == submitter_label and row["status"] == "completed"
        ]
        axis_means: Dict[str, float] = {}
        for axis in AXIS_ORDER:
            values = [cell["per_axis_mean"].get(axis) for cell in completed if axis in cell["per_axis_mean"]]
            if values:
                axis_means[axis] = _round(_mean([float(value) for value in values]) or 0.0)
        mean_judge_overall_pass_rate = _mean(
            [float(cell["judge_overall_pass_rate_pct"]) for cell in completed]
        )
        mean_threshold_pass_rate = _mean(
            [float(cell["threshold_pass_rate_pct"]) for cell in completed]
        )
        mean_axis_score = _mean([float(cell["mean_axis_score"]) for cell in completed])
        mean_grounding_issues = _mean(
            [float(cell["total_grounding_issues"]) for cell in completed]
        )
        aggregated_submitters.append(
            {
                "submitter_label": submitter_label,
                "model": submitter.get("model"),
                "request_model": submitter.get("request_model"),
                "num_completed_judges": len(completed),
                "completed_judges": [cell["judge_label"] for cell in completed],
                "final_pass_count": submitter["final_pass_count"],
                "final_pass_rate_pct": submitter["final_pass_rate_pct"],
                "final_mean_citation_specificity_score": submitter[
                    "final_mean_citation_specificity_score"
                ],
                "mean_judge_overall_pass_rate_pct": _round(mean_judge_overall_pass_rate)
                if mean_judge_overall_pass_rate is not None
                else None,
                "mean_threshold_pass_rate_pct": _round(mean_threshold_pass_rate)
                if mean_threshold_pass_rate is not None
                else None,
                "mean_axis_score": _round(mean_axis_score) if mean_axis_score is not None else None,
                "mean_grounding_issues": _round(mean_grounding_issues)
                if mean_grounding_issues is not None
                else None,
                "parse_failures_total": sum(cell["parse_failures"] for cell in completed),
                "per_axis_mean": axis_means,
            }
        )

    aggregated_submitters.sort(
        key=lambda row: (
            row["mean_judge_overall_pass_rate_pct"] is None,
            -(row["mean_judge_overall_pass_rate_pct"] or 0.0),
            row["submitter_label"],
        )
    )

    judge_spread: List[Dict[str, Any]] = []
    for judge_label in judge_labels:
        completed = [
            row for row in matrix_rows if row["judge_label"] == judge_label and row["status"] == "completed"
        ]
        ordered = sorted(
            completed,
            key=lambda row: (-row["judge_overall_pass_rate_pct"], row["submitter_label"]),
        )
        if len(ordered) >= 2:
            best = ordered[0]
            worst = ordered[-1]
            spread_pp = _round(best["judge_overall_pass_rate_pct"] - worst["judge_overall_pass_rate_pct"])
        else:
            best = ordered[0] if ordered else None
            worst = ordered[-1] if ordered else None
            spread_pp = None
        judge_spread.append(
            {
                "judge_label": judge_label,
                "completed_cells": len(completed),
                "best_submitter_label": best["submitter_label"] if best else None,
                "best_judge_overall_pass_rate_pct": best["judge_overall_pass_rate_pct"] if best else None,
                "worst_submitter_label": worst["submitter_label"] if worst else None,
                "worst_judge_overall_pass_rate_pct": worst["judge_overall_pass_rate_pct"] if worst else None,
                "spread_pp": spread_pp,
            }
        )

    comparable_submitters = [row for row in aggregated_submitters if row["num_completed_judges"] > 0]
    common_judges: List[str] = []
    if comparable_submitters:
        common_judge_set = set(comparable_submitters[0]["completed_judges"])
        for row in comparable_submitters[1:]:
            common_judge_set &= set(row["completed_judges"])
        common_judges = sorted(common_judge_set)

    for row in aggregated_submitters:
        common_cells = [
            cell
            for cell in matrix_rows
            if cell["status"] == "completed"
            and cell["submitter_label"] == row["submitter_label"]
            and cell["judge_label"] in common_judges
        ]
        common_rate = _mean([float(cell["judge_overall_pass_rate_pct"]) for cell in common_cells])
        row["common_judges"] = common_judges
        row["common_judge_overall_pass_rate_pct"] = (
            _round(common_rate) if common_rate is not None else None
        )

    common_submitter_spread_pp: Optional[float]
    comparable_on_common_judges = [
        row for row in aggregated_submitters if row["common_judge_overall_pass_rate_pct"] is not None
    ]
    if len(comparable_on_common_judges) >= 2:
        ordered = sorted(
            comparable_on_common_judges,
            key=lambda row: (-row["common_judge_overall_pass_rate_pct"], row["submitter_label"]),
        )
        common_submitter_spread_pp = _round(
            ordered[0]["common_judge_overall_pass_rate_pct"]
            - ordered[-1]["common_judge_overall_pass_rate_pct"]
        )
    else:
        common_submitter_spread_pp = None

    return {
        "submitter_runs": list(submitter_runs.values()),
        "judge_labels": judge_labels,
        "matrix_cells": matrix_rows,
        "aggregated_submitters": aggregated_submitters,
        "judge_spread": judge_spread,
        "coverage": {
            "expected_cells": len(submitter_runs) * len(judge_labels),
            "completed_cells": completed_cells,
            "blocked_cells": blocked_count,
            "missing_cells": missing_count,
        },
        "common_judges": common_judges,
        "common_submitter_spread_pp": common_submitter_spread_pp,
        "common_submitter_spread_gate_30pp": (
            common_submitter_spread_pp is not None
            and round(common_submitter_spread_pp, 1) >= 30.0
        ),
    }


def render_matrix_markdown(report: Mapping[str, Any]) -> str:
    lines: List[str] = [
        "# LLM Public Slice Matrix Summary",
        "",
        "- submitter runs: "
        f"{len(report['submitter_runs'])}",
        "- judges declared: "
        f"{len(report['judge_labels'])}",
        "- completed cells: "
        f"{report['coverage']['completed_cells']} / {report['coverage']['expected_cells']}",
        "- blocked cells: "
        f"{report['coverage']['blocked_cells']}",
        "- missing cells: "
        f"{report['coverage']['missing_cells']}",
        "- common judges across compared submitters: "
        f"{', '.join(report['common_judges']) if report['common_judges'] else 'none'}",
        "- common-judge submitter spread (mean judge overall pass): "
        f"{_format_pct(report['common_submitter_spread_pp'])}",
        "- common-judge spread gate >= 30 pp: "
        f"{'yes' if report['common_submitter_spread_gate_30pp'] else 'no'}",
        "",
        "## Submitter Runs",
        "",
        "| submitter | request model | deterministic pass | citation specificity | completed judges | common-judge pass |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in report["aggregated_submitters"]:
        deterministic = f"{row['final_pass_count']} ({_format_pct(row['final_pass_rate_pct'])})"
        lines.append(
            "| "
            f"{row['submitter_label']} | "
            f"{row.get('request_model') or row.get('model') or 'n/a'} | "
            f"{deterministic} | "
            f"{_format_float(row['final_mean_citation_specificity_score'])} | "
            f"{row['num_completed_judges']} |"
            f" {_format_pct(row['common_judge_overall_pass_rate_pct'])} |"
        )

    lines.extend(
        [
            "",
            "## Aggregated Submitter Comparison",
            "",
            "| submitter | mean judge overall pass | mean threshold pass | mean axis score | mean grounding issues | parse failures |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report["aggregated_submitters"]:
        lines.append(
            "| "
            f"{row['submitter_label']} | "
            f"{_format_pct(row['mean_judge_overall_pass_rate_pct'])} | "
            f"{_format_pct(row['mean_threshold_pass_rate_pct'])} | "
            f"{_format_float(row['mean_axis_score'])} | "
            f"{_format_float(row['mean_grounding_issues'])} | "
            f"{row['parse_failures_total']} |"
        )

    lines.extend(
        [
            "",
            "## Raw Matrix Cells",
            "",
            "| submitter | judge | status | judge overall pass | threshold pass | mean axis | grounding issues | parse failures |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report["matrix_cells"]:
        if row["status"] == "completed":
            overall_pass = f"{row['judge_overall_pass']} ({_format_pct(row['judge_overall_pass_rate_pct'])})"
            threshold_pass = f"{row['passes_threshold_rule']} ({_format_pct(row['threshold_pass_rate_pct'])})"
            mean_axis = _format_float(row["mean_axis_score"])
            grounding = str(row["total_grounding_issues"])
            parse_failures = str(row["parse_failures"])
        else:
            overall_pass = row["reason"]
            threshold_pass = "n/a"
            mean_axis = "n/a"
            grounding = "n/a"
            parse_failures = "n/a"
        lines.append(
            "| "
            f"{row['submitter_label']} | "
            f"{row['judge_label']} | "
            f"{row['status']} | "
            f"{overall_pass} | "
            f"{threshold_pass} | "
            f"{mean_axis} | "
            f"{grounding} | "
            f"{parse_failures} |"
        )

    lines.extend(
        [
            "",
            "## Same-Judge Spread",
            "",
            "| judge | completed cells | best submitter | best pass | worst submitter | worst pass | spread |",
            "| --- | ---: | --- | ---: | --- | ---: | ---: |",
        ]
    )
    for row in report["judge_spread"]:
        lines.append(
            "| "
            f"{row['judge_label']} | "
            f"{row['completed_cells']} | "
            f"{row['best_submitter_label'] or 'n/a'} | "
            f"{_format_pct(row['best_judge_overall_pass_rate_pct'])} | "
            f"{row['worst_submitter_label'] or 'n/a'} | "
            f"{_format_pct(row['worst_judge_overall_pass_rate_pct'])} | "
            f"{_format_pct(row['spread_pp'])} |"
        )

    lines.extend(["", "## Per-Submitter Axis Means", ""])
    for row in report["aggregated_submitters"]:
        lines.extend(
            [
                f"### {row['submitter_label']}",
                "",
                "| axis | mean |",
                "| --- | ---: |",
            ]
        )
        for axis in AXIS_ORDER:
            if axis in row["per_axis_mean"]:
                lines.append(f"| {axis} | {_format_float(row['per_axis_mean'][axis])} |")
        lines.append("")

    blocked_or_missing = [
        row for row in report["matrix_cells"] if row["status"] in {"blocked", "missing"}
    ]
    if blocked_or_missing:
        lines.extend(["## Pending Cells", ""])
        for row in blocked_or_missing:
            lines.append(
                f"- `{row['submitter_label']} x {row['judge_label']}`: {row['status']} — {row['reason']}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--submitter-run",
        action="append",
        default=[],
        help="Submitter run in the form label=path-to-run-dir.",
    )
    parser.add_argument(
        "--judge-label",
        action="append",
        default=[],
        help="Expected judge label for the matrix. Repeat for each judge.",
    )
    parser.add_argument(
        "--judge-cell",
        action="append",
        default=[],
        help="Completed judge cell in the form submitter:judge=path-to-run-dir.",
    )
    parser.add_argument(
        "--blocked-cell",
        action="append",
        default=[],
        help="Blocked judge cell in the form submitter:judge=reason.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write summary.json and summary.md into.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)

    submitter_runs: Dict[str, Dict[str, Any]] = {}
    for raw in args.submitter_run:
        label, path = parse_labeled_path_arg(raw)
        if label in submitter_runs:
            raise ValueError(f"Duplicate submitter label: {label}")
        submitter_runs[label] = load_submitter_run(label, path)

    judge_cells = [
        load_judge_cell(submitter_label, judge_label, path)
        for submitter_label, judge_label, path in (
            parse_judge_cell_arg(raw) for raw in args.judge_cell
        )
    ]
    blocked_cells = {
        (submitter_label, judge_label): reason
        for submitter_label, judge_label, reason in (
            parse_blocked_cell_arg(raw) for raw in args.blocked_cell
        )
    }

    report = build_matrix_report(
        submitter_runs=submitter_runs,
        judge_labels=args.judge_label,
        judge_cells=judge_cells,
        blocked_cells=blocked_cells,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.md").write_text(
        render_matrix_markdown(report),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
