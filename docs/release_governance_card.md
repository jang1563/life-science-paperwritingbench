# Release Governance Card

## Release Tiers

- `public_gold`
- `shadow_gold`
- `stress_only`
- `excluded`

## Public Release Requirements

- `PaperScientific = A`
- `PaperPackaging = P1`
- `candidate_tier = public_gold_candidate`
- frozen `TruthManifest`
- releasable evidence-backed `EvidenceUnit`
- deterministic public/private holdout assignment
- per-unit canary string for contamination monitoring

## Shadow Release Requirements

- paper is a `shadow_candidate`
- frozen `TruthManifest`
- releasable unit

## Stress Release Requirements

- paper is a `stress_candidate`
- frozen `TruthManifest`
- releasable unit

## Integrity Policy

- `Q` cases never enter any release tier
- partial retractions that invalidate core claims are excluded
- integrity overrides always take precedence over score-like domain outcomes

## Current Operational Support

- JSONL serialization helpers for governance artifacts
- deterministic release-index construction
- release-bundle construction with split-safety checks
- release-bundle provenance manifest with input fingerprints and policy digests
- artifact-level SHA-256 checksums for release packaging verification
- bundle verification reports for post-build integrity checks
- ingestion audit and ingestion verification reports before qualification/release
- truth-manifest freeze and truth-manifest verification before task bundling
- pilot calibration scaffold for 12 papers before larger-scale curation
- full-calibration scaffold, adjudication queue, and calibration drift audit before v1-core release
- release artifacts separate `benchmark_split` from `holdout_bucket`
