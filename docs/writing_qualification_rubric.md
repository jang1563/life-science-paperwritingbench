# Writing Qualification Rubric v1

This rubric separates `well written` from `scientifically strong`.

It is designed for life-science source papers that may be:

- scientifically strong but poorly written,
- smoothly written but scientifically weak,
- or strong on both axes.

The scientific benchmark should not collapse those cases into one scalar.

## Qualification Levels

- `W1`
  - strong writing exemplar
  - appropriate for public writing-gold consideration when the paper also satisfies source and packaging requirements
- `W2`
  - usable but not exemplar-quality writing
  - acceptable for shadow analysis, reviewer training, or source-quality contrast sets
- `W3`
  - insufficient as a writing exemplar
  - typically indicates major reporting or narrative problems

## Critical Domains

- `abstract_result_alignment`
  - the abstract accurately reflects the main findings, effect directions, and scope
- `narrative_coherence`
  - the paper moves logically from problem to method to results to claims
- `methods_clarity`
  - the methods section is concrete enough that a domain reader can understand what was done without guessing
- `figure_table_grounding`
  - figures and tables are correctly narrated in the text and the narrative does not drift away from the displayed evidence
- `limitation_uncertainty_disclosure`
  - caveats, uncertainty, and scope boundaries are stated rather than hidden

## Supporting Domains

- `title_scope_alignment`
  - the title does not oversell beyond what the paper actually establishes
- `citation_contextualization`
  - related work and citations are used to situate claims rather than decorate them

## Decision Rules

- `W3`
  - any critical domain fails
  - more than one critical domain is borderline
  - or required writing review fields are missing
- `W1`
  - all critical domains pass
  - all supporting domains pass
- `W2`
  - all remaining non-failing cases

## Operational Guidance

- `W1` is intentionally strict.
- top venue or journal prestige is not enough for `W1`.
- open peer review is not a direct writing score input.
- `public_writing_eligible` should only be `True` when:
  - paper candidate tier is `public_gold_candidate`
  - and writing qualification is `W1`

## Reviewer Notes

- Reviewers should score writing quality from the paper as written, not from their estimate of the underlying science.
- If the science is weak but the prose is polished, mark the writing honestly and let scientific qualification reject the paper separately.
- If the science is strong but the prose is muddy, keep the paper available for source curation while marking writing below exemplar level.
