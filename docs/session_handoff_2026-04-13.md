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

## First LLM smoke test (Phase 2 entry point)

The first end-to-end LLM run against the benchmark is now in place:

- `scripts/llm_smoke_eval.py` picks one public shadow bundle per task
  family (`methods_to_text`, `results_to_text`, `abstract_from_evidence`),
  loads evidence from the merged `source_bundles_full180_enriched_v16`
  corpus, calls a cost-effective model through an OpenAI-compatible
  endpoint (default: DeepSeek V3 chat), writes `SubmissionRecord`
  JSONL, and runs the existing `evaluate_submissions` deterministic
  checks.
- API keys are read from `~/.api_keys` in `export KEY=VALUE` form.
  Providers pre-wired: DeepSeek, Gemini 2.5 Flash, GPT-4o-mini.
- Submissions, evaluations, and a `summary.md` land under
  `calibration/llm_smoke_v1/` (tracked in git; each run overwrites).
- First DeepSeek V3 run (3 bundles, one per task family): **3/3
  deterministic checks passed**; outputs 173–293 words, cited figures/
  tables and specific quantitative details from the evidence, and
  explicitly named every required evidence identifier. Total cost ≈
  $0.003; latency 11–15s per call.
- Full public-slice run (30 bundles, DeepSeek V3): **30/30 passed** the
  deterministic checks with clean per-family breakdown —
  `abstract_from_evidence 12/12`, `methods_to_text 12/12`,
  `results_to_text 6/6`. Total tokens 89,978 prompt + 10,483 completion
  (~$0.036). Spot-check on a mouse-brain-atlas paper confirmed the
  model's "7 million cells, 4.0 million passed QC" summary is grounded
  (both numbers appear in the source evidence) — not hallucinated.
- The `scripts/llm_smoke_eval.py --task-source inspection-slice` mode
  drove the 30-bundle run and writes outputs to
  `calibration/llm_public_slice_v1/`. Retry-with-backoff is built in
  (3 attempts, exponential backoff) so transient API failures do not
  waste the whole batch.

Critical caveat: **deterministic checks are structural, not
substantive.** They verify that the output contains the required
section marker, the word "evidence", ≥12 words, ≥50% of evidence
tokens, and matches any `expected_answer_texts` — which the prompt
explicitly instructs the model to do. 30/30 tells us the pipeline and
the prompt work end-to-end; it does NOT discriminate between models
or between genuine grounding and fluent plausibility. Judge-layer
scoring is still required before any cross-model claim.

This is the start of Phase 2 (actual model evaluation) after the Phase 1
governance/taxonomy work.

## First judge pass (Claude Sonnet 4.6)

`scripts/llm_judge_eval.py` runs a frontier model against the DeepSeek
V3 submissions with a 5-axis rubric: `writing_structure_compliance`,
`evidence_grounding`, `factual_fidelity`, `traceability`,
`hallucination_absence`. Pass threshold 0.6 per axis, overall pass iff
all axes pass.

Full 30-bundle pass with Claude Sonnet 4.6 (temperature 0.0) on the
DeepSeek public-slice submissions: **judge passed 7 / 30** — versus
30 / 30 on deterministic checks. Per-family: `abstract_from_evidence
0 / 12`, `methods_to_text 5 / 12`, `results_to_text 2 / 6`.

Per-axis means: `writing_structure_compliance 0.665`,
`evidence_grounding 0.693`, `factual_fidelity 0.683`,
`traceability 0.467` (worst), `hallucination_absence 0.689`. 139
grounding issues were flagged across 30 submissions.

Cost: 114,726 input + 26,891 output tokens ≈ $0.75 (plus $0.05 dev).

### Diagnostic findings

- **Deterministic checks were gameable.** The current submission prompt
  instructs DeepSeek to cite the task bundle's internal pointers
  (`methods_section`, `abstract_section`, `section_text`) as
  "evidence identifiers". This passes the traceability heuristic
  (which looks for those exact tokens in the output) but the judge
  correctly flags them as placeholder-style references with no
  correspondence to real figures, tables, or accessions in the source.
  This is the single biggest source of the 139 grounding issues.
- **Real factual errors slipped past deterministic checks.** The judge
  caught: a "nurse-monitored" vs "researcher-monitored" misattribution;
  a "BLU9931 dosing not provided" claim when Fig. 7 explicitly states
  "30 mg/kg b.i.d."; an incomplete microarray-comparison statement
  (YTN16 vs YTN2 only, when the source compared 4 sublines); and a
  comparative-statistics claim not supported by the evidence snippet.
- **Abstracts scored worst** (0 / 12 pass) because abstracts by
  convention do not cite figures/tables, but our prompt demanded
  traceability "evidence identifiers", producing awkward
  self-referential meta-commentary (`the abstract_section of this
  paper synthesizes...`).

Artifacts: `calibration/llm_public_slice_v1_judged/{judgments.jsonl,
summary.{json,md}}` plus 30 per-bundle judge prompts for auditing.

## Second submission + judge pass (prompt v2)

The diagnostic loop closed: the submission prompt was rewritten to
forbid placeholder-pointer citation and instead demand citation of
real figures, tables, quantitative values, and accessions. A new
supplementary metric `citation_specificity` was added to the submission
script, measuring real citation patterns (figure/table references,
p-values, numeric magnitudes with units, accessions matching the
canonical life-sciences regex set, and repository URLs) and explicitly
scoring 0.0 on any output that contains a forbidden pointer token.

Re-running all 30 DeepSeek V3 submissions with prompt v2 and then
re-judging with Claude Sonnet 4.6:

| axis or metric | v1 | v2 |
|---|---:|---:|
| judge overall_pass | 7 / 30 | **15 / 30** |
| all axes >= 0.6 | 7 / 30 | 18 / 30 |
| grounding issues flagged | 139 | 111 |
| mean writing_structure_compliance | 0.665 | 0.816 |
| mean evidence_grounding | 0.693 | 0.808 |
| mean factual_fidelity | 0.683 | 0.779 |
| mean traceability | 0.467 | 0.632 |
| mean hallucination_absence | 0.689 | 0.781 |
| forbidden-pointer-free outputs | 0 / 30 | 30 / 30 |
| deterministic_checks_passed | 30 / 30 | 0 / 30 |

Every axis improved. `results_to_text` went 2 / 6 -> 6 / 6 (judge),
`methods_to_text` 5 / 12 -> 8 / 12, `abstract_from_evidence`
0 / 12 -> 1 / 12 (abstracts remain weakest because the judge rubric
penalizes missing figure/table refs even though abstracts do not
conventionally carry them — see below).

The deterministic pass rate dropped to 0 / 30 in v2 by design, because
the `evaluate_submission` traceability check in `src/life_science_paperwritingbench/baselines.py`
literally looks for the pointer tokens (`methods_section`,
`abstract_section`, etc.) in the output. v2 outputs are correctly free
of those, so the check fails for exactly the reason it was gameable
before. The drop is the diagnostic, not a regression — **the old 30 / 30
pass rate was the false-green-light signal we fixed**.

Cost of the v2 iteration: ~$0.81 ($0.04 submissions + $0.72 judge +
$0.05 dev). Cumulative Phase-2 session spend: ~$1.61.

Artifacts: `calibration/llm_public_slice_v2/{submissions.jsonl,
summary.{json,md}}` and `calibration/llm_public_slice_v2_judged/
{judgments.jsonl, summary.{json,md}}`, plus the updated
`scripts/llm_smoke_eval.py` with `PROMPT_VERSION = "v2"` and the
`citation_specificity` helper.

### Remaining diagnostic

`abstract_from_evidence` still scores 1 / 12 on the judge, dragged down
by a mean traceability of 0.354. The per-axis inspection shows the
judge penalizes abstracts for not citing specific figures/tables — but
real scientific abstracts conventionally do not cite figures or tables.
This is a rubric-fit problem, not a generation problem: the traceability
axis needs to be family-aware (for abstracts, "traceability" should
reward specific quantitative values and named accessions; figure/table
citations should be waived). Fixing this will likely raise the
abstract pass rate without changing the model.

## Remaining substantive targets

The next-step ordering is now governed by the strategic direction doc
[`docs/strategic_review_2026-04-13.md`](./strategic_review_2026-04-13.md),
which replaces and extends the per-item list that previously lived in
this section. Summary of the direction it sets:

- **Tier A — v0.1 research preview** (~4 weeks half-time, ~$13 API,
  $0 cash). Four sessions, each gated by a numeric success criterion:
  1. Scoring-layer refresh: hoist `citation_specificity` into a new
     `src/life_science_paperwritingbench/scoring.py` module; add
     `evaluate_submission_v2` in `baselines.py` while preserving the
     v1 behavior as an alias for release-artifact reproducibility.
     Gate A1: v2 deterministic pass rate ≥ v2 judge pass rate.
  2. Judge rubric v3: switch `scripts/llm_judge_eval.py:RUBRIC_AXES`
     to 4-point anchored ordinal with behavioral anchors; family-aware
     abstract axis (swap `traceability` → `quantitative_specificity`).
     Gate A2: abstract pass rate ≥ 5/12 on the 30-bundle slice.
  3. Cross-model breadth: add Gemini 2.5 Flash and Claude Haiku 4.5
     as submitters; Gemini 2.5 Pro and GPT-5 mini as additional
     judges; 3-judge jury with family-bias exclusion. Gate A3:
     ≥ 30 pp spread between strongest and weakest model.
  4. Canary probe + README refresh + workshop-paper draft.
- **Tier B — v1.0 citable launch** (~3 months on top of Tier A,
  $0–$2k cash), conditional on Tier A exit criteria + at least one
  biomedical colleague committed as co-author annotator. 60-bundle
  human validation, κ / ICC / α reporting, jury-vs-human calibration,
  Inspect-evals integration, and only then `leaderboard_gate_passed`.

See the strategic review doc for the competitive-landscape analysis
(LAB-Bench / PaperBench / DeepScholar-Bench / MedHELM / WritingBench),
judge-validation methodology (Cohen κ / ICC(2,1) / Krippendorff α with
publishable bars), the sample-size reconciliation between
`research/04_judge_design_and_validation.md` (floor of 30 units) and
statistical theory (60 units for CI half-width ≈ 0.15), and per-session
verification commands.

## Follow-up tasks on the governance side

These are still open from Phase 1 and are worth finishing before the
benchmark is claimed to be production-ready:

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
