# Pre-Human Validation Semantic Packet Audit

## Purpose

This audit records the Phase 2 packet-level review before any human reviewer
sees the `publication_validation_v1` materials.

Human dispatch remains held. The review target is not frozen. This document is
intended to catch packet, rubric, and sidecar ambiguity while the batch is still
cheap to regenerate or patch.

## Scope

Audited artifacts:

- `calibration/publication_validation_v1/judge_units.jsonl`
- `calibration/publication_validation_v1/selected_task_bundles.jsonl`
- `calibration/publication_validation_v1/truth_manifest_lookup.jsonl`
- `calibration/publication_validation_v1/selected_truth_manifests.jsonl`
- `calibration/publication_validation_v1/review_packets/packet_manifest.jsonl`
- `calibration/publication_validation_v1/review_packets/packets/reviewer_a/*.md`
- `calibration/publication_validation_v1/review_packets/packets/reviewer_b/*.md`
- `calibration/publication_validation_v1/reviewer_forms/reviewer_a_judge_review_forms.jsonl`
- `calibration/publication_validation_v1/reviewer_forms/reviewer_b_judge_review_forms.jsonl`

Manual spot checks included representative reviewer A/B packet pairs and the
lowest-context unit found by the automated scan.

## Automated Coverage

| Check | Observed | Interpretation |
| --- | ---: | --- |
| Judge units | 60 | Expected count present |
| Selected task bundles | 60 | One selected bundle per unit |
| Truth-manifest lookup rows | 60 | One lookup row per unit |
| Selected truth manifests | 49 | Expected reuse across units; not a deficit |
| Packet manifest rows | 120 | Reviewer A/B packet rows complete |
| Reviewer A forms | 60 | Expected reviewer-specific working copy present |
| Reviewer B forms | 60 | Expected reviewer-specific working copy present |
| P0/P1 structural linkage issues | 0 | Unit, packet, lookup, and form linkage is structurally intact |
| Unit assertion-count range | 3-9 | Thin edge cases exist |
| Unit evidence-item range | 1-3 | Thin edge cases exist |
| Truth-manifest assertion-count range | 3-9 | Mirrors selected unit range |

Study-class coverage remains balanced enough for a calibration batch:

| Study class | Units |
| --- | ---: |
| `animal_preclinical` | 12 |
| `human_interventional` | 12 |
| `human_observational` | 9 |
| `mechanistic_experimental` | 9 |
| `methods_resource` | 9 |
| `systematic_review_meta_analysis` | 9 |

Task-family coverage is balanced:

| Task family | Units |
| --- | ---: |
| `abstract_from_evidence` | 20 |
| `methods_to_text` | 20 |
| `results_to_text` | 20 |

## Findings

| ID | Severity | Status | Finding | Risk | Required action before dispatch |
| --- | --- | --- | --- | --- | --- |
| `SPK-001` | `P1` | Open | All 120 packet markdown files point reviewers at canonical `judge_review_forms.jsonl` rather than the reviewer-specific working copy under `reviewer_forms/`. | Reviewers may edit or return the wrong JSONL, while the protocol expects `reviewer_forms/reviewer_a_judge_review_forms.jsonl` and `reviewer_forms/reviewer_b_judge_review_forms.jsonl`. | Regenerate or patch packets so reviewer A/B packets name their own `reviewer_forms/<reviewer>_judge_review_forms.jsonl` sidecar. Keep canonical `judge_review_forms.jsonl` blank as the frozen source template. |
| `SPK-002` | `P1` | Open | All 120 packets use rubric wording such as "eventual section" rather than the selected scored object. | Reviewers may infer they are judging an unseen or future model-generated section instead of the frozen benchmark unit and truth-manifest evidence. | Replace reviewer-facing wording with target-specific language after the target is frozen. If Target A is selected, say the round scores the frozen benchmark unit against the linked truth-manifest evidence. |
| `SPK-003` | `P1` | Open | Packets do not contain an explicit `Scored Object` block. | The target must be reconstructed from surrounding packet sections and launch docs, which is fragile for human review. | Add a short, repeated `Scored Object` section to every packet and reviewer index. |
| `SPK-004` | `P1` | Open | Packet `Scoring Profile` rubric axes differ from the actual reviewer form axes. The packets show family-specific axes such as `methods_specificity`, `results_grounding`, or `abstract_coverage`; the reviewer forms use `evidence_fidelity`, `traceability`, `provenance_completeness`, and `writing_structure_compliance`. | Reviewers may score against the wrong axes or treat task-generation profiles as human-review rubric fields. | Either remove `Scoring Profile.rubric_axes` from reviewer packets, or relabel it as a task-generation profile and place the actual human-review axes beside the form instructions. |
| `SPK-005` | `P2` | Needs decision | Unit `JV:TB:BU:EUAUTO:22F7B605D96A` is the thinnest observed unit, with one evidence item and three assertions from `TM:13C68909DC37`. | The unit may be valid, but it gives reviewers little context for provenance, traceability, and writing-structure judgments. | Manually decide whether to keep it as a thin-evidence calibration edge case, replace it, or flag it in reviewer notes. |
| `SPK-006` | `P2` | Documented | The selected batch has 49 selected truth manifests for 60 units because several truth manifests are reused across units. | Reuse is not structurally wrong, but it can be mistaken for missing truth manifests during later review. | Keep the reuse documented and ensure any future audit treats manifest reuse separately from missing lookup rows. |

## Representative Manual Reads

The representative reviewer A/B pair for
`JV:TB:BU:EUAUTO:1CA35667BC48` is substantively symmetric: reviewer identity
and path differ, but evidence, assertions, constraints, and scoring profile are
the same. This supports the structural audit's A/B parity conclusion.

The lowest-context packet,
`review_packets/packets/reviewer_a/jv_tb_bu_euauto_22f7b605d96a.md`, is not
broken, but it is thin. Its selected truth manifest has one evidence item
(`abstract_section`) and three assertion texts. That makes it a useful stress
case only if the reviewer guidance explicitly tells reviewers that thin
evidence can legitimately lead to low or cautious rubric scores.

## Target Implication

Target A, benchmark-unit evidence validation, remains the most plausible target
for the current batch. The packet content already exposes validation units,
truth manifests, evidence snippets, assertion ids, authoring constraints, and
reviewer-specific forms.

Target A is not yet dispatch-ready because reviewer-facing language still
mixes benchmark-unit validation, future section wording, and task-generation
axis labels. These are fixable packet/template issues, not evidence that the
entire batch must be discarded.

Target B, model-output section validation, remains unsuitable for this batch as
currently packeted because the packets do not expose exact generated candidate
sections as the scored object.

## Recommended Fix Before Phase 3

Patch the packet-generation source and regenerate the dispatch materials with
these reviewer-visible additions:

```markdown
## Scored Object

This round scores the frozen benchmark unit against the linked frozen
truth-manifest evidence. It does not score a model-generated section.

## Reviewer Form

Use `reviewer_forms/<reviewer>_judge_review_forms.jsonl` and update only the
row matching this `validation_unit_id` and `reviewer_id`.

## Human-Review Axes

- `evidence_fidelity`
- `traceability`
- `provenance_completeness`
- `writing_structure_compliance`
```

Then rerun the semantic audit and start Phase 3 rubric red-team only after
`SPK-001` through `SPK-004` are closed.

## Dispatch Decision

Do not dispatch the calibration mini-round yet.

The batch is structurally coherent, but reviewer-facing packet semantics are
not yet clean enough for one-shot human validation.
