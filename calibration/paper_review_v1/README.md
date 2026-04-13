# paper_review_v1

This directory contains the first paper-level review scaffold for the `180 qualification-ready` papers collected in `collection_v1_2018_present`.

Files:

- `paper_review_entries.jsonl`
  - one row per paper
  - includes candidate study class, claim mode, metadata-hint warnings, and recommended standards
- `scientific_review_forms.jsonl`
  - blank scientific review forms
  - two reviewer slots per paper
- `writing_review_forms.jsonl`
  - blank writing review forms
  - two reviewer slots per paper
- `paper_review_adjudications.jsonl`
  - blank adjudication shells
  - one row per paper
- `paper_packaging_review_priors.jsonl`
  - deterministic packaging-review priors from collection metadata
  - one row per paper
- `paper_packaging_review_priors_summary.json`
  - aggregate packaging-prior summary
- `paper_review_packets.jsonl`
  - reviewer-facing packets combining review entries, paper metadata, and packaging priors
  - sorted by deterministic review priority
- `paper_review_packets_summary.json`
  - packet-level summary including top-priority paper IDs and packaging pass counts
- `workloads/reviewer_a_paper_review_assignments.jsonl`
- `workloads/reviewer_b_paper_review_assignments.jsonl`
  - reviewer-specific workload files
  - each row contains the prioritized packet plus the reviewer-matched scientific and writing forms
- `workloads/paper_review_workload_summary.json`
  - workload summary with assignment counts and top-priority papers per reviewer
- `handoff/reviewer_a_handoff.md`
- `handoff/reviewer_b_handoff.md`
  - reviewer-facing markdown briefs with top-priority starts and workflow notes
- `handoff/reviewer_a_handoff_summary.json`
- `handoff/reviewer_b_handoff_summary.json`
  - reviewer-specific JSON summaries for quick tracking and audit
- `paper_review_queue.jsonl`
  - current queue status for each paper
- `paper_review_progress.json`
  - current review-slot completion summary
- `adjudicated_paper_reviews.jsonl`
  - finalized paper-review records
  - currently empty until adjudications are marked finalized
- `paper_qualification_decisions.jsonl`
  - paper qualification decisions derived from finalized adjudicated reviews plus packaging priors
  - currently empty until adjudications are finalized
- `paper_qualification_decisions_summary.json`
  - summary for qualification-decision coverage
- `paper_review_summary.json`
  - batch summary for coverage and sanity checks

Current scaffold stats:

- total papers: `180`
- study-class balance: `30` per class
- scientific review forms: `360`
- writing review forms: `360`
- metadata-warning papers: `86`
- adjudication shells: `180`
- packaging-review priors: `180`
- review packets: `180`
- reviewer workloads: `360 assignments total`
- reviewer handoff bundles: `2`
- current queue status: `180 awaiting_reviews`
- current qualification decisions: `0`

Suggested next step:

1. Start from `workloads/reviewer_a_paper_review_assignments.jsonl` and `workloads/reviewer_b_paper_review_assignments.jsonl`
2. Use `handoff/reviewer_a_handoff.md` and `handoff/reviewer_b_handoff.md` as the human-readable start point
3. Fill the embedded scientific and writing review forms for each reviewer
4. Export updated reviewer copies back into `scientific_review_forms.jsonl` and `writing_review_forms.jsonl`
5. Run `merge-paper-scientific-forms` and `merge-paper-writing-forms` on uploaded reviewer copies
6. Inspect `paper_review_queue.jsonl` and `paper_review_progress.json`
7. Fill and finalize `paper_review_adjudications.jsonl`
8. Run `finalize-paper-adjudications`
9. Run `build-paper-qualification-decisions`
