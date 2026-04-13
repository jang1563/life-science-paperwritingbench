# Evaluation Extraction Contract

## Purpose

`build-evaluation-extraction` converts reviewed parser-assisted extraction specs into
QA-ready artifacts without replacing the writing-oriented truth-manifest flow.

The command produces:

- `ObservationRecord`
- `QuestionRecord`
- `AnswerRecord`
- `SourceQualityRecord`
- `EvaluationExtractionAuditReport`

This layer is intended to support `literature_qa`, `trial_qa`, `figure_qa`,
`table_qa`, and `source_quality_qa` style evaluation units alongside the existing
manuscript-writing task families.

## Input Contract

- `SourcePaper` JSONL
- `EvidenceUnit` JSONL
- reviewed extraction spec JSONL from `build-parser-assisted-extraction`

The extraction spec remains the primary source for assertion-level observations.
Structured metadata can enrich observations when present.

## Supported Structured Metadata

### Figure / table enrichment

- `figure_captions`
- `figure_observations`
- `table_captions`
- `table_rows`
- `table_cells`
- `table_observations`

### Trial enrichment

- `trial_registry_summary`
- `trial_arms`
- `trial_endpoints`
- `trial_outcomes`

### Source-quality enrichment

- `review_comments`
- `review_concerns`
- `decision_letters`

### Resource enrichment

- `resource_identifiers`
- `resource_inventory`

Structured metadata may be:

- plain strings
- delimiter-separated strings
- JSON arrays
- JSON objects

## Current Heuristics

- extraction-spec assertions become draft observations
- figure and table pointers are mapped into separate QA families when identifiable
- human-interventional methods units prefer `trial_qa`
- review comments and decision-letter text are converted into `source_quality_qa`
- source-quality records are classified heuristically into concern type and severity

## Important Limits

- this layer is QA-oriented and does not replace `TruthManifest`
- generated questions and answers are deterministic drafts, not adjudicated gold
- source-quality labels are heuristic suggestions and should be curator-reviewed
- figure/table observations are still metadata-backed, not PDF-native vision output
