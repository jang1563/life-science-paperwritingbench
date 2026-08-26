# Canary Probe Report

## Status

This repo now has a working completion-style canary probe in:

- `scripts/canary_probe.py`

Current artifacts:

- dry run: `calibration/canary_probe_v1_dry_run/summary.md`
- initial live OpenAI/DeepSeek run: `calibration/canary_probe_v1_live_openai_deepseek/summary.md`
- live Anthropic run: `calibration/canary_probe_v1_live_anthropic/summary.md`
- current hosted-working-set run: `calibration/canary_probe_v1_live_hosted_working_set/summary.md`

## Current Hosted-Working-Set Result

Live coverage in the current environment:

- models probed:
  - `deepseek-chat`
  - `gpt-4o-mini`
  - `gpt-5.4-mini`
  - `claude-haiku-4-5`
  - `claude-sonnet-4-6`
- public canaries sampled per model: `1`
- matched unpublished controls sampled per model: `1`
- exact public-canary matches: `0 / 5`
- exact control-canary matches: `0 / 5`

Per-model snapshot:

| model | status | public exact | control exact | min public distance | min control distance |
| --- | --- | ---: | ---: | ---: | ---: |
| `deepseek-chat` | `ok` | `0 / 1` | `0 / 1` | `8` | `8` |
| `gpt-4o-mini` | `ok` | `0 / 1` | `0 / 1` | `18` | `15` |
| `gpt-5.4-mini` | `ok` | `0 / 1` | `0 / 1` | `8` | `8` |
| `claude-haiku-4-5` | `ok` | `0 / 1` | `0 / 1` | `8` | `8` |
| `claude-sonnet-4-6` | `ok` | `0 / 1` | `0 / 1` | `8` | `8` |

Interpretation:

- no exact canary reproduction was observed in the current partial live run
- no exact random-control reproduction was observed either
- this is encouraging, but it is **not** yet a full release-facing contamination check because Gemini coverage is still missing

## Important Caveats

- this probe deliberately writes only redacted artifacts:
  - hashes
  - lengths
  - match outcomes
  - edit distances
- it does **not** write raw canary strings or raw model outputs back into the repo
- current live coverage is partial because Gemini models are still missing from
  the hosted-working-set artifact
- the current live run is therefore a `5-model` probe, not the final
  registry-complete contamination report

## Recommended Next Step

- rerun `scripts/canary_probe.py` after Gemini access is restored
- expand the live run to the full registry-declared production model set
- keep publishing any positive reproduction explicitly rather than hiding it
