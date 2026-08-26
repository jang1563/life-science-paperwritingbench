# Human Annotation Protocol

## Purpose

This protocol is the operational guide for the first publication-validation
batch:

- `calibration/publication_validation_v1/`

It turns the current frozen batch into completed reviewer labels,
adjudications, agreement metrics, and an updated publication-readiness
snapshot.

Per `docs/judge_validation_contract.md`, this round is primarily about creating
human-adjudicated benchmark units for future judge validation. Unless the
organizer explicitly defines a different artifact for a later round, reviewers
should treat the target as the frozen benchmark-unit package plus the matching
frozen truth-manifest evidence, not a frontier-model submission.

## Current Batch Snapshot

- selected validation units: `60`
- task-family coverage:
  - `20` `methods_to_text`
  - `20` `results_to_text`
  - `20` `abstract_from_evidence`
- study-class stratification: ready
- review design: `2` independent reviewers + `1` adjudicator
- batch state: frozen, packet-complete, awaiting human review

Primary batch references:

- batch overview:
  `calibration/publication_validation_v1/README.md`
- structural hold audit:
  `calibration/publication_validation_v1/annotation_hold_audit.md`
- reviewer packet summary:
  `calibration/publication_validation_v1/review_packets/summary.md`
- judge-validation contract:
  `docs/judge_validation_contract.md`
- pre-launch preflight:
  `calibration/publication_validation_v1/pre_human_review_preflight.md`
- launch readiness assessment:
  `calibration/publication_validation_v1/launch_readiness_assessment_2026-04-23.md`
- calibration starter set:
  `calibration/publication_validation_v1/calibration_mini_round.md`
- organizer dispatch map:
  `calibration/publication_validation_v1/handoff_manifest.md`
- organizer launch checklist:
  `calibration/publication_validation_v1/review_launch_checklist.md`
- adjudicator handoff:
  `calibration/publication_validation_v1/adjudicator_handoff.md`

## Roles

Before dispatch, the organizer should complete
`calibration/publication_validation_v1/pre_human_review_preflight.md` so the
review target, calibration plan, and agreement plan are explicit for this round.
The organizer should also review
`calibration/publication_validation_v1/launch_readiness_assessment_2026-04-23.md`
before starting the round.

### Reviewers

- score only the units assigned to their `reviewer_id`
- work from the markdown packets for context
- write final labels into their reviewer-specific `reviewer_forms/*.jsonl` working copy
- do not edit rubric axes, rubric version, or unit identifiers

### Adjudicator

- reviews merged reviewer disagreement after both reviewers finish
- writes the final locked labels into `judge_adjudications.jsonl`
- records short rationale for non-trivial disagreements

## Files To Use

Each reviewer starts from:

- reviewer index:
  `calibration/publication_validation_v1/review_packets/reviewer_indexes/<reviewer>_index.md`
- reviewer assignment sidecar:
  `calibration/publication_validation_v1/review_packets/reviewer_assignments/<reviewer>_publication_review_assignments.jsonl`
- reviewer working copy:
  `calibration/publication_validation_v1/reviewer_forms/<reviewer>_judge_review_forms.jsonl`
- canonical source of blank forms:
  `calibration/publication_validation_v1/judge_review_forms.jsonl`
- truth-manifest lookup:
  `calibration/publication_validation_v1/truth_manifest_lookup.jsonl`
- selected truth manifests:
  `calibration/publication_validation_v1/selected_truth_manifests.jsonl`

Before the full round starts, reviewers should also receive any organizer
clarification about the exact object being scored for each packet if that
object is not already obvious from the reviewer-facing materials.

The adjudicator uses:

- merged forms:
  `calibration/publication_validation_v1/judge_review_forms_merged.jsonl`
- adjudication shells:
  `calibration/publication_validation_v1/judge_adjudications.jsonl`
- adjudication queue:
  `calibration/publication_validation_v1/judge_queue.jsonl`

## Recommended Calibration Pass

Before the full round, both reviewers should score the shared starter units in:

- `calibration/publication_validation_v1/calibration_mini_round.md`

Recommended use:

- both reviewers score only those `6` units first
- the organizer checks whether the scored artifact is clear in practice
- the organizer compares early disagreements and clarifies borderline guidance
- only then should the remaining `54` units proceed

After the starter files come back, the organizer can verify that exactly the
starter rows are complete before telling reviewers to continue:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-review-intake \
  --batch-dir calibration/publication_validation_v1 \
  --stage calibration
```

## Rubric Scale

Use the same four-point anchored ordinal scale for each rubric axis:

- `0`: absent, clearly wrong, or contradicted by the benchmark evidence
- `1`: partially supported or materially incomplete
- `2`: mostly correct, with minor omissions or mild weakness
- `3`: fully compliant relative to the supplied benchmark evidence

Current required axes:

- `evidence_fidelity`
- `traceability`
- `provenance_completeness`
- `writing_structure_compliance`

Reviewer guidance:

- judge only against the supplied benchmark evidence and packet context
- do not reward likely-but-unstated scientific facts
- do not penalize abstracts for lacking literal figure/table citations when
  the packet instead provides concrete quantitative grounding
- use `notes` for ambiguity, evidence gaps, or reasons a score felt close

## Reviewer Workflow

1. Open your reviewer index and work through the assigned packet markdown
   files in order.
2. For each packet, find the matching row in
   your reviewer-specific working copy in
   `calibration/publication_validation_v1/reviewer_forms/` using:
   - `validation_unit_id`
   - your `reviewer_id`
3. If the packet markdown is not sufficient by itself, use
   `truth_manifest_lookup.jsonl` to find the matching
   `truth_manifest_id`, then consult `selected_truth_manifests.jsonl` for the
   frozen assertion text and provenance context tied to that unit.
4. Fill all four `rubric_labels` with `0`-`3` scores.
5. Set `completed` to `true`.
6. Optionally set `confidence` to a `0`-`3` integer if used internally;
   otherwise leave it `null`.
7. Add short `notes` when the case is ambiguous, underspecified, or likely
   to need adjudication.
8. Do not rename fields, remove rows, add axes, or change the rubric
   version.

Return path:

- send back your completed reviewer-specific JSONL copy rather than editing
  the canonical blank master in place
- if the organizer requests a shared calibration pass first, pause after the
  starter units before moving through the rest of the index

Recommended pacing:

- target about `8-10` minutes per unit on the first pass
- flag unusually hard packets in `notes` rather than stalling the batch

## Adjudication Workflow

After both reviewers finish:

First, audit the returned reviewer copies before merge:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-review-intake \
  --batch-dir calibration/publication_validation_v1 \
  --stage full
```

1. Merge reviewer outputs:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli merge-judge-review-forms \
  --inputs calibration/publication_validation_v1/reviewer_forms/reviewer_a_judge_review_forms.jsonl \
           calibration/publication_validation_v1/reviewer_forms/reviewer_b_judge_review_forms.jsonl \
  --output calibration/publication_validation_v1/judge_review_forms_merged.jsonl
```

2. Build the adjudication queue:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli build-judge-adjudication-queue \
  --judge-units calibration/publication_validation_v1/judge_units.jsonl \
  --forms calibration/publication_validation_v1/judge_review_forms_merged.jsonl \
  --adjudications calibration/publication_validation_v1/judge_adjudications.jsonl \
  --reviewers reviewer_a reviewer_b \
  --output calibration/publication_validation_v1/judge_queue.jsonl
```

3. For each queued disagreement, fill the matching row in
   `judge_adjudications.jsonl`:
   - set `final_rubric_labels`
   - set `finalized` to `true`
   - add brief `rationale`

## Post-Annotation Checks

Recompute agreement:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-judge-agreement \
  --judge-units calibration/publication_validation_v1/judge_units.jsonl \
  --forms calibration/publication_validation_v1/judge_review_forms_merged.jsonl \
  --adjudications calibration/publication_validation_v1/judge_adjudications.jsonl \
  --output calibration/publication_validation_v1/judge_agreement.json
```

Refresh publication readiness:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli summarize-publication-readiness \
  --matrix-summary calibration/llm_public_slice_matrix_v1/summary.json \
  --canary-summary calibration/canary_probe_v1_live_hosted_working_set/summary.json \
  --validation-summary calibration/publication_validation_v1/publication_validation_summary.json \
  --agreement-metrics calibration/publication_validation_v1/judge_agreement.json \
  --output calibration/publication_validation_v1/publication_readiness_snapshot.json
```

## Success Condition For This Round

This round is complete when all of the following are true:

- both reviewers have marked every assigned form `completed = true`
- adjudication is finalized for the disputed units
- `judge_agreement.json` exists and reports non-zero comparable items
- `publication_readiness_snapshot.json` has been refreshed with real
  agreement metrics

At that point, the project moves from "frozen batch awaiting review" to
"human-validated slice with measurable agreement."
