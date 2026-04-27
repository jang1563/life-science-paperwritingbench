# Pre-Human Validation Target Review

## Purpose

This document is the review gate before fixing the human-validation target for
`calibration/publication_validation_v1/`.

The goal is to avoid spending reviewer time on an underspecified or
irreversible round. The current recommendation is not to launch human review
yet. Instead, use this document as the first gate in a deeper pre-human-review
campaign.

## Current Local Status

Structural audit command run before this review:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-annotation-hold \
  --batch-dir calibration/publication_validation_v1 \
  --output /tmp/lspwb_hold_audit_pre_target.json \
  --markdown-output /tmp/lspwb_hold_audit_pre_target.md
```

Observed result on 2026-04-27:

- `ok=true`
- `structurally_ready=true`
- `awaiting_human_review=true`
- `total_judge_units=60`
- reviewer assignments: `reviewer_a=60`, `reviewer_b=60`
- `packet_coverage_complete=true`
- duplicate validation-unit, packet, and task-bundle ids: none
- finalized adjudications: `0`

This means the batch is structurally ready. It does not mean the review target
is semantically ready.

## External Benchmark Lessons

The human-validation target should be fixed only after checking it against
current benchmark practice.

| Reference | Relevant design choice | Lesson for this project |
| --- | --- | --- |
| PaperBench | Uses hierarchical rubrics for 8,316 gradable tasks, co-developed with paper authors, and separately evaluates the LLM judge. Source: <https://openai.com/index/paperbench/> | The scored object and grading rubric must be explicit. If this project wants model-output validation, the exact generated section text must be present in reviewer materials. |
| LAB-Bench | Releases biology research tasks across 8 categories, includes human comparison, notes that multiple-choice tasks may need manual open-answer validation, and withholds 20% as a private contamination set. Sources: <https://www.futurehouse.org/research-announcements/lab-bench-measuring-capabilities-of-language-models-for-biology-research>, <https://huggingface.co/datasets/futurehouse/lab-bench> | Public/private split, canaries, and human baselines are relevant. For evidence-grounded writing, manual validation is especially important because automatic or proxy scores can be gamed. |
| MedHELM | Uses a clinician-validated taxonomy, 37 evaluations, and multi-evaluator LLM jury against expert-defined criteria. Source: <https://www.nature.com/articles/s41591-025-04151-2> | Biomedical evaluation should name the clinical/scientific taxonomy, criterion source, and agreement between automated and expert judgments. LLM-judge scores alone are not enough. |
| HELM | Emphasizes taxonomy, multi-metric reporting, and standardized comparison rather than a single accuracy score. Source: <https://crfm.stanford.edu/2022/11/17/helm.html> | The final human-validation report should publish per-axis metrics, coverage, and limitations, not only one pass/fail number. |
| DeepScholar-Bench | Evaluates live research synthesis along knowledge synthesis, retrieval quality, and verifiability. Source: <https://huggingface.co/papers/2508.20033> | Verifiability should stay first-class. Evidence fidelity and provenance axes are appropriate for this project. |
| NLG human-evaluation best practices | Notes large variation in human evaluation practice and argues for explicit best-practice design. Source: <https://aclanthology.org/W19-8643/> | Calibration, instructions, target clarity, and agreement reporting should be frozen before reviewers see the full batch. |

## Candidate Human-Validation Targets

### Target A: Benchmark-Unit Evidence Validation

Reviewers judge whether each frozen benchmark unit is valid against its frozen
truth-manifest evidence.

Current readiness:

- structurally ready
- matches `docs/judge_validation_contract.md`
- supported by `truth_manifest_lookup.jsonl` and
  `selected_truth_manifests.jsonl`
- matches existing packet content, which exposes metadata, evidence pointers,
  authoring constraints, scoring profile, and rubric guidance

Weakness:

- reviewers are not scoring a concrete generated section
- wording such as "eventual section" can feel indirect
- this validates the benchmark/judge-validation slice, not model-output quality

Use this target if the claim is:

- "we created a human-adjudicated benchmark-unit validation slice"
- "the judge-validation units were reviewed against frozen evidence"
- "this supports later LLM-judge validation"

Do not use this target to claim:

- "model outputs are human validated"
- "the leaderboard is human validated"
- "a specific model's section-writing quality has human labels"

### Target B: Model-Output Section Validation

Reviewers judge generated Methods, Results, or Abstract text against evidence.

Current readiness:

- not ready in the current `publication_validation_v1` package

Blocking issue:

- current packet markdown does not expose the exact candidate section text to
  score
- launch readiness assessment already marks this as red if the organizer
  intends to score model outputs in this round

Required rebuild before using this target:

- choose the model/run/submission artifact
- freeze exact candidate text per validation unit
- embed or link the exact text inside reviewer packets
- hide model identity if blinding is intended
- adapt rubric wording from "eventual section" to "candidate section"
- add model-output-specific intake checks

Use this target if the claim is:

- "model-generated sections were human rated"
- "human labels calibrate or validate the LLM judge on generated outputs"

Do not use the current package for this target.

### Target C: Hybrid Two-Layer Validation

Reviewers first validate benchmark units, then a second round rates model
outputs on the validated units.

Current readiness:

- feasible as a staged program, not as one immediate launch

Recommended shape:

1. Round 1: Target A, benchmark-unit evidence validation.
2. Fix or drop units that fail human review.
3. Round 2: Target B, model-output section validation only on validated units.

This is the deepest and cleanest path, but it costs more time and reviewer
attention.

## Recommendation Before Target Freeze

Do not freeze the target until the next audit campaign completes.

Current best hypothesis:

- Target A is appropriate for the current `publication_validation_v1` package.
- Target B is not appropriate without rebuilding packets.
- Target C is the strongest publication path if time and reviewer bandwidth
  allow two rounds.

Decision rule:

- choose Target A if the immediate goal is to unlock human-adjudicated
  judge-validation units
- choose Target B only after a new model-output packet build exists
- choose Target C if the project wants the strongest eventual publication claim

## Open Questions To Resolve

1. Are reviewers expected to evaluate benchmark-unit integrity, generated text,
   or both?
2. Is the first human-validation claim meant to support judge-validation units,
   a model leaderboard, or both?
3. Should the first reviewer round be allowed to drop or quarantine units, or
   only score them?
4. Should notes tags be required, optional, or only requested for scores `0`
   and `1`?
5. What exact agreement metric is primary: per-axis weighted kappa, aggregate
   kappa, ordinal alpha, or ICC?

## Required Gate Before Human Dispatch

Human dispatch remains blocked until:

- target choice is written in `pre_human_review_preflight.md`
- target choice is repeated in reviewer launch messages
- calibration mini-round instructions match that target
- packet audit confirms reviewer-facing materials expose all required evidence
  for the chosen target
- agreement metric and "usable agreement" threshold are fixed before review
- P0 and P1 findings from `docs/pre_human_validation_audit_campaign.md` are
  closed
