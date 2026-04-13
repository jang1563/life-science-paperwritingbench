# Contamination and Private Holdout

Reviewed: 2026-04-09

## Goal

Set default contamination defenses for a public scientific benchmark.

## Sources

- LAB-Bench dataset card: https://huggingface.co/datasets/futurehouse/lab-bench
- LAB-Bench announcement: https://www.futurehouse.org/research-announcements/lab-bench-measuring-capabilities-of-language-models-for-biology-research
- Benchmarking Benchmark Leakage in LLMs: https://huggingface.co/papers/2404.18824
- DeepScholar-Bench overview: https://sky.cs.berkeley.edu/project/deepscholar-bench/

## Key Findings

- Public benchmarks are vulnerable to direct contamination, prompt-overfit, and retrieval-assisted memorization.
- Leakage is not only sample overlap. In science benchmarks it also occurs through shared consortium data, related papers, or repeated dataset families.
- A purely public benchmark makes it difficult to distinguish generalization from benchmark-specific adaptation.

## Adopted Defaults

- public/private release split defaults to `80/20`
- private split is retained for maintainers and future blind evaluation
- use a canary prefix `LS-PWB-CANARY` for sensitive release artifacts and pre-release slices
- enforce split safety at `BenchmarkUnit` level, not just paper level
- track:
  - `SourceFamily`
  - `ConsortiumLineage`
  - `DatasetLineage`
  - `LabLineage`
- apply both:
  - cross-split leakage checks
  - lineage-dominance caps

## Rejected Alternatives

- public-only release with no blind holdout
- split construction only at paper level
- contamination policy based only on exact paper duplication
