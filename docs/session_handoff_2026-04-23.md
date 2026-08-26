# Session Handoff: 2026-04-23

## Purpose

This file is the restart point for the current publication-validation /
dispatch work after the latest handoff hardening and adversarial review.

Use it to answer four questions quickly:

- what is already working
- what changed in this session
- what is still risky
- what the next session should do first

## Current focus

The active workstream is:

- `calibration/publication_validation_v1/`

This is the first frozen human-review batch for benchmark-unit
adjudication against frozen truth-manifest evidence.

This round is currently framed as:

- benchmark-unit adjudication
- not named-model output review
- two independent reviewers plus one adjudicator

## Continuation update: dispatch hardening completed

The first four recommended next-session fixes below have now been applied:

- dispatch reviewer indexes are regenerated bundle-local and now point at
  `packets/<file>.md`
- preserved dispatch reviewer JSONL working copies are checked against the
  canonical `(validation_unit_id, reviewer_id)` row set before being kept
- `build-publication-review-packets` now supports
  `--refresh-dispatch-reviewer-forms` for explicit overwrite
- adjudicator dispatch guidance is gated on the complete post-review artifact
  set and no longer copies stale `publication_readiness_snapshot.json` into
  the adjudicator bundle before intake is complete
- dispatch README provenance is generated from the supplied `batch_dir`

The publication-validation packets and dispatch bundles were regenerated with:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli \
  build-publication-review-packets \
  --batch-dir calibration/publication_validation_v1 \
  --output-dir calibration/publication_validation_v1/review_packets
```

Targeted tests passing after regeneration:

- `tests.test_qualification.QualificationTests.test_cli_build_publication_validation_batch`
- `tests.test_qualification.QualificationTests.test_cli_build_publication_review_packets_and_audit_hold`
- `tests.test_qualification.QualificationTests.test_cli_build_publication_review_packets_detects_stale_dispatch_forms`
- `tests.test_qualification.QualificationTests.test_cli_build_publication_review_packets_without_adjudications_file`

Verification update:

- `python3 -m compileall -q src scripts tests` passes
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passes
  (`239` tests)

## Continuation update: review blockers fixed

The follow-up thorough review found and fixed two remaining dispatch /
adjudication blockers:

- completed judge-review forms now count as complete only when all required
  rubric axes have numeric values
- incomplete completed forms are kept pending in the adjudication queue and
  are excluded from agreement metrics with an explicit issue
- reviewer dispatch `calibration_mini_round.md` is generated per reviewer
  with local `packets/<file>.md` paths
- reviewer and adjudicator dispatch protocol copies no longer carry stale
  `calibration/publication_validation_v1/...` review/adjudication paths

The real `calibration/publication_validation_v1/review_packets` and
`calibration/publication_validation_v1/dispatch` artifacts were regenerated
after these fixes.

## Continuation update: publication-readiness gate hardened

The latest overall-project review found and fixed eight readiness-gate edge
cases around frontier model identity and partially filled readiness artifacts:

- hosted submitter coverage is now matched against registry-facing
  `model_label` aliases as well as provider `request_model` IDs
- canary coverage now canonicalizes requested/ok model identifiers through
  the registry, including provider `request_model` aliases
- `production_models_ok` is combined with ok `model_summaries` instead of
  being used only when no ok summary rows exist
- judge-only registry entries are no longer treated as required hosted
  submitters merely because `submitter_track` defaulted to `hosted_frontier`
- frontier registry normalization now defaults missing `submitter_track` to
  `not_applicable` for judge-only entries and `hosted_frontier` only for
  submitter-capable entries
- the hosted/open-weight track gate now infers tracks from `submitter_runs`
  when `submitter_tracks_present` is absent
- non-numeric or non-finite agreement metrics such as `n/a`, `None`, and
  `nan` now fail closed as `0.0` instead of crashing or leaking NaN
- string boolean readiness flags such as `"false"` and `"0"` are parsed
  explicitly instead of becoming truthy through Python's default `bool()`

A regression now covers a custom registry where `model_label` differs from
`request_model`.

Verification update:

- `python3 -m compileall -q src scripts tests` passes
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passes
  (`242` tests)

## Canonical artifacts right now

Main batch directory:

- `calibration/publication_validation_v1/`

Primary organizer docs:

- `calibration/publication_validation_v1/README.md`
- `calibration/publication_validation_v1/handoff_manifest.md`
- `calibration/publication_validation_v1/review_launch_checklist.md`
- `calibration/publication_validation_v1/pre_human_review_preflight.md`
- `calibration/publication_validation_v1/launch_readiness_assessment_2026-04-23.md`
- `calibration/publication_validation_v1/calibration_mini_round.md`

Truth-manifest sidecars:

- `calibration/publication_validation_v1/truth_manifest_lookup.jsonl`
- `calibration/publication_validation_v1/truth_manifest_lookup.md`
- `calibration/publication_validation_v1/selected_truth_manifests.jsonl`

Protocol:

- `validation/human_annotation_protocol.md`

Reviewer bundle roots:

- `calibration/publication_validation_v1/dispatch/reviewer_a/`
- `calibration/publication_validation_v1/dispatch/reviewer_b/`

Adjudicator bundle root:

- `calibration/publication_validation_v1/dispatch/adjudicator/`

Root launch-message sources:

- `calibration/publication_validation_v1/launch_messages/reviewer_a_launch_message.md`
- `calibration/publication_validation_v1/launch_messages/reviewer_b_launch_message.md`
- `calibration/publication_validation_v1/launch_messages/adjudicator_1_launch_message.md`

## What changed in this session

The main code path is now in:

- `src/life_science_paperwritingbench/cli.py`
- `src/life_science_paperwritingbench/publication_annotation.py`

Implemented changes:

- publication-validation batch build writes truth-manifest sidecars when
  `--truth-manifests` is supplied
- publication-review packet rebuild now regenerates handoff assets and
  dispatch bundles
- reviewer and adjudicator launch-message files are generated
- dispatch reviewer bundles now include:
  - `launch_message.md`
  - `human_annotation_protocol.md`
  - `reviewer_index.md`
  - `reviewer_assignments.jsonl`
  - `judge_review_forms.jsonl`
  - `packets/`
  - `truth_manifest_lookup.jsonl`
  - `selected_truth_manifests.jsonl`
  - `calibration_mini_round.md` when present
- dispatch adjudicator bundle now includes:
  - `launch_message.md`
  - `human_annotation_protocol.md`
  - `adjudicator_handoff.md`
  - `judge_adjudications.jsonl`
  - `judge_units.jsonl`
  - optional post-review files if present

Hardening already completed:

- dispatch `launch_message.md` now uses bundle-local filenames instead of
  batch-root paths
- rerunning `build-publication-review-packets` no longer overwrites an
  existing dispatch reviewer working copy
- `build-publication-review-packets` no longer hard-fails when
  `judge_adjudications.jsonl` is absent

## What was verified

Targeted tests run and passing:

- `tests.test_qualification.QualificationTests.test_cli_build_publication_validation_batch`
- `tests.test_qualification.QualificationTests.test_cli_build_publication_review_packets_and_audit_hold`
- `tests.test_qualification.QualificationTests.test_cli_build_publication_review_packets_without_adjudications_file`

Command used:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_qualification.QualificationTests.test_cli_build_publication_validation_batch \
  tests.test_qualification.QualificationTests.test_cli_build_publication_review_packets_and_audit_hold \
  tests.test_qualification.QualificationTests.test_cli_build_publication_review_packets_without_adjudications_file
```

Important note:

- the full test suite has now been rerun successfully

## Current known problems after review

No unresolved dispatch or publication-readiness blocker is known right now.
The next useful checks are operational: review the generated reviewer bundles
one final time before sending them, then proceed with human reviewer intake.

## Practical command to resume with

After the next fixes, this is the main regeneration command:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli \
  build-publication-review-packets \
  --batch-dir calibration/publication_validation_v1 \
  --output-dir calibration/publication_validation_v1/review_packets
```

## Git state worth remembering

At handoff time the tree is still dirty.

Relevant modified / untracked paths:

- `src/life_science_paperwritingbench/cli.py`
- `src/life_science_paperwritingbench/judgeflow.py`
- `src/life_science_paperwritingbench/judge_agreement.py`
- `src/life_science_paperwritingbench/publication.py`
- `src/life_science_paperwritingbench/publication_annotation.py`
- `tests/test_qualification.py`
- `validation/human_annotation_protocol.md`
- `calibration/publication_validation_v1/`
- `docs/session_handoff_2026-04-23.md`

Also note there were unrelated existing doc changes already present:

- `docs/benchmark_transparency_card.md`
- `docs/session_handoff_2026-04-13.md`
- `docs/strategic_review_2026-04-13.md`
- `docs/canary_probe_report.md`

Do not clean or revert those blindly in the next session.
