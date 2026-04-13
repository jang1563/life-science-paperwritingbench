from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from .metadata_hints import suggest_governance_metadata_hints
from .models import (
    IngestionAuditReport,
    IngestionRecord,
    IngestionVerificationReport,
    LineageInfo,
    MetadataSourceRecord,
    SourcePaper,
)
from .policy import (
    ClaimMode,
    CrossmarkUpdateType,
    IntegrityFlag,
    ModalityOverlay,
    PUBLIC_GOLD_START_YEAR,
    PublicationStatus,
    StudyClass,
)


_TITLE_KEY_RE = re.compile(r"[^a-z0-9]+")


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_text(value: str) -> str:
    normalized = _TITLE_KEY_RE.sub(" ", value.strip().lower())
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_title(value: str) -> str:
    return _normalize_text(value)


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
    normalized = str(value).strip().upper()
    normalized = normalized.replace(" ", "")
    if not normalized:
        return None
    if not normalized.startswith("PMC"):
        digits = "".join(ch for ch in normalized if ch.isdigit())
        normalized = f"PMC{digits}" if digits else normalized
    return normalized


def _parse_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    return None


def _parse_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    match = re.search(r"(19|20)\d{2}", text)
    if match:
        return int(match.group(0))
    try:
        return int(text)
    except ValueError:
        return None


def _parse_enum(enum_cls: Any, value: Any) -> Optional[Any]:
    if value is None or value == "":
        return None
    try:
        return enum_cls(str(value))
    except ValueError:
        return None


def _parse_enum_list(enum_cls: Any, value: Any) -> Tuple[Any, ...]:
    if value is None or value == "":
        return ()
    values = value if isinstance(value, (list, tuple)) else [value]
    parsed = []
    for item in values:
        parsed_item = _parse_enum(enum_cls, item)
        if parsed_item is not None and parsed_item not in parsed:
            parsed.append(parsed_item)
    return tuple(parsed)


def _metadata_value(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _first_present(data: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return None


def _lineage_from_raw(data: Mapping[str, Any]) -> LineageInfo:
    source_family = _first_present(data, ("source_family",))
    consortium = _first_present(data, ("consortium_lineages", "consortium_lineage"))
    dataset = _first_present(data, ("dataset_lineages", "dataset_lineage"))
    lab = _first_present(data, ("lab_lineages", "lab_lineage"))

    def _tupleify(value: Any) -> Tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, (list, tuple)):
            return tuple(str(item) for item in value if str(item).strip())
        return (str(value),)

    return LineageInfo(
        source_family=str(source_family) if source_family not in (None, "") else None,
        consortium_lineages=_tupleify(consortium),
        dataset_lineages=_tupleify(dataset),
        lab_lineages=_tupleify(lab),
    )


def _canonical_payload(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _stable_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_payload(payload).encode("utf-8")).hexdigest()


def _ingestion_id(source_name: str, source_record_id: str) -> str:
    digest = hashlib.sha256(f"{source_name}:{source_record_id}".encode("utf-8")).hexdigest()[:12].upper()
    return f"ING:{digest}"


def _record_identity(record: MetadataSourceRecord) -> int:
    if record.doi:
        return 0
    if record.pmid:
        return 1
    if record.pmcid:
        return 2
    return 3


def _sorted_unique(values: Iterable[Any]) -> Tuple[Any, ...]:
    seen = set()
    ordered: List[Any] = []
    for value in sorted((item for item in values if item not in (None, "")), key=lambda item: str(item)):
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, index: int) -> int:
        parent = self.parent[index]
        if parent != index:
            self.parent[index] = self.find(parent)
        return self.parent[index]

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def ingest_metadata_records(
    raw_records: Sequence[Mapping[str, Any]],
    default_source_name: Optional[str] = None,
) -> Tuple[MetadataSourceRecord, ...]:
    standardized = []
    for index, raw in enumerate(raw_records):
        source_name = str(
            default_source_name
            or _first_present(raw, ("source_name", "source", "provider", "source_system"))
            or "local_export"
        )
        source_record_id = str(
            _first_present(raw, ("source_record_id", "record_id", "id", "uid"))
            or f"{source_name}:{index + 1}"
        )
        title = str(_first_present(raw, ("title", "paper_title", "article_title")) or "").strip()
        publication_status = _parse_enum(
            PublicationStatus,
            _first_present(raw, ("publication_status", "status")),
        )
        if publication_status is None:
            if _parse_bool(_first_present(raw, ("is_preprint", "preprint"))):
                publication_status = PublicationStatus.PREPRINT
            elif title:
                publication_status = PublicationStatus.PUBLISHED
            else:
                publication_status = PublicationStatus.UNKNOWN
        peer_reviewed = _parse_bool(_first_present(raw, ("peer_reviewed", "is_peer_reviewed")))
        if peer_reviewed is None and publication_status == PublicationStatus.PUBLISHED:
            peer_reviewed = True

        study_class = _parse_enum(StudyClass, _first_present(raw, ("study_class",)))
        claim_mode = _parse_enum(ClaimMode, _first_present(raw, ("claim_mode",)))
        modality_overlays = _parse_enum_list(ModalityOverlay, _first_present(raw, ("modality_overlays",)))
        crossmark_updates = _parse_enum_list(
            CrossmarkUpdateType,
            _first_present(raw, ("crossmark_updates",)),
        )
        integrity_flags = _parse_enum_list(IntegrityFlag, _first_present(raw, ("integrity_flags",)))
        lineage = _lineage_from_raw(raw)

        consumed_keys = {
            "source_name",
            "source",
            "provider",
            "source_system",
            "source_record_id",
            "record_id",
            "id",
            "uid",
            "title",
            "paper_title",
            "article_title",
            "publication_year",
            "year",
            "published_year",
            "doi",
            "DOI",
            "doi_url",
            "pmid",
            "PMID",
            "pmcid",
            "PMCID",
            "publication_status",
            "status",
            "is_preprint",
            "preprint",
            "peer_reviewed",
            "is_peer_reviewed",
            "study_class",
            "claim_mode",
            "modality_overlays",
            "crossmark_updates",
            "integrity_flags",
            "explicit_pre2018_exception",
            "controlled_access_human_data",
            "small_cell_risk",
            "source_family",
            "consortium_lineages",
            "consortium_lineage",
            "dataset_lineages",
            "dataset_lineage",
            "lab_lineages",
            "lab_lineage",
        }

        metadata = {
            str(key): _metadata_value(value)
            for key, value in raw.items()
            if key not in consumed_keys and value not in (None, "")
        }
        standardized.append(
            MetadataSourceRecord(
                ingestion_id=_ingestion_id(source_name, source_record_id),
                source_name=source_name,
                source_record_id=source_record_id,
                title=title,
                publication_year=_parse_int(
                    _first_present(raw, ("publication_year", "year", "published_year"))
                ),
                doi=_normalize_doi(_first_present(raw, ("doi", "DOI", "doi_url"))),
                pmid=_normalize_pmid(_first_present(raw, ("pmid", "PMID"))),
                pmcid=_normalize_pmcid(_first_present(raw, ("pmcid", "PMCID"))),
                publication_status=publication_status,
                peer_reviewed=peer_reviewed,
                study_class=study_class,
                claim_mode=claim_mode,
                modality_overlays=modality_overlays,
                lineage=lineage,
                crossmark_updates=crossmark_updates,
                integrity_flags=integrity_flags,
                explicit_pre2018_exception=bool(raw.get("explicit_pre2018_exception", False)),
                controlled_access_human_data=bool(raw.get("controlled_access_human_data", False)),
                small_cell_risk=bool(raw.get("small_cell_risk", False)),
                metadata=metadata,
            )
        )
    return tuple(standardized)


def _dedup_keys(record: MetadataSourceRecord) -> Tuple[Tuple[str, str], ...]:
    keys = []
    if record.doi:
        keys.append(("doi", record.doi))
    if record.pmid:
        keys.append(("pmid", record.pmid))
    if record.pmcid:
        keys.append(("pmcid", record.pmcid))
    normalized_title = normalize_title(record.title)
    if normalized_title and record.publication_year is not None:
        keys.append(("title_year", f"{normalized_title}:{record.publication_year}"))
    return tuple(keys)


def _merge_lineage(records: Sequence[MetadataSourceRecord]) -> LineageInfo:
    source_family = next((record.lineage.source_family for record in records if record.lineage.source_family), None)
    return LineageInfo(
        source_family=source_family,
        consortium_lineages=_sorted_unique(
            lineage
            for record in records
            for lineage in record.lineage.consortium_lineages
        ),
        dataset_lineages=_sorted_unique(
            lineage
            for record in records
            for lineage in record.lineage.dataset_lineages
        ),
        lab_lineages=_sorted_unique(
            lineage
            for record in records
            for lineage in record.lineage.lab_lineages
        ),
    )


def _merge_metadata(records: Sequence[MetadataSourceRecord]) -> Dict[str, str]:
    values: MutableMapping[str, List[str]] = defaultdict(list)
    for record in records:
        for key, value in record.metadata.items():
            if value not in values[key]:
                values[key].append(value)
    merged = {}
    for key in sorted(values):
        merged[key] = " | ".join(sorted(values[key]))
    return merged


def _publication_status_for_group(records: Sequence[MetadataSourceRecord]) -> PublicationStatus:
    statuses = {record.publication_status for record in records}
    terminal_order = (
        PublicationStatus.RETRACTED,
        PublicationStatus.WITHDRAWN,
        PublicationStatus.REMOVED,
    )
    for status in terminal_order:
        if status in statuses:
            return status
    if PublicationStatus.PUBLISHED in statuses:
        return PublicationStatus.PUBLISHED
    if PublicationStatus.PREPRINT in statuses:
        return PublicationStatus.PREPRINT
    return PublicationStatus.UNKNOWN


def _metadata_fingerprint_payload(
    paper_id: str,
    title: str,
    publication_year: Optional[int],
    doi: Optional[str],
    pmid: Optional[str],
    pmcid: Optional[str],
    publication_status: PublicationStatus,
    peer_reviewed: bool,
    metadata: Mapping[str, str],
) -> Mapping[str, Any]:
    return {
        "paper_id": paper_id,
        "title": title,
        "publication_year": publication_year,
        "doi": doi,
        "pmid": pmid,
        "pmcid": pmcid,
        "publication_status": publication_status.value,
        "peer_reviewed": peer_reviewed,
        "metadata": dict(sorted(metadata.items())),
    }


def _paper_id_for_group(
    doi: Optional[str],
    pmid: Optional[str],
    pmcid: Optional[str],
    normalized_title: str,
    publication_year: Optional[int],
) -> str:
    if doi:
        return f"DOI:{doi}"
    if pmid:
        return f"PMID:{pmid}"
    if pmcid:
        return f"PMCID:{pmcid}"
    digest = hashlib.sha256(f"{normalized_title}:{publication_year or 'UNK'}".encode("utf-8")).hexdigest()[:16]
    return f"TITLE:{digest.upper()}"


def _group_records(records: Sequence[MetadataSourceRecord]) -> Tuple[Tuple[MetadataSourceRecord, ...], ...]:
    union_find = _UnionFind(len(records))
    key_to_index: Dict[Tuple[str, str], int] = {}
    for index, record in enumerate(records):
        for key in _dedup_keys(record):
            if key in key_to_index:
                union_find.union(index, key_to_index[key])
            else:
                key_to_index[key] = index

    grouped: MutableMapping[int, List[MetadataSourceRecord]] = defaultdict(list)
    for index, record in enumerate(records):
        grouped[union_find.find(index)].append(record)

    normalized_groups = []
    for root in sorted(grouped):
        normalized_groups.append(
            tuple(
                sorted(
                    grouped[root],
                    key=lambda item: (
                        _record_identity(item),
                        item.publication_year is None,
                        -len(item.title),
                        item.source_name,
                        item.source_record_id,
                    ),
                )
            )
        )
    return tuple(normalized_groups)


def _default_study_class() -> StudyClass:
    return StudyClass.MECHANISTIC_EXPERIMENTAL


def _default_claim_mode() -> ClaimMode:
    return ClaimMode.EXPLORATORY


def _releaseability_flags(
    paper: SourcePaper,
    normalized_title: str,
    has_identifier: bool,
) -> Tuple[bool, Tuple[str, ...]]:
    flags: List[str] = []
    if paper.publication_status != PublicationStatus.PUBLISHED:
        flags.append("not_published")
    if not paper.peer_reviewed:
        flags.append("not_peer_reviewed")
    if not normalized_title:
        flags.append("missing_normalized_title")
    if paper.publication_year < PUBLIC_GOLD_START_YEAR and not paper.explicit_pre2018_exception:
        flags.append("pre2018_requires_exception")
    if not has_identifier:
        flags.append("missing_persistent_identifier")
    if paper.controlled_access_human_data:
        flags.append("controlled_access_human_data")
    license_text = str(paper.metadata.get("license", "")).strip().lower()
    if license_text in {"", "unknown", "restricted", "closed"}:
        flags.append("license_unclear_or_restricted")

    blocking = {
        "not_published",
        "not_peer_reviewed",
        "missing_normalized_title",
        "pre2018_requires_exception",
    }
    passed = not any(flag in blocking for flag in flags)
    return passed, tuple(flags)


def normalize_metadata_records(
    records: Sequence[MetadataSourceRecord],
) -> Tuple[Tuple[SourcePaper, ...], Tuple[IngestionRecord, ...], IngestionAuditReport]:
    grouped_records = _group_records(records)
    papers: List[SourcePaper] = []
    ingestion_records: List[IngestionRecord] = []
    source_counts = defaultdict(int)
    flag_counts = defaultdict(int)
    identifier_coverage = defaultdict(int)
    publication_status_counts = defaultdict(int)

    for record in records:
        source_counts[record.source_name] += 1

    for group in grouped_records:
        preferred = group[0]
        title = next((record.title for record in group if record.title), preferred.title)
        publication_year = next(
            (record.publication_year for record in group if record.publication_year is not None),
            None,
        )
        doi = next((record.doi for record in group if record.doi), None)
        pmid = next((record.pmid for record in group if record.pmid), None)
        pmcid = next((record.pmcid for record in group if record.pmcid), None)
        normalized_title = normalize_title(title)
        paper_id = _paper_id_for_group(doi, pmid, pmcid, normalized_title, publication_year)

        explicit_study_class = next((record.study_class for record in group if record.study_class), None)
        explicit_claim_mode = next((record.claim_mode for record in group if record.claim_mode), None)
        explicit_overlays = _sorted_unique(
            overlay for record in group for overlay in record.modality_overlays
        )
        merged_metadata = _merge_metadata(group)
        merged_metadata.update(
            {
                "normalized_title": normalized_title,
                "source_names": ",".join(sorted({record.source_name for record in group})),
                "source_record_ids": ",".join(record.source_record_id for record in group),
            }
        )
        if doi:
            merged_metadata["doi"] = doi
        if pmid:
            merged_metadata["pmid"] = pmid
        if pmcid:
            merged_metadata["pmcid"] = pmcid

        provisional_paper = SourcePaper(
            paper_id=paper_id,
            title=title,
            publication_year=publication_year if publication_year is not None else 1900,
            publication_status=_publication_status_for_group(group),
            peer_reviewed=any(record.peer_reviewed is True for record in group),
            study_class=explicit_study_class or _default_study_class(),
            claim_mode=explicit_claim_mode or _default_claim_mode(),
            modality_overlays=explicit_overlays,
            lineage=_merge_lineage(group),
            crossmark_updates=_sorted_unique(
                update for record in group for update in record.crossmark_updates
            ),
            integrity_flags=_sorted_unique(
                flag for record in group for flag in record.integrity_flags
            ),
            explicit_pre2018_exception=any(record.explicit_pre2018_exception for record in group),
            controlled_access_human_data=any(record.controlled_access_human_data for record in group),
            small_cell_risk=any(record.small_cell_risk for record in group),
            metadata=merged_metadata,
        )
        hint = suggest_governance_metadata_hints(provisional_paper)
        study_class = explicit_study_class or hint.suggested_study_class or provisional_paper.study_class
        claim_mode = explicit_claim_mode or hint.suggested_claim_mode or provisional_paper.claim_mode
        modality_overlays = _sorted_unique(explicit_overlays + hint.suggested_modality_overlays)
        finalized_paper = SourcePaper(
            paper_id=paper_id,
            title=title,
            publication_year=publication_year if publication_year is not None else 1900,
            publication_status=provisional_paper.publication_status,
            peer_reviewed=provisional_paper.peer_reviewed,
            study_class=study_class,
            claim_mode=claim_mode,
            modality_overlays=modality_overlays,
            lineage=provisional_paper.lineage,
            crossmark_updates=provisional_paper.crossmark_updates,
            integrity_flags=provisional_paper.integrity_flags,
            explicit_pre2018_exception=provisional_paper.explicit_pre2018_exception,
            controlled_access_human_data=provisional_paper.controlled_access_human_data,
            small_cell_risk=provisional_paper.small_cell_risk,
            metadata=provisional_paper.metadata,
        )
        has_identifier = any((doi, pmid, pmcid))
        releaseability_passed, releaseability_flags = _releaseability_flags(
            finalized_paper,
            normalized_title=normalized_title,
            has_identifier=has_identifier,
        )
        metadata_fingerprint_sha256 = _stable_digest(
            _metadata_fingerprint_payload(
                paper_id=paper_id,
                title=title,
                publication_year=publication_year,
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
                publication_status=finalized_paper.publication_status,
                peer_reviewed=finalized_paper.peer_reviewed,
                metadata=finalized_paper.metadata,
            )
        )

        papers.append(finalized_paper)
        publication_status_counts[finalized_paper.publication_status.value] += 1
        if doi:
            identifier_coverage["doi"] += 1
        elif pmid:
            identifier_coverage["pmid"] += 1
        elif pmcid:
            identifier_coverage["pmcid"] += 1
        else:
            identifier_coverage["title_year_only"] += 1
        for flag in releaseability_flags:
            flag_counts[flag] += 1

        for record in group:
            ingestion_records.append(
                IngestionRecord(
                    ingestion_id=record.ingestion_id,
                    source_name=record.source_name,
                    source_record_id=record.source_record_id,
                    paper_id=paper_id,
                    doi=doi,
                    pmid=pmid,
                    pmcid=pmcid,
                    normalized_title=normalized_title,
                    publication_year=publication_year,
                    releaseability_precheck_passed=releaseability_passed,
                    releaseability_flags=releaseability_flags,
                    metadata_fingerprint_sha256=metadata_fingerprint_sha256,
                )
            )

    papers = sorted(papers, key=lambda item: item.paper_id)
    ingestion_records = sorted(ingestion_records, key=lambda item: (item.paper_id, item.ingestion_id))
    releaseability_passed = sum(1 for record in papers if any(
        ingestion.releaseability_precheck_passed for ingestion in ingestion_records if ingestion.paper_id == record.paper_id
    ))
    report = IngestionAuditReport(
        generated_at=_utc_timestamp(),
        raw_records=len(records),
        normalized_papers=len(papers),
        merged_duplicates=max(0, len(records) - len(papers)),
        releaseability_precheck_passed=releaseability_passed,
        releaseability_precheck_failed=len(papers) - releaseability_passed,
        source_counts=dict(sorted(source_counts.items())),
        publication_status_counts=dict(sorted(publication_status_counts.items())),
        identifier_coverage=dict(sorted(identifier_coverage.items())),
        releaseability_flag_counts=dict(sorted(flag_counts.items())),
        notes=(
            "publication_year=1900 indicates missing source-year metadata at normalization time",
        )
        if any(paper.publication_year == 1900 for paper in papers)
        else (),
    )
    return tuple(papers), tuple(ingestion_records), report


def audit_ingestion_artifacts(
    papers: Sequence[SourcePaper],
    ingestion_records: Sequence[IngestionRecord],
    generated_at: Optional[str] = None,
) -> IngestionAuditReport:
    source_counts = defaultdict(int)
    flag_counts = defaultdict(int)
    identifier_coverage = defaultdict(int)
    publication_status_counts = defaultdict(int)
    paper_releaseability: Dict[str, bool] = {}

    for record in ingestion_records:
        source_counts[record.source_name] += 1
        paper_releaseability[record.paper_id] = record.releaseability_precheck_passed
        for flag in record.releaseability_flags:
            flag_counts[flag] += 1

    for paper in papers:
        publication_status_counts[paper.publication_status.value] += 1

    grouped_records: MutableMapping[str, List[IngestionRecord]] = defaultdict(list)
    for record in ingestion_records:
        grouped_records[record.paper_id].append(record)
    for records_for_paper in grouped_records.values():
        if any(record.doi for record in records_for_paper):
            identifier_coverage["doi"] += 1
        elif any(record.pmid for record in records_for_paper):
            identifier_coverage["pmid"] += 1
        elif any(record.pmcid for record in records_for_paper):
            identifier_coverage["pmcid"] += 1
        else:
            identifier_coverage["title_year_only"] += 1

    releaseability_passed = sum(1 for passed in paper_releaseability.values() if passed)
    return IngestionAuditReport(
        generated_at=generated_at or _utc_timestamp(),
        raw_records=len(ingestion_records),
        normalized_papers=len(papers),
        merged_duplicates=max(0, len(ingestion_records) - len(papers)),
        releaseability_precheck_passed=releaseability_passed,
        releaseability_precheck_failed=max(0, len(papers) - releaseability_passed),
        source_counts=dict(sorted(source_counts.items())),
        publication_status_counts=dict(sorted(publication_status_counts.items())),
        identifier_coverage=dict(sorted(identifier_coverage.items())),
        releaseability_flag_counts=dict(sorted(flag_counts.items())),
        notes=(),
    )


def verify_ingestion_artifacts(
    papers: Sequence[SourcePaper],
    ingestion_records: Sequence[IngestionRecord],
) -> IngestionVerificationReport:
    paper_counts: MutableMapping[str, int] = defaultdict(int)
    for paper in papers:
        paper_counts[paper.paper_id] += 1
    duplicate_paper_ids = sorted(paper_id for paper_id, count in paper_counts.items() if count > 1)

    ingestion_counts: MutableMapping[str, int] = defaultdict(int)
    for record in ingestion_records:
        ingestion_counts[record.ingestion_id] += 1
    duplicate_ingestion_ids = sorted(
        ingestion_id for ingestion_id, count in ingestion_counts.items() if count > 1
    )

    missing_normalized_titles = sorted(
        record.ingestion_id for record in ingestion_records if not record.normalized_title
    )
    missing_metadata_fingerprints = sorted(
        record.ingestion_id for record in ingestion_records if not record.metadata_fingerprint_sha256
    )

    records_by_paper: MutableMapping[str, List[IngestionRecord]] = defaultdict(list)
    for record in ingestion_records:
        records_by_paper[record.paper_id].append(record)

    precedence_violations = []
    for paper_id, records_for_paper in sorted(records_by_paper.items()):
        has_doi = any(record.doi for record in records_for_paper)
        has_pmid = any(record.pmid for record in records_for_paper)
        has_pmcid = any(record.pmcid for record in records_for_paper)
        if has_doi and not paper_id.startswith("DOI:"):
            precedence_violations.append(f"{paper_id}:expected DOI precedence")
        elif not has_doi and has_pmid and not paper_id.startswith("PMID:"):
            precedence_violations.append(f"{paper_id}:expected PMID precedence")
        elif not has_doi and not has_pmid and has_pmcid and not paper_id.startswith("PMCID:"):
            precedence_violations.append(f"{paper_id}:expected PMCID precedence")

    notes = []
    if len({record.paper_id for record in ingestion_records}) != len(papers):
        notes.append("ingestion records reference a different number of papers than normalized paper artifacts")
    ok = not any(
        (
            duplicate_paper_ids,
            duplicate_ingestion_ids,
            missing_normalized_titles,
            missing_metadata_fingerprints,
            precedence_violations,
        )
    )
    return IngestionVerificationReport(
        ok=ok,
        normalized_papers=len(papers),
        ingestion_records=len(ingestion_records),
        duplicate_paper_ids=tuple(duplicate_paper_ids),
        duplicate_ingestion_ids=tuple(duplicate_ingestion_ids),
        missing_normalized_titles=tuple(missing_normalized_titles),
        missing_metadata_fingerprints=tuple(missing_metadata_fingerprints),
        precedence_violations=tuple(precedence_violations),
        notes=tuple(notes),
    )
