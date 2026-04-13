# AI for Science Benchmark Governance

Reviewed: 2026-04-09

## Goal

Define why this benchmark needs a stronger governance layer than a normal text-generation benchmark.

## Sources

- LAB-Bench announcement: https://www.futurehouse.org/research-announcements/lab-bench-measuring-capabilities-of-language-models-for-biology-research
- LAB-Bench dataset card: https://huggingface.co/datasets/futurehouse/lab-bench
- DeepScholar-Bench overview: https://sky.cs.berkeley.edu/project/deepscholar-bench/
- PaperBench: https://openai.com/index/paperbench/
- Datasheets for Datasets: https://www.microsoft.com/en-us/research/publication/datasheets-for-datasets/
- Benchmarking Benchmark Leakage in LLMs: https://huggingface.co/papers/2404.18824

## Key Findings

- Biology and research-synthesis benchmarks fail when paper quality, benchmark packaging, and final evaluation are conflated.
- LAB-Bench shows that scientific benchmarks benefit from tighter control over split construction and contamination defenses.
- DeepScholar-Bench highlights a separate issue: stale expert-curated test sets can drift away from the current literature environment, so evidence fidelity and provenance need to be evaluated independently from prose quality.
- PaperBench shows the value of decomposing complex evaluation into structured rubrics and validating judges separately from the task benchmark.
- Dataset-governance literature argues that benchmark documentation is not optional in high-stakes settings.

## Adopted Decisions

- Treat benchmark governance as a first-class subsystem.
- Separate:
  - paper qualification
  - unit release qualification
  - final evaluation
- Use explicit release tiers:
  - `public_gold`
  - `shadow_gold`
  - `stress_only`
- Require release documentation artifacts alongside the benchmark itself.

## Rejected Alternatives

- A single `public_gold_eligible` boolean at paper level.
- A benchmark that evaluates writing quality without explicit evidence/provenance structure.
- A public-only evaluation set without a private holdout.
