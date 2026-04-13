# Implementation Notes

## Current Milestone

The repository is in the governance-hardening phase.

Implemented:

- paper candidate-tier qualification
- unit release-tier qualification
- standards-aware scientific review requirements
- controlled-access packaging constraints
- cross-split leakage detection
- lineage-dominance detection
- JSONL serialization helpers for benchmark governance records
- deterministic public/private holdout helpers
- canary-string generation for release rehearsal
- 12-paper pilot calibration scaffold
- reviewer-form and adjudication-shell schemas for pilot execution
- agreement-metric computation against adjudicated pilot labels
- 60-paper full-calibration scaffold generation and coverage validation
- reviewer-form merge, adjudication-queue construction, calibration summaries, and drift-audit helpers
- CLI support for pilot/full calibration ops and release-index generation
- metadata-driven governance hints for study class, claim mode, overlays, and required standards
- separate writing-quality qualification (`W1 / W2 / W3`) alongside scientific and packaging qualification
- paper-level scientific vs writing review-batch generation for qualification-ready collections
- paper-review form merge, adjudication-shell generation, adjudication queue construction, progress summaries, and finalized paper-review artifacts
- deterministic packaging-review priors from collected paper metadata
- reviewer-facing paper-review packets that combine entries, metadata context, and packaging priors into a deterministic priority order
- reviewer-specific paper-review workload files that bundle each packet with the matching scientific and writing review forms
- reviewer-facing handoff bundles with markdown summaries, top-priority papers, and warning-heavy starts
- batch paper-qualification decision generation from finalized adjudicated reviews plus packaging priors
- shadow-first auto-review source-bundle construction, deterministic proxy-panel voting, aggregation, and auto qualification
- PMCID-backed full-text evidence enrichment for the auto-review lane
- release-bundle generation with enforced holdout split-safety validation
- release-bundle provenance manifests and artifact checksums for packaging verification
- release-bundle verification reports
- TaskBundle / TruthManifestBundle construction
- long-run program progress summaries and maintenance-log scaffolding
- knowledge-base layout initialization helpers
- local-file metadata ingestion standardization and deduplicating normalization
- API-backed collection batch scaffolding with PubMed seed retrieval and Europe PMC / Crossref enrichment
- ingestion audit and verification reports
- local / Cayuga execution-profile scaffolding
- scaffold baseline-replay job generation from local or Cayuga execution profiles
- semi-structured extraction records from local JSONL specs
- parser-assisted extraction drafts from metadata-backed section text into editable evidence-unit/spec artifacts
- QA-ready evaluation extraction into observations, question-answer pairs, and source-quality signals
- QA-oriented TaskBundle construction so evaluation artifacts can flow through the same baseline/eval interface
- truth-manifest build / freeze / verify flow
- deterministic lean-baseline replay and submission scoring from `TaskBundle`
- judge-validation slice template construction and readiness auditing
- judge-review form, adjudication queue, and judge-slice finalization workflow
- judge-batch directory generation and progress summaries
- task-bundle inventory reporting and deterministic judge-candidate selection
- selection-aware judge-batch generation with task-bundle inventory and candidate-summary artifacts

Not implemented yet:

- reviewer calibration UI
- external HPC execution wrappers for large-scale replay
- automatic extraction of `EvidenceUnit` from full paper text/PDFs
- actual human-adjudicated judge validation content beyond the current template/audit scaffold
- uniform richer section/full-text enrichment for every paper in the `180-paper` qualification-ready corpus

## Design Choices

- The package uses only the Python standard library.
- `qualify_paper()` does not return final public release eligibility.
- `qualify_paper()` now separates source suitability from writing-exemplar suitability: `candidate_tier` remains source-governance oriented, while `public_writing_eligible` is reserved for `W1` papers that can act as public writing exemplars.
- `qualify_unit()` is the first function that can emit a final release tier.
- `TruthManifest` is evidence/provenance oriented rather than manuscript oriented.
- standards such as `CONSORT_2025`, `STROBE`, `PRISMA_2020`, `MIAME_MINSEQE`, and `MIQE_2_0` are used as executable governance requirements, not only as documentation labels.
- public/private holdout assignment is deterministic by hashed unit ID plus salt, so release rehearsal is reproducible.
- release artifacts separate `benchmark_split` from `holdout_bucket` to avoid routing ambiguity.
- pilot and full calibration coverage are validated as code, not left as prose checklists.
- pilot/full agreement thresholds are validated separately from qualification logic, which keeps calibration governance distinct from benchmark scoring.
- full calibration drift is tracked as a first-class audit artifact rather than a spreadsheet-only process.
- metadata hinting is advisory rather than authoritative; it surfaces likely standards and configuration mismatches without overriding human curation.
- long-run execution remains `file + CLI + periodic batch`; no always-on services are assumed.
- local-file ingestion is the first supported M1 path; API-backed ingestion can be layered later without changing the normalized artifact contract.
- API-backed collection now sits above the existing local-file normalization contract: `ApiFetchRecord -> CollectionCandidateRecord -> MetadataSourceRecord -> SourcePaper`.
- collection fetches are replay-first by design: raw dumps are reused unless `--refresh` is supplied, so offline reruns and tests can reuse canonical source payloads.
- PubMed is used only for seed retrieval, while Europe PMC and Crossref are enrichment-only sources for OA/full-text and DOI/license/Crossmark signals.
- reserve PubMed queries run only when a class-specific primary seed yields fewer than 60 unique candidates, which keeps the first pass deterministic while still handling underfilled classes.
- Cayuga integration is currently profile-based rather than launcher-based, so cluster execution can be added without coupling governance logic to a scheduler.
- semi-structured extraction is spec-driven on purpose, so human-reviewed evidence bundles can be built deterministically before any PDF parser or model-based extractor is introduced.
- parser-assisted extraction is deliberately conservative: it drafts `EvidenceUnit` and extraction specs from metadata-backed section text, then hands off to the existing reviewed spec-driven flow.
- evaluation extraction is deliberately parallel to truth-manifest construction: it creates QA-ready artifacts for `literature_qa`, `trial_qa`, `figure_qa`, `table_qa`, and `source_quality_qa` without changing the benchmark truth contract.
- lean baseline replay is deterministic and uses only `TaskBundle` inputs, so baseline rehearsal stays separate from judge logic and private-holdout evaluation.
- judge validation is now scaffolded as a separate file/CLI workflow, and program progress only counts units that are human-adjudicated, frozen, and rubric-complete.
- judge review operations mirror calibration ops: blank templates are generated deterministically, duplicate uploads are merge-safe, and finalized adjudications can be applied back onto `JudgeValidationUnit` artifacts.
- judge batch generation now uses the same deterministic candidate-selection layer as standalone judge-candidate curation, so `build-judge-batch` and `select-judge-candidates` stay consistent.
- auto review is explicitly a parallel, lower-trust lane: it uses deterministic prechecks plus a proxy three-role panel and is hard-capped below public release.
- auto review artifacts carry execution/profile/model fingerprints so shadow triage runs can be replayed on Cayuga or local environments without changing governance outputs.
- auto-only outputs never set `public_writing_eligible`, never count toward judge readiness, and only become useful for downstream extraction when a paper reaches `shadow_candidate`.
- the first full auto-review pass over the current `180-paper` qualification-ready corpus produced `180 metadata_only` bundles and therefore `180 stress_candidate` records; this is treated as an evidence-richness diagnosis, not a model failure.
- cached PMC full-text enrichment is now wired in ahead of auto-review bundling, and the current full enriched pass now produces `180 shadow_candidate` papers, `0 excluded`, and `180 review_ready`.
- auto review now filters modality overlays against direct bundle evidence before enforcing overlay-specific standards, which prevents false positives such as travel-distance `km` text incorrectly triggering `ENZYMOLOGY/STRENDA`.
- auto review now also uses richer abstract- and figure-aware rescue logic for protocol/resource papers and underparsed empirical papers, which cleared the prior four-paper residual ceiling in the full180 enriched pass.
- the current shadow release lane is `auto_review_shadow_v10`, with `180` shadow papers, `518` bundles, `430` public bundles, `88` private bundles, and `0` mixed-holdout papers.
- the `auto_review_shadow_v10` directory now also carries `baseline_runs.jsonl`, `program_progress.json`, and `maintenance_log.jsonl`, and the current progress report marks `v1_core_gate_passed = true` while leaving the leaderboard gate closed.
- a new `shadow_public_inspection_v1` slice now lives alongside the release artifacts: `30` public-shadow entries, class-balanced at `5` per study class, with `17` low-confidence entries prioritized for manual inspection.
- the inspection lane now includes a deterministic taxonomy report; after the grounding-aware parser refresh, the current top buckets are `low_confidence_shadow (17)`, `identifier_sparse_low_confidence (9)`, and `trial_registry_traceability (8)`.
- parser/enrichment `v11` improved source-bundle evidence without changing figure/table volume: `resource_identifier_count` moved from `18` to `30`, `trial_registry_count` from `41` to `48`, and writing labels improved from `W1/W2/W3 = 16/157/7` to `23/153/4`.
- the `shadow_public_inspection_v1 -> v2` delta confirms that these parser gains reached the inspection lane: `resource_ids` tags increased by `3`, while `identifier_sparse_low_confidence` dropped from `12` to `9`.
- parser/enrichment `v12` now separates `figure/table captions` from `figure/table reference snippets`; the full180 enriched pass records `figure_reference_snippet_count = 166` and `table_reference_snippet_count = 127`.
- the `shadow_public_inspection_v2 -> v3` delta shows that the grounding-aware tags reached inspection as intended: `figure_grounded +28`, `table_grounded +23`, and `figure_table_grounding -28`.
- `recovery_v1` is now a deterministic batch artifact rather than an ad hoc list: it selects `30` class-balanced `near_shadow_scientific_borderline` papers, writes selected `SourcePaper` and packaging-prior subsets, and generates a Cayuga rerun script that rebuilds evidence enrichment, source bundles, panel votes, aggregated reviews, and auto qualification outputs in one pass.
- recovery-batch selection now supports `--exclude-selected-entries`, so later waves can be built from the same queue without reusing prior papers.
- `recovery_v2` is now scaffolded as the first non-overlapping follow-on wave after `recovery_v1`: it selects `30` more papers with `0` overlap, preserves class balance, and writes a separate Cayuga rerun script plus overlap report.

## Default Policies

- public/private holdout default: `0.8 / 0.2`
- canary prefix default: `LS-PWB-CANARY`
- controlled-access papers require:
  - `controlled_access_rule_satisfied = True`
  - at least one allowed safe derived artifact
  - an `artifact_inventory_id`
- preprints are shadow-only

## Next Recommended Work

1. Add parser-assisted extraction from richer section exports or parsed full text on top of the current metadata-driven draft path.
2. Add task-bundle construction for QA-oriented evaluation artifacts in parallel with writing bundles.
3. Add API-backed ingestion connectors for PubMed / Crossref / Europe PMC on top of the local-file contract.
4. Use `paper_review_packets.jsonl` as the reviewer-facing work queue, then populate the `paper_review_v1` batch with completed scientific and writing review forms for the `180 qualification-ready` papers.
5. Populate the judge-validation slice with real human-adjudicated units after curation protocol sign-off.
6. Add richer parser-assisted extraction from section exports or parsed full text.
7. Add optional HPC execution wrappers for large baseline replay and blind private-holdout scoring.
8. Push richer parser/evidence enrichment at future newly collected papers and harder paper types rather than rerunning broad recovery waves blindly.
9. Keep the `auto_review_shadow_v10` public lane as the deterministic development surface while human review remains unavailable.
