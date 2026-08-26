from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence

from .io import (
    adjudication_queue_entry_from_dict,
    adjudicated_paper_review_record_from_dict,
    auto_aggregated_paper_review_record_from_dict,
    auto_review_evidence_enrichment_record_from_dict,
    auto_panel_vote_from_dict,
    auto_qualification_record_from_dict,
    auto_review_recovery_batch_entry_from_dict,
    auto_review_source_bundle_from_dict,
    answer_record_from_dict,
    api_fetch_record_from_dict,
    collection_batch_spec_from_dict,
    collection_candidate_record_from_dict,
    assertion_record_from_dict,
    baseline_run_spec_from_dict,
    benchmark_unit_decision_record_from_dict,
    benchmark_unit_from_dict,
    evidence_extraction_record_from_dict,
    evidence_record_from_dict,
    execution_profile_from_dict,
    evaluation_record_from_dict,
    evaluation_extraction_audit_report_from_dict,
    load_jsonl,
    evidence_unit_from_dict,
    ingestion_record_from_dict,
    judge_adjudication_queue_entry_from_dict,
    judge_adjudication_record_from_dict,
    judge_review_form_from_dict,
    judge_slice_audit_report_from_dict,
    judge_validation_unit_from_dict,
    maintenance_log_entry_from_dict,
    metadata_governance_hint_from_dict,
    metadata_source_record_from_dict,
    observation_record_from_dict,
    paper_packaging_review_record_from_dict,
    paper_review_adjudication_record_from_dict,
    paper_review_batch_entry_from_dict,
    paper_review_packet_from_dict,
    paper_reviewer_handoff_report_from_dict,
    paper_reviewer_assignment_from_dict,
    paper_qualification_batch_report_from_dict,
    paper_qualification_record_from_dict,
    paper_review_progress_summary_from_dict,
    paper_review_queue_entry_from_dict,
    paper_qualification_record_from_dict,
    paper_scientific_review_form_from_dict,
    paper_writing_review_form_from_dict,
    paper_qualification_decision_from_dict,
    pilot_adjudication_record_from_dict,
    pilot_calibration_spec_from_dict,
    pilot_review_form_from_dict,
    question_record_from_dict,
    shadow_inspection_batch_report_from_dict,
    shadow_inspection_entry_from_dict,
    shadow_inspection_taxonomy_report_from_dict,
    source_paper_from_dict,
    submission_record_from_dict,
    task_bundle_from_dict,
    truth_manifest_from_dict,
    source_quality_record_from_dict,
    write_jsonl,
)
from .collection import (
    DEFAULT_COLLECTION_BATCH_ID,
    audit_collection_batch,
    build_collection_batch,
    enrich_candidates_with_crossref,
    enrich_candidates_with_europepmc,
    fetch_pubmed_batch,
    merge_collection_candidates,
    rank_collection_candidates,
    shortlist_collection_candidates,
)
from .auto_review import (
    aggregate_auto_paper_reviews,
    audit_auto_review_source_bundles,
    build_auto_paper_qualification_records,
    build_auto_review_source_bundles,
    run_auto_paper_reviews,
    summarize_auto_review_batch,
)
from .evidence_enrichment import (
    audit_auto_review_evidence_enrichments,
    build_auto_review_evidence_enrichments,
    materialize_enriched_source_papers,
)
from .execution import (
    build_auto_review_recovery_job_spec,
    build_baseline_replay_job_spec,
    build_cayuga_execution_profile,
    default_execution_profile,
    render_execution_job_script,
)
from .baselines import evaluate_submissions, run_baseline
from .extraction import (
    build_evaluation_extraction_artifacts,
    build_parser_assisted_extraction_drafts,
    build_extraction_records,
    build_truth_manifest_from_extractions,
    freeze_truth_manifest,
    verify_truth_manifest,
)
from .ingestion import (
    audit_ingestion_artifacts,
    ingest_metadata_records,
    normalize_metadata_records,
    verify_ingestion_artifacts,
)
from .metadata_hints import suggest_governance_metadata_hints
from .paper_review import (
    build_paper_review_batch_entries,
    build_paper_review_batch_report,
    build_paper_review_packet_report,
    build_paper_review_packets,
    build_paper_scientific_review_forms,
    build_paper_writing_review_forms,
)
from .paper_review_flow import (
    build_paper_reviewer_assignments,
    build_paper_review_adjudication_shells,
    build_paper_review_queue,
    build_paper_reviewer_handoff_report,
    build_paper_review_workload_report,
    finalize_paper_adjudications,
    merge_paper_scientific_review_forms,
    merge_paper_writing_review_forms,
    render_paper_reviewer_handoff_markdown,
    summarize_paper_review_progress,
)
from .paper_qualification_flow import (
    build_packaging_review_priors,
    build_paper_qualification_batch_report,
    build_paper_qualification_records,
)
from .judge import (
    audit_judge_validation_slice,
    audit_llm_judge_alignment,
    build_judge_validation_slice,
    build_judge_validation_units,
    render_llm_judge_alignment_markdown,
)
from .judgeflow import (
    build_judge_adjudication_queue,
    build_judge_adjudication_shells,
    build_judge_review_forms,
    finalize_judge_validation_units,
    merge_judge_review_forms,
    summarize_judge_progress,
)
from .inspection import (
    build_shadow_inspection_batch,
    build_shadow_inspection_taxonomy,
    compare_shadow_inspection_reports,
    render_shadow_inspection_markdown,
    render_shadow_inspection_taxonomy_markdown,
    summarize_shadow_inspection_batch,
    summarize_shadow_inspection_taxonomy,
)
from .program import (
    build_baseline_run_inventory,
    build_maintenance_log_entry,
    initialize_knowledge_base_layout,
    summarize_program_progress,
)
from .release import (
    BUNDLE_VERIFY_REPORT_FILENAME,
    ReleaseIndexEntry,
    build_release_index,
    build_release_manifest_bundle,
    render_release_bundle_artifacts,
    verify_release_bundle_directory,
)
from .reviewflow import (
    build_adjudication_queue,
    build_pilot_adjudication_shells,
    build_pilot_review_forms,
    compute_agreement_against_adjudication,
    merge_review_forms,
    summarize_calibration_progress,
    validate_pilot_agreement_thresholds,
)
from .recovery import (
    build_auto_review_recovery_batch,
    build_auto_review_recovery_batch_report,
    select_recovery_batch_packaging_reviews,
    select_recovery_batch_papers,
)
from .calibration import (
    audit_calibration_drift,
    build_full_calibration_scaffold,
    pilot_coverage_summary,
    validate_calibration_set,
    validate_full_calibration_set,
    validate_pilot_calibration_set,
)
from .tasking import (
    annotate_task_bundles_with_release_index,
    build_benchmark_unit_decisions_from_auto_qualifications,
    build_benchmark_units_from_evidence_units,
    build_evaluation_task_bundles,
    build_task_bundles,
    build_truth_manifest_bundle,
    select_judge_candidate_task_bundles,
    summarize_judge_candidate_selection,
    summarize_task_bundles,
)
from .policy import BaselineKind, DomainOutcome, PackagingDomain, ReleaseTier, TaskFamily


def _write_json(path: str, payload: Mapping[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _read_json(path: str) -> Mapping[str, object]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_bytes(path: str, payload: bytes) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)


def _write_text(path: str, payload: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload, encoding="utf-8")


def _print_json(payload: Mapping[str, object]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _load_json_object(path: str) -> Mapping[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_json_or_jsonl_records(path: str) -> Sequence[Mapping[str, object]]:
    if path.endswith(".jsonl"):
        return tuple(load_jsonl(path))
    payload = _load_json_object(path)
    if isinstance(payload, list):
        return tuple(payload)
    return (payload,)


def _load_program_progress_decisions(path: str) -> Sequence[object]:
    raw_records = _load_json_or_jsonl_records(path)
    decisions = []
    for record in raw_records:
        if "decision" in record:
            if any(
                key in record
                for key in ("review_origin", "auto_release_cap_reason", "judge_validation_ready")
            ):
                decisions.append(auto_qualification_record_from_dict(dict(record)).decision)
            else:
                decisions.append(paper_qualification_record_from_dict(dict(record)).decision)
        else:
            decisions.append(paper_qualification_decision_from_dict(dict(record)))
    return tuple(decisions)


def _load_baseline_run_specs_from_paths(paths: Sequence[str]):
    baseline_runs = []
    for path in paths:
        for record in _load_json_or_jsonl_records(path):
            baseline_runs.append(baseline_run_spec_from_dict(dict(record)))
    return build_baseline_run_inventory(tuple(baseline_runs))


def _safe_filename_token(value: str) -> str:
    token = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value.strip())
    return token or "reviewer"


def command_validate_pilot(args: argparse.Namespace) -> int:
    specs = load_jsonl(args.manifest, loader=pilot_calibration_spec_from_dict)
    summary = pilot_coverage_summary(specs)
    issues = validate_pilot_calibration_set(specs)
    payload = {
        "summary": summary,
        "issues": list(issues),
        "ok": not issues,
    }
    if args.output:
        _write_json(args.output, payload)
    _print_json(payload)
    return 0 if not issues else 1


def command_validate_calibration(args: argparse.Namespace) -> int:
    specs = load_jsonl(args.manifest, loader=pilot_calibration_spec_from_dict)
    summary = pilot_coverage_summary(specs)
    if args.mode == "pilot":
        issues = validate_pilot_calibration_set(specs)
    elif args.mode == "full":
        issues = validate_full_calibration_set(specs)
    else:
        issues = validate_calibration_set(
            specs,
            minimum_total=args.minimum_total,
            minimum_per_study_class=args.minimum_per_study_class,
            minimum_hybrid=args.minimum_hybrid,
            minimum_quarantine=args.minimum_quarantine,
            minimum_controlled_access=args.minimum_controlled_access,
            minimum_negative_or_descriptive=args.minimum_negative_or_descriptive,
        )
    payload = {
        "summary": summary,
        "issues": list(issues),
        "ok": not issues,
        "mode": args.mode,
    }
    if args.output:
        _write_json(args.output, payload)
    _print_json(payload)
    return 0 if not issues else 1


def command_write_full_calibration_scaffold(args: argparse.Namespace) -> int:
    specs = build_full_calibration_scaffold(prefix=args.prefix)
    write_jsonl(args.output, specs)
    summary = pilot_coverage_summary(specs)
    payload = {
        "output": args.output,
        "specs_written": len(specs),
        "prefix": args.prefix,
        "summary": summary,
    }
    if args.summary_output:
        _write_json(args.summary_output, summary)
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_init_knowledge_base(args: argparse.Namespace) -> int:
    created_paths = initialize_knowledge_base_layout(args.root)
    root = Path(args.root)
    _write_text(
        str(root / "README.md"),
        "# Knowledge Base\n\nThis directory stores raw, normalized, enriched, qualified, and released benchmark artifacts.\n",
    )
    for subdirectory in ("raw", "normalized", "enriched", "qualified", "released"):
        _write_text(
            str(root / subdirectory / "README.md"),
            f"# {subdirectory}\n\nThis directory is reserved for `{subdirectory}` benchmark-knowledge artifacts.\n",
        )
    payload = {
        "root": args.root,
        "paths_initialized": len(created_paths),
    }
    _print_json(payload)
    return 0


def command_build_collection_batch(args: argparse.Namespace) -> int:
    batch_spec = build_collection_batch(
        batch_id=args.batch_id,
        year_start=args.year_start,
        year_end=args.year_end,
        primary_retmax=args.primary_retmax,
        reserve_retmax=args.reserve_retmax,
        target_candidates_per_class=args.target_candidates_per_class,
    )
    _write_json(args.output, batch_spec.to_dict())
    payload = {
        "batch_id": batch_spec.batch_id,
        "output": args.output,
        "query_specs": len(batch_spec.query_specs),
    }
    if args.queries_output:
        write_jsonl(args.queries_output, batch_spec.query_specs)
        payload["queries_output"] = args.queries_output
    _print_json(payload)
    return 0


def command_fetch_pubmed_batch(args: argparse.Namespace) -> int:
    batch_spec = collection_batch_spec_from_dict(dict(_load_json_object(args.batch_spec)))
    records = fetch_pubmed_batch(
        batch_spec,
        args.raw_dir,
        refresh=args.refresh,
    )
    write_jsonl(args.output, records)
    payload = {
        "batch_id": batch_spec.batch_id,
        "fetch_records_written": len(records),
        "output": args.output,
        "raw_dir": args.raw_dir,
    }
    if args.summary_output:
        summary = {
            "batch_id": batch_spec.batch_id,
            "query_count": len(batch_spec.query_specs),
            "fetch_records_written": len(records),
            "study_class_counts": {},
            "lane_counts": {},
        }
        for record in records:
            summary["study_class_counts"][record.study_class.value] = (
                summary["study_class_counts"].get(record.study_class.value, 0) + 1
            )
            summary["lane_counts"][record.lane] = summary["lane_counts"].get(record.lane, 0) + 1
        _write_json(args.summary_output, summary)
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_merge_collection_candidates(args: argparse.Namespace) -> int:
    fetch_records = load_jsonl(args.input, loader=api_fetch_record_from_dict)
    candidates = merge_collection_candidates(fetch_records)
    write_jsonl(args.output, candidates)
    payload = {
        "fetch_records_loaded": len(fetch_records),
        "candidates_written": len(candidates),
        "output": args.output,
    }
    if args.summary_output:
        summary = {
            "fetch_records_loaded": len(fetch_records),
            "candidates_written": len(candidates),
            "multi_class_candidates": sum(1 for candidate in candidates if len(candidate.study_class_votes) > 1),
        }
        _write_json(args.summary_output, summary)
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_fetch_europepmc_enrichment(args: argparse.Namespace) -> int:
    candidates = load_jsonl(args.input, loader=collection_candidate_record_from_dict)
    enriched_candidates, fetch_records = enrich_candidates_with_europepmc(
        candidates,
        args.raw_dir,
        refresh=args.refresh,
    )
    write_jsonl(args.output, enriched_candidates)
    if args.fetch_records_output:
        write_jsonl(args.fetch_records_output, fetch_records)
    payload = {
        "input_candidates": len(candidates),
        "enriched_candidates_written": len(enriched_candidates),
        "fetch_records_written": len(fetch_records),
        "output": args.output,
        "raw_dir": args.raw_dir,
    }
    if args.fetch_records_output:
        payload["fetch_records_output"] = args.fetch_records_output
    if args.summary_output:
        summary = {
            "input_candidates": len(candidates),
            "enriched_candidates_written": len(enriched_candidates),
            "fetch_records_written": len(fetch_records),
            "oa_fulltext_available_count": sum(
                1 for candidate in enriched_candidates if candidate.oa_fulltext_available
            ),
            "pmcid_count": sum(1 for candidate in enriched_candidates if candidate.pmcid),
        }
        _write_json(args.summary_output, summary)
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_fetch_crossref_enrichment(args: argparse.Namespace) -> int:
    candidates = load_jsonl(args.input, loader=collection_candidate_record_from_dict)
    enriched_candidates, fetch_records = enrich_candidates_with_crossref(
        candidates,
        args.raw_dir,
        refresh=args.refresh,
    )
    write_jsonl(args.output, enriched_candidates)
    if args.fetch_records_output:
        write_jsonl(args.fetch_records_output, fetch_records)
    payload = {
        "input_candidates": len(candidates),
        "enriched_candidates_written": len(enriched_candidates),
        "fetch_records_written": len(fetch_records),
        "output": args.output,
        "raw_dir": args.raw_dir,
    }
    if args.fetch_records_output:
        payload["fetch_records_output"] = args.fetch_records_output
    if args.summary_output:
        summary = {
            "input_candidates": len(candidates),
            "enriched_candidates_written": len(enriched_candidates),
            "fetch_records_written": len(fetch_records),
            "open_license_count": sum(
                1
                for candidate in enriched_candidates
                if candidate.license and "creativecommons.org/licenses/" in candidate.license.lower()
            ),
            "crossmark_update_count": sum(
                1 for candidate in enriched_candidates if candidate.crossmark_updates
            ),
        }
        _write_json(args.summary_output, summary)
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_rank_collection_candidates(args: argparse.Namespace) -> int:
    candidates = load_jsonl(args.input, loader=collection_candidate_record_from_dict)
    ranked = rank_collection_candidates(candidates)
    write_jsonl(args.output, ranked)
    payload = {
        "input_candidates": len(candidates),
        "ranked_candidates_written": len(ranked),
        "output": args.output,
    }
    if args.summary_output:
        summary = {
            "input_candidates": len(candidates),
            "ranked_candidates_written": len(ranked),
            "top_candidate_ids": [candidate.candidate_id for candidate in ranked[:10]],
        }
        _write_json(args.summary_output, summary)
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_shortlist_collection_candidates(args: argparse.Namespace) -> int:
    candidates = load_jsonl(args.input, loader=collection_candidate_record_from_dict)
    shortlisted, metadata_records, report = shortlist_collection_candidates(
        candidates,
        target_candidates_per_class=args.target_per_class,
        batch_id=args.batch_id,
    )
    write_jsonl(args.output, shortlisted)
    write_jsonl(args.metadata_output, metadata_records)
    payload = {
        "input_candidates": len(candidates),
        "shortlisted_candidates_written": len(shortlisted),
        "metadata_records_written": len(metadata_records),
        "output": args.output,
        "metadata_output": args.metadata_output,
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_audit_collection_batch(args: argparse.Namespace) -> int:
    batch_spec = collection_batch_spec_from_dict(dict(_load_json_object(args.batch_spec)))
    candidates = load_jsonl(args.candidates, loader=collection_candidate_record_from_dict)
    shortlisted_candidates = (
        load_jsonl(args.shortlisted_candidates, loader=collection_candidate_record_from_dict)
        if args.shortlisted_candidates
        else []
    )
    releaseability_records = (
        load_jsonl(args.ingestion_records, loader=ingestion_record_from_dict)
        if args.ingestion_records
        else []
    )
    report = audit_collection_batch(
        batch_spec,
        candidates,
        shortlisted_candidates=shortlisted_candidates,
        releaseability_records=releaseability_records,
        total_raw_fetch_records=args.total_raw_fetch_records,
    )
    if args.output:
        _write_json(args.output, report.to_dict())
    _print_json(report.to_dict())
    return 0


def command_ingest_metadata(args: argparse.Namespace) -> int:
    raw_records = load_jsonl(args.input)
    records = ingest_metadata_records(raw_records, default_source_name=args.source_name)
    write_jsonl(args.output, records)
    payload = {
        "raw_records": len(raw_records),
        "standardized_records": len(records),
        "output": args.output,
    }
    if args.summary_output:
        source_counts: Dict[str, int] = {}
        for record in records:
            source_counts[record.source_name] = source_counts.get(record.source_name, 0) + 1
        _write_json(
            args.summary_output,
            {
                "raw_records": len(raw_records),
                "standardized_records": len(records),
                "source_counts": source_counts,
            },
        )
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_normalize_papers(args: argparse.Namespace) -> int:
    records = load_jsonl(args.input, loader=metadata_source_record_from_dict)
    papers, ingestion_records, audit = normalize_metadata_records(records)
    write_jsonl(args.papers_output, papers)
    write_jsonl(args.ingestion_output, ingestion_records)
    if args.audit_output:
        _write_json(args.audit_output, audit.to_dict())
    payload = {
        "source_records": len(records),
        "normalized_papers": len(papers),
        "ingestion_records_written": len(ingestion_records),
        "papers_output": args.papers_output,
        "ingestion_output": args.ingestion_output,
    }
    if args.audit_output:
        payload["audit_output"] = args.audit_output
    _print_json(payload)
    return 0


def command_audit_ingestion(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    ingestion_records = load_jsonl(args.ingestion_records, loader=ingestion_record_from_dict)
    report = audit_ingestion_artifacts(papers, ingestion_records)
    if args.output:
        _write_json(args.output, report.to_dict())
    _print_json(report.to_dict())
    return 0


def command_verify_ingestion(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    ingestion_records = load_jsonl(args.ingestion_records, loader=ingestion_record_from_dict)
    report = verify_ingestion_artifacts(papers, ingestion_records)
    if args.output:
        _write_json(args.output, report.to_dict())
    _print_json(report.to_dict())
    return 0 if report.ok else 1


def command_write_execution_profile(args: argparse.Namespace) -> int:
    if args.profile == "cayuga":
        if not args.cayuga_root:
            raise ValueError("--cayuga-root is required for the cayuga execution profile")
        profile = build_cayuga_execution_profile(
            cayuga_root=args.cayuga_root,
            repo_root=args.repo_root,
            working_directory_name=args.working_directory_name,
            python_bin=args.python_bin,
        )
    else:
        profile = default_execution_profile(
            repo_root=args.repo_root,
            python_bin=args.python_bin,
            working_directory=args.working_directory,
        )
    _write_json(args.output, profile.to_dict())
    payload = {
        "profile": profile.profile_name,
        "backend": profile.backend,
        "output": args.output,
    }
    _print_json(payload)
    return 0


def command_write_baseline_replay_job(args: argparse.Namespace) -> int:
    profile = execution_profile_from_dict(json.loads(Path(args.execution_profile).read_text(encoding="utf-8")))
    baseline_kind = BaselineKind(args.baseline_kind)
    job_spec = build_baseline_replay_job_spec(
        profile,
        task_bundles_path=args.task_bundles,
        baseline_kind=baseline_kind,
        output_dir=args.output_dir,
        producer_id=args.producer_id,
        job_name=args.job_name,
    )
    script_text = render_execution_job_script(job_spec, profile)
    script_path = Path(args.script_output)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(script_text, encoding="utf-8")
    script_path.chmod(0o755)
    _write_json(args.spec_output, job_spec.to_dict())
    payload = {
        "job_id": job_spec.job_id,
        "job_name": job_spec.job_name,
        "backend": job_spec.backend,
        "execution_profile": args.execution_profile,
        "script_output": args.script_output,
        "spec_output": args.spec_output,
        "output_dir": args.output_dir,
        "baseline_kind": baseline_kind.value,
    }
    _print_json(payload)
    return 0


def command_build_parser_assisted_extraction(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    evidence_units, extraction_specs, report = build_parser_assisted_extraction_drafts(
        papers,
        max_assertions_per_unit=args.max_assertions_per_unit,
    )
    write_jsonl(args.evidence_units_output, evidence_units)
    write_jsonl(args.specs_output, extraction_specs)
    payload = {
        "papers_processed": len(papers),
        "evidence_units_written": len(evidence_units),
        "extraction_specs_written": len(extraction_specs),
        "evidence_units_output": args.evidence_units_output,
        "specs_output": args.specs_output,
    }
    if args.audit_output:
        _write_json(args.audit_output, report.to_dict())
        payload["audit_output"] = args.audit_output
    _print_json(payload)
    return 0


def command_build_evaluation_extraction(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    evidence_units = load_jsonl(args.evidence_units, loader=evidence_unit_from_dict)
    extraction_specs = load_jsonl(args.specs)
    observations, questions, answers, quality_records, report = build_evaluation_extraction_artifacts(
        source_papers=papers,
        evidence_units=evidence_units,
        extraction_specs=extraction_specs,
        max_questions_per_unit=args.max_questions_per_unit,
    )
    write_jsonl(args.observations_output, observations)
    write_jsonl(args.questions_output, questions)
    write_jsonl(args.answers_output, answers)
    write_jsonl(args.source_quality_output, quality_records)
    payload = {
        "papers_processed": len(papers),
        "observations_written": len(observations),
        "questions_written": len(questions),
        "answers_written": len(answers),
        "source_quality_written": len(quality_records),
        "observations_output": args.observations_output,
        "questions_output": args.questions_output,
        "answers_output": args.answers_output,
        "source_quality_output": args.source_quality_output,
    }
    if args.audit_output:
        _write_json(args.audit_output, report.to_dict())
        payload["audit_output"] = args.audit_output
    _print_json(payload)
    return 0


def command_extract_evidence_records(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    evidence_units = load_jsonl(args.evidence_units, loader=evidence_unit_from_dict)
    extraction_specs = load_jsonl(args.input)
    paper_map = {paper.paper_id: paper for paper in papers}
    evidence_unit_map = {unit.unit_id: unit for unit in evidence_units}
    assertion_records, evidence_records, extraction_records, audit = build_extraction_records(
        source_papers=paper_map,
        evidence_units=evidence_unit_map,
        extraction_specs=extraction_specs,
        default_evidence_type=args.default_evidence_type,
    )
    write_jsonl(args.assertions_output, assertion_records)
    write_jsonl(args.evidence_records_output, evidence_records)
    write_jsonl(args.extractions_output, extraction_records)
    if args.audit_output:
        _write_json(args.audit_output, audit.to_dict())
    payload = {
        "assertions_written": len(assertion_records),
        "evidence_records_written": len(evidence_records),
        "extractions_written": len(extraction_records),
        "assertions_output": args.assertions_output,
        "evidence_records_output": args.evidence_records_output,
        "extractions_output": args.extractions_output,
    }
    if args.audit_output:
        payload["audit_output"] = args.audit_output
    _print_json(payload)
    return 0


def command_build_truth_manifests(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    evidence_units = load_jsonl(args.evidence_units, loader=evidence_unit_from_dict)
    assertion_records = load_jsonl(args.assertions, loader=assertion_record_from_dict)
    evidence_records = load_jsonl(args.evidence_records, loader=evidence_record_from_dict)
    extraction_records = load_jsonl(args.extractions, loader=evidence_extraction_record_from_dict)

    paper_map = {paper.paper_id: paper for paper in papers}
    evidence_by_paper: Dict[str, list] = {}
    for unit in evidence_units:
        evidence_by_paper.setdefault(unit.paper_id, []).append(unit)
    assertions_by_paper: Dict[str, list] = {}
    for record in assertion_records:
        assertions_by_paper.setdefault(record.paper_id, []).append(record)
    evidence_records_by_paper: Dict[str, list] = {}
    for record in evidence_records:
        evidence_records_by_paper.setdefault(record.paper_id, []).append(record)
    extractions_by_paper: Dict[str, list] = {}
    for record in extraction_records:
        extractions_by_paper.setdefault(record.paper_id, []).append(record)

    manifests = []
    for paper_id in sorted(extractions_by_paper):
        if paper_id not in paper_map:
            raise KeyError(f"missing source paper for manifest build: {paper_id}")
        manifests.append(
            build_truth_manifest_from_extractions(
                paper=paper_map[paper_id],
                evidence_units=tuple(evidence_by_paper.get(paper_id, ())),
                assertion_records=tuple(assertions_by_paper.get(paper_id, ())),
                evidence_records=tuple(evidence_records_by_paper.get(paper_id, ())),
                extraction_records=tuple(extractions_by_paper[paper_id]),
                caveats=tuple(args.caveat or ()),
            )
        )
    write_jsonl(args.output, manifests)
    _print_json(
        {
            "truth_manifests_written": len(manifests),
            "output": args.output,
        }
    )
    return 0


def command_freeze_truth_manifests(args: argparse.Namespace) -> int:
    manifests = load_jsonl(args.input, loader=truth_manifest_from_dict)
    frozen_manifests = tuple(
        freeze_truth_manifest(manifest, frozen_at=args.frozen_at)
        for manifest in manifests
    )
    write_jsonl(args.output, frozen_manifests)
    _print_json(
        {
            "input_manifests": len(manifests),
            "frozen_manifests": len(frozen_manifests),
            "output": args.output,
        }
    )
    return 0


def command_verify_truth_manifests(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    evidence_units = load_jsonl(args.evidence_units, loader=evidence_unit_from_dict)
    assertion_records = load_jsonl(args.assertions, loader=assertion_record_from_dict)
    evidence_records = load_jsonl(args.evidence_records, loader=evidence_record_from_dict)
    extraction_records = load_jsonl(args.extractions, loader=evidence_extraction_record_from_dict)
    manifests = load_jsonl(args.manifests, loader=truth_manifest_from_dict)

    paper_map = {paper.paper_id: paper for paper in papers}
    evidence_by_paper: Dict[str, list] = {}
    for unit in evidence_units:
        evidence_by_paper.setdefault(unit.paper_id, []).append(unit)
    assertions_by_paper: Dict[str, list] = {}
    for record in assertion_records:
        assertions_by_paper.setdefault(record.paper_id, []).append(record)
    evidence_records_by_paper: Dict[str, list] = {}
    for record in evidence_records:
        evidence_records_by_paper.setdefault(record.paper_id, []).append(record)
    extractions_by_paper: Dict[str, list] = {}
    for record in extraction_records:
        extractions_by_paper.setdefault(record.paper_id, []).append(record)

    reports = []
    for manifest in manifests:
        if manifest.paper_id not in paper_map:
            raise KeyError(f"missing source paper for truth-manifest verify: {manifest.paper_id}")
        reports.append(
            verify_truth_manifest(
                truth_manifest=manifest,
                paper=paper_map[manifest.paper_id],
                evidence_units=tuple(evidence_by_paper.get(manifest.paper_id, ())),
                assertion_records=tuple(assertions_by_paper.get(manifest.paper_id, ())),
                evidence_records=tuple(evidence_records_by_paper.get(manifest.paper_id, ())),
                extraction_records=tuple(extractions_by_paper.get(manifest.paper_id, ())),
            )
        )
    write_jsonl(args.output, reports)
    ok = all(report.ok for report in reports)
    _print_json(
        {
            "reports_written": len(reports),
            "ok": ok,
            "output": args.output,
        }
    )
    return 0 if ok else 1


def command_suggest_metadata_hints(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    hints = tuple(suggest_governance_metadata_hints(paper) for paper in papers)
    write_jsonl(args.output, hints)
    payload = {
        "papers_processed": len(papers),
        "hints_written": len(hints),
        "output": args.output,
    }
    if args.summary_output:
        warnings_count = sum(1 for hint in hints if hint.warnings)
        _write_json(
            args.summary_output,
            {
                "papers_processed": len(papers),
                "warnings_count": warnings_count,
                "warning_paper_ids": [hint.paper_id for hint in hints if hint.warnings],
            },
        )
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_build_paper_review_batch(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    metadata_hints = (
        load_jsonl(args.metadata_hints, loader=metadata_governance_hint_from_dict)
        if args.metadata_hints
        else []
    )
    entries = build_paper_review_batch_entries(
        papers=papers,
        metadata_hints=metadata_hints,
        batch_id=args.batch_id,
    )
    scientific_forms = build_paper_scientific_review_forms(entries, reviewer_ids=tuple(args.reviewers))
    writing_forms = build_paper_writing_review_forms(entries, reviewer_ids=tuple(args.reviewers))
    report = build_paper_review_batch_report(entries)
    write_jsonl(args.entries_output, entries)
    write_jsonl(args.scientific_forms_output, scientific_forms)
    write_jsonl(args.writing_forms_output, writing_forms)
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
    payload = {
        "batch_id": args.batch_id,
        "papers_loaded": len(papers),
        "entries_written": len(entries),
        "scientific_forms_written": len(scientific_forms),
        "writing_forms_written": len(writing_forms),
        "entries_output": args.entries_output,
        "scientific_forms_output": args.scientific_forms_output,
        "writing_forms_output": args.writing_forms_output,
    }
    if args.summary_output:
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_build_paper_review_packets(args: argparse.Namespace) -> int:
    entries = load_jsonl(args.entries, loader=paper_review_batch_entry_from_dict)
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    packaging_reviews = load_jsonl(args.packaging_reviews, loader=paper_packaging_review_record_from_dict)
    packets = build_paper_review_packets(
        entries=entries,
        papers=papers,
        packaging_review_records=packaging_reviews,
    )
    report = build_paper_review_packet_report(packets)
    write_jsonl(args.output, packets)
    payload = {
        "entries_loaded": len(entries),
        "papers_loaded": len(papers),
        "packaging_reviews_loaded": len(packaging_reviews),
        "packets_written": len(packets),
        "output": args.output,
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_build_paper_review_workloads(args: argparse.Namespace) -> int:
    packets = load_jsonl(args.packets, loader=paper_review_packet_from_dict)
    scientific_forms = load_jsonl(args.scientific_forms, loader=paper_scientific_review_form_from_dict)
    writing_forms = load_jsonl(args.writing_forms, loader=paper_writing_review_form_from_dict)
    assignments = build_paper_reviewer_assignments(
        packets=packets,
        scientific_forms=scientific_forms,
        writing_forms=writing_forms,
        reviewer_ids=tuple(args.reviewers),
    )
    report = build_paper_review_workload_report(assignments)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assignment_counts: Dict[str, int] = {}
    for reviewer_id in args.reviewers:
        reviewer_assignments = [
            assignment for assignment in assignments
            if assignment.reviewer_id == reviewer_id
        ]
        assignment_counts[reviewer_id] = len(reviewer_assignments)
        filename = f"{_safe_filename_token(reviewer_id)}_paper_review_assignments.jsonl"
        write_jsonl(str(output_dir / filename), reviewer_assignments)
    summary_path = output_dir / "paper_review_workload_summary.json"
    _write_json(str(summary_path), report.to_dict())
    payload = {
        "packets_loaded": len(packets),
        "scientific_forms_loaded": len(scientific_forms),
        "writing_forms_loaded": len(writing_forms),
        "assignment_counts": assignment_counts,
        "output_dir": str(output_dir),
        "summary_output": str(summary_path),
    }
    _print_json(payload)
    return 0


def command_build_paper_review_handoff(args: argparse.Namespace) -> int:
    assignments = []
    for path in args.assignments:
        assignments.extend(load_jsonl(path, loader=paper_reviewer_assignment_from_dict))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    handoff_counts: Dict[str, int] = {}
    for reviewer_id in args.reviewers:
        report = build_paper_reviewer_handoff_report(
            assignments=assignments,
            reviewer_id=reviewer_id,
            top_priority_count=args.top_priority_count,
        )
        markdown = render_paper_reviewer_handoff_markdown(
            assignments=assignments,
            reviewer_id=reviewer_id,
            top_priority_count=args.top_priority_count,
        )
        filename_prefix = _safe_filename_token(reviewer_id)
        _write_json(str(output_dir / f"{filename_prefix}_handoff_summary.json"), report.to_dict())
        _write_text(str(output_dir / f"{filename_prefix}_handoff.md"), markdown)
        handoff_counts[reviewer_id] = report.total_assignments
    payload = {
        "assignments_loaded": len(assignments),
        "handoff_counts": handoff_counts,
        "output_dir": str(output_dir),
    }
    _print_json(payload)
    return 0


def command_merge_paper_scientific_forms(args: argparse.Namespace) -> int:
    forms = []
    for path in args.inputs:
        forms.extend(load_jsonl(path, loader=paper_scientific_review_form_from_dict))
    merged = merge_paper_scientific_review_forms(forms)
    write_jsonl(args.output, merged)
    payload = {
        "inputs": list(args.inputs),
        "forms_loaded": len(forms),
        "forms_written": len(merged),
        "output": args.output,
    }
    _print_json(payload)
    return 0


def command_merge_paper_writing_forms(args: argparse.Namespace) -> int:
    forms = []
    for path in args.inputs:
        forms.extend(load_jsonl(path, loader=paper_writing_review_form_from_dict))
    merged = merge_paper_writing_review_forms(forms)
    write_jsonl(args.output, merged)
    payload = {
        "inputs": list(args.inputs),
        "forms_loaded": len(forms),
        "forms_written": len(merged),
        "output": args.output,
    }
    _print_json(payload)
    return 0


def command_build_paper_review_adjudication_shells(args: argparse.Namespace) -> int:
    entries = load_jsonl(args.entries, loader=paper_review_batch_entry_from_dict)
    adjudications = build_paper_review_adjudication_shells(
        entries,
        adjudicator_id=args.adjudicator,
        reviewer_ids=tuple(args.reviewers),
    )
    write_jsonl(args.output, adjudications)
    payload = {
        "entries_loaded": len(entries),
        "adjudications_written": len(adjudications),
        "output": args.output,
        "adjudicator": args.adjudicator,
    }
    _print_json(payload)
    return 0


def command_build_paper_review_queue(args: argparse.Namespace) -> int:
    entries = load_jsonl(args.entries, loader=paper_review_batch_entry_from_dict)
    scientific_forms = load_jsonl(args.scientific_forms, loader=paper_scientific_review_form_from_dict)
    writing_forms = load_jsonl(args.writing_forms, loader=paper_writing_review_form_from_dict)
    adjudications = load_jsonl(args.adjudications, loader=paper_review_adjudication_record_from_dict)
    queue = build_paper_review_queue(
        entries,
        scientific_forms,
        writing_forms,
        adjudications,
        reviewer_ids=tuple(args.reviewers),
    )
    write_jsonl(args.output, queue)
    payload = {
        "entries_loaded": len(entries),
        "queue_entries_written": len(queue),
        "output": args.output,
    }
    _print_json(payload)
    return 0


def command_summarize_paper_review_progress(args: argparse.Namespace) -> int:
    entries = load_jsonl(args.entries, loader=paper_review_batch_entry_from_dict)
    scientific_forms = load_jsonl(args.scientific_forms, loader=paper_scientific_review_form_from_dict)
    writing_forms = load_jsonl(args.writing_forms, loader=paper_writing_review_form_from_dict)
    adjudications = load_jsonl(args.adjudications, loader=paper_review_adjudication_record_from_dict)
    summary = summarize_paper_review_progress(
        entries,
        scientific_forms,
        writing_forms,
        adjudications,
        reviewer_ids=tuple(args.reviewers),
    )
    payload = summary.to_dict()
    if args.output:
        _write_json(args.output, payload)
    _print_json(payload)
    return 0


def command_finalize_paper_adjudications(args: argparse.Namespace) -> int:
    adjudications = load_jsonl(args.adjudications, loader=paper_review_adjudication_record_from_dict)
    finalized = finalize_paper_adjudications(adjudications)
    write_jsonl(args.output, finalized)
    payload = {
        "adjudications_loaded": len(adjudications),
        "finalized_records_written": len(finalized),
        "output": args.output,
    }
    _print_json(payload)
    return 0


def command_build_packaging_review_priors(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    packaging_records = build_packaging_review_priors(papers)
    write_jsonl(args.output, packaging_records)
    payload = {
        "papers_loaded": len(papers),
        "packaging_reviews_written": len(packaging_records),
        "output": args.output,
    }
    if args.summary_output:
        summary = {
            "papers_loaded": len(papers),
            "packaging_reviews_written": len(packaging_records),
            "artifact_access_pass_count": sum(
                1
                for record in packaging_records
                if record.packaging_review.domain_outcomes[PackagingDomain.ARTIFACT_ACCESS] == DomainOutcome.PASS
            ),
            "releaseability_pass_count": sum(
                1
                for record in packaging_records
                if record.packaging_review.domain_outcomes[PackagingDomain.RELEASEABILITY] == DomainOutcome.PASS
            ),
        }
        _write_json(args.summary_output, summary)
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_build_paper_qualification_decisions(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    adjudicated_reviews = load_jsonl(args.adjudicated_reviews, loader=adjudicated_paper_review_record_from_dict)
    packaging_reviews = load_jsonl(args.packaging_reviews, loader=paper_packaging_review_record_from_dict)
    records = build_paper_qualification_records(
        papers=papers,
        adjudicated_reviews=adjudicated_reviews,
        packaging_reviews=packaging_reviews,
    )
    report = build_paper_qualification_batch_report(
        papers=papers,
        adjudicated_reviews=adjudicated_reviews,
        packaging_reviews=packaging_reviews,
        records=records,
    )
    write_jsonl(args.output, records)
    payload = {
        "papers_loaded": len(papers),
        "adjudicated_reviews_loaded": len(adjudicated_reviews),
        "packaging_reviews_loaded": len(packaging_reviews),
        "decisions_written": len(records),
        "output": args.output,
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_build_auto_review_evidence_enrichments(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    fetch_records, enrichments = build_auto_review_evidence_enrichments(
        papers,
        raw_dir=args.raw_dir,
        refresh=args.refresh,
    )
    write_jsonl(args.output, enrichments)
    if args.fetch_records_output:
        write_jsonl(args.fetch_records_output, fetch_records)
    report = audit_auto_review_evidence_enrichments(fetch_records, enrichments)
    payload = {
        "papers_loaded": len(papers),
        "fetch_records_written": len(fetch_records),
        "enrichment_records_written": len(enrichments),
        "raw_dir": args.raw_dir,
        "output": args.output,
    }
    if args.fetch_records_output:
        payload["fetch_records_output"] = args.fetch_records_output
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_materialize_enriched_source_papers(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    enrichments = load_jsonl(args.evidence_enrichments, loader=auto_review_evidence_enrichment_record_from_dict)
    enriched_papers = materialize_enriched_source_papers(papers, enrichments)
    write_jsonl(args.output, enriched_papers)
    payload = {
        "papers_loaded": len(papers),
        "enrichments_loaded": len(enrichments),
        "enriched_papers_written": len(enriched_papers),
        "output": args.output,
    }
    _print_json(payload)
    return 0


def command_build_auto_review_source_bundles(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    evidence_enrichments = (
        load_jsonl(args.evidence_enrichments, loader=auto_review_evidence_enrichment_record_from_dict)
        if args.evidence_enrichments
        else ()
    )
    output_path = Path(args.output)
    if output_path.exists() and not args.refresh:
        bundles = load_jsonl(args.output, loader=auto_review_source_bundle_from_dict)
    else:
        bundles = build_auto_review_source_bundles(papers, evidence_enrichments=evidence_enrichments)
        write_jsonl(args.output, bundles)
    report = audit_auto_review_source_bundles(bundles)
    payload = {
        "papers_loaded": len(papers),
        "evidence_enrichments_loaded": len(evidence_enrichments),
        "source_bundles_written": len(bundles),
        "output": args.output,
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_audit_auto_review_source_bundles(args: argparse.Namespace) -> int:
    bundles = load_jsonl(args.source_bundles, loader=auto_review_source_bundle_from_dict)
    report = audit_auto_review_source_bundles(bundles)
    payload = report.to_dict()
    if args.output:
        _write_json(args.output, payload)
    _print_json(payload)
    return 0


def command_run_auto_paper_reviews(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    bundles = load_jsonl(args.source_bundles, loader=auto_review_source_bundle_from_dict)
    execution_profile = execution_profile_from_dict(_load_json_object(args.execution_profile))
    packaging_reviews = (
        load_jsonl(args.packaging_reviews, loader=paper_packaging_review_record_from_dict)
        if args.packaging_reviews
        else ()
    )
    output_path = Path(args.output)
    if output_path.exists() and not args.refresh:
        votes = load_jsonl(args.output, loader=auto_panel_vote_from_dict)
    else:
        votes = run_auto_paper_reviews(
            papers,
            bundles,
            execution_profile=execution_profile,
            model_id=args.model_id,
            packaging_reviews=packaging_reviews,
            temperature=args.temperature,
            top_p=args.top_p,
            seed=args.seed,
        )
        write_jsonl(args.output, votes)
    report = summarize_auto_review_batch(
        papers,
        bundles=bundles,
        panel_votes=votes,
    )
    payload = {
        "papers_loaded": len(papers),
        "source_bundles_loaded": len(bundles),
        "panel_votes_written": len(votes),
        "output": args.output,
        "execution_profile": args.execution_profile,
        "model_id": args.model_id,
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_aggregate_auto_paper_reviews(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    bundles = load_jsonl(args.source_bundles, loader=auto_review_source_bundle_from_dict)
    panel_votes = load_jsonl(args.panel_votes, loader=auto_panel_vote_from_dict)
    output_path = Path(args.output)
    if output_path.exists() and not args.refresh:
        aggregated = load_jsonl(args.output, loader=auto_aggregated_paper_review_record_from_dict)
    else:
        aggregated = aggregate_auto_paper_reviews(papers, bundles, panel_votes)
        write_jsonl(args.output, aggregated)
    report = summarize_auto_review_batch(
        papers,
        bundles=bundles,
        panel_votes=panel_votes,
        aggregated_reviews=aggregated,
    )
    payload = {
        "papers_loaded": len(papers),
        "source_bundles_loaded": len(bundles),
        "panel_votes_loaded": len(panel_votes),
        "aggregated_reviews_written": len(aggregated),
        "output": args.output,
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_build_auto_paper_qualification_decisions(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    bundles = load_jsonl(args.source_bundles, loader=auto_review_source_bundle_from_dict)
    aggregated = load_jsonl(args.aggregated_reviews, loader=auto_aggregated_paper_review_record_from_dict)
    packaging_reviews = load_jsonl(args.packaging_reviews, loader=paper_packaging_review_record_from_dict)
    records = build_auto_paper_qualification_records(
        papers=papers,
        bundles=bundles,
        aggregated_reviews=aggregated,
        packaging_reviews=packaging_reviews,
    )
    write_jsonl(args.output, records)
    report = summarize_auto_review_batch(
        papers,
        bundles=bundles,
        aggregated_reviews=aggregated,
        qualification_records=records,
    )
    payload = {
        "papers_loaded": len(papers),
        "source_bundles_loaded": len(bundles),
        "aggregated_reviews_loaded": len(aggregated),
        "packaging_reviews_loaded": len(packaging_reviews),
        "qualification_records_written": len(records),
        "output": args.output,
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_summarize_auto_review_batch(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    bundles = (
        load_jsonl(args.source_bundles, loader=auto_review_source_bundle_from_dict)
        if args.source_bundles
        else ()
    )
    panel_votes = (
        load_jsonl(args.panel_votes, loader=auto_panel_vote_from_dict)
        if args.panel_votes
        else ()
    )
    aggregated = (
        load_jsonl(args.aggregated_reviews, loader=auto_aggregated_paper_review_record_from_dict)
        if args.aggregated_reviews
        else ()
    )
    qualification_records = (
        load_jsonl(args.qualifications, loader=auto_qualification_record_from_dict)
        if args.qualifications
        else ()
    )
    report = summarize_auto_review_batch(
        papers,
        bundles=bundles,
        panel_votes=panel_votes,
        aggregated_reviews=aggregated,
        qualification_records=qualification_records,
    )
    payload = report.to_dict()
    if args.output:
        _write_json(args.output, payload)
    _print_json(payload)
    return 0


def command_build_auto_review_recovery_batch(args: argparse.Namespace) -> int:
    if args.selected_papers_output and not args.papers:
        raise ValueError("--papers is required when --selected-papers-output is used")
    if args.selected_packaging_reviews_output and not args.packaging_reviews:
        raise ValueError("--packaging-reviews is required when --selected-packaging-reviews-output is used")
    queue_entries = load_jsonl(args.recovery_queue, loader=auto_review_recovery_batch_entry_from_dict)
    excluded_entries = []
    for path in args.exclude_selected_entries:
        excluded_entries.extend(load_jsonl(path, loader=auto_review_recovery_batch_entry_from_dict))
    excluded_paper_ids = tuple(dict.fromkeys(entry.paper_id for entry in excluded_entries))
    selected_entries = build_auto_review_recovery_batch(
        queue_entries,
        target_total=args.target_total,
        preferred_buckets=tuple(args.preferred_buckets),
        per_class_target=args.per_class_target,
        excluded_paper_ids=excluded_paper_ids,
        strict_preferred_buckets=args.strict_preferred_buckets,
    )
    report = build_auto_review_recovery_batch_report(
        queue_entries,
        selected_entries,
        target_total=args.target_total,
        preferred_buckets=tuple(args.preferred_buckets),
        per_class_target=args.per_class_target,
    )
    write_jsonl(args.output, selected_entries)
    payload = {
        "queue_entries_loaded": len(queue_entries),
        "selected_entries_written": len(selected_entries),
        "output": args.output,
        "target_total": args.target_total,
        "preferred_buckets": list(args.preferred_buckets),
        "per_class_target": args.per_class_target,
        "strict_preferred_buckets": args.strict_preferred_buckets,
    }
    if excluded_paper_ids:
        payload["excluded_paper_ids_count"] = len(excluded_paper_ids)
        payload["exclude_selected_entries"] = list(args.exclude_selected_entries)
    if args.selected_papers_output:
        papers = load_jsonl(args.papers, loader=source_paper_from_dict)
        selected_papers = select_recovery_batch_papers(papers, selected_entries)
        write_jsonl(args.selected_papers_output, selected_papers)
        payload["papers_loaded"] = len(papers)
        payload["selected_papers_written"] = len(selected_papers)
        payload["selected_papers_output"] = args.selected_papers_output
    if args.selected_packaging_reviews_output:
        packaging_reviews = load_jsonl(args.packaging_reviews, loader=paper_packaging_review_record_from_dict)
        selected_packaging_reviews = select_recovery_batch_packaging_reviews(packaging_reviews, selected_entries)
        write_jsonl(args.selected_packaging_reviews_output, selected_packaging_reviews)
        payload["packaging_reviews_loaded"] = len(packaging_reviews)
        payload["selected_packaging_reviews_written"] = len(selected_packaging_reviews)
        payload["selected_packaging_reviews_output"] = args.selected_packaging_reviews_output
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_write_auto_review_recovery_job(args: argparse.Namespace) -> int:
    execution_profile = execution_profile_from_dict(_load_json_object(args.execution_profile))
    job_spec = build_auto_review_recovery_job_spec(
        execution_profile,
        execution_profile_path=args.execution_profile,
        papers_path=args.papers,
        packaging_reviews_path=args.packaging_reviews,
        output_dir=args.output_dir,
        model_id=args.model_id,
        raw_dir=args.raw_dir,
        job_name=args.job_name,
    )
    script = render_execution_job_script(job_spec, execution_profile)
    _write_json(args.job_spec_output, job_spec.to_dict())
    _write_text(args.script_output, script)
    payload = {
        "execution_profile": args.execution_profile,
        "job_name": job_spec.job_name,
        "job_kind": job_spec.job_kind,
        "job_spec_output": args.job_spec_output,
        "script_output": args.script_output,
        "output_dir": args.output_dir,
    }
    _print_json(payload)
    return 0


def command_build_pilot_templates(args: argparse.Namespace) -> int:
    specs = load_jsonl(args.manifest, loader=pilot_calibration_spec_from_dict)
    forms = build_pilot_review_forms(specs, reviewer_ids=tuple(args.reviewers))
    adjudications = build_pilot_adjudication_shells(
        specs,
        adjudicator_id=args.adjudicator,
        reviewer_ids=tuple(args.reviewers),
    )
    write_jsonl(args.forms_output, forms)
    write_jsonl(args.adjudication_output, adjudications)
    payload = {
        "forms_written": len(forms),
        "adjudications_written": len(adjudications),
        "forms_output": args.forms_output,
        "adjudication_output": args.adjudication_output,
    }
    _print_json(payload)
    return 0


def command_build_calibration_batch(args: argparse.Namespace) -> int:
    specs = load_jsonl(args.manifest, loader=pilot_calibration_spec_from_dict)
    if args.mode == "pilot":
        issues = validate_pilot_calibration_set(specs)
    else:
        issues = validate_full_calibration_set(specs)
    if issues and not args.allow_invalid:
        raise ValueError("; ".join(issues))
    forms = build_pilot_review_forms(specs, reviewer_ids=tuple(args.reviewers))
    adjudications = build_pilot_adjudication_shells(
        specs,
        adjudicator_id=args.adjudicator,
        reviewer_ids=tuple(args.reviewers),
    )
    write_jsonl(args.forms_output, forms)
    write_jsonl(args.adjudication_output, adjudications)
    payload = {
        "mode": args.mode,
        "forms_written": len(forms),
        "adjudications_written": len(adjudications),
        "forms_output": args.forms_output,
        "adjudication_output": args.adjudication_output,
        "issues": list(issues),
    }
    if args.summary_output:
        _write_json(
            args.summary_output,
            {
                "coverage_summary": pilot_coverage_summary(specs),
                "issues": list(issues),
                "mode": args.mode,
            },
        )
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_merge_review_forms(args: argparse.Namespace) -> int:
    merged_inputs = []
    for input_path in args.inputs:
        merged_inputs.extend(load_jsonl(input_path, loader=pilot_review_form_from_dict))
    merged = merge_review_forms(merged_inputs)
    write_jsonl(args.output, merged)
    _print_json(
        {
            "input_forms": len(merged_inputs),
            "merged_forms": len(merged),
            "output": args.output,
        }
    )
    return 0


def command_build_adjudication_queue(args: argparse.Namespace) -> int:
    specs = load_jsonl(args.manifest, loader=pilot_calibration_spec_from_dict)
    forms = load_jsonl(args.forms, loader=pilot_review_form_from_dict)
    adjudications = load_jsonl(args.adjudications, loader=pilot_adjudication_record_from_dict)
    queue = build_adjudication_queue(
        specs,
        forms,
        adjudications,
        reviewer_ids=tuple(args.reviewers),
    )
    write_jsonl(args.output, queue)
    payload = {
        "queue_entries": len(queue),
        "output": args.output,
        "status_counts": {},
    }
    for entry in queue:
        payload["status_counts"][entry.status] = payload["status_counts"].get(entry.status, 0) + 1
    _print_json(payload)
    return 0


def command_summarize_pilot_agreement(args: argparse.Namespace) -> int:
    forms = load_jsonl(args.forms, loader=pilot_review_form_from_dict)
    adjudications = load_jsonl(
        args.adjudications,
        loader=pilot_adjudication_record_from_dict,
    )
    summary = compute_agreement_against_adjudication(forms, adjudications)
    issues = validate_pilot_agreement_thresholds(summary)
    payload = {
        "summary": summary.to_dict(),
        "issues": list(issues),
        "ok": not issues,
    }
    if args.output:
        _write_json(args.output, payload)
    _print_json(payload)
    return 0 if not issues else 1


def command_summarize_calibration(args: argparse.Namespace) -> int:
    specs = load_jsonl(args.manifest, loader=pilot_calibration_spec_from_dict)
    forms = load_jsonl(args.forms, loader=pilot_review_form_from_dict)
    adjudications = load_jsonl(args.adjudications, loader=pilot_adjudication_record_from_dict)
    payload = {
        "coverage_summary": pilot_coverage_summary(specs),
        "progress_summary": summarize_calibration_progress(
            specs,
            forms,
            adjudications,
            reviewer_ids=tuple(args.reviewers),
        ),
    }
    if args.output:
        _write_json(args.output, payload)
    _print_json(payload)
    return 0


def command_audit_calibration_drift(args: argparse.Namespace) -> int:
    baseline_specs = load_jsonl(args.baseline_manifest, loader=pilot_calibration_spec_from_dict)
    updated_specs = load_jsonl(args.updated_manifest, loader=pilot_calibration_spec_from_dict)
    report = audit_calibration_drift(baseline_specs, updated_specs)
    if args.output:
        _write_json(args.output, report.to_dict())
    _print_json(report.to_dict())
    return 0


def command_build_judge_review_templates(args: argparse.Namespace) -> int:
    judge_units = load_jsonl(args.judge_units, loader=judge_validation_unit_from_dict)
    forms = build_judge_review_forms(judge_units, reviewer_ids=tuple(args.reviewers))
    adjudications = build_judge_adjudication_shells(
        judge_units,
        adjudicator_id=args.adjudicator,
        reviewer_ids=tuple(args.reviewers),
    )
    write_jsonl(args.forms_output, forms)
    write_jsonl(args.adjudication_output, adjudications)
    _print_json(
        {
            "judge_units_loaded": len(judge_units),
            "forms_written": len(forms),
            "adjudications_written": len(adjudications),
            "forms_output": args.forms_output,
            "adjudication_output": args.adjudication_output,
        }
    )
    return 0


def command_merge_judge_review_forms(args: argparse.Namespace) -> int:
    merged_inputs = []
    for input_path in args.inputs:
        merged_inputs.extend(load_jsonl(input_path, loader=judge_review_form_from_dict))
    merged = merge_judge_review_forms(merged_inputs)
    write_jsonl(args.output, merged)
    _print_json(
        {
            "input_forms": len(merged_inputs),
            "merged_forms": len(merged),
            "output": args.output,
        }
    )
    return 0


def command_build_judge_adjudication_queue(args: argparse.Namespace) -> int:
    judge_units = load_jsonl(args.judge_units, loader=judge_validation_unit_from_dict)
    forms = load_jsonl(args.forms, loader=judge_review_form_from_dict)
    adjudications = load_jsonl(args.adjudications, loader=judge_adjudication_record_from_dict)
    queue = build_judge_adjudication_queue(
        judge_units,
        forms,
        adjudications,
        reviewer_ids=tuple(args.reviewers),
    )
    write_jsonl(args.output, queue)
    payload = {
        "queue_entries": len(queue),
        "output": args.output,
        "status_counts": {},
    }
    for entry in queue:
        payload["status_counts"][entry.status] = payload["status_counts"].get(entry.status, 0) + 1
    _print_json(payload)
    return 0


def command_finalize_judge_slice(args: argparse.Namespace) -> int:
    judge_units = load_jsonl(args.judge_units, loader=judge_validation_unit_from_dict)
    adjudications = load_jsonl(args.adjudications, loader=judge_adjudication_record_from_dict)
    finalized_units = finalize_judge_validation_units(judge_units, adjudications)
    write_jsonl(args.output, finalized_units)
    ready_count = sum(
        1
        for unit in finalized_units
        if unit.human_adjudicated and unit.frozen
    )
    _print_json(
        {
            "input_judge_units": len(judge_units),
            "adjudications_loaded": len(adjudications),
            "finalized_units_written": len(finalized_units),
            "adjudicated_and_frozen_units": ready_count,
            "output": args.output,
        }
    )
    return 0


def command_build_judge_batch(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    include_task_families = tuple(TaskFamily(value) for value in args.task_family) if args.task_family else None
    include_release_tiers = tuple(ReleaseTier(value) for value in args.release_tier) if args.release_tier else None
    inventory_report = summarize_task_bundles(task_bundles)
    selected_task_bundles = select_judge_candidate_task_bundles(
        task_bundles,
        target_total=args.target_total,
        include_task_families=include_task_families,
        include_release_tiers=include_release_tiers,
        include_holdout_buckets=tuple(args.holdout_bucket) if args.holdout_bucket else None,
    )
    selection_report = summarize_judge_candidate_selection(
        selected_task_bundles,
        target_total=args.target_total,
    )
    judge_units = build_judge_validation_units(
        selected_task_bundles,
    )
    forms = build_judge_review_forms(judge_units, reviewer_ids=tuple(args.reviewers))
    adjudications = build_judge_adjudication_shells(
        judge_units,
        adjudicator_id=args.adjudicator,
        reviewer_ids=tuple(args.reviewers),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_bundles_output = output_dir / "selected_task_bundles.jsonl"
    inventory_output = output_dir / "task_bundle_inventory.json"
    selection_output = output_dir / "judge_candidate_selection.json"
    judge_units_output = output_dir / "judge_units.jsonl"
    forms_output = output_dir / "judge_review_forms.jsonl"
    adjudications_output = output_dir / "judge_adjudications.jsonl"
    summary_output = output_dir / "judge_batch_summary.json"
    write_jsonl(str(selected_bundles_output), selected_task_bundles)
    _write_json(str(inventory_output), inventory_report.to_dict())
    _write_json(str(selection_output), selection_report.to_dict())
    write_jsonl(str(judge_units_output), judge_units)
    write_jsonl(str(forms_output), forms)
    write_jsonl(str(adjudications_output), adjudications)
    summary_payload = {
        "task_bundles_loaded": len(task_bundles),
        "selected_task_bundles": len(selected_task_bundles),
        "judge_units": len(judge_units),
        "judge_review_forms": len(forms),
        "judge_adjudications": len(adjudications),
        "target_total": args.target_total,
        "reviewers": list(args.reviewers),
        "adjudicator": args.adjudicator,
    }
    if include_task_families:
        summary_payload["task_families"] = [task_family.value for task_family in include_task_families]
    if include_release_tiers:
        summary_payload["release_tiers"] = [release_tier.value for release_tier in include_release_tiers]
    if args.holdout_bucket:
        summary_payload["holdout_buckets"] = list(args.holdout_bucket)
    _write_json(str(summary_output), summary_payload)
    _print_json(
        {
            "output_dir": str(output_dir),
            "selected_task_bundles_output": str(selected_bundles_output),
            "task_bundle_inventory_output": str(inventory_output),
            "judge_candidate_selection_output": str(selection_output),
            "judge_units_output": str(judge_units_output),
            "forms_output": str(forms_output),
            "adjudications_output": str(adjudications_output),
            "summary_output": str(summary_output),
            **summary_payload,
        }
    )
    return 0


def command_summarize_task_bundles(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    report = summarize_task_bundles(task_bundles)
    if args.output:
        _write_json(args.output, report.to_dict())
    _print_json(report.to_dict())
    return 0


def command_select_judge_candidates(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    include_task_families = tuple(TaskFamily(value) for value in args.task_family) if args.task_family else None
    include_release_tiers = tuple(ReleaseTier(value) for value in args.release_tier) if args.release_tier else None
    selected = select_judge_candidate_task_bundles(
        task_bundles,
        target_total=args.target_total,
        include_task_families=include_task_families,
        include_release_tiers=include_release_tiers,
        include_holdout_buckets=tuple(args.holdout_bucket) if args.holdout_bucket else None,
    )
    report = summarize_judge_candidate_selection(selected, target_total=args.target_total)
    write_jsonl(args.output, selected)
    payload = {
        "selected_output": args.output,
        "selected_total": len(selected),
        "target_total": args.target_total,
        "summary": report.to_dict(),
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_build_shadow_inspection_batch(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    papers = {
        paper.paper_id: paper
        for paper in load_jsonl(args.papers, loader=source_paper_from_dict)
    }
    auto_records = {
        record.paper_id: record
        for record in load_jsonl(args.auto_qualification_records, loader=auto_qualification_record_from_dict)
    }
    source_bundles = {
        bundle.paper_id: bundle
        for bundle in load_jsonl(args.source_bundles, loader=auto_review_source_bundle_from_dict)
    }
    entries = build_shadow_inspection_batch(
        task_bundles=task_bundles,
        papers=papers,
        auto_qualification_records=auto_records,
        source_bundles=source_bundles,
        target_total=args.target_total,
        include_holdout_buckets=tuple(args.holdout_bucket) if args.holdout_bucket else None,
    )
    report = summarize_shadow_inspection_batch(entries, target_total=args.target_total)
    write_jsonl(args.output, entries)
    payload = {
        "entries_written": len(entries),
        "output": args.output,
        "summary": report.to_dict(),
    }
    if args.summary_output:
        _write_json(args.summary_output, report.to_dict())
        payload["summary_output"] = args.summary_output
    if args.markdown_output:
        markdown = render_shadow_inspection_markdown(entries, report)
        _write_text(args.markdown_output, markdown)
        payload["markdown_output"] = args.markdown_output
    _print_json(payload)
    return 0


def command_summarize_shadow_inspection_taxonomy(args: argparse.Namespace) -> int:
    entries = load_jsonl(args.inspection_entries, loader=shadow_inspection_entry_from_dict)
    categories = build_shadow_inspection_taxonomy(entries)
    if args.minimum_entry_count > 1:
        categories = tuple(
            category
            for category in categories
            if category.entry_count >= args.minimum_entry_count
        )
    report = summarize_shadow_inspection_taxonomy(entries, categories)
    payload = {
        "category_count": len(categories),
        "output": args.output,
        "summary": report.to_dict(),
    }
    _write_json(args.output, report.to_dict())
    if args.markdown_output:
        markdown = render_shadow_inspection_taxonomy_markdown(report)
        _write_text(args.markdown_output, markdown)
        payload["markdown_output"] = args.markdown_output
    _print_json(payload)
    return 0


def command_compare_shadow_inspection_runs(args: argparse.Namespace) -> int:
    previous_report = shadow_inspection_batch_report_from_dict(_read_json(args.previous_summary))
    current_report = shadow_inspection_batch_report_from_dict(_read_json(args.current_summary))
    previous_taxonomy = shadow_inspection_taxonomy_report_from_dict(_read_json(args.previous_taxonomy))
    current_taxonomy = shadow_inspection_taxonomy_report_from_dict(_read_json(args.current_taxonomy))
    report = compare_shadow_inspection_reports(
        previous_report,
        current_report,
        previous_taxonomy,
        current_taxonomy,
        previous_label=args.previous_label,
        current_label=args.current_label,
    )
    _write_json(args.output, report.to_dict())
    _print_json({"output": args.output, "summary": report.to_dict()})
    return 0


def command_summarize_judge_progress(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    judge_units = load_jsonl(args.judge_units, loader=judge_validation_unit_from_dict)
    forms = load_jsonl(args.forms, loader=judge_review_form_from_dict)
    adjudications = load_jsonl(args.adjudications, loader=judge_adjudication_record_from_dict)
    payload = {
        "slice_audit": audit_judge_validation_slice(
            task_bundles=task_bundles,
            judge_units=judge_units,
            minimum_total=args.minimum_total,
        ).to_dict(),
        "progress_summary": summarize_judge_progress(
            judge_units,
            forms,
            adjudications,
            reviewer_ids=tuple(args.reviewers),
        ),
    }
    if args.output:
        _write_json(args.output, payload)
    _print_json(payload)
    return 0


def command_build_release_index(args: argparse.Namespace) -> int:
    units = load_jsonl(args.units, loader=benchmark_unit_from_dict)
    decisions = load_jsonl(
        args.decisions,
        loader=benchmark_unit_decision_record_from_dict,
    )
    decision_map = {
        record.benchmark_unit_id: record
        for record in decisions
    }

    entries = build_release_index(
        units,
        decision_map,
        public_ratio=args.public_ratio,
        private_ratio=args.private_ratio,
        holdout_salt=args.holdout_salt,
        canary_prefix=args.canary_prefix,
        canary_salt=args.canary_salt,
        enforce_split_safety=not args.allow_split_safety_violations,
    )
    write_jsonl(args.output, entries)
    payload = {
        "entries_written": len(entries),
        "output": args.output,
    }
    _print_json(payload)
    return 0


def command_build_release_bundle(args: argparse.Namespace) -> int:
    units = load_jsonl(args.units, loader=benchmark_unit_from_dict)
    decisions = load_jsonl(
        args.decisions,
        loader=benchmark_unit_decision_record_from_dict,
    )
    decision_map = {
        record.benchmark_unit_id: record
        for record in decisions
    }
    bundle = build_release_manifest_bundle(
        units,
        decision_map,
        public_ratio=args.public_ratio,
        private_ratio=args.private_ratio,
        holdout_salt=args.holdout_salt,
        canary_prefix=args.canary_prefix,
        canary_salt=args.canary_salt,
        enforce_split_safety=not args.allow_split_safety_violations,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_payloads = render_release_bundle_artifacts(bundle)
    for artifact_name, payload in artifact_payloads.items():
        _write_bytes(str(output_dir / artifact_name), payload)
    verification_report = verify_release_bundle_directory(str(output_dir))
    _write_json(str(output_dir / BUNDLE_VERIFY_REPORT_FILENAME), verification_report.to_dict())
    payload = {
        "output_dir": str(output_dir),
        "artifacts_written": sorted(artifact_payloads),
        "verification_report": str(output_dir / BUNDLE_VERIFY_REPORT_FILENAME),
        "summary": bundle.summary(),
    }
    _print_json(payload)
    return 0


def command_verify_release_bundle(args: argparse.Namespace) -> int:
    report = verify_release_bundle_directory(args.bundle_dir)
    output_path = args.output or str(Path(args.bundle_dir) / BUNDLE_VERIFY_REPORT_FILENAME)
    _write_json(output_path, report.to_dict())
    payload = {
        "ok": report.ok,
        "output": output_path,
        "release_bundle_id": report.release_bundle_id,
    }
    _print_json(payload)
    return 0 if report.ok else 1


def command_build_task_bundles(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    evidence_units = load_jsonl(args.evidence_units, loader=evidence_unit_from_dict)
    benchmark_units = load_jsonl(args.benchmark_units, loader=benchmark_unit_from_dict)
    truth_manifests = load_jsonl(args.truth_manifests, loader=truth_manifest_from_dict)
    decisions = load_jsonl(args.decisions, loader=benchmark_unit_decision_record_from_dict)

    paper_map = {paper.paper_id: paper for paper in papers}
    evidence_unit_map = {unit.unit_id: unit for unit in evidence_units}
    truth_manifest_map = {}
    for manifest in truth_manifests:
        if manifest.paper_id in truth_manifest_map:
            raise ValueError(f"multiple truth manifests found for {manifest.paper_id}")
        truth_manifest_map[manifest.paper_id] = manifest
    release_tier_map = {
        record.benchmark_unit_id: record.release_tier
        for record in decisions
    }

    task_bundles = build_task_bundles(
        benchmark_units=benchmark_units,
        papers=paper_map,
        evidence_units=evidence_unit_map,
        truth_manifests=truth_manifest_map,
        release_tiers=release_tier_map,
        provenance_manifest_id=args.provenance_manifest_id,
    )
    truth_manifest_bundles = tuple(
        build_truth_manifest_bundle(
            truth_manifest=truth_manifest_map[paper_id],
            evidence_units=tuple(
                evidence_unit_map[unit_id]
                for unit_id in sorted(
                    {
                        unit_id
                        for bundle in task_bundles
                        if bundle.paper_id == paper_id
                        for unit_id in bundle.evidence_unit_ids
                    }
                )
            ),
            provenance_manifest_id=args.provenance_manifest_id,
        )
        for paper_id in sorted({bundle.paper_id for bundle in task_bundles if bundle.paper_id})
    )
    write_jsonl(args.output, task_bundles)
    if args.truth_manifest_bundles_output:
        write_jsonl(args.truth_manifest_bundles_output, truth_manifest_bundles)
    payload = {
        "task_bundles_written": len(task_bundles),
        "output": args.output,
        "truth_manifest_bundles_written": len(truth_manifest_bundles),
    }
    if args.truth_manifest_bundles_output:
        payload["truth_manifest_bundles_output"] = args.truth_manifest_bundles_output
    _print_json(payload)
    return 0


def command_build_benchmark_units_from_evidence(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict) if args.papers else []
    evidence_units = load_jsonl(args.evidence_units, loader=evidence_unit_from_dict)
    paper_map = {paper.paper_id: paper for paper in papers}
    benchmark_units = build_benchmark_units_from_evidence_units(
        evidence_units=evidence_units,
        papers=paper_map if paper_map else None,
        benchmark_unit_id_prefix=args.benchmark_unit_id_prefix,
        default_split=args.default_split,
    )
    write_jsonl(args.output, benchmark_units)
    _print_json(
        {
            "benchmark_units_written": len(benchmark_units),
            "output": args.output,
        }
    )
    return 0


def command_build_benchmark_unit_decisions_from_auto_review(args: argparse.Namespace) -> int:
    benchmark_units = load_jsonl(args.benchmark_units, loader=benchmark_unit_from_dict)
    auto_qualification_records = load_jsonl(
        args.auto_qualifications,
        loader=auto_qualification_record_from_dict,
    )
    record_map = {record.paper_id: record for record in auto_qualification_records}
    decision_records = build_benchmark_unit_decisions_from_auto_qualifications(
        benchmark_units=benchmark_units,
        auto_qualification_records=record_map,
        include_stress_candidates=args.include_stress_candidates,
    )
    write_jsonl(args.output, decision_records)
    release_tier_counts: Dict[str, int] = {}
    for record in decision_records:
        release_tier_counts[record.release_tier.value] = release_tier_counts.get(record.release_tier.value, 0) + 1
    _print_json(
        {
            "benchmark_unit_decisions_written": len(decision_records),
            "output": args.output,
            "release_tier_counts": release_tier_counts,
        }
    )
    return 0


def command_annotate_task_bundles_with_release_index(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    release_index_payloads = load_jsonl(args.release_index)
    release_index = {
        str(item["benchmark_unit_id"]): ReleaseIndexEntry(
            benchmark_unit_id=str(item["benchmark_unit_id"]),
            paper_id=str(item["paper_id"]),
            release_tier=ReleaseTier(str(item["release_tier"])),
            holdout_bucket=str(item["holdout_bucket"]),
            canary_string=str(item["canary_string"]),
            benchmark_split=str(item.get("benchmark_split") or "") or None,
        )
        for item in release_index_payloads
    }
    annotated = annotate_task_bundles_with_release_index(
        task_bundles,
        release_index,
        strict=not args.allow_missing_release_index_entries,
    )
    write_jsonl(args.output, annotated)
    summary = summarize_task_bundles(annotated).to_dict()
    payload = {
        "task_bundles_loaded": len(task_bundles),
        "annotated_task_bundles_written": len(annotated),
        "output": args.output,
        "holdout_bucket_counts": summary["holdout_bucket_counts"],
    }
    if args.summary_output:
        _write_json(args.summary_output, summary)
        payload["summary_output"] = args.summary_output
    _print_json(payload)
    return 0


def command_build_evaluation_task_bundles(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    observations = load_jsonl(args.observations, loader=observation_record_from_dict)
    questions = load_jsonl(args.questions, loader=question_record_from_dict)
    answers = load_jsonl(args.answers, loader=answer_record_from_dict)
    truth_manifests = load_jsonl(args.truth_manifests, loader=truth_manifest_from_dict)
    source_quality_records = (
        load_jsonl(args.source_quality_records, loader=source_quality_record_from_dict)
        if args.source_quality_records
        else []
    )

    paper_map = {paper.paper_id: paper for paper in papers}
    truth_manifest_map = {}
    for manifest in truth_manifests:
        if manifest.paper_id in truth_manifest_map:
            raise ValueError(f"multiple truth manifests found for {manifest.paper_id}")
        truth_manifest_map[manifest.paper_id] = manifest

    task_bundles = build_evaluation_task_bundles(
        questions=questions,
        answers=answers,
        observations=observations,
        papers=paper_map,
        truth_manifests=truth_manifest_map,
        default_release_tier=ReleaseTier(args.default_release_tier),
        provenance_manifest_id=args.provenance_manifest_id,
        source_quality_records=tuple(source_quality_records),
    )
    write_jsonl(args.output, task_bundles)
    _print_json(
        {
            "task_bundles_written": len(task_bundles),
            "output": args.output,
            "default_release_tier": args.default_release_tier,
        }
    )
    return 0


def command_run_baseline(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    baseline_kind = BaselineKind(args.baseline_kind)
    run_spec, submissions = run_baseline(
        task_bundles=task_bundles,
        baseline_kind=baseline_kind,
        producer_id=args.producer_id,
    )
    write_jsonl(args.submissions_output, submissions)
    write_jsonl(args.run_spec_output, [run_spec])
    payload = {
        "baseline_kind": baseline_kind.value,
        "task_bundles_processed": len(task_bundles),
        "submissions_written": len(submissions),
        "submissions_output": args.submissions_output,
        "run_spec_output": args.run_spec_output,
        "baseline_id": run_spec.baseline_id,
    }
    _print_json(payload)
    return 0


def command_score_submissions(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    submissions = load_jsonl(args.submissions, loader=submission_record_from_dict)
    evaluations = evaluate_submissions(task_bundles, submissions, version=args.scoring_version)
    write_jsonl(args.output, evaluations)
    payload = {
        "task_bundles_loaded": len(task_bundles),
        "submissions_loaded": len(submissions),
        "evaluations_written": len(evaluations),
        "output": args.output,
        "scoring_version": args.scoring_version,
        "passed_deterministic_checks": sum(1 for evaluation in evaluations if evaluation.deterministic_checks_passed),
    }
    _print_json(payload)
    return 0


def command_build_baseline_run_inventory(args: argparse.Namespace) -> int:
    baseline_runs = _load_baseline_run_specs_from_paths(tuple(args.run_spec))
    write_jsonl(args.output, baseline_runs)
    payload = {
        "input_artifacts": len(tuple(args.run_spec)),
        "baseline_runs_written": len(baseline_runs),
        "output": args.output,
        "replay_verified": sum(1 for run in baseline_runs if run.replay_verified),
    }
    _print_json(payload)
    return 0


def command_build_judge_slice(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    include_task_families = tuple(TaskFamily(value) for value in args.task_family) if args.task_family else None
    include_release_tiers = tuple(ReleaseTier(value) for value in args.release_tier) if args.release_tier else None
    judge_units = build_judge_validation_slice(
        task_bundles=task_bundles,
        target_total=args.target_total,
        include_task_families=include_task_families,
        include_release_tiers=include_release_tiers,
        include_holdout_buckets=tuple(args.holdout_bucket) if args.holdout_bucket else None,
        human_adjudicated=args.human_adjudicated,
        frozen=args.freeze,
    )
    write_jsonl(args.output, judge_units)
    payload = {
        "task_bundles_loaded": len(task_bundles),
        "judge_units_written": len(judge_units),
        "output": args.output,
        "target_total": args.target_total,
    }
    if include_task_families:
        payload["task_families"] = [task_family.value for task_family in include_task_families]
    if include_release_tiers:
        payload["release_tiers"] = [release_tier.value for release_tier in include_release_tiers]
    _print_json(payload)
    return 0


def command_audit_judge_slice(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    judge_units = load_jsonl(args.judge_units, loader=judge_validation_unit_from_dict)
    report = audit_judge_validation_slice(
        task_bundles=task_bundles,
        judge_units=judge_units,
        minimum_total=args.minimum_total,
    )
    if args.output:
        _write_json(args.output, report.to_dict())
    _print_json(report.to_dict())
    return 0 if report.ok else 1


def command_audit_llm_eval_alignment(args: argparse.Namespace) -> int:
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    evaluations = load_jsonl(args.evaluations, loader=evaluation_record_from_dict)
    judgments = load_jsonl(args.judgments)
    report = audit_llm_judge_alignment(
        task_bundles=task_bundles,
        evaluations=evaluations,
        judgments=judgments,
    )
    if args.output:
        _write_json(args.output, report.to_dict())
    if args.markdown_output:
        Path(args.markdown_output).write_text(
            render_llm_judge_alignment_markdown(report) + "\n",
            encoding="utf-8",
        )
    _print_json(report.to_dict())
    return 0 if report.ok else 1


def command_summarize_program_progress(args: argparse.Namespace) -> int:
    papers = load_jsonl(args.papers, loader=source_paper_from_dict)
    paper_decisions = _load_program_progress_decisions(args.paper_decisions)
    task_bundles = load_jsonl(args.task_bundles, loader=task_bundle_from_dict)
    judge_validation_units = (
        load_jsonl(args.judge_validation_units, loader=judge_validation_unit_from_dict)
        if args.judge_validation_units
        else []
    )
    baseline_runs = (
        _load_baseline_run_specs_from_paths((args.baseline_runs,))
        if args.baseline_runs
        else []
    )
    report = summarize_program_progress(
        source_papers=papers,
        paper_decisions=paper_decisions,
        task_bundles=task_bundles,
        judge_validation_units=judge_validation_units,
        baseline_runs=baseline_runs,
    )
    if args.output:
        _write_json(args.output, report.to_dict())
    _print_json(report.to_dict())
    return 0


def command_build_maintenance_log_entry(args: argparse.Namespace) -> int:
    entry = build_maintenance_log_entry(
        phase=args.phase,
        summary=args.summary,
        release_bundle_id=args.release_bundle_id,
        artifacts=tuple(args.artifacts or ()),
        notes=tuple(args.notes or ()),
    )
    write_jsonl(args.output, [entry])
    payload = {
        "output": args.output,
        "entry_id": entry.entry_id,
    }
    _print_json(payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lspwb",
        description="Operational helpers for Life-Science PaperWritingBench governance workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_pilot = subparsers.add_parser(
        "validate-pilot",
        help="Validate pilot calibration coverage requirements.",
    )
    validate_pilot.add_argument("--manifest", required=True)
    validate_pilot.add_argument("--output")
    validate_pilot.set_defaults(func=command_validate_pilot)

    validate_calibration = subparsers.add_parser(
        "validate-calibration",
        help="Validate a calibration manifest against pilot, full, or custom coverage targets.",
    )
    validate_calibration.add_argument("--manifest", required=True)
    validate_calibration.add_argument("--mode", choices=("pilot", "full", "custom"), default="full")
    validate_calibration.add_argument("--minimum-total", type=int, default=60)
    validate_calibration.add_argument("--minimum-per-study-class", type=int, default=10)
    validate_calibration.add_argument("--minimum-hybrid", type=int, default=15)
    validate_calibration.add_argument("--minimum-quarantine", type=int, default=6)
    validate_calibration.add_argument("--minimum-controlled-access", type=int, default=8)
    validate_calibration.add_argument("--minimum-negative-or-descriptive", type=int, default=8)
    validate_calibration.add_argument("--output")
    validate_calibration.set_defaults(func=command_validate_calibration)

    write_full_calibration = subparsers.add_parser(
        "write-full-calibration-scaffold",
        help="Write a deterministic 60-paper full calibration scaffold manifest.",
    )
    write_full_calibration.add_argument("--output", required=True)
    write_full_calibration.add_argument("--prefix", default="full")
    write_full_calibration.add_argument("--summary-output")
    write_full_calibration.set_defaults(func=command_write_full_calibration_scaffold)

    init_knowledge_base = subparsers.add_parser(
        "init-knowledge-base",
        help="Initialize the long-run knowledge-base directory layout.",
    )
    init_knowledge_base.add_argument("--root", required=True)
    init_knowledge_base.set_defaults(func=command_init_knowledge_base)

    build_collection = subparsers.add_parser(
        "build-collection-batch",
        help="Write a deterministic collection-batch spec and optional query-spec JSONL.",
    )
    build_collection.add_argument("--output", required=True)
    build_collection.add_argument("--queries-output")
    build_collection.add_argument("--batch-id", default=DEFAULT_COLLECTION_BATCH_ID)
    build_collection.add_argument("--year-start", type=int, default=2018)
    build_collection.add_argument("--year-end", type=int, default=3000)
    build_collection.add_argument("--primary-retmax", type=int, default=120)
    build_collection.add_argument("--reserve-retmax", type=int, default=80)
    build_collection.add_argument("--target-candidates-per-class", type=int, default=50)
    build_collection.set_defaults(func=command_build_collection_batch)

    fetch_pubmed = subparsers.add_parser(
        "fetch-pubmed-batch",
        help="Fetch or replay PubMed seed retrieval for a collection batch into raw artifacts and fetch records.",
    )
    fetch_pubmed.add_argument("--batch-spec", required=True)
    fetch_pubmed.add_argument("--raw-dir", required=True)
    fetch_pubmed.add_argument("--output", required=True)
    fetch_pubmed.add_argument("--summary-output")
    fetch_pubmed.add_argument("--refresh", action="store_true")
    fetch_pubmed.set_defaults(func=command_fetch_pubmed_batch)

    merge_collection = subparsers.add_parser(
        "merge-collection-candidates",
        help="Merge collection fetch records into candidate records using DOI > PMID > PMCID > title/year precedence.",
    )
    merge_collection.add_argument("--input", required=True)
    merge_collection.add_argument("--output", required=True)
    merge_collection.add_argument("--summary-output")
    merge_collection.set_defaults(func=command_merge_collection_candidates)

    enrich_europepmc = subparsers.add_parser(
        "fetch-europepmc-enrichment",
        help="Fetch or replay Europe PMC enrichment for merged collection candidates.",
    )
    enrich_europepmc.add_argument("--input", required=True)
    enrich_europepmc.add_argument("--raw-dir", required=True)
    enrich_europepmc.add_argument("--output", required=True)
    enrich_europepmc.add_argument("--fetch-records-output")
    enrich_europepmc.add_argument("--summary-output")
    enrich_europepmc.add_argument("--refresh", action="store_true")
    enrich_europepmc.set_defaults(func=command_fetch_europepmc_enrichment)

    enrich_crossref = subparsers.add_parser(
        "fetch-crossref-enrichment",
        help="Fetch or replay Crossref enrichment for merged collection candidates.",
    )
    enrich_crossref.add_argument("--input", required=True)
    enrich_crossref.add_argument("--raw-dir", required=True)
    enrich_crossref.add_argument("--output", required=True)
    enrich_crossref.add_argument("--fetch-records-output")
    enrich_crossref.add_argument("--summary-output")
    enrich_crossref.add_argument("--refresh", action="store_true")
    enrich_crossref.set_defaults(func=command_fetch_crossref_enrichment)

    rank_collection = subparsers.add_parser(
        "rank-collection-candidates",
        help="Apply deterministic benchmark-ready ranking to collection candidates.",
    )
    rank_collection.add_argument("--input", required=True)
    rank_collection.add_argument("--output", required=True)
    rank_collection.add_argument("--summary-output")
    rank_collection.set_defaults(func=command_rank_collection_candidates)

    shortlist_collection = subparsers.add_parser(
        "shortlist-collection-candidates",
        help="Shortlist per-class collection candidates and convert them to MetadataSourceRecord artifacts.",
    )
    shortlist_collection.add_argument("--input", required=True)
    shortlist_collection.add_argument("--output", required=True)
    shortlist_collection.add_argument("--metadata-output", required=True)
    shortlist_collection.add_argument("--summary-output")
    shortlist_collection.add_argument("--target-per-class", type=int, default=50)
    shortlist_collection.add_argument("--batch-id", default=DEFAULT_COLLECTION_BATCH_ID)
    shortlist_collection.set_defaults(func=command_shortlist_collection_candidates)

    audit_collection = subparsers.add_parser(
        "audit-collection-batch",
        help="Audit candidate, shortlist, and releaseability coverage for a collection batch.",
    )
    audit_collection.add_argument("--batch-spec", required=True)
    audit_collection.add_argument("--candidates", required=True)
    audit_collection.add_argument("--shortlisted-candidates")
    audit_collection.add_argument("--ingestion-records")
    audit_collection.add_argument("--total-raw-fetch-records", type=int)
    audit_collection.add_argument("--output")
    audit_collection.set_defaults(func=command_audit_collection_batch)

    ingest_metadata = subparsers.add_parser(
        "ingest-metadata",
        help="Standardize local metadata-export records into repo-native ingestion records.",
    )
    ingest_metadata.add_argument("--input", required=True)
    ingest_metadata.add_argument("--output", required=True)
    ingest_metadata.add_argument("--source-name")
    ingest_metadata.add_argument("--summary-output")
    ingest_metadata.set_defaults(func=command_ingest_metadata)

    normalize_papers = subparsers.add_parser(
        "normalize-papers",
        help="Deduplicate standardized metadata records into normalized SourcePaper and IngestionRecord artifacts.",
    )
    normalize_papers.add_argument("--input", required=True)
    normalize_papers.add_argument("--papers-output", required=True)
    normalize_papers.add_argument("--ingestion-output", required=True)
    normalize_papers.add_argument("--audit-output")
    normalize_papers.set_defaults(func=command_normalize_papers)

    audit_ingestion = subparsers.add_parser(
        "audit-ingestion",
        help="Summarize normalized ingestion artifacts for coverage and releaseability signals.",
    )
    audit_ingestion.add_argument("--papers", required=True)
    audit_ingestion.add_argument("--ingestion-records", required=True)
    audit_ingestion.add_argument("--output")
    audit_ingestion.set_defaults(func=command_audit_ingestion)

    verify_ingestion = subparsers.add_parser(
        "verify-ingestion",
        help="Verify dedup precedence, normalized titles, and metadata fingerprints for ingestion artifacts.",
    )
    verify_ingestion.add_argument("--papers", required=True)
    verify_ingestion.add_argument("--ingestion-records", required=True)
    verify_ingestion.add_argument("--output")
    verify_ingestion.set_defaults(func=command_verify_ingestion)

    execution_profile = subparsers.add_parser(
        "write-execution-profile",
        help="Write a local or Cayuga execution profile without changing the repo source of truth.",
    )
    execution_profile.add_argument("--profile", choices=("default", "cayuga"), default="default")
    execution_profile.add_argument("--repo-root", required=True)
    execution_profile.add_argument("--output", required=True)
    execution_profile.add_argument("--python-bin", default="python3")
    execution_profile.add_argument("--working-directory")
    execution_profile.add_argument("--working-directory-name", default="life_science_paperwritingbench_runs")
    execution_profile.add_argument("--cayuga-root")
    execution_profile.set_defaults(func=command_write_execution_profile)

    baseline_replay_job = subparsers.add_parser(
        "write-baseline-replay-job",
        help="Write a scaffold baseline-replay job script and spec from an execution profile.",
    )
    baseline_replay_job.add_argument("--execution-profile", required=True)
    baseline_replay_job.add_argument("--task-bundles", required=True)
    baseline_replay_job.add_argument(
        "--baseline-kind",
        required=True,
        choices=(
            BaselineKind.REFERENCE_TEMPLATE.value,
            BaselineKind.RETRIEVAL_WRITER.value,
            BaselineKind.SECTION_WISE_PIPELINE.value,
        ),
    )
    baseline_replay_job.add_argument("--output-dir", required=True)
    baseline_replay_job.add_argument("--script-output", required=True)
    baseline_replay_job.add_argument("--spec-output", required=True)
    baseline_replay_job.add_argument("--producer-id")
    baseline_replay_job.add_argument("--job-name")
    baseline_replay_job.set_defaults(func=command_write_baseline_replay_job)

    parser_assisted_extraction = subparsers.add_parser(
        "build-parser-assisted-extraction",
        help="Build metadata-driven draft evidence units and extraction specs for later human review.",
    )
    parser_assisted_extraction.add_argument("--papers", required=True)
    parser_assisted_extraction.add_argument("--evidence-units-output", required=True)
    parser_assisted_extraction.add_argument("--specs-output", required=True)
    parser_assisted_extraction.add_argument("--audit-output")
    parser_assisted_extraction.add_argument("--max-assertions-per-unit", type=int, default=3)
    parser_assisted_extraction.set_defaults(func=command_build_parser_assisted_extraction)

    evaluation_extraction = subparsers.add_parser(
        "build-evaluation-extraction",
        help="Build QA-ready observations, questions, answers, and source-quality records from reviewed extraction specs.",
    )
    evaluation_extraction.add_argument("--papers", required=True)
    evaluation_extraction.add_argument("--evidence-units", required=True)
    evaluation_extraction.add_argument("--specs", required=True)
    evaluation_extraction.add_argument("--observations-output", required=True)
    evaluation_extraction.add_argument("--questions-output", required=True)
    evaluation_extraction.add_argument("--answers-output", required=True)
    evaluation_extraction.add_argument("--source-quality-output", required=True)
    evaluation_extraction.add_argument("--audit-output")
    evaluation_extraction.add_argument("--max-questions-per-unit", type=int, default=2)
    evaluation_extraction.set_defaults(func=command_build_evaluation_extraction)

    extract_evidence = subparsers.add_parser(
        "extract-evidence-records",
        help="Build assertion, evidence, and extraction records from semi-structured extraction specs.",
    )
    extract_evidence.add_argument("--papers", required=True)
    extract_evidence.add_argument("--evidence-units", required=True)
    extract_evidence.add_argument("--input", required=True)
    extract_evidence.add_argument("--assertions-output", required=True)
    extract_evidence.add_argument("--evidence-records-output", required=True)
    extract_evidence.add_argument("--extractions-output", required=True)
    extract_evidence.add_argument("--audit-output")
    extract_evidence.add_argument("--default-evidence-type", default="text_span")
    extract_evidence.set_defaults(func=command_extract_evidence_records)

    build_truth_manifests = subparsers.add_parser(
        "build-truth-manifests",
        help="Build unfrozen truth manifests from extraction records.",
    )
    build_truth_manifests.add_argument("--papers", required=True)
    build_truth_manifests.add_argument("--evidence-units", required=True)
    build_truth_manifests.add_argument("--assertions", required=True)
    build_truth_manifests.add_argument("--evidence-records", required=True)
    build_truth_manifests.add_argument("--extractions", required=True)
    build_truth_manifests.add_argument("--output", required=True)
    build_truth_manifests.add_argument("--caveat", action="append")
    build_truth_manifests.set_defaults(func=command_build_truth_manifests)

    freeze_truth_manifests = subparsers.add_parser(
        "freeze-truth-manifests",
        help="Freeze truth manifests after review/adjudication.",
    )
    freeze_truth_manifests.add_argument("--input", required=True)
    freeze_truth_manifests.add_argument("--output", required=True)
    freeze_truth_manifests.add_argument("--frozen-at")
    freeze_truth_manifests.set_defaults(func=command_freeze_truth_manifests)

    verify_truth_manifests = subparsers.add_parser(
        "verify-truth-manifests",
        help="Verify frozen truth manifests against extraction artifacts.",
    )
    verify_truth_manifests.add_argument("--papers", required=True)
    verify_truth_manifests.add_argument("--evidence-units", required=True)
    verify_truth_manifests.add_argument("--assertions", required=True)
    verify_truth_manifests.add_argument("--evidence-records", required=True)
    verify_truth_manifests.add_argument("--extractions", required=True)
    verify_truth_manifests.add_argument("--manifests", required=True)
    verify_truth_manifests.add_argument("--output", required=True)
    verify_truth_manifests.set_defaults(func=command_verify_truth_manifests)

    suggest_metadata = subparsers.add_parser(
        "suggest-metadata-hints",
        help="Suggest study class, overlays, and required standards from source-paper metadata.",
    )
    suggest_metadata.add_argument("--papers", required=True)
    suggest_metadata.add_argument("--output", required=True)
    suggest_metadata.add_argument("--summary-output")
    suggest_metadata.set_defaults(func=command_suggest_metadata_hints)

    build_paper_review = subparsers.add_parser(
        "build-paper-review-batch",
        help="Generate paper-level scientific and writing review scaffolds from qualification-ready papers.",
    )
    build_paper_review.add_argument("--papers", required=True)
    build_paper_review.add_argument("--metadata-hints")
    build_paper_review.add_argument("--entries-output", required=True)
    build_paper_review.add_argument("--scientific-forms-output", required=True)
    build_paper_review.add_argument("--writing-forms-output", required=True)
    build_paper_review.add_argument("--summary-output")
    build_paper_review.add_argument("--batch-id", default="paper_review_v1")
    build_paper_review.add_argument("--reviewers", nargs="+", required=True)
    build_paper_review.set_defaults(func=command_build_paper_review_batch)

    build_paper_packets = subparsers.add_parser(
        "build-paper-review-packets",
        help="Build reviewer-facing paper-review packets by combining entries, source papers, and packaging priors.",
    )
    build_paper_packets.add_argument("--entries", required=True)
    build_paper_packets.add_argument("--papers", required=True)
    build_paper_packets.add_argument("--packaging-reviews", required=True)
    build_paper_packets.add_argument("--output", required=True)
    build_paper_packets.add_argument("--summary-output")
    build_paper_packets.set_defaults(func=command_build_paper_review_packets)

    build_paper_workloads = subparsers.add_parser(
        "build-paper-review-workloads",
        help="Build reviewer-specific paper-review workload files from prioritized packets and reviewer forms.",
    )
    build_paper_workloads.add_argument("--packets", required=True)
    build_paper_workloads.add_argument("--scientific-forms", required=True)
    build_paper_workloads.add_argument("--writing-forms", required=True)
    build_paper_workloads.add_argument("--reviewers", nargs="+", required=True)
    build_paper_workloads.add_argument("--output-dir", required=True)
    build_paper_workloads.set_defaults(func=command_build_paper_review_workloads)

    build_paper_handoff = subparsers.add_parser(
        "build-paper-review-handoff",
        help="Build reviewer-facing handoff summaries and markdown from reviewer assignment files.",
    )
    build_paper_handoff.add_argument("--assignments", nargs="+", required=True)
    build_paper_handoff.add_argument("--reviewers", nargs="+", required=True)
    build_paper_handoff.add_argument("--output-dir", required=True)
    build_paper_handoff.add_argument("--top-priority-count", type=int, default=20)
    build_paper_handoff.set_defaults(func=command_build_paper_review_handoff)

    merge_paper_scientific = subparsers.add_parser(
        "merge-paper-scientific-forms",
        help="Merge duplicate paper scientific-review forms by keeping the latest form per paper/reviewer pair.",
    )
    merge_paper_scientific.add_argument("--inputs", nargs="+", required=True)
    merge_paper_scientific.add_argument("--output", required=True)
    merge_paper_scientific.set_defaults(func=command_merge_paper_scientific_forms)

    merge_paper_writing = subparsers.add_parser(
        "merge-paper-writing-forms",
        help="Merge duplicate paper writing-review forms by keeping the latest form per paper/reviewer pair.",
    )
    merge_paper_writing.add_argument("--inputs", nargs="+", required=True)
    merge_paper_writing.add_argument("--output", required=True)
    merge_paper_writing.set_defaults(func=command_merge_paper_writing_forms)

    build_paper_adjudications = subparsers.add_parser(
        "build-paper-review-adjudication-shells",
        help="Build paper-review adjudication shells from review-batch entries.",
    )
    build_paper_adjudications.add_argument("--entries", required=True)
    build_paper_adjudications.add_argument("--output", required=True)
    build_paper_adjudications.add_argument("--adjudicator", required=True)
    build_paper_adjudications.add_argument("--reviewers", nargs="+", required=True)
    build_paper_adjudications.set_defaults(func=command_build_paper_review_adjudication_shells)

    build_paper_queue = subparsers.add_parser(
        "build-paper-review-queue",
        help="Build a paper-review adjudication queue from entries, forms, and adjudications.",
    )
    build_paper_queue.add_argument("--entries", required=True)
    build_paper_queue.add_argument("--scientific-forms", required=True)
    build_paper_queue.add_argument("--writing-forms", required=True)
    build_paper_queue.add_argument("--adjudications", required=True)
    build_paper_queue.add_argument("--reviewers", nargs="+", required=True)
    build_paper_queue.add_argument("--output", required=True)
    build_paper_queue.set_defaults(func=command_build_paper_review_queue)

    summarize_paper_review = subparsers.add_parser(
        "summarize-paper-review-progress",
        help="Summarize paper-review completion and queue status.",
    )
    summarize_paper_review.add_argument("--entries", required=True)
    summarize_paper_review.add_argument("--scientific-forms", required=True)
    summarize_paper_review.add_argument("--writing-forms", required=True)
    summarize_paper_review.add_argument("--adjudications", required=True)
    summarize_paper_review.add_argument("--reviewers", nargs="+", required=True)
    summarize_paper_review.add_argument("--output")
    summarize_paper_review.set_defaults(func=command_summarize_paper_review_progress)

    finalize_paper_review = subparsers.add_parser(
        "finalize-paper-adjudications",
        help="Finalize adjudicated paper-review records from completed adjudication forms.",
    )
    finalize_paper_review.add_argument("--adjudications", required=True)
    finalize_paper_review.add_argument("--output", required=True)
    finalize_paper_review.set_defaults(func=command_finalize_paper_adjudications)

    build_packaging_priors = subparsers.add_parser(
        "build-packaging-review-priors",
        help="Build deterministic packaging-review priors from source-paper metadata.",
    )
    build_packaging_priors.add_argument("--papers", required=True)
    build_packaging_priors.add_argument("--output", required=True)
    build_packaging_priors.add_argument("--summary-output")
    build_packaging_priors.set_defaults(func=command_build_packaging_review_priors)

    build_paper_decisions = subparsers.add_parser(
        "build-paper-qualification-decisions",
        help="Build paper qualification decisions from finalized adjudicated reviews and packaging priors.",
    )
    build_paper_decisions.add_argument("--papers", required=True)
    build_paper_decisions.add_argument("--adjudicated-reviews", required=True)
    build_paper_decisions.add_argument("--packaging-reviews", required=True)
    build_paper_decisions.add_argument("--output", required=True)
    build_paper_decisions.add_argument("--summary-output")
    build_paper_decisions.set_defaults(func=command_build_paper_qualification_decisions)

    build_auto_evidence = subparsers.add_parser(
        "build-auto-review-evidence-enrichments",
        help="Fetch PMC full-text XML and extract methods/results/caption evidence for auto review.",
    )
    build_auto_evidence.add_argument("--papers", required=True)
    build_auto_evidence.add_argument("--raw-dir", required=True)
    build_auto_evidence.add_argument("--output", required=True)
    build_auto_evidence.add_argument("--fetch-records-output")
    build_auto_evidence.add_argument("--summary-output")
    build_auto_evidence.add_argument("--refresh", action="store_true")
    build_auto_evidence.set_defaults(func=command_build_auto_review_evidence_enrichments)

    materialize_enriched_papers = subparsers.add_parser(
        "materialize-enriched-source-papers",
        help="Overlay auto-review evidence enrichments onto source-paper metadata for downstream extraction.",
    )
    materialize_enriched_papers.add_argument("--papers", required=True)
    materialize_enriched_papers.add_argument("--evidence-enrichments", required=True)
    materialize_enriched_papers.add_argument("--output", required=True)
    materialize_enriched_papers.set_defaults(func=command_materialize_enriched_source_papers)

    build_auto_source_bundles = subparsers.add_parser(
        "build-auto-review-source-bundles",
        help="Build auto-review source bundles from source papers and enriched metadata.",
    )
    build_auto_source_bundles.add_argument("--papers", required=True)
    build_auto_source_bundles.add_argument("--evidence-enrichments")
    build_auto_source_bundles.add_argument("--output", required=True)
    build_auto_source_bundles.add_argument("--summary-output")
    build_auto_source_bundles.add_argument("--refresh", action="store_true")
    build_auto_source_bundles.set_defaults(func=command_build_auto_review_source_bundles)

    audit_auto_source_bundles = subparsers.add_parser(
        "audit-auto-review-source-bundles",
        help="Audit auto-review source bundles for completeness and provenance coverage.",
    )
    audit_auto_source_bundles.add_argument("--source-bundles", required=True)
    audit_auto_source_bundles.add_argument("--output")
    audit_auto_source_bundles.set_defaults(func=command_audit_auto_review_source_bundles)

    run_auto_reviews = subparsers.add_parser(
        "run-auto-paper-reviews",
        help="Run deterministic auto-review panel votes from source bundles and an execution profile.",
    )
    run_auto_reviews.add_argument("--papers", required=True)
    run_auto_reviews.add_argument("--source-bundles", required=True)
    run_auto_reviews.add_argument("--execution-profile", required=True)
    run_auto_reviews.add_argument("--model-id", required=True)
    run_auto_reviews.add_argument("--packaging-reviews")
    run_auto_reviews.add_argument("--output", required=True)
    run_auto_reviews.add_argument("--summary-output")
    run_auto_reviews.add_argument("--temperature", type=float, default=0.0)
    run_auto_reviews.add_argument("--top-p", type=float, default=1.0)
    run_auto_reviews.add_argument("--seed", type=int, default=0)
    run_auto_reviews.add_argument("--refresh", action="store_true")
    run_auto_reviews.set_defaults(func=command_run_auto_paper_reviews)

    aggregate_auto_reviews = subparsers.add_parser(
        "aggregate-auto-paper-reviews",
        help="Aggregate auto-review panel votes into scientific and writing proxy reviews.",
    )
    aggregate_auto_reviews.add_argument("--papers", required=True)
    aggregate_auto_reviews.add_argument("--source-bundles", required=True)
    aggregate_auto_reviews.add_argument("--panel-votes", required=True)
    aggregate_auto_reviews.add_argument("--output", required=True)
    aggregate_auto_reviews.add_argument("--summary-output")
    aggregate_auto_reviews.add_argument("--refresh", action="store_true")
    aggregate_auto_reviews.set_defaults(func=command_aggregate_auto_paper_reviews)

    build_auto_decisions = subparsers.add_parser(
        "build-auto-paper-qualification-decisions",
        help="Build shadow-first auto-only paper qualification decisions from aggregated auto reviews.",
    )
    build_auto_decisions.add_argument("--papers", required=True)
    build_auto_decisions.add_argument("--source-bundles", required=True)
    build_auto_decisions.add_argument("--aggregated-reviews", required=True)
    build_auto_decisions.add_argument("--packaging-reviews", required=True)
    build_auto_decisions.add_argument("--output", required=True)
    build_auto_decisions.add_argument("--summary-output")
    build_auto_decisions.set_defaults(func=command_build_auto_paper_qualification_decisions)

    summarize_auto_reviews = subparsers.add_parser(
        "summarize-auto-review-batch",
        help="Summarize source-bundle, panel-vote, aggregation, and qualification coverage for auto review.",
    )
    summarize_auto_reviews.add_argument("--papers", required=True)
    summarize_auto_reviews.add_argument("--source-bundles")
    summarize_auto_reviews.add_argument("--panel-votes")
    summarize_auto_reviews.add_argument("--aggregated-reviews")
    summarize_auto_reviews.add_argument("--qualifications")
    summarize_auto_reviews.add_argument("--output")
    summarize_auto_reviews.set_defaults(func=command_summarize_auto_review_batch)

    build_auto_recovery_batch = subparsers.add_parser(
        "build-auto-review-recovery-batch",
        help="Select a deterministic, class-balanced shadow-recovery batch from an auto-review recovery queue.",
    )
    build_auto_recovery_batch.add_argument("--recovery-queue", required=True)
    build_auto_recovery_batch.add_argument("--papers")
    build_auto_recovery_batch.add_argument("--packaging-reviews")
    build_auto_recovery_batch.add_argument("--output", required=True)
    build_auto_recovery_batch.add_argument("--summary-output")
    build_auto_recovery_batch.add_argument("--selected-papers-output")
    build_auto_recovery_batch.add_argument("--selected-packaging-reviews-output")
    build_auto_recovery_batch.add_argument(
        "--preferred-buckets",
        nargs="+",
        default=("near_shadow_scientific_borderline",),
    )
    build_auto_recovery_batch.add_argument(
        "--exclude-selected-entries",
        action="append",
        default=[],
        help="JSONL files of prior recovery batch entries to exclude by paper_id.",
    )
    build_auto_recovery_batch.add_argument(
        "--strict-preferred-buckets",
        action="store_true",
        help="Only select papers from preferred buckets; do not backfill from other priority buckets.",
    )
    build_auto_recovery_batch.add_argument("--target-total", type=int, default=30)
    build_auto_recovery_batch.add_argument("--per-class-target", type=int, default=5)
    build_auto_recovery_batch.set_defaults(func=command_build_auto_review_recovery_batch)

    write_auto_recovery_job = subparsers.add_parser(
        "write-auto-review-recovery-job",
        help="Write a Cayuga/local execution job scaffold for rerunning a selected auto-review recovery batch.",
    )
    write_auto_recovery_job.add_argument("--execution-profile", required=True)
    write_auto_recovery_job.add_argument("--papers", required=True)
    write_auto_recovery_job.add_argument("--packaging-reviews", required=True)
    write_auto_recovery_job.add_argument("--output-dir", required=True)
    write_auto_recovery_job.add_argument("--job-spec-output", required=True)
    write_auto_recovery_job.add_argument("--script-output", required=True)
    write_auto_recovery_job.add_argument("--model-id", required=True)
    write_auto_recovery_job.add_argument("--raw-dir")
    write_auto_recovery_job.add_argument("--job-name")
    write_auto_recovery_job.set_defaults(func=command_write_auto_review_recovery_job)

    build_templates = subparsers.add_parser(
        "build-pilot-templates",
        help="Generate blank reviewer-form and adjudication template JSONL files.",
    )
    build_templates.add_argument("--manifest", required=True)
    build_templates.add_argument("--forms-output", required=True)
    build_templates.add_argument("--adjudication-output", required=True)
    build_templates.add_argument("--adjudicator", required=True)
    build_templates.add_argument("--reviewers", nargs="+", required=True)
    build_templates.set_defaults(func=command_build_pilot_templates)

    build_calibration = subparsers.add_parser(
        "build-calibration-batch",
        help="Build reviewer-form and adjudication templates for a pilot or full calibration manifest.",
    )
    build_calibration.add_argument("--manifest", required=True)
    build_calibration.add_argument("--forms-output", required=True)
    build_calibration.add_argument("--adjudication-output", required=True)
    build_calibration.add_argument("--adjudicator", required=True)
    build_calibration.add_argument("--reviewers", nargs="+", required=True)
    build_calibration.add_argument("--mode", choices=("pilot", "full"), default="full")
    build_calibration.add_argument("--allow-invalid", action="store_true")
    build_calibration.add_argument("--summary-output")
    build_calibration.set_defaults(func=command_build_calibration_batch)

    merge_forms = subparsers.add_parser(
        "merge-review-forms",
        help="Merge duplicate review-form uploads by keeping the latest form per calibration/reviewer pair.",
    )
    merge_forms.add_argument("--inputs", nargs="+", required=True)
    merge_forms.add_argument("--output", required=True)
    merge_forms.set_defaults(func=command_merge_review_forms)

    adjudication_queue = subparsers.add_parser(
        "build-adjudication-queue",
        help="Build an adjudication queue from calibration specs, reviewer forms, and adjudication records.",
    )
    adjudication_queue.add_argument("--manifest", required=True)
    adjudication_queue.add_argument("--forms", required=True)
    adjudication_queue.add_argument("--adjudications", required=True)
    adjudication_queue.add_argument("--reviewers", nargs="+", required=True)
    adjudication_queue.add_argument("--output", required=True)
    adjudication_queue.set_defaults(func=command_build_adjudication_queue)

    summarize_agreement = subparsers.add_parser(
        "summarize-pilot-agreement",
        help="Compute pilot agreement against adjudicated labels.",
    )
    summarize_agreement.add_argument("--forms", required=True)
    summarize_agreement.add_argument("--adjudications", required=True)
    summarize_agreement.add_argument("--output")
    summarize_agreement.set_defaults(func=command_summarize_pilot_agreement)

    summarize_calibration = subparsers.add_parser(
        "summarize-calibration",
        help="Summarize coverage, review completion, queue status, and agreement for a calibration batch.",
    )
    summarize_calibration.add_argument("--manifest", required=True)
    summarize_calibration.add_argument("--forms", required=True)
    summarize_calibration.add_argument("--adjudications", required=True)
    summarize_calibration.add_argument("--reviewers", nargs="+", required=True)
    summarize_calibration.add_argument("--output")
    summarize_calibration.set_defaults(func=command_summarize_calibration)

    calibration_drift = subparsers.add_parser(
        "audit-calibration-drift",
        help="Audit drift between two calibration manifests.",
    )
    calibration_drift.add_argument("--baseline-manifest", required=True)
    calibration_drift.add_argument("--updated-manifest", required=True)
    calibration_drift.add_argument("--output")
    calibration_drift.set_defaults(func=command_audit_calibration_drift)

    build_release = subparsers.add_parser(
        "build-release-index",
        help="Build a release index with holdout buckets and canary strings.",
    )
    build_release.add_argument("--units", required=True)
    build_release.add_argument("--decisions", required=True)
    build_release.add_argument("--output", required=True)
    build_release.add_argument("--public-ratio", type=float, default=0.8)
    build_release.add_argument("--private-ratio", type=float, default=0.2)
    build_release.add_argument("--holdout-salt", default="ls-pwb-holdout-v1")
    build_release.add_argument("--canary-prefix", default="LS-PWB-CANARY")
    build_release.add_argument("--canary-salt", default="ls-pwb-canary-v1")
    build_release.add_argument("--allow-split-safety-violations", action="store_true")
    build_release.set_defaults(func=command_build_release_index)

    build_bundle = subparsers.add_parser(
        "build-release-bundle",
        help="Build a release bundle with index, summary, and split-safety artifacts.",
    )
    build_bundle.add_argument("--units", required=True)
    build_bundle.add_argument("--decisions", required=True)
    build_bundle.add_argument("--output-dir", required=True)
    build_bundle.add_argument("--public-ratio", type=float, default=0.8)
    build_bundle.add_argument("--private-ratio", type=float, default=0.2)
    build_bundle.add_argument("--holdout-salt", default="ls-pwb-holdout-v1")
    build_bundle.add_argument("--canary-prefix", default="LS-PWB-CANARY")
    build_bundle.add_argument("--canary-salt", default="ls-pwb-canary-v1")
    build_bundle.add_argument("--allow-split-safety-violations", action="store_true")
    build_bundle.set_defaults(func=command_build_release_bundle)

    verify_bundle = subparsers.add_parser(
        "verify-release-bundle",
        help="Verify checksums, summary consistency, and provenance consistency for a release bundle.",
    )
    verify_bundle.add_argument("--bundle-dir", required=True)
    verify_bundle.add_argument("--output")
    verify_bundle.set_defaults(func=command_verify_release_bundle)

    build_benchmark_units_parser = subparsers.add_parser(
        "build-benchmark-units-from-evidence",
        help="Build one-to-one BenchmarkUnit artifacts from EvidenceUnit inputs.",
    )
    build_benchmark_units_parser.add_argument("--evidence-units", required=True)
    build_benchmark_units_parser.add_argument("--output", required=True)
    build_benchmark_units_parser.add_argument("--papers")
    build_benchmark_units_parser.add_argument("--benchmark-unit-id-prefix", default="BU")
    build_benchmark_units_parser.add_argument("--default-split")
    build_benchmark_units_parser.set_defaults(func=command_build_benchmark_units_from_evidence)

    build_benchmark_unit_decisions_parser = subparsers.add_parser(
        "build-benchmark-unit-decisions-from-auto-review",
        help="Build BenchmarkUnitDecisionRecord artifacts from auto-review paper qualification outputs.",
    )
    build_benchmark_unit_decisions_parser.add_argument("--benchmark-units", required=True)
    build_benchmark_unit_decisions_parser.add_argument("--auto-qualifications", required=True)
    build_benchmark_unit_decisions_parser.add_argument("--output", required=True)
    build_benchmark_unit_decisions_parser.add_argument("--include-stress-candidates", action="store_true")
    build_benchmark_unit_decisions_parser.set_defaults(
        func=command_build_benchmark_unit_decisions_from_auto_review
    )

    build_task_bundle_parser = subparsers.add_parser(
        "build-task-bundles",
        help="Build TaskBundle and TruthManifestBundle artifacts from benchmark inputs.",
    )
    build_task_bundle_parser.add_argument("--papers", required=True)
    build_task_bundle_parser.add_argument("--evidence-units", required=True)
    build_task_bundle_parser.add_argument("--benchmark-units", required=True)
    build_task_bundle_parser.add_argument("--truth-manifests", required=True)
    build_task_bundle_parser.add_argument("--decisions", required=True)
    build_task_bundle_parser.add_argument("--output", required=True)
    build_task_bundle_parser.add_argument("--truth-manifest-bundles-output")
    build_task_bundle_parser.add_argument("--provenance-manifest-id")
    build_task_bundle_parser.set_defaults(func=command_build_task_bundles)

    annotate_task_bundles_parser = subparsers.add_parser(
        "annotate-task-bundles-with-release-index",
        help="Apply holdout bucket and release tier metadata from a release index onto TaskBundle artifacts.",
    )
    annotate_task_bundles_parser.add_argument("--task-bundles", required=True)
    annotate_task_bundles_parser.add_argument("--release-index", required=True)
    annotate_task_bundles_parser.add_argument("--output", required=True)
    annotate_task_bundles_parser.add_argument("--summary-output")
    annotate_task_bundles_parser.add_argument("--allow-missing-release-index-entries", action="store_true")
    annotate_task_bundles_parser.set_defaults(func=command_annotate_task_bundles_with_release_index)

    build_evaluation_task_bundle_parser = subparsers.add_parser(
        "build-evaluation-task-bundles",
        help="Build TaskBundle artifacts from QA-oriented evaluation extraction records.",
    )
    build_evaluation_task_bundle_parser.add_argument("--papers", required=True)
    build_evaluation_task_bundle_parser.add_argument("--observations", required=True)
    build_evaluation_task_bundle_parser.add_argument("--questions", required=True)
    build_evaluation_task_bundle_parser.add_argument("--answers", required=True)
    build_evaluation_task_bundle_parser.add_argument("--truth-manifests", required=True)
    build_evaluation_task_bundle_parser.add_argument("--output", required=True)
    build_evaluation_task_bundle_parser.add_argument("--source-quality-records")
    build_evaluation_task_bundle_parser.add_argument("--provenance-manifest-id")
    build_evaluation_task_bundle_parser.add_argument(
        "--default-release-tier",
        choices=(
            ReleaseTier.PUBLIC_GOLD.value,
            ReleaseTier.SHADOW_GOLD.value,
            ReleaseTier.STRESS_ONLY.value,
        ),
        default=ReleaseTier.SHADOW_GOLD.value,
    )
    build_evaluation_task_bundle_parser.set_defaults(func=command_build_evaluation_task_bundles)

    build_judge_slice = subparsers.add_parser(
        "build-judge-slice",
        help="Build a deterministic judge-validation slice template from TaskBundle artifacts.",
    )
    build_judge_slice.add_argument("--task-bundles", required=True)
    build_judge_slice.add_argument("--output", required=True)
    build_judge_slice.add_argument("--target-total", type=int, default=30)
    build_judge_slice.add_argument(
        "--task-family",
        action="append",
        choices=tuple(task_family.value for task_family in TaskFamily),
    )
    build_judge_slice.add_argument(
        "--release-tier",
        action="append",
        choices=(
            ReleaseTier.PUBLIC_GOLD.value,
            ReleaseTier.SHADOW_GOLD.value,
            ReleaseTier.STRESS_ONLY.value,
        ),
    )
    build_judge_slice.add_argument("--holdout-bucket", action="append")
    build_judge_slice.add_argument("--human-adjudicated", action="store_true")
    build_judge_slice.add_argument("--freeze", action="store_true")
    build_judge_slice.set_defaults(func=command_build_judge_slice)

    audit_judge_slice = subparsers.add_parser(
        "audit-judge-slice",
        help="Audit whether a judge-validation slice is human-adjudicated, frozen, and rubric-complete.",
    )
    audit_judge_slice.add_argument("--task-bundles", required=True)
    audit_judge_slice.add_argument("--judge-units", required=True)
    audit_judge_slice.add_argument("--minimum-total", type=int, default=30)
    audit_judge_slice.add_argument("--output")
    audit_judge_slice.set_defaults(func=command_audit_judge_slice)

    audit_llm_eval_alignment = subparsers.add_parser(
        "audit-llm-eval-alignment",
        help="Audit bundle-level agreement between deterministic scoring and judge pass/fail outcomes.",
    )
    audit_llm_eval_alignment.add_argument("--task-bundles", required=True)
    audit_llm_eval_alignment.add_argument("--evaluations", required=True)
    audit_llm_eval_alignment.add_argument("--judgments", required=True)
    audit_llm_eval_alignment.add_argument("--output")
    audit_llm_eval_alignment.add_argument("--markdown-output")
    audit_llm_eval_alignment.set_defaults(func=command_audit_llm_eval_alignment)

    build_judge_templates = subparsers.add_parser(
        "build-judge-review-templates",
        help="Generate blank judge-review and judge-adjudication template JSONL files.",
    )
    build_judge_templates.add_argument("--judge-units", required=True)
    build_judge_templates.add_argument("--forms-output", required=True)
    build_judge_templates.add_argument("--adjudication-output", required=True)
    build_judge_templates.add_argument("--adjudicator", required=True)
    build_judge_templates.add_argument("--reviewers", nargs="+", required=True)
    build_judge_templates.set_defaults(func=command_build_judge_review_templates)

    merge_judge_forms = subparsers.add_parser(
        "merge-judge-review-forms",
        help="Merge duplicate judge-review form uploads by keeping the latest form per unit/reviewer pair.",
    )
    merge_judge_forms.add_argument("--inputs", nargs="+", required=True)
    merge_judge_forms.add_argument("--output", required=True)
    merge_judge_forms.set_defaults(func=command_merge_judge_review_forms)

    judge_adjudication_queue = subparsers.add_parser(
        "build-judge-adjudication-queue",
        help="Build an adjudication queue for judge-validation units from judge review forms.",
    )
    judge_adjudication_queue.add_argument("--judge-units", required=True)
    judge_adjudication_queue.add_argument("--forms", required=True)
    judge_adjudication_queue.add_argument("--adjudications", required=True)
    judge_adjudication_queue.add_argument("--reviewers", nargs="+", required=True)
    judge_adjudication_queue.add_argument("--output", required=True)
    judge_adjudication_queue.set_defaults(func=command_build_judge_adjudication_queue)

    finalize_judge_slice = subparsers.add_parser(
        "finalize-judge-slice",
        help="Apply finalized judge adjudications back onto judge-validation units.",
    )
    finalize_judge_slice.add_argument("--judge-units", required=True)
    finalize_judge_slice.add_argument("--adjudications", required=True)
    finalize_judge_slice.add_argument("--output", required=True)
    finalize_judge_slice.set_defaults(func=command_finalize_judge_slice)

    build_judge_batch = subparsers.add_parser(
        "build-judge-batch",
        help="Build a full judge-validation batch directory from TaskBundle artifacts.",
    )
    build_judge_batch.add_argument("--task-bundles", required=True)
    build_judge_batch.add_argument("--output-dir", required=True)
    build_judge_batch.add_argument("--target-total", type=int, default=30)
    build_judge_batch.add_argument(
        "--task-family",
        action="append",
        choices=tuple(task_family.value for task_family in TaskFamily),
    )
    build_judge_batch.add_argument(
        "--release-tier",
        action="append",
        choices=(
            ReleaseTier.PUBLIC_GOLD.value,
            ReleaseTier.SHADOW_GOLD.value,
            ReleaseTier.STRESS_ONLY.value,
        ),
    )
    build_judge_batch.add_argument("--holdout-bucket", action="append")
    build_judge_batch.add_argument("--adjudicator", required=True)
    build_judge_batch.add_argument("--reviewers", nargs="+", required=True)
    build_judge_batch.set_defaults(func=command_build_judge_batch)

    summarize_task_bundle_inventory = subparsers.add_parser(
        "summarize-task-bundles",
        help="Summarize task-bundle coverage across family, study class, claim mode, tier, and holdout bucket.",
    )
    summarize_task_bundle_inventory.add_argument("--task-bundles", required=True)
    summarize_task_bundle_inventory.add_argument("--output")
    summarize_task_bundle_inventory.set_defaults(func=command_summarize_task_bundles)

    select_judge_candidates = subparsers.add_parser(
        "select-judge-candidates",
        help="Select a deterministic, diverse set of judge-candidate TaskBundle artifacts.",
    )
    select_judge_candidates.add_argument("--task-bundles", required=True)
    select_judge_candidates.add_argument("--output", required=True)
    select_judge_candidates.add_argument("--summary-output")
    select_judge_candidates.add_argument("--target-total", type=int, default=30)
    select_judge_candidates.add_argument(
        "--task-family",
        action="append",
        choices=tuple(task_family.value for task_family in TaskFamily),
    )
    select_judge_candidates.add_argument(
        "--release-tier",
        action="append",
        choices=(
            ReleaseTier.PUBLIC_GOLD.value,
            ReleaseTier.SHADOW_GOLD.value,
            ReleaseTier.STRESS_ONLY.value,
        ),
    )
    select_judge_candidates.add_argument("--holdout-bucket", action="append")
    select_judge_candidates.set_defaults(func=command_select_judge_candidates)

    build_shadow_inspection = subparsers.add_parser(
        "build-shadow-inspection-batch",
        help="Select a deterministic public-shadow inspection slice with markdown-ready context.",
    )
    build_shadow_inspection.add_argument("--task-bundles", required=True)
    build_shadow_inspection.add_argument("--papers", required=True)
    build_shadow_inspection.add_argument("--auto-qualification-records", required=True)
    build_shadow_inspection.add_argument("--source-bundles", required=True)
    build_shadow_inspection.add_argument("--output", required=True)
    build_shadow_inspection.add_argument("--summary-output")
    build_shadow_inspection.add_argument("--markdown-output")
    build_shadow_inspection.add_argument("--target-total", type=int, default=30)
    build_shadow_inspection.add_argument("--holdout-bucket", action="append")
    build_shadow_inspection.set_defaults(func=command_build_shadow_inspection_batch)

    summarize_shadow_taxonomy = subparsers.add_parser(
        "summarize-shadow-inspection-taxonomy",
        help="Group a shadow inspection slice into overlapping failure and refinement categories.",
    )
    summarize_shadow_taxonomy.add_argument("--inspection-entries", required=True)
    summarize_shadow_taxonomy.add_argument("--output", required=True)
    summarize_shadow_taxonomy.add_argument("--markdown-output")
    summarize_shadow_taxonomy.add_argument("--minimum-entry-count", type=int, default=1)
    summarize_shadow_taxonomy.set_defaults(func=command_summarize_shadow_inspection_taxonomy)

    compare_shadow_inspection = subparsers.add_parser(
        "compare-shadow-inspection-runs",
        help="Compare two shadow inspection slices and their taxonomy reports.",
    )
    compare_shadow_inspection.add_argument("--previous-summary", required=True)
    compare_shadow_inspection.add_argument("--current-summary", required=True)
    compare_shadow_inspection.add_argument("--previous-taxonomy", required=True)
    compare_shadow_inspection.add_argument("--current-taxonomy", required=True)
    compare_shadow_inspection.add_argument("--previous-label", default="previous")
    compare_shadow_inspection.add_argument("--current-label", default="current")
    compare_shadow_inspection.add_argument("--output", required=True)
    compare_shadow_inspection.set_defaults(func=command_compare_shadow_inspection_runs)

    summarize_judge = subparsers.add_parser(
        "summarize-judge-progress",
        help="Summarize judge-slice readiness, review completion, and adjudication queue status.",
    )
    summarize_judge.add_argument("--task-bundles", required=True)
    summarize_judge.add_argument("--judge-units", required=True)
    summarize_judge.add_argument("--forms", required=True)
    summarize_judge.add_argument("--adjudications", required=True)
    summarize_judge.add_argument("--reviewers", nargs="+", required=True)
    summarize_judge.add_argument("--minimum-total", type=int, default=30)
    summarize_judge.add_argument("--output")
    summarize_judge.set_defaults(func=command_summarize_judge_progress)

    run_baseline_parser = subparsers.add_parser(
        "run-baseline",
        help="Run a deterministic lean baseline over TaskBundle artifacts.",
    )
    run_baseline_parser.add_argument("--task-bundles", required=True)
    run_baseline_parser.add_argument(
        "--baseline-kind",
        required=True,
        choices=(
            BaselineKind.REFERENCE_TEMPLATE.value,
            BaselineKind.RETRIEVAL_WRITER.value,
            BaselineKind.SECTION_WISE_PIPELINE.value,
        ),
    )
    run_baseline_parser.add_argument("--producer-id")
    run_baseline_parser.add_argument("--submissions-output", required=True)
    run_baseline_parser.add_argument("--run-spec-output", required=True)
    run_baseline_parser.set_defaults(func=command_run_baseline)

    score_submissions_parser = subparsers.add_parser(
        "score-submissions",
        help="Run deterministic scoring over submission artifacts for TaskBundle inputs.",
    )
    score_submissions_parser.add_argument("--task-bundles", required=True)
    score_submissions_parser.add_argument("--submissions", required=True)
    score_submissions_parser.add_argument("--output", required=True)
    score_submissions_parser.add_argument(
        "--scoring-version",
        choices=("v1", "v2"),
        default="v2",
        help="v2 (default) uses citation-specificity. v1 preserves the pre-2026-04 pointer-token scoring for reproducibility of legacy release artifacts.",
    )
    score_submissions_parser.set_defaults(func=command_score_submissions)

    baseline_inventory = subparsers.add_parser(
        "build-baseline-run-inventory",
        help="Merge baseline run spec artifacts into a deduplicated JSONL inventory.",
    )
    baseline_inventory.add_argument("--run-spec", action="append", required=True)
    baseline_inventory.add_argument("--output", required=True)
    baseline_inventory.set_defaults(func=command_build_baseline_run_inventory)

    summarize_program = subparsers.add_parser(
        "summarize-program-progress",
        help="Summarize progress against the long-run benchmark program gates.",
    )
    summarize_program.add_argument("--papers", required=True)
    summarize_program.add_argument("--paper-decisions", required=True)
    summarize_program.add_argument("--task-bundles", required=True)
    summarize_program.add_argument("--judge-validation-units")
    summarize_program.add_argument("--baseline-runs")
    summarize_program.add_argument("--output")
    summarize_program.set_defaults(func=command_summarize_program_progress)

    maintenance_log = subparsers.add_parser(
        "build-maintenance-log-entry",
        help="Create a maintenance log JSONL entry for a release or audit event.",
    )
    maintenance_log.add_argument("--phase", required=True)
    maintenance_log.add_argument("--summary", required=True)
    maintenance_log.add_argument("--release-bundle-id")
    maintenance_log.add_argument("--artifacts", nargs="*")
    maintenance_log.add_argument("--notes", nargs="*")
    maintenance_log.add_argument("--output", required=True)
    maintenance_log.set_defaults(func=command_build_maintenance_log_entry)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        _print_json(
            {
                "ok": False,
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
