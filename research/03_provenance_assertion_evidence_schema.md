# Provenance, Assertions, and Evidence Schema

Reviewed: 2026-04-09

## Goal

Explain why the benchmark should model truth as assertion/evidence/provenance objects instead of using manuscript text as direct ground truth.

## Sources

- PROV overview: https://www.w3.org/TR/prov-overview/
- Evidence Ontology (ECO): https://pmc.ncbi.nlm.nih.gov/articles/PMC4105709/
- Assertion/evidence/provenance ontology survey: https://pubmed.ncbi.nlm.nih.gov/40855889/

## Key Findings

- Scientific assertions are stronger when linked to explicit evidence and provenance records.
- Provenance modeling helps separate what was observed, who curated it, and how a benchmark artifact was derived.
- ECO-style evidence typing is especially useful in biology because the same claim may be supported by different evidence classes such as experiment, computational analysis, or curator inference.

## Adopted Decisions

- `TruthManifest` is evidence/provenance oriented.
- Required fields include:
  - `assertion_ids`
  - `assertion_texts`
  - `evidence_items`
  - `evidence_types`
  - `excluded_assertions`
  - `provenance_entities`
  - `provenance_activities`
  - `provenance_agents`
  - `applied_standards`
  - `frozen_at`
- Manuscript prose is treated as a carrier, not as direct benchmark truth.

## Rejected Alternatives

- Using the final paper text as the only gold target.
- Keeping provenance only in free-text notes.
- Treating evidence and provenance as optional metadata.
