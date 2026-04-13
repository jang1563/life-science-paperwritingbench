from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .judge import judge_validation_unit_ready
from .models import (
    AutoQualificationRecord,
    BaselineRunSpec,
    JudgeValidationUnit,
    MaintenanceLogEntry,
    PaperQualificationDecision,
    PaperQualificationRecord,
    ProgramProgressReport,
    SourcePaper,
    TaskBundle,
)
from .policy import BaselineKind, CandidateTier


KB_SUBDIRECTORIES = (
    "raw",
    "normalized",
    "enriched",
    "qualified",
    "released",
)

V1_CORE_TARGETS = {
    "paper_qualified": 180,
    "task_bundles_total": 150,
    "public_units": 120,
    "private_units": 30,
    "lean_baselines": 3,
}

LEADERBOARD_TARGETS = {
    "judge_validation_units": 30,
    "agentic_baselines": 2,
}

LEAN_BASELINES = {
    BaselineKind.REFERENCE_TEMPLATE,
    BaselineKind.RETRIEVAL_WRITER,
    BaselineKind.SECTION_WISE_PIPELINE,
}

AGENTIC_BASELINES = {
    BaselineKind.SINGLE_AGENT_WRITER,
    BaselineKind.MULTI_AGENT_ORCHESTRATION,
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def initialize_knowledge_base_layout(root: str) -> Tuple[str, ...]:
    root_path = Path(root)
    created = []
    root_path.mkdir(parents=True, exist_ok=True)
    created.append(str(root_path))
    for subdirectory in KB_SUBDIRECTORIES:
        path = root_path / subdirectory
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))
    return tuple(created)


def _count_by(values: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def normalize_program_progress_decisions(
    paper_decisions: Sequence[object],
) -> Tuple[PaperQualificationDecision, ...]:
    normalized = []
    for item in paper_decisions:
        if isinstance(item, PaperQualificationDecision):
            normalized.append(item)
        elif isinstance(item, PaperQualificationRecord):
            normalized.append(item.decision)
        elif isinstance(item, AutoQualificationRecord):
            normalized.append(item.decision)
        else:
            raise TypeError(
                "paper_decisions must contain PaperQualificationDecision, "
                "PaperQualificationRecord, or AutoQualificationRecord"
            )
    return tuple(normalized)


def build_baseline_run_inventory(
    baseline_runs: Sequence[BaselineRunSpec],
) -> Tuple[BaselineRunSpec, ...]:
    latest_by_id: Dict[str, BaselineRunSpec] = {}
    order = []
    for run in baseline_runs:
        if run.baseline_id not in latest_by_id:
            order.append(run.baseline_id)
        latest_by_id[run.baseline_id] = run
    return tuple(latest_by_id[baseline_id] for baseline_id in order)


def summarize_program_progress(
    source_papers: Sequence[SourcePaper],
    paper_decisions: Sequence[object],
    task_bundles: Sequence[TaskBundle],
    judge_validation_units: Sequence[JudgeValidationUnit] = (),
    baseline_runs: Sequence[BaselineRunSpec] = (),
    generated_at: Optional[str] = None,
) -> ProgramProgressReport:
    normalized_decisions = normalize_program_progress_decisions(paper_decisions)
    baseline_inventory = build_baseline_run_inventory(baseline_runs)
    notes = []
    if len(source_papers) != len(normalized_decisions):
        notes.append("paper decisions are compared to source papers by sequence order; counts may be approximate")
    paper_qualified = sum(
        1
        for decision in normalized_decisions
        if decision.eligible_for_unit_extraction and decision.candidate_tier != CandidateTier.EXCLUDED
    )
    public_units = sum(1 for bundle in task_bundles if bundle.holdout_bucket == "public")
    private_units = sum(1 for bundle in task_bundles if bundle.holdout_bucket == "private")
    paper_by_id = {paper.paper_id: paper for paper in source_papers}
    hybrid_overlay_units = sum(
        1
        for bundle in task_bundles
        if bundle.paper_id in paper_by_id and len(paper_by_id[bundle.paper_id].modality_overlays) > 1
    )
    controlled_access_qualified_papers = sum(
        1
        for paper, decision in zip(source_papers, normalized_decisions)
        if paper.controlled_access_human_data
        and decision.eligible_for_unit_extraction
        and decision.candidate_tier != CandidateTier.EXCLUDED
    )
    study_class_counts = _count_by(bundle.study_class.value for bundle in task_bundles)
    task_family_counts = _count_by(bundle.task_family.value for bundle in task_bundles)
    claim_mode_counts = _count_by(bundle.claim_mode.value for bundle in task_bundles)

    replayable_kinds = {
        run.baseline_kind
        for run in baseline_inventory
        if run.replay_verified
    }
    replayable_baselines = len(replayable_kinds)
    ready_judge_validation_units = sum(
        1 for unit in judge_validation_units if judge_validation_unit_ready(unit)
    )

    v1_core_gate_passed = (
        paper_qualified >= V1_CORE_TARGETS["paper_qualified"]
        and len(task_bundles) >= V1_CORE_TARGETS["task_bundles_total"]
        and public_units >= V1_CORE_TARGETS["public_units"]
        and private_units >= V1_CORE_TARGETS["private_units"]
        and len(replayable_kinds & LEAN_BASELINES) >= V1_CORE_TARGETS["lean_baselines"]
    )
    leaderboard_gate_passed = (
        v1_core_gate_passed
        and ready_judge_validation_units >= LEADERBOARD_TARGETS["judge_validation_units"]
        and len(replayable_kinds & AGENTIC_BASELINES) >= LEADERBOARD_TARGETS["agentic_baselines"]
    )

    if public_units + private_units < len(task_bundles):
        notes.append("some task bundles do not yet have a holdout bucket assignment")

    return ProgramProgressReport(
        generated_at=generated_at or _utc_timestamp(),
        source_candidates=len(source_papers),
        paper_qualified=paper_qualified,
        task_bundles_total=len(task_bundles),
        public_units=public_units,
        private_units=private_units,
        hybrid_overlay_units=hybrid_overlay_units,
        controlled_access_qualified_papers=controlled_access_qualified_papers,
        judge_validation_units=ready_judge_validation_units,
        replayable_baselines=replayable_baselines,
        study_class_counts=study_class_counts,
        task_family_counts=task_family_counts,
        claim_mode_counts=claim_mode_counts,
        v1_core_gate_passed=v1_core_gate_passed,
        leaderboard_gate_passed=leaderboard_gate_passed,
        notes=tuple(notes),
    )


def build_maintenance_log_entry(
    phase: str,
    summary: str,
    release_bundle_id: Optional[str] = None,
    artifacts: Sequence[str] = (),
    notes: Sequence[str] = (),
    created_at: Optional[str] = None,
) -> MaintenanceLogEntry:
    timestamp = created_at or _utc_timestamp()
    digest = hashlib.sha256(f"{timestamp}:{phase}:{summary}".encode("utf-8")).hexdigest()[:12].upper()
    return MaintenanceLogEntry(
        entry_id=f"MLE:{digest}",
        created_at=timestamp,
        phase=phase,
        summary=summary,
        release_bundle_id=release_bundle_id,
        artifacts=tuple(artifacts),
        notes=tuple(notes),
    )
