# Judge Validation Workflow

This directory is reserved for the first populated judge-validation slice.

Recommended workflow:

1. Inventory released `TaskBundle` artifacts with `summarize-task-bundles` and select candidates with `select-judge-candidates`, or use `build-judge-batch` directly to materialize a selection-aware batch.
2. Build `JudgeValidationUnit` templates from selected `TaskBundle` artifacts with `build-judge-slice`, or generate the full directory with `build-judge-batch`.
3. Generate reviewer forms and adjudication shells with `build-judge-review-templates` if they were not created by `build-judge-batch`.
4. Collect reviewer JSONL files and merge them with `merge-judge-review-forms`.
5. Build an adjudication queue with `build-judge-adjudication-queue`.
6. After adjudication, apply finalized labels back onto the base slice with `finalize-judge-slice`.
7. Run `audit-judge-slice` and `summarize-judge-progress` on the finalized units.

`build-judge-batch` writes a selection-aware bundle:

- `selected_task_bundles.jsonl`
- `task_bundle_inventory.json`
- `judge_candidate_selection.json`
- `judge_units.jsonl`
- `judge_review_forms.jsonl`
- `judge_adjudications.jsonl`
- `judge_batch_summary.json`

No checked-in judge slice is provided yet because the slice should only be populated from curated released task bundles.
