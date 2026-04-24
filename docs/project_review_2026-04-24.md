# Project Review 2026-04-24

This ledger tracks the from-scratch project review requested on 2026-04-24.
The goal is to review the repository by category, compare documentation against
actual artifacts and code behavior, fix high-confidence issues as they are
found, and leave unresolved risks explicit instead of implicit.

## Review Method

- Read project claims before code so the implementation can be checked against
  declared goals rather than isolated local assumptions.
- Keep historical handoffs as historical records, but mark misleading current
  status language when it can confuse launch or publication decisions.
- Prefer narrow fixes during review: documentation corrections, regression
  tests, and low-risk hardening before larger refactors.
- Record verification commands and artifact checks as the review progresses.

## Category Plan

| Category | Status | Notes |
| --- | --- | --- |
| Repository map and review taxonomy | Complete | Initial file inventory, dirty tree, docs, source, scripts, validation, and calibration artifacts inspected. |
| Documentation, handoffs, and declared goals | Complete | README, DATA, handoff, transparency, canary, governance, and publication-validation launch docs reviewed against current artifacts. |
| Core data models and serialization contracts | Complete | `models.py`, `io.py`, qualification/release schemas, and compatibility behavior reviewed; high-confidence loader/export fixes landed. |
| CLI and workflow orchestration | Complete | End-to-end command surfaces and file contract consistency reviewed; parser/function contract checks pass. |
| Publication validation and human review dispatch | Complete | Batch construction, packets, reviewer forms, adjudication queue, readiness summaries, and current dispatch artifacts reviewed. |
| Judge workflow and agreement metrics | Complete | Rubric handling, form validation, adjudication, metrics, and failure modes reviewed; numeric rubric hardening landed. |
| Frontier runtime, canary, matrix, and external execution | Complete | Registry, provider identity mapping, matrix summaries, canary coverage, and HPC/local runners reviewed; registry/matrix alias hardening landed. |
| Ingestion, qualification, release, and policy gates | Complete | Split safety, provenance, truth manifests, publication tiers, and leakage controls reviewed; ingestion/release hardening landed. |
| Tests and verification | Complete | Targeted regressions, artifact sanity checks, full compile, and full unittest suite passed. |
| Final prioritized findings and residual risks | Complete | High-confidence fixes landed; remaining risks are launch-process gaps rather than newly found code blockers. |

## Findings

| ID | Severity | Status | Area | Finding | Action |
| --- | --- | --- | --- | --- | --- |
| DOC-001 | Low | Fixed | Handoff | `docs/session_handoff_2026-04-23.md` said seven readiness-gate edge cases but listed eight. | Updated the count to eight. |
| DOC-002 | Medium | Fixed | Current-status docs | README current limitations said the live publication-validation slice still needed to be populated, but `calibration/publication_validation_v1` is populated, packet-complete, and structurally ready. | Updated README to distinguish populated batch readiness from pending human review/adjudication. |
| DOC-003 | Medium | Fixed | Matrix/canary docs | Transparency and canary docs still described Anthropic and Gemini as blocked, but current artifacts include Anthropic coverage and are missing Gemini coverage. | Updated README, transparency card, canary report, and readiness commands to use the hosted-working-set canary artifact. |
| DOC-004 | Low | Fixed | Transparency card | `docs/benchmark_transparency_card.md` said there was no populated judge validation slice without distinguishing blank human adjudication from a populated publication-validation batch. | Updated the limitation to say the batch is populated and packet-complete, while human adjudication/agreement remain pending. |
| DOC-005 | Medium | Fixed | Generated dispatch/docs | The publication-validation dispatch copies and CLI-generated handoff default still pointed readiness refresh commands at the older 3-model OpenAI/DeepSeek canary artifact. | Updated the CLI default, validation protocol, dispatch copies, and workshop draft to point at the hosted-working-set canary artifact. |
| DOC-006 | Low | Accepted | Historical docs | The 2026-04-13 strategic review and handoff still contain older matrix/canary status. | Left unchanged because they are dated historical records, not current launch instructions. |
| MIO-001 | High | Fixed | IO contracts | Human-review, adjudication, and calibration-manifest loaders used Python `bool(...)` for editable boolean fields, so string values like `"false"` or `"0"` could be treated as complete/finalized/enabled. | Added safe boolean parsing for human-review, judge-validation, pilot-review, paper-review, and pilot-calibration loaders with regression coverage. |
| ING-001 | Medium | Fixed | Ingestion | Metadata ingestion used Python `bool(...)` for safety flags, so string false values could incorrectly mark records as pre-2018 exceptions, controlled-access, or small-cell-risk. | Reused the ingestion boolean parser for those fields and added regression coverage. |
| API-001 | Low | Fixed | Package exports | Three public loader functions existed in `io.py` and were imported by `__init__.py`, but were missing from `__all__`. | Added `auto_review_evidence_enrichment_record_from_dict`, `auto_review_evidence_enrichment_audit_report_from_dict`, and `pmc_full_text_fetch_record_from_dict` to `__all__`. |
| API-002 | Low | Fixed | Serialization | `LineageInfo` was the only dataclass without a public `*_from_dict` loader. | Added `lineage_info_from_dict`, exported it, and registered it in `MODEL_LOADERS`. |
| CLI-001 | Low | Fixed | CLI imports | `cli.py` imported `paper_qualification_record_from_dict` twice, making the already-large command module noisier to audit. | Removed the duplicate import. |
| JUD-001 | Medium | Fixed | Judge rubric validation | Completed judge forms and finalized adjudications treated non-finite values such as `"nan"` and out-of-range values such as `4.0` as valid numeric rubric scores. | Centralized judge rubric score parsing so only finite scores in the `0-3` rubric range count as scored, and added regression coverage. |
| JUD-002 | Low | Fixed | Judge adjudication queue | Queue disagreement detection compared raw `repr(...)` values, so equivalent JSON/user-entered scores like `1`, `1.0`, and `"1.0"` could be flagged as reviewer disagreement. | Normalized scored rubric values to floats before distinct-value comparison and added regression coverage. |
| FRT-001 | Medium | Fixed | Frontier registry | Registry `omit_temperature` used Python `bool(...)`, so a human-edited string value `"false"` would omit temperature anyway. | Added safe registry boolean parsing and regression coverage. |
| FRT-002 | Low | Fixed | Matrix provenance | Matrix summary registry lookup matched direct labels but not provider `request_model` aliases, so custom registry labels could lose provenance when summaries reported provider model names. | Added registry alias lookup over `model_label` and `request_model`, with regression coverage. |
| ING-002 | Medium | Fixed | Ingestion | Metadata enum-list fields such as `modality_overlays`, `crossmark_updates`, and `integrity_flags` only accepted actual lists/tuples; comma-, semicolon-, or pipe-separated export strings were silently dropped. | Added delimited string parsing for enum lists and regression coverage for overlays, Crossmark updates, and integrity flags. |
| REL-001 | Medium | Fixed | Release artifacts | Release index/bundle builders did not reject duplicate benchmark-unit ids, extra decisions for unknown units, or decision mapping keys that disagreed with the decision record id. | Added shared release-input validation before index/bundle construction and regression coverage. |
| MIO-002 | Medium | Fixed | IO contracts | Second-pass bool audit found remaining JSON/dict loaders where string false values could still be treated as true for source, metadata, packaging, evidence, report, and progress artifacts. | Replaced remaining loader `bool(data...)` coercions with the shared safe boolean parser and added broad artifact-loader regression coverage. |
| JUD-003 | Medium | Fixed | LLM judge alignment | LLM judgment payloads and judge-output parsing treated string `"false"` as a passing judgment because they used Python truthiness. | Added safe boolean parsing for `overall_pass` in alignment audits and `scripts/llm_judge_eval.py`, with regressions. |
| REC-001 | Low | Fixed | Recovery selection | Auto-review recovery queue records treated string `"false"` as selected. | Added safe boolean parsing for queue-record `selected` and regression coverage. |
| SCO-001 | Medium | Fixed | Deterministic scoring | Citation-specificity scoring missed lowercase `fig. 1` references and mixed-case forbidden pointer tokens such as `Methods_Section`; the smoke script's local summary scorer had the same drift. | Made figure-reference matching and forbidden-pointer detection case-insensitive in package scoring and the smoke script, with regression coverage. |
| COL-001 | Medium | Fixed | Collection enrichment | EuropePMC and Crossref enrichment caught fetch errors but decoded and parsed JSON outside the guarded block, so malformed cached or fetched JSON could crash a collection run instead of marking the candidate with an enrichment error. | Moved decode/JSON parsing inside the guarded block, catch `UnicodeDecodeError` and `json.JSONDecodeError`, and added malformed-JSON regression coverage. |
| AUT-001 | Low | Fixed | Auto-review source bundles | Source-bundle construction accepted paper metadata `abstract` but ignored the common `abstract_text` alias, reducing source completeness and downstream abstract-based inference for records using that field. | Added `abstract_text` fallback handling and regression coverage. |

## Verification Log

- `rg --files`: built initial repository inventory.
- `git status --short`: confirmed dirty worktree with existing tracked and
  untracked changes; review must not revert unrelated work.
- `wc -l README.md DATA.md docs/*.md research/*.md paper/workshop_draft_v0.md validation/human_annotation_protocol.md`:
  scoped documentation size before reading.
- Read `README.md`, `DATA.md`, `pyproject.toml`, `docs/implementation_notes.md`,
  `docs/dataset_card.md`, `docs/session_handoff_2026-04-23.md`,
  `docs/benchmark_transparency_card.md`, `docs/canary_probe_report.md`,
  `docs/release_governance_card.md`, and the top-level
  `calibration/publication_validation_v1` launch/readiness docs.
- Checked `calibration/publication_validation_v1/publication_validation_summary.json`,
  `annotation_hold_audit.json`, `publication_readiness_snapshot.json`,
  `calibration/llm_public_slice_matrix_v1/summary.{json,md}`, and the live
  canary summaries for OpenAI/DeepSeek, Anthropic, and the hosted working set.
- Searched current docs, dispatch copies, validation protocol, workshop draft,
  and CLI defaults for stale `canary_probe_v1_live_openai_deepseek` readiness
  references and updated active references to the hosted-working-set artifact.
- Targeted verification:
  `PYTHONPATH=src python3 -m unittest tests.test_qualification.QualificationTests.test_human_review_string_boolean_flags_are_parsed tests.test_qualification.QualificationTests.test_ingest_metadata_records_parses_string_boolean_flags -v`
  passed.
- Export-contract check found no remaining public `*_from_dict` functions in
  `io.py` missing from package `__all__`.
- Dataclass-loader check found no remaining dataclasses without a matching
  public `*_from_dict` loader.
- CLI parser/function contract check: 88 registered subcommands, 88 analyzed
  command functions, no `args.*` fields used by commands missing from their
  parser definitions.
- `PYTHONPATH=src python3 -m life_science_paperwritingbench.cli --help` and
  representative publication-readiness subcommand help invocations completed
  successfully.
- `PYTHONPATH=src python3 -m life_science_paperwritingbench.cli audit-publication-annotation-hold --batch-dir calibration/publication_validation_v1 --output /tmp/lspwb_publication_hold_audit_check.json --markdown-output /tmp/lspwb_publication_hold_audit_check.md`
  reproduced `ok=true`, `structurally_ready=true`, and
  `awaiting_human_review=true` for the current publication-validation batch.
- Current publication-validation artifact row counts match the expected launch
  contract: 60 selected bundles, 60 judge units, 120 canonical reviewer forms,
  60 adjudication shells, 120 packet manifest rows, and 60 reviewer working
  forms per reviewer.
- Packet path consistency check found zero missing root packet markdown files,
  zero missing dispatch packet markdown files, 60 dispatch assignments per
  reviewer, and 60 dispatch form rows per reviewer.
- Publication validation targeted tests passed after correcting one mistyped
  unittest selector:
  `test_publication_validation_slice_and_readiness_gate`,
  `test_publication_readiness_matches_submitter_runs_by_registry_model_label`,
  `test_publication_readiness_non_numeric_agreement_metrics_fail_closed`,
  `test_publication_readiness_string_boolean_flags_are_parsed`,
  `test_publication_readiness_blocks_partial_matrix_and_canary_coverage`,
  `test_cli_build_publication_validation_slice_and_readiness`,
  `test_cli_build_publication_validation_batch`,
  `test_publication_annotation_packets_and_hold_audit`,
  `test_publication_annotation_hold_audit_detects_missing_packet_pair`,
  `test_cli_build_publication_review_packets_and_audit_hold`,
  `test_cli_build_publication_review_packets_detects_stale_dispatch_forms`,
  and `test_cli_build_publication_review_packets_without_adjudications_file`.
- Judge targeted tests passed:
  `test_completed_judge_forms_require_numeric_required_axes`,
  `test_completed_judge_forms_reject_nonfinite_and_out_of_range_scores`,
  `test_judge_queue_normalizes_equivalent_numeric_scores_for_disagreement`,
  `test_compute_judge_agreement_round_trips_and_hits_perfect_metrics`,
  `test_cli_summarize_judge_agreement`,
  `test_audit_judge_validation_slice_passes_for_ready_units`,
  `test_audit_judge_validation_slice_detects_missing_axes_duplicates_and_missing_bundle`,
  `test_cli_build_and_audit_judge_slice`,
  `test_judge_review_workflow_build_merge_queue_and_finalize`,
  `test_cli_build_and_finalize_judge_review_workflow`,
  `test_cli_build_judge_batch_and_summarize_progress`,
  `test_cli_build_judge_batch_respects_holdout_filter`,
  `test_validate_judge_agreement_thresholds_reports_metric_and_coverage_issues`,
  and `test_compute_judge_agreement_ignores_units_outside_declared_slice`.
- `python3 -m compileall -q src/life_science_paperwritingbench/judge.py src/life_science_paperwritingbench/judgeflow.py src/life_science_paperwritingbench/judge_agreement.py tests/test_qualification.py`
  passed.
- Frontier targeted tests passed:
  `test_frontier_registry_loads_roles_and_vllm_slot`,
  `test_frontier_registry_runtime_overrides_vllm_slot`,
  `test_frontier_runtime_default_model_selection_respects_registry_path`,
  `test_frontier_runtime_default_canary_models_respect_registry_path`,
  `test_frontier_runtime_builds_backend_payloads`,
  `test_frontier_runtime_load_api_keys_strips_inline_shell_comments`,
  `test_llm_matrix_summary_builds_partial_report_with_spread_and_blocked_cell`,
  `test_llm_matrix_summary_excludes_same_family_bias_cells`,
  `test_llm_matrix_summary_matches_registry_by_request_model_alias`,
  `test_llm_matrix_summary_main_writes_summary_files`,
  `test_canary_probe_builds_public_and_control_specs_without_leaking_raw_output`,
  `test_canary_probe_evaluate_response_detects_exact_match_and_distance`,
  `test_canary_probe_main_dry_run_writes_redacted_summary`,
  and `test_canary_probe_allows_vllm_backend_without_api_key`.
- `python3 -m compileall -q src/life_science_paperwritingbench/frontier_runtime.py scripts/llm_matrix_summary.py tests/test_qualification.py`
  passed.
- Frontier artifact sanity check: registry has 11 total models; submitter-role
  labels are `claude-haiku-4-5`, `deepseek-chat`, `gemini-2.5-flash`,
  `gpt-4o-mini`, and `openweight-vllm-submitter`; default canary models are
  `deepseek-chat`, `gpt-4o-mini`, `gemini-2.5-flash`,
  `claude-haiku-4-5`, `claude-sonnet-4-6`, `gpt-5.4-mini`, and
  `gemini-2.5-pro`.
- Current matrix/canary artifacts match the documented state: matrix completed
  `5 / 9` total cells, `4 / 6` official cells, `3` family-bias exclusions,
  and `1` missing cell; hosted-working-set canary requested/completed five
  models, has no exact public/control match, and is missing
  `gemini-2.5-flash` plus `gemini-2.5-pro`.
- Release/split targeted tests passed:
  `test_release_index_is_deterministic_and_skips_excluded_units`,
  `test_release_inputs_reject_duplicate_unknown_and_mismatched_decisions`,
  `test_release_index_enforces_split_safety_on_holdout_buckets`,
  `test_release_index_keeps_same_paper_units_in_same_holdout_bucket`,
  `test_release_bundle_ignores_excluded_units_for_split_safety`,
  `test_release_manifest_bundle_includes_summary`,
  `test_release_manifest_bundle_checksums_match_rendered_artifacts`,
  `test_verify_release_bundle_directory_returns_ok`,
  `test_verify_release_bundle_directory_detects_checksum_mismatch`,
  `test_cross_split_lineage_is_violation`, and
  `test_lineage_dominance_cap_is_violation`.
- Ingestion targeted tests passed:
  `test_ingest_and_normalize_metadata_records_uses_identifier_precedence`,
  `test_ingest_metadata_records_parses_string_boolean_flags`, and
  `test_verify_ingestion_artifacts_flags_precedence_violation`.
- `python3 -m compileall -q src/life_science_paperwritingbench/ingestion.py src/life_science_paperwritingbench/release.py tests/test_qualification.py`
  passed.
- Qualification targeted tests passed after correcting class-qualified unittest
  selectors:
  `test_controlled_access_requires_safe_artifact_inventory_for_p1`,
  `PaperQualificationFlowTests.test_build_packaging_review_priors_and_qualification_records`,
  `PaperQualificationFlowTests.test_build_packaging_review_priors_and_qualification_records_cli`,
  `PaperQualificationFlowTests.test_auto_review_observational_review_ready_without_registry_can_still_reach_shadow`,
  and `PaperQualificationFlowTests.test_auto_review_interventional_without_registry_or_structured_results_stays_stress`.
- `python3 -m compileall -q src scripts tests` passed.
- A wrapped `/bin/zsh -lc "PYTHONPATH=src python3 -m unittest discover -s tests -v"`
  invocation failed before running tests because the local shell tried to invoke
  a missing Xcode Command Line Tools `xcrun` path. The direct Python invocation
  was then used for verification.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed:
  248 tests ran in 14.756 seconds with `OK`.
- Second-pass scans covered stale status strings, remaining risky boolean
  coercions, execution-profile/script contracts, baseline scoring, and scoring
  helper behavior.
- Second-pass targeted tests passed:
  `test_core_artifact_string_boolean_flags_are_parsed`,
  `test_report_artifact_string_boolean_flags_are_parsed`,
  `test_llm_judge_string_false_flags_are_parsed`,
  `test_recovery_queue_string_selected_flag_is_parsed`,
  `test_citation_specificity_credits_real_citations`,
  `test_citation_specificity_zeros_on_forbidden_pointer_tokens`, and related
  existing alignment/scoring tests.
- Second-pass compile passed:
  `python3 -m compileall -q src scripts tests`.
- Second-pass full suite passed:
  `PYTHONPATH=src python3 -m unittest discover -s tests -v` ran 252 tests in
  40.911 seconds with `OK`.
- Third-pass review covered collection fetch/merge/ranking error semantics,
  EuropePMC/Crossref enrichment parsing, evidence-source metadata aliases, and
  auto-review source-bundle inference gates.
- Third-pass targeted collection and auto-review tests passed:
  `test_europepmc_and_crossref_enrichment_update_candidate_fields`,
  `test_crossref_enrichment_tolerates_missing_records`,
  `test_collection_enrichment_tolerates_malformed_json`,
  `test_shortlist_collection_candidates_preserves_per_class_caps_and_metadata`,
  `test_build_auto_review_source_bundles_metadata_only`,
  `test_build_auto_review_source_bundles_accepts_abstract_text_alias`,
  `test_build_auto_review_source_bundles_infers_methods_from_abstract`, and
  `test_build_auto_review_source_bundles_infers_results_from_abstract`.
- Third-pass compile passed:
  `python3 -m compileall -q src scripts tests`.
- Third-pass full suite passed:
  `PYTHONPATH=src python3 -m unittest discover -s tests -v` ran 254 tests in
  44.477 seconds with `OK`.

## Final Review Outcome

The review found no remaining code-level blocker after the fixes recorded
above. The highest-risk issues were all fail-closed/contract problems around
human-editable booleans, judge rubric numeric validation, ingestion export
formats, matrix registry provenance, and release input consistency. Those now
have direct regression coverage.

The current publication-validation batch is structurally ready and packet
complete, but it is still waiting on human review, adjudication, and
post-adjudication agreement/readiness refreshes. This is the main project risk
before any publication-facing release claim.

The current frontier evidence should be described as hosted-working-set
coverage, not complete provider coverage. The matrix/canary artifacts still
need Gemini completion, and any open-weight claims should stay separate until
the VLLM/open-weight path has comparable completed artifacts.

Dated 2026-04-13 handoffs and strategic-review notes remain historical context.
They should not be used as launch instructions without cross-checking this
ledger and the 2026-04-23/2026-04-24 current-state docs.
