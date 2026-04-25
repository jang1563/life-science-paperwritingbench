# v0.1 Research Preview Freeze Checklist

## Purpose

This checklist defines the non-human-validation path for freezing a
`v0.1 research preview`.

Human reviewer execution is intentionally on hold. The preview freeze should
therefore make the project easier to inspect, reproduce, and discuss without
claiming that the benchmark is publication-ready or human-validated.

## Freeze Claim Boundary

The preview may claim:

- a governance-first benchmark framework for evidence-grounded biomedical
  section writing
- three current writing families:
  - `methods_to_text`
  - `results_to_text`
  - `abstract_from_evidence`
- deterministic scoring `v2` and rubric judge `v3` are implemented
- agentic `writer -> critic -> reviser` baselines exist with a conservative
  non-regressive selector
- the current partial hosted matrix shows early separation across submitters
- the current hosted-working-set canary probe observed no exact public/control
  canary reproduction among completed models
- a frozen `60`-bundle publication-validation batch is selected,
  packet-complete, and structurally ready for a future human round
- the project has an Inspect-compatible adapter and artifact-backed replay
  helpers

The preview must not claim:

- human-validated benchmark status
- final leaderboard readiness
- completed Gemini coverage
- registry-complete contamination clearance
- publication-grade judge agreement
- citable benchmark validation based only on LLM judge scores
- equivalence between hosted-frontier and open-weight tracks before comparable
  open-weight artifacts exist

## Current Hold Items

These are intentionally held, not forgotten:

- human reviewer calibration and full review execution
- adjudication and agreement metrics (`kappa`, `ICC`, `alpha`)
- Gemini submitter / judge / canary completion
- open-weight VLLM run completion
- camera-ready paper formatting and external-read submission

## Freeze Gates

### Gate 1: Claim-Language Freeze

- README says `v0.1 research preview`, not benchmark release
- workshop draft says human validation is held/pending
- transparency card names Gemini and human agreement as release-facing gaps
- `leaderboard_gate_passed=false` remains explicit

### Gate 2: Artifact Anchor Freeze

- external-reader artifact index is named
- best judged agentic artifact is named
- best deterministic/citation artifact is named
- current matrix summary is named
- current canary report is named
- current publication-validation batch is named
- current readiness snapshot is named and remains red

### Gate 3: Reproducibility Freeze

Run before tagging or opening a preview PR:

```bash
python3 -m compileall -q src scripts tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Also refresh the structural publication-validation hold audit:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-annotation-hold \
  --batch-dir calibration/publication_validation_v1 \
  --output /tmp/lspwb_publication_hold_audit_check.json \
  --markdown-output /tmp/lspwb_publication_hold_audit_check.md
```

Expected current interpretation:

- `ok=true`
- `structurally_ready=true`
- `awaiting_human_review=true`
- `review_completion_rate=0.0`

### Gate 4: Non-Human Next Work

If human validation stays held, prioritize:

1. Complete Gemini coverage when credentials are available.
2. Keep hosted-working-set results separate from registry-complete claims.
3. Tighten Inspect adapter examples and replay documentation.
4. Prepare an open-weight/VLLM track without mixing it into hosted results;
   use `docs/open_weight_vllm_track.md` as the track policy.
5. Keep the workshop draft in preview language until agreement metrics exist.

## Release Note Template

Use `docs/v0.1_research_preview_release_notes.md` as the release-facing note.
For a shorter preview tag or PR body, use this shape:

```text
Life-Science PaperWritingBench v0.1 research preview

This preview demonstrates the benchmark governance stack, three
evidence-grounded writing families, deterministic/LLM-judge evaluation, a
partial hosted model matrix, and redacted canary probes.

It is not a final benchmark release. Human agreement metrics, Gemini coverage,
and open-weight comparable artifacts remain pending.
```
