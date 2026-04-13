# Judge Design and Validation

Reviewed: 2026-04-09

## Goal

Define when and how automated judges should enter the benchmark stack.

## Sources

- PaperBench: https://openai.com/index/paperbench/
- DeepScholar-Bench overview: https://sky.cs.berkeley.edu/project/deepscholar-bench/
- Datasheets for Datasets: https://www.microsoft.com/en-us/research/publication/datasheets-for-datasets/

## Key Findings

- Judge quality should be validated independently from benchmark construction.
- Scientific-writing evaluation needs structured rubrics and a human-adjudicated slice before LLM judges are trusted.
- Provenance and evidence fidelity are separable from stylistic quality and should not be hidden behind one scalar judge score.

## Adopted Decisions

- Do not implement an LLM judge as part of the current milestone.
- First build a human-adjudicated validation slice of at least 30 units.
- Judge development begins only after:
  - release-tier governance is stable
  - pilot calibration is complete
  - unit-level gold manifests are frozen
- Keep judge-rubric validation separate from qualification-rubric validation.

## Rejected Alternatives

- Using a single LLM judge before a human validation slice exists.
- Blending qualification and judge scoring into one pipeline.
- Treating style preference as equivalent to scientific fidelity.
