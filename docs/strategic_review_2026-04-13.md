# Strategic Review & Direction-Setting Plan

**Project:** Life-Science PaperWritingBench
**Prepared:** 2026-04-13
**Status:** Final (review-hardened) — awaiting user approval

> This document doubles as the research deliverable. **Execution step 1 below is to copy it to `docs/strategic_review_2026-04-13.md`** so it stays with the project.

---

## Context

**Why this review:** Phase-1 governance is complete (180 papers, 518 bundles, NCBI fallback, taxonomy). Phase-2 has produced one end-to-end LLM + judge pass (DeepSeek V3 + Claude Sonnet 4.6). The v1→v2 prompt iteration exposed that the deterministic layer was gameable and the judge discriminates (7→15/30 pass). Before further investment, the user asked for an honest landscape check — specifically, "Can I do this without human validation?" with the follow-up "maybe I can find someone in the lab or our institute."

**Intended outcome:** a prioritized direction for the next 1–4 sessions, grounded in comparable-benchmark patterns, with explicit stop/go gates.

---

## Phase 1 — Internal audit

| Layer | Status | Notes |
|---|---|---|
| Governance core (qualification, release tiers, lineage) | ✅ Complete | 180 papers, 518 bundles (430 public / 88 private), 0 split-safety violations, `v1_core_gate_passed = true` |
| Contamination defenses (public/private holdout + canary) | ✅ Complete | 80/20 split, canary prefix `LS-PWB-CANARY` — matches LAB-Bench practice |
| TruthManifest schema (frozen) | ✅ Complete | |
| Evidence acquisition (EuropePMC + NCBI PMC efetch fallback) | ✅ Complete | 3 non-OA papers recovered; resource-URL regex added |
| Taxonomy refinement | ✅ Complete | v11 slice: all acquisition-gap categories at 0 |
| Deterministic scoring layer | ⚠️ Stale | `baselines.py:evaluate_submission` keyed on placeholder tokens; v2 outputs score 0/30 by design |
| Judge layer (Claude Sonnet 4.6, 5-axis, 0–1 continuous) | ⚠️ Partial | 15/30 pass on v2; abstract rubric mismatch (1/12); principled order violated — see note below |
| Cross-model evaluation | ❌ Not done | DeepSeek V3 only |
| Judge-to-judge agreement | ❌ Not done | Single judge; self-bias not mitigated |
| Human-validated reference units | ❌ Not done | 0 human-adjudicated |
| Prior-work citations in README/docs | ❌ Not done | LAB-Bench / PaperBench / DeepScholar-Bench / MedHELM only in `research/` |
| `leaderboard_gate_passed` | ❌ `false` | Correctly blocked |

**Governance-principle note.** The project's own `research/04_judge_design_and_validation.md` lists among rejected alternatives: *"Using a single LLM judge before a human validation slice exists"*, and states as an adopted decision: *"First build a human-adjudicated validation slice of at least 30 units."* Our Sonnet-4.6 judge run was valuable as a diagnostic — it is what exposed the v1 prompt bug — but it was built ahead of the committed order. This plan puts human validation back in its intended position.

**Session API spend so far:** ~$1.61 (submissions $0.04 + v1 judge $0.75 + v2 submissions $0.04 + v2 judge $0.72 + dev $0.05 + misc $0.01). The user's earlier $3 ceiling was for the judge-wiring iteration specifically, not a lifetime project budget; Tier A below defines a fresh ~$20 budget.

---

## Phase 2 — External research (condensed)

### 2.1 Competitive landscape

| Benchmark | Task | Overlap with us |
|---|---|---|
| **LAB-Bench** (FutureHouse, 2024) | Biology research MCQ; 2,457 Qs; 80/20 canary | Governance template matched |
| **PaperBench** (OpenAI, 2025) | Replicate 20 ICML papers as **code**; 8,316 rubric nodes | Rubric-design template; separate `JudgeEval` validates the judge (o3-mini F1=0.83 on 5 manually graded) |
| **DeepScholar-Bench** (UC Berkeley Sky, 2025) | Generate **related-work sections** from arXiv, live/rolling | Closest in spirit; scope narrower than ours |
| **MedHELM** (Stanford CRFM, 2025) | 121 clinical tasks incl. note generation; 29 clinicians | LLM-jury ICC=0.47 on 56 rated instances, exceeding clinician-clinician ICC=0.43 |
| **WritingBench** (NeurIPS 2025) | General writing across 6 domains incl. Academic abstracts | Not biomedical, not evidence-conditioned; 7B critic @ 83% human agreement |
| Adjacent QA-only | BioASQ, MedQA, PubMedQA, MedMCQA, SciFact, SciAssess, SciRIFF, BioProBench, CURIE, BixBench | None generate paper sections from evidence |

**Niche claim (hedged):** as far as our research agent's literature search surfaced, the specific triplet `methods_to_text + results_to_text + abstract_from_evidence` on qualified biomedical full-text is not occupied by an existing benchmark. This is a library-search finding, not a proof of novelty; a pre-submission literature review would tighten the claim before publication.

### 2.2 What drives citation of a benchmark

| Adoption driver | Our current status |
|---|---|
| Concrete realistic task | ✅ paper-section writing |
| Credible contamination story (canary + private holdout) | ✅ matches LAB-Bench |
| Frontier-model baselines at launch (≥5 models) | ❌ only DeepSeek V3 |
| Reproducible judge (published rubric + validation κ/ICC) | ❌ no JudgeEval-equivalent |
| Harness integration (Inspect / HELM) | ❌ none |
| Named co-authors / institutional endorsement | ❌ solo |
| Single memorable headline number | ❌ too early |
| License clarity | ✅ Apache-2.0 code; `DATA.md` specifies CC-BY-4.0 intent for released data |
| Versioning / maintenance cadence | ❌ not yet committed |

### 2.3 Judge-validation methodology (credible bars)

- **Statistics to report:** Cohen κ on pass/fail binarization + ICC(2,1) on continuous scores + Krippendorff α on robustness. Standard triple in biomedical NLP.
- **Publishable bars:** κ > 0.6 "substantial" (Landis–Koch), α ≥ 0.80 publishable, ICC ≥ 0.75 "good". MedHELM's **ICC=0.47** (framed as "exceeding clinician-clinician ICC=0.43") is the minimum-defensible bar. Realistic target: **κ ≈ 0.6–0.7, ICC ≈ 0.55–0.70**.
- **Rubric anchoring:** 0–1 continuous scoring has known failure modes (G-Eval 2023 — low variance, poor correlation with humans without logprob access). 10-point scales show central-tendency bias. **Switch to 4-point anchored ordinal** (0 = absent/wrong, 1 = partial, 2 = mostly correct, 3 = fully compliant) with 2–3-sentence behavioral anchors per level per axis. Pass threshold mean ≥ 2.0. No midpoint on purpose.
- **Multi-judge panel:** 3 judges (GPT-5 + Claude Sonnet 4.6 + Gemini 2.5 Pro, or substitute an open-weights model as the third). Unweighted-mean aggregation. **Family-bias exclusion mandatory** (Panickssery et al. NeurIPS 2024 arXiv 2410.21819; arXiv 2508.06709) — e.g., don't use Claude to grade a Claude submission; drop to 2-judge mean for that cell.
- **Sample size — reconciling our docs with statistical theory:** `research/04_judge_design_and_validation.md` committed to *"at least 30 units"* as the floor; `docs/long_term_program.md` references a 60-paper calibration scaffold. A κ ≈ 0.6 point estimate with 95% CI half-width ≈ 0.15 needs **n ≈ 60** bundles; half-width 0.10 needs **n ≈ 100–150**. Plan target: **60 human-annotated bundles** (honors the project's 60-paper commitment and gives CI width ≈ 0.15). 30 is acceptable only for a preliminary IAA sanity check.
- **Annotator protocol:** 2 independent annotators + 1 senior adjudicator. Report IAA *before* adjudication as the honest number. If pre-adjudication κ < 0.4 → rubric is underspecified, revise before scaling. (If only 1 colleague is available, see contingency under Tier B.)

### 2.4 Launch resourcing

| Path | Human annotators | Cash | API | Half-time timeline | Output |
|---|---|---|---|---|---|
| Solo / research preview | 0 | $0 | ~$20 | 4 weeks | arXiv + HuggingFace, honest "not-validated-yet" framing |
| Lab-collaborator (our likely path) | 2–3 colleagues as co-authors | $0–$2k honoraria | ~$20 for Tier A + ~$1–2k for Tier B baselines | 3–4 months | arXiv + workshop paper, citable |
| Institutional (MedHELM template) | 29+ clinicians | ~$10–30k honoraria | ~$11k leaderboard refresh | 6+ months | NeurIPS D&B / Nature Methods research paper |

---

## Phase 3 — Direct answer to the user's core question

**"Can I do this without human validation?"**

**As a citable benchmark — no.** Every 2024–2026 biomedical benchmark that gets cited (LAB-Bench, PaperBench, MedHELM, DeepScholar-Bench, WritingBench) publishes human-agreement numbers. Without ≥ 30–60 human-annotated bundles and a κ / ICC / α trio, reviewers will decline the benchmark claim on methodological grounds and the judge scores are not defensible. The project's own `research/04` committed to this before we started.

**But:** external paid annotators aren't the only path. The user's lead — "maybe I can find someone in the lab or our institute" — is how most 2024–2026 benchmarks actually recruited annotators. Co-authorship is an accepted incentive.

**What to do now:** ship a v0.1 **research preview** (Tier A below) that fixes the known internal-consistency bugs and gives you a tangible artifact to recruit with. Then pursue Tier B if and only if ≥ 2 biomedical colleagues agree to annotate in exchange for co-authorship.

---

## Phase 4 — Recommended direction (two-tier)

### Tier A — v0.1 research preview (~4 weeks half-time, ~$20 API)

Fix the internal-consistency bugs the v2 iteration surfaced, add cross-model breadth, and publish an honest research preview. Do this **regardless** of Tier B; it's the forcing function for recruitment.

Four sessions, each with an explicit gate before the next.

**Session 1 — Scoring-layer refresh (~$5 API, 1 session).**
- Rewrite `src/life_science_paperwritingbench/baselines.py`:
  - Keep `_evidence_tokens` and `evaluate_submission` unchanged as `_evidence_tokens_v1` / `evaluate_submission_v1` (preserve reproducibility of existing release artifacts).
  - Add new `evaluate_submission_v2` that replaces the pointer-token traceability heuristic with a regex-based citation-specificity score (hoist the `citation_specificity` helper from `scripts/llm_smoke_eval.py` into a new package module `src/life_science_paperwritingbench/scoring.py` — keeping `baselines.py` free of duplicate regex).
  - Wire `evaluate_submissions` to accept a `version: Literal["v1","v2"]` kwarg defaulting to `"v2"`.
- Update unit tests in `tests/test_qualification.py`: the two existing `test_run_baseline_and_evaluate_submissions*` tests use `evidence_pointers=("Fig1", "Table1")` — they should still pass under v2 because Fig1/Table1 match the new regex. Add 3–4 new tests: (a) v2 rejects placeholder pointer tokens, (b) v2 credits real figure/table/accession/URL citations, (c) forbidden-pointer output still fails v2.
- Success criterion: full test suite passes; v2 evaluation on `calibration/llm_public_slice_v2/submissions.jsonl` yields a deterministic pass rate **≥ 15/30 (current judge pass rate) and ≤ 30/30**. The v2 deterministic check is more permissive than the judge's full rubric — it tests for citation *presence*, the judge tests for citation *correctness* — so deterministic ≥ judge is the expected relation.

**Gate A1 → A2:** the expected relation holds. If deterministic < judge on the same submissions, the new scoring is too strict — loosen or re-examine before adding more rubric changes.

**Session 2 — Judge rubric v3 (~$5 API, 1 session).**
- In `scripts/llm_judge_eval.py`:
  - Switch `RUBRIC_AXES` to 4-point anchored ordinal (0–3 integer). Add behavioral anchors per axis per level in the judge prompt.
  - Add family-aware rubric variant: for `task_family == abstract_from_evidence`, replace the `traceability` axis with a new `quantitative_specificity` axis (rewards p-values, sample sizes, effect sizes, accessions, organism names; explicitly waives figure/table citation requirement). Document the swap in the judge prompt and in `docs/benchmark_transparency_card.md`.
  - Change `PASS_THRESHOLD` to mean ≥ 2.0 on 0–3 scale; keep the old 0–1 threshold as a legacy alias.
- Re-run the 30-bundle judge on `calibration/llm_public_slice_v2/submissions.jsonl` with v3 rubric, output to `calibration/llm_public_slice_v2_judged_v3/`.
- Success criterion: abstract pass rate improves to ≥ 5/12 (up from 1/12 under v2 rubric). Non-abstract pass rates should remain ≥ current levels.

**Gate A2 → A3:** abstract-rubric mismatch is resolved. If abstracts still under 3/12, reopen the axis definitions.

**Session 3 — Cross-model breadth (~$7 API, 1 session).**
- Activate Gemini 2.5 Flash in `scripts/llm_smoke_eval.py` (already wired in `PROVIDERS`, just run with `--model gemini-2.5-flash`) and add Claude Haiku 4.5 as a new submitter provider — copy the Anthropic `x-api-key` adapter pattern from `scripts/llm_judge_eval.py` (already proven working there). Run all three (DeepSeek V3, Gemini 2.5 Flash, Claude Haiku 4.5) on the 30-bundle slice with the v2 prompt.
- Add two judges to `scripts/llm_judge_eval.py`: Gemini 2.5 Pro and GPT-5 mini (or GPT-4o if pricing shifts). Run the 3-judge jury on all three models' submissions, aggregating with unweighted mean and applying family-bias exclusion (Claude judge drops for Claude submissions, Gemini judge drops for Gemini submissions; DeepSeek has no family collision). Output to `calibration/llm_public_slice_matrix_v1/`.
- Emit a matrix summary. For each of the 3 submitters, aggregate per-axis scores across the (up to 3) eligible judges to produce **3 submitters × 5 axes = 15 per-submitter-per-axis means**, plus **3 per-submitter overall pass rates**. Separately report the raw 3 submitters × 3 judges × 5 axes = 45 cell means so judge-to-judge disagreement is visible.
- Success criterion: ≥ 30 percentage-point spread between weakest and strongest model's overall pass rate. If tight clustering, the rubric is still underspecified and Gate A3 fails.

**Gate A3 → A4:** meaningful cross-model spread observed. If not, stop and return to rubric design.

**Session 4 — Canary probe + README refresh + arXiv draft (~$5 API, 1–2 sessions).**
- New script `scripts/canary_probe.py`: contamination probe across the 5 frontier models (3 submitters + 2 judges). Because Anthropic does not expose token log-probabilities and OpenAI/Gemini increasingly restrict them, the probe is **a completion test**, not a log-prob test: prompt each model with a short natural-language stem containing the canary prefix (`Continue the sequence exactly: LS-PWB-CANARY-...`) and check whether the model reproduces the full stored canary string verbatim. Also run matched-length random-control canaries that were never published, as a negative control. Report per-model: (a) did the model reproduce our canary verbatim? (b) did it reproduce any random control? (c) Levenshtein distance to the expected continuation. Binary reproducing-the-public-canary = contamination red flag. Publish in `docs/canary_probe_report.md`.
- Rewrite `README.md`:
  - Add "Related work" section citing LAB-Bench, PaperBench, DeepScholar-Bench, MedHELM, WritingBench with DOIs/URLs.
  - Add "Evaluation methodology" section documenting the 4-point ordinal rubric, family-aware abstract axis, 3-judge jury, family-bias exclusion.
  - Add "Current limitations" section: v0.1 research preview, no human validation yet, rubric κ/ICC pending, solo authorship.
- Draft a 6–8 page workshop paper in `paper/` (new dir) covering: governance core, task families, rubric design, cross-model results, canary-probe results, honest limitations. See venue note below for realistic targets.
- Tag and push a `v0.1-research-preview` git tag. Consider an arXiv submission once the draft has been read by at least one external reader.

Realistic venues given 2026 timing: workshop tracks at **NeurIPS 2026** (typically September/October deadline) or **AAAI 2027**, or a late arXiv-only release targeting **BioNLP 2027 at ACL**. BioNLP 2026 at ACL has already closed, and the NeurIPS D&B main track (typically May–June deadline) is probably too tight for Tier A alone and better paired with Tier B.

**Tier A exit criteria (all must hold before considering Tier B):**
1. v2 deterministic pass rate ≥ v2 judge pass rate on the same 30 submissions (internal consistency).
2. 4-point ordinal rubric with behavioral anchors is shipped and covered by at least one regression test.
3. Abstract family rubric swap yields ≥ 5 / 12 pass rate on the 30-bundle slice (up from 1 / 12 pre-swap).
4. 3 models × 3 judges matrix is published with ≥ 30 percentage-point spread between strongest and weakest submitter's overall pass rate.
5. Canary probe report is published; any positive reproduction (contamination finding) is documented explicitly rather than hidden.
6. README has `## Related work`, `## Evaluation methodology`, `## Current limitations` sections citing the 5 competitive benchmarks.
7. Workshop-paper draft exists in `paper/` and has been read by at least one external reader before arXiv submission.

### Tier B — v1.0 citable launch (~3 months on top of Tier A, $0–$2k cash)

**Proceed only if Tier A exit criteria hold AND at least one biomedical colleague commits to co-authorship.**

1. **Recruit annotators.** Aim for 2 biomedical colleagues (postdoc or senior PhD) + user as senior adjudicator. If only 1 colleague is available, the contingency is: (a) user serves as second annotator on bundles the colleague hasn't touched; external adjudicator recruited via Anthropic / OpenAI grant program or LAB-Bench-style volunteer ask; (b) if that also fails, stay permanently at Tier A v0.1 and apply for research credits to fund an external annotator later.
2. **Annotation protocol** (`validation/human_annotation_protocol.md`):
   - 60 bundles (20 per task family), stratified by study class.
   - 4-point ordinal × 5 axes (abstract family uses `quantitative_specificity` instead of `traceability`).
   - ~40 h per annotator wall-clock (60 × 5 × ~8 min ÷ 2 annotators), 6 weeks at half-time.
   - Adjudication queue written from disagreements (Δ ≥ 1 on any axis).
3. **Compute agreement** in new `scripts/compute_agreement.py`:
   - Cohen κ on pass/fail binarization, Krippendorff α on ordinal, ICC(2,1) on mean-axis continuous. Report all three, pre- and post-adjudication.
   - Gate: pre-adjudication κ ≥ 0.4 (rubric-specification minimum). Post-adjudication κ ≥ 0.6 is the publication bar.
4. **Judge-vs-human calibration.** For each of the 3 judges and the jury mean, compute ICC against the adjudicator and against each individual annotator. Gate: jury-vs-adjudicator ICC ≥ 0.5 (matches MedHELM).
5. **Inspect-evals integration.** New file `inspect_evals/life_science_paperwritingbench.py` exposing the benchmark as an Inspect task. Single biggest adoption multiplier per the comparative literature.
6. **v1.0 paper + release.** Realistic venue order of preference: (a) **NeurIPS D&B 2027** (gives runway for recruitment + annotation), (b) **Nature Methods** research article (not Perspective — the benchmark is an artifact, not a viewpoint piece), (c) ACL / BioNLP 2027. NeurIPS D&B 2026 main track is technically possible if recruitment happens in weeks-not-months, but tight enough that planning for it is risky.
7. **Flip `leaderboard_gate_passed = true`** only after all of: κ ≥ 0.6 on 60 bundles, jury-vs-adjudicator ICC ≥ 0.5, ≥ 5 models in matrix, Inspect task landed.

### What explicitly NOT to do

- Do not scale the LLM submission + judge to the **full 430-public-bundle corpus** until the rubric is 4-point anchored and family-aware. Wasted cost otherwise.
- Do not add task families (discussion, figure captions, related work) before Tier A ships. Three families is the right scope.
- Do not attempt NeurIPS D&B solo before recruiting ≥ 2 co-authors.
- Do not rewrite the governance core (`qualification.py`, `split_safety.py`, `release.py`). It's the repo's strongest asset.
- Do not delete or overwrite v1-scoring artifacts; preserve them for release-contract reproducibility.

---

## Critical files to modify (Tier A)

| File | Change | Session |
|---|---|---|
| **`src/life_science_paperwritingbench/scoring.py`** (new) | Host `citation_specificity` + regex constants hoisted from `scripts/llm_smoke_eval.py` | 1 |
| **`src/life_science_paperwritingbench/baselines.py`** | Add `evaluate_submission_v2` using `scoring.citation_specificity`; keep v1 as alias | 1 |
| **`src/life_science_paperwritingbench/__init__.py`** | Export new helpers | 1 |
| **`tests/test_qualification.py`** | Update `test_run_baseline_and_evaluate_submissions{,_for_qa_bundle}` to pass under v2; add 3–4 v2-specific tests | 1 |
| **`scripts/llm_judge_eval.py`** | 4-point ordinal rubric + family-aware abstract axis + jury aggregation helper | 2, 3 |
| **`scripts/llm_smoke_eval.py`** | Add Gemini 2.5 Flash and Claude Haiku 4.5 providers; remove now-duplicated regex | 3 |
| **`scripts/canary_probe.py`** (new) | Per-model canary log-probability probe | 4 |
| **`README.md`** | Related-work section, evaluation-methodology section, limitations section | 4 |
| **`docs/benchmark_transparency_card.md`** | Rubric versioning, jury composition, family-bias exclusion, canary-probe procedure | 4 |
| **`docs/session_handoff_2026-04-13.md`** | Replace next-step list with Tier A / Tier B structure | 4 |
| **`paper/`** (new dir) | 6–8 page workshop-paper draft | 4 |

## Reused helpers (avoid rewriting)

- `scripts/llm_smoke_eval.py:citation_specificity()` and its `_FIGURE_REF_RE`, `_TABLE_REF_RE`, `_PVALUE_RE`, `_NUMERIC_MAGNITUDE_RE`, `_ACCESSION_RE`, `_REPO_URL_RE`. Move verbatim to `src/life_science_paperwritingbench/scoring.py`; `llm_smoke_eval.py` then imports them.
- `scripts/llm_judge_eval.py:call_anthropic()` + `call_openai_compatible()` with retry-with-backoff. Keep in the script (no need to hoist yet).
- `src/life_science_paperwritingbench/evidence_enrichment.py:_ACCESSION_PATTERN` and `_REPOSITORY_URL_PATTERN`. Canonical regex set. Scoring module imports these rather than duplicating.
- `src/life_science_paperwritingbench/inspection.py:_has_abstract_inferred_only_signal`. Already models upstream acquisition gap — the scoring module can use it to suppress low-grounding penalties on bundles whose evidence is abstract-inferred.

---

## Verification (end-to-end checks per session)

**Session 1:**
1. `python3 -m compileall src tests scripts` — clean.
2. `PYTHONPATH=src python3 -m unittest tests.test_qualification` — all tests pass (expect +3–4 new tests).
3. `PYTHONPATH=src python3 -c "from life_science_paperwritingbench.scoring import citation_specificity; print(citation_specificity('Results. As shown in Fig. 1, p<0.05...'))"` — returns non-zero score.
4. `PYTHONPATH=src python3 scripts/llm_smoke_eval.py --task-source inspection-slice --output-dir calibration/llm_public_slice_v3` — v3 deterministic pass rate is **≥ 15/30 (the current judge pass rate)** and **≤ 30/30**. The v2 citation-specificity metric is more permissive than the judge's full rubric, so the deterministic layer should not be stricter than the judge; if it is, the new scoring is miscalibrated.

**Session 2:**
5. `PYTHONPATH=src python3 scripts/llm_judge_eval.py --submissions-path calibration/llm_public_slice_v3/submissions.jsonl --output-dir calibration/llm_public_slice_v3_judged` — abstract pass rate **≥ 5/12**.

**Session 3:**
6. Matrix summary in `calibration/llm_public_slice_matrix_v1/summary.md` shows 3 models × 3 judges, with ≥ 30 pp spread between strongest and weakest model.
7. Inspect a single cell to confirm family-bias exclusion fired (Claude-judge row for Claude-submitter column should show only 2-judge mean).

**Session 4:**
8. `PYTHONPATH=src python3 scripts/canary_probe.py` produces `docs/canary_probe_report.md`. Expected: 0 models reproduce the public canary verbatim on a clean run; 0 models reproduce the random controls (sanity check). Any model that reproduces the canary → contamination finding to publish explicitly.
9. `README.md` has `## Related work`, `## Evaluation methodology`, `## Current limitations` sections.
10. `git tag v0.1-research-preview && git push --tags`.

**Tier B (if pursued):**
11. `scripts/compute_agreement.py` reports κ, ICC, α on 60 annotated bundles; pre-adjudication κ ≥ 0.4 before scaling; post-adjudication κ ≥ 0.6 before release.
12. `inspect eval life_science_paperwritingbench --model claude-sonnet-4-6 --limit 3` runs without errors.

---

## Budget summary

| Item | Cash | API |
|---|---:|---:|
| Session 1 (scoring refresh) | $0 | ~$0 (compile + test only, no new LLM calls) |
| Session 2 (judge rubric v3) | $0 | ~$1 (re-judge 30 bundles with updated rubric) |
| Session 3 (3-model × 3-judge matrix) | $0 | ~$7 (3 × 30 submissions ≈ $0.25 + 3 × 3 × 30 judge calls ≈ $6.75 at Sonnet+Gemini Pro+GPT-5-mini rates; family-bias exclusion reduces a few cells to 2 judges) |
| Session 4 (canary probe + docs + draft) | $0 | ~$5 (canary probe is low-token; writing is offline) |
| **Tier A total** | **$0** | **~$13** |
| Tier B API (recompute matrix on 60 bundles with full rubric) | $0 | ~$20 |
| Tier B annotator honoraria (co-authorship covers most; optional) | $0–$2k | — |
| Inspect-evals integration | $0 | ~$5 |
| **Tier B total additional** | **$0–$2k** | **~$25** |

Lifetime project API spend through Tier B ≈ **~$40** if research credits don't materialize; $0–$5 if they do. Anthropic and OpenAI both offer research-credit programs that are routinely granted at the scale we need; applying early in Tier A is an easy accelerator but not a dependency. Annotator honoraria are the only non-API line and are avoidable if co-authors agree to contribute their time in exchange for authorship.

---

## Execution sequence (post-approval)

1. Copy `~/.claude/plans/nifty-seeking-koala.md` to `docs/strategic_review_2026-04-13.md` and commit with message "Add strategic review doc for Phase 2 direction-setting".
2. Update `docs/session_handoff_2026-04-13.md` to replace the old "remaining substantive targets" block with a pointer to `strategic_review_2026-04-13.md` and the Tier A session plan.
3. Begin **Session 1** (scoring-layer refresh): create `src/life_science_paperwritingbench/scoring.py`, add `evaluate_submission_v2`, update tests, commit.
4. Stop. Report Session 1 outcome against Gate A1→A2 to the user before spending Session 2 API.

---

## One-sentence framing (aspirational, for post-Tier-B launch)

> Life-Science PaperWritingBench evaluates LLMs on writing biomedical paper sections (methods, results, abstract) from qualified evidence, with LAB-Bench-grade contamination defenses and a 3-judge LLM jury whose agreement with biomedical annotators is measured and published — currently a v0.1 research preview, moving toward a v1.0 citable release with lab co-authored human validation.
