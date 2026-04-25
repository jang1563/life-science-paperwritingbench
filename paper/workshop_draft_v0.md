# Life-Science PaperWritingBench: A Governance-First Benchmark for Evidence-Grounded Biomedical Section Writing

## Status

This document is a working manuscript draft for the repo's `v0.1 research
preview`. It is intentionally honest about what is already implemented, what
has early empirical support, and what is deliberately held or incomplete.
Human reviewer execution is currently on hold, so the draft should be read as
a preview-freeze artifact rather than a claim of human-validated benchmark
readiness.

## Draft Abstract

Large language models can now produce fluent scientific prose, but evaluating
whether that prose remains faithful to biomedical source evidence is still
difficult. We present Life-Science PaperWritingBench, a governance-first
benchmark framework for evidence-grounded biomedical section writing. The
framework separates paper qualification, evidence-unit extraction,
truth-manifest freezing, release-tier assignment, contamination controls, and
model evaluation rather than collapsing them into one task-release decision.
The current `v0.1` research preview focuses on three writing families:
`methods_to_text`, `results_to_text`, and `abstract_from_evidence`. It combines
deterministic scoring with a rubric-based LLM judge and includes both
single-pass and agentic `writer -> critic -> reviser` baselines. Early results
show that a conservative non-regressive selector improves judged quality for
the strongest agentic baseline while preserving deterministic citation
behavior. A partial hosted model matrix shows separation across DeepSeek,
OpenAI, and Anthropic submitters, and a hosted-working-set canary probe reports
no exact public/control canary reproduction among completed models. The repo
also includes an Inspect-compatible adapter, artifact-backed replay helpers,
and a frozen `60`-bundle human-validation batch with reviewer packets and
adjudication shells. Reviewer execution is currently held, so agreement
statistics are not reported. We therefore release this as a research preview,
not a final leaderboard or human-validated benchmark, and make the remaining
validation and provider-coverage gaps explicit.

## 1. Introduction

Progress in LLM scientific writing is now easy to overstate because strong
surface fluency can hide weak evidence use. A model may produce a polished
abstract, methods section, or results summary while silently introducing
unsupported claims, invented numerical values, or misplaced procedural detail.
For biomedical writing, these failures are especially important: the burden is
not only to write well, but to write in a way that remains tied to the actual
study evidence.

Recent benchmark design in science and writing has clarified several useful
patterns without yet solving this exact problem. LAB-Bench showed the value of
contamination-aware split design in biology [1]. PaperBench showed the value
of decomposed rubrics and separate judge validation [2]. DeepScholar-Bench
highlighted the difficulty of long-form research synthesis [3]. MedHELM showed
that human-agreement reporting is essential in medically meaningful evaluation
[4]. WritingBench demonstrated how far general writing evaluation can be pushed
without becoming domain-specific [5]. Life-Science PaperWritingBench draws from
all of these, but focuses on a different task: evidence-grounded biomedical
section writing from curated paper evidence bundles.

Life-Science PaperWritingBench is built around that distinction. The project
does not treat "paper writing" as a generic long-form generation task. Instead,
it treats benchmark construction as a layered governance problem followed by an
evaluation problem. Before a model ever writes a section, the source paper has
to be screened for scientific and integrity risks, evidence units have to be
curated, a truth manifest has to be frozen, and the resulting benchmark units
have to be assigned to safe release tiers with contamination-aware split
controls. Only then do writing tasks become eligible for model evaluation.

The benchmark's current writing target is deliberately narrow. The preview
release focuses on three section families that are both scientifically central
and realistically evaluable from paper evidence bundles:

- `methods_to_text`
- `results_to_text`
- `abstract_from_evidence`

This keeps the benchmark aligned with the kinds of writing errors we can
meaningfully score today, while deferring broader tasks like discussion,
related work, or figure-caption generation until the current release path is
stronger.

### Figure 1. Current benchmark pipeline

```text
Source papers
    |
    v
Paper qualification
  scientific / writing / packaging / integrity
    |
    v
Evidence extraction + truth-manifest freeze
    |
    v
Benchmark units + release-tier assignment
  public_gold / shadow_gold / stress_only
    |
    +------------------------------+
    |                              |
    v                              v
Split safety + canary policy   TaskBundle construction
    |                              |
    +---------------+--------------+
                    |
                    v
          Model generation lane
      single-pass or writer->critic->reviser
                    |
                    v
           Deterministic scoring v2
                    |
                    v
            Rubric-based judge v3
                    |
                    v
      Matrix summaries + canary probes + audits
```

## 2. Positioning Relative to Prior Benchmarks

The benchmark sits between several adjacent traditions in scientific and
writing evaluation, but does not match any of them directly.

| Benchmark | Main task | What we borrow | What remains distinct here |
| --- | --- | --- | --- |
| LAB-Bench [1] | Biology research tasks and scientific QA | public/private split discipline, canary policy, contamination posture | our target is evidence-grounded paper-section writing, not research QA |
| PaperBench [2] | AI-paper replication with rubric decomposition | rubric design, judge-audit mindset | our outputs are biomedical sections rather than executable replications |
| DeepScholar-Bench [3] | related-work generation from live literature | closest task spirit, synthesis framing | our benchmark is evidence-bounded and section-specific rather than open-web related-work synthesis |
| MedHELM [4] | medically grounded evaluation with human calibration | publication bar for human-agreement reporting | our current preview does not yet meet that validation bar |
| WritingBench [5] | broad generative writing evaluation | writing-evaluation reference point | not biomedical, not evidence-conditioned |

The core claim of this repo is therefore not "we built a general writing
benchmark." It is closer to: we are building a governance-first benchmark for
biomedical section writing where contamination control, release safety, and
evidence fidelity are first-class design constraints.

## 3. Governance-First Benchmark Design

The repository's strongest differentiator is that benchmark governance is not
treated as preprocessing. It is the benchmark.

### 3.1 Paper qualification

Each source paper is assessed across scientific quality, writing quality,
packaging quality, and integrity disposition. Retracted, withdrawn, removed, or
otherwise terminal integrity cases are excluded. Expressions of concern and
some partial retractions are quarantined rather than silently mixed into normal
evaluation pools. This matters because a writing benchmark is only as credible
as its source corpus.

### 3.2 Evidence extraction and truth freezing

Eligible papers are converted into evidence units and then into frozen truth
manifests. This prevents downstream task definitions from drifting every time
the codebase changes. A benchmark unit is only releaseable once its supporting
truth artifact is frozen.

### 3.3 Release-tier assignment and split safety

The project distinguishes between `public_gold`, `shadow_gold`,
`stress_only`, and excluded artifacts. Public release is intentionally stricter
than internal shadow evaluation. The repo also maintains deterministic
public/private holdout assignment and split-safety validation so closely
related artifacts do not leak across boundaries.

### 3.4 Canary-based contamination monitoring

Every release index entry carries a deterministic canary string. These canaries
are not cosmetic. They exist so the benchmark can later probe for memorization
or training contamination without exposing the full secret strings in the
public repo.

## 4. Task Families

The current preview includes three writing families:

### 4.1 `methods_to_text`

Generate a Methods section from curated evidence, preserving procedural detail,
study design, assays, cohort description, and grounded references to figures,
tables, or accessions when supported.

### 4.2 `results_to_text`

Generate a Results section that keeps observed outcomes, quantitative claims,
and evidence anchors intact without inventing statistical detail.

### 4.3 `abstract_from_evidence`

Generate a compact Abstract from the supplied evidence bundle. This family is
the hardest to calibrate because good abstracts need quantitative specificity,
but conventional traceability rules can easily push the output toward awkward
or unscientific "process language."

This family split is intentionally modest. Discussion, related work, and
figure-caption generation remain out of scope for the preview release because
the current repo is still converging on a defensible evaluation stack for the
three core families above.

## 5. Evaluation Methodology

### 5.1 Deterministic scoring

The deterministic layer provides a first-pass floor for structure and
specificity. The current repo uses a `v2` scoring layer rather than the older
placeholder-token setup. This layer is intentionally simpler than the full
judge: it checks whether the output looks like the requested section and
whether it contains grounded specificity signals such as figure/table anchors,
numeric detail, or accessions where appropriate.

That simplicity is useful, but it is not sufficient. One of the repo's major
lessons to date is that a deterministic layer can be gameable if its proxy
signals are too easy to satisfy stylistically.

### 5.2 Rubric-based LLM judging

The current judge configuration is rubric `v3`, which uses:

- a 4-point anchored ordinal scale (`0`-`3`)
- a mean-axis pass rule, `mean(axis_scores) >= 2.0`
- a family-aware abstract rubric in which
  `quantitative_specificity` replaces `traceability`

This was an important correction. Earlier judging behavior showed that
abstracts were being penalized by criteria that made more sense for Methods and
Results. The family-aware swap improved that mismatch and made abstract
evaluation more realistic.

### 5.3 Agentic baseline

The strongest current submission baseline is a ScholarPeer-inspired
`writer -> critic -> reviser` lane with a conservative selector. The reviser is
allowed to propose an improvement, but the final system keeps the draft when a
revision would regress deterministic pass or citation specificity. In practice,
this turned out to be more reliable than trusting the reviser unconditionally.

### 5.4 Cross-model matrix summaries

The repo now includes a reusable matrix-summary lane that aggregates submitter
and judge artifacts into a single partial leaderboard-style report while
explicitly marking blocked or missing cells. This is important because the
current release story is not "everything is complete"; it is "the benchmark is
already showing separation signals even though the full matrix is not done."

### 5.5 Canary probe

The current contamination check is a completion-style probe rather than a
log-probability audit. A model is prompted with a partially revealed canary and
asked to complete the exact string. The probe also uses unpublished matched
control canaries. Artifacts record hashes, lengths, match outcomes, and edit
distances, but not raw canary strings or raw model outputs.

## 6. Current Preview Results

### 6.1 Best deterministic / citation anchor

The cleanest deterministic artifact at the moment is:

- `calibration/llm_agentic_public_slice_v1_rerun2/summary.md`

Key results:

| Metric | Value |
| --- | ---: |
| tasks | `30` |
| draft deterministic pass | `24 / 30` |
| final deterministic pass | `26 / 30` |
| draft mean citation specificity | `0.778` |
| final mean citation specificity | `0.878` |
| critique parse failures | `0` |

This artifact remains the strongest citation-specificity reference point for
the current DeepSeek agentic lane.

### 6.2 Best judged artifact

The strongest judged artifact at the moment is:

- `calibration/llm_agentic_public_slice_v1_rerun5_judged_v3/summary.md`

Key results under Claude Sonnet 4.6:

| Metric | Value |
| --- | ---: |
| threshold-rule pass | `30 / 30` |
| judge-reported overall pass | `30 / 30` |
| strict all-axes >= threshold | `27 / 30` |
| mean axis score | `2.653` |
| grounding issues | `60` |
| parse failures | `0` |

The important caveat is that this gain came from the selected-output policy,
not from a uniformly strong reviser. The selector is part of the result.

### 6.3 Cross-model signal

The current partial matrix summary is:

- `calibration/llm_public_slice_matrix_v1/summary.md`

Current completed coverage:

- submitters: `deepseek-chat-agentic-rerun5`, `gpt-4o-mini-agentic-v1`,
  `claude-haiku-4-5-agentic-v1`
- judges: `claude-sonnet-4-6`, `gpt-5.4-mini`, `gpt-5-mini`
- completed cells: `5 / 9`
- family-bias exclusions: `3 / 9`
- missing diagnostic cells: `1 / 9`

Current official-jury comparison:

| Submitter | Deterministic pass | Citation specificity | Mean official judge pass | Completed official judges |
| --- | ---: | ---: | ---: | ---: |
| `deepseek-chat-agentic-rerun5` | `26 / 30` (`86.7%`) | `0.844` | `91.7%` | `2` |
| `gpt-4o-mini-agentic-v1` | `22 / 30` (`73.3%`) | `0.756` | `76.7%` | `1` |
| `claude-haiku-4-5-agentic-v1` | `25 / 30` (`83.3%`) | `0.822` | `63.3%` | `1` |

No official judge currently covers all compared submitters, so the current
common-judge spread is `n/a`. Same-judge comparisons still show separation
within the completed cells.

The strongest same-judge separation so far comes from `claude-sonnet-4-6`:

- DeepSeek agentic rerun5: `30 / 30`
- `gpt-4o-mini` agentic v1: `23 / 30`
- spread: `23.3` percentage points

The matrix is still incomplete, however. The release-facing hosted matrix still
needs Gemini submitter coverage (`gemini-2.5-flash`) and Gemini official judge
coverage (`gemini-2.5-pro`) before readiness gates can pass.

### 6.4 Canary mini-probe

The current live contamination mini-probe is:

- `calibration/canary_probe_v1_live_hosted_working_set/summary.md`

Coverage:

- `deepseek-chat`
- `gpt-4o-mini`
- `gpt-5.4-mini`
- `claude-haiku-4-5`
- `claude-sonnet-4-6`

Current result:

| Model | Public exact matches | Control exact matches | Min public distance | Min control distance |
| --- | ---: | ---: | ---: | ---: |
| `deepseek-chat` | `0 / 1` | `0 / 1` | `8` | `8` |
| `gpt-4o-mini` | `0 / 1` | `0 / 1` | `18` | `15` |
| `gpt-5.4-mini` | `0 / 1` | `0 / 1` | `8` | `8` |
| `claude-haiku-4-5` | `0 / 1` | `0 / 1` | `8` | `8` |
| `claude-sonnet-4-6` | `0 / 1` | `0 / 1` | `8` | `8` |

This is encouraging, but it remains only a partial contamination check because
Gemini coverage is still missing from the current hosted-working-set artifact.

### 6.5 Publication-validation batch and readiness gate

The repo now also contains a first frozen publication-validation batch:

- `calibration/publication_validation_v1/`

Key batch facts:

| Metric | Value |
| --- | ---: |
| selected bundles | `60` |
| task-family coverage | `20` each across `methods_to_text`, `results_to_text`, and `abstract_from_evidence` |
| study-class stratification ready | `true` |
| structurally ready | `true` |
| packet coverage complete | `true` |
| reviewer assignments complete | `true` |
| awaiting reviews | `60` |
| finalized adjudications | `0` |

This matters because the repo is no longer missing a validation workflow in
the abstract. It now has a selection-locked batch, reviewer packets, blank
review forms, blank adjudication shells, and a structural hold audit showing
that the batch is ready for humans. What is still missing is the human review
execution itself, which is currently held. The current publication-readiness
snapshot remains red because agreement metrics are still absent and the
frontier matrix / canary coverage are still incomplete.

## 7. What These Results Mean

The preview results support three cautious conclusions.

First, the benchmark is already hard enough to separate submitters. Even with a
partial matrix, the repo is not showing a collapsed or saturated picture across
models.

Second, benchmark quality is currently better reflected by the combined view of
deterministic checks, judged quality, and grounding-issue reporting than by any
single pass/fail metric alone. The repo's strongest current result is not "the
judge passed everything"; it is that a particular baseline improved judged
quality while maintaining a usable deterministic traceability profile.

Third, governance and contamination work are not just peripheral additions.
They materially affect how believable the benchmark is. The release-tier logic,
split safety, canary design, and integrity filters are part of the benchmark's
claim to rigor, not implementation details.

## 8. Limitations

The current preview has several important limitations that should be stated
plainly.

- The repo now has a frozen `60`-bundle publication-validation batch, but it
  still does not report `kappa`, `ICC`, or `alpha` because human reviewer
  execution is currently held and no completed reviews have been merged yet.
- The cross-model matrix is incomplete.
- Anthropic coverage is present in the current matrix and canary artifacts, but
  Gemini submitter/judge coverage is still missing from the release-facing
  gates.
- The current canary report is a partial mini-probe, not a full frontier-model
  contamination release.
- The project is still effectively in a solo-author preview stage.

For these reasons, the current repo state should be described as a
`v0.1 research preview` rather than a finished leaderboard benchmark.

## 9. Conclusion

Life-Science PaperWritingBench is promising not because it already has a final
leaderboard, but because it combines benchmark governance, evidence-grounded
writing tasks, rubric-based judging, contamination monitoring, and explicit
release gating in a single workflow. The current preview suggests that
biomedical section-writing systems can already be meaningfully separated, and
that agentic revision can help when paired with a conservative selector.
However, the project is not yet at the point where judged scores alone should
be treated as publication-grade benchmark evidence. While human validation is
held, the immediate milestone is a clean `v0.1 research preview` freeze:
reproducible artifacts, precise claim language, clearer replay instructions,
and explicit separation between hosted-frontier and future open-weight tracks.

## References

[1] LAB-Bench: Measuring Capabilities of Language Models for Biology Research.
FutureHouse / arXiv 2407.10362.
https://arxiv.org/abs/2407.10362

[2] PaperBench: Evaluating AI's Ability to Replicate AI Research.
OpenAI, 2025.
https://openai.com/index/paperbench/

[3] DeepScholar-Bench: A Live Benchmark and Automated Evaluation for
Generative Research Synthesis.
UC Berkeley Sky Computing Lab / arXiv 2508.20033.
https://sky.cs.berkeley.edu/project/deepscholar-bench/

[4] Holistic evaluation of large language models for medical tasks with
MedHELM.
Nature Medicine, 2025.
https://www.nature.com/articles/s41591-025-04151-2

[5] WritingBench: A Comprehensive Benchmark for Generative Writing.
arXiv 2503.05244.
https://arxiv.org/abs/2503.05244

## Appendix: Current Artifact Anchors

- Best judged agentic artifact:
  `calibration/llm_agentic_public_slice_v1_rerun5_judged_v3/summary.md`
- Best deterministic / citation artifact:
  `calibration/llm_agentic_public_slice_v1_rerun2/summary.md`
- Current partial matrix:
  `calibration/llm_public_slice_matrix_v1/summary.md`
- Current canary probe report:
  `docs/canary_probe_report.md`
- Current publication-validation batch:
  `calibration/publication_validation_v1/README.md`
- Current publication-validation summary:
  `calibration/publication_validation_v1/publication_validation_summary.json`
- Current publication-readiness snapshot:
  `calibration/publication_validation_v1/publication_readiness_snapshot.json`

## Appendix: Held Human-Validation Path

The human-validation gap is operational more than architectural, but this work
is currently held.

1. Distribute the frozen reviewer packets under
   `calibration/publication_validation_v1/review_packets/`.
2. Merge completed reviewer forms into a single
   `judge_review_forms_merged.jsonl` artifact.
3. Build the adjudication queue and finalize
   `judge_adjudications.jsonl` for the disputed units.
4. Recompute `judge_agreement.json` and refresh
   `publication_readiness_snapshot.json`.

In other words, the repo now has the batch-selection, packet-generation,
and structural-QA pieces in place; the remaining work is to execute the
human review loop and then rerun the readiness gate with real agreement
numbers.

Until that happens, use `docs/research_preview_freeze_checklist.md` as the
active non-human preview-freeze plan.

## Open Writing Tasks

- align the final paper format with the target workshop venue
- convert this markdown draft into the preferred workshop paper format
- replace the ASCII pipeline figure with a camera-ready figure if needed
