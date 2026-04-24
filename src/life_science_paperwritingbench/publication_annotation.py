from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .judge import DEFAULT_JUDGE_RUBRIC_AXES, audit_judge_validation_slice
from .judgeflow import merge_judge_review_forms, summarize_judge_progress
from .models import (
    JudgeAdjudicationRecord,
    JudgeReviewForm,
    JudgeValidationUnit,
    PublicationAnnotationHoldAuditReport,
    PublicationAnnotationPacket,
    PublicationAnnotationPacketSummary,
    TaskBundle,
)
from .publication import DEFAULT_PUBLICATION_TARGET_PER_FAMILY, FRONTIER_WRITING_TASK_FAMILIES


PUBLICATION_SELECTION_LOCK_NOTE = "publication_validation_selection_locked"
PUBLICATION_RUBRIC_LOCK_NOTE = "publication_validation_rubric_locked"

PUBLICATION_RUBRIC_GUIDANCE: Mapping[str, str] = {
    "evidence_fidelity": (
        "Judge whether the eventual section stays faithful to the bundled benchmark evidence and avoids unsupported claims."
    ),
    "traceability": (
        "Judge whether concrete statements can be traced back to the provided evidence units, assertions, and provenance hints."
    ),
    "provenance_completeness": (
        "Judge whether the section preserves source/provenance cues that the benchmark expects for grounded scientific writing."
    ),
    "writing_structure_compliance": (
        "Judge whether the section follows the requested section form and reads like a compliant scientific section rather than notes or meta-commentary."
    ),
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_filename_token(value: str) -> str:
    token = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    token = "_".join(part for part in token.split("_") if part)
    return token or "packet"


def _pair_key(validation_unit_id: str, reviewer_id: str) -> str:
    return f"{validation_unit_id}::{reviewer_id}"


def _expected_publication_total() -> int:
    return DEFAULT_PUBLICATION_TARGET_PER_FAMILY * len(FRONTIER_WRITING_TASK_FAMILIES)


def _reviewer_form_filename(reviewer_id: str) -> str:
    return f"{_safe_filename_token(reviewer_id)}_judge_review_forms.jsonl"


def lock_publication_annotation_units(
    judge_units: Sequence[JudgeValidationUnit],
) -> Tuple[JudgeValidationUnit, ...]:
    locked_units: List[JudgeValidationUnit] = []
    for unit in judge_units:
        notes = list(unit.notes)
        if PUBLICATION_SELECTION_LOCK_NOTE not in notes:
            notes.append(PUBLICATION_SELECTION_LOCK_NOTE)
        if PUBLICATION_RUBRIC_LOCK_NOTE not in notes:
            notes.append(PUBLICATION_RUBRIC_LOCK_NOTE)
        locked_units.append(
            JudgeValidationUnit(
                validation_unit_id=unit.validation_unit_id,
                task_bundle_id=unit.task_bundle_id,
                human_adjudicated=unit.human_adjudicated,
                rubric_labels=dict(unit.rubric_labels),
                frozen=True,
                rubric_version=unit.rubric_version,
                adjudicator_id=unit.adjudicator_id,
                notes=tuple(notes),
            )
        )
    return tuple(locked_units)


def build_publication_annotation_packets(
    *,
    task_bundles: Sequence[TaskBundle],
    judge_units: Sequence[JudgeValidationUnit],
    forms: Sequence[JudgeReviewForm],
    reviewer_ids: Sequence[str],
    authoritative_form_path: str,
    packet_dir: str = "review_packets/packets",
) -> Tuple[PublicationAnnotationPacket, ...]:
    bundle_map = {bundle.task_bundle_id: bundle for bundle in task_bundles}
    merged_forms = merge_judge_review_forms(forms)
    form_lookup = {(form.validation_unit_id, form.reviewer_id): form for form in merged_forms}
    packets: List[PublicationAnnotationPacket] = []
    for unit in sorted(judge_units, key=lambda item: (item.validation_unit_id, item.task_bundle_id)):
        bundle = bundle_map.get(unit.task_bundle_id)
        if bundle is None:
            continue
        for reviewer_id in reviewer_ids:
            packet_id = f"PACKET:{reviewer_id}:{unit.validation_unit_id}"
            reviewer_dir = _safe_filename_token(reviewer_id)
            unit_token = _safe_filename_token(unit.validation_unit_id)
            packet_markdown_path = (Path(packet_dir) / reviewer_dir / f"{unit_token}.md").as_posix()
            form_present = (unit.validation_unit_id, reviewer_id) in form_lookup
            notes: List[str] = []
            if not form_present:
                notes.append("missing_authoritative_form")
            if not unit.frozen:
                notes.append("judge_unit_not_frozen")
            if PUBLICATION_SELECTION_LOCK_NOTE not in unit.notes:
                notes.append("selection_lock_note_missing")
            if PUBLICATION_RUBRIC_LOCK_NOTE not in unit.notes:
                notes.append("rubric_lock_note_missing")
            artifacts = dict(bundle.input_artifacts)
            packets.append(
                PublicationAnnotationPacket(
                    packet_id=packet_id,
                    reviewer_id=reviewer_id,
                    validation_unit_id=unit.validation_unit_id,
                    task_bundle_id=bundle.task_bundle_id,
                    task_family=bundle.task_family,
                    study_class=bundle.study_class,
                    claim_mode=bundle.claim_mode,
                    release_tier=bundle.release_tier,
                    paper_id=bundle.paper_id,
                    holdout_bucket=bundle.holdout_bucket,
                    rubric_version=unit.rubric_version,
                    authoritative_form_present=form_present,
                    authoritative_form_path=authoritative_form_path,
                    packet_markdown_path=packet_markdown_path,
                    evidence_unit_ids=tuple(str(item) for item in artifacts.get("evidence_unit_ids", bundle.evidence_unit_ids)),
                    evidence_pointers=tuple(str(item) for item in artifacts.get("evidence_pointers", ())),
                    evidence_items=tuple(str(item) for item in artifacts.get("evidence_items", ())),
                    evidence_types=tuple(str(item) for item in artifacts.get("evidence_types", ())),
                    assertion_ids=tuple(str(item) for item in artifacts.get("assertion_ids", ())),
                    authoring_constraints=dict(bundle.authoring_constraints),
                    scoring_profile=dict(bundle.scoring_profile),
                    notes=tuple(notes),
                )
            )
    return tuple(packets)


def summarize_publication_annotation_packets(
    packets: Sequence[PublicationAnnotationPacket],
    *,
    judge_units: Sequence[JudgeValidationUnit],
    reviewer_ids: Sequence[str],
) -> PublicationAnnotationPacketSummary:
    expected_pairs = {
        _pair_key(unit.validation_unit_id, reviewer_id)
        for unit in judge_units
        for reviewer_id in reviewer_ids
    }
    packet_id_counter = Counter(packet.packet_id for packet in packets)
    pair_counter = Counter(_pair_key(packet.validation_unit_id, packet.reviewer_id) for packet in packets)
    actual_pairs = set(pair_counter)
    missing_pairs = tuple(sorted(expected_pairs - actual_pairs))
    unexpected_pairs = tuple(sorted(actual_pairs - expected_pairs))
    duplicate_packet_ids = tuple(sorted(packet_id for packet_id, count in packet_id_counter.items() if count > 1))
    duplicate_packet_pairs = tuple(sorted(pair for pair, count in pair_counter.items() if count > 1))
    reviewer_assignment_counts = Counter(packet.reviewer_id for packet in packets)
    task_family_counts = Counter(packet.task_family.value for packet in packets)
    study_class_counts = Counter(packet.study_class.value for packet in packets)
    rubric_versions = tuple(sorted({packet.rubric_version for packet in packets}))
    missing_authoritative_form_pairs = tuple(
        sorted(
            _pair_key(packet.validation_unit_id, packet.reviewer_id)
            for packet in packets
            if not packet.authoritative_form_present
        )
    )
    issues: List[str] = []
    if missing_pairs:
        issues.append(f"missing reviewer packet coverage for {len(missing_pairs)} unit/reviewer pairs")
    if unexpected_pairs:
        issues.append(f"unexpected reviewer packet coverage for {len(unexpected_pairs)} unit/reviewer pairs")
    if duplicate_packet_ids:
        issues.append(f"duplicate packet ids detected: {', '.join(duplicate_packet_ids[:5])}")
    if duplicate_packet_pairs:
        issues.append(f"duplicate reviewer packet pairs detected: {', '.join(duplicate_packet_pairs[:5])}")
    if missing_authoritative_form_pairs:
        issues.append(
            f"authoritative JSONL sidecars missing for {len(missing_authoritative_form_pairs)} packet assignments"
        )
    packet_coverage_complete = not missing_pairs and not unexpected_pairs and not duplicate_packet_pairs
    authoritative_form_coverage_complete = not missing_authoritative_form_pairs
    return PublicationAnnotationPacketSummary(
        generated_at=_utc_timestamp(),
        total_packets=len(packets),
        expected_packets=len(expected_pairs),
        total_judge_units=len(judge_units),
        reviewer_ids=tuple(reviewer_ids),
        reviewer_assignment_counts=dict(reviewer_assignment_counts),
        task_family_counts=dict(task_family_counts),
        study_class_counts=dict(study_class_counts),
        rubric_versions=rubric_versions,
        packet_coverage_complete=packet_coverage_complete,
        authoritative_form_coverage_complete=authoritative_form_coverage_complete,
        duplicate_packet_ids=duplicate_packet_ids,
        duplicate_packet_pairs=duplicate_packet_pairs,
        missing_packet_pairs=missing_pairs,
        unexpected_packet_pairs=unexpected_pairs,
        missing_authoritative_form_pairs=missing_authoritative_form_pairs,
        issues=tuple(issues),
        ok=packet_coverage_complete and authoritative_form_coverage_complete and not duplicate_packet_ids,
    )


def render_publication_annotation_packet_markdown(
    packet: PublicationAnnotationPacket,
    *,
    judge_unit: JudgeValidationUnit,
    task_bundle: TaskBundle,
) -> str:
    lines: List[str] = [
        f"# Publication Annotation Packet: {packet.reviewer_id}",
        "",
        f"- Packet ID: `{packet.packet_id}`",
        f"- Validation unit: `{packet.validation_unit_id}`",
        f"- Task bundle: `{packet.task_bundle_id}`",
        f"- Paper ID: `{packet.paper_id or 'unknown'}`",
        f"- Task family: `{packet.task_family.value}`",
        f"- Study class: `{packet.study_class.value}`",
        f"- Claim mode: `{packet.claim_mode.value}`",
        f"- Release tier: `{packet.release_tier.value}`",
        f"- Holdout bucket: `{packet.holdout_bucket or 'unassigned'}`",
        f"- Rubric version: `{packet.rubric_version}`",
        f"- Truth manifest: `{task_bundle.truth_manifest_id or 'unknown'}`",
        f"- Authoritative sidecar: `{packet.authoritative_form_path}` "
        f"(match `validation_unit_id={packet.validation_unit_id}` and `reviewer_id={packet.reviewer_id}`)",
        "",
        "## Frozen Contract",
        "",
        f"- Selection locked: `{'yes' if PUBLICATION_SELECTION_LOCK_NOTE in judge_unit.notes else 'no'}`",
        f"- Rubric locked: `{'yes' if PUBLICATION_RUBRIC_LOCK_NOTE in judge_unit.notes else 'no'}`",
        f"- Judge unit frozen: `{'yes' if judge_unit.frozen else 'no'}`",
        f"- Human-adjudicated already: `{'yes' if judge_unit.human_adjudicated else 'no'}`",
        "",
        "## Evidence Context",
        "",
        f"- Evidence unit IDs: {', '.join(f'`{item}`' for item in packet.evidence_unit_ids) or 'none'}",
        f"- Evidence pointers: {', '.join(f'`{item}`' for item in packet.evidence_pointers) or 'none'}",
        f"- Evidence items: {', '.join(f'`{item}`' for item in packet.evidence_items) or 'none'}",
        f"- Evidence types: {', '.join(f'`{item}`' for item in packet.evidence_types) or 'none'}",
        f"- Assertion IDs: {', '.join(f'`{item}`' for item in packet.assertion_ids) or 'none'}",
        "",
        "## Authoring Constraints",
        "",
        "```json",
        json.dumps(dict(task_bundle.authoring_constraints), indent=2, sort_keys=True),
        "```",
        "",
        "## Scoring Profile",
        "",
        "```json",
        json.dumps(dict(task_bundle.scoring_profile), indent=2, sort_keys=True),
        "```",
        "",
        "## Rubric Guidance",
        "",
    ]
    for axis in DEFAULT_JUDGE_RUBRIC_AXES:
        lines.append(f"- `{axis}`: {PUBLICATION_RUBRIC_GUIDANCE.get(axis, 'Assess this axis using the frozen batch rubric.')}")
    lines.extend(
        [
            "",
            "## Reviewer Workflow",
            "",
            "- Read this packet for context, but treat the JSONL sidecar as the authoritative submission surface.",
            "- Update the matching row in `judge_review_forms.jsonl` using the same `validation_unit_id` and `reviewer_id`.",
            "- Do not add or remove rubric axes, and do not change the rubric version for this frozen round.",
            "- Return the updated JSONL form copy for merge and adjudication.",
        ]
    )
    if packet.notes:
        lines.extend(["", "## Packet QA Notes", ""])
        for note in packet.notes:
            lines.append(f"- `{note}`")
    return "\n".join(lines).rstrip() + "\n"


def render_publication_annotation_reviewer_markdown(
    packets: Sequence[PublicationAnnotationPacket],
    *,
    reviewer_id: str,
    batch_dir: str,
    packet_dir: Optional[str] = None,
) -> str:
    reviewer_packets = sorted(
        [packet for packet in packets if packet.reviewer_id == reviewer_id],
        key=lambda item: (item.task_family.value, item.study_class.value, item.validation_unit_id),
    )
    study_counts = Counter(packet.study_class.value for packet in reviewer_packets)
    family_counts = Counter(packet.task_family.value for packet in reviewer_packets)
    rubric_versions = sorted({packet.rubric_version for packet in reviewer_packets})
    lines: List[str] = [
        f"# Publication Annotation Handoff: {reviewer_id}",
        "",
        f"- Batch directory: `{batch_dir}`",
        f"- Total assignments: `{len(reviewer_packets)}`",
        f"- Rubric versions: {', '.join(f'`{item}`' for item in rubric_versions) or 'none'}",
        "",
        "## Coverage",
        "",
        f"- Task families: {', '.join(f'`{key}`={value}' for key, value in sorted(family_counts.items())) or 'none'}",
        f"- Study classes: {', '.join(f'`{key}`={value}' for key, value in sorted(study_counts.items())) or 'none'}",
        "",
        "## Assignments",
        "",
    ]
    for packet in reviewer_packets:
        packet_path = packet.packet_markdown_path
        if packet_dir is not None:
            packet_path = (Path(packet_dir) / Path(packet.packet_markdown_path).name).as_posix()
        lines.append(
            f"- `{packet.validation_unit_id}` "
            f"`{packet.task_family.value}` "
            f"`{packet.study_class.value}` "
            f"`{packet.paper_id or 'unknown'}` "
            f"-> `{packet_path}`"
        )
    lines.extend(
        [
            "",
            "## Workflow",
            "",
            "- Read each markdown packet for context.",
            "- Fill the matching row in `judge_review_forms.jsonl`; that JSONL remains authoritative.",
            "- Keep `validation_unit_id`, `reviewer_id`, rubric axes, and rubric version unchanged.",
            "- Return updated JSONL reviewer copies for merge and adjudication.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_publication_annotation_packet_summary_markdown(
    summary: PublicationAnnotationPacketSummary,
) -> str:
    lines: List[str] = [
        "# Publication Annotation Packet Summary",
        "",
        f"- Total packets: `{summary.total_packets}` / `{summary.expected_packets}` expected",
        f"- Total judge units: `{summary.total_judge_units}`",
        f"- Packet coverage complete: `{'yes' if summary.packet_coverage_complete else 'no'}`",
        f"- Authoritative form coverage complete: `{'yes' if summary.authoritative_form_coverage_complete else 'no'}`",
        f"- Rubric versions: {', '.join(f'`{item}`' for item in summary.rubric_versions) or 'none'}",
        "",
        "## Reviewer Assignment Counts",
        "",
    ]
    for reviewer_id in summary.reviewer_ids:
        lines.append(f"- `{reviewer_id}`: `{summary.reviewer_assignment_counts.get(reviewer_id, 0)}`")
    if summary.issues:
        lines.extend(["", "## Issues", ""])
        for issue in summary.issues:
            lines.append(f"- {issue}")
    return "\n".join(lines).rstrip() + "\n"


def build_publication_annotation_reviewer_form_copies(
    forms: Sequence[JudgeReviewForm],
    *,
    reviewer_ids: Sequence[str],
) -> Mapping[str, Tuple[JudgeReviewForm, ...]]:
    merged_forms = merge_judge_review_forms(forms)
    copies: Dict[str, Tuple[JudgeReviewForm, ...]] = {}
    for reviewer_id in reviewer_ids:
        reviewer_forms = [
            form for form in merged_forms if form.reviewer_id == reviewer_id
        ]
        reviewer_forms.sort(key=lambda item: item.validation_unit_id)
        copies[reviewer_id] = tuple(reviewer_forms)
    return copies


def render_publication_annotation_handoff_manifest(
    *,
    batch_dir: str,
    protocol_path: str,
    preflight_path: Optional[str],
    launch_readiness_assessment_path: Optional[str],
    calibration_mini_round_path: Optional[str],
    canonical_forms_path: str,
    judge_units_path: str,
    batch_summary_path: str,
    hold_audit_path: str,
    launch_checklist_path: str,
    adjudicator_handoff_path: str,
    reviewer_index_paths: Mapping[str, str],
    reviewer_packet_dir_paths: Mapping[str, str],
    reviewer_assignment_paths: Mapping[str, str],
    reviewer_form_paths: Mapping[str, str],
    reviewer_launch_message_paths: Mapping[str, str],
    adjudicator_launch_message_paths: Mapping[str, str],
    truth_manifest_lookup_path: Optional[str],
    selected_truth_manifests_path: Optional[str],
    merged_forms_path: str,
    adjudication_shells_path: str,
    adjudication_queue_path: str,
    agreement_output_path: str,
    readiness_snapshot_path: str,
) -> str:
    reviewer_ids = tuple(sorted(reviewer_index_paths))
    lines: List[str] = [
        "# Publication Validation Handoff Manifest",
        "",
        "## Purpose",
        "",
        "This file is the organizer-facing dispatch map for launching the first",
        "human-review round of:",
        "",
        f"- `{batch_dir}`",
        "",
        "Use it to decide which files to send to each reviewer, which files stay with",
        "the organizer, and which files become relevant only at adjudication time.",
        "",
    ]
    for reviewer_id in reviewer_ids:
        label = reviewer_id.replace("_", " ").title()
        lines.extend(
            [
                f"## {label} Package",
                "",
                f"Send these files to `{reviewer_id}`:",
                "",
                "- launch message:",
                f"  `{reviewer_launch_message_paths[reviewer_id]}`",
                f"- protocol:",
                f"  `{protocol_path}`",
            ]
        )
        if truth_manifest_lookup_path and selected_truth_manifests_path:
            lines.extend(
                [
                    "- truth-manifest lookup:",
                    f"  `{truth_manifest_lookup_path}`",
                    "- selected truth-manifest sidecars:",
                    f"  `{selected_truth_manifests_path}`",
                ]
            )
        lines.extend(
            [
                "- reviewer index:",
                f"  `{reviewer_index_paths[reviewer_id]}`",
                "- reviewer packets directory:",
                f"  `{reviewer_packet_dir_paths[reviewer_id]}`",
                "- reviewer assignment sidecar:",
                f"  `{reviewer_assignment_paths[reviewer_id]}`",
                "- reviewer working copy:",
                f"  `{reviewer_form_paths[reviewer_id]}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Organizer Files",
            "",
            "Keep these local while review is in progress:",
            "",
            "- canonical blank forms:",
            f"  `{canonical_forms_path}`",
            "- frozen judge units:",
            f"  `{judge_units_path}`",
            "- batch summary:",
            f"  `{batch_summary_path}`",
            "- hold audit:",
            f"  `{hold_audit_path}`",
        ]
    )
    if preflight_path:
        lines.extend(
            [
                "- pre-launch preflight:",
                f"  `{preflight_path}`",
            ]
        )
    if launch_readiness_assessment_path:
        lines.extend(
            [
                "- launch readiness assessment:",
                f"  `{launch_readiness_assessment_path}`",
            ]
        )
    if calibration_mini_round_path:
        lines.extend(
            [
                "- calibration starter set:",
                f"  `{calibration_mini_round_path}`",
            ]
        )
    if truth_manifest_lookup_path and selected_truth_manifests_path:
        lines.extend(
            [
                "- truth-manifest lookup:",
                f"  `{truth_manifest_lookup_path}`",
                "- selected truth-manifest sidecars:",
                f"  `{selected_truth_manifests_path}`",
            ]
        )
    lines.extend(
        [
            "- launch checklist:",
            f"  `{launch_checklist_path}`",
            "- adjudicator handoff:",
            f"  `{adjudicator_handoff_path}`",
            "",
            "## Adjudicator Package",
            "",
            "Send these files to the adjudicator only after reviewer intake is complete:",
            "",
        ]
    )
    for adjudicator_id in tuple(sorted(adjudicator_launch_message_paths)):
        lines.extend(
            [
                f"- launch message for `{adjudicator_id}`:",
                f"  `{adjudicator_launch_message_paths[adjudicator_id]}`",
            ]
        )
    lines.extend(
        [
            "- adjudicator handoff:",
            f"  `{adjudicator_handoff_path}`",
            "",
            "## Adjudication Files",
            "",
            "These matter after both reviewers return completed forms:",
            "",
            "- merged reviewer forms:",
            f"  `{merged_forms_path}`",
            "- adjudication shells:",
            f"  `{adjudication_shells_path}`",
            "- adjudication queue:",
            f"  `{adjudication_queue_path}`",
            "- agreement output:",
            f"  `{agreement_output_path}`",
            "- readiness snapshot:",
            f"  `{readiness_snapshot_path}`",
            "",
            "## Important Handling Rule",
            "",
            "- reviewers should edit only their reviewer-specific working copy under",
            "  `reviewer_forms/`",
            "- the organizer merges returned copies into",
            "  `judge_review_forms_merged.jsonl`",
            "- the blank canonical `judge_review_forms.jsonl` stays untouched as the frozen",
            "  starting state for this round",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_publication_annotation_review_launch_checklist(
    *,
    reviewer_ids: Sequence[str],
    reviewer_form_paths: Mapping[str, str],
    hold_audit_path: str,
    manifest_path: str,
    protocol_path: str,
    preflight_path: Optional[str],
    launch_readiness_assessment_path: Optional[str],
    calibration_mini_round_path: Optional[str],
    truth_manifest_lookup_path: Optional[str],
    selected_truth_manifests_path: Optional[str],
    judge_units_path: str,
    merged_forms_path: str,
    adjudication_shells_path: str,
    adjudication_queue_path: str,
    agreement_output_path: str,
    readiness_snapshot_path: str,
    validation_summary_path: str,
    matrix_summary_path: str,
    canary_summary_path: str,
) -> str:
    reviewer_ids = tuple(reviewer_ids)
    merge_inputs = " \\\n           ".join(
        reviewer_form_paths[reviewer_id] for reviewer_id in reviewer_ids
    )
    reviewer_args = " ".join(reviewer_ids)
    lines: List[str] = [
        "# Publication Validation Review Launch Checklist",
        "",
        "## Preflight",
        "",
    ]
    step_index = 1
    if preflight_path:
        lines.append(f"{step_index}. Read and complete `{preflight_path}`.")
        step_index += 1
    if launch_readiness_assessment_path:
        lines.append(f"{step_index}. Read `{launch_readiness_assessment_path}`.")
        step_index += 1
    if calibration_mini_round_path:
        lines.append(f"{step_index}. Review the shared starter set in `{calibration_mini_round_path}`.")
        step_index += 1
    lines.extend(
        [
            f"{step_index}. Confirm `{hold_audit_path}` still reports:",
            "   - `Structurally ready: yes`",
            "   - `Awaiting human review: yes`",
            f"{step_index + 1}. Confirm all reviewer working copies exist:",
        ]
    )
    for reviewer_id in reviewer_ids:
        lines.append(f"   - `{reviewer_form_paths[reviewer_id]}`")
    step_index += 2
    lines.extend(
        [
            f"{step_index}. Confirm the packet directories exist for all reviewers under",
            "   `review_packets/packets/`.",
        ]
    )
    step_index += 1
    if truth_manifest_lookup_path and selected_truth_manifests_path:
        lines.extend(
            [
                f"{step_index}. If this round is using benchmark-unit adjudication, confirm the reviewer package also includes:",
                f"   - `{truth_manifest_lookup_path}`",
                f"   - `{selected_truth_manifests_path}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Dispatch",
            "",
            f"1. Send each reviewer the package listed in `{manifest_path}`.",
            f"2. Include `{protocol_path}` with each dispatch.",
        ]
    )
    if calibration_mini_round_path:
        lines.extend(
            [
                f"3. Ask reviewers to begin with only the shared starter units in `{calibration_mini_round_path}`, then pause before opening the remaining units.",
            ]
        )
        dispatch_step = 4
    else:
        dispatch_step = 3
    if truth_manifest_lookup_path and selected_truth_manifests_path:
        lines.extend(
            [
                f"{dispatch_step}. Make clear that this round adjudicates frozen benchmark units against the supplied truth-manifest evidence.",
                f"{dispatch_step + 1}. Ask reviewers to return only their completed reviewer-specific JSONL copy.",
            ]
        )
    else:
        lines.extend(
            [
                f"{dispatch_step}. Ask reviewers to return only their completed reviewer-specific JSONL copy.",
            ]
        )
    lines.extend(
        [
            "",
            "## Intake",
            "",
            "1. Save the returned reviewer copies back into the same `reviewer_forms/` paths.",
            "2. Sanity-check that each returned file still has the expected row count and reviewer id.",
            "",
            "## Merge",
            "",
            "```bash",
            "PYTHONPATH=src python3 -m life_science_paperwritingbench.cli merge-judge-review-forms \\",
            f"  --inputs {merge_inputs} \\",
            f"  --output {merged_forms_path}",
            "```",
            "",
            "## Adjudication",
            "",
            "```bash",
            "PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-judge-adjudication-queue \\",
            f"  --judge-units {judge_units_path} \\",
            f"  --forms {merged_forms_path} \\",
            f"  --adjudications {adjudication_shells_path} \\",
            f"  --reviewers {reviewer_args} \\",
            f"  --output {adjudication_queue_path}",
            "```",
            "",
            f"Fill `{adjudication_shells_path}` only after both reviewer copies are merged and",
            "the queue is generated.",
            "",
            "## Post-Review Metrics",
            "",
            "```bash",
            "PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-judge-agreement \\",
            f"  --judge-units {judge_units_path} \\",
            f"  --forms {merged_forms_path} \\",
            f"  --adjudications {adjudication_shells_path} \\",
            f"  --output {agreement_output_path}",
            "",
            "PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-publication-readiness \\",
            f"  --matrix-summary {matrix_summary_path} \\",
            f"  --canary-summary {canary_summary_path} \\",
            f"  --validation-summary {validation_summary_path} \\",
            f"  --agreement-metrics {agreement_output_path} \\",
            f"  --output {readiness_snapshot_path}",
            "```",
            "",
            "## Done Condition",
            "",
            "This launch round is complete when:",
            "",
            "- all reviewer working copies are fully completed",
            f"- `{merged_forms_path}` exists",
            f"- `{adjudication_queue_path}` exists",
            "- adjudication is finalized where needed",
            f"- `{agreement_output_path}` exists",
            f"- `{readiness_snapshot_path}` has been refreshed",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_publication_annotation_reviewer_request_template(
    *,
    reviewer_ids: Sequence[str],
    protocol_path: str,
    reviewer_index_paths: Mapping[str, str],
    reviewer_packet_dir_paths: Mapping[str, str],
    reviewer_assignment_paths: Mapping[str, str],
    reviewer_form_paths: Mapping[str, str],
    calibration_mini_round_path: Optional[str],
    truth_manifest_lookup_path: Optional[str],
    selected_truth_manifests_path: Optional[str],
    reviewer_assignment_counts: Mapping[str, int],
    reviewer_task_family_counts: Mapping[str, Mapping[str, int]],
) -> str:
    lines: List[str] = [
        "# Reviewer Request Template",
        "",
        "Use the matching block below when sending the first publication-validation",
        "review package.",
        "",
    ]
    for reviewer_id in reviewer_ids:
        family_summary = ", ".join(
            f"`{task_family}`={count}"
            for task_family, count in sorted(reviewer_task_family_counts.get(reviewer_id, {}).items())
        )
        lines.extend(
            [
                f"## Template: {reviewer_id}",
                "",
                f"Subject: Life-Science PaperWritingBench review batch for `{reviewer_id}`",
                "",
                "Hi,",
                "",
                "I am sending the first `Life-Science PaperWritingBench` publication-validation",
                "batch for review.",
                f"This round covers `{reviewer_assignment_counts.get(reviewer_id, 0)}` assigned writing units,",
                f"with family coverage {family_summary}.",
                "",
            ]
        )
        if truth_manifest_lookup_path and selected_truth_manifests_path:
            lines.extend(
                [
                    "This round is for frozen benchmark-unit adjudication against the supplied",
                    "truth-manifest evidence, not for evaluating a named model run.",
                    "",
                ]
            )
        lines.extend(
            [
                "Please use these files:",
                "",
                f"- protocol: `{protocol_path}`",
            ]
        )
        if truth_manifest_lookup_path and selected_truth_manifests_path:
            lines.extend(
                [
                    f"- truth-manifest lookup:",
                    f"  `{truth_manifest_lookup_path}`",
                    "- selected truth-manifest sidecars:",
                    f"  `{selected_truth_manifests_path}`",
                ]
            )
        lines.extend(
            [
                "- reviewer index:",
                f"  `{reviewer_index_paths[reviewer_id]}`",
                "- packet directory:",
                f"  `{reviewer_packet_dir_paths[reviewer_id]}`",
                "- assignment sidecar:",
                f"  `{reviewer_assignment_paths[reviewer_id]}`",
                "- working form copy:",
                f"  `{reviewer_form_paths[reviewer_id]}`",
                "",
                f"Please fill only the rows for `{reviewer_id}`, keep the schema unchanged, and",
                "return the completed JSONL working copy when finished.",
                "",
            ]
        )
        if calibration_mini_round_path:
            lines.extend(
                [
                    f"If the organizer asks for the shared starter pass in `{calibration_mini_round_path}`,",
                    "complete only those units first, then pause before continuing with the remaining units.",
                    "",
                ]
            )
        lines.extend(
            [
                "The scoring scale is `0-3` per axis:",
                "",
                "- `0`: absent or wrong",
                "- `1`: partial",
                "- `2`: mostly correct",
                "- `3`: fully compliant",
                "",
                "Thanks.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_publication_annotation_reviewer_launch_message(
    *,
    reviewer_id: str,
    protocol_path: str,
    reviewer_index_path: str,
    reviewer_packet_dir_path: str,
    reviewer_assignment_path: str,
    reviewer_form_path: str,
    calibration_mini_round_path: Optional[str],
    truth_manifest_lookup_path: Optional[str],
    selected_truth_manifests_path: Optional[str],
    reviewer_assignment_count: int,
    reviewer_task_family_counts: Mapping[str, int],
) -> str:
    family_summary = ", ".join(
        f"`{task_family}`={count}"
        for task_family, count in sorted(reviewer_task_family_counts.items())
    )
    if not family_summary:
        family_summary = "`none`"
    lines: List[str] = [
        f"Subject: Publication-validation launch package for `{reviewer_id}`",
        "",
        "Hi,",
        "",
        "I am sending your `Life-Science PaperWritingBench` publication-validation",
        "package.",
        f"Your current assignment covers `{reviewer_assignment_count}` frozen benchmark units,",
        f"with family coverage {family_summary}.",
        "",
        "This round is for human adjudication of frozen benchmark units against the",
        "supplied benchmark evidence. It is not a named model-run review.",
        "",
        "Please start with these files:",
        "",
        f"1. `{protocol_path}`",
        f"2. `{reviewer_index_path}`",
    ]
    next_step = 3
    if calibration_mini_round_path:
        lines.extend(
            [
                f"{next_step}. Complete only the shared starter units in",
                f"   `{calibration_mini_round_path}`, then pause for organizer confirmation",
                "   before opening the rest of the batch.",
            ]
        )
        next_step += 1
    lines.extend(
        [
            f"{next_step}. Use `{reviewer_packet_dir_path}` for per-unit context while",
            "   filling your reviewer working copy.",
            "",
            "Files in your package:",
            "",
            f"- protocol: `{protocol_path}`",
            f"- reviewer index: `{reviewer_index_path}`",
            f"- reviewer packet directory: `{reviewer_packet_dir_path}`",
            f"- assignment sidecar: `{reviewer_assignment_path}`",
            f"- working form copy: `{reviewer_form_path}`",
        ]
    )
    if truth_manifest_lookup_path and selected_truth_manifests_path:
        lines.extend(
            [
                f"- truth-manifest lookup: `{truth_manifest_lookup_path}`",
                f"- selected truth-manifest sidecars: `{selected_truth_manifests_path}`",
            ]
        )
    lines.extend(
        [
            "",
            "Please return only your completed reviewer-specific JSONL working copy.",
            "Do not rename columns, do not reorder rows, and do not edit the canonical",
            "master form.",
            "",
        ]
    )
    if truth_manifest_lookup_path and selected_truth_manifests_path:
        lines.extend(
            [
                "If packet metadata alone is insufficient, consult the supplied",
                "truth-manifest sidecars before scoring the unit.",
                "",
            ]
        )
    lines.extend(
        [
            "The scoring scale remains `0-3` per axis:",
            "",
            "- `0`: absent or wrong",
            "- `1`: partial",
            "- `2`: mostly correct",
            "- `3`: fully compliant",
            "",
            "Thanks.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_publication_annotation_adjudicator_launch_message(
    *,
    adjudicator_id: str,
    protocol_path: str,
    adjudicator_handoff_path: str,
    merged_forms_path: str,
    adjudication_shells_path: str,
    adjudication_queue_path: str,
    agreement_output_path: str,
    readiness_snapshot_path: str,
    post_review_inputs_ready: bool = True,
) -> str:
    lines: List[str] = [
        f"Subject: Publication-validation adjudication package for `{adjudicator_id}`",
        "",
        "Hi,",
        "",
        "I am sending the adjudication package for the current",
        "`Life-Science PaperWritingBench` publication-validation round.",
        "",
        "Please wait to begin until both reviewer JSONL copies have been returned,",
        "merged, and the organizer has refreshed this adjudicator bundle.",
        "",
    ]
    if not post_review_inputs_ready:
        lines.extend(
            [
                "This dispatch copy is not ready for adjudication yet.",
                "Use the refreshed adjudicator bundle only after organizer intake is complete.",
                "",
                "Current orientation files:",
                "",
                f"1. `{protocol_path}`",
                f"2. `{adjudicator_handoff_path}`",
                "",
                "Thanks.",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "When intake is complete, use these files in order:",
            "",
            f"1. `{protocol_path}`",
            f"2. `{adjudicator_handoff_path}`",
            f"3. `{merged_forms_path}`",
            f"4. `{adjudication_queue_path}`",
            f"5. `{adjudication_shells_path}`",
            "",
            "After adjudication, the expected refreshed outputs are:",
            "",
            f"- `{agreement_output_path}`",
            f"- `{readiness_snapshot_path}`",
            "",
            "Thanks.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_publication_annotation_adjudicator_handoff_markdown(
    *,
    batch_dir: str,
    protocol_path: str,
    merged_forms_path: str,
    judge_units_path: str,
    adjudication_shells_path: str,
    adjudication_queue_path: str,
    agreement_output_path: str,
    readiness_snapshot_path: str,
    validation_summary_path: str,
    matrix_summary_path: str,
    canary_summary_path: str,
    reviewer_ids: Sequence[str],
) -> str:
    reviewer_args = " ".join(reviewer_ids)
    lines: List[str] = [
        "# Publication Validation Adjudicator Handoff",
        "",
        f"- Batch directory: `{batch_dir}`",
        f"- Protocol: `{protocol_path}`",
        f"- Reviewer ids: {', '.join(f'`{reviewer_id}`' for reviewer_id in reviewer_ids)}",
        "",
        "## Inputs",
        "",
        f"- Frozen judge units: `{judge_units_path}`",
        f"- Merged reviewer forms: `{merged_forms_path}`",
        f"- Adjudication shells: `{adjudication_shells_path}`",
        "",
        "## Queue Build",
        "",
        "```bash",
        "PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-judge-adjudication-queue \\",
        f"  --judge-units {judge_units_path} \\",
        f"  --forms {merged_forms_path} \\",
        f"  --adjudications {adjudication_shells_path} \\",
        f"  --reviewers {reviewer_args} \\",
        f"  --output {adjudication_queue_path}",
        "```",
        "",
        "## Adjudicator Task",
        "",
        f"- review disagreements listed in `{adjudication_queue_path}`",
        f"- fill `final_rubric_labels` in `{adjudication_shells_path}`",
        "- set `finalized = true` for resolved units",
        "- add short rationale when the disagreement is non-trivial",
        "",
        "## After Adjudication",
        "",
        "```bash",
        "PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-judge-agreement \\",
        f"  --judge-units {judge_units_path} \\",
        f"  --forms {merged_forms_path} \\",
        f"  --adjudications {adjudication_shells_path} \\",
        f"  --output {agreement_output_path}",
        "",
        "PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-publication-readiness \\",
        f"  --matrix-summary {matrix_summary_path} \\",
        f"  --canary-summary {canary_summary_path} \\",
        f"  --validation-summary {validation_summary_path} \\",
        f"  --agreement-metrics {agreement_output_path} \\",
        f"  --output {readiness_snapshot_path}",
        "```",
        "",
        "## Expected Outputs",
        "",
        f"- `{adjudication_queue_path}`",
        f"- `{agreement_output_path}`",
        f"- `{readiness_snapshot_path}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def audit_publication_annotation_hold(
    *,
    batch_dir: str,
    task_bundles: Sequence[TaskBundle],
    selected_task_bundles: Sequence[TaskBundle],
    judge_units: Sequence[JudgeValidationUnit],
    forms: Sequence[JudgeReviewForm],
    adjudications: Sequence[JudgeAdjudicationRecord],
    packets: Sequence[PublicationAnnotationPacket],
    reviewer_ids: Sequence[str],
) -> PublicationAnnotationHoldAuditReport:
    expected_total = _expected_publication_total()
    reviewer_ids = tuple(reviewer_ids)
    merged_forms = merge_judge_review_forms(forms)
    slice_audit = audit_judge_validation_slice(
        task_bundles=task_bundles,
        judge_units=judge_units,
        minimum_total=len(judge_units),
    )
    packet_summary = summarize_publication_annotation_packets(
        packets,
        judge_units=judge_units,
        reviewer_ids=reviewer_ids,
    )
    expected_pairs = {
        _pair_key(unit.validation_unit_id, reviewer_id)
        for unit in judge_units
        for reviewer_id in reviewer_ids
    }
    form_pairs = {_pair_key(form.validation_unit_id, form.reviewer_id) for form in merged_forms}
    packet_pairs = {_pair_key(packet.validation_unit_id, packet.reviewer_id) for packet in packets}
    missing_form_pairs = tuple(sorted(expected_pairs - form_pairs))
    unexpected_form_pairs = tuple(sorted(form_pairs - expected_pairs))
    missing_packet_pairs = tuple(sorted(expected_pairs - packet_pairs))
    unexpected_packet_pairs = tuple(sorted(packet_pairs - expected_pairs))

    selected_task_bundle_ids = {bundle.task_bundle_id for bundle in selected_task_bundles}
    judge_task_bundle_ids = {unit.task_bundle_id for unit in judge_units}
    missing_selected_task_bundle_ids = tuple(sorted(selected_task_bundle_ids - judge_task_bundle_ids))
    unexpected_selected_task_bundle_ids = tuple(sorted(judge_task_bundle_ids - selected_task_bundle_ids))

    adjudication_ids = {record.validation_unit_id for record in adjudications}
    expected_validation_unit_ids = {unit.validation_unit_id for unit in judge_units}
    missing_adjudication_validation_unit_ids = tuple(sorted(expected_validation_unit_ids - adjudication_ids))
    unexpected_adjudication_validation_unit_ids = tuple(sorted(adjudication_ids - expected_validation_unit_ids))

    rubric_versions = tuple(sorted({unit.rubric_version for unit in judge_units}))
    adjudicator_ids = tuple(sorted({record.adjudicator_id for record in adjudications if record.adjudicator_id}))
    selection_locked = (
        len(judge_units) == expected_total
        and not slice_audit.duplicate_validation_unit_ids
        and not slice_audit.duplicate_task_bundle_ids
        and not missing_selected_task_bundle_ids
        and not unexpected_selected_task_bundle_ids
        and all(unit.frozen for unit in judge_units)
        and all(PUBLICATION_SELECTION_LOCK_NOTE in unit.notes for unit in judge_units)
    )
    form_axis_mismatches = []
    unit_lookup = {unit.validation_unit_id: unit for unit in judge_units}
    for form in merged_forms:
        unit = unit_lookup.get(form.validation_unit_id)
        if unit is None:
            continue
        if set(form.rubric_labels) != set(unit.rubric_labels):
            form_axis_mismatches.append(_pair_key(form.validation_unit_id, form.reviewer_id))
    adjudication_axis_mismatches = []
    for record in adjudications:
        unit = unit_lookup.get(record.validation_unit_id)
        if unit is None:
            continue
        if set(record.final_rubric_labels) != set(unit.rubric_labels):
            adjudication_axis_mismatches.append(record.validation_unit_id)
    rubric_locked = (
        len(rubric_versions) == 1
        and all(PUBLICATION_RUBRIC_LOCK_NOTE in unit.notes for unit in judge_units)
        and not form_axis_mismatches
        and not adjudication_axis_mismatches
    )
    reviewer_assignments_complete = not missing_form_pairs and not unexpected_form_pairs
    authoritative_sidecars_present = (
        reviewer_assignments_complete
        and not missing_adjudication_validation_unit_ids
        and not unexpected_adjudication_validation_unit_ids
    )
    structurally_ready = (
        selection_locked
        and rubric_locked
        and reviewer_assignments_complete
        and packet_summary.packet_coverage_complete
        and packet_summary.authoritative_form_coverage_complete
        and authoritative_sidecars_present
        and not missing_packet_pairs
        and not unexpected_packet_pairs
        and not packet_summary.duplicate_packet_ids
    )
    progress = summarize_judge_progress(
        judge_units,
        merged_forms,
        adjudications,
        reviewer_ids=reviewer_ids,
    )
    awaiting_human_review = structurally_ready and (
        progress["review_slots_completed"] < progress["review_slots_total"]
    )
    issues: List[str] = []
    if len(judge_units) != expected_total:
        issues.append(
            f"expected frozen publication batch to contain {expected_total} judge units, found {len(judge_units)}"
        )
    if not selection_locked:
        issues.append("publication selection lock is incomplete")
    if not rubric_locked:
        issues.append("publication rubric lock is incomplete")
    if missing_form_pairs:
        issues.append(f"missing authoritative judge_review_forms for {len(missing_form_pairs)} unit/reviewer pairs")
    if unexpected_form_pairs:
        issues.append(f"unexpected judge_review_forms present for {len(unexpected_form_pairs)} unit/reviewer pairs")
    if missing_packet_pairs:
        issues.append(f"missing markdown packets for {len(missing_packet_pairs)} unit/reviewer pairs")
    if unexpected_packet_pairs:
        issues.append(f"unexpected markdown packets present for {len(unexpected_packet_pairs)} unit/reviewer pairs")
    if missing_adjudication_validation_unit_ids:
        issues.append(
            f"missing adjudication shells for {len(missing_adjudication_validation_unit_ids)} validation units"
        )
    if unexpected_adjudication_validation_unit_ids:
        issues.append(
            f"unexpected adjudication shells present for {len(unexpected_adjudication_validation_unit_ids)} validation units"
        )
    if form_axis_mismatches:
        issues.append(f"rubric-axis drift detected in {len(form_axis_mismatches)} reviewer forms")
    if adjudication_axis_mismatches:
        issues.append(f"rubric-axis drift detected in {len(adjudication_axis_mismatches)} adjudication shells")
    issues.extend(packet_summary.issues)
    return PublicationAnnotationHoldAuditReport(
        generated_at=_utc_timestamp(),
        batch_dir=batch_dir,
        total_judge_units=len(judge_units),
        reviewer_ids=reviewer_ids,
        adjudicator_ids=adjudicator_ids,
        rubric_versions=rubric_versions,
        selection_locked=selection_locked,
        rubric_locked=rubric_locked,
        reviewer_assignments_complete=reviewer_assignments_complete,
        packet_coverage_complete=packet_summary.packet_coverage_complete
        and packet_summary.authoritative_form_coverage_complete,
        authoritative_sidecars_present=authoritative_sidecars_present,
        structurally_ready=structurally_ready,
        awaiting_human_review=awaiting_human_review,
        review_completion_rate=float(progress["review_completion_rate"]),
        finalized_adjudications=int(progress["finalized_adjudications"]),
        queue_status_counts=dict(progress["queue_status_counts"]),
        reviewer_assignment_counts=dict(packet_summary.reviewer_assignment_counts),
        duplicate_validation_unit_ids=slice_audit.duplicate_validation_unit_ids,
        duplicate_task_bundle_ids=slice_audit.duplicate_task_bundle_ids,
        duplicate_packet_ids=packet_summary.duplicate_packet_ids,
        missing_selected_task_bundle_ids=missing_selected_task_bundle_ids,
        unexpected_selected_task_bundle_ids=unexpected_selected_task_bundle_ids,
        missing_form_pairs=missing_form_pairs,
        unexpected_form_pairs=unexpected_form_pairs,
        missing_packet_pairs=missing_packet_pairs,
        unexpected_packet_pairs=unexpected_packet_pairs,
        missing_adjudication_validation_unit_ids=missing_adjudication_validation_unit_ids,
        unexpected_adjudication_validation_unit_ids=unexpected_adjudication_validation_unit_ids,
        issues=tuple(issues),
        ok=structurally_ready,
    )


def render_publication_annotation_hold_markdown(
    report: PublicationAnnotationHoldAuditReport,
) -> str:
    lines: List[str] = [
        "# Publication Annotation Hold Audit",
        "",
        f"- Batch directory: `{report.batch_dir}`",
        f"- Total judge units: `{report.total_judge_units}`",
        f"- Selection locked: `{'yes' if report.selection_locked else 'no'}`",
        f"- Rubric locked: `{'yes' if report.rubric_locked else 'no'}`",
        f"- Reviewer assignments complete: `{'yes' if report.reviewer_assignments_complete else 'no'}`",
        f"- Packet coverage complete: `{'yes' if report.packet_coverage_complete else 'no'}`",
        f"- Authoritative sidecars present: `{'yes' if report.authoritative_sidecars_present else 'no'}`",
        f"- Structurally ready: `{'yes' if report.structurally_ready else 'no'}`",
        f"- Awaiting human review: `{'yes' if report.awaiting_human_review else 'no'}`",
        f"- Review completion rate: `{report.review_completion_rate:.3f}`",
        f"- Finalized adjudications: `{report.finalized_adjudications}`",
        "",
        "## Reviewer Assignment Counts",
        "",
    ]
    for reviewer_id in report.reviewer_ids:
        lines.append(f"- `{reviewer_id}`: `{report.reviewer_assignment_counts.get(reviewer_id, 0)}`")
    lines.extend(["", "## Queue Status Counts", ""])
    for status, count in sorted(report.queue_status_counts.items()):
        lines.append(f"- `{status}`: `{count}`")
    if report.issues:
        lines.extend(["", "## Issues", ""])
        for issue in report.issues:
            lines.append(f"- {issue}")
    return "\n".join(lines).rstrip() + "\n"
