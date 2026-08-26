# Open-Weight / VLLM Track Policy

## Purpose

This document fixes the release-facing boundary between hosted-frontier results
and open-weight / VLLM results for the `v0.1 research preview`.

The short version:

- hosted-frontier submitters define the official hosted matrix gate
- open-weight / VLLM submitters are a separate track
- open-weight results may be reported as preview diagnostics once comparable
  artifacts exist
- open-weight results must not be pooled into hosted-frontier averages,
  same-judge spreads, or leaderboard claims

## Current Registry Slot

The shared frontier registry includes one stable open-weight submitter slot:

- `openweight-vllm-submitter`

Registry location:

- `configs/models/frontier_registry_v1.json`

Important registry fields:

- `backend_type = vllm_http`
- `execution_target = cayuga_vllm`
- `submitter_track = open_weight`
- `request_model` is deployment-configured by
  `LSPWB_VLLM_SERVED_MODEL_NAME`
- endpoint is deployment-configured by `LSPWB_VLLM_ENDPOINT_URL`
- model/version note is deployment-configured by
  `LSPWB_VLLM_MODEL_VERSION_NOTE`

This keeps the benchmark artifact contract stable while allowing the actual
served open-weight model to vary by cluster job.

## Track Separation Rules

Hosted-frontier track:

- uses `submitter_track = hosted_frontier`
- uses hosted API execution targets
- is the release-facing official hosted matrix
- must complete required hosted submitter x official judge cells before the
  hosted matrix gate can pass

Open-weight track:

- uses `submitter_track = open_weight`
- uses `backend_type = vllm_http`
- should be named and reported as an open-weight diagnostic or separate track
- must include served model name, endpoint, hardware, tensor parallelism, dtype
  or quantization note, registry path, task source, scoring version, and git
  commit in run metadata
- does not satisfy missing hosted-frontier submitter cells

Publication readiness:

- `official_hosted_matrix_complete` is based only on required hosted-frontier
  submitters and official hosted judges
- `hosted_and_open_weight_submitters_present` is a separate track-presence gate
- readiness JSON now includes `track_summary` so missing tracks are visible
- final leaderboard claims remain blocked until all release-facing gates pass

## Scaffold A VLLM Submitter Job

Use the existing job scaffold to write the job spec and run script:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli write-frontier-submitter-job \
  --execution-profile configs/execution/cayuga_profile.json \
  --registry-path configs/models/frontier_registry_v1.json \
  --model-label openweight-vllm-submitter \
  --runner-kind agentic \
  --task-source inspection-slice \
  --output-dir /tmp/lspwb_openweight_vllm_agentic \
  --job-spec-output /tmp/lspwb_openweight_vllm_agentic/job_spec.json \
  --script-output /tmp/lspwb_openweight_vllm_agentic/run_frontier_agentic.sh \
  --endpoint-url http://<HOST>:8000/v1/chat/completions \
  --served-model-name <SERVED_MODEL_NAME> \
  --tensor-parallel-size 4 \
  --gpu-count 4 \
  --dtype-note <DTYPE_OR_QUANTIZATION_NOTE>
```

The scaffold is intentionally not a leaderboard submission by itself. Treat it
as a reproducible run recipe whose output can later be registered into a
separate open-weight matrix summary.

## Artifact Naming

Prefer output directories that keep track and model identity explicit:

```text
calibration/openweight_vllm_<served-model-slug>_<task-source>_<YYYYMMDD>/
```

Expected artifacts:

- `job_spec.json`
- `run_frontier_agentic.sh`
- `summary.json`
- `summary.md`
- `submissions.jsonl`
- `baseline_run_spec.jsonl`
- `agentic_trace.jsonl`

Before comparing with hosted results, also record:

- git commit
- registry path and registry version
- served model name
- endpoint host class, not private credentials
- GPU count and tensor parallelism
- dtype or quantization note
- task source
- scoring version
- whether outputs were generated with dry run disabled

## Safe Preview Language

Safe wording:

- "open-weight/VLLM diagnostic track"
- "separate from the hosted-frontier matrix"
- "not yet comparable to hosted-frontier artifacts"
- "deployment-configured open-weight slot"
- "pending comparable artifacts"

Avoid wording that implies:

- open-weight results are part of the current hosted matrix
- hosted and open-weight scores are directly comparable before matching task
  slice, prompt, scoring, and judge conditions
- the open-weight track satisfies the hosted matrix gate
- a final leaderboard exists

## Promotion Criteria

An open-weight run can become a release-facing separate-track artifact only
after it has:

1. non-dry submissions on the same task slice as the hosted comparison
2. deterministic scoring with the same scoring version
3. judge results from the same official judge set, excluding same-family bias
   where applicable
4. canary handling documented without raw canary leakage
5. complete run metadata for deployment reproducibility
6. a matrix summary that preserves `submitter_track = open_weight`
