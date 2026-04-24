# Life-Science PaperWritingBench

This repository is building a life-science paper-writing benchmark with two
coupled layers:

- benchmark governance: which papers and evidence units are safe and strong
  enough to curate and release
- benchmark evaluation: how LLM-generated Methods, Results, and Abstract
  sections are scored, judged, audited, and stress-tested for contamination

The governance layer is still the foundation of the project. It decides:

- whether a source paper is strong enough to curate,
- whether its evidence units can be extracted,
- and which release tier each unit belongs to.

## Current Focus

The repository now implements a qualification-and-evaluation stack with three
governance stages and an early model-evaluation lane.

Governance stages:

1. `paper review`
2. `evidence-unit extraction + truth-manifest freeze`
3. `unit release-tier assignment`

This separation is intentional. In an AI-for-Science benchmark, paper-level eligibility, unit-level eligibility, and public release eligibility should not collapse into one boolean.

Current evaluation lane:

1. deterministic submission scoring
2. API-backed LLM baseline generation
3. rubric-based LLM judging
4. cross-model matrix summaries
5. canary-style contamination probes

## Current Evaluation Status

The current repo state is best thought of as a `v0.1 research preview`.

Current evaluation anchors:

- best judged agentic artifact:
  `calibration/llm_agentic_public_slice_v1_rerun5_judged_v3/`
- best deterministic / citation-specificity artifact:
  `calibration/llm_agentic_public_slice_v1_rerun2/`
- current partial cross-model matrix:
  `calibration/llm_public_slice_matrix_v1/summary.md`
- current canary probe report:
  `docs/canary_probe_report.md`

## What Exists

- a dependency-free Python package under `src/life_science_paperwritingbench/`
- typed models for:
  - `SourcePaper`
  - `ScientificReview`
  - `WritingReview`
  - `PackagingReview`
  - `EvidenceUnit`
  - `TruthManifest`
  - `BenchmarkUnit`
- governance logic for:
  - paper scientific grade: `A / B / C / Q`
  - paper writing grade: `W1 / W2 / W3`
  - paper packaging grade: `P1 / P2 / P3`
  - paper candidate tier: `public_gold_candidate / shadow_candidate / stress_candidate / excluded`
  - unit release tier: `public_gold / shadow_gold / stress_only / excluded`
- standards-aware scientific qualification
- lineage-aware split leakage and dominance checks
- JSONL read/write helpers for governance artifacts
- deterministic `public/private` holdout helpers and canary-string generation
- release bundle generation with split-safety validation
- release bundle provenance manifests and artifact checksums
- release bundle verification reports
- a 12-paper pilot calibration scaffold under `calibration/`
- reviewer-form and adjudication helpers for pilot execution
- full-calibration coverage validation, scaffold generation, adjudication queues, and drift audits
- metadata-based governance hinting for study class, claim mode, overlays, and standards
- paper-level scientific vs writing review-batch scaffolding for qualification-ready collections
- shadow-first auto-review source bundling, proxy panel voting, aggregation, and auto qualification
- local-file metadata ingestion and normalization for exported literature metadata
- API-backed collection scaffolding for PubMed seed retrieval plus Europe PMC / Crossref enrichment
- deterministic releaseability prechecks and ingestion verification reports
- semi-structured extraction helpers for `AssertionRecord`, `EvidenceRecord`, and `EvidenceExtractionRecord`
- parser-assisted extraction drafts from source-paper metadata into `EvidenceUnit` + extraction-spec JSONL
- QA-ready evaluation extraction into `ObservationRecord`, `QuestionRecord`, `AnswerRecord`, and `SourceQualityRecord`
- evaluation task-bundle construction for QA-oriented benchmark families
- truth-manifest build / freeze / verify CLI flow
- TaskBundle / TruthManifestBundle construction helpers
- deterministic lean-baseline replay and submission scoring for released TaskBundles
- deterministic v2 submission scoring and deterministic-vs-judge alignment audits
- API-backed single-pass and agentic `writer -> critic -> reviser` evaluation scripts
- shared frontier-model registry and backend runtime for submitters, judges, canary probes, and matrix summaries
- shared single-pass writing prompt builder for external runner reuse
- rubric `v3` LLM judging with a 4-point anchored ordinal scale
- family-aware abstract judging that swaps `traceability` for `quantitative_specificity`
- partial cross-model matrix aggregation and reporting
- completion-style canary probe artifacts with redacted outputs only
- Inspect-compatible task adapter plus artifact-backed submission / judge replay helpers
- publication-validation slice builders and readiness-gate summaries
- publication-validation study-class stratification auditing with per-family targets and deficits
- program-progress summaries and maintenance-log scaffolding
- local and Cayuga execution-profile scaffolding
- knowledge-base directory initialization helpers
- research notes under `research/`
- governance cards under `docs/`

## Qualification Model

`qualify_paper(...)` returns a `PaperQualificationDecision` with:

- `scientific`
- `writing`
- `packaging`
- `candidate_tier`
- `public_writing_eligible`
- `eligible_for_unit_extraction`
- `required_standards`
- `missing_standards`
- `integrity_disposition`

`qualify_unit(...)` returns a `UnitQualificationDecision` with:

- `release_tier`
- `gold_eligible`
- `reasons`

Final public release is only possible after a frozen `TruthManifest` exists. `public_writing_eligible` is stricter: it is only `True` when the paper is a public-gold source candidate and also satisfies `W1` writing-exemplar criteria.

Auto-only review is intentionally stricter and lower-trust. `build-auto-paper-qualification-decisions` writes `AutoQualificationRecord` artifacts that:

- never emit `public_gold_candidate`
- always keep `public_writing_eligible = False`
- never count toward judge validation readiness
- are intended only for `shadow_candidate` or `stress_candidate` triage

## Default Governance Policies

- public holdout policy: `public 80% / private 20%`
- canary default prefix: `LS-PWB-CANARY`
- public-gold publication window: `2018-present`
- preprints: knowledge-base or shadow use only
- open peer review: audit evidence only

## Related Work

- [LAB-Bench](https://arxiv.org/abs/2407.10362): a biology-research benchmark
  with public/private split discipline and a published canary string. This repo
  borrows more from its contamination-governance pattern than from its task mix.
- [PaperBench](https://openai.com/index/paperbench/): a frontier benchmark for
  research replication with structured rubrics and separate judge validation.
  This repo borrows the judge-audit mindset and rubric decomposition, but our
  task is evidence-grounded biomedical section writing rather than code
  replication.
- [DeepScholar-Bench](https://sky.cs.berkeley.edu/project/deepscholar-bench/):
  a live benchmark for generating related-work sections from current literature.
  It is the closest benchmark in spirit, but narrower in task scope than our
  Methods / Results / Abstract writing focus.
- [MedHELM](https://www.nature.com/articles/s41591-025-04151-2): a clinical
  evaluation framework that demonstrates why biomedical benchmark claims need
  human-agreement statistics, not only LLM-judge scores.
- [WritingBench](https://arxiv.org/abs/2503.05244): a broad generative-writing
  benchmark. It is useful as a writing-evaluation reference, but it is not
  biomedical and not evidence-conditioned.

## Evaluation Methodology

- Released writing families are `methods_to_text`, `results_to_text`, and
  `abstract_from_evidence`.
- Deterministic scoring currently uses the `v2` layer for structure,
  traceability, and citation-specificity style checks before any LLM judge is
  considered.
- The current judge configuration is rubric `v3`:
  - 4-point anchored ordinal scores (`0`-`3`)
  - pass rule `mean(axis_scores) >= 2.0`
  - family-aware abstract evaluation where `quantitative_specificity` replaces
    `traceability`
- The current agentic baseline uses a `writer -> critic -> reviser` loop plus a
  non-regressive selector, so a revision is only kept when it does not damage
  deterministic quality.
- The intended jury-style evaluation setup is multi-judge rather than
  single-judge. Current live artifacts already include Claude Sonnet 4.6,
  GPT-5.4 mini, and GPT-5 mini cells, and the planned full matrix applies
  family-bias exclusion rather than allowing a same-family judge to score its
  own submitter family.
- Contamination controls include:
  - deterministic `public/private` holdout assignment
  - per-unit canary strings in the release index
  - completion-style canary probes that check exact reproduction without
    writing raw canaries or raw model outputs back into repo artifacts

## Current Limitations

- This is still a `v0.1 research preview`, not a human-validated benchmark
  release.
- The repo now has a populated, packet-complete publication-validation batch
  from real benchmark bundles, but it is still awaiting human review and
  adjudication; `kappa`, `ICC`, and `alpha` are still pending.
- The current cross-model matrix and canary probes are meaningful but
  incomplete; Anthropic coverage is present in current artifacts, while Gemini
  submitter/judge coverage is still missing from the release-facing gates.
- `leaderboard_gate_passed` remains `false`, which is intentional.
- The project is still effectively solo-authored at this stage; co-authored
  human validation is still the threshold between preview status and a
  defensible benchmark release.

## Quick Start

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Frontier registry helpers:

```bash
PYTHONPATH=src python3 - <<'PY'
from life_science_paperwritingbench import load_frontier_registry, default_frontier_registry_path

registry = load_frontier_registry(default_frontier_registry_path())
print(sorted(registry))
PY
```

Build a publication-validation slice and summarize the readiness gate:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-publication-validation-slice \
  --task-bundles knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl \
  --output /tmp/publication_validation.jsonl \
  --summary-output /tmp/publication_validation_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-publication-readiness \
  --matrix-summary calibration/llm_public_slice_matrix_v1/summary.json \
  --canary-summary calibration/canary_probe_v1_live_hosted_working_set/summary.json \
  --validation-summary /tmp/publication_validation_summary.json \
  --agreement-metrics calibration/judge_v1/judge_agreement.json \
  --output /tmp/publication_readiness.json
```

For human annotation work, prefer the batch helper so the selected bundles,
judge units, reviewer forms, adjudication shells, reviewer-facing markdown
packets, and annotation-hold QA summaries all land in one directory:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-publication-validation-batch \
  --task-bundles knowledge_base/released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl \
  --output-dir calibration/publication_validation_v1 \
  --adjudicator adjudicator_1 \
  --reviewers reviewer_a reviewer_b
```

This batch now also writes:

- `review_packets/packet_manifest.jsonl`
- `review_packets/reviewer_assignments/*.jsonl`
- `review_packets/reviewer_indexes/*.md`
- `review_packets/packets/<reviewer>/*.md`
- `annotation_hold_audit.json`
- `annotation_hold_audit.md`

Rebuild packet artifacts or rerun the structural audit independently:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-publication-review-packets \
  --batch-dir calibration/publication_validation_v1

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-annotation-hold \
  --batch-dir calibration/publication_validation_v1 \
  --output calibration/publication_validation_v1/annotation_hold_audit.json \
  --markdown-output calibration/publication_validation_v1/annotation_hold_audit.md
```

`annotation_hold_audit.json` is intentionally separate from
`publication_readiness_snapshot.json`: the hold audit answers whether the
frozen batch is structurally ready and merely waiting on human review, while
publication readiness stays red until agreement, matrix, and contamination
gates are satisfied.

Inspect adapter usage:

```bash
PYTHONPATH=src python3 - <<'PY'
from inspect_evals.life_science_paperwritingbench import build_inspect_records

records = build_inspect_records(limit=3)
print([record["id"] for record in records])
PY
```

Validate the pilot calibration scaffold:

```bash
PYTHONPATH=src python3 - <<'PY'
from life_science_paperwritingbench import (
    load_jsonl,
    pilot_calibration_spec_from_dict,
    validate_pilot_calibration_set,
)

specs = load_jsonl(
    "calibration/pilot_v1/pilot_manifest.jsonl",
    loader=pilot_calibration_spec_from_dict,
)
print(validate_pilot_calibration_set(specs))
PY
```

Generate and validate a deterministic 60-paper full calibration scaffold:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli write-full-calibration-scaffold \
  --output calibration/full_v1/full_manifest_template.jsonl \
  --summary-output /tmp/full_calibration_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli validate-calibration \
  --manifest calibration/full_v1/full_manifest_template.jsonl \
  --mode full
```

Build reviewer forms, merge uploads, and generate an adjudication queue for full calibration:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-calibration-batch \
  --manifest calibration/full_v1/full_manifest_template.jsonl \
  --forms-output /tmp/full_reviewer_forms.jsonl \
  --adjudication-output /tmp/full_adjudications.jsonl \
  --adjudicator adjudicator_1 \
  --reviewers reviewer_a reviewer_b \
  --mode full \
  --summary-output /tmp/full_batch_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli merge-review-forms \
  --inputs /tmp/full_reviewer_forms.jsonl \
  --output /tmp/full_reviewer_forms_merged.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-adjudication-queue \
  --manifest calibration/full_v1/full_manifest_template.jsonl \
  --forms /tmp/full_reviewer_forms_merged.jsonl \
  --adjudications /tmp/full_adjudications.jsonl \
  --reviewers reviewer_a reviewer_b \
  --output /tmp/full_adjudication_queue.jsonl
```

Initialize the long-run knowledge base layout:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli init-knowledge-base \
  --root knowledge_base
```

Suggest governance hints from source-paper metadata:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli suggest-metadata-hints \
  --papers /tmp/source_papers.jsonl \
  --output /tmp/metadata_hints.jsonl \
  --summary-output /tmp/metadata_hint_summary.json
```

Build a paper-level scientific + writing review batch from qualification-ready papers:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-paper-review-batch \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --metadata-hints knowledge_base/qualified/collection_v1_2018_present/qualification_ready_metadata_hints.jsonl \
  --entries-output calibration/paper_review_v1/paper_review_entries.jsonl \
  --scientific-forms-output calibration/paper_review_v1/scientific_review_forms.jsonl \
  --writing-forms-output calibration/paper_review_v1/writing_review_forms.jsonl \
  --summary-output calibration/paper_review_v1/paper_review_summary.json \
  --batch-id paper_review_v1 \
  --reviewers reviewer_a reviewer_b

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-paper-review-adjudication-shells \
  --entries calibration/paper_review_v1/paper_review_entries.jsonl \
  --output calibration/paper_review_v1/paper_review_adjudications.jsonl \
  --adjudicator adjudicator_1 \
  --reviewers reviewer_a reviewer_b

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-paper-review-queue \
  --entries calibration/paper_review_v1/paper_review_entries.jsonl \
  --scientific-forms calibration/paper_review_v1/scientific_review_forms.jsonl \
  --writing-forms calibration/paper_review_v1/writing_review_forms.jsonl \
  --adjudications calibration/paper_review_v1/paper_review_adjudications.jsonl \
  --reviewers reviewer_a reviewer_b \
  --output calibration/paper_review_v1/paper_review_queue.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-paper-review-progress \
  --entries calibration/paper_review_v1/paper_review_entries.jsonl \
  --scientific-forms calibration/paper_review_v1/scientific_review_forms.jsonl \
  --writing-forms calibration/paper_review_v1/writing_review_forms.jsonl \
  --adjudications calibration/paper_review_v1/paper_review_adjudications.jsonl \
  --reviewers reviewer_a reviewer_b \
  --output calibration/paper_review_v1/paper_review_progress.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-packaging-review-priors \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --output calibration/paper_review_v1/paper_packaging_review_priors.jsonl \
  --summary-output calibration/paper_review_v1/paper_packaging_review_priors_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-paper-review-packets \
  --entries calibration/paper_review_v1/paper_review_entries.jsonl \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --packaging-reviews calibration/paper_review_v1/paper_packaging_review_priors.jsonl \
  --output calibration/paper_review_v1/paper_review_packets.jsonl \
  --summary-output calibration/paper_review_v1/paper_review_packets_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-paper-review-workloads \
  --packets calibration/paper_review_v1/paper_review_packets.jsonl \
  --scientific-forms calibration/paper_review_v1/scientific_review_forms.jsonl \
  --writing-forms calibration/paper_review_v1/writing_review_forms.jsonl \
  --reviewers reviewer_a reviewer_b \
  --output-dir calibration/paper_review_v1/workloads

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-paper-review-handoff \
  --assignments calibration/paper_review_v1/workloads/reviewer_a_paper_review_assignments.jsonl \
               calibration/paper_review_v1/workloads/reviewer_b_paper_review_assignments.jsonl \
  --reviewers reviewer_a reviewer_b \
  --output-dir calibration/paper_review_v1/handoff

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-paper-qualification-decisions \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --adjudicated-reviews calibration/paper_review_v1/adjudicated_paper_reviews.jsonl \
  --packaging-reviews calibration/paper_review_v1/paper_packaging_review_priors.jsonl \
  --output calibration/paper_review_v1/paper_qualification_decisions.jsonl \
  --summary-output calibration/paper_review_v1/paper_qualification_decisions_summary.json
```

Run the shadow-first auto-review path for the same `180-paper` qualification-ready collection:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-auto-review-evidence-enrichments \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --raw-dir knowledge_base/raw/collection_v1_2018_present/pmc_fulltext_auto_review \
  --output knowledge_base/enriched/collection_v1_2018_present/auto_review/evidence_enrichments.jsonl \
  --fetch-records-output knowledge_base/raw/collection_v1_2018_present/pmc_fulltext_fetch_records.jsonl \
  --summary-output knowledge_base/enriched/collection_v1_2018_present/auto_review/evidence_enrichment_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-auto-review-source-bundles \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --evidence-enrichments knowledge_base/enriched/collection_v1_2018_present/auto_review/evidence_enrichments.jsonl \
  --output knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles.jsonl \
  --summary-output knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-auto-review-source-bundles \
  --source-bundles knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles.jsonl \
  --output knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundle_audit.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli write-execution-profile \
  --profile cayuga \
  --repo-root . \
  --cayuga-root <CAYUGA_ROOT> \
  --output configs/execution/cayuga_profile.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli run-auto-paper-reviews \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --source-bundles knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles.jsonl \
  --execution-profile configs/execution/cayuga_profile.json \
  --model-id cayuga-shadow-v1 \
  --packaging-reviews calibration/paper_review_v1/paper_packaging_review_priors.jsonl \
  --output calibration/auto_review_v1/panel_votes.jsonl \
  --summary-output calibration/auto_review_v1/panel_votes_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli aggregate-auto-paper-reviews \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --source-bundles knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles.jsonl \
  --panel-votes calibration/auto_review_v1/panel_votes.jsonl \
  --output calibration/auto_review_v1/aggregated_reviews.jsonl \
  --summary-output calibration/auto_review_v1/aggregated_reviews_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-auto-paper-qualification-decisions \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --source-bundles knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles.jsonl \
  --aggregated-reviews calibration/auto_review_v1/aggregated_reviews.jsonl \
  --packaging-reviews calibration/paper_review_v1/paper_packaging_review_priors.jsonl \
  --output knowledge_base/qualified/collection_v1_2018_present/auto_review/auto_qualification_records.jsonl \
  --summary-output knowledge_base/qualified/collection_v1_2018_present/auto_review/auto_qualification_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-auto-review-batch \
  --papers knowledge_base/normalized/collection_v1_2018_present/qualification_ready_source_papers.jsonl \
  --source-bundles knowledge_base/enriched/collection_v1_2018_present/auto_review/source_bundles.jsonl \
  --panel-votes calibration/auto_review_v1/panel_votes.jsonl \
  --aggregated-reviews calibration/auto_review_v1/aggregated_reviews.jsonl \
  --qualifications knowledge_base/qualified/collection_v1_2018_present/auto_review/auto_qualification_records.jsonl \
  --output knowledge_base/qualified/collection_v1_2018_present/auto_review/auto_review_batch_summary.json
```

The first metadata-only auto-review pass over the current `180-paper` collection produced:

- `metadata_only` bundles: `180`
- `shadow_candidate`: `0`
- `stress_candidate`: `180`
- `eligible_for_unit_extraction`: `0`

This is expected for the current corpus because it is still mostly `abstract + metadata`. The auto-review lane is therefore useful today as a reproducible triage diagnostic, not as a substitute for richer evidence extraction or human review.

The current enriched full-collection pass is now much stronger. `full180_enriched_v9` produced:

- `shadow_candidate`: `180`
- `excluded`: `0`
- `eligible_for_unit_extraction`: `180`
- `review_ready`: `180`
- `partial`: `0`
- `metadata_only`: `0`

Current qualification summary:

- `auto_qualification_summary_full180_enriched_v13.json`

Current shadow release lane:

- `auto_review_shadow_v10`
- `180` shadow papers
- `518` `shadow_gold` bundles
- `430` public bundles
- `88` private bundles
- `0` split-safety violations
- `0` mixed-holdout papers
- `v1_core_gate_passed = true`

Current release artifacts:

- `release_summary.json`
- `shadow_candidate_holdout_consistency_report.json`
- `shadow_candidate_public_baseline_comparison_summary.json`
- `program_progress.json`
- `maintenance_log.jsonl`
- `shadow_public_inspection_v1_summary.json`
- `shadow_public_inspection_v1.md`
- `shadow_public_inspection_v1_taxonomy.json`
- `shadow_public_inspection_v1_taxonomy.md`

Important note on current auto review behavior:

- the panel is still deterministic and rule-based today
- overlay-specific standards are only enforced when the bundle contains direct evidence for that modality
- this prevents false positives such as travel-distance `km` text incorrectly triggering `ENZYMOLOGY/STRENDA`

Residual non-shadow summary:

- `residual_non_shadow_summary_v8.json`

Current judge-inspection batch on the public shadow lane:

- [judge_batch_summary.json](calibration/auto_review_shadow_judge_v6/judge_batch_summary.json)

Current inspection-taxonomy highlights:

- `7` overlapping categories in the current public inspection slice
- after grounding-aware parser `v12`, the refreshed `shadow_public_inspection_v3` slice now carries `figure_grounded (28)` and `table_grounded (23)` tags
- parser/enrichment `v13` now adds explicit `trial_registry_reference_snippets`; the full180 enriched pass records `trial_registry_reference_snippet_count = 91`
- the same `v13` pass also improves writing labels from `W1/W2/W3 = 23/153/4` to `63/113/4`
- confidence calibration `v14` keeps `180 shadow_candidate` papers but shifts `confidence = low/medium` from `34/146` to `5/175`
- the current largest taxonomy buckets are `stable_shadow_controls (23)`, `low_confidence_shadow (3)`, and `identifier_sparse_low_confidence (3)`
- the taxonomy is meant to drive prompt/parser refinement, not replace qualification
- the refreshed `shadow_public_inspection_v2` slice reduced `identifier_sparse_low_confidence` from `12` to `9` and increased `resource_ids` coverage from `2` to `5`
- the paired delta report lives at `shadow_public_inspection_v1_to_v2_delta.json`
- the next delta, `shadow_public_inspection_v2_to_v3_delta.json`, shows `figure_table_grounding -28` with grounded tags added to the slice
- the latest delta, `shadow_public_inspection_v3_to_v4_delta.json`, shows `trial_registry_grounded +4` and `trial_registry_traceability -8`
- the newest delta, `shadow_public_inspection_v4_to_v5_delta.json`, shows `low_confidence_shadow -14` and `identifier_sparse_low_confidence -6`
- the current delta, `shadow_public_inspection_v5_to_v6_delta.json`, shows `resource_release_grounded +3` and `resource_release_specificity -3`, leaving only `2` resource-release specificity entries in the slice

Standardize local metadata exports, then normalize them into repo-native papers:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli ingest-metadata \
  --input /tmp/raw_metadata_export.jsonl \
  --output /tmp/metadata_source_records.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli normalize-papers \
  --input /tmp/metadata_source_records.jsonl \
  --papers-output /tmp/source_papers.jsonl \
  --ingestion-output /tmp/ingestion_records.jsonl \
  --audit-output /tmp/ingestion_audit.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli verify-ingestion \
  --papers /tmp/source_papers.jsonl \
  --ingestion-records /tmp/ingestion_records.jsonl \
  --output /tmp/ingestion_verify.json
```

Run the first API-backed collection batch using the checked-in `2018-present` design:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-collection-batch \
  --output configs/collection/collection_v1_2018_present.json \
  --queries-output configs/collection/collection_v1_2018_present_queries.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli fetch-pubmed-batch \
  --batch-spec configs/collection/collection_v1_2018_present.json \
  --raw-dir knowledge_base/raw/collection_v1_2018_present/pubmed \
  --output knowledge_base/raw/collection_v1_2018_present/pubmed_fetch_records.jsonl \
  --summary-output knowledge_base/raw/collection_v1_2018_present/pubmed_fetch_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli merge-collection-candidates \
  --input knowledge_base/raw/collection_v1_2018_present/pubmed_fetch_records.jsonl \
  --output knowledge_base/normalized/collection_v1_2018_present/collection_candidates.jsonl \
  --summary-output knowledge_base/normalized/collection_v1_2018_present/merge_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli fetch-europepmc-enrichment \
  --input knowledge_base/normalized/collection_v1_2018_present/collection_candidates.jsonl \
  --raw-dir knowledge_base/raw/collection_v1_2018_present/europepmc \
  --output knowledge_base/enriched/collection_v1_2018_present/collection_candidates_europepmc.jsonl \
  --fetch-records-output knowledge_base/raw/collection_v1_2018_present/europepmc_fetch_records.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli fetch-crossref-enrichment \
  --input knowledge_base/enriched/collection_v1_2018_present/collection_candidates_europepmc.jsonl \
  --raw-dir knowledge_base/raw/collection_v1_2018_present/crossref \
  --output knowledge_base/enriched/collection_v1_2018_present/collection_candidates_enriched.jsonl \
  --fetch-records-output knowledge_base/raw/collection_v1_2018_present/crossref_fetch_records.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli shortlist-collection-candidates \
  --input knowledge_base/enriched/collection_v1_2018_present/collection_candidates_enriched.jsonl \
  --output knowledge_base/qualified/collection_v1_2018_present/shortlisted_candidates.jsonl \
  --metadata-output knowledge_base/qualified/collection_v1_2018_present/metadata_source_records.jsonl \
  --summary-output knowledge_base/qualified/collection_v1_2018_present/shortlist_report.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli normalize-papers \
  --input knowledge_base/qualified/collection_v1_2018_present/metadata_source_records.jsonl \
  --papers-output knowledge_base/normalized/collection_v1_2018_present/source_papers.jsonl \
  --ingestion-output knowledge_base/normalized/collection_v1_2018_present/ingestion_records.jsonl \
  --audit-output knowledge_base/normalized/collection_v1_2018_present/ingestion_audit.json
```

Write a Cayuga execution profile without moving the repo source of truth:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli write-execution-profile \
  --profile cayuga \
  --repo-root "$PWD" \
  --cayuga-root <CAYUGA_ROOT> \
  --output configs/execution/cayuga_profile.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli write-baseline-replay-job \
  --execution-profile configs/execution/cayuga_profile.json \
  --task-bundles /tmp/task_bundles.jsonl \
  --baseline-kind retrieval_writer \
  --output-dir /tmp/cayuga_baseline_replay \
  --script-output /tmp/cayuga_baseline_replay/run_baseline_replay.sh \
  --spec-output /tmp/cayuga_baseline_replay/baseline_replay_spec.json
```

Extract semi-structured evidence records and build frozen truth manifests:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-parser-assisted-extraction \
  --papers /tmp/source_papers.jsonl \
  --evidence-units-output /tmp/evidence_units.jsonl \
  --specs-output /tmp/extraction_specs.jsonl \
  --audit-output /tmp/parser_assisted_extraction_audit.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-evaluation-extraction \
  --papers /tmp/source_papers.jsonl \
  --evidence-units /tmp/evidence_units.jsonl \
  --specs /tmp/extraction_specs.jsonl \
  --observations-output /tmp/observations.jsonl \
  --questions-output /tmp/questions.jsonl \
  --answers-output /tmp/answers.jsonl \
  --source-quality-output /tmp/source_quality.jsonl \
  --audit-output /tmp/evaluation_extraction_audit.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-evaluation-task-bundles \
  --papers /tmp/source_papers.jsonl \
  --observations /tmp/observations.jsonl \
  --questions /tmp/questions.jsonl \
  --answers /tmp/answers.jsonl \
  --truth-manifests /tmp/truth_manifests_frozen.jsonl \
  --source-quality-records /tmp/source_quality.jsonl \
  --default-release-tier shadow_gold \
  --output /tmp/evaluation_task_bundles.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli extract-evidence-records \
  --papers /tmp/source_papers.jsonl \
  --evidence-units /tmp/evidence_units.jsonl \
  --input /tmp/extraction_specs.jsonl \
  --assertions-output /tmp/assertions.jsonl \
  --evidence-records-output /tmp/evidence_records.jsonl \
  --extractions-output /tmp/extractions.jsonl \
  --audit-output /tmp/extraction_audit.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-truth-manifests \
  --papers /tmp/source_papers.jsonl \
  --evidence-units /tmp/evidence_units.jsonl \
  --assertions /tmp/assertions.jsonl \
  --evidence-records /tmp/evidence_records.jsonl \
  --extractions /tmp/extractions.jsonl \
  --output /tmp/truth_manifests.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli freeze-truth-manifests \
  --input /tmp/truth_manifests.jsonl \
  --output /tmp/truth_manifests_frozen.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli verify-truth-manifests \
  --papers /tmp/source_papers.jsonl \
  --evidence-units /tmp/evidence_units.jsonl \
  --assertions /tmp/assertions.jsonl \
  --evidence-records /tmp/evidence_records.jsonl \
  --extractions /tmp/extractions.jsonl \
  --manifests /tmp/truth_manifests_frozen.jsonl \
  --output /tmp/truth_manifest_verify.jsonl
```

Generate blank reviewer forms and adjudication shells:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-pilot-templates \
  --manifest calibration/pilot_v1/pilot_manifest.jsonl \
  --forms-output /tmp/reviewer_forms.jsonl \
  --adjudication-output /tmp/adjudications.jsonl \
  --adjudicator adjudicator_1 \
  --reviewers reviewer_a reviewer_b
```

Build a release index from benchmark-unit and unit-decision JSONL:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-release-index \
  --units /tmp/benchmark_units.jsonl \
  --decisions /tmp/unit_decisions.jsonl \
  --output /tmp/release_index.jsonl
```

`--decisions` should contain `benchmark_unit_id`, `release_tier`, `gold_eligible`, and `reasons` for each benchmark unit.

Build a full release bundle:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-release-bundle \
  --units /tmp/benchmark_units.jsonl \
  --decisions /tmp/unit_decisions.jsonl \
  --output-dir /tmp/release_bundle
```

The release bundle writes:

- `release_index.jsonl`
- `split_safety_violations.jsonl`
- `release_summary.json`
- `provenance_manifest.json`
- `checksums.json`
- `bundle_verify_report.json`

Verify an existing release bundle:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli verify-release-bundle \
  --bundle-dir /tmp/release_bundle
```

Build TaskBundle artifacts from benchmark inputs:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-task-bundles \
  --papers /tmp/source_papers.jsonl \
  --evidence-units /tmp/evidence_units.jsonl \
  --benchmark-units /tmp/benchmark_units.jsonl \
  --truth-manifests /tmp/truth_manifests.jsonl \
  --decisions /tmp/unit_decisions.jsonl \
  --output /tmp/task_bundles.jsonl \
  --truth-manifest-bundles-output /tmp/truth_manifest_bundles.jsonl
```

Replay a lean baseline and score the resulting submissions:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli run-baseline \
  --task-bundles /tmp/task_bundles.jsonl \
  --baseline-kind retrieval_writer \
  --submissions-output /tmp/submissions.jsonl \
  --run-spec-output /tmp/baseline_run.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli score-submissions \
  --task-bundles /tmp/task_bundles.jsonl \
  --submissions /tmp/submissions.jsonl \
  --output /tmp/evaluations.jsonl
```

Build and audit a judge-validation slice template:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-judge-slice \
  --task-bundles /tmp/task_bundles.jsonl \
  --output /tmp/judge_units.jsonl \
  --target-total 30

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-judge-slice \
  --task-bundles /tmp/task_bundles.jsonl \
  --judge-units /tmp/judge_units.jsonl \
  --output /tmp/judge_slice_audit.json
```

`build-judge-slice` writes rubric templates with the required axes but does not mark them ready. A unit only counts toward program progress when it is human-adjudicated, frozen, and has non-empty labels for `evidence_fidelity`, `traceability`, `provenance_completeness`, and `writing_structure_compliance`.

Build judge review forms, adjudication shells, and finalize reviewed units:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-judge-review-templates \
  --judge-units /tmp/judge_units.jsonl \
  --forms-output /tmp/judge_review_forms.jsonl \
  --adjudication-output /tmp/judge_adjudications.jsonl \
  --adjudicator adjudicator_1 \
  --reviewers reviewer_a reviewer_b

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-judge-adjudication-queue \
  --judge-units /tmp/judge_units.jsonl \
  --forms /tmp/judge_review_forms.jsonl \
  --adjudications /tmp/judge_adjudications.jsonl \
  --reviewers reviewer_a reviewer_b \
  --output /tmp/judge_queue.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli finalize-judge-slice \
  --judge-units /tmp/judge_units.jsonl \
  --adjudications /tmp/judge_adjudications.jsonl \
  --output /tmp/judge_units_finalized.jsonl
```

Or build a full judge batch directory and summarize progress:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-judge-batch \
  --task-bundles /tmp/task_bundles.jsonl \
  --output-dir calibration/judge_v1 \
  --target-total 30 \
  --holdout-bucket public \
  --adjudicator adjudicator_1 \
  --reviewers reviewer_a reviewer_b

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-judge-progress \
  --task-bundles /tmp/task_bundles.jsonl \
  --judge-units calibration/judge_v1/judge_units.jsonl \
  --forms calibration/judge_v1/judge_review_forms.jsonl \
  --adjudications calibration/judge_v1/judge_adjudications.jsonl \
  --reviewers reviewer_a reviewer_b \
  --output calibration/judge_v1/judge_progress.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-judge-agreement \
  --judge-units calibration/judge_v1/judge_units.jsonl \
  --forms calibration/judge_v1/judge_review_forms.jsonl \
  --adjudications calibration/judge_v1/judge_adjudications.jsonl \
  --output calibration/judge_v1/judge_agreement.json
```

`build-judge-batch` now also writes:

- `selected_task_bundles.jsonl`
- `task_bundle_inventory.json`
- `judge_candidate_selection.json`

`summarize-judge-agreement` writes publication-readiness-compatible
top-level metrics including `pre_adjudication_kappa`,
`post_adjudication_kappa`, and `jury_vs_adjudicator_icc`, plus ordinal
alpha and ICC diagnostics.

Inventory task bundles and select a deterministic candidate set for judge curation:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-task-bundles \
  --task-bundles /tmp/task_bundles.jsonl \
  --output /tmp/task_bundle_summary.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli select-judge-candidates \
  --task-bundles /tmp/task_bundles.jsonl \
  --output /tmp/judge_candidate_task_bundles.jsonl \
  --summary-output /tmp/judge_candidate_summary.json \
  --target-total 30 \
  --holdout-bucket public
```

Summarize long-run program progress:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-baseline-run-inventory \
  --run-spec /tmp/reference_run_spec.jsonl \
  --run-spec /tmp/retrieval_run_spec.jsonl \
  --run-spec /tmp/section_run_spec.jsonl \
  --output /tmp/baseline_runs.jsonl

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-program-progress \
  --papers /tmp/source_papers.jsonl \
  --paper-decisions /tmp/paper_decisions_or_auto_records.jsonl \
  --task-bundles /tmp/task_bundles.jsonl \
  --baseline-runs /tmp/baseline_runs.jsonl \
  --output /tmp/program_progress.json

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-shadow-inspection-batch \
  --task-bundles /tmp/public_shadow_task_bundles.jsonl \
  --papers /tmp/shadow_source_papers.jsonl \
  --auto-qualification-records /tmp/auto_qualification_records.jsonl \
  --source-bundles /tmp/source_bundles.jsonl \
  --output /tmp/shadow_inspection.jsonl \
  --summary-output /tmp/shadow_inspection_summary.json \
  --markdown-output /tmp/shadow_inspection.md \
  --target-total 30

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-shadow-inspection-taxonomy \
  --inspection-entries /tmp/shadow_inspection.jsonl \
  --output /tmp/shadow_inspection_taxonomy.json \
  --markdown-output /tmp/shadow_inspection_taxonomy.md \
  --minimum-entry-count 2
```

## Minimal Example

```python
from life_science_paperwritingbench import (
    CandidateTier,
    ClaimMode,
    DomainOutcome,
    PackagingDomain,
    PackagingReview,
    PublicationStatus,
    ScientificCriticalDomain,
    ScientificReview,
    ScientificSupportingDomain,
    SourcePaper,
    StandardId,
    StudyClass,
    qualify_paper,
)

paper = SourcePaper(
    paper_id="PMID:123456",
    title="Example paper",
    publication_year=2024,
    publication_status=PublicationStatus.PUBLISHED,
    peer_reviewed=True,
    study_class=StudyClass.MECHANISTIC_EXPERIMENTAL,
    claim_mode=ClaimMode.EXPLORATORY,
)

scientific_review = ScientificReview(
    critical_domains={
        ScientificCriticalDomain.INTEGRITY_STATUS: DomainOutcome.PASS,
        ScientificCriticalDomain.DESIGN_ANALYSIS_CREDIBILITY: DomainOutcome.PASS,
        ScientificCriticalDomain.MINIMAL_INTERPRETABLE_CORE: DomainOutcome.PASS,
        ScientificCriticalDomain.REQUIRED_TRACEABILITY: DomainOutcome.PASS,
        ScientificCriticalDomain.CLAIM_MODE_ALIGNMENT: DomainOutcome.PASS,
    },
    supporting_domains={
        ScientificSupportingDomain.REPRODUCIBILITY_SUPPORT: DomainOutcome.PASS,
        ScientificSupportingDomain.RESOURCE_SPECIFICITY: DomainOutcome.PASS,
    },
    applied_standards=(StandardId.MDAR,),
    standard_outcomes={StandardId.MDAR: DomainOutcome.PASS},
)

packaging_review = PackagingReview(
    domain_outcomes={
        PackagingDomain.RELEASEABILITY: DomainOutcome.PASS,
        PackagingDomain.EVIDENCE_PACK_RECONSTRUCTABILITY: DomainOutcome.PASS,
        PackagingDomain.ARTIFACT_ACCESS: DomainOutcome.PASS,
        PackagingDomain.PROVENANCE_COMPLETENESS: DomainOutcome.PASS,
        PackagingDomain.SPLIT_SAFETY: DomainOutcome.PASS,
    },
)

decision = qualify_paper(paper, scientific_review, packaging_review)
assert decision.candidate_tier == CandidateTier.PUBLIC_GOLD_CANDIDATE
print(decision.to_dict())
```

## Documentation

- [Implementation Notes](./docs/implementation_notes.md)
- [Long-Term Program](./docs/long_term_program.md)
- [Parser-Assisted Extraction Contract](./docs/parser_assisted_extraction_contract.md)
- [Execution Config README](./configs/execution/README.md)
- [Dataset Card](./docs/dataset_card.md)
- [Benchmark Transparency Card](./docs/benchmark_transparency_card.md)
- [Release Governance Card](./docs/release_governance_card.md)
- [Pilot Calibration README](./calibration/pilot_v1/README.md)
- [Full Calibration README](./calibration/full_v1/README.md)

## Research Index

- [Research README](./research/README.md)

## License and data

- **Code** in this repository is licensed under the [Apache License 2.0](./LICENSE) (see also [`NOTICE`](./NOTICE)). Both commercial and non-commercial use are permitted.
- **Data** ingested or emitted by the pipeline is governed separately — see [`DATA.md`](./DATA.md) for upstream source terms (PubMed, Europe PMC, Crossref, bioRxiv) and release-bundle licensing.
- To cite this work, see [`CITATION.cff`](./CITATION.cff).
