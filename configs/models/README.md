# Frontier Model Registry

`frontier_registry_v1.json` is the shared source of truth for:

- submitter model labels used by the LLM runners
- judge model labels used by rubric evaluation
- matrix provenance and judge-policy grouping
- canary probe model definitions

The registry includes three backend types:

- `openai_compatible_api`
- `anthropic_api`
- `vllm_http`

The `openweight-vllm-submitter` slot is deployment-oriented. It can be filled
at runtime with environment variables exported by Cayuga job scaffolds:

- `LSPWB_VLLM_ENDPOINT_URL`
- `LSPWB_VLLM_SERVED_MODEL_NAME`
- `LSPWB_VLLM_MODEL_VERSION_NOTE`

This keeps open-weight deployment details out of the scripts themselves while
preserving one stable model label and one stable artifact contract.

Open-weight / VLLM outputs are a separate track from hosted-frontier outputs.
Use `docs/open_weight_vllm_track.md` for release-facing naming, metadata, and
claim-boundary rules.

The same registry is now also used by the Inspect-facing helpers in
`inspect_evals/life_science_paperwritingbench.py`, so external runners can use
the same model labels and backend metadata as the first-party scripts.
