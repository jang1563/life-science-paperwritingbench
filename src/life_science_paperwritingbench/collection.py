from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from .ingestion import (
    MetadataSourceRecord,
    IngestionRecord,
    normalize_title,
)
from .models import (
    ApiFetchRecord,
    ApiQuerySpec,
    CollectionBatchReport,
    CollectionBatchSpec,
    CollectionCandidateRecord,
)
from .policy import CrossmarkUpdateType, PublicationStatus, StudyClass


DEFAULT_COLLECTION_BATCH_ID = "collection_v1_2018_present"
DEFAULT_COLLECTION_YEAR_START = 2018
DEFAULT_COLLECTION_YEAR_END = 3000
DEFAULT_PRIMARY_RETMAX = 120
DEFAULT_RESERVE_RETMAX = 80
DEFAULT_TARGET_CANDIDATES_PER_CLASS = 50
DEFAULT_COLLECTION_SEED_SOURCE = "pubmed"
DEFAULT_COLLECTION_ENRICHMENT_SOURCES = ("europepmc", "crossref")
DEFAULT_OA_FULLTEXT_POLICY = "preferred"
OPEN_REVIEW_VENUES = ("elife", "peerj", "f1000research")
OPEN_LICENSE_MARKERS = (
    "creativecommons.org/licenses/",
    "cc by",
    "cc-by",
    "cc0",
    "public domain",
    "open access",
)
ACCESSION_PATTERNS = (
    re.compile(r"\bGSE\d+\b", re.IGNORECASE),
    re.compile(r"\bSRR\d+\b", re.IGNORECASE),
    re.compile(r"\bERP\d+\b", re.IGNORECASE),
    re.compile(r"\bPRJNA\d+\b", re.IGNORECASE),
    re.compile(r"\bPDB[:\s-]?[A-Z0-9]{4}\b", re.IGNORECASE),
)
TRIAL_REGISTRY_PATTERN = re.compile(r"\bNCT\d{8}\b", re.IGNORECASE)
FIGURE_TABLE_PATTERN = re.compile(r"\b(?:fig(?:ure)?|table|tbl)\b", re.IGNORECASE)
METHODS_RESULTS_PATTERN = re.compile(
    r"\b(methods?|results?|protocol|assay|western blot|immunoblot|cohort|hazard ratio|meta-analysis)\b",
    re.IGNORECASE,
)


PRIMARY_QUERY_TEMPLATES: Mapping[StudyClass, str] = {
    StudyClass.HUMAN_INTERVENTIONAL: '("randomized controlled trial"[Publication Type] OR "clinical trial"[Publication Type]) AND humans[MeSH Terms] AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.HUMAN_OBSERVATIONAL: '("cohort studies"[MeSH Terms] OR "case-control studies"[MeSH Terms] OR "observational study"[Publication Type]) AND humans[MeSH Terms] AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.SYSTEMATIC_REVIEW_META_ANALYSIS: '("systematic review"[Publication Type] OR "meta-analysis"[Publication Type]) AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.ANIMAL_PRECLINICAL: '("animals"[MeSH Terms] NOT humans[MeSH Terms]) AND (mouse[Title/Abstract] OR mice[Title/Abstract] OR rat[Title/Abstract] OR murine[Title/Abstract] OR "animal model"[Title/Abstract]) AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.MECHANISTIC_EXPERIMENTAL: '(cell[Title/Abstract] OR molecular[Title/Abstract] OR signaling[Title/Abstract] OR pathway[Title/Abstract] OR CRISPR[Title/Abstract] OR knockdown[Title/Abstract]) NOT review[Publication Type] AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.METHODS_RESOURCE: '(protocol[Title/Abstract] OR method[Title/Abstract] OR resource[Title/Abstract] OR atlas[Title/Abstract] OR database[Title/Abstract] OR toolkit[Title/Abstract] OR benchmark[Title/Abstract]) AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
}

RESERVE_QUERY_TEMPLATES: Mapping[StudyClass, str] = {
    StudyClass.HUMAN_INTERVENTIONAL: '(trial[Title/Abstract] OR randomiz*[Title/Abstract] OR intervention*[Title/Abstract]) AND humans[MeSH Terms] AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.HUMAN_OBSERVATIONAL: '(cohort[Title/Abstract] OR observational[Title/Abstract] OR registry[Title/Abstract] OR biomarker[Title/Abstract] OR association[Title/Abstract]) AND humans[MeSH Terms] AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.SYSTEMATIC_REVIEW_META_ANALYSIS: '("systematic review"[Title] OR "meta-analysis"[Title] OR "meta analysis"[Title]) AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.ANIMAL_PRECLINICAL: '(preclinical[Title/Abstract] OR "in vivo"[Title/Abstract]) AND ("animals"[MeSH Terms] NOT humans[MeSH Terms]) AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.MECHANISTIC_EXPERIMENTAL: '(mechanism[Title/Abstract] OR mechanistic[Title/Abstract] OR perturbation[Title/Abstract] OR assay[Title/Abstract]) NOT review[Publication Type] AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
    StudyClass.METHODS_RESOURCE: '(resource[Title] OR atlas[Title] OR database[Title] OR protocol[Title] OR software[Title] OR toolkit[Title]) AND ("2018/01/01"[Date - Publication] : "3000"[Date - Publication])',
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_digest(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:12].upper()


def _normalize_doi(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).strip()
    normalized = re.sub(r"^https?://(dx\.)?doi\.org/", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"^doi:\s*", "", normalized, flags=re.IGNORECASE)
    normalized = normalized.strip().lower()
    return normalized or None


def _normalize_pmid(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits or None


def _normalize_pmcid(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).strip().upper().replace(" ", "")
    if not normalized:
        return None
    if not normalized.startswith("PMC"):
        digits = "".join(ch for ch in normalized if ch.isdigit())
        normalized = f"PMC{digits}" if digits else normalized
    return normalized


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text.replace("\r", " ").replace("\n", " "))
    return text.strip()


def _open_review_signal(journal: str) -> bool:
    lowered = journal.strip().lower()
    return any(marker in lowered for marker in OPEN_REVIEW_VENUES)


def _is_open_license(value: Optional[str]) -> bool:
    lowered = str(value or "").strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in OPEN_LICENSE_MARKERS)


def _benchmark_ready_signal_count(title: str, abstract: str, metadata: Optional[Mapping[str, Any]] = None) -> int:
    haystack = " ".join(piece for piece in (title, abstract) if piece).strip()
    metadata = metadata or {}
    accession_like = bool(any(pattern.search(haystack) for pattern in ACCESSION_PATTERNS))
    trial_registry = bool(TRIAL_REGISTRY_PATTERN.search(haystack))
    figure_table = bool(FIGURE_TABLE_PATTERN.search(haystack))
    methods_results = bool(METHODS_RESULTS_PATTERN.search(haystack))
    return int(bool(abstract.strip())) + int(accession_like) + int(trial_registry) + int(figure_table) + int(methods_results)


def _candidate_rank_tuple(candidate: CollectionCandidateRecord) -> Tuple[Any, ...]:
    return (
        0 if candidate.publication_status == PublicationStatus.PUBLISHED else 1,
        0 if candidate.peer_reviewed is True else 1,
        0 if candidate.oa_fulltext_available else 1,
        0 if bool(candidate.pmcid) else 1,
        0 if _is_open_license(candidate.license) else 1,
        0 if bool(candidate.doi) else 1,
        -int(candidate.benchmark_ready_signal_count),
        0 if candidate.open_review_signal else 1,
        -(candidate.publication_year or 0),
        candidate.paper_key,
    )


def _paper_key_for_identifiers(
    doi: Optional[str],
    pmid: Optional[str],
    pmcid: Optional[str],
    title: str,
    publication_year: Optional[int],
) -> str:
    if doi:
        return f"DOI:{doi}"
    if pmid:
        return f"PMID:{pmid}"
    if pmcid:
        return f"PMCID:{pmcid}"
    return f"TITLE:{normalize_title(title)}:{publication_year or 'UNK'}"


def build_collection_batch(
    *,
    batch_id: str = DEFAULT_COLLECTION_BATCH_ID,
    year_start: int = DEFAULT_COLLECTION_YEAR_START,
    year_end: int = DEFAULT_COLLECTION_YEAR_END,
    primary_retmax: int = DEFAULT_PRIMARY_RETMAX,
    reserve_retmax: int = DEFAULT_RESERVE_RETMAX,
    target_candidates_per_class: int = DEFAULT_TARGET_CANDIDATES_PER_CLASS,
) -> CollectionBatchSpec:
    query_specs = []
    for study_class in StudyClass:
        query_specs.append(
            ApiQuerySpec(
                batch_id=batch_id,
                study_class=study_class,
                lane="primary",
                source="pubmed",
                query_text=PRIMARY_QUERY_TEMPLATES[study_class],
                retmax=primary_retmax,
                year_start=year_start,
                year_end=year_end,
            )
        )
        query_specs.append(
            ApiQuerySpec(
                batch_id=batch_id,
                study_class=study_class,
                lane="reserve",
                source="pubmed",
                query_text=RESERVE_QUERY_TEMPLATES[study_class],
                retmax=reserve_retmax,
                year_start=year_start,
                year_end=year_end,
            )
        )
    return CollectionBatchSpec(
        batch_id=batch_id,
        year_start=year_start,
        year_end=year_end,
        primary_retmax=primary_retmax,
        reserve_retmax=reserve_retmax,
        target_candidates_per_class=target_candidates_per_class,
        seed_source=DEFAULT_COLLECTION_SEED_SOURCE,
        enrichment_sources=DEFAULT_COLLECTION_ENRICHMENT_SOURCES,
        oa_fulltext_policy=DEFAULT_OA_FULLTEXT_POLICY,
        query_specs=tuple(query_specs),
        notes=(
            "PubMed is seed retrieval only.",
            "Europe PMC is OA/full-text enrichment only.",
            "Crossref is DOI/license/Crossmark enrichment only.",
        ),
    )


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
    fetcher: Optional[Any] = None,
) -> bytes:
    if path.exists() and not refresh:
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (fetcher or _read_url_bytes)(url, headers=headers or {})
    path.write_bytes(payload)
    return payload


def _pubmed_esearch_url(query: str, retmax: int) -> str:
    return (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&retmode=json&retmax={retmax}&sort=relevance&term={urllib.parse.quote(query)}"
    )


def _pubmed_efetch_url(pmids: Sequence[str]) -> str:
    return (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&retmode=xml&id={urllib.parse.quote(','.join(pmids))}"
    )


def _pubmed_ids_for_query(
    query_spec: ApiQuerySpec,
    raw_dir: Path,
    *,
    refresh: bool,
    fetcher: Optional[Any] = None,
) -> Tuple[str, ...]:
    esearch_path = raw_dir / f"pubmed__{query_spec.study_class.value}__{query_spec.lane}__esearch.json"
    payload = _load_or_fetch_bytes(
        esearch_path,
        _pubmed_esearch_url(query_spec.query_text, query_spec.retmax),
        refresh=refresh,
        fetcher=fetcher,
    )
    response = json.loads(payload.decode("utf-8"))
    return tuple(str(item) for item in response.get("esearchresult", {}).get("idlist", []))


def _xml_text(element: Optional[ET.Element]) -> str:
    if element is None:
        return ""
    return _clean_text("".join(element.itertext()))


def _xml_first(root: ET.Element, path: str) -> str:
    element = root.find(path)
    return _xml_text(element)


def _parse_pubmed_article(
    article: ET.Element,
    *,
    study_class: StudyClass,
    lane: str,
    raw_payload_path: str,
) -> ApiFetchRecord:
    pmid = _normalize_pmid(_xml_first(article, "./MedlineCitation/PMID"))
    title = _xml_first(article, "./MedlineCitation/Article/ArticleTitle")
    abstract = " ".join(
        piece
        for piece in (
            _clean_text("".join(element.itertext()))
            for element in article.findall("./MedlineCitation/Article/Abstract/AbstractText")
        )
        if piece
    )
    journal = _xml_first(article, "./MedlineCitation/Article/Journal/Title")
    publication_year = None
    for path in (
        "./MedlineCitation/Article/ArticleDate/Year",
        "./MedlineCitation/Article/Journal/JournalIssue/PubDate/Year",
    ):
        value = _xml_first(article, path)
        if value.isdigit():
            publication_year = int(value)
            break
    doi = None
    pmcid = None
    publication_type_texts = [
        _clean_text(element.text)
        for element in article.findall("./MedlineCitation/Article/PublicationTypeList/PublicationType")
        if _clean_text(element.text)
    ]
    for identifier in article.findall("./PubmedData/ArticleIdList/ArticleId"):
        id_type = identifier.attrib.get("IdType", "").lower()
        if id_type == "doi" and doi is None:
            doi = _normalize_doi(identifier.text)
        elif id_type == "pmc" and pmcid is None:
            pmcid = _normalize_pmcid(identifier.text)
    source_record_id = pmid or doi or pmcid or _stable_digest(title, raw_payload_path)
    is_preprint = any("preprint" in item.lower() for item in publication_type_texts)
    return ApiFetchRecord(
        fetch_id=f"FETCH:{_stable_digest('pubmed', study_class.value, lane, source_record_id)}",
        source="pubmed",
        study_class=study_class,
        lane=lane,
        source_record_id=source_record_id,
        doi=doi,
        pmid=pmid,
        pmcid=pmcid,
        title=title,
        publication_year=publication_year,
        journal=journal,
        abstract=abstract,
        publication_status=(
            PublicationStatus.PREPRINT
            if is_preprint
            else PublicationStatus.PUBLISHED if title else PublicationStatus.UNKNOWN
        ),
        peer_reviewed=False if is_preprint else True if title else None,
        raw_payload_path=raw_payload_path,
        metadata={"publication_types": publication_type_texts},
    )


def fetch_pubmed_batch(
    batch_spec: CollectionBatchSpec,
    raw_dir: str,
    *,
    refresh: bool = False,
    fetcher: Optional[Any] = None,
) -> Tuple[ApiFetchRecord, ...]:
    raw_path = Path(raw_dir)
    records: List[ApiFetchRecord] = []
    query_specs_by_class: Dict[StudyClass, Dict[str, ApiQuerySpec]] = defaultdict(dict)
    for query_spec in batch_spec.query_specs:
        if query_spec.source == "pubmed":
            query_specs_by_class[query_spec.study_class][query_spec.lane] = query_spec

    for study_class in StudyClass:
        class_specs = query_specs_by_class.get(study_class, {})
        primary_spec = class_specs.get("primary")
        if primary_spec is None:
            continue
        primary_records = _fetch_pubmed_query(primary_spec, raw_path, refresh=refresh, fetcher=fetcher)
        records.extend(primary_records)

        primary_keys = {
            _paper_key_for_identifiers(
                record.doi,
                record.pmid,
                record.pmcid,
                record.title,
                record.publication_year,
            )
            for record in primary_records
        }
        reserve_spec = class_specs.get("reserve")
        if reserve_spec is None or len(primary_keys) >= 60:
            continue
        records.extend(_fetch_pubmed_query(reserve_spec, raw_path, refresh=refresh, fetcher=fetcher))
    return tuple(
        sorted(
            records,
            key=lambda item: (item.study_class.value, item.lane, item.source_record_id),
        )
    )


def _fetch_pubmed_query(
    query_spec: ApiQuerySpec,
    raw_path: Path,
    *,
    refresh: bool,
    fetcher: Optional[Any] = None,
) -> Tuple[ApiFetchRecord, ...]:
    records: List[ApiFetchRecord] = []
    pmids = _pubmed_ids_for_query(query_spec, raw_path, refresh=refresh, fetcher=fetcher)
    for chunk_index in range(0, len(pmids), 100):
        chunk = pmids[chunk_index: chunk_index + 100]
        if not chunk:
            continue
        chunk_path = raw_path / (
            f"pubmed__{query_spec.study_class.value}__{query_spec.lane}__efetch_{chunk_index // 100 + 1:02d}.xml"
        )
        payload = _load_or_fetch_bytes(
            chunk_path,
            _pubmed_efetch_url(chunk),
            refresh=refresh,
            fetcher=fetcher,
        )
        root = ET.fromstring(payload)
        for article in root.findall("./PubmedArticle"):
            records.append(
                _parse_pubmed_article(
                    article,
                    study_class=query_spec.study_class,
                    lane=query_spec.lane,
                    raw_payload_path=str(chunk_path),
                )
            )
    return tuple(records)


def _candidate_vote_counts(records: Sequence[ApiFetchRecord]) -> Dict[str, int]:
    counter = Counter(record.study_class.value for record in records)
    return dict(sorted(counter.items()))


def _selected_study_class(votes: Mapping[str, int]) -> Optional[StudyClass]:
    if len(votes) != 1:
        return None
    return StudyClass(next(iter(votes)))


def _shortlist_target_class(votes: Mapping[str, int]) -> Optional[StudyClass]:
    if not votes:
        return None
    best = sorted(votes.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return StudyClass(best)


def merge_collection_candidates(fetch_records: Sequence[ApiFetchRecord]) -> Tuple[CollectionCandidateRecord, ...]:
    grouped: MutableMapping[str, List[ApiFetchRecord]] = defaultdict(list)
    for record in fetch_records:
        paper_key = _paper_key_for_identifiers(
            record.doi,
            record.pmid,
            record.pmcid,
            record.title,
            record.publication_year,
        )
        grouped[paper_key].append(record)

    candidates = []
    for paper_key, records in sorted(grouped.items()):
        preferred = sorted(
            records,
            key=lambda item: (
                0 if item.doi else 1,
                0 if item.pmid else 1,
                0 if item.pmcid else 1,
                item.source,
                item.source_record_id,
            ),
        )[0]
        votes = _candidate_vote_counts(records)
        title = next((record.title for record in records if record.title), preferred.title)
        abstract = next((record.abstract for record in records if record.abstract), preferred.abstract)
        journal = next((record.journal for record in records if record.journal), preferred.journal)
        publication_year = next(
            (record.publication_year for record in records if record.publication_year is not None),
            preferred.publication_year,
        )
        publication_status = (
            PublicationStatus.PREPRINT
            if any(record.publication_status == PublicationStatus.PREPRINT for record in records)
            else PublicationStatus.PUBLISHED if any(record.publication_status == PublicationStatus.PUBLISHED for record in records)
            else preferred.publication_status
        )
        peer_reviewed = False if publication_status == PublicationStatus.PREPRINT else any(
            record.peer_reviewed is True for record in records
        )
        candidate = CollectionCandidateRecord(
            candidate_id=f"CAND:{_stable_digest(paper_key)}",
            paper_key=paper_key,
            study_class_votes=votes,
            selected_study_class=_selected_study_class(votes),
            shortlist_target_class=_shortlist_target_class(votes),
            doi=preferred.doi,
            pmid=preferred.pmid,
            pmcid=preferred.pmcid,
            title=title,
            publication_year=publication_year,
            journal=journal,
            abstract=abstract,
            publication_status=publication_status,
            peer_reviewed=peer_reviewed,
            oa_fulltext_available=False,
            license=None,
            crossmark_updates=(),
            open_review_signal=_open_review_signal(journal),
            benchmark_ready_signal_count=_benchmark_ready_signal_count(title, abstract),
            rank_tuple=(),
            source_names=tuple(sorted({record.source for record in records})),
            source_record_ids=tuple(sorted({record.source_record_id for record in records})),
            metadata={
                "study_class_votes": dict(votes),
            },
        )
        candidates.append(candidate)
    return tuple(candidates)


def _candidate_lookup_key(candidate: CollectionCandidateRecord) -> Tuple[str, str]:
    if candidate.pmid:
        return "pmid", candidate.pmid
    if candidate.pmcid:
        return "pmcid", candidate.pmcid
    if candidate.doi:
        return "doi", candidate.doi
    return "title", normalize_title(candidate.title)


def _europepmc_url(candidate: CollectionCandidateRecord) -> Optional[str]:
    if candidate.pmid:
        query = f"EXT_ID:{candidate.pmid} AND SRC:MED"
    elif candidate.pmcid:
        query = f"PMCID:{candidate.pmcid}"
    elif candidate.doi:
        query = f'DOI:"{candidate.doi}"'
    else:
        return None
    return (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?format=json&pageSize=1&query={urllib.parse.quote(query)}"
    )


def _crossref_url(candidate: CollectionCandidateRecord) -> Optional[str]:
    if not candidate.doi:
        return None
    return f"https://api.crossref.org/works/{urllib.parse.quote(candidate.doi)}"


def _merge_candidate_metadata(candidate: CollectionCandidateRecord, updates: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(candidate.metadata)
    merged.update({str(key): value for key, value in updates.items()})
    return merged


def enrich_candidates_with_europepmc(
    candidates: Sequence[CollectionCandidateRecord],
    raw_dir: str,
    *,
    refresh: bool = False,
    fetcher: Optional[Any] = None,
) -> Tuple[Tuple[CollectionCandidateRecord, ...], Tuple[ApiFetchRecord, ...]]:
    raw_path = Path(raw_dir)
    enriched_candidates = []
    fetch_records = []
    for candidate in candidates:
        url = _europepmc_url(candidate)
        if not url:
            enriched_candidates.append(candidate)
            continue
        raw_payload_path = raw_path / f"europepmc__{candidate.candidate_id}.json"
        try:
            payload = _load_or_fetch_bytes(raw_payload_path, url, refresh=refresh, fetcher=fetcher)
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as exc:
            enriched_candidates.append(
                CollectionCandidateRecord(
                    candidate_id=candidate.candidate_id,
                    paper_key=candidate.paper_key,
                    study_class_votes=candidate.study_class_votes,
                    selected_study_class=candidate.selected_study_class,
                    shortlist_target_class=candidate.shortlist_target_class,
                    doi=candidate.doi,
                    pmid=candidate.pmid,
                    pmcid=candidate.pmcid,
                    title=candidate.title,
                    publication_year=candidate.publication_year,
                    journal=candidate.journal,
                    abstract=candidate.abstract,
                    publication_status=candidate.publication_status,
                    peer_reviewed=candidate.peer_reviewed,
                    oa_fulltext_available=candidate.oa_fulltext_available,
                    license=candidate.license,
                    crossmark_updates=candidate.crossmark_updates,
                    open_review_signal=candidate.open_review_signal,
                    benchmark_ready_signal_count=candidate.benchmark_ready_signal_count,
                    rank_tuple=candidate.rank_tuple,
                    source_names=candidate.source_names,
                    source_record_ids=candidate.source_record_ids,
                    metadata=_merge_candidate_metadata(candidate, {"europepmc_error": str(exc)}),
                )
            )
            continue
        response = json.loads(payload.decode("utf-8"))
        result = (response.get("resultList", {}) or {}).get("result", []) or []
        record_payload = result[0] if result else {}
        fetch_records.append(
            ApiFetchRecord(
                fetch_id=f"FETCH:{_stable_digest('europepmc', candidate.candidate_id)}",
                source="europepmc",
                study_class=candidate.shortlist_target_class or candidate.selected_study_class or StudyClass.MECHANISTIC_EXPERIMENTAL,
                lane="enrichment",
                source_record_id=str(record_payload.get("id") or candidate.candidate_id),
                doi=_normalize_doi(record_payload.get("doi")) or candidate.doi,
                pmid=_normalize_pmid(record_payload.get("pmid")) or candidate.pmid,
                pmcid=_normalize_pmcid(record_payload.get("pmcid")) or candidate.pmcid,
                title=_clean_text(record_payload.get("title")) or candidate.title,
                publication_year=int(record_payload["pubYear"]) if str(record_payload.get("pubYear", "")).isdigit() else candidate.publication_year,
                journal=_clean_text(record_payload.get("journalTitle")) or candidate.journal,
                abstract=_clean_text(record_payload.get("abstractText")) or candidate.abstract,
                publication_status=PublicationStatus.PUBLISHED if record_payload else candidate.publication_status,
                peer_reviewed=candidate.peer_reviewed,
                raw_payload_path=str(raw_payload_path),
                metadata={
                    "is_open_access": str(record_payload.get("isOpenAccess", "")).strip(),
                },
            )
        )
        oa_fulltext_available = (
            str(record_payload.get("isOpenAccess", "")).strip().upper() == "Y"
            or bool(record_payload.get("pmcid") or candidate.pmcid)
        )
        journal = _clean_text(record_payload.get("journalTitle")) or candidate.journal
        abstract = _clean_text(record_payload.get("abstractText")) or candidate.abstract
        pmcid = _normalize_pmcid(record_payload.get("pmcid")) or candidate.pmcid
        enriched_candidates.append(
            CollectionCandidateRecord(
                candidate_id=candidate.candidate_id,
                paper_key=candidate.paper_key,
                study_class_votes=candidate.study_class_votes,
                selected_study_class=candidate.selected_study_class,
                shortlist_target_class=candidate.shortlist_target_class,
                doi=_normalize_doi(record_payload.get("doi")) or candidate.doi,
                pmid=_normalize_pmid(record_payload.get("pmid")) or candidate.pmid,
                pmcid=pmcid,
                title=_clean_text(record_payload.get("title")) or candidate.title,
                publication_year=int(record_payload["pubYear"]) if str(record_payload.get("pubYear", "")).isdigit() else candidate.publication_year,
                journal=journal,
                abstract=abstract,
                publication_status=PublicationStatus.PUBLISHED if record_payload else candidate.publication_status,
                peer_reviewed=candidate.peer_reviewed,
                oa_fulltext_available=oa_fulltext_available,
                license=candidate.license,
                crossmark_updates=candidate.crossmark_updates,
                open_review_signal=_open_review_signal(journal) or candidate.open_review_signal,
                benchmark_ready_signal_count=_benchmark_ready_signal_count(candidate.title, abstract),
                rank_tuple=candidate.rank_tuple,
                source_names=tuple(sorted(set(candidate.source_names + ("europepmc",)))),
                source_record_ids=candidate.source_record_ids,
                metadata=_merge_candidate_metadata(
                    candidate,
                    {
                        "europepmc_is_open_access": str(record_payload.get("isOpenAccess", "")),
                        "europepmc_in_epmc": str(record_payload.get("inEPMC", "")),
                    },
                ),
            )
        )
    return tuple(enriched_candidates), tuple(fetch_records)


def _crossmark_updates_from_crossref(message: Mapping[str, Any]) -> Tuple[CrossmarkUpdateType, ...]:
    updates = []
    relation = message.get("relation", {}) or {}
    relation_text = json.dumps(relation, sort_keys=True).lower()
    if "retraction" in relation_text:
        updates.append(CrossmarkUpdateType.RETRACTION)
    if "withdraw" in relation_text:
        updates.append(CrossmarkUpdateType.WITHDRAWAL)
    if "remove" in relation_text:
        updates.append(CrossmarkUpdateType.REMOVAL)
    if "correction" in relation_text or "corrigendum" in relation_text:
        updates.append(CrossmarkUpdateType.CORRECTION)
    return tuple(dict.fromkeys(updates))


def enrich_candidates_with_crossref(
    candidates: Sequence[CollectionCandidateRecord],
    raw_dir: str,
    *,
    refresh: bool = False,
    fetcher: Optional[Any] = None,
) -> Tuple[Tuple[CollectionCandidateRecord, ...], Tuple[ApiFetchRecord, ...]]:
    raw_path = Path(raw_dir)
    enriched_candidates = []
    fetch_records = []
    for candidate in candidates:
        url = _crossref_url(candidate)
        if not url:
            enriched_candidates.append(candidate)
            continue
        raw_payload_path = raw_path / f"crossref__{candidate.candidate_id}.json"
        try:
            payload = _load_or_fetch_bytes(
                raw_payload_path,
                url,
                refresh=refresh,
                headers={"User-Agent": "life-science-paperwritingbench/0.1 (mailto:local@example.com)"},
                fetcher=fetcher,
            )
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as exc:
            enriched_candidates.append(
                CollectionCandidateRecord(
                    candidate_id=candidate.candidate_id,
                    paper_key=candidate.paper_key,
                    study_class_votes=candidate.study_class_votes,
                    selected_study_class=candidate.selected_study_class,
                    shortlist_target_class=candidate.shortlist_target_class,
                    doi=candidate.doi,
                    pmid=candidate.pmid,
                    pmcid=candidate.pmcid,
                    title=candidate.title,
                    publication_year=candidate.publication_year,
                    journal=candidate.journal,
                    abstract=candidate.abstract,
                    publication_status=candidate.publication_status,
                    peer_reviewed=candidate.peer_reviewed,
                    oa_fulltext_available=candidate.oa_fulltext_available,
                    license=candidate.license,
                    crossmark_updates=candidate.crossmark_updates,
                    open_review_signal=candidate.open_review_signal,
                    benchmark_ready_signal_count=candidate.benchmark_ready_signal_count,
                    rank_tuple=candidate.rank_tuple,
                    source_names=candidate.source_names,
                    source_record_ids=candidate.source_record_ids,
                    metadata=_merge_candidate_metadata(candidate, {"crossref_error": str(exc)}),
                )
            )
            continue
        response = json.loads(payload.decode("utf-8"))
        message = response.get("message", {}) or {}
        license_urls = [
            str(item.get("URL", "")).strip()
            for item in message.get("license", []) or []
            if str(item.get("URL", "")).strip()
        ]
        license_text = " | ".join(license_urls) if license_urls else candidate.license
        crossmark_updates = _crossmark_updates_from_crossref(message) or candidate.crossmark_updates
        journal_values = message.get("container-title", []) or []
        journal = _clean_text(journal_values[0]) if journal_values else candidate.journal
        title_values = message.get("title", []) or []
        title = _clean_text(title_values[0]) if title_values else candidate.title
        fetch_records.append(
            ApiFetchRecord(
                fetch_id=f"FETCH:{_stable_digest('crossref', candidate.candidate_id)}",
                source="crossref",
                study_class=candidate.shortlist_target_class or candidate.selected_study_class or StudyClass.MECHANISTIC_EXPERIMENTAL,
                lane="enrichment",
                source_record_id=candidate.doi or candidate.candidate_id,
                doi=_normalize_doi(message.get("DOI")) or candidate.doi,
                pmid=candidate.pmid,
                pmcid=candidate.pmcid,
                title=title,
                publication_year=candidate.publication_year,
                journal=journal,
                abstract=candidate.abstract,
                publication_status=PublicationStatus.PUBLISHED if message else candidate.publication_status,
                peer_reviewed=candidate.peer_reviewed,
                raw_payload_path=str(raw_payload_path),
                metadata={
                    "license": license_urls,
                    "crossmark_updates": [item.value for item in crossmark_updates],
                },
            )
        )
        enriched_candidates.append(
            CollectionCandidateRecord(
                candidate_id=candidate.candidate_id,
                paper_key=candidate.paper_key,
                study_class_votes=candidate.study_class_votes,
                selected_study_class=candidate.selected_study_class,
                shortlist_target_class=candidate.shortlist_target_class,
                doi=_normalize_doi(message.get("DOI")) or candidate.doi,
                pmid=candidate.pmid,
                pmcid=candidate.pmcid,
                title=title,
                publication_year=candidate.publication_year,
                journal=journal,
                abstract=candidate.abstract,
                publication_status=PublicationStatus.PUBLISHED if message else candidate.publication_status,
                peer_reviewed=candidate.peer_reviewed,
                oa_fulltext_available=candidate.oa_fulltext_available,
                license=license_text,
                crossmark_updates=crossmark_updates,
                open_review_signal=_open_review_signal(journal) or candidate.open_review_signal,
                benchmark_ready_signal_count=_benchmark_ready_signal_count(title, candidate.abstract),
                rank_tuple=candidate.rank_tuple,
                source_names=tuple(sorted(set(candidate.source_names + ("crossref",)))),
                source_record_ids=candidate.source_record_ids,
                metadata=_merge_candidate_metadata(
                    candidate,
                    {
                        "crossref_license_urls": license_urls,
                        "crossref_has_crossmark_updates": bool(crossmark_updates),
                    },
                ),
            )
        )
    return tuple(enriched_candidates), tuple(fetch_records)


def rank_collection_candidates(
    candidates: Sequence[CollectionCandidateRecord],
) -> Tuple[CollectionCandidateRecord, ...]:
    ranked = []
    for candidate in candidates:
        rank_tuple = _candidate_rank_tuple(candidate)
        ranked.append(
            CollectionCandidateRecord(
                candidate_id=candidate.candidate_id,
                paper_key=candidate.paper_key,
                study_class_votes=candidate.study_class_votes,
                selected_study_class=candidate.selected_study_class,
                shortlist_target_class=candidate.shortlist_target_class,
                doi=candidate.doi,
                pmid=candidate.pmid,
                pmcid=candidate.pmcid,
                title=candidate.title,
                publication_year=candidate.publication_year,
                journal=candidate.journal,
                abstract=candidate.abstract,
                publication_status=candidate.publication_status,
                peer_reviewed=candidate.peer_reviewed,
                oa_fulltext_available=candidate.oa_fulltext_available,
                license=candidate.license,
                crossmark_updates=candidate.crossmark_updates,
                open_review_signal=candidate.open_review_signal,
                benchmark_ready_signal_count=candidate.benchmark_ready_signal_count,
                rank_tuple=rank_tuple,
                source_names=candidate.source_names,
                source_record_ids=candidate.source_record_ids,
                metadata=dict(candidate.metadata),
            )
        )
    return tuple(sorted(ranked, key=lambda item: item.rank_tuple))


def _metadata_record_for_candidate(candidate: CollectionCandidateRecord) -> MetadataSourceRecord:
    return MetadataSourceRecord(
        ingestion_id=f"ING:{_stable_digest(candidate.candidate_id)}",
        source_name="collection_candidate",
        source_record_id=candidate.candidate_id,
        title=candidate.title,
        publication_year=candidate.publication_year,
        doi=candidate.doi,
        pmid=candidate.pmid,
        pmcid=candidate.pmcid,
        publication_status=candidate.publication_status,
        peer_reviewed=candidate.peer_reviewed,
        study_class=candidate.selected_study_class,
        claim_mode=None,
        modality_overlays=(),
        metadata={
            "journal": candidate.journal,
            "abstract": candidate.abstract,
            "license": candidate.license or "",
            "oa_fulltext_available": "true" if candidate.oa_fulltext_available else "false",
            "open_review_signal": "true" if candidate.open_review_signal else "false",
            "study_class_votes": json.dumps(candidate.study_class_votes, sort_keys=True),
            "shortlist_target_class": candidate.shortlist_target_class.value if candidate.shortlist_target_class else "",
            "benchmark_ready_signal_count": str(candidate.benchmark_ready_signal_count),
            "rank_tuple": json.dumps(list(candidate.rank_tuple)),
            "source_names": ",".join(candidate.source_names),
            "source_record_ids": ",".join(candidate.source_record_ids),
        },
    )


def shortlist_collection_candidates(
    candidates: Sequence[CollectionCandidateRecord],
    *,
    target_candidates_per_class: int = DEFAULT_TARGET_CANDIDATES_PER_CLASS,
    batch_id: str = DEFAULT_COLLECTION_BATCH_ID,
) -> Tuple[Tuple[CollectionCandidateRecord, ...], Tuple[MetadataSourceRecord, ...], CollectionBatchReport]:
    ranked = rank_collection_candidates(candidates)
    shortlisted: List[CollectionCandidateRecord] = []
    seen = set()
    per_class: Dict[str, int] = defaultdict(int)
    for candidate in ranked:
        target_class = candidate.shortlist_target_class
        if target_class is None:
            continue
        class_key = target_class.value
        if per_class[class_key] >= target_candidates_per_class:
            continue
        if candidate.candidate_id in seen:
            continue
        shortlisted.append(candidate)
        seen.add(candidate.candidate_id)
        per_class[class_key] += 1

    metadata_records = tuple(_metadata_record_for_candidate(candidate) for candidate in shortlisted)
    report = summarize_collection_batch(
        batch_id=batch_id,
        candidates=candidates,
        shortlisted_candidates=shortlisted,
        total_queries=0,
        total_raw_fetch_records=0,
        releaseability_records=(),
        target_candidates_per_class=target_candidates_per_class,
    )
    return tuple(shortlisted), metadata_records, report


def summarize_collection_batch(
    *,
    batch_id: str,
    candidates: Sequence[CollectionCandidateRecord],
    shortlisted_candidates: Sequence[CollectionCandidateRecord] = (),
    total_queries: int = 0,
    total_raw_fetch_records: int = 0,
    releaseability_records: Sequence[IngestionRecord] = (),
    target_candidates_per_class: int = DEFAULT_TARGET_CANDIDATES_PER_CLASS,
) -> CollectionBatchReport:
    source_counts = Counter(source for candidate in candidates for source in candidate.source_names)
    candidate_counts = Counter(
        (candidate.shortlist_target_class or candidate.selected_study_class or StudyClass.MECHANISTIC_EXPERIMENTAL).value
        for candidate in candidates
    )
    shortlist_counts = Counter(
        (candidate.shortlist_target_class or candidate.selected_study_class or StudyClass.MECHANISTIC_EXPERIMENTAL).value
        for candidate in shortlisted_candidates
    )
    class_deficits = {
        study_class.value: max(0, target_candidates_per_class - shortlist_counts.get(study_class.value, 0))
        for study_class in StudyClass
    }
    identifier_coverage = Counter()
    for candidate in candidates:
        if candidate.doi:
            identifier_coverage["doi"] += 1
        elif candidate.pmid:
            identifier_coverage["pmid"] += 1
        elif candidate.pmcid:
            identifier_coverage["pmcid"] += 1
        else:
            identifier_coverage["title_year_only"] += 1
    releaseability_precheck_passed = sum(1 for record in releaseability_records if record.releaseability_precheck_passed)
    releaseability_precheck_failed = max(0, len({record.paper_id for record in releaseability_records}) - releaseability_precheck_passed)
    notes = ()
    if not releaseability_records:
        notes = ("releaseability_precheck counts are zero until normalize-papers has been run",)
    return CollectionBatchReport(
        generated_at=_utc_timestamp(),
        batch_id=batch_id,
        total_queries=total_queries,
        total_raw_fetch_records=total_raw_fetch_records,
        total_candidates=len(candidates),
        source_counts=dict(sorted(source_counts.items())),
        class_candidate_counts=dict(sorted(candidate_counts.items())),
        class_shortlist_counts=dict(sorted(shortlist_counts.items())),
        class_deficits=dict(sorted(class_deficits.items())),
        identifier_coverage=dict(sorted(identifier_coverage.items())),
        oa_fulltext_available_count=sum(1 for candidate in candidates if candidate.oa_fulltext_available),
        open_review_signal_count=sum(1 for candidate in candidates if candidate.open_review_signal),
        releaseability_precheck_passed=releaseability_precheck_passed,
        releaseability_precheck_failed=releaseability_precheck_failed,
        notes=notes,
    )


def audit_collection_batch(
    batch_spec: CollectionBatchSpec,
    candidates: Sequence[CollectionCandidateRecord],
    *,
    shortlisted_candidates: Sequence[CollectionCandidateRecord] = (),
    releaseability_records: Sequence[IngestionRecord] = (),
    total_raw_fetch_records: Optional[int] = None,
) -> CollectionBatchReport:
    return summarize_collection_batch(
        batch_id=batch_spec.batch_id,
        candidates=candidates,
        shortlisted_candidates=shortlisted_candidates,
        total_queries=len(batch_spec.query_specs),
        total_raw_fetch_records=(
            len(candidates) if total_raw_fetch_records is None else total_raw_fetch_records
        ),
        releaseability_records=releaseability_records,
        target_candidates_per_class=batch_spec.target_candidates_per_class,
    )
