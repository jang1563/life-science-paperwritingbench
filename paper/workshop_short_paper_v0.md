# Life-Science PaperWritingBench: A Governance-First Benchmark for Evidence-Grounded Biomedical Section Writing

## Status

This is a venue-neutral short-paper draft for adapting the `v0.1 research
preview` into a workshop or short-track submission. It is intentionally bounded:
human reviewer execution is on hold, Gemini coverage is incomplete, and the
project must not be described as a final leaderboard or human-validated
benchmark.

The longer narrative draft lives in `paper/workshop_draft_v0.md`. The current
figure source is `paper/figures/governance_pipeline.svg`.

## Abstract

Large language models can now produce fluent scientific prose, but fluency does
not guarantee that biomedical claims remain faithful to source evidence. We
present Life-Science PaperWritingBench, a governance-first benchmark framework
for evidence-grounded biomedical section writing. The benchmark separates paper
qualification, evidence-unit extraction, truth-manifest freezing, release-tier
assignment, contamination controls, and model evaluation before any generated
section is scored. The current `v0.1` research preview focuses on three writing
families: `methods_to_text`, `results_to_text`, and
`abstract_from_evidence`. It combines deterministic scoring with a rubric-based
LLM judge and includes single-pass and agentic `writer -> critic -> reviser`
baselines. Early preview artifacts show that a conservative agentic selection
policy improves deterministic citation specificity on a public slice and that
partial hosted-frontier matrix results separate DeepSeek, OpenAI, and Anthropic
submitters under available official judges. A redacted hosted-working-set
canary probe found no exact public/control canary reproduction among completed
models. However, human reviewer execution is held, Gemini coverage is missing,
and agreement statistics are not available. We therefore release the current
state as a research preview and make the remaining validation gates explicit.

## 1. Motivation

Scientific writing benchmarks often reward outputs that look plausible before
they test whether the output is grounded in the supplied evidence. This is a
serious failure mode for biomedical section writing. A generated abstract,
methods section, or results section can be polished while inventing numerical
values, misplacing a figure reference, or converting an unsupported inference
into a factual claim. The benchmark problem is therefore not only generation
quality, but controlled evidence use.

Life-Science PaperWritingBench treats that problem as a governance problem
before a modeling problem. Source papers must be qualified, evidence must be
converted into auditable units, truth manifests must be frozen, release tiers
must be assigned, and contamination controls must exist before model outputs are
scored. This structure is designed to prevent a common benchmark failure: a
leaderboard that is easy to run but hard to trust.

The preview release is deliberately narrow. It focuses on three biomedical
section-writing families where evidence-bounded scoring is realistic today:

- `methods_to_text`: write Methods prose from curated procedural evidence.
- `results_to_text`: write Results prose from observed outcomes and anchors.
- `abstract_from_evidence`: write a compact abstract from supplied evidence.

Discussion, related-work synthesis, and figure-caption generation remain out of
scope for this preview because they require stronger validation than the current
release has.

## 2. Benchmark Design

Figure 1 summarizes the current pipeline. Source papers first pass through
paper qualification, which screens scientific quality, writing quality,
packaging quality, and integrity disposition. Eligible sources are converted to
evidence units and frozen truth manifests. Benchmark units are then assigned to
release tiers such as `public_gold`, `shadow_gold`, and `stress_only`, with
split-safety checks and canary strings attached to release-index entries.

This governance stack is intentionally separate from model evaluation. Only
after a benchmark unit is frozen and release-tiered does it enter a generation
lane. The current generation lane supports single-pass baselines and an agentic
`writer -> critic -> reviser` baseline. Outputs then pass through deterministic
scoring, rubric-based LLM judging, matrix aggregation, canary probes, and
publication-readiness audits.

**Figure 1:** Governance-first benchmark pipeline. Current source:
`paper/figures/governance_pipeline.svg`; caption draft:
`paper/figures/governance_pipeline_caption.md`.

## 3. Evaluation Stack

The preview uses a layered evaluation stack.

First, deterministic scoring `v2` provides a reproducible floor for section
shape and evidence specificity. It checks whether the output resembles the
requested section and whether it contains grounded specificity signals such as
figure/table anchors, numeric detail, or accessions where appropriate. This
layer is useful for fast regression checks, but it is not intended to be a full
semantic judge.

Second, rubric judge `v3` evaluates generated sections across writing
structure, evidence grounding, factual fidelity, traceability, quantitative
specificity, and hallucination absence. The judge is used as an early
development signal, not as a substitute for human agreement.

Third, matrix evaluation separates submitters and judges so that same-provider
family bias can be excluded. The current matrix records submitter provenance,
judge provenance, judge policy, completed cells, excluded cells, and missing
cells.

Fourth, canary probes test whether hosted models exactly reproduce redacted
benchmark canaries or matched controls. The repo stores hashes, lengths, match
outcomes, and edit distances, not raw canary strings or raw model outputs.

Finally, publication-readiness audits keep the release claim boundary explicit.
The current readiness state is intentionally red because human agreement,
Gemini coverage, registry-complete contamination checks, and comparable
open-weight artifacts remain pending.

## 4. Preview Results

The current artifacts support a research-preview claim, not a final benchmark
claim.

| Evidence source | Preview observation | Claim boundary |
| --- | --- | --- |
| Deterministic agentic anchor: `calibration/llm_agentic_public_slice_v1_rerun2/summary.md` | On 30 public-slice tasks, the agentic final output improved deterministic pass count from 24/30 to 26/30 and mean citation specificity from 0.778 to 0.878. | Deterministic scores are regression signals, not human validation. |
| Judged agentic anchor: `calibration/llm_agentic_public_slice_v1_rerun5_judged_v3/summary.md` | Rubric judge `v3` marked 30/30 submissions above the mean-axis threshold, with mean axis score 2.653 and 60 reported grounding issues. | LLM judge results cannot substitute for human agreement. |
| Hosted matrix: `calibration/llm_public_slice_matrix_v1/summary.md` | The matrix has 3 submitter runs, 3 declared judges, 5/9 completed cells, and 4/6 official cells completed. Same-judge official spread is 23.3 percentage points under `claude-sonnet-4-6` and 20.0 points under `gpt-5.4-mini`. | Matrix coverage is partial; Gemini submitter, judge, and canary coverage are missing. |
| Canary probe: `docs/canary_probe_report.md` | The hosted-working-set probe covers 5 models and observed 0/5 exact public-canary matches and 0/5 exact control-canary matches. | This is not registry-complete contamination clearance. |
| Publication-validation batch: `calibration/publication_validation_v1/` | A 60-bundle human-validation batch is selected, packet-complete, and structurally ready, with 0 finalized adjudications. | Human reviewer execution is held; `kappa`, `ICC`, and `alpha` are absent. |

These results are encouraging because they show that the repository now has an
inspectable benchmark stack: task construction, deterministic scoring,
LLM-judge scoring, matrix aggregation, canary probing, replay documentation,
and publication-readiness auditing all point to concrete artifacts. The same
results also explain why the release should stay in preview language. The most
important missing evidence is not another automated score; it is human
agreement on the judgment rubric, plus completion of the hosted provider matrix
and contamination probe.

## 5. Limitations

The current preview has five release-blocking limitations.

First, human validation has not been executed. The batch is ready for review,
but there are no completed reviewer labels, adjudications, or agreement
statistics.

Second, the hosted matrix is incomplete. Current artifacts include DeepSeek,
OpenAI, and Anthropic coverage, but Gemini coverage remains missing from the
release-facing matrix and canary probe.

Third, the LLM judge is a useful development instrument but not a publication
grade validator by itself. The judge can identify grounding issues, but its
agreement with domain reviewers remains unmeasured.

Fourth, canary probes are partial. No exact reproduction was observed in the
completed hosted-working-set probe, but registry-complete contamination
clearance has not been established.

Fifth, open-weight and VLLM runs are intentionally separated from the hosted
frontier track. Open-weight artifacts may be valuable, but they must not fill
missing hosted-frontier matrix cells.

## 6. Next Steps

The next non-human step is to adapt this draft to a target venue while
preserving the research-preview boundary. That adaptation should choose the
venue-specific format, compress the background, convert Figure 1 into the
preferred figure style, and keep the limitations section explicit.

When credentials and compute are available, the benchmark work should then
complete Gemini submitter/judge/canary coverage and scaffold the separate
open-weight/VLLM track. When human validation resumes, the calibration starter
set should be audited before the full review round proceeds.

## References

[1] LAB-Bench. Biology research task benchmark with contamination-aware split
design.

[2] PaperBench. AI-paper replication benchmark with decomposed rubric design
and judge validation.

[3] DeepScholar-Bench. Long-form research synthesis and related-work
generation benchmark.

[4] MedHELM. Medically grounded evaluation framework emphasizing human
agreement and calibration.

[5] WritingBench. Broad generative writing evaluation benchmark.
