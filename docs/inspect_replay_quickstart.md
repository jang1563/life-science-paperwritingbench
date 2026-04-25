# Inspect And Replay Quickstart

## Purpose

This quickstart shows the API-free Inspect/replay path for the `v0.1 research
preview`.

Use it when you want to inspect benchmark records, replay deterministic scores
from existing submissions, or attach existing judge artifacts to Inspect-style
records without launching new provider calls.

## Default Inputs

The adapter defaults to the current public shadow writing lane:

- task bundles:
  `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl`
- source bundles:
  `knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v16.jsonl`

The current preview anchors used below are:

- submissions:
  `calibration/llm_agentic_public_slice_v1_rerun2/submissions.jsonl`
- judge results:
  `calibration/llm_agentic_public_slice_v1_rerun5_judged_v3/judgments.jsonl`

## Build Inspect Records

```bash
PYTHONPATH=src python3 - <<'PY'
from inspect_evals.life_science_paperwritingbench import build_inspect_records

records = build_inspect_records(limit=3)
print(len(records))
print([record["id"] for record in records])
print(records[0]["input"])
PY
```

Expected interpretation:

- this does not call an external model
- records contain `input` fields for Inspect-facing task metadata
- records contain `metadata.task_bundle`
- records contain `metadata.source_bundle` when the source bundle is available

## Replay Deterministic Submission Scores

```bash
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from inspect_evals.life_science_paperwritingbench import replay_submission_scores

scores = replay_submission_scores(
    Path("calibration/llm_agentic_public_slice_v1_rerun2/submissions.jsonl")
)
print(len(scores))
print(scores[0]["task_bundle_id"])
print(scores[0]["deterministic_checks_passed"])
PY
```

Expected current result:

- `30` scored rows
- deterministic scoring uses the repo's default scoring version `v2`
- no provider call is made

## Replay Existing Judge Results

```bash
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from inspect_evals.life_science_paperwritingbench import replay_judge_results

judges = replay_judge_results(
    Path("calibration/llm_agentic_public_slice_v1_rerun5_judged_v3/judgments.jsonl")
)
print(len(judges))
print(judges[0]["task_bundle_id"])
print(judges[0]["overall_pass"])
PY
```

Expected current result:

- `30` replayed judge rows
- each matched row is enriched with task family, study class, and claim mode
- this replays existing judge JSONL; it does not re-judge outputs

## Build Records With Submission And Judge Context

```bash
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from inspect_evals.life_science_paperwritingbench import build_inspect_records

records = build_inspect_records(
    submissions_path=Path("calibration/llm_agentic_public_slice_v1_rerun2/submissions.jsonl"),
    judgments_path=Path("calibration/llm_agentic_public_slice_v1_rerun5_judged_v3/judgments.jsonl"),
    include_submission_scores=True,
    limit=3,
)
print(records[0]["metadata"].keys())
PY
```

Expected interpretation:

- `submission_record` is attached when a submission exists for the task bundle
- `submission_deterministic_evaluation` is attached when
  `include_submission_scores=True`
- `judge_result` is attached when a judgment exists for the task bundle

## Dry-Run Provider Submission Generation

Use dry run when checking prompt construction and output schema without
calling a hosted model:

```bash
PYTHONPATH=src python3 - <<'PY'
from inspect_evals.life_science_paperwritingbench import generate_submission_records

rows = generate_submission_records(
    model_label="deepseek-chat",
    limit=1,
    dry_run=True,
)
print(len(rows))
print(rows[0]["model"])
print(rows[0]["submission_record"]["task_bundle_id"])
print(bool(rows[0]["prompt"]))
print("deterministic_checks_passed" in rows[0]["deterministic_evaluation"])
PY
```

Expected current result:

- one generated row
- no provider call is made
- prompt, submission record, usage shell, and deterministic evaluation fields
  are present

## Provider-Backed Generation

Provider-backed generation uses the shared frontier registry:

- `configs/models/frontier_registry_v1.json`

Only run non-dry submissions when the relevant key is available in the
environment or in `~/.api_keys`.

Keep generated Inspect submissions separate from the current hosted matrix
unless they use the same task slice, model labels, registry path, and scoring
version.
