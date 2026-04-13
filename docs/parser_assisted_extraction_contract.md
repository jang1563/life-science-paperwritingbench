# Parser-Assisted Extraction Contract

## Purpose

`build-parser-assisted-extraction` reads `SourcePaper.metadata` and produces draft:

- `EvidenceUnit` records
- extraction spec JSONL records for `extract-evidence-records`

The output is intentionally conservative. It is a reviewable draft, not final truth.
It is also the input layer for `build-evaluation-extraction`, which creates QA-ready
`ObservationRecord`, `QuestionRecord`, `AnswerRecord`, and `SourceQualityRecord` artifacts.

## Supported Metadata Keys

### Abstract / claim cluster

- `abstract`
- `abstract_text`
- `summary`
- `summary_text`
- optional pointers:
  - `abstract_pointer`
  - `abstract_pointers`
- optional excluded assertions:
  - `abstract_excluded_assertions`

### Results / figure-table result

- `results_text`
- `results_summary`
- `figure_table_summary`
- optional structured metadata used by `build-evaluation-extraction`:
  - `figure_captions`
  - `figure_observations`
  - `table_captions`
  - `table_rows`
  - `table_cells`
  - `table_observations`
- optional pointers:
  - `figure_pointers`
  - `table_pointers`
  - `results_pointers`
- optional excluded assertions:
  - `results_excluded_assertions`

### Methods / protocol block

- `methods_text`
- `methods_summary`
- `protocol_text`
- `protocol_summary`
- optional structured metadata used by `build-evaluation-extraction`:
  - `trial_registry_summary`
  - `trial_arms`
  - `trial_endpoints`
  - `trial_outcomes`
- optional pointers:
  - `methods_pointers`
  - `protocol_pointers`
- optional excluded assertions:
  - `methods_excluded_assertions`

### Review / revision block

- `review_response_text`
- `review_response`
- `revision_response_text`
- optional structured metadata used by `build-evaluation-extraction`:
  - `review_comments`
  - `review_concerns`
  - `decision_letters`
- optional pointers:
  - `review_response_pointers`
- optional excluded assertions:
  - `review_excluded_assertions`

### Resource description block

- `resource_text`
- `resource_description`
- `resource_summary`
- optional structured metadata used by `build-evaluation-extraction`:
  - `resource_identifiers`
  - `resource_inventory`
- optional pointers:
  - `resource_pointers`
- optional excluded assertions:
  - `resource_excluded_assertions`

## Formatting Expectations

- text fields should be plain strings
- structured metadata fields may also be JSON arrays or objects
- multi-sentence strings are allowed
- newline-separated bullets are allowed
- pointer lists should use `;`, `|`, or newline as delimiters
- excluded assertions should also be plain text strings; sentence splitting is applied automatically

## Current Heuristics

- statements are split from newline blocks and sentence boundaries
- bullet prefixes such as `-`, `*`, or `1.` are stripped
- each section is capped by `--max-assertions-per-unit`
- every generated unit includes a default section pointer such as `abstract_section` or `results_section`
- results units also include explicit figure/table pointers when provided

## Review Requirement

The generated extraction specs should be reviewed before:

1. `extract-evidence-records`
2. `build-truth-manifests`
3. `freeze-truth-manifests`
4. `build-evaluation-extraction`

This keeps parser assistance separate from final benchmark truth.
