# Source-Paper Qualification Rubric v4

This note freezes the planning spec that the current codebase implements.

## Core Principles

- qualification is two-axis and two-level
- benchmark truth is evidence-grounded rather than manuscript-grounded
- open peer review is audit evidence only
- split safety is enforced at the benchmark-unit level

## Paper-Level Qualification

- `ScientificQualification`: `A`, `B`, `C`, `Q`
- `PackagingQualification`: `P1`, `P2`, `P3`

Public gold requires:

- `Scientific = A`
- `Packaging = P1`
- published and peer reviewed source paper
- explicit `TruthManifest`
- at least one `UnitGoldEligible = yes`

## Unit-Level Qualification

Each benchmark release unit must:

- point to explicit `EvidenceUnit`s
- have local evidence support
- be internally coherent
- avoid excluded unsupported narrative
- be releasable under the packaging policy

## Scientific Domains

Critical domains:

- `integrity_status`
- `design_analysis_credibility`
- `minimal_interpretable_core`
- `required_traceability`
- `claim_mode_alignment`

Supporting domains:

- `reproducibility_support`
- `resource_specificity`

Audit evidence:

- `editorial_review_signal`
- `community_integrity_signal`
- `post_publication_discussion_signal`

## Classes and Overlays

Primary classes:

- `human_interventional`
- `human_observational`
- `systematic_review_meta_analysis`
- `animal_preclinical`
- `mechanistic_experimental`
- `methods_resource`

Overlays:

- `biomarker_prognostic`
- `omics_transcriptomics`
- `sequence_metagenomics`
- `proteomics_massspec`
- `structural_biophysics`
- `ecology_biodiversity`
- `qPCR`
- `enzymology`

## Year-Aware Standardization

- default public gold window: `2018-present`
- pre-2018 papers default to knowledge base or shadow use
- older papers can enter public gold only with an explicit exception review

## Packaging Policy

Allowed safe artifacts:

- published aggregate statistics
- figure/table observations already disclosed in the paper
- de-identified method summaries
- citation metadata
- accession metadata

Forbidden public packaging artifacts:

- row-level human data
- restricted supplements
- newly recomputed sensitive aggregates without explicit permission

## Workflow

1. intake, deduplication, and lineage assignment
2. integrity screening
3. class, overlay, and claim-mode assignment
4. dual human paper review
5. adjudication for `Q`, disagreements, and `A + P1`
6. packaging review
7. evidence-unit extraction
8. truth-manifest construction
9. split-safety validation
