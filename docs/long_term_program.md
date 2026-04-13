# Long-Term Program

## Program Shape

The benchmark is intended to close in two linked releases:

- `v1-core`: knowledge base, qualification, extraction, calibration, release bundles, and lean baselines
- `v1.0 leaderboard`: judge validation slice, agentic baselines, and blinded private-holdout evaluation

## Implemented Long-Run Scaffolding

- `knowledge_base/` layout initialization
- local-file metadata ingestion and deduplicating normalization
- API-backed collection batch scaffolding for `collection_v1_2018_present`
- paper-level scientific and writing review scaffolding for the `180 qualification-ready` collection
- shadow-first auto-review scaffolding for the `180 qualification-ready` collection
- PMCID-backed full-text evidence enrichment and cached-subset auto-review reruns
- ingestion audit / verification reporting
- parser-assisted extraction drafts plus semi-structured extraction records and truth-manifest freeze/verify flow
- 60-paper full-calibration scaffold generation, validation, adjudication queues, and drift audits
- `TaskBundle` and `TruthManifestBundle` construction
- deterministic lean-baseline replay and submission scoring over `TaskBundle`
- judge-validation slice template construction, review workflow, and readiness auditing
- release-bundle verification reports
- local and Cayuga execution-profile scaffolding
- baseline, submission, evaluation, judge-validation, and maintenance-log record types
- program-progress summaries for gate tracking

## Remaining Milestones

1. Run the first real `300-candidate` collection batch and produce the `220 normalized / 180 shortlist` artifacts
2. Richer parser-assisted or model-assisted evidence extraction on top of the current metadata-driven draft flow
3. Expand the current cached-subset auto-review success (`21 shadow_candidate` papers from `70` enriched papers) toward the full `180-paper` qualification-ready set
4. Populate the 60-paper full calibration manifest with real curated papers
5. Populate released task bundles with curated corpus content and baseline configs
6. Populate the judge-validation slice with human-adjudicated units using the existing review/adjudication workflow
7. Agentic baseline replay and official leaderboard

## Execution Model

- standard-library Python only
- `file + CLI + periodic batch` workflow
- optional external HPC execution for large-scale replay, without moving the repo source of truth
- parallel human-reviewed and auto-reviewed lanes, with auto-only outputs capped below public release
