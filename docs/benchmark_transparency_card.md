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

## Judge Rubric Snapshot

- `scripts/llm_judge_eval.py` now supports a 4-point anchored ordinal rubric (`0`-`3`) as rubric `v3`
- rubric `v3` uses a mean-axis pass rule: `mean(axis_scores) >= 2.0`
- `abstract_from_evidence` swaps `traceability` for `quantitative_specificity`
- abstract judging explicitly rewards p-values, sample sizes, effect sizes, accessions, and organism names without requiring figure/table citations

## Current Matrix Checkpoint

- current matrix artifact: `calibration/llm_public_slice_matrix_v1/summary.md`
- matrix summarizer: `scripts/llm_matrix_summary.py`
- current declared matrix coverage: `3` submitters x `3` judges with `5 / 9`
  cells complete, `3` family-bias exclusions, and `1` diagnostic missing cell
- current official coverage in the matrix artifact: `4` completed official cells
  across `3` submitters and `2` official judges
- current release-readiness gap: the registry requires Gemini submitter
  coverage (`gemini-2.5-flash`) and Gemini official judge coverage
  (`gemini-2.5-pro`) before the hosted official matrix can pass
- current common-judge submitter spread: `n/a` because no official judge covers
  all compared submitters
- current strongest same-judge spread: `23.3` percentage points under
  `claude-sonnet-4-6`
- current caveat: `gpt-5-mini` is diagnostic-only and has one completed
  diagnostic cell with `7` parse failures

## Current Canary Checkpoint

- canary probe script: `scripts/canary_probe.py`
- current report: `docs/canary_probe_report.md`
- current live hosted-working-set artifact: `calibration/canary_probe_v1_live_hosted_working_set/summary.md`
- current live result on `deepseek-chat`, `gpt-4o-mini`, `gpt-5.4-mini`,
  `claude-haiku-4-5`, and `claude-sonnet-4-6`:
  - exact public-canary matches: `0 / 5`
  - exact random-control matches: `0 / 5`
- current caveat:
  - this is a partial `5-model` contamination check, not yet the full
    registry-declared production probe
  - Gemini remains missing from the current hosted-working-set run

## Current Preview-Freeze Stance

- current freeze target: `v0.1 research preview`
- current freeze checklist: `docs/research_preview_freeze_checklist.md`
- human reviewer execution is on hold
- the publication-validation batch is selected, packet-complete, and
  structurally ready, but it is not human-validated
- `leaderboard_gate_passed=false` is the correct state until agreement,
  matrix, and canary gates are complete
- hosted-frontier results and future open-weight/VLLM results should remain
  separate tracks until comparable artifacts exist
- open-weight / VLLM track policy: `docs/open_weight_vllm_track.md`

## Known Current Limitations

- no network-backed ingestion connector yet
- no human-adjudicated judge validation slice yet; human reviewer execution is
  held, and agreement/adjudication metrics are still pending
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
