"""Citation-specificity scoring for generated paper sections.

This module hosts the content-aware citation heuristics used by the v2
submission-scoring layer. It was developed in scripts/llm_smoke_eval.py
during the Phase-2 LLM evaluation work, where the v1 deterministic check
(pointer-token overlap) was found to be gameable by a submission prompt
that simply stuffed placeholder labels like ``methods_section`` into the
output. See ``docs/strategic_review_2026-04-13.md`` for the full context.

The functions here are consulted by
``life_science_paperwritingbench.baselines.evaluate_submission_v2``; the
regex constants are also importable by the ``scripts/llm_smoke_eval.py``
runner so the submission pipeline and the scoring layer share one source
of truth. The original accession and repository-URL patterns live in
``life_science_paperwritingbench.evidence_enrichment`` and are reused
here by composition rather than duplicated.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence, Tuple

from .evidence_enrichment import _ACCESSION_PATTERN, _REPOSITORY_URL_PATTERN

__all__ = [
    "FIGURE_REF_PATTERN",
    "TABLE_REF_PATTERN",
    "PVALUE_PATTERN",
    "NUMERIC_MAGNITUDE_PATTERN",
    "ACCESSION_PATTERN",
    "REPOSITORY_URL_PATTERN",
    "FORBIDDEN_POINTER_TOKENS",
    "CITATION_SATURATION_COUNT",
    "CitationSpecificityReport",
    "citation_specificity",
    "citation_specificity_score",
]


FIGURE_REF_PATTERN = re.compile(
    r"\b(?:Fig(?:ure)?s?\.?|FIG\.?)\s*\d+[A-Za-z]?(?:[-,\s]+\d+[A-Za-z]?)*\b"
)
TABLE_REF_PATTERN = re.compile(
    r"\bTable[s]?\s*\d+[A-Za-z]?(?:[-,\s]+\d+[A-Za-z]?)*\b",
    re.IGNORECASE,
)
PVALUE_PATTERN = re.compile(r"\b[pP]\s*[<>=]\s*0?\.\d+\b")
NUMERIC_MAGNITUDE_PATTERN = re.compile(
    r"\b\d[\d,]*\.?\d*\s*(?:%|-fold|fold|mg|kg|nm|μm|µm|mm|cm|ml|kb|bp|nM|µM|mM|mg/kg|mg/mL|ml/kg)\b",
    re.IGNORECASE,
)
# Reused from evidence_enrichment so there is exactly one canonical regex
# set for accessions and repository URLs across the codebase.
ACCESSION_PATTERN = _ACCESSION_PATTERN
REPOSITORY_URL_PATTERN = _REPOSITORY_URL_PATTERN

FORBIDDEN_POINTER_TOKENS: Tuple[str, ...] = (
    "methods_section",
    "results_section",
    "abstract_section",
    "section_text",
    "methods_evidence",
    "results_evidence",
)

# Output with this many distinct real-citation tokens scores the maximum
# 1.0. Chosen empirically during Session 2 of the Phase-2 iteration —
# DeepSeek V3 submissions that reach 3 unique real citations reliably
# pass the judge's traceability axis as well.
CITATION_SATURATION_COUNT: int = 3


class CitationSpecificityReport(dict):
    """Plain-dict subclass so callers can ``report["accessions"]`` and also
    ``report.accessions`` in future without breaking existing JSON serializers.

    The shape is documented in :func:`citation_specificity`; this subclass
    exists only to give the return value a stable nominal type without
    paying the cost of a frozen dataclass.
    """


def _unique_matches(pattern: "re.Pattern[str]", text: str) -> List[str]:
    seen: List[str] = []
    for match in pattern.finditer(text):
        token = match.group(0)
        if token not in seen:
            seen.append(token)
    return seen


def citation_specificity(output_text: str) -> CitationSpecificityReport:
    """Score the citation-specificity of a generated section.

    Returns a dict with the following keys:

    - ``figure_refs`` / ``table_refs`` / ``pvalues`` / ``numeric_magnitudes``
      / ``accessions`` / ``repo_urls``: ordered unique matches.
    - ``forbidden_pointer_hits``: placeholder-label substrings found in the
      output (should be empty; any hit forces the score to 0.0).
    - ``citation_count``: total unique real-citation tokens.
    - ``citation_specificity_score``: 0.0 if any forbidden hit or no real
      citations; 1.0 when ``citation_count >= CITATION_SATURATION_COUNT``;
      linear in between (``citation_count / CITATION_SATURATION_COUNT``).
    - ``forbidden_pointer_free``: ``bool``, convenience of the above.

    The score is intentionally permissive about *correctness* — that is
    the judge layer's job. Here we only verify the output *contains*
    real scientific citation patterns rather than placeholder pointers.
    """
    text = output_text or ""

    figure_refs = _unique_matches(FIGURE_REF_PATTERN, text)
    table_refs = _unique_matches(TABLE_REF_PATTERN, text)
    pvalues = _unique_matches(PVALUE_PATTERN, text)
    numeric_magnitudes = _unique_matches(NUMERIC_MAGNITUDE_PATTERN, text)
    accessions = _unique_matches(ACCESSION_PATTERN, text)
    repo_urls = _unique_matches(REPOSITORY_URL_PATTERN, text)

    forbidden_hits = [token for token in FORBIDDEN_POINTER_TOKENS if token in text]

    citation_count = (
        len(figure_refs)
        + len(table_refs)
        + len(pvalues)
        + len(numeric_magnitudes)
        + len(accessions)
        + len(repo_urls)
    )
    if forbidden_hits or citation_count == 0:
        score = 0.0
    elif citation_count >= CITATION_SATURATION_COUNT:
        score = 1.0
    else:
        score = citation_count / CITATION_SATURATION_COUNT

    return CitationSpecificityReport(
        figure_refs=figure_refs,
        table_refs=table_refs,
        pvalues=pvalues,
        numeric_magnitudes=numeric_magnitudes,
        accessions=accessions,
        repo_urls=repo_urls,
        forbidden_pointer_hits=forbidden_hits,
        citation_count=citation_count,
        citation_specificity_score=round(score, 3),
        forbidden_pointer_free=not forbidden_hits,
    )


def citation_specificity_score(output_text: str) -> float:
    """Scalar convenience wrapper: ``float`` score in [0.0, 1.0]."""
    return float(citation_specificity(output_text)["citation_specificity_score"])
