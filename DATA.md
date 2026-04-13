# Data, Sources, and Licensing

This document describes where benchmark data originates and how it is licensed.
It covers both (a) inputs ingested at runtime by the pipeline and (b) release
bundles produced for downstream evaluation.

## What this repository does NOT ship

The `knowledge_base/` directory is **not** tracked in git. It is regenerated
by running the pipeline and can grow to hundreds of MB. This keeps the
repository code-focused and avoids redistributing upstream content under
terms we cannot unilaterally impose.

## Upstream sources

The collection and enrichment stages of the pipeline can query the following
public life-science services. Users running the pipeline are responsible for
complying with each service's terms of use and rate-limit guidance.

| Source | Role in pipeline | License / terms |
|---|---|---|
| NCBI PubMed / PubMed Central | seed search + abstracts + metadata | https://www.ncbi.nlm.nih.gov/home/about/policies/ |
| Europe PMC | full-text enrichment, XML parsing | https://europepmc.org/Copyright (varies per article; many OA items are CC-BY) |
| Crossref | metadata + DOI resolution | https://www.crossref.org/documentation/retrieve-metadata/rest-api/terms/ |
| bioRxiv / medRxiv | preprint discovery and metadata | https://www.biorxiv.org/about/FAQ (typically CC-BY or similar) |

Full-text articles retrieved from Europe PMC or PMC Open Access carry their
**own** article-level license. The pipeline tracks per-article license tags in
the evidence-enrichment records so that downstream release-bundle construction
can apply the correct redistribution rules.

## Release bundles

Release bundles produced by the `build-release-bundle` CLI are **not**
distributed through this repository. When they are published, each bundle
is accompanied by:

- a provenance manifest (`release_summary.json`) listing source DOIs, upstream
  licenses, split-safety reports, and checksums,
- a holdout-consistency report, and
- a `DATA_LICENSE` that inherits from the most restrictive upstream license in
  the bundle.

The default intent is **CC-BY-4.0** for the governance/annotation layer
authored in this repository (e.g., qualification decisions, truth manifests,
evaluation task bundles). Where a bundle re-packages article-derived content,
that content remains under its upstream license and is tagged accordingly.

The private / canary split is **not** intended for public distribution and is
governed by `docs/release_governance_card.md`. Canary strings and holdout
fingerprints are used to detect leakage into training corpora.

## Reuse guidance

- **Code (this repository):** Apache-2.0 — permissive, with explicit patent
  grant. Both commercial and non-commercial reuse are permitted.
- **Governance layer (annotations, manifests, task bundles produced by
  authors of this repository):** intended CC-BY-4.0 when published.
- **Upstream article content:** respect the per-article license recorded in
  the evidence records. Do not redistribute content whose upstream license
  forbids it.
- **Attribution:** when citing the benchmark, use the reference in
  `CITATION.cff`.

## Questions

For questions about redistribution of a specific artifact, open an issue at
https://github.com/jang1563/life-science-paperwritingbench/issues .
