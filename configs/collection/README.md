# Collection Configs

This directory stores versioned collection-batch specs for API-backed literature retrieval.

- `collection_v1_2018_present.json`
  - deterministic batch spec for the first `2018-present` broad-stratified collection round
  - PubMed seed retrieval only
  - Europe PMC and Crossref are enrichment-only sources
- `collection_v1_2018_present_queries.jsonl`
  - flattened `ApiQuerySpec` records for the same batch

Recommended workflow:

1. Use the checked-in batch spec as the source of truth.
2. Write raw fetch dumps to `knowledge_base/raw/<batch_id>/`.
3. Merge and enrich candidates before converting them into `MetadataSourceRecord` artifacts.
4. Keep reruns replay-first by reusing raw dumps unless `--refresh` is explicitly supplied.
