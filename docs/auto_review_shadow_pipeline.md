# Auto Review Shadow Pipeline

## Purpose

The auto-review lane exists to keep benchmark curation moving when no human paper review is available.

It is intentionally lower trust than the human-reviewed path:

- it never produces `public_gold_candidate`
- it never sets `public_writing_eligible = True`
- it never contributes to judge validation readiness
- it is meant for `shadow_candidate` and `stress_candidate` triage only

Current implementation note:

- the panel is deterministic and rule-based today
- `model_id` and execution-profile fields are recorded as replay metadata
- the current lane should be read as deterministic proxy triage, not as live LLM judging

## Flow

1. Build `AutoReviewSourceBundle` artifacts from `SourcePaper` plus available enrichment.
2. Audit bundle completeness and provenance coverage.
3. Run deterministic prechecks before any proxy voting.
4. Generate one deterministic proxy vote each for:
   - `scientific_reviewer`
   - `writing_reviewer`
   - `evidence_skeptic`
5. Aggregate domain votes by majority rule with conservative tie handling.
6. Convert aggregated votes into `AutoQualificationRecord`.

## Bundle Completeness

`AutoReviewSourceBundle.bundle_completeness` is one of:

- `metadata_only`
- `partial`
- `review_ready`

Rules:

- `metadata_only` is capped to `stress_candidate`
- `partial` can support low-confidence scientific proxy review but is capped below public release
- `review_ready` is required for full shadow-candidate consideration

## Deterministic Caps

The following conditions override proxy-review optimism:

- retraction, withdrawal, removal: `excluded`
- expression of concern: `excluded`
- core-claim-invalidating partial retraction: `excluded`
- preprint: capped to `stress_candidate`
- controlled-access without safe derived artifacts: never `P1`
- missing methods/results/captions and no registry or accession evidence: writing review skipped

## Current Batch Status

The lane has now gone through three clearly different states.

Initial metadata-only diagnosis:

- `180` total papers
- `180` `metadata_only` bundles
- `0` `shadow_candidate`
- `180` `stress_candidate`
- `0` papers eligible for unit extraction

This first pass was still useful because it proved the shadow pipeline and showed that evidence richness, not orchestration, was the bottleneck.

Current full-collection enriched pass (`full180_enriched_v9`):

- `180` total papers
- `180` `review_ready`
- `0` `partial`
- `0` `metadata_only`
- `180` `shadow_candidate`
- `0` `excluded`
- `180` papers eligible for unit extraction

Current release lane (`auto_review_shadow_v10`):

- `180` shadow papers
- `518` `shadow_gold` bundles
- `430` public bundles
- `88` private bundles
- `149` public papers
- `31` private papers
- `0` split-safety violations
- `0` mixed-holdout papers

These artifacts live under:

- `auto_qualification_summary_full180_enriched_v9.json`
- `release_summary.json`
- `shadow_candidate_holdout_consistency_report.json`
- `shadow_candidate_public_baseline_comparison_summary.json`
- `program_progress.json`
- `maintenance_log.jsonl`
- `shadow_public_inspection_v1_summary.json`
- `shadow_public_inspection_v1.md`
- `shadow_public_inspection_v1_taxonomy.json`
- `shadow_public_inspection_v1_taxonomy.md`

Current program-state interpretation:

- `v1_core_gate_passed = true`
- `leaderboard_gate_passed = false`
- the current lane is operationally strong enough for deterministic shadow development, but still intentionally blocked from public-gold and human-validated leaderboard status
- `shadow_public_inspection_v1` is the current fast spot-check surface: `30` public entries, `17` low-confidence, `2` `W3`, and balanced coverage across all six study classes
- the paired taxonomy now gives a deterministic refinement queue: after resource-release grounding, the leading buckets are `stable_shadow_controls (23)`, `low_confidence_shadow (3)`, `identifier_sparse_low_confidence (3)`, and `resource_release_specificity (2)`
- the refreshed `shadow_public_inspection_v2` slice keeps the same class balance while improving identifier coverage: `resource_ids` entries rise from `2` to `5`, and `identifier_sparse_low_confidence` drops from `12` to `9`
- the inspection delta artifact is `shadow_public_inspection_v1_to_v2_delta.json`
- parser/enrichment `v12` adds explicit `figure_reference_snippets` and `table_reference_snippets`, so figure/table grounding can be audited as a first-class signal instead of being inferred from caption presence alone
- the next delta artifact, `shadow_public_inspection_v2_to_v3_delta.json`, shows `figure_table_grounding -28` after grounded tags were added
- parser/enrichment `v13` adds explicit `trial_registry_reference_snippets`, and the full180 enriched pass records `trial_registry_reference_snippet_count = 91`
- the latest delta artifact, `shadow_public_inspection_v3_to_v4_delta.json`, shows `trial_registry_grounded +4` and `trial_registry_traceability -8`
- confidence calibration `v14` now treats `limitation_uncertainty_disclosure` as a tolerated insufficiency for confidence scoring, which moves full180 `confidence low/medium` from `34/146` to `5/175`
- the latest delta artifact, `shadow_public_inspection_v4_to_v5_delta.json`, shows `low_confidence_shadow -14` and `identifier_sparse_low_confidence -6`
- the newest delta artifact, `shadow_public_inspection_v5_to_v6_delta.json`, shows `resource_release_grounded +3` and `resource_release_specificity -3`, leaving only `2` resource-release specificity entries in the current slice

Residual non-shadow set:

- `0` papers remain non-shadow
- no residual `stress_candidate` papers remain in the full enriched pass
- the previously excluded four-paper ceiling has now been recovered by richer abstract/figure-aware auto review

Residual summary:

- `residual_non_shadow_summary_v8.json`

Important implementation note:

- overlay-specific standards are now enforced only when the bundle contains direct evidence for that modality
- this prevents false positives such as a travel-distance `km` mention incorrectly triggering `ENZYMOLOGY` and `STRENDA`
- the auto-review lane still records `model_id` and execution profile for replay, but the actual voting logic remains deterministic and rule-based today

Judge inspection lane:

- a `30`-unit public-only inspection batch is scaffolded at [judge_batch_summary.json](calibration/auto_review_shadow_judge_v6/judge_batch_summary.json)
- it is intentionally not judge-ready yet because no human adjudication has been added

## Why This Still Helps

Even when everything lands in `stress_candidate`, the auto-review lane is useful because it:

- proves the shadow pipeline is reproducible
- records execution/profile/model fingerprints
- highlights evidence-richness bottlenecks
- identifies exactly what enrichment is needed next

## Next Upgrade Path

The auto-review lane is now productive enough to support shadow development, so the next upgrades are narrower:

- keep improving parser/evidence enrichment for future collection waves and harder paper types
- keep tightening modality-specific false-positive control in metadata hints and auto review
- preserve paper-level holdout grouping as shadow releases grow
- use the public `430`-bundle shadow lane as the main deterministic dev/eval surface until human review becomes available
