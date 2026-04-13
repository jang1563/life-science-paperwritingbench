# Judge Validation Contract

## Purpose

The judge-validation slice exists to validate future judge behavior against human-adjudicated benchmark units.

It is intentionally separate from:

- source-paper qualification
- unit release-tier assignment
- deterministic benchmark scoring

## Required Rubric Axes

Each ready `JudgeValidationUnit` must contain non-empty labels for:

- `evidence_fidelity`
- `traceability`
- `provenance_completeness`
- `writing_structure_compliance`

## Ready-State Definition

A `JudgeValidationUnit` counts toward leaderboard progress only when all of the following are true:

- `human_adjudicated = true`
- `frozen = true`
- all required rubric axes are present and non-empty

Blank templates produced by `build-judge-slice` are not counted as ready units.

## File Workflow

1. Build a deterministic slice template from released `TaskBundle` artifacts.
2. Human adjudicators fill rubric labels and mark the units adjudicated.
3. Freeze the records.
4. Run `audit-judge-slice`.
5. Only after the audit passes should the slice be used for judge development or leaderboard readiness checks.

## Audit Checks

`audit-judge-slice` verifies:

- minimum unit count
- known `task_bundle_id` linkage
- duplicate `validation_unit_id` detection
- duplicate `task_bundle_id` detection
- human-adjudicated count
- frozen count
- ready-unit count
- task-family / study-class / release-tier coverage summary

## Non-Goals

- It does not run an LLM judge.
- It does not merge qualification with evaluation.
- It does not assign final scientific truth; that remains the job of frozen truth manifests.
