#!/usr/bin/env python3
"""Run an API-backed writer -> critic -> reviser loop over public task bundles.

This script is the first ScholarPeer-inspired agentic baseline for the repo.
It deliberately avoids touching the package's deterministic baseline lane:

- package `run-baseline` remains deterministic replay only
- `SubmissionRecord` remains unchanged
- draft / critique / revision traces are written as sidecar artifacts

The final output of each task is still written as a normal `SubmissionRecord`
so it can be scored and judged by the existing package and scripts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from life_science_paperwritingbench.baselines import evaluate_submissions  # noqa: E402
from life_science_paperwritingbench.io import (  # noqa: E402
    auto_review_source_bundle_from_dict,
    task_bundle_from_dict,
    write_jsonl,
)
from life_science_paperwritingbench.models import (  # noqa: E402
    BaselineRunSpec,
    SubmissionRecord,
)
from life_science_paperwritingbench.policy import BaselineKind  # noqa: E402
from life_science_paperwritingbench.scoring import citation_specificity  # noqa: E402


PROVIDERS: Dict[str, Dict[str, Any]] = {
    "deepseek-chat": {
        "endpoint": "https://api.deepseek.com/chat/completions",
        "api_key_env": "DEEPSEEK_API_KEY",
        "request_model": "deepseek-chat",
        "flavor": "openai",
    },
    "gemini-2.5-flash": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key_env": "GEMINI_API_KEY",
        "request_model": "gemini-2.5-flash",
        "flavor": "openai",
    },
    "gpt-4o-mini": {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "request_model": "gpt-4o-mini",
        "flavor": "openai",
    },
    "claude-haiku-4-5": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "request_model": "claude-haiku-4-5",
        "flavor": "anthropic",
    },
}

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1200
CRITIC_TEMPERATURE = 0.0
CRITIC_MAX_TOKENS_FLOOR = 1800
WRITER_PROMPT_VERSION = "agentic-writer-v6"
CRITIC_PROMPT_VERSION = "agentic-critic-v3"
REVISER_PROMPT_VERSION = "agentic-reviser-v7"
SELECTION_POLICY_VERSION = "non_regressive_det_then_citation_v1"
REVISION_ROUNDS = 1
CRITIQUE_KEYS: Tuple[str, ...] = (
    "structure_issues",
    "grounding_gaps",
    "fidelity_risks",
    "family_specific_gaps",
    "hallucination_risks",
    "revision_instructions",
)

DEFAULT_TASK_BUNDLE_IDS: Sequence[str] = (
    "TB:BU:EUAUTO:0647BFACA729",
    "TB:BU:EUAUTO:DE9706E77A3C",
    "TB:BU:EUAUTO:EFABE066E1CC",
)

KB_ROOT = REPO_ROOT / "knowledge_base"
TASK_BUNDLES_PATH = (
    KB_ROOT
    / "released/collection_v1_2018_present/auto_review_shadow_v10/shadow_candidate_task_bundles_public.jsonl"
)
SOURCE_BUNDLES_PATH = (
    KB_ROOT
    / "enriched/collection_v1_2018_present/auto_review/source_bundles_full180_enriched_v16.jsonl"
)
INSPECTION_SLICE_PATH = (
    KB_ROOT
    / "released/collection_v1_2018_present/auto_review_shadow_v10/shadow_public_inspection_v11.jsonl"
)
OUTPUT_DIR_SMOKE = REPO_ROOT / "calibration/llm_agentic_smoke_v1"
OUTPUT_DIR_SLICE = REPO_ROOT / "calibration/llm_agentic_public_slice_v1"

TASK_FAMILY_TO_TARGET: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "methods_to_text": ("Methods", ("abstract_text", "results_text", "figure_captions", "table_snippets")),
    "results_to_text": ("Results", ("abstract_text", "methods_text", "figure_captions", "table_snippets")),
    "abstract_from_evidence": ("Abstract", ("methods_text", "results_text", "figure_captions", "table_snippets")),
}


def load_api_keys(path: Path) -> Dict[str, str]:
    keys: Dict[str, str] = {}
    if not path.exists():
        return keys
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        keys[name.strip()] = value.strip().strip('"').strip("'")
    return keys


def load_task_bundles(path: Path) -> List[Any]:
    bundles = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                bundles.append(task_bundle_from_dict(json.loads(line)))
    return bundles


def load_source_bundles(path: Path) -> Dict[str, Any]:
    bundles: Dict[str, Any] = {}
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            bundles[record["paper_id"]] = auto_review_source_bundle_from_dict(record)
    return bundles


def _load_inspection_slice_bundle_ids(path: Path) -> List[str]:
    ids: List[str] = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("task_bundle_id"):
                ids.append(entry["task_bundle_id"])
    return ids


def _clip(text: str, limit: int = 6000) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_list(items: Sequence[str], limit_each: int = 800, max_items: int = 8) -> str:
    if not items:
        return "(none provided)"
    lines: List[str] = []
    for idx, item in enumerate(items[:max_items], start=1):
        lines.append(f"{idx}. {_clip(item, limit_each)}")
    return "\n".join(lines)


def build_evidence_block(task_family_value: str, source_bundle) -> str:
    _, include_fields = TASK_FAMILY_TO_TARGET[task_family_value]
    sections: List[Tuple[str, str]] = []
    if "abstract_text" in include_fields and source_bundle.abstract_text:
        sections.append(("Abstract", _clip(source_bundle.abstract_text)))
    if "methods_text" in include_fields and source_bundle.methods_text:
        sections.append(("Methods", _clip(source_bundle.methods_text)))
    if "results_text" in include_fields and source_bundle.results_text:
        sections.append(("Results", _clip(source_bundle.results_text)))
    if "figure_captions" in include_fields and source_bundle.figure_captions:
        sections.append(("Figure captions", _format_list(source_bundle.figure_captions)))
    if "table_snippets" in include_fields and source_bundle.table_snippets:
        sections.append(("Table snippets", _format_list(source_bundle.table_snippets)))
    return "\n\n".join(f"## {title}\n{content}" for title, content in sections)


def build_writer_prompt(task_bundle, source_bundle, paper_title: str) -> str:
    task_family_value = task_bundle.task_family.value
    section_title, _ = TASK_FAMILY_TO_TARGET[task_family_value]
    evidence_block = build_evidence_block(task_family_value, source_bundle)

    if task_family_value == "abstract_from_evidence":
        length_guidance = "Use 150-300 words. Abstracts should be compact."
        citation_guidance = (
            "Abstracts do NOT cite figure or table numbers. Instead, name the specific entities, "
            "sample sizes, p-values, effect sizes, and accession identifiers as they appear in the "
            "evidence. Do not write 'as shown in Fig. 1' in an abstract."
        )
    else:
        length_guidance = "Use 200-400 words."
        citation_guidance = (
            "Cite specific figures and tables from the evidence using the exact label as it appears "
            "(e.g. 'Fig. 1', 'Figure 2B', 'Table 3'). Cite accession identifiers, trial-registry IDs, "
            "or repository URLs when they appear in the evidence. Quote quantitative values exactly "
            "as given (sample sizes, p-values, fold changes, time points, organism strains)."
        )

    family_scope_guidance = (
        "Summarize study setup and the main supported findings compactly. Do not introduce exact medians, "
        "cutoffs, matching ratios, calipers, or subgroup statistics unless they are explicitly visible in the evidence."
        if task_family_value == "abstract_from_evidence"
        else (
            "Write a true Methods section: describe cohorts, interventions, measurements, assays, and analyses only. "
            "Do NOT include observed outcomes, comparative findings, response rates, odds ratios, hazard ratios, "
            "effect sizes, subgroup results, or significance claims unless they are part of the protocol or sample allocation."
            if task_family_value == "methods_to_text"
            else "Write a true Results section: report findings only. Preserve distinctions like added-vs-total counts, "
            "pre-matching vs post-matching analyses, and exclusion-vs-inclusion criteria exactly as stated in the evidence; "
            "do not derive totals, invert criteria, or restate broad methods details as results."
        )
    )

    return f"""You are a biomedical scientific-writing assistant. Draft the "{section_title}" section of a research paper using ONLY the evidence provided below.

Hard requirements:
- Begin with a heading line that is exactly: {section_title}
- {length_guidance}
- Ground every substantive claim in a specific piece of the evidence.
- {citation_guidance}
- {family_scope_guidance}
- Use exact numbers, identifiers, assay names, software/tool names, registry IDs, panel labels, and model versions ONLY when they are explicitly visible in the evidence.
- If an exact detail is only implied by a cited table, figure, or caption whose relevant contents are not shown, omit it or generalize it rather than inventing it.
- Preserve grounded traceability anchors that are explicitly visible in the evidence, such as figure/table labels, p-values, sample sizes, time points, accessions, and registry IDs.
- If a detail is not in the evidence, state that explicitly rather than inventing it. Do not speculate.
- Do not copy sentences verbatim from the evidence; paraphrase while preserving specific values and entities.
- Do not add labels or preambles such as `Evidence basis:`, `This section is based on...`, or similar process notes.
- Do not narrate evidence limitations with sentences like `the evidence does not specify...`; simply omit unsupported details.
- Do not use process-language phrases such as `evidence-supported findings`, `evidence-guided workflow`, or similar meta-commentary in the final prose.

Forbidden patterns (these are automatic quality failures — do NOT do any of them):
- Inventing numerical values, p-values, sample sizes, organism names, or citations that are not in the evidence.
- Citing placeholder pointer labels like "methods_section", "abstract_section", "results_section", or "section_text". These are internal artifact names; they are not real scientific citations and must never appear in the output.
- Self-referential meta-commentary such as "this abstract" or "the methods_section of this paper".

Paper context:
- Paper title: {paper_title}
- Task family: {task_family_value}
- Study class: {task_bundle.study_class.value}
- Claim mode: {task_bundle.claim_mode.value}

Evidence:

{evidence_block}

Write the "{section_title}" section now, starting with the required heading line and satisfying all requirements."""


def _critic_family_instruction(task_family_value: str) -> str:
    if task_family_value == "abstract_from_evidence":
        return (
            "For abstract_from_evidence: optimize for structure, evidence grounding, factual fidelity, "
            "quantitative specificity, and hallucination avoidance. Never ask for figure or table "
            "citations in the abstract. Instead, prefer concrete sample sizes, p-values, effect sizes, "
            "accessions, organism names, and similarly specific grounded details when they are present. "
            "Reject exact medians, cutoffs, calipers, matching ratios, subgroup counts, odds ratios, or "
            "other exact values unless they are directly visible in the provided evidence. Preserve "
            "supported quantitative anchors that are explicitly stated."
        )
    if task_family_value == "methods_to_text":
        return (
            "For methods_to_text: optimize for structure, evidence grounding, factual fidelity, citation "
            "specificity, and hallucination avoidance. Ask for exact figure/table labels, accession "
            "identifiers, registry IDs, repository URLs, and quantitative details only when the evidence "
            "supports them. Reject results leakage: response rates, outcome counts, comparative findings, "
            "significance claims, odds ratios, hazard ratios, effect sizes, and subgroup outcomes belong in Results "
            "unless they explicitly define protocol arms or sample allocation. Reject invented procedural embellishments "
            "such as unshown assay brands, software names, tool versions, calipers, registry IDs, or platform details. "
            "Preserve grounded figure/table labels, cohort sizes, time points, and assay names when they are explicitly supported. "
            "If a grounded figure/table label anchors eligibility, follow-up timing, sample disposition, assays, or protocol structure, "
            "keep that label and remove only the leaky result claim around it. Prefer reframing grounded citations into procedural "
            "sentences rather than deleting them outright."
        )
    if task_family_value == "results_to_text":
        return (
            "For results_to_text: optimize for structure, evidence grounding, factual fidelity, citation "
            "specificity, and hallucination avoidance. Ask for exact figure/table labels, accession "
            "identifiers, registry IDs, repository URLs, and quantitative details only when the evidence supports them. "
            "Reject logical inversions, arithmetic-derived totals, and conflations such as added-vs-total counts, "
            "inclusion-vs-exclusion criteria, or pre-matching vs post-matching results."
        )
    return (
        f"For {task_family_value}: optimize for structure, evidence grounding, factual fidelity, citation "
        "specificity, and hallucination avoidance. Ask for exact figure/table labels, accession "
        "identifiers, registry IDs, repository URLs, and quantitative details when the evidence supports them."
    )


def build_critic_prompt(task_bundle, source_bundle, paper_title: str, draft_output_text: str) -> str:
    task_family_value = task_bundle.task_family.value
    section_title, _ = TASK_FAMILY_TO_TARGET[task_family_value]
    evidence_block = build_evidence_block(task_family_value, source_bundle)
    schema_block = json.dumps({key: ["<issue>"] for key in CRITIQUE_KEYS}, indent=2)

    return f"""You are a strict biomedical writing critic reviewing a generated "{section_title}" section against the provided evidence.

Your task is to diagnose only the issues that matter for one high-quality revision pass.

Family-specific policy:
{_critic_family_instruction(task_family_value)}

General policy:
- Use only the evidence shown below.
- Flag unsupported claims, factual mismatches, weak grounding, missing specificity, and possible hallucinations.
- Treat unsupported exact specifics as highest-priority problems: numbers, sample counts, medians, cutoffs, OR/HR values, registry IDs, DOIs, assay names, software names, tool versions, and panel labels.
- If an exact detail is not explicitly visible in the evidence, tell the reviser to remove it or replace it with a more general grounded statement.
- Do not accept values inferred from unseen table rows, omitted figure panels, or outside domain knowledge.
- Do not ask the reviser to delete grounded traceability anchors that are explicitly supported, such as figure/table labels, p-values, sample sizes, time points, accessions, or registry IDs.
- Keep each list concise and actionable.
- Return at most 3 short items per list and keep each item to a single sentence.
- Keep the full JSON compact enough to fit comfortably within a short revision pass.
- If a category has no issues, return an empty list.
- `revision_instructions` must contain concrete rewrite actions for the reviser.
- Respond with JSON only. No prose before or after. No markdown fences.

Paper context:
- Paper title: {paper_title}
- Task family: {task_family_value}
- Study class: {task_bundle.study_class.value}
- Claim mode: {task_bundle.claim_mode.value}

Evidence:

{evidence_block}

Draft to critique:

{draft_output_text}

Return exactly one JSON object matching this schema:

{schema_block}"""


def build_reviser_prompt(task_bundle, source_bundle, paper_title: str, draft_output_text: str, critique_payload: Mapping[str, Sequence[str]]) -> str:
    task_family_value = task_bundle.task_family.value
    section_title, _ = TASK_FAMILY_TO_TARGET[task_family_value]
    evidence_block = build_evidence_block(task_family_value, source_bundle)
    critique_json = json.dumps(critique_payload, indent=2)

    if task_family_value == "abstract_from_evidence":
        family_revision_rule = (
            "Do not add figure or table citations. Improve quantitative specificity only when the evidence "
            "directly supports it, and preserve supported p-values, sample sizes, and other quantitative anchors."
        )
    elif task_family_value == "methods_to_text":
        family_revision_rule = (
            "Keep the section procedural. Remove result-style claims, outcome counts, significance claims, "
            "and comparative findings unless they explicitly define the protocol or sample allocation. "
            "Only keep assay names, software names, registry IDs, and platform details when they are directly stated in the evidence. "
            "Preserve grounded figure/table labels, cohort sizes, time points, and named assays that are explicitly supported. "
            "If critique removes a leaky sentence that contains a grounded figure/table label, salvage the supported label by attaching "
            "it to a procedural sentence rather than deleting it outright."
        )
    elif task_family_value == "results_to_text":
        family_revision_rule = (
            "Keep the section result-focused. Preserve denominators, totals, and category definitions exactly as stated; "
            "do not derive totals, invert criteria, or blend pre-analysis and post-analysis cohorts. Preserve supported "
            "quantitative anchors and figure/table labels while removing unsupported specifics."
        )
    else:
        family_revision_rule = (
            "When supported by the evidence, improve citation specificity using exact figure/table labels, "
            "accessions, registry identifiers, repository URLs, and quantitative values."
        )

    return f"""You are revising a biomedical "{section_title}" section after critique.

Revise the draft exactly once using ONLY:
- the original evidence
- the draft
- the structured critique

Hard rules:
- Begin with the heading line exactly: {section_title}
- Preserve supported details from the draft when they are correct.
- Remove or rewrite unsupported, vague, or inaccurate claims.
- Do not introduce any new facts that are not grounded in the evidence.
- {family_revision_rule}
- When critique flags an unsupported exact detail, remove it or replace it with a more general grounded statement; never swap in a different unsupported exact detail.
- Remove any preamble or meta-commentary such as `Evidence basis:` or `the evidence does not specify...`.
- Remove process-language phrases such as `evidence-supported findings`, `evidence-guided workflow`, or similar meta-commentary.
- Do not mention the critique, review process, or revision process in the final output.
- Output only the revised section text, not JSON.

Paper context:
- Paper title: {paper_title}
- Task family: {task_family_value}
- Study class: {task_bundle.study_class.value}
- Claim mode: {task_bundle.claim_mode.value}

Evidence:

{evidence_block}

Draft:

{draft_output_text}

Structured critique:

{critique_json}

Write the revised "{section_title}" section now."""


def call_openai_compatible(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, timeout: int = 120) -> Dict[str, Any]:
    payload = {
        "model": provider["request_model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    payload[provider.get("token_param", "max_tokens")] = max_tokens
    request = urllib.request.Request(
        provider["endpoint"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        body = response.read()
    decoded = json.loads(body)
    usage = decoded.get("usage", {}) or {}
    return {
        "output_text": str(decoded["choices"][0]["message"]["content"]).strip(),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        },
        "raw": decoded,
    }


def call_anthropic(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, timeout: int = 120) -> Dict[str, Any]:
    payload = {
        "model": provider["request_model"],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        provider["endpoint"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        body = response.read()
    decoded = json.loads(body)
    output_text = "".join(
        part.get("text", "")
        for part in decoded.get("content", [])
        if isinstance(part, dict) and part.get("type") == "text"
    )
    usage = decoded.get("usage", {}) or {}
    prompt_tokens = usage.get("input_tokens")
    completion_tokens = usage.get("output_tokens")
    total_tokens = None
    if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
        total_tokens = prompt_tokens + completion_tokens
    return {
        "output_text": output_text.strip(),
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "raw": decoded,
    }


def call_llm(prompt: str, *, provider: Mapping[str, Any], api_key: str, temperature: float, max_tokens: int, timeout: int = 120) -> Dict[str, Any]:
    fn = call_anthropic if provider.get("flavor") == "anthropic" else call_openai_compatible
    return fn(
        prompt,
        provider=provider,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


def _error_message(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            body = ""
        body = re.sub(r"\s+", " ", body)
        if body:
            if len(body) > 500:
                body = body[:500] + "..."
            return f"{exc}; body={body}"
    return str(exc)


def call_llm_with_retry(
    prompt: str,
    *,
    provider: Mapping[str, Any],
    api_key: str,
    temperature: float,
    max_tokens: int,
    attempts: int = 3,
    backoff_seconds: float = 2.0,
) -> Dict[str, Any]:
    last_exc: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            return call_llm(
                prompt,
                provider=provider,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, socket.timeout) as exc:
            last_exc = exc
            if attempt == attempts:
                break
            sleep_for = backoff_seconds * (2 ** (attempt - 1))
            print(
                f"    attempt {attempt} failed ({_error_message(exc)}); sleeping {sleep_for:.1f}s",
                file=sys.stderr,
            )
            time.sleep(sleep_for)
    assert last_exc is not None
    raise RuntimeError(_error_message(last_exc)) from last_exc


def extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    if not cleaned.lstrip().startswith("{"):
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first != -1 and last != -1 and last > first:
            cleaned = cleaned[first : last + 1]
    return json.loads(cleaned)


def blank_critique_payload(message: str) -> Dict[str, List[str]]:
    return {
        "structure_issues": [],
        "grounding_gaps": [message],
        "fidelity_risks": [message],
        "family_specific_gaps": [message],
        "hallucination_risks": [message],
        "revision_instructions": [
            "Conservatively revise the draft: remove unsupported claims, preserve grounded details, and do not add new facts.",
        ],
    }


def parse_critique_output(text: str) -> Tuple[Dict[str, List[str]], Optional[str]]:
    try:
        payload = extract_json_object(text)
    except (json.JSONDecodeError, ValueError) as exc:
        return blank_critique_payload(f"critic output did not parse as JSON: {exc}"), str(exc)

    normalized: Dict[str, List[str]] = {}
    for key in CRITIQUE_KEYS:
        raw = payload.get(key)
        if not isinstance(raw, list):
            return blank_critique_payload(f"critic output missing required list field: {key}"), f"missing_or_invalid:{key}"
        normalized[key] = [str(item).strip() for item in raw if str(item).strip()]

    extra_keys = [key for key in payload if key not in CRITIQUE_KEYS]
    if extra_keys:
        return blank_critique_payload("critic output included unexpected fields"), "unexpected_fields"

    return normalized, None


def _remove_markdown_fences(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:\w+)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    return cleaned.strip()


def _remove_meta_process_phrases(body: str) -> str:
    cleaned = body
    cleaned, leading_phrase_removed = re.subn(
        r"^\s*In this evidence-guided workflow,\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    if leading_phrase_removed:
        cleaned = re.sub(r"^([a-z])", lambda match: match.group(1).upper(), cleaned, count=1)

    replacements: Sequence[Tuple[str, str]] = (
        (r"\bTogether, these evidence-supported findings\b", "Together, these findings"),
        (r"\bTogether, these evidence-supported results\b", "Together, these results"),
        (r"\bThese evidence-supported findings\b", "These findings"),
        (r"\bThese evidence-supported results\b", "These results"),
        (r"\bevidence-guided workflow\b", "workflow"),
    )
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def normalize_section_output(task_family_value: str, text: str) -> str:
    section_title, _ = TASK_FAMILY_TO_TARGET[task_family_value]
    cleaned = _remove_markdown_fences(text)
    if not cleaned:
        return section_title

    lines = cleaned.splitlines()
    if lines and lines[0].strip().lower() == section_title.lower():
        body = "\n".join(lines[1:]).strip()
    else:
        body = cleaned

    body = re.sub(r"^\s*Evidence basis:\s*[^\n]*\n*", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    body = _remove_meta_process_phrases(body)

    if not body:
        return section_title
    return f"{section_title}\n\n{body.strip()}"


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:12].upper()}"


def _fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_submission_record(task_bundle_id: str, producer_id: str, output_text: str, config_fingerprint_sha256: str) -> SubmissionRecord:
    return SubmissionRecord(
        submission_id=_stable_id(
            "SUB",
            {
                "task_bundle_id": task_bundle_id,
                "producer_id": producer_id,
            },
        ),
        task_bundle_id=task_bundle_id,
        source="llm",
        producer_id=producer_id,
        output_text=output_text,
        config_fingerprint_sha256=config_fingerprint_sha256,
    )


def build_baseline_run_spec(
    task_bundle_ids: Sequence[str],
    producer_id: str,
    *,
    model: str,
    request_model: str,
    temperature: float,
    task_source: str,
    replay_verified: bool,
) -> BaselineRunSpec:
    config = {
        "baseline_kind": BaselineKind.MULTI_AGENT_ORCHESTRATION.value,
        "task_bundle_ids": tuple(task_bundle_ids),
        "producer_id": producer_id,
        "model": model,
        "request_model": request_model,
        "temperature": temperature,
        "task_source": task_source,
        "writer_prompt_version": WRITER_PROMPT_VERSION,
        "critic_prompt_version": CRITIC_PROMPT_VERSION,
        "reviser_prompt_version": REVISER_PROMPT_VERSION,
        "selection_policy": SELECTION_POLICY_VERSION,
        "revision_rounds": REVISION_ROUNDS,
    }
    return BaselineRunSpec(
        baseline_id=_stable_id("BASE", config),
        baseline_kind=BaselineKind.MULTI_AGENT_ORCHESTRATION,
        task_bundle_ids=tuple(task_bundle_ids),
        config_fingerprint_sha256=_fingerprint(config),
        replay_verified=replay_verified,
        notes=(
            "api-backed multi-agent orchestration run",
            f"model={model}",
            f"request_model={request_model}",
            f"task_source={task_source}",
            "single-pass reference = writer draft",
            f"selection_policy={SELECTION_POLICY_VERSION}",
        ),
    )


def _response_text(response: Mapping[str, Any]) -> str:
    if "output_text" in response:
        return str(response["output_text"]).strip()
    return str(response["choices"][0]["message"]["content"]).strip()


def _stage_usage(response: Mapping[str, Any], elapsed_seconds: float) -> Dict[str, Any]:
    usage = dict(response.get("usage") or {})
    usage["elapsed_seconds"] = round(elapsed_seconds, 2)
    return usage


def _avg(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def select_output_stage(
    draft_output_text: str,
    reviser_output_text: str,
    *,
    draft_passed: bool,
    reviser_passed: bool,
    draft_citation_score: float,
    reviser_citation_score: float,
) -> Tuple[str, str, str]:
    if reviser_passed and not draft_passed:
        return reviser_output_text, "reviser", "deterministic_pass_improved"
    if reviser_passed == draft_passed and reviser_citation_score >= draft_citation_score:
        if reviser_citation_score > draft_citation_score:
            return reviser_output_text, "reviser", "citation_specificity_improved"
        return reviser_output_text, "reviser", "non_regressive_tie"
    if draft_passed and not reviser_passed:
        return draft_output_text, "draft", "deterministic_regression_blocked"
    if reviser_citation_score < draft_citation_score:
        return draft_output_text, "draft", "citation_regression_blocked"
    return draft_output_text, "draft", "conservative_draft_fallback"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(PROVIDERS))
    parser.add_argument("--keys-file", default=str(Path.home() / ".api_keys"))
    parser.add_argument("--task-source", choices=("smoke", "inspection-slice"), default="smoke")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pause-between-calls", type=float, default=0.3)
    parser.add_argument("--mark-replay-verified", action="store_true")
    args = parser.parse_args()

    provider = PROVIDERS[args.model]
    critic_max_tokens = max(args.max_tokens, CRITIC_MAX_TOKENS_FLOOR)
    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif args.task_source == "inspection-slice":
        output_dir = OUTPUT_DIR_SLICE
    else:
        output_dir = OUTPUT_DIR_SMOKE
    output_dir.mkdir(parents=True, exist_ok=True)

    keys = load_api_keys(Path(args.keys_file).expanduser())
    env_key = os.environ.get(provider["api_key_env"])
    api_key = env_key or keys.get(provider["api_key_env"])
    if not args.dry_run and not api_key:
        print(f"Missing {provider['api_key_env']} (checked env and {args.keys_file})", file=sys.stderr)
        return 2

    task_bundles = {bundle.task_bundle_id: bundle for bundle in load_task_bundles(TASK_BUNDLES_PATH)}
    source_bundles = load_source_bundles(SOURCE_BUNDLES_PATH)

    if args.task_source == "inspection-slice":
        selected_ids: Sequence[str] = _load_inspection_slice_bundle_ids(INSPECTION_SLICE_PATH)
    else:
        selected_ids = DEFAULT_TASK_BUNDLE_IDS

    picks = []
    for task_bundle_id in selected_ids:
        match = task_bundles.get(task_bundle_id)
        if match is None:
            print(f"No task bundle found for id={task_bundle_id}", file=sys.stderr)
            continue
        if match.paper_id not in source_bundles:
            print(f"No source bundle for paper_id={match.paper_id}", file=sys.stderr)
            continue
        picks.append(match)

    if not picks:
        print("No task bundles selected; aborting.", file=sys.stderr)
        return 3

    producer_id = (
        f"llm-agentic:{BaselineKind.MULTI_AGENT_ORCHESTRATION.value}:"
        f"{args.model}@temp={args.temperature}"
    )
    submission_fingerprint = _fingerprint(
        {
            "baseline_kind": BaselineKind.MULTI_AGENT_ORCHESTRATION.value,
            "model": args.model,
            "request_model": provider["request_model"],
            "temperature": args.temperature,
            "task_source": args.task_source,
            "writer_prompt_version": WRITER_PROMPT_VERSION,
            "critic_prompt_version": CRITIC_PROMPT_VERSION,
            "reviser_prompt_version": REVISER_PROMPT_VERSION,
            "selection_policy": SELECTION_POLICY_VERSION,
            "revision_rounds": REVISION_ROUNDS,
            "producer_id": producer_id,
        }
    )

    final_submissions: List[SubmissionRecord] = []
    trace_rows: List[Dict[str, Any]] = []
    usage_rows: List[Dict[str, Any]] = []

    for idx, bundle in enumerate(picks, start=1):
        source_bundle = source_bundles[bundle.paper_id]
        paper_title = str((source_bundle.provenance_fields or {}).get("title") or bundle.paper_id)
        basename = f"{idx:02d}_{bundle.task_bundle_id.replace(':', '_')}"

        writer_prompt = build_writer_prompt(bundle, source_bundle, paper_title)
        writer_prompt_path = output_dir / "prompts" / f"writer_prompt_{basename}.md"
        _write_text(writer_prompt_path, writer_prompt)

        if args.dry_run:
            print(f"[{idx}/{len(picks)}] DRY RUN — wrote writer prompt to {writer_prompt_path}")
            draft_output_text = normalize_section_output(
                bundle.task_family.value,
                f"{TASK_FAMILY_TO_TARGET[bundle.task_family.value][0]}\n(dry run placeholder draft)",
            )
            writer_usage = {"prompt_tokens": None, "completion_tokens": None, "elapsed_seconds": 0.0}
        else:
            print(f"[{idx}/{len(picks)}] writer on {bundle.task_bundle_id} ({bundle.task_family.value})")
            writer_started = time.time()
            writer_response = call_llm_with_retry(
                writer_prompt,
                provider=provider,
                api_key=api_key,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            writer_elapsed = time.time() - writer_started
            draft_output_text = normalize_section_output(
                bundle.task_family.value,
                _response_text(writer_response),
            )
            writer_usage = _stage_usage(writer_response, writer_elapsed)
            print(
                "    writer done in "
                f"{writer_elapsed:.1f}s prompt_tokens={writer_usage.get('prompt_tokens')} "
                f"completion_tokens={writer_usage.get('completion_tokens')}"
            )

        critic_prompt = build_critic_prompt(bundle, source_bundle, paper_title, draft_output_text)
        critic_prompt_path = output_dir / "prompts" / f"critic_prompt_{basename}.md"
        _write_text(critic_prompt_path, critic_prompt)

        if args.dry_run:
            critique_payload = blank_critique_payload("dry run placeholder critique")
            critic_raw_output = json.dumps(critique_payload, indent=2)
            critic_parse_error = None
            critic_usage = {"prompt_tokens": None, "completion_tokens": None, "elapsed_seconds": 0.0}
        else:
            print(f"[{idx}/{len(picks)}] critic on {bundle.task_bundle_id}")
            critic_started = time.time()
            critic_response = call_llm_with_retry(
                critic_prompt,
                provider=provider,
                api_key=api_key,
                temperature=CRITIC_TEMPERATURE,
                max_tokens=critic_max_tokens,
            )
            critic_elapsed = time.time() - critic_started
            critic_raw_output = _response_text(critic_response)
            critique_payload, critic_parse_error = parse_critique_output(critic_raw_output)
            critic_usage = _stage_usage(critic_response, critic_elapsed)
            print(
                "    critic done in "
                f"{critic_elapsed:.1f}s prompt_tokens={critic_usage.get('prompt_tokens')} "
                f"completion_tokens={critic_usage.get('completion_tokens')}"
            )

        reviser_prompt = build_reviser_prompt(
            bundle,
            source_bundle,
            paper_title,
            draft_output_text,
            critique_payload,
        )
        reviser_prompt_path = output_dir / "prompts" / f"reviser_prompt_{basename}.md"
        _write_text(reviser_prompt_path, reviser_prompt)

        if args.dry_run:
            reviser_output_text = normalize_section_output(
                bundle.task_family.value,
                f"{TASK_FAMILY_TO_TARGET[bundle.task_family.value][0]}\n(dry run placeholder final)",
            )
            reviser_usage = {"prompt_tokens": None, "completion_tokens": None, "elapsed_seconds": 0.0}
        else:
            print(f"[{idx}/{len(picks)}] reviser on {bundle.task_bundle_id}")
            reviser_started = time.time()
            reviser_response = call_llm_with_retry(
                reviser_prompt,
                provider=provider,
                api_key=api_key,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            reviser_elapsed = time.time() - reviser_started
            reviser_output_text = normalize_section_output(
                bundle.task_family.value,
                _response_text(reviser_response),
            )
            reviser_usage = _stage_usage(reviser_response, reviser_elapsed)
            print(
                "    reviser done in "
                f"{reviser_elapsed:.1f}s prompt_tokens={reviser_usage.get('prompt_tokens')} "
                f"completion_tokens={reviser_usage.get('completion_tokens')}"
            )
            if args.pause_between_calls > 0 and idx < len(picks):
                time.sleep(args.pause_between_calls)

        draft_submission = build_submission_record(
            task_bundle_id=bundle.task_bundle_id,
            producer_id=producer_id + ":draft",
            output_text=draft_output_text,
            config_fingerprint_sha256=submission_fingerprint,
        )
        draft_evaluation = evaluate_submissions((bundle,), (draft_submission,))[0]
        draft_citation = citation_specificity(draft_output_text)
        reviser_submission = build_submission_record(
            task_bundle_id=bundle.task_bundle_id,
            producer_id=producer_id + ":reviser",
            output_text=reviser_output_text,
            config_fingerprint_sha256=submission_fingerprint,
        )
        reviser_evaluation = evaluate_submissions((bundle,), (reviser_submission,))[0]
        reviser_citation = citation_specificity(reviser_output_text)
        final_output_text, selected_output_stage, selected_output_reason = select_output_stage(
            draft_output_text,
            reviser_output_text,
            draft_passed=draft_evaluation.deterministic_checks_passed,
            reviser_passed=reviser_evaluation.deterministic_checks_passed,
            draft_citation_score=float(draft_citation["citation_specificity_score"]),
            reviser_citation_score=float(reviser_citation["citation_specificity_score"]),
        )
        final_submission = build_submission_record(
            task_bundle_id=bundle.task_bundle_id,
            producer_id=producer_id,
            output_text=final_output_text,
            config_fingerprint_sha256=submission_fingerprint,
        )
        final_evaluation = evaluate_submissions((bundle,), (final_submission,))[0]
        final_citation = citation_specificity(final_output_text)

        _write_text(output_dir / "drafts" / f"draft_{basename}.md", draft_output_text + "\n")
        _write_text(output_dir / "critic" / f"critique_{basename}.json", json.dumps(critique_payload, indent=2) + "\n")
        _write_text(output_dir / "revised" / f"revised_{basename}.md", reviser_output_text + "\n")
        _write_text(output_dir / "final" / f"final_{basename}.md", final_output_text + "\n")

        final_submissions.append(final_submission)
        usage_rows.extend(
            [
                {"task_bundle_id": bundle.task_bundle_id, "stage": "writer", **writer_usage},
                {"task_bundle_id": bundle.task_bundle_id, "stage": "critic", **critic_usage},
                {"task_bundle_id": bundle.task_bundle_id, "stage": "reviser", **reviser_usage},
            ]
        )
        trace_rows.append(
            {
                "task_bundle_id": bundle.task_bundle_id,
                "paper_id": bundle.paper_id,
                "task_family": bundle.task_family.value,
                "study_class": bundle.study_class.value,
                "claim_mode": bundle.claim_mode.value,
                "producer_id": producer_id,
                "model": args.model,
                "request_model": provider["request_model"],
                "temperature": args.temperature,
                "writer_prompt_version": WRITER_PROMPT_VERSION,
                "critic_prompt_version": CRITIC_PROMPT_VERSION,
                "reviser_prompt_version": REVISER_PROMPT_VERSION,
                "revision_rounds": REVISION_ROUNDS,
                "writer_prompt_path": str(writer_prompt_path),
                "critic_prompt_path": str(critic_prompt_path),
                "reviser_prompt_path": str(reviser_prompt_path),
                "draft_output_text": draft_output_text,
                "critic_payload": critique_payload,
                "critic_parse_error": critic_parse_error,
                "critic_raw_output": critic_raw_output,
                "reviser_output_text": reviser_output_text,
                "final_output_text": final_output_text,
                "draft_citation": dict(draft_citation),
                "reviser_citation": dict(reviser_citation),
                "final_citation": dict(final_citation),
                "draft_evaluation": draft_evaluation.to_dict(),
                "reviser_evaluation": reviser_evaluation.to_dict(),
                "final_evaluation": final_evaluation.to_dict(),
                "single_pass_reference": "writer draft",
                "selection_policy": SELECTION_POLICY_VERSION,
                "selected_output_stage": selected_output_stage,
                "selected_output_reason": selected_output_reason,
                "stage_usage": {
                    "writer": writer_usage,
                    "critic": critic_usage,
                    "reviser": reviser_usage,
                },
            }
        )

    submissions_path = output_dir / "submissions.jsonl"
    write_jsonl(str(submissions_path), final_submissions)

    run_spec = build_baseline_run_spec(
        [bundle.task_bundle_id for bundle in picks],
        producer_id,
        model=args.model,
        request_model=provider["request_model"],
        temperature=args.temperature,
        task_source=args.task_source,
        replay_verified=args.mark_replay_verified,
    )
    run_spec_path = output_dir / "baseline_run_spec.jsonl"
    write_jsonl(str(run_spec_path), [run_spec])

    trace_path = output_dir / "agentic_trace.jsonl"
    with trace_path.open("w", encoding="utf-8") as handle:
        for row in trace_rows:
            handle.write(json.dumps(row) + "\n")

    draft_pass_count = sum(
        1 for row in trace_rows if row["draft_evaluation"]["deterministic_checks_passed"]
    )
    reviser_pass_count = sum(
        1 for row in trace_rows if row["reviser_evaluation"]["deterministic_checks_passed"]
    )
    final_pass_count = sum(
        1 for row in trace_rows if row["final_evaluation"]["deterministic_checks_passed"]
    )
    draft_mean_citation = _avg(
        [float(row["draft_citation"]["citation_specificity_score"]) for row in trace_rows]
    )
    reviser_mean_citation = _avg(
        [float(row["reviser_citation"]["citation_specificity_score"]) for row in trace_rows]
    )
    final_mean_citation = _avg(
        [float(row["final_citation"]["citation_specificity_score"]) for row in trace_rows]
    )

    deterministic_regressions = [
        row["task_bundle_id"]
        for row in trace_rows
        if row["draft_evaluation"]["deterministic_checks_passed"]
        and not row["final_evaluation"]["deterministic_checks_passed"]
    ]
    citation_regressions = [
        row["task_bundle_id"]
        for row in trace_rows
        if float(row["final_citation"]["citation_specificity_score"])
        < float(row["draft_citation"]["citation_specificity_score"])
    ]
    raw_reviser_deterministic_regressions = [
        row["task_bundle_id"]
        for row in trace_rows
        if row["draft_evaluation"]["deterministic_checks_passed"]
        and not row["reviser_evaluation"]["deterministic_checks_passed"]
    ]
    raw_reviser_citation_regressions = [
        row["task_bundle_id"]
        for row in trace_rows
        if float(row["reviser_citation"]["citation_specificity_score"])
        < float(row["draft_citation"]["citation_specificity_score"])
    ]
    critique_parse_failures = [
        row["task_bundle_id"]
        for row in trace_rows
        if row["critic_parse_error"] is not None
    ]
    selection_overrides = [
        row["task_bundle_id"]
        for row in trace_rows
        if row["selected_output_stage"] != "reviser"
    ]

    by_task_family: Dict[str, Dict[str, Any]] = {}
    for row in trace_rows:
        family = row["task_family"]
        bucket = by_task_family.setdefault(
            family,
            {
                "total": 0,
                "draft_pass": 0,
                "reviser_pass": 0,
                "final_pass": 0,
                "draft_citation_scores": [],
                "reviser_citation_scores": [],
                "final_citation_scores": [],
                "critique_parse_failures": 0,
            },
        )
        bucket["total"] += 1
        bucket["draft_pass"] += int(row["draft_evaluation"]["deterministic_checks_passed"])
        bucket["reviser_pass"] += int(row["reviser_evaluation"]["deterministic_checks_passed"])
        bucket["final_pass"] += int(row["final_evaluation"]["deterministic_checks_passed"])
        bucket["draft_citation_scores"].append(
            float(row["draft_citation"]["citation_specificity_score"])
        )
        bucket["reviser_citation_scores"].append(
            float(row["reviser_citation"]["citation_specificity_score"])
        )
        bucket["final_citation_scores"].append(
            float(row["final_citation"]["citation_specificity_score"])
        )
        bucket["critique_parse_failures"] += int(row["critic_parse_error"] is not None)

    for bucket in by_task_family.values():
        bucket["draft_mean_citation"] = _avg(bucket.pop("draft_citation_scores"))
        bucket["reviser_mean_citation"] = _avg(bucket.pop("reviser_citation_scores"))
        bucket["final_mean_citation"] = _avg(bucket.pop("final_citation_scores"))

    total_prompt_tokens = sum((row.get("prompt_tokens") or 0) for row in usage_rows)
    total_completion_tokens = sum((row.get("completion_tokens") or 0) for row in usage_rows)

    summary = {
        "model": args.model,
        "request_model": provider["request_model"],
        "producer_id": producer_id,
        "baseline_kind": BaselineKind.MULTI_AGENT_ORCHESTRATION.value,
        "task_source": args.task_source,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "critic_max_tokens": critic_max_tokens,
        "revision_rounds": REVISION_ROUNDS,
        "selection_policy": SELECTION_POLICY_VERSION,
        "writer_prompt_version": WRITER_PROMPT_VERSION,
        "critic_prompt_version": CRITIC_PROMPT_VERSION,
        "reviser_prompt_version": REVISER_PROMPT_VERSION,
        "num_tasks": len(picks),
        "replay_verified": run_spec.replay_verified,
        "draft_pass_count": draft_pass_count,
        "reviser_pass_count": reviser_pass_count,
        "final_pass_count": final_pass_count,
        "draft_mean_citation_specificity_score": draft_mean_citation,
        "reviser_mean_citation_specificity_score": reviser_mean_citation,
        "final_mean_citation_specificity_score": final_mean_citation,
        "deterministic_regressions": deterministic_regressions,
        "citation_regressions": citation_regressions,
        "raw_reviser_deterministic_regressions": raw_reviser_deterministic_regressions,
        "raw_reviser_citation_regressions": raw_reviser_citation_regressions,
        "selection_overrides": selection_overrides,
        "critique_parse_failures": critique_parse_failures,
        "single_pass_reference": "writer draft using the same evidence-bounded prompt style as llm_smoke_eval.py",
        "by_task_family": by_task_family,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "usage": usage_rows,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Agentic LLM Evaluation",
        "",
        f"- model: `{args.model}` (request model: `{provider['request_model']}`)",
        f"- baseline kind: `{BaselineKind.MULTI_AGENT_ORCHESTRATION.value}`",
        f"- task source: `{args.task_source}`",
        f"- revision rounds: {REVISION_ROUNDS}",
        f"- selection policy: `{SELECTION_POLICY_VERSION}`",
        f"- critic max tokens: {critic_max_tokens}",
        f"- replay verified: `{run_spec.replay_verified}`",
        f"- tasks: {len(picks)}",
        f"- draft deterministic pass: {draft_pass_count} / {len(picks)}",
        f"- raw reviser deterministic pass: {reviser_pass_count} / {len(picks)}",
        f"- final deterministic pass: {final_pass_count} / {len(picks)}",
        f"- draft mean citation specificity: {draft_mean_citation:.3f}",
        f"- raw reviser mean citation specificity: {reviser_mean_citation:.3f}",
        f"- final mean citation specificity: {final_mean_citation:.3f}",
        f"- critique parse failures: {len(critique_parse_failures)}",
        f"- total tokens: prompt={total_prompt_tokens}, completion={total_completion_tokens}",
        "",
        "## Acceptance Checks",
        "",
        f"- raw reviser deterministic pass count >= draft: `{reviser_pass_count >= draft_pass_count}`",
        f"- final deterministic pass count >= draft: `{final_pass_count >= draft_pass_count}`",
        f"- raw reviser mean citation specificity >= draft: `{reviser_mean_citation >= draft_mean_citation}`",
        f"- final mean citation specificity >= draft: `{final_mean_citation >= draft_mean_citation}`",
        f"- raw reviser deterministic regressions: {raw_reviser_deterministic_regressions or '(none)' }",
        f"- raw reviser citation regressions: {raw_reviser_citation_regressions or '(none)' }",
        f"- deterministic regressions: {deterministic_regressions or '(none)' }",
        f"- citation regressions: {citation_regressions or '(none)' }",
        f"- selection overrides: {selection_overrides or '(none)' }",
        f"- single-pass reference: {summary['single_pass_reference']}",
        "",
        "## Per task family",
        "",
        "| task_family | draft pass / total | raw reviser pass / total | final pass / total | draft mean citation | raw reviser mean citation | final mean citation | critique parse failures |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family in sorted(by_task_family):
        bucket = by_task_family[family]
        md_lines.append(
            f"| {family} | {bucket['draft_pass']} / {bucket['total']} | "
            f"{bucket['reviser_pass']} / {bucket['total']} | "
            f"{bucket['final_pass']} / {bucket['total']} | "
            f"{bucket['draft_mean_citation']:.3f} | {bucket['reviser_mean_citation']:.3f} | "
            f"{bucket['final_mean_citation']:.3f} | "
            f"{bucket['critique_parse_failures']} |"
        )
    md_lines.extend(["", "## Per task", ""])
    for row in trace_rows:
        md_lines.extend(
            [
                f"### {row['task_family']} — {row['paper_id']}",
                "",
                f"- task_bundle_id: `{row['task_bundle_id']}`",
                f"- selected output stage: `{row['selected_output_stage']}`",
                f"- selected output reason: `{row['selected_output_reason']}`",
                f"- draft deterministic pass: `{row['draft_evaluation']['deterministic_checks_passed']}`",
                f"- raw reviser deterministic pass: `{row['reviser_evaluation']['deterministic_checks_passed']}`",
                f"- final deterministic pass: `{row['final_evaluation']['deterministic_checks_passed']}`",
                f"- draft citation specificity: `{row['draft_citation']['citation_specificity_score']}`",
                f"- raw reviser citation specificity: `{row['reviser_citation']['citation_specificity_score']}`",
                f"- final citation specificity: `{row['final_citation']['citation_specificity_score']}`",
                f"- critique parse error: `{row['critic_parse_error']}`",
                "",
            ]
        )
    (output_dir / "summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
