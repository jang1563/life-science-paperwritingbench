# Benchmark Transparency Card

## Evaluation Philosophy

- separate paper qualification from unit release
- separate public release from shadow and stress evaluation
- separate scientific quality from packaging quality
- separate benchmark governance from model scoring

## Leakage Controls

- lineage-based split safety
- lineage-dominance cap
- public/private holdout split
- canary string policy for sensitive evaluation artifacts

## Known Current Limitations

- no network-backed ingestion connector yet
- no populated judge validation slice yet; current repo provides template construction and readiness auditing only
- no reviewer-facing calibration UI yet; current calibration ops are file + CLI based
- no scheduler launcher yet for large-scale replay
- no full-text PDF parser yet; current extraction is metadata-driven parser-assisted drafting plus semi-structured reviewed specs

## Planned Transparency Artifacts

- release manifest
- provenance manifest
- bundle verification report
- calibration summary and calibration drift report
- contamination policy
- benchmark maintenance log
