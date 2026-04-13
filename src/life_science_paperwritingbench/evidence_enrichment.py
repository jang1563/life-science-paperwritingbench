from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .models import (
    AutoReviewEvidenceEnrichmentAuditReport,
    AutoReviewEvidenceEnrichmentRecord,
    PmcFullTextFetchRecord,
    SourcePaper,
)


_ACCESSION_PATTERN = re.compile(
    r"\b(?:"
    r"GSE\d+|GSM\d+|GDS\d+|GPL\d+|"
    r"SRP\d+|SRX\d+|SRR\d+|SRS\d+|"
    r"ERP\d+|ERX\d+|ERR\d+|ERS\d+|"
    r"DRP\d+|DRX\d+|DRR\d+|DRS\d+|"
    r"PRJNA\d+|PRJEB\d+|PRJDB\d+|"
    r"SAMN\d+|SAMEA\d+|"
    r"E-MTAB-\d+|E-GEOD-\d+|"
    r"PXD\d+|PDB[:\s]?[A-Za-z0-9]{4}|RRID:[A-Za-z0-9:_-]+"
    r")\b",
    re.IGNORECASE,
)
_TRIAL_REGISTRY_PATTERN = re.compile(
    r"\b(?:NCT\d{8}|ISRCTN\d+|CRD420\d+|ACTRN\d+|ChiCTR[-A-Za-z0-9]+|CTRI/\d{4}/\d{2}/\d+|UMIN\d+)\b",
    re.IGNORECASE,
)
_METHODS_TITLE_PATTERN = re.compile(
    r"\b(?:method|methods|materials and methods|experimental procedures?|patients and methods|study design)\b",
    re.IGNORECASE,
)
_RESULTS_TITLE_PATTERN = re.compile(
    r"\b(?:result|results|finding|findings|outcome|outcomes)\b",
    re.IGNORECASE,
)
_DATA_AVAILABILITY_TITLE_PATTERN = re.compile(
    r"\b(?:data availability|availability of data|availability of data and materials|data access|accession|code availability)\b",
    re.IGNORECASE,
)
_TRIAL_REGISTRY_TRACEABILITY_PATTERN = re.compile(
    r"\b(?:clinicaltrials\.gov|trial registration|registered under|registered at|registered in|"
    r"primary endpoint|secondary endpoint|randomiz|randomis|placebo|intervention arm|control arm|"
    r"allocation|assigned|study arm|outcome assessment)\b",
    re.IGNORECASE,
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _iter_children(element: ET.Element, name: str) -> Iterable[ET.Element]:
    for child in list(element):
        if _local_name(child.tag) == name:
            yield child


def _element_text(element: Optional[ET.Element]) -> str:
    if element is None:
        return ""
    return _normalize_text(" ".join(text for text in element.itertext() if text))


def _first_child_text(element: ET.Element, child_name: str) -> str:
    for child in _iter_children(element, child_name):
        return _element_text(child)
    return ""


def _truncate_text(text: str, limit: int) -> str:
    normalized = _normalize_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 3)].rstrip() + "..."


def _dedupe(items: Iterable[str]) -> Tuple[str, ...]:
    ordered: List[str] = []
    seen = set()
    for item in items:
        normalized = _normalize_text(item)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(normalized)
    return tuple(ordered)


def _find_sections(root: ET.Element, title_pattern: re.Pattern[str]) -> Tuple[str, ...]:
    sections: List[str] = []
    for element in root.iter():
        if _local_name(element.tag) != "sec":
            continue
        title = _first_child_text(element, "title")
        if not title or not title_pattern.search(title):
            continue
        section_text = _element_text(element)
        if section_text:
            sections.append(section_text)
    return _dedupe(sections)


def _figure_captions(root: ET.Element, limit: int = 12) -> Tuple[str, ...]:
    captions: List[str] = []
    for element in root.iter():
        if _local_name(element.tag) != "fig":
            continue
        label = _first_child_text(element, "label")
        caption = _first_child_text(element, "caption")
        if label and caption:
            caption = f"{label}. {caption}"
        if caption:
            captions.append(_truncate_text(caption, 600))
        if len(captions) >= limit:
            break
    return _dedupe(captions)


def _table_snippets(root: ET.Element, limit: int = 12) -> Tuple[str, ...]:
    snippets: List[str] = []
    for element in root.iter():
        if _local_name(element.tag) != "table-wrap":
            continue
        label = _first_child_text(element, "label")
        caption = _first_child_text(element, "caption")
        if label and caption:
            caption = f"{label}. {caption}"
        cells: List[str] = []
        for child in element.iter():
            if _local_name(child.tag) in {"td", "th"}:
                text = _element_text(child)
                if text:
                    cells.append(text)
                if len(cells) >= 6:
                    break
        snippet = " | ".join(part for part in [caption, "; ".join(cells)] if part)
        if snippet:
            snippets.append(_truncate_text(snippet, 600))
        if len(snippets) >= limit:
            break
    return _dedupe(snippets)


def _xref_snippets(root: ET.Element, ref_type: str, limit: int = 12) -> Tuple[str, ...]:
    snippets: List[str] = []
    for element in root.iter():
        if _local_name(element.tag) != "p":
            continue
        has_target_xref = any(
            _local_name(child.tag) == "xref" and child.attrib.get("ref-type") == ref_type
            for child in element.iter()
        )
        if not has_target_xref:
            continue
        text = _truncate_text(_element_text(element), 600)
        if text:
            snippets.append(text)
        if len(snippets) >= limit:
            break
    return _dedupe(snippets)


def _trial_registry_reference_snippets(root: ET.Element, limit: int = 12) -> Tuple[str, ...]:
    snippets: List[str] = []
    for element in root.iter():
        if _local_name(element.tag) != "p":
            continue
        text = _truncate_text(_element_text(element), 600)
        if not text:
            continue
        if not (
            _TRIAL_REGISTRY_PATTERN.search(text)
            or _TRIAL_REGISTRY_TRACEABILITY_PATTERN.search(text)
        ):
            continue
        snippets.append(text)
        if len(snippets) >= limit:
            break
    return _dedupe(snippets)


def _identifier_hits(*texts: str) -> Tuple[str, ...]:
    hits: List[str] = []
    for text in texts:
        hits.extend(match.group(0).replace(" ", "") for match in _ACCESSION_PATTERN.finditer(text))
    return _dedupe(hits)


def _trial_hits(*texts: str) -> Tuple[str, ...]:
    hits: List[str] = []
    for text in texts:
        hits.extend(match.group(0).replace(" ", "") for match in _TRIAL_REGISTRY_PATTERN.finditer(text))
    return _dedupe(hits)


def _pmc_fulltext_url(pmcid: str) -> str:
    return f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"


def _read_url_bytes(url: str, *, headers: Optional[Mapping[str, str]] = None, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers=dict(headers or {}))
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read()


def _load_or_fetch_bytes(
    path: Path,
    url: str,
    *,
    refresh: bool,
    headers: Optional[Mapping[str, str]] = None,
    fetcher: Optional[Callable[..., bytes]] = None,
) -> Tuple[bytes, bool]:
    if path.exists() and not refresh:
        return path.read_bytes(), True
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (fetcher or _read_url_bytes)(url, headers=headers or {})
    path.write_bytes(payload)
    return payload, False


def _joined_sections(sections: Sequence[str], limit: int = 12000) -> str:
    return _truncate_text(" ".join(_normalize_text(section) for section in sections if section), limit)


def _parse_fulltext_payload(payload: bytes, raw_payload_path: str, pmcid: Optional[str], paper_id: str) -> AutoReviewEvidenceEnrichmentRecord:
    notes: List[str] = []
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        return AutoReviewEvidenceEnrichmentRecord(
            paper_id=paper_id,
            pmcid=pmcid,
            raw_payload_path=raw_payload_path,
            notes=(f"xml_parse_error:{exc}",),
        )

    methods_sections = _find_sections(root, _METHODS_TITLE_PATTERN)
    results_sections = _find_sections(root, _RESULTS_TITLE_PATTERN)
    data_availability_sections = _find_sections(root, _DATA_AVAILABILITY_TITLE_PATTERN)
    figure_captions = _dedupe(_figure_captions(root))
    table_snippets = _dedupe(_table_snippets(root))
    figure_reference_snippets = _dedupe(_xref_snippets(root, "fig"))
    table_reference_snippets = _dedupe(_xref_snippets(root, "table"))
    trial_registry_reference_snippets = _dedupe(_trial_registry_reference_snippets(root))

    methods_text = _joined_sections(methods_sections)
    results_text = _joined_sections(results_sections)
    if not methods_text:
        notes.append("methods_text_missing")
    if not results_text:
        notes.append("results_text_missing")

    identifiers = _identifier_hits(
        methods_text,
        results_text,
        " ".join(figure_captions),
        " ".join(table_snippets),
        " ".join(figure_reference_snippets),
        " ".join(table_reference_snippets),
        _joined_sections(data_availability_sections, 6000),
        _element_text(root),
    )
    trials = _trial_hits(
        methods_text,
        results_text,
        " ".join(figure_captions),
        " ".join(table_snippets),
        " ".join(figure_reference_snippets),
        " ".join(table_reference_snippets),
        " ".join(trial_registry_reference_snippets),
        _joined_sections(data_availability_sections, 6000),
        _element_text(root),
    )

    provenance_fields: Dict[str, str] = {}
    if methods_text:
        provenance_fields["methods_text"] = "pmc_fulltext_xml:sec[methods]"
    if results_text:
        provenance_fields["results_text"] = "pmc_fulltext_xml:sec[results]"
    if figure_captions:
        provenance_fields["figure_captions"] = "pmc_fulltext_xml:fig/caption"
    if table_snippets:
        provenance_fields["table_snippets"] = "pmc_fulltext_xml:table-wrap"
    if figure_reference_snippets:
        provenance_fields["figure_reference_snippets"] = "pmc_fulltext_xml:p/xref[@ref-type='fig']"
    if table_reference_snippets:
        provenance_fields["table_reference_snippets"] = "pmc_fulltext_xml:p/xref[@ref-type='table']"
    if identifiers:
        provenance_fields["resource_identifiers"] = "pmc_fulltext_xml+regex"
    if trials:
        provenance_fields["trial_registry_ids"] = "pmc_fulltext_xml+regex"
    if trial_registry_reference_snippets:
        provenance_fields["trial_registry_reference_snippets"] = "pmc_fulltext_xml:p[trial_registry_context]"
    if data_availability_sections:
        provenance_fields["data_availability"] = "pmc_fulltext_xml:sec[data_availability]"
        notes.append("data_availability_section_used_for_identifier_scan")

    return AutoReviewEvidenceEnrichmentRecord(
        paper_id=paper_id,
        pmcid=pmcid,
        raw_payload_path=raw_payload_path,
        methods_text=methods_text,
        results_text=results_text,
        figure_captions=figure_captions,
        table_snippets=table_snippets,
        figure_reference_snippets=figure_reference_snippets,
        table_reference_snippets=table_reference_snippets,
        resource_identifiers=identifiers,
        trial_registry_ids=trials,
        trial_registry_reference_snippets=trial_registry_reference_snippets,
        provenance_fields=provenance_fields,
        notes=tuple(notes),
    )


def build_auto_review_evidence_enrichments(
    papers: Sequence[SourcePaper],
    raw_dir: str,
    *,
    refresh: bool = False,
    fetcher: Optional[Callable[..., bytes]] = None,
) -> Tuple[Tuple[PmcFullTextFetchRecord, ...], Tuple[AutoReviewEvidenceEnrichmentRecord, ...]]:
    raw_path = Path(raw_dir)
    fetch_records: List[PmcFullTextFetchRecord] = []
    enrichments: List[AutoReviewEvidenceEnrichmentRecord] = []
    for paper in papers:
        pmcid = str((paper.metadata or {}).get("pmcid") or "").strip()
        if not pmcid:
            fetch_records.append(
                PmcFullTextFetchRecord(
                    paper_id=paper.paper_id,
                    pmcid=None,
                    fetch_url="",
                    raw_payload_path="",
                    fetch_ok=False,
                    used_cache=False,
                    content_sha256="",
                    error="missing_pmcid",
                )
            )
            enrichments.append(
                AutoReviewEvidenceEnrichmentRecord(
                    paper_id=paper.paper_id,
                    pmcid=None,
                    notes=("missing_pmcid",),
                )
            )
            continue

        url = _pmc_fulltext_url(pmcid)
        raw_payload_path = raw_path / f"{pmcid}.xml"
        try:
            payload, used_cache = _load_or_fetch_bytes(
                raw_payload_path,
                url,
                refresh=refresh,
                headers={"User-Agent": "life-science-paperwritingbench/0.1 (mailto:local@example.com)"},
                fetcher=fetcher,
            )
            fetch_records.append(
                PmcFullTextFetchRecord(
                    paper_id=paper.paper_id,
                    pmcid=pmcid,
                    fetch_url=url,
                    raw_payload_path=str(raw_payload_path),
                    fetch_ok=True,
                    used_cache=used_cache,
                    content_sha256=hashlib.sha256(payload).hexdigest(),
                )
            )
            enrichments.append(
                _parse_fulltext_payload(
                    payload,
                    raw_payload_path=str(raw_payload_path),
                    pmcid=pmcid,
                    paper_id=paper.paper_id,
                )
            )
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            fetch_records.append(
                PmcFullTextFetchRecord(
                    paper_id=paper.paper_id,
                    pmcid=pmcid,
                    fetch_url=url,
                    raw_payload_path=str(raw_payload_path),
                    fetch_ok=False,
                    used_cache=False,
                    content_sha256="",
                    error=str(exc),
                )
            )
            enrichments.append(
                AutoReviewEvidenceEnrichmentRecord(
                    paper_id=paper.paper_id,
                    pmcid=pmcid,
                    raw_payload_path=str(raw_payload_path),
                    notes=(f"fetch_error:{exc}",),
                )
            )
    return tuple(fetch_records), tuple(enrichments)


def audit_auto_review_evidence_enrichments(
    fetch_records: Sequence[PmcFullTextFetchRecord],
    enrichments: Sequence[AutoReviewEvidenceEnrichmentRecord],
) -> AutoReviewEvidenceEnrichmentAuditReport:
    return AutoReviewEvidenceEnrichmentAuditReport(
        generated_at=_utc_timestamp(),
        total_records=len(enrichments),
        methods_text_count=sum(1 for item in enrichments if item.methods_text),
        results_text_count=sum(1 for item in enrichments if item.results_text),
        figure_caption_count=sum(1 for item in enrichments if item.figure_captions),
        table_snippet_count=sum(1 for item in enrichments if item.table_snippets),
        figure_reference_snippet_count=sum(1 for item in enrichments if item.figure_reference_snippets),
        table_reference_snippet_count=sum(1 for item in enrichments if item.table_reference_snippets),
        resource_identifier_count=sum(1 for item in enrichments if item.resource_identifiers),
        trial_registry_count=sum(1 for item in enrichments if item.trial_registry_ids),
        trial_registry_reference_snippet_count=sum(
            1 for item in enrichments if item.trial_registry_reference_snippets
        ),
        fetch_ok_count=sum(1 for item in fetch_records if item.fetch_ok),
        notes=(
            "PMCID-backed Europe PMC fullTextXML is replay-first and reuses cached raw XML unless --refresh is supplied.",
        ),
    )


def materialize_enriched_source_papers(
    papers: Sequence[SourcePaper],
    enrichments: Sequence[AutoReviewEvidenceEnrichmentRecord],
) -> Tuple[SourcePaper, ...]:
    enrichment_by_paper = {record.paper_id: record for record in enrichments}
    enriched_papers: List[SourcePaper] = []
    for paper in papers:
        enrichment = enrichment_by_paper.get(paper.paper_id)
        if enrichment is None:
            enriched_papers.append(paper)
            continue
        metadata = dict(paper.metadata)
        if enrichment.methods_text:
            metadata["methods_text"] = enrichment.methods_text
        if enrichment.results_text:
            metadata["results_text"] = enrichment.results_text
        if enrichment.figure_captions:
            metadata["figure_captions"] = list(enrichment.figure_captions)
        if enrichment.table_snippets:
            metadata["table_snippets"] = list(enrichment.table_snippets)
        if enrichment.figure_reference_snippets:
            metadata["figure_reference_snippets"] = list(enrichment.figure_reference_snippets)
        if enrichment.table_reference_snippets:
            metadata["table_reference_snippets"] = list(enrichment.table_reference_snippets)
        if enrichment.resource_identifiers:
            metadata["resource_identifiers"] = list(enrichment.resource_identifiers)
        if enrichment.trial_registry_ids:
            metadata["trial_registry_ids"] = list(enrichment.trial_registry_ids)
        if enrichment.trial_registry_reference_snippets:
            metadata["trial_registry_reference_snippets"] = list(enrichment.trial_registry_reference_snippets)
        if enrichment.provenance_fields:
            metadata["auto_review_provenance_fields"] = dict(enrichment.provenance_fields)
        if enrichment.notes:
            metadata["auto_review_enrichment_notes"] = list(enrichment.notes)
        enriched_papers.append(
            SourcePaper(
                paper_id=paper.paper_id,
                title=paper.title,
                publication_year=paper.publication_year,
                publication_status=paper.publication_status,
                peer_reviewed=paper.peer_reviewed,
                study_class=paper.study_class,
                claim_mode=paper.claim_mode,
                modality_overlays=paper.modality_overlays,
                lineage=paper.lineage,
                crossmark_updates=paper.crossmark_updates,
                integrity_flags=paper.integrity_flags,
                major_correction_affects_interpretation=paper.major_correction_affects_interpretation,
                partial_retraction_invalidates_core_claims=paper.partial_retraction_invalidates_core_claims,
                explicit_pre2018_exception=paper.explicit_pre2018_exception,
                controlled_access_human_data=paper.controlled_access_human_data,
                small_cell_risk=paper.small_cell_risk,
                metadata=metadata,
            )
        )
    return tuple(enriched_papers)
