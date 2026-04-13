# Dataset Card

## Purpose

This benchmark is designed to evaluate evidence-grounded scientific writing workflows for life-science papers.

It is not intended to reward stylistic imitation of published prose. It is intended to evaluate:

- evidence fidelity
- scientific traceability
- provenance completeness
- governance-safe benchmark construction

## Unit of Release

The public benchmark releases `BenchmarkUnit` objects backed by:

- one qualified `SourcePaper`
- one or more qualified `EvidenceUnit`s
- one frozen `TruthManifest`
- one derived `TaskBundle`

## Exclusions

- retracted, withdrawn, or removed papers
- quarantined integrity cases
- units that depend on excluded unsupported narrative
- units without frozen manifest support
- release artifacts that violate packaging policy

## Default Release Policy

- public holdout: `80%`
- private holdout: `20%`
- preprints: shadow-only
- open peer review: audit signal only
