# Session Handoff: 2026-04-26

## Purpose

This is the restart point for the current `v0.1 research preview` freeze.

Use it to answer:

- what is complete enough to show externally
- what is intentionally held
- which artifacts define the current claim boundary
- what the next non-human work should be

## Current Stance

The project is in `v0.1 research preview` state.

Human reviewer execution is intentionally on hold. The frozen
publication-validation batch is selected, packet-complete, and structurally
ready, but it is not human-validated.

The current release-facing interpretation is:

- `leaderboard_gate_passed=false`
- hosted-frontier matrix is partial
- Gemini submitter, judge, and canary coverage are still missing
- open-weight / VLLM is a separate track and does not satisfy hosted-frontier
  matrix cells
- no `kappa`, `ICC`, or `alpha` agreement metrics are available yet

## Current Reader Map

Start here:

- `docs/v0.1_research_preview_artifact_index.md`

Then inspect:

- `docs/v0.1_research_preview_release_notes.md`
- `docs/research_preview_freeze_checklist.md`
- `docs/inspect_replay_quickstart.md`
- `docs/open_weight_vllm_track.md`
- `paper/workshop_draft_v0.md`
- `paper/figures/governance_pipeline.mmd`

Current artifact anchors:

- best deterministic / citation anchor:
  `calibration/llm_agentic_public_slice_v1_rerun2/summary.md`
- best judged agentic anchor:
  `calibration/llm_agentic_public_slice_v1_rerun5_judged_v3/summary.md`
- partial hosted matrix:
  `calibration/llm_public_slice_matrix_v1/summary.md`
- current canary report:
  `docs/canary_probe_report.md`
- publication-validation batch:
  `calibration/publication_validation_v1/`
- readiness snapshot:
  `calibration/publication_validation_v1/publication_readiness_snapshot.json`

## Recent Completed Work

Recent preview-freeze commits on
`codex-project-review-hardening-publication-readiness`:

- `0450af2` Add v0.1 preview artifact index
- `dbaca88` Separate open-weight VLLM track policy
- `a5ea220` Add Inspect replay quickstart
- `f9fa67e` Add v0.1 preview release notes
- `fa06782` Add preview freeze checklist and review intake audit
- `afac2df` Update publication readiness handoff docs

Main outcomes:

- added `audit-publication-review-intake` to validate returned reviewer JSONL
  before merge
- documented the human-validation hold while keeping the batch structurally
  ready
- added a preview freeze checklist and release notes
- added an external-reader artifact index
- added an Inspect/replay quickstart for API-free record building,
  deterministic replay, judge replay, and dry-run provider submission schema
  checks
- added open-weight / VLLM track policy and readiness `track_summary`
- added a regression proving open-weight submitter runs do not fill missing
  hosted-frontier matrix cells

## Verification Status

The latest code-bearing preview-freeze pass completed:

```bash
python3 -m compileall -q src scripts tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Observed result:

- compile check passed
- full unittest suite passed: `256` tests
- whitespace diff check passed

Additional targeted checks passed:

- publication readiness / VLLM track tests
- Inspect adapter replay tests
- artifact-path existence checks for the preview artifact index

The readiness refresh command currently exits nonzero as expected because the
leaderboard gate is still red:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-publication-readiness \
  --matrix-summary calibration/llm_public_slice_matrix_v1/summary.json \
  --canary-summary calibration/canary_probe_v1_live_hosted_working_set/summary.json \
  --validation-summary calibration/publication_validation_v1/publication_validation_summary.json \
  --output calibration/publication_validation_v1/publication_readiness_snapshot.json
```

Expected current failure reasons:

- missing Gemini submitter/judge/canary coverage
- missing open-weight comparable artifact
- missing human agreement metrics

## Do Not Accidentally Claim

Do not describe the current project as:

- human-validated
- publication-ready
- final leaderboard-ready
- Gemini-complete
- registry-complete for contamination
- open-weight / hosted-frontier comparable
- validated by LLM judges alone

Use "research preview" language until human agreement, Gemini coverage, and
separate-track open-weight artifacts exist.

## Next Recommended Work

Recommended order if human validation stays held:

1. Prepare the workshop draft for a target venue format while preserving
   preview language.
2. Render and refine `paper/figures/governance_pipeline.mmd` into a
   camera-ready or publication-friendly pipeline figure.
3. When Gemini credentials are available, complete Gemini submitter, official
   judge, and canary cells.
4. When cluster time is available, scaffold and run the
   `openweight-vllm-submitter` track using `docs/open_weight_vllm_track.md`.
5. When human validation resumes, start with the calibration starter set and
   run `audit-publication-review-intake --stage calibration` before letting
   reviewers continue.

## If Resuming Human Validation Later

Keep the current hold discipline:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-review-intake \
  --batch-dir calibration/publication_validation_v1 \
  --stage calibration
```

Only after starter intake is clean should the full round proceed. Before merge:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-review-intake \
  --batch-dir calibration/publication_validation_v1 \
  --stage full
```
