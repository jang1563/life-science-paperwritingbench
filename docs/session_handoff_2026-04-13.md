# Session Handoff: 2026-04-13

## Purpose

This file is the restart point for the current `Life_science_paperwritingbench` state.

It is written to make the next session efficient:

- what is stable
- what is only shadow/auto-only
- which artifacts are canonical right now
- what changed most recently
- what to do next

## Current project state

### Stable operating baseline

The project currently has a working `auto-review shadow-first` lane with deterministic provenance-tracked artifacts.

The strongest current release baseline is:

- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/`

The current program status is:

- `180` qualified papers
- `518` shadow bundles
- `430` public bundles
- `88` private bundles
- `0` split-safety violations
- `0` mixed-holdout papers
- `v1_core_gate_passed = true`
- `leaderboard_gate_passed = false`

Canonical summaries:

- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/release_summary.json`
- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/program_progress.json`
- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_public_baseline_comparison_summary.json`

### Auto qualification baseline

The latest full-corpus auto qualification pass is:

- `knowledge_base/qualified/collection_v1_2018_present/auto_review/auto_qualification_summary_full180_enriched_v14.json`

Current auto qualification facts:

- `180 shadow_candidate`
- `180 review_ready`
- `scientific A = 180`
- `packaging P1 = 180`
- `writing W1/W2/W3 = 63/113/4`
- `confidence low/medium = 5/175`

Important interpretation:

- this is still `auto-only`
- it is valid for `shadow` development
- it is not valid for `public_gold`
- it is not valid for `public writing exemplar`
- it is not valid for `human-validated leaderboard`

### Inspection baseline

The latest inspection slice is:

- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6.jsonl`

Its paired summaries are:

- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6_summary.json`
- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6_taxonomy.json`
- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6.md`
- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6_taxonomy.md`

Current `v6` inspection profile:

- `30` public entries
- balanced across all `6` study classes
- `low confidence = 3`
- `medium confidence = 27`
- `W1/W2/W3 = 1/27/2`

Current taxonomy counts:

- `stable_shadow_controls = 23`
- `low_confidence_shadow = 3`
- `identifier_sparse_low_confidence = 3`
- `resource_release_specificity = 2`
- `writing_quality_risk = 2`
- `hybrid_overlay_complexity = 3`
- `figure_table_grounding = 1`

Recent inspection delta:

- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v5_to_v6_delta.json`

Key delta facts:

- `resource_release_grounded +3`
- `resource_release_specificity -3`
- `stable_shadow_controls +3`

## What changed most recently

### Latest code change

The latest code change was in:

- `src/life_science_paperwritingbench/inspection.py`
- `tests/test_qualification.py`

What changed:

- new focus tag `abstract_inferred_only` is added to a bundle when all four hold:
  - any source-bundle note contains `fetch_error`
  - any source-bundle note contains `inferred from abstract`
  - no grounded figure or table evidence is present
  - no `resource_identifiers` or `trial_registry_ids` are present
- new taxonomy category `fulltext_acquisition_gap` (priority `high`) is emitted when `abstract_inferred_only` is present on an entry
- `resource_release_specificity` is now suppressed when `abstract_inferred_only` is also present, so the two remaining resource-release residuals with `fetch_error` + abstract-inferred methods/results get reclassified as `fulltext_acquisition_gap` instead of being tagged as parser-labeling risk
- `compare_shadow_inspection_reports` now emits delta notes when `fulltext_acquisition_gap` grows/shrinks or when `abstract_inferred_only` entries enter a slice

The previous change (still current) remains:

- resource-release cases are not treated as specificity-risk by default; a `resource_release_grounded` tag is added when either explicit `resource_identifiers` exist or `methods + results + grounded figure/table` evidence is present; `resource_release_specificity` is only emitted when `resource_release_claim` is present without `resource_release_grounded`

That prior change narrowed the bucket from `5` to `2`; the new change is expected to reclassify those `2` residuals into `fulltext_acquisition_gap`.

### Latest residual cases that still look genuinely weak

The two resource-release cases still in `resource_release_specificity` are:

- `DOI:10.1016/j.jmr.2022.107268`
- `DOI:10.1002/cpz1.1028`

Why they still look risky:

- `fetch_error` notes in source bundles
- `methods_text` inferred from abstract
- `results_text` inferred from abstract
- no figure support
- no table support
- no resource identifiers
- low confidence remains justified

These are currently more like `full-text acquisition / specificity evidence gap` cases than parser-tagging mistakes.

## Important constraints

### Meaning constraints

- `auto-review` is a deterministic proxy lane, not a true human review lane
- keep `public_gold_candidate` disabled in auto-only mode
- keep `public_writing_eligible = false` in auto-only mode
- keep `judge_validation_ready = false` in auto-only mode
- do not blur shadow-only artifacts into the human-validated path

### Split constraints

- same paper must stay in the same holdout bucket
- do not regress the fixed mixed-holdout issue
- release builders must ignore `excluded` units for split-safety

### Evidence constraints

- do not count vague release-language alone as strong resource grounding
- direct identifiers are still strongest evidence
- grounded figure/table plus usable methods/results can count as support
- abstract-only inferred content should remain lower-trust

## Canonical files to inspect first next session

If starting fresh, inspect these in order:

1. `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/program_progress.json`
2. `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/release_summary.json`
3. `knowledge_base/qualified/collection_v1_2018_present/auto_review/auto_qualification_summary_full180_enriched_v14.json`
4. `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6_summary.json`
5. `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6_taxonomy.json`
6. `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v5_to_v6_delta.json`

## Best next step

The `fulltext_acquisition_gap` category is now implemented in code and
covered by unit tests. The logical next step is to **run it against the
current full-corpus inspection artifacts** and confirm that the two
remaining resource-release residuals (`DOI:10.1016/j.jmr.2022.107268` and
`DOI:10.1002/cpz1.1028`) move out of `resource_release_specificity` and
into `fulltext_acquisition_gap` as expected.

Recommended next target:

- rebuild the inspection batch and taxonomy on the current enriched
  `full180` corpus and compare against `shadow_public_inspection_v6`
- confirm the two residuals are now tagged `fulltext_acquisition_gap`
  rather than `resource_release_specificity`
- use the paired delta report to verify `resource_release_specificity -2`
  and `fulltext_acquisition_gap +2`

After that, the next substantive improvements in priority order are:

1. **Retry full-text acquisition** for the two `fulltext_acquisition_gap`
   papers — publisher-native or Europe PMC refetch — and re-run the lane
   to see whether they can leave the gap category.
2. **Tighten `identifier_sparse_low_confidence`**: the remaining 3 cases
   are not explained by the gap category and deserve their own audit.
3. **Promote confidence calibration `v14` semantics** into a
   reproducible pass (the `34/146 → 5/175` low/medium shift has held
   across recent inspections and is load-bearing for downstream gates).

## Suggested commands for the next session

### Re-run tests

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

### Rebuild inspection batch and taxonomy

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-shadow-inspection-batch \
  --task-bundles knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --auto-qualification-records knowledge_base/qualified/collection_v1_2018_present/auto_review/auto_qualification_records_full180_enriched_v14.jsonl \
  --source-bundles knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v13.jsonl \
  --output knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_next.jsonl \
  --summary-output knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_next_summary.json \
  --markdown-output knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_next.md \
  --target-total 30 \
  --holdout-bucket public

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-shadow-inspection-taxonomy \
  --inspection-entries knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_next.jsonl \
  --output knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_next_taxonomy.json \
  --markdown-output knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_next_taxonomy.md
```

### Compare inspection deltas

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli compare-shadow-inspection-runs \
  --previous-summary knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6_summary.json \
  --current-summary knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_next_summary.json \
  --previous-taxonomy knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6_taxonomy.json \
  --current-taxonomy knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_next_taxonomy.json \
  --previous-label v6 \
  --current-label next \
  --output knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6_to_next_delta.json
```

## If you want to continue with code first

Touchpoints most likely needed:

- `src/life_science_paperwritingbench/inspection.py`
- `src/life_science_paperwritingbench/auto_review.py`
- `src/life_science_paperwritingbench/evidence_enrichment.py`
- `tests/test_qualification.py`

## If you want to continue with artifact analysis first

Start with:

- `knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v6.jsonl`
- `knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v13.jsonl`
- `knowledge_base/qualified/collection_v1_2018_present/auto_review/auto_qualification_records_full180_enriched_v14.jsonl`

## Current confidence in the lane

This is a strong `shadow development` state.

It is good enough for:

- deterministic shadow release maintenance
- parser/enrichment refinement
- inspection-driven debugging
- lean baseline replay on public shadow bundles

It is not yet claiming:

- human-validated source quality
- public gold benchmark status
- official leaderboard validity

## Short version

If resuming fast:

1. read `program_progress.json`
2. read `shadow_public_inspection_v6_taxonomy.json`
3. target the remaining `2` resource-release residuals and the `3` identifier-sparse low-confidence cases
4. most likely next improvement is a `fulltext_acquisition_gap` category, not a broader threshold change
