from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Sequence, Tuple


FRONTIER_SINGLE_PASS_PROMPT_VERSION = "v2"

TASK_FAMILY_TO_TARGET: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "methods_to_text": ("Methods", ("abstract_text", "results_text", "figure_captions", "table_snippets")),
    "results_to_text": ("Results", ("abstract_text", "methods_text", "figure_captions", "table_snippets")),
    "abstract_from_evidence": ("Abstract", ("methods_text", "results_text", "figure_captions", "table_snippets")),
}


def clip_frontier_text(text: str, limit: int = 6000) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def format_frontier_list(
    items: Sequence[str],
    *,
    limit_each: int = 800,
    max_items: int = 8,
) -> str:
    if not items:
        return "(none provided)"
    lines = []
    for idx, item in enumerate(items[:max_items], start=1):
        lines.append(f"{idx}. {clip_frontier_text(item, limit_each)}")
    return "\n".join(lines)


def build_frontier_single_pass_prompt(task_bundle: Any, source_bundle: Any, paper_title: str) -> str:
    task_family_value = task_bundle.task_family.value
    section_title, include_fields = TASK_FAMILY_TO_TARGET[task_family_value]

    sections: List[Tuple[str, str]] = []
    if "abstract_text" in include_fields and source_bundle.abstract_text:
        sections.append(("Abstract", clip_frontier_text(source_bundle.abstract_text)))
    if "methods_text" in include_fields and source_bundle.methods_text:
        sections.append(("Methods", clip_frontier_text(source_bundle.methods_text)))
    if "results_text" in include_fields and source_bundle.results_text:
        sections.append(("Results", clip_frontier_text(source_bundle.results_text)))
    if "figure_captions" in include_fields and source_bundle.figure_captions:
        sections.append(("Figure captions", format_frontier_list(source_bundle.figure_captions)))
    if "table_snippets" in include_fields and source_bundle.table_snippets:
        sections.append(("Table snippets", format_frontier_list(source_bundle.table_snippets)))

    sections_block = "\n\n".join(f"## {title}\n{content}" for title, content in sections)

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

    return f"""You are a biomedical scientific-writing assistant. Draft the "{section_title}" section of a research paper using ONLY the evidence provided below.

Hard requirements:
- Begin with a heading line that is exactly: {section_title}
- {length_guidance}
- Ground every substantive claim in a specific piece of the evidence.
- {citation_guidance}
- If a detail is not in the evidence, state that explicitly rather than inventing it. Do not speculate.
- Do not copy sentences verbatim from the evidence; paraphrase while preserving specific values and entities.

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

{sections_block}

Write the "{section_title}" section now, starting with the required heading line and satisfying all requirements."""


def frontier_submission_fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def frontier_submission_id(task_bundle_id: str, producer_id: str) -> str:
    digest = hashlib.sha256(f"{task_bundle_id}|{producer_id}".encode("utf-8")).hexdigest()
    return f"SUB:{digest[:12].upper()}"
