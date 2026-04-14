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

- `src/life_science_paperwritingbench/evidence_enrichment.py`
- `src/life_science_paperwritingbench/inspection.py`
- `tests/test_qualification.py`

Evidence enrichment now extracts repository URLs as `resource_identifiers`:

- new `_REPOSITORY_URL_PATTERN` in `evidence_enrichment.py` catches
  code-hosting URLs (`github.com/u/r`, enterprise `github.*.edu/u/r`,
  `gitlab.com/u/r`, `bitbucket.org/u/r`, `codeberg.org/u/r`,
  `sourceforge.net/projects/p`) and data-archive URLs
  (`zenodo.org/record/N`, `zenodo.org/doi/10.5281/…`, `osf.io/<id>`,
  `figshare.com/articles/…`, `datadryad.org/stash/…`)
- `_identifier_hits` now unions matches from `_ACCESSION_PATTERN` and
  `_REPOSITORY_URL_PATTERN`; trailing punctuation is stripped so
  sentence-final URLs are captured cleanly
- consistent with existing `_ACCESSION_PATTERN` semantics, the URL
  regex enriches the raw signal and does not try to disambiguate
  "released by this paper" vs "used by this paper". The downstream
  `resource_release_grounded` logic still only fires on papers whose
  `claim_mode` is `resource_release`
- two new unit tests cover the positive arms (GitHub / enterprise
  GitHub / Zenodo / OSF all extracted) and the negative arm (ORCID
  and generic `example.com` URLs do NOT match)

Verified on the three NCBI-recovered papers:

- `DOI:10.1016/j.jmr.2022.107268` (SpecDB): now gains
  `https://github.rpi.edu/RPIBioinformatics/SpecDB` as a
  `resource_identifier`, picks up `resource_ids` and
  `resource_release_grounded` focus tags, and leaves
  `identifier_sparse_low_confidence`
- `DOI:10.1002/cpz1.1028` (Copz1 protocol): remains identifier-sparse
  because its data-availability statement says *"Data sharing is not
  applicable"* — genuine sparsity, not a parser gap
- `DOI:10.1002/jpen.70069` (retrospective observational): remains
  identifier-sparse because the study reports patient-level clinical
  data that is typically not shared — genuine sparsity

`v10 → v11` delta: `identifier_sparse_low_confidence -1`,
`resource_ids +1`.

Prior change: evidence enrichment has an NCBI PMC efetch fallback:

- when the Europe PMC `fullTextXML` fetch returns an HTTP 4xx (i.e. the
  paper is non-OA or not in the Europe PMC redistribution set), the
  pipeline transparently retries via
  `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=...`
  and writes a separate `<pmcid>.ncbi.xml` cache file
- on NCBI success the enrichment record is tagged
  `pmc_source:ncbi_efetch_fallback` in its notes so downstream gates can
  detect the backend that succeeded
- on NCBI failure the fetch record captures both the Europe PMC error
  and the NCBI error so the audit trail is complete
- the fallback only fires on HTTP 4xx; transient failures (DNS,
  timeouts, 5xx) fall back to the previous behavior so an outage does
  not mask itself as a structural gap

Verified end-to-end on the three previously-blocked papers: all three
were successfully fetched via NCBI, producing methods/results text and
grounded figure/table evidence. The `v9 → v10` inspection delta shows
`fulltext_acquisition_gap -3` and `fulltext_acquisition_blocked_upstream
-3`, and `identifier_sparse_low_confidence` re-emerges at `3` —
exactly the category's intended meaning now that the three papers have
full text but still lack resource/trial-registry identifiers.

Prior inspection-layer changes (still in place):

What changed:

- new focus tag `abstract_inferred_only` is added to a bundle when all four hold:
  - any source-bundle note contains `fetch_error`
  - any source-bundle note contains `inferred from abstract`
  - no grounded figure or table evidence is present
  - no `resource_identifiers` or `trial_registry_ids` are present
- new taxonomy category `fulltext_acquisition_gap` (priority `high`) is emitted when `abstract_inferred_only` is present on an entry
- `resource_release_specificity` is now suppressed when `abstract_inferred_only` is also present, so the two remaining resource-release residuals with `fetch_error` + abstract-inferred methods/results get reclassified as `fulltext_acquisition_gap` instead of being tagged as parser-labeling risk
- `identifier_sparse_low_confidence` is also suppressed when `abstract_inferred_only` is present, because lacking resource/trial-registry identifiers in an abstract-inferred bundle is a downstream consequence of the fetch failure rather than a genuine identifier-sparsity signal; the category is preserved for the true case where a paper has full text but still lacks identifiers
- new focus tag `fulltext_acquisition_blocked_upstream` and paired taxonomy category (priority `high`) are emitted when a bundle already qualifies as `abstract_inferred_only` **and** at least one of its notes contains an HTTP 4xx error (`HTTP Error 400/401/403/404/410/451`), i.e. the Europe PMC fetch returned a client-side rejection. This distinguishes "retry will help" (DNS, timeouts, 5xx) from "retry is pointless" (the paper is non-OA or not indexed upstream) and points at an alternate-backend or manual-acquisition escalation rather than another retry
- `compare_shadow_inspection_reports` now emits delta notes when `fulltext_acquisition_gap` or `fulltext_acquisition_blocked_upstream` grows/shrinks or when `abstract_inferred_only` entries enter a slice

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

The `v6 → v7 → v8 → v9 → v10` trajectory closed the fulltext-acquisition
branch end-to-end:

- `v6 → v7`: `resource_release_specificity -2`, `fulltext_acquisition_gap +3`
- `v7 → v8`: `identifier_sparse_low_confidence -3` (suppressed when
  the same entry is already in `fulltext_acquisition_gap`)
- `v8 → v9`: `fulltext_acquisition_blocked_upstream +3` after re-running
  evidence enrichment with working network — all three fetches returned
  HTTP 404 from Europe PMC. Europe PMC's own search API confirmed two
  of the three PMCIDs are `isOpenAccess=N` and the third (`PMC13047292`)
  is not indexed at all
- `v9 → v10`: after adding the NCBI efetch fallback in
  `evidence_enrichment.py`, all three blocked papers were successfully
  fetched via `eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`,
  producing methods/results text and grounded figure/table evidence.
  `fulltext_acquisition_gap` and `fulltext_acquisition_blocked_upstream`
  both dropped from `3` to `0`, and `identifier_sparse_low_confidence`
  re-emerged at `3` — exactly its intended meaning now that the three
  papers have full text but still lack resource/trial-registry
  identifiers

Current `v11` slice buckets (after regex extension for repo URLs):

- `stable_shadow_controls = 23`
- `low_confidence_shadow = 3`
- `identifier_sparse_low_confidence = 2`
- `hybrid_overlay_complexity = 3`
- `writing_quality_risk = 2`
- `figure_table_grounding = 1`
- `fulltext_acquisition_gap = 0`
- `fulltext_acquisition_blocked_upstream = 0`

Artifacts for the three newly-recovered papers live at:

- `knowledge_base/qualified/collection_v1_2018_present/auto_review/recovery_v7/rerun_outputs/pmc_fulltext_raw/{PMC11179667,PMC13047292,PMC9922030}.ncbi.xml`
- `knowledge_base/qualified/collection_v1_2018_present/auto_review/recovery_v7/rerun_outputs/evidence_enrichments.jsonl`
- `knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v15.jsonl` (180-paper merged corpus with the three recovered bundles)

A manual regex sweep of the three NCBI XMLs found **no** missed
accessions (only DOI citations in references). So for these three
papers the current `identifier_sparse_low_confidence` signal is
genuine: the papers describe resources but do not publish standard-
format accessions (GSE/SRR/PXD/RRID/PDB/etc.).

Recommended next target (in priority order):

1. **Audit `identifier_sparse_low_confidence` as a real signal now**.
   With the acquisition-gap collapse done, decide whether these three
   entries represent:
   - (a) a parser-pattern gap (accessions are present in non-standard
     form, e.g. BMRB IDs, author-assigned resource URLs, Zenodo/Github
     links) that `_ACCESSION_PATTERN` in `evidence_enrichment.py`
     should learn;
   - (b) a genuine authorship quality issue (papers that describe a
     resource without publishing a persistent identifier).
   The first NCBI XML (SpecDB) is especially worth reading — a
   biomolecular NMR database paper almost certainly mentions a BMRB
   accession or a project URL that the current regex does not catch.
2. **Refresh the whole corpus via the new NCBI fallback path** in a
   single batch run to pull any other non-OA papers that were silently
   abstract-inferred up to this point; then rebuild the auto
   qualification + inspection slices. This is the cheapest way to find
   out whether `fulltext_acquisition_blocked_upstream` is truly zero
   corpus-wide or just zero in the current 30-entry public slice.
3. **Promote confidence calibration `v14` semantics** into a
   reproducible pass (the `34/146 → 5/175` low/medium shift has held
   across recent inspections and is load-bearing for downstream gates).
4. **Audit the three `low_confidence_shadow` entries** now that
   `low_confidence_shadow` is no longer contaminated by fetch failures.

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
