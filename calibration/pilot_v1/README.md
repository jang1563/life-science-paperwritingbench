# Pilot Calibration Set v1

This directory contains the first 12-paper pilot scaffold for reviewer calibration.

## Purpose

The pilot is not a benchmark release. It is a governance rehearsal that checks:

- `study_class` agreement
- `claim_mode` agreement
- `candidate_tier` agreement
- unit-level `release_tier` agreement

## Coverage Targets

- at least 12 papers total
- at least 2 papers for each `study_class`
- at least 3 hybrid multi-overlay papers
- at least 1 quarantine example
- at least 1 controlled-access example
- at least 1 negative-result or descriptive/resource example

## Files

- `pilot_manifest.jsonl`
  - one record per planned pilot paper
  - uses the `PilotCalibrationSpec` schema
- `reviewer_forms_template.jsonl`
  - blank two-reviewer template
  - uses the `PilotReviewForm` schema
- `adjudication_template.jsonl`
  - blank adjudication shell
  - uses the `PilotAdjudicationRecord` schema

## Suggested Workflow

1. Load the manifest with `load_jsonl(..., loader=pilot_calibration_spec_from_dict)`.
2. Validate coverage with `validate_pilot_calibration_set(...)`.
3. Generate or edit reviewer forms with `build_pilot_review_forms(...)`.
4. Generate or edit adjudication shells with `build_pilot_adjudication_shells(...)`.
5. Replace placeholder IDs and notes with real candidate papers after curation.
6. Freeze reviewer guidance before collecting agreement metrics.
7. Compute agreement with `compute_agreement_against_adjudication(...)` and check thresholds with `validate_pilot_agreement_thresholds(...)`.
