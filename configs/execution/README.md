# Execution Profiles

Execution profiles keep heavy replay or blind-eval routing outside the repository source of truth.

Current supported scaffolds:

- `default`: local file-and-CLI batch execution
- `cayuga`: Slurm-oriented profile for the Cayuga environment at `<CAYUGA_ROOT>`

Generate a Cayuga profile:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli write-execution-profile \
  --profile cayuga \
  --repo-root "$PWD" \
  --cayuga-root <CAYUGA_ROOT> \
  --output configs/execution/cayuga_profile.json
```

The generated profile is intentionally scaffold-only:

- benchmark artifacts remain under this repository
- `knowledge_base/` remains the source of truth
- the profile exists to help future replay, batch scoring, and private-holdout wrappers target larger compute safely

You can also generate a scaffold baseline-replay job from the profile:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli write-baseline-replay-job \
  --execution-profile configs/execution/cayuga_profile.json \
  --task-bundles /tmp/task_bundles.jsonl \
  --baseline-kind reference_template \
  --output-dir /tmp/cayuga_baseline_replay \
  --script-output /tmp/cayuga_baseline_replay/run_baseline_replay.sh \
  --spec-output /tmp/cayuga_baseline_replay/baseline_replay_spec.json
```

For shared-registry frontier submitter runs, including Cayuga-hosted vLLM
submitters, write a scaffold job with:

```bash
PYTHONPATH=src python3 -m life_science_paperwritingbench.cli write-frontier-submitter-job \
  --execution-profile configs/execution/cayuga_profile.json \
  --registry-path configs/models/frontier_registry_v1.json \
  --model-label openweight-vllm-submitter \
  --runner-kind agentic \
  --task-source inspection-slice \
  --output-dir /tmp/cayuga_frontier_agentic \
  --job-spec-output /tmp/cayuga_frontier_agentic/job_spec.json \
  --script-output /tmp/cayuga_frontier_agentic/run_frontier_agentic.sh \
  --endpoint-url http://<HOST>:8000/v1/chat/completions \
  --served-model-name <SERVED_MODEL_NAME> \
  --tensor-parallel-size 4 \
  --gpu-count 4
```

Treat `openweight-vllm-submitter` outputs as a separate open-weight track, not
as hosted-frontier matrix cells. See `docs/open_weight_vllm_track.md` before
registering or comparing those artifacts.
