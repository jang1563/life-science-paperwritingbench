from __future__ import annotations

import hashlib
import shlex
from pathlib import Path
from typing import Optional, Sequence

from .frontier_runtime import load_frontier_model
from .models import ExecutionJobSpec, ExecutionProfile
from .policy import BaselineKind


def build_cayuga_execution_profile(
    cayuga_root: str,
    repo_root: str,
    working_directory_name: str = "life_science_paperwritingbench_runs",
    python_bin: str = "python3",
) -> ExecutionProfile:
    cayuga_path = Path(cayuga_root).expanduser()
    repo_path = Path(repo_root).expanduser()
    working_directory = cayuga_path / working_directory_name
    digest = hashlib.sha256(
        f"cayuga:{cayuga_path}:{repo_path}:{working_directory}".encode("utf-8")
    ).hexdigest()[:12].upper()
    return ExecutionProfile(
        profile_id=f"EXEC:{digest}",
        profile_name="cayuga",
        backend="slurm",
        root_path=str(cayuga_path),
        repo_root=str(repo_path),
        working_directory=str(working_directory),
        python_bin=python_bin,
        launch_prefix=("sbatch",),
        environment_exports={
            "LSPWB_REPO_ROOT": str(repo_path),
            "LSPWB_KB_ROOT": str(repo_path / "knowledge_base"),
            "LSPWB_WORKDIR": str(working_directory),
            "LSPWB_CAYUGA_ROOT": str(cayuga_path),
        },
        notes=(
            "Cayuga profile is scaffold-only; the repository remains the source of truth.",
            "Use this profile for large replay or blind-eval wrappers, not for direct artifact editing inside the cluster root.",
        ),
    )


def default_execution_profile(
    repo_root: str,
    python_bin: str = "python3",
    working_directory: Optional[str] = None,
) -> ExecutionProfile:
    repo_path = Path(repo_root).expanduser()
    workdir = Path(working_directory).expanduser() if working_directory else repo_path
    digest = hashlib.sha256(f"default:{repo_path}:{workdir}".encode("utf-8")).hexdigest()[:12].upper()
    return ExecutionProfile(
        profile_id=f"EXEC:{digest}",
        profile_name="default",
        backend="local",
        root_path=str(repo_path),
        repo_root=str(repo_path),
        working_directory=str(workdir),
        python_bin=python_bin,
        launch_prefix=(),
        environment_exports={
            "LSPWB_REPO_ROOT": str(repo_path),
            "LSPWB_KB_ROOT": str(repo_path / "knowledge_base"),
            "LSPWB_WORKDIR": str(workdir),
        },
        notes=("Default local execution profile for file-and-CLI batch workflows.",),
    )


def _job_digest(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:12].upper()


def _quote(value: str) -> str:
    return shlex.quote(str(value))


def build_baseline_replay_job_spec(
    profile: ExecutionProfile,
    *,
    task_bundles_path: str,
    baseline_kind: BaselineKind,
    output_dir: str,
    producer_id: Optional[str] = None,
    job_name: Optional[str] = None,
) -> ExecutionJobSpec:
    output_path = Path(output_dir).expanduser()
    submissions_output = output_path / "submissions.jsonl"
    run_spec_output = output_path / "baseline_run.jsonl"
    evaluations_output = output_path / "evaluations.jsonl"
    resolved_job_name = job_name or f"lspwb-{baseline_kind.value.replace('_', '-')}"
    job_id = f"JOB:{_job_digest(profile.profile_id, baseline_kind.value, str(output_path), str(task_bundles_path))}"

    run_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli run-baseline "
        f"--task-bundles {_quote(task_bundles_path)} "
        f"--baseline-kind {_quote(baseline_kind.value)} "
        f"--submissions-output {_quote(str(submissions_output))} "
        f"--run-spec-output {_quote(str(run_spec_output))}"
    )
    if producer_id:
        run_command += f" --producer-id {_quote(producer_id)}"

    score_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli score-submissions "
        f"--task-bundles {_quote(task_bundles_path)} "
        f"--submissions {_quote(str(submissions_output))} "
        f"--output {_quote(str(evaluations_output))}"
    )

    return ExecutionJobSpec(
        job_id=job_id,
        job_name=resolved_job_name,
        profile_id=profile.profile_id,
        job_kind="baseline_replay",
        backend=profile.backend,
        working_directory=profile.working_directory,
        command_sequence=(
            f"mkdir -p {_quote(str(output_path))}",
            f"cd {_quote(profile.repo_root)}",
            run_command,
            score_command,
        ),
        environment_exports=dict(profile.environment_exports),
        output_artifacts={
            "task_bundles": str(Path(task_bundles_path).expanduser()),
            "output_dir": str(output_path),
            "submissions": str(submissions_output),
            "baseline_run": str(run_spec_output),
            "evaluations": str(evaluations_output),
        },
        notes=(
            "Scaffold-only execution job for deterministic baseline replay.",
            "Generated scripts should be reviewed before cluster submission.",
        ),
    )


def build_frontier_submitter_job_spec(
    profile: ExecutionProfile,
    *,
    registry_path: str,
    model_label: str,
    runner_kind: str,
    task_source: str,
    output_dir: str,
    keys_file: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 1200,
    pause_between_calls: float = 0.0,
    dry_run: bool = False,
    endpoint_url: Optional[str] = None,
    served_model_name: Optional[str] = None,
    tensor_parallel_size: Optional[int] = None,
    gpu_count: Optional[int] = None,
    dtype_note: Optional[str] = None,
    scheduler_notes: Sequence[str] = (),
    job_name: Optional[str] = None,
) -> ExecutionJobSpec:
    if runner_kind not in {"smoke", "agentic"}:
        raise ValueError("runner_kind must be 'smoke' or 'agentic'")
    if task_source not in {"smoke", "inspection-slice"}:
        raise ValueError("task_source must be 'smoke' or 'inspection-slice'")

    provider = load_frontier_model(model_label, registry_path=registry_path, role="submitter", env={})
    if provider.get("backend_type") == "vllm_http":
        if not endpoint_url:
            raise ValueError("endpoint_url is required for vllm_http submitter jobs")
        if not served_model_name:
            raise ValueError("served_model_name is required for vllm_http submitter jobs")

    output_path = Path(output_dir).expanduser()
    script_name = "llm_agentic_eval.py" if runner_kind == "agentic" else "llm_smoke_eval.py"
    resolved_job_name = job_name or f"lspwb-{runner_kind}-{model_label.replace('.', '-').replace('_', '-')}"
    job_id = f"JOB:{_job_digest(profile.profile_id, runner_kind, model_label, task_source, str(output_path))}"
    env_exports = dict(profile.environment_exports)
    env_exports["LSPWB_FRONTIER_REGISTRY_PATH"] = str(Path(registry_path).expanduser())
    if endpoint_url:
        env_exports["LSPWB_VLLM_ENDPOINT_URL"] = endpoint_url
    if served_model_name:
        env_exports["LSPWB_VLLM_SERVED_MODEL_NAME"] = served_model_name
    if dtype_note:
        env_exports["LSPWB_VLLM_MODEL_VERSION_NOTE"] = dtype_note
    if tensor_parallel_size is not None:
        env_exports["LSPWB_VLLM_TENSOR_PARALLEL_SIZE"] = str(tensor_parallel_size)
    if gpu_count is not None:
        env_exports["LSPWB_VLLM_GPU_COUNT"] = str(gpu_count)

    command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} {_quote(str(Path(profile.repo_root) / 'scripts' / script_name))} "
        f"--model {_quote(model_label)} "
        f"--registry-path {_quote(str(Path(registry_path).expanduser()))} "
        f"--task-source {_quote(task_source)} "
        f"--output-dir {_quote(str(output_path))} "
        f"--temperature {_quote(str(temperature))} "
        f"--max-tokens {_quote(str(max_tokens))} "
        f"--pause-between-calls {_quote(str(pause_between_calls))}"
    )
    if keys_file:
        command += f" --keys-file {_quote(keys_file)}"
    if dry_run:
        command += " --dry-run"

    output_artifacts = {
        "output_dir": str(output_path),
        "summary": str(output_path / "summary.json"),
        "submissions": str(output_path / "submissions.jsonl"),
    }
    if runner_kind == "smoke":
        output_artifacts["evaluations"] = str(output_path / "evaluations.jsonl")
    else:
        output_artifacts["baseline_run_spec"] = str(output_path / "baseline_run_spec.jsonl")
        output_artifacts["agentic_trace"] = str(output_path / "agentic_trace.jsonl")

    notes = [
        "Scaffold-only execution job for shared-registry frontier submitter evaluation.",
        f"runner_kind={runner_kind}",
        f"task_source={task_source}",
        f"model_label={model_label}",
        f"backend_type={provider.get('backend_type')}",
        f"provider_name={provider.get('provider_name')}",
        f"execution_target={provider.get('execution_target')}",
    ]
    if endpoint_url:
        notes.append(f"vllm_endpoint={endpoint_url}")
    if served_model_name:
        notes.append(f"served_model_name={served_model_name}")
    if tensor_parallel_size is not None:
        notes.append(f"tensor_parallel_size={tensor_parallel_size}")
    if gpu_count is not None:
        notes.append(f"gpu_count={gpu_count}")
    if dtype_note:
        notes.append(f"dtype_note={dtype_note}")
    notes.extend(str(item) for item in scheduler_notes)

    return ExecutionJobSpec(
        job_id=job_id,
        job_name=resolved_job_name,
        profile_id=profile.profile_id,
        job_kind=f"frontier_submitter_{runner_kind}",
        backend=profile.backend,
        working_directory=profile.working_directory,
        command_sequence=(
            f"mkdir -p {_quote(str(output_path))}",
            f"cd {_quote(profile.repo_root)}",
            command,
        ),
        environment_exports=env_exports,
        output_artifacts=output_artifacts,
        notes=tuple(notes),
    )


def build_auto_review_recovery_job_spec(
    profile: ExecutionProfile,
    *,
    execution_profile_path: str,
    papers_path: str,
    packaging_reviews_path: str,
    output_dir: str,
    model_id: str,
    raw_dir: Optional[str] = None,
    job_name: Optional[str] = None,
) -> ExecutionJobSpec:
    output_path = Path(output_dir).expanduser()
    raw_path = Path(raw_dir).expanduser() if raw_dir else output_path / "pmc_fulltext_raw"
    evidence_output = output_path / "evidence_enrichments.jsonl"
    fetch_records_output = output_path / "pmc_fetch_records.jsonl"
    evidence_summary_output = output_path / "evidence_enrichment_summary.json"
    enriched_papers_output = output_path / "enriched_source_papers.jsonl"
    source_bundles_output = output_path / "source_bundles.jsonl"
    source_bundle_summary_output = output_path / "source_bundle_audit.json"
    panel_votes_output = output_path / "panel_votes.jsonl"
    panel_vote_summary_output = output_path / "panel_vote_summary.json"
    aggregated_reviews_output = output_path / "aggregated_reviews.jsonl"
    aggregated_summary_output = output_path / "aggregated_review_summary.json"
    qualification_output = output_path / "auto_qualification_records.jsonl"
    qualification_summary_output = output_path / "auto_qualification_summary.json"
    batch_summary_output = output_path / "auto_review_batch_summary.json"
    resolved_job_name = job_name or "lspwb-auto-review-recovery"
    job_id = f"JOB:{_job_digest(profile.profile_id, str(output_path), str(papers_path), model_id)}"

    evidence_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli build-auto-review-evidence-enrichments "
        f"--papers {_quote(papers_path)} "
        f"--raw-dir {_quote(str(raw_path))} "
        f"--output {_quote(str(evidence_output))} "
        f"--fetch-records-output {_quote(str(fetch_records_output))} "
        f"--summary-output {_quote(str(evidence_summary_output))} "
        f"--refresh"
    )
    materialize_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli materialize-enriched-source-papers "
        f"--papers {_quote(papers_path)} "
        f"--evidence-enrichments {_quote(str(evidence_output))} "
        f"--output {_quote(str(enriched_papers_output))}"
    )
    source_bundle_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli build-auto-review-source-bundles "
        f"--papers {_quote(papers_path)} "
        f"--evidence-enrichments {_quote(str(evidence_output))} "
        f"--output {_quote(str(source_bundles_output))} "
        f"--summary-output {_quote(str(source_bundle_summary_output))} "
        f"--refresh"
    )
    panel_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli run-auto-paper-reviews "
        f"--papers {_quote(papers_path)} "
        f"--source-bundles {_quote(str(source_bundles_output))} "
        f"--execution-profile {_quote(execution_profile_path)} "
        f"--model-id {_quote(model_id)} "
        f"--packaging-reviews {_quote(packaging_reviews_path)} "
        f"--output {_quote(str(panel_votes_output))} "
        f"--summary-output {_quote(str(panel_vote_summary_output))} "
        f"--refresh"
    )
    aggregate_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli aggregate-auto-paper-reviews "
        f"--papers {_quote(papers_path)} "
        f"--source-bundles {_quote(str(source_bundles_output))} "
        f"--panel-votes {_quote(str(panel_votes_output))} "
        f"--output {_quote(str(aggregated_reviews_output))} "
        f"--summary-output {_quote(str(aggregated_summary_output))} "
        f"--refresh"
    )
    qualification_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli build-auto-paper-qualification-decisions "
        f"--papers {_quote(papers_path)} "
        f"--source-bundles {_quote(str(source_bundles_output))} "
        f"--aggregated-reviews {_quote(str(aggregated_reviews_output))} "
        f"--packaging-reviews {_quote(packaging_reviews_path)} "
        f"--output {_quote(str(qualification_output))} "
        f"--summary-output {_quote(str(qualification_summary_output))}"
    )
    summary_command = (
        f"PYTHONPATH={_quote(str(Path(profile.repo_root) / 'src'))} "
        f"{_quote(profile.python_bin)} -m life_science_paperwritingbench.cli summarize-auto-review-batch "
        f"--papers {_quote(papers_path)} "
        f"--source-bundles {_quote(str(source_bundles_output))} "
        f"--panel-votes {_quote(str(panel_votes_output))} "
        f"--aggregated-reviews {_quote(str(aggregated_reviews_output))} "
        f"--qualifications {_quote(str(qualification_output))} "
        f"--output {_quote(str(batch_summary_output))}"
    )

    return ExecutionJobSpec(
        job_id=job_id,
        job_name=resolved_job_name,
        profile_id=profile.profile_id,
        job_kind="auto_review_recovery",
        backend=profile.backend,
        working_directory=profile.working_directory,
        command_sequence=(
            f"mkdir -p {_quote(str(output_path))}",
            f"mkdir -p {_quote(str(raw_path))}",
            f"cd {_quote(profile.repo_root)}",
            evidence_command,
            materialize_command,
            source_bundle_command,
            panel_command,
            aggregate_command,
            qualification_command,
            summary_command,
        ),
        environment_exports=dict(profile.environment_exports),
        output_artifacts={
            "papers": str(Path(papers_path).expanduser()),
            "packaging_reviews": str(Path(packaging_reviews_path).expanduser()),
            "raw_dir": str(raw_path),
            "output_dir": str(output_path),
            "evidence_enrichments": str(evidence_output),
            "fetch_records": str(fetch_records_output),
            "evidence_summary": str(evidence_summary_output),
            "enriched_papers": str(enriched_papers_output),
            "source_bundles": str(source_bundles_output),
            "source_bundle_summary": str(source_bundle_summary_output),
            "panel_votes": str(panel_votes_output),
            "panel_vote_summary": str(panel_vote_summary_output),
            "aggregated_reviews": str(aggregated_reviews_output),
            "aggregated_summary": str(aggregated_summary_output),
            "qualification_records": str(qualification_output),
            "qualification_summary": str(qualification_summary_output),
            "batch_summary": str(batch_summary_output),
        },
        notes=(
            "Scaffold-only execution job for shadow-recovery auto review reruns.",
            "Generated script refreshes evidence enrichment and proxy-panel outputs before rebuilding auto qualification records.",
        ),
    )


def render_execution_job_script(job_spec: ExecutionJobSpec, profile: ExecutionProfile) -> str:
    lines = ["#!/bin/bash"]
    if profile.backend == "slurm":
        lines.extend(
            [
                f"#SBATCH --job-name={job_spec.job_name}",
                "",
            ]
        )
    lines.extend(
        [
            "set -euo pipefail",
            "",
        ]
    )
    for key, value in sorted(job_spec.environment_exports.items()):
        lines.append(f"export {key}={_quote(value)}")
    if job_spec.environment_exports:
        lines.append("")
    lines.extend(job_spec.command_sequence)
    lines.append("")
    return "\n".join(lines)
