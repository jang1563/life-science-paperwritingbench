# Full Calibration Set v1

This directory is reserved for the first 60-paper full calibration cycle.

## Purpose

The full calibration set expands the 12-paper pilot into the production-facing governance rehearsal for:

- `study_class` agreement
- `claim_mode` agreement
- `candidate_tier` agreement
- unit-level `release_tier` agreement
- adjudication throughput and backlog tracking
- calibration drift tracking across batch revisions

## Coverage Targets

- at least 60 papers total
- at least 10 papers for each `study_class`
- at least 15 hybrid multi-overlay papers
- at least 6 quarantine examples
- at least 8 controlled-access examples
- at least 8 negative-result or descriptive/resource examples

## Suggested Files

- `full_manifest_template.jsonl`
  - generated with `write-full-calibration-scaffold`
  - deterministic starting scaffold that already satisfies full-calibration coverage targets
- `full_manifest.jsonl`
  - one record per calibration paper
  - uses the `PilotCalibrationSpec` schema for now
- `reviewer_forms_template.jsonl`
  - generated with `build-calibration-batch`
- `adjudication_template.jsonl`
  - generated with `build-calibration-batch`
- `adjudication_queue.jsonl`
  - generated with `build-adjudication-queue`
- `calibration_summary.json`
  - generated with `summarize-calibration`
- `calibration_drift.json`
  - generated with `audit-calibration-drift`

## Suggested Workflow

1. Generate `full_manifest_template.jsonl` with `write-full-calibration-scaffold`.
2. Copy or adapt it into `full_manifest.jsonl`.
3. Validate it with `validate-calibration --mode full`.
4. Generate reviewer and adjudication templates with `build-calibration-batch`.
5. Merge reviewer uploads with `merge-review-forms`.
6. Build the adjudication queue with `build-adjudication-queue`.
7. Summarize progress with `summarize-calibration`.
8. Compare revisions of the manifest with `audit-calibration-drift`.
