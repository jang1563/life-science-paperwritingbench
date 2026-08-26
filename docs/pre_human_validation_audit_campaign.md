# Pre-Human Validation Audit Campaign

## Purpose

This is the work plan for finding errors before any human reviewer sees the
full `publication_validation_v1` batch.

The campaign deliberately precedes target freeze. It assumes that human review
is expensive, hard to redo, and vulnerable to ambiguity once reviewers have seen
the materials.

## Severity

- `P0`: invalidates or likely invalidates the human round; dispatch must stop
- `P1`: must be fixed before dispatch
- `P2`: can proceed only if explicitly documented and accepted
- `P3`: useful cleanup after launch

## Phase 0: Target Suitability Review

Owner output:

- `docs/pre_human_validation_target_review.md`

Questions:

- Is the current batch suitable for benchmark-unit validation?
- Is it suitable for model-output validation?
- Would a two-round hybrid design be stronger?
- What claim will the first human round support?

Exit criteria:

- one target is selected or a rebuild is requested
- reviewer-facing claim language is drafted
- P0 target mismatch findings are closed

## Phase 1: Structural Audit

Commands:

```bash
python3 -m compileall -q src scripts tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check

PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-annotation-hold \
  --batch-dir calibration/publication_validation_v1 \
  --output /tmp/lspwb_publication_hold_audit_check.json \
  --markdown-output /tmp/lspwb_publication_hold_audit_check.md
```

Checks:

- 60 judge units
- 120 reviewer form rows
- 60 reviewer A rows and 60 reviewer B rows
- 60 adjudication shells
- reviewer A/B packet coverage complete
- no duplicate validation-unit, task-bundle, or packet ids
- truth-manifest lookup sidecars present
- canonical blank forms remain blank

P0 examples:

- missing packet pair
- missing reviewer form pair
- duplicate validation-unit id
- reviewer A/B assignment mismatch
- canonical blank forms already completed

## Phase 2: Packet Semantic Audit

Review every packet before dispatch.

Per-unit checklist:

- packet names the validation unit, task bundle, DOI, family, study class, and
  truth manifest
- reviewer can identify the exact object being scored
- evidence pointers and assertion ids are present
- truth-manifest lookup resolves
- selected truth manifest contains enough context for all rubric axes
- authoring constraints match task family
- rubric guidance is not inconsistent with task family
- reviewer A and reviewer B packets are semantically identical apart from
  reviewer id/path
- no model/run/submitter identity is leaked unless intentionally accepted

Output:

- `docs/pre_human_validation_semantic_packet_audit.md`

Status values:

- `ok`
- `clarify_before_dispatch`
- `fix_before_dispatch`
- `exclude_or_rebuild`

P0 examples:

- packet cannot identify a scored object for the selected target
- truth manifest is missing or mismatched
- reviewer A and reviewer B see different substantive evidence

P1 examples:

- ambiguous target wording
- missing evidence pointer that forces reviewer guesswork
- rubric axis impossible to score from materials

## Phase 3: Rubric Red-Team

Stress the four axes before reviewers use them:

- `evidence_fidelity`
- `traceability`
- `provenance_completeness`
- `writing_structure_compliance`

Borderline cases to test:

- evidence is factually correct but provenance cues are missing
- claim is plausible but not present in evidence
- abstract has quantitative grounding but no literal figure/table citation
- Methods-style prose includes Results claims
- source evidence is thin, so the correct action is a low score
- benchmark unit is valid but reviewer packet is hard to use

Output:

- `docs/pre_human_validation_rubric_red_team.md`
- reviewer FAQ entries for recurrent ambiguities

Exit criteria:

- axis definitions are operational
- scores `0`, `1`, `2`, and `3` have examples
- note tags are frozen or explicitly optional

## Phase 4: Methodology Gap Review

Compare this project against benchmark practice from:

- PaperBench
- LAB-Bench
- MedHELM
- HELM
- DeepScholar-Bench
- NLG human-evaluation best-practice literature

Output:

- `docs/pre_human_validation_methodology_gap_review.md`

Questions:

- Is the benchmark taxonomy explicit enough?
- Is the scored object explicit enough?
- Are human and automated judge roles separated?
- Are contamination controls adequate for the claim?
- Are metrics multi-axis rather than a single headline number?
- Are missing provider/open-weight gates separated from human validation?

## Phase 5: Reviewer UX Dry Run

Simulate a reviewer using only the dispatch package.

Tasks:

- open reviewer index
- locate first calibration packet
- locate matching JSONL row
- locate truth manifest through lookup
- fill a mock row in a temp copy
- run calibration-stage intake audit against the temp copy

Output:

- `docs/pre_human_validation_reviewer_ux_dry_run.md`

P0 examples:

- reviewer cannot find the row to edit
- reviewer must infer target from multiple files
- intake audit cannot distinguish calibration-only completion from full-round
  completion

## Phase 6: Target Freeze

Only after Phases 0-5:

- update `calibration/publication_validation_v1/pre_human_review_preflight.md`
- update launch messages if needed
- update reviewer FAQ if created
- rerun structural audit
- rerun compile/tests/diff checks

Target freeze should state one of:

- Target A: benchmark-unit evidence validation
- Target B: model-output section validation
- Target C: staged hybrid validation

## Phase 7: Human Calibration Mini-Round

Send only the 6 shared starter units:

- `calibration/publication_validation_v1/calibration_mini_round.md`

After returned forms:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-review-intake \
  --batch-dir calibration/publication_validation_v1 \
  --stage calibration
```

Review:

- disagreement count
- per-axis disagreements
- notes tags
- missing/ambiguous evidence reports
- time burden

Proceed to the remaining 54 units only if no new P0/P1 issue appears.

## Phase 8: Full Round And Adjudication

After full return:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-review-intake \
  --batch-dir calibration/publication_validation_v1 \
  --stage full
```

Then merge, build adjudication queue, adjudicate, compute agreement, and refresh
publication readiness following `validation/human_annotation_protocol.md`.

## Done Condition

The project is ready for human dispatch only when:

- P0 count is `0`
- P1 count is `0`
- target choice is frozen
- calibration mini-round package is clear
- structural audit passes
- semantic packet audit has no `fix_before_dispatch` or
  `exclude_or_rebuild` entries
- agreement thresholds are predeclared
- final claim boundary still says `research preview` until metrics exist
