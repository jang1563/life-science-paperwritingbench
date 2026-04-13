from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .models import (
    AutoAggregatedPaperReviewRecord,
    AutoReviewEvidenceEnrichmentRecord,
    AutoPanelVote,
    AutoQualificationRecord,
    AutoReviewBatchReport,
    AutoReviewSourceBundle,
    AutoReviewSourceBundleAuditReport,
    ExecutionProfile,
    PackagingReview,
    PaperPackagingReviewRecord,
    PaperQualificationDecision,
    ScientificReview,
    SourcePaper,
    WritingReview,
)
from .policy import (
    ClaimMode,
    AutoReviewBundleCompleteness,
    AutoReviewConfidence,
    AutoReviewRole,
    CandidateTier,
    DomainOutcome,
    IntegrityDisposition,
    ModalityOverlay,
    PackagingPolicy,
    PaperPackagingQualification,
    PaperScientificQualification,
    PaperWritingQualification,
    PublicationStatus,
    ScientificCriticalDomain,
    ScientificSupportingDomain,
    StandardId,
    StudyClass,
    WritingCriticalDomain,
    WritingSupportingDomain,
)
from .qualification import (
    qualify_packaging,
    qualify_scientific,
    qualify_writing,
    required_standards_for_paper,
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
_LIMITATION_PATTERN = re.compile(
    r"\b(?:limit|limitation|uncertain|uncertainty|may|might|suggest|future work|confidence interval|ci\b)\b",
    re.IGNORECASE,
)
_METHODS_RESULTS_PATTERN = re.compile(
    r"\b(?:method|methods|result|results|measured|assay|cohort|randomized|experiment|analysis)\b",
    re.IGNORECASE,
)
_FIGURE_TABLE_PATTERN = re.compile(r"\b(?:figure|fig\.?|table)\b", re.IGNORECASE)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_QUANTITATIVE_RESULT_PATTERN = re.compile(
    r"\b(?:odds ratio|hazard ratio|risk ratio|relative risk|95% ci|p\s*[<=>]\s*0?\.\d+|mortality rate|survival|cutoff values|receiver operating characteristic|roc curve)\b",
    re.IGNORECASE,
)
_ENZYMOLOGY_SIGNAL_PATTERNS = (
    re.compile(r"\benzyme kinetics\b", re.IGNORECASE),
    re.compile(r"\bmichaelis menten\b", re.IGNORECASE),
    re.compile(r"\bmichaelis-menten\b", re.IGNORECASE),
    re.compile(r"\bsubstrate turnover\b", re.IGNORECASE),
    re.compile(r"\bkcat\b", re.IGNORECASE),
    re.compile(r"\bkm\b.{0,24}\b(?:enzyme|enzymatic|substrate|kinetic|activity)\b", re.IGNORECASE),
    re.compile(r"\b(?:enzyme|enzymatic)\b.{0,24}\bkm\b", re.IGNORECASE),
)

_ABSTRACT_METHODS_CUES = (
    "we conducted",
    "we analyzed",
    "we used",
    "we employed",
    "we developed",
    "we sampled",
    "we enrolled",
    "we collected",
    "we profiled",
    "using ",
    "workflow",
    "protocol",
    "survey",
    "cohort",
    "meta-analysis",
    "meta analysis",
    "systematic review",
    "single-cell",
    "randomized",
    "algorithm",
    "toolkit",
    "database",
    "platform",
    "server",
    "viewer",
    "assay",
    "study",
    "retrospective",
    "prospective",
    "survival analysis",
    "cox proportional hazards",
    "kaplan-meier",
    "western blot",
    "knockdown",
    "transduced",
    "dynamometry",
    "bioelectrical impedance",
    "available methods",
    "working group",
)

_ABSTRACT_RESULTS_CUES = (
    "results show",
    "results revealed",
    "results reveal",
    "we found",
    "we present",
    "this article presents",
    "this article provides",
    "provides",
    "introduce",
    "allows",
    "facilitates",
    "show that",
    "showed that",
    "reveals",
    "revealed",
    "demonstrated",
    "indicates",
    "associated with",
    "improved",
    "accuracy",
    "recall",
    "f1",
    "benchmark",
    "establishes",
    "found that",
    "validated",
    "predictor",
    "predictors",
    "mortality",
    "survival",
    "hazard ratio",
    "odds ratio",
    "reduced",
    "increase",
    "decrease",
)

_RESOURCE_RELEASE_CUES = (
    "protocol",
    "workflow",
    "resource",
    "database",
    "toolkit",
    "atlas",
    "benchmark",
    "software",
    "platform",
    "server",
    "viewer",
    "editor",
    "api",
    "checklist",
    "survey",
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _text_items(value: object) -> Tuple[str, ...]:
    items: List[str] = []
    if value is None:
        return ()
    if isinstance(value, str):
        normalized = _normalize_text(value)
        return (normalized,) if normalized else ()
    if isinstance(value, Mapping):
        text = _coerce_text(value.get("text") or value.get("value") or value.get("description") or value.get("pointer"))
        normalized = _normalize_text(text)
        return (normalized,) if normalized else ()
    if isinstance(value, (list, tuple)):
        for item in value:
            items.extend(_text_items(item))
    return tuple(item for item in items if item)


def _join_non_empty(parts: Iterable[str]) -> str:
    return " ".join(part for part in (_normalize_text(item) for item in parts) if part)


def _has_enzymology_signal(text: str) -> bool:
    return any(pattern.search(text) for pattern in _ENZYMOLOGY_SIGNAL_PATTERNS)


def _split_sentences(text: str) -> Tuple[str, ...]:
    normalized = _normalize_text(text)
    if not normalized:
        return ()
    return tuple(
        sentence.strip()
        for sentence in _SENTENCE_SPLIT_PATTERN.split(normalized)
        if sentence.strip()
    )


def _select_sentences_with_cues(text: str, cues: Sequence[str]) -> Tuple[str, ...]:
    selected: List[str] = []
    for sentence in _split_sentences(text):
        lowered = sentence.lower()
        if any(cue in lowered for cue in cues):
            selected.append(sentence)
    return tuple(selected)


def _has_resource_release_signal(paper: SourcePaper, *texts: str) -> bool:
    if not (
        paper.study_class == StudyClass.METHODS_RESOURCE
        or paper.claim_mode == ClaimMode.RESOURCE_RELEASE
    ):
        return False
    corpus = _join_non_empty(texts).lower()
    return any(token in corpus for token in _RESOURCE_RELEASE_CUES)


def _bundle_has_resource_release_signal(bundle: AutoReviewSourceBundle) -> bool:
    corpus = _join_non_empty(
        (
            bundle.abstract_text,
            bundle.methods_text,
            bundle.results_text,
            " ".join(bundle.figure_captions),
            " ".join(bundle.table_snippets),
        )
    ).lower()
    return any(token in corpus for token in _RESOURCE_RELEASE_CUES)


def _infer_methods_text_from_abstract(
    paper: SourcePaper,
    abstract_text: str,
    existing_results_text: str,
) -> str:
    if not abstract_text:
        return ""
    selected = _select_sentences_with_cues(abstract_text, _ABSTRACT_METHODS_CUES)
    if not selected:
        return ""
    has_result_like_abstract = bool(_select_sentences_with_cues(abstract_text, _ABSTRACT_RESULTS_CUES))
    if existing_results_text or has_result_like_abstract or paper.study_class in {
        StudyClass.METHODS_RESOURCE,
        StudyClass.SYSTEMATIC_REVIEW_META_ANALYSIS,
    }:
        return _join_non_empty(selected[:4])
    return ""


def _infer_results_text_from_abstract(
    paper: SourcePaper,
    abstract_text: str,
    existing_methods_text: str,
) -> str:
    if not abstract_text:
        return ""
    selected = _select_sentences_with_cues(abstract_text, _ABSTRACT_RESULTS_CUES)
    if selected and (existing_methods_text or _has_resource_release_signal(paper, abstract_text)):
        return _join_non_empty(selected[:4])
    return ""


def _infer_results_text_from_figures(
    paper: SourcePaper,
    figure_captions: Sequence[str],
    existing_methods_text: str,
    abstract_text: str,
) -> str:
    if not figure_captions:
        return ""
    selected = _select_sentences_with_cues(
        " ".join(figure_captions),
        (
            "result",
            "results",
            "show",
            "shows",
            "showed",
            "revealed",
            "hazard ratio",
            "odds ratio",
            "survival",
            "mortality",
            "validated",
            "validation",
            "benchmark",
            "performance",
            "coverage",
            "association",
            "detected",
            "representative",
        ),
    )
    if selected and (
        existing_methods_text
        or bool(_select_sentences_with_cues(abstract_text, _ABSTRACT_METHODS_CUES))
        or paper.study_class in {
            StudyClass.ANIMAL_PRECLINICAL,
            StudyClass.HUMAN_OBSERVATIONAL,
            StudyClass.MECHANISTIC_EXPERIMENTAL,
            StudyClass.METHODS_RESOURCE,
        }
    ):
        return _join_non_empty(selected[:3])
    return ""


def _identifier_hits(*texts: str) -> Tuple[str, ...]:
    hits: List[str] = []
    for text in texts:
        hits.extend(match.group(0).replace(" ", "") for match in _ACCESSION_PATTERN.finditer(text))
    ordered: List[str] = []
    seen = set()
    for item in hits:
        normalized = item.strip()
        if not normalized or normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        ordered.append(normalized)
    return tuple(ordered)


def _trial_registry_hits(*texts: str) -> Tuple[str, ...]:
    hits: List[str] = []
    for text in texts:
        hits.extend(match.group(0).replace(" ", "") for match in _TRIAL_REGISTRY_PATTERN.finditer(text))
    ordered: List[str] = []
    seen = set()
    for item in hits:
        normalized = item.strip()
        if not normalized or normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        ordered.append(normalized)
    return tuple(ordered)


def _metadata_text(metadata: Mapping[str, object], *keys: str) -> str:
    for key in keys:
        text = _coerce_text(metadata.get(key))
        if text:
            return _normalize_text(text)
    return ""


def _metadata_items(metadata: Mapping[str, object], *keys: str) -> Tuple[str, ...]:
    items: List[str] = []
    for key in keys:
        items.extend(_text_items(metadata.get(key)))
    ordered: List[str] = []
    seen = set()
    for item in items:
        token = item.strip()
        if not token or token.lower() in seen:
            continue
        seen.add(token.lower())
        ordered.append(token)
    return tuple(ordered)


def _bundle_completeness(
    methods_text: str,
    results_text: str,
    figure_captions: Sequence[str],
    table_snippets: Sequence[str],
    resource_identifiers: Sequence[str],
    trial_registry_ids: Sequence[str],
    open_review_snippets: Sequence[str],
) -> AutoReviewBundleCompleteness:
    if methods_text and results_text and (
        figure_captions
        or table_snippets
        or resource_identifiers
        or trial_registry_ids
        or _QUANTITATIVE_RESULT_PATTERN.search(_join_non_empty((methods_text, results_text)))
    ):
        return AutoReviewBundleCompleteness.REVIEW_READY
    if methods_text or results_text or figure_captions or table_snippets or open_review_snippets:
        return AutoReviewBundleCompleteness.PARTIAL
    return AutoReviewBundleCompleteness.METADATA_ONLY


def build_auto_review_source_bundles(
    papers: Sequence[SourcePaper],
    evidence_enrichments: Sequence[AutoReviewEvidenceEnrichmentRecord] = (),
) -> Tuple[AutoReviewSourceBundle, ...]:
    enrichment_by_paper = {record.paper_id: record for record in evidence_enrichments}
    bundles: List[AutoReviewSourceBundle] = []
    for paper in papers:
        metadata = paper.metadata
        enrichment = enrichment_by_paper.get(paper.paper_id)
        abstract_text = _metadata_text(metadata, "abstract")
        methods_text = (
            _normalize_text(enrichment.methods_text)
            if enrichment and enrichment.methods_text
            else _metadata_text(metadata, "methods_text", "methods", "method_text", "methods_section")
        )
        results_text = (
            _normalize_text(enrichment.results_text)
            if enrichment and enrichment.results_text
            else _metadata_text(metadata, "results_text", "results", "result_text", "results_section")
        )
        methods_inferred_from_abstract = False
        results_inferred_from_abstract = False
        if not methods_text:
            inferred_methods = _infer_methods_text_from_abstract(paper, abstract_text, results_text)
            if inferred_methods:
                methods_text = inferred_methods
                methods_inferred_from_abstract = True
        if not results_text:
            inferred_results = _infer_results_text_from_abstract(paper, abstract_text, methods_text)
            if inferred_results:
                results_text = inferred_results
                results_inferred_from_abstract = True
        results_inferred_from_figures = False
        figure_captions = (
            tuple(_normalize_text(item) for item in enrichment.figure_captions)
            if enrichment and enrichment.figure_captions
            else _metadata_items(metadata, "figure_captions", "figure_caption_texts")
        )
        table_snippets = (
            tuple(_normalize_text(item) for item in enrichment.table_snippets)
            if enrichment and enrichment.table_snippets
            else _metadata_items(metadata, "table_snippets", "table_rows", "table_cells")
        )
        figure_reference_snippets = (
            tuple(_normalize_text(item) for item in enrichment.figure_reference_snippets)
            if enrichment and enrichment.figure_reference_snippets
            else _metadata_items(metadata, "figure_reference_snippets")
        )
        table_reference_snippets = (
            tuple(_normalize_text(item) for item in enrichment.table_reference_snippets)
            if enrichment and enrichment.table_reference_snippets
            else _metadata_items(metadata, "table_reference_snippets")
        )
        open_review_snippets = _metadata_items(
            metadata,
            "open_review_snippets",
            "review_comments",
            "decision_letters",
            "review_response_text",
        )
        resource_identifiers = (
            tuple(_normalize_text(item) for item in enrichment.resource_identifiers)
            if enrichment and enrichment.resource_identifiers
            else _metadata_items(metadata, "resource_identifiers", "accession_ids")
        )
        combined_text = _join_non_empty(
            (
                paper.title,
                abstract_text,
                methods_text,
                results_text,
                " ".join(figure_captions),
                " ".join(table_snippets),
                " ".join(figure_reference_snippets),
                " ".join(table_reference_snippets),
                " ".join(open_review_snippets),
            )
        )
        detected_identifiers = _identifier_hits(combined_text)
        detected_trials = (
            tuple(_normalize_text(item) for item in enrichment.trial_registry_ids)
            if enrichment and enrichment.trial_registry_ids
            else ()
        ) or _trial_registry_hits(combined_text)
        if detected_identifiers:
            resource_identifiers = tuple(dict.fromkeys(resource_identifiers + detected_identifiers))
        trial_registry_ids = tuple(dict.fromkeys(detected_trials))

        if not methods_text and figure_captions:
            inferred_methods_with_figures = _infer_methods_text_from_abstract(
                paper,
                abstract_text,
                _join_non_empty(figure_captions),
            )
            if inferred_methods_with_figures:
                methods_text = inferred_methods_with_figures
                methods_inferred_from_abstract = True

        if not results_text:
            inferred_results_from_figures = _infer_results_text_from_figures(
                paper,
                figure_captions,
                methods_text,
                abstract_text,
            )
            if inferred_results_from_figures:
                results_text = inferred_results_from_figures
                results_inferred_from_figures = True

        provenance_fields: Dict[str, str] = {}
        if abstract_text:
            provenance_fields["abstract"] = "metadata.abstract"
        if methods_text:
            provenance_fields["methods_text"] = (
                "metadata.abstract:derived_methods"
                if methods_inferred_from_abstract
                else "metadata.methods_text"
            )
        if results_text:
            provenance_fields["results_text"] = (
                "metadata.abstract:derived_results"
                if results_inferred_from_abstract
                else (
                    "metadata.figure_captions:derived_results"
                    if results_inferred_from_figures
                    else "metadata.results_text"
                )
            )
        if figure_captions:
            provenance_fields["figure_captions"] = "metadata.figure_captions"
        if table_snippets:
            provenance_fields["table_snippets"] = "metadata.table_rows/table_cells"
        if figure_reference_snippets:
            provenance_fields["figure_reference_snippets"] = "metadata.figure_reference_snippets"
        if table_reference_snippets:
            provenance_fields["table_reference_snippets"] = "metadata.table_reference_snippets"
        if resource_identifiers:
            provenance_fields["resource_identifiers"] = "metadata.resource_identifiers+regex"
        if trial_registry_ids:
            provenance_fields["trial_registry_ids"] = "metadata+regex"
        if open_review_snippets:
            provenance_fields["open_review_snippets"] = "metadata.review_comments/decision_letters"
        if enrichment and enrichment.provenance_fields:
            provenance_fields.update({str(key): str(value) for key, value in enrichment.provenance_fields.items()})

        completeness = _bundle_completeness(
            methods_text,
            results_text,
            figure_captions,
            table_snippets,
            resource_identifiers,
            trial_registry_ids,
            open_review_snippets,
        )
        if (
            completeness != AutoReviewBundleCompleteness.REVIEW_READY
            and methods_text
            and results_text
            and _has_resource_release_signal(
                paper,
                paper.title,
                abstract_text,
                methods_text,
                results_text,
                " ".join(figure_captions),
                " ".join(table_snippets),
            )
        ):
            completeness = AutoReviewBundleCompleteness.REVIEW_READY
        notes: List[str] = []
        if enrichment and enrichment.notes:
            notes.extend(str(item) for item in enrichment.notes)
        if methods_inferred_from_abstract:
            notes.append("methods inferred from abstract for auto-review bundling")
        if results_inferred_from_abstract:
            notes.append("results inferred from abstract for auto-review bundling")
        if results_inferred_from_figures:
            notes.append("results inferred from figure captions for auto-review bundling")
        if completeness == AutoReviewBundleCompleteness.METADATA_ONLY:
            notes.append("bundle is metadata-only and will be capped to stress_candidate")
        elif completeness == AutoReviewBundleCompleteness.PARTIAL:
            notes.append("bundle has partial evidence and will receive low-confidence auto review")

        bundles.append(
            AutoReviewSourceBundle(
                paper_id=paper.paper_id,
                bundle_completeness=completeness,
                abstract_text=abstract_text,
                methods_text=methods_text,
                results_text=results_text,
                figure_captions=tuple(figure_captions),
                table_snippets=tuple(table_snippets),
                figure_reference_snippets=tuple(figure_reference_snippets),
                table_reference_snippets=tuple(table_reference_snippets),
                resource_identifiers=tuple(resource_identifiers),
                trial_registry_ids=tuple(trial_registry_ids),
                open_review_snippets=tuple(open_review_snippets),
                provenance_fields=provenance_fields,
                notes=tuple(notes),
            )
        )
    return tuple(bundles)


def audit_auto_review_source_bundles(
    bundles: Sequence[AutoReviewSourceBundle],
) -> AutoReviewSourceBundleAuditReport:
    completeness_counts = Counter(bundle.bundle_completeness.value for bundle in bundles)
    methods_text_count = sum(1 for bundle in bundles if bundle.methods_text)
    results_text_count = sum(1 for bundle in bundles if bundle.results_text)
    figure_caption_count = sum(1 for bundle in bundles if bundle.figure_captions)
    table_snippet_count = sum(1 for bundle in bundles if bundle.table_snippets)
    figure_reference_snippet_count = sum(1 for bundle in bundles if bundle.figure_reference_snippets)
    table_reference_snippet_count = sum(1 for bundle in bundles if bundle.table_reference_snippets)
    resource_identifier_count = sum(1 for bundle in bundles if bundle.resource_identifiers)
    trial_registry_count = sum(1 for bundle in bundles if bundle.trial_registry_ids)
    open_review_snippet_count = sum(1 for bundle in bundles if bundle.open_review_snippets)
    provenance_warning_paper_ids = tuple(
        bundle.paper_id
        for bundle in bundles
        if not bundle.provenance_fields or "abstract" not in bundle.provenance_fields
    )
    notes: List[str] = []
    if completeness_counts.get(AutoReviewBundleCompleteness.METADATA_ONLY.value, 0):
        notes.append("metadata-only bundles are capped to stress_candidate in auto-only mode")
    return AutoReviewSourceBundleAuditReport(
        generated_at=_utc_timestamp(),
        total_bundles=len(bundles),
        completeness_counts=dict(completeness_counts),
        methods_text_count=methods_text_count,
        results_text_count=results_text_count,
        figure_caption_count=figure_caption_count,
        table_snippet_count=table_snippet_count,
        figure_reference_snippet_count=figure_reference_snippet_count,
        table_reference_snippet_count=table_reference_snippet_count,
        resource_identifier_count=resource_identifier_count,
        trial_registry_count=trial_registry_count,
        open_review_snippet_count=open_review_snippet_count,
        provenance_warning_paper_ids=provenance_warning_paper_ids,
        notes=tuple(notes),
    )


def _has_limitation_signal(bundle: AutoReviewSourceBundle) -> bool:
    corpus = _join_non_empty((bundle.abstract_text, bundle.results_text, " ".join(bundle.open_review_snippets)))
    return bool(_LIMITATION_PATTERN.search(corpus))


def _has_figure_table_signal(bundle: AutoReviewSourceBundle) -> bool:
    if bundle.figure_captions or bundle.table_snippets:
        return True
    corpus = _join_non_empty((bundle.results_text, bundle.abstract_text))
    return bool(_FIGURE_TABLE_PATTERN.search(corpus))


def _has_grounded_figure_table_support(bundle: AutoReviewSourceBundle) -> bool:
    return bool(
        (bundle.figure_captions and bundle.figure_reference_snippets)
        or (bundle.table_snippets and bundle.table_reference_snippets)
    )


def _has_methods_results_signal(bundle: AutoReviewSourceBundle) -> bool:
    corpus = _join_non_empty((bundle.methods_text, bundle.results_text, bundle.abstract_text))
    return bool(_METHODS_RESULTS_PATTERN.search(corpus))


def _traceability_corpus(bundle: AutoReviewSourceBundle) -> str:
    return _join_non_empty(
        (
            bundle.abstract_text,
            bundle.methods_text,
            bundle.results_text,
            " ".join(bundle.figure_captions),
            " ".join(bundle.table_snippets),
            " ".join(bundle.figure_reference_snippets),
            " ".join(bundle.table_reference_snippets),
            " ".join(bundle.resource_identifiers),
            " ".join(bundle.trial_registry_ids),
        )
    ).lower()


def _has_quantitative_result_signal(bundle: AutoReviewSourceBundle) -> bool:
    corpus = _join_non_empty((bundle.abstract_text, bundle.methods_text, bundle.results_text))
    return bool(_QUANTITATIVE_RESULT_PATTERN.search(corpus))


def _traceability_outcome(paper: SourcePaper, bundle: AutoReviewSourceBundle) -> DomainOutcome:
    if bundle.resource_identifiers or bundle.trial_registry_ids:
        return DomainOutcome.PASS

    has_structured_evidence = bool(
        bundle.methods_text
        and bundle.results_text
        and (bundle.figure_captions or bundle.table_snippets or _has_figure_table_signal(bundle))
    )
    corpus = _traceability_corpus(bundle)

    if paper.study_class == StudyClass.HUMAN_INTERVENTIONAL:
        if has_structured_evidence and (
            "trial" in corpus
            or "randomized" in corpus
            or "intervention" in corpus
            or "primary endpoint" in corpus
        ):
            return DomainOutcome.PASS
    elif paper.study_class == StudyClass.HUMAN_OBSERVATIONAL:
        if has_structured_evidence or (bundle.methods_text and bundle.results_text and _has_quantitative_result_signal(bundle)):
            return DomainOutcome.PASS
    elif paper.study_class == StudyClass.SYSTEMATIC_REVIEW_META_ANALYSIS:
        if bundle.methods_text and bundle.results_text and (
            "systematic review" in corpus or "meta-analysis" in corpus or "meta analysis" in corpus
        ):
            return DomainOutcome.PASS
    elif paper.study_class == StudyClass.ANIMAL_PRECLINICAL:
        if has_structured_evidence:
            return DomainOutcome.PASS
    elif paper.study_class == StudyClass.MECHANISTIC_EXPERIMENTAL:
        if has_structured_evidence:
            return DomainOutcome.PASS
    elif paper.study_class == StudyClass.METHODS_RESOURCE:
        if bundle.methods_text and (
            has_structured_evidence
            or any(token in corpus for token in ("protocol", "resource", "database", "toolkit", "benchmark", "atlas"))
        ):
            return DomainOutcome.PASS

    if paper.metadata.get("doi") or paper.metadata.get("pmid") or paper.metadata.get("pmcid"):
        return DomainOutcome.BORDERLINE
    return DomainOutcome.FAIL


def _standard_evidence_available(
    paper: SourcePaper,
    bundle: AutoReviewSourceBundle,
    standard: StandardId,
) -> bool:
    overlays = set(paper.modality_overlays)
    has_structured_evidence = bool(
        bundle.methods_text
        and bundle.results_text
        and (bundle.figure_captions or bundle.table_snippets or _has_figure_table_signal(bundle))
    )
    corpus = _join_non_empty(
        (
            bundle.abstract_text,
            bundle.methods_text,
            bundle.results_text,
            " ".join(bundle.figure_captions),
            " ".join(bundle.table_snippets),
            " ".join(bundle.figure_reference_snippets),
            " ".join(bundle.table_reference_snippets),
            " ".join(bundle.resource_identifiers),
            " ".join(bundle.trial_registry_ids),
            paper.title,
        )
    ).lower()
    if standard.value.startswith("consort"):
        return bool(bundle.trial_registry_ids or (bundle.methods_text and bundle.results_text))
    if standard.value.startswith("strobe"):
        return bool(bundle.methods_text and bundle.results_text)
    if standard in {StandardId.PRISMA_2020, StandardId.AMSTAR_2}:
        return "systematic review" in corpus or "meta-analysis" in corpus or "meta analysis" in corpus
    if standard.value.startswith("arrive"):
        return bool(bundle.methods_text and bundle.results_text)
    if standard == StandardId.MDAR:
        return bool(bundle.methods_text or bundle.results_text)
    if standard == StandardId.REMARK:
        return bool(
            "biomarker" in corpus
            or (
                ModalityOverlay.BIOMARKER_PROGNOSTIC in overlays
                and bundle.methods_text
                and bundle.results_text
                and any(
                    token in corpus
                    for token in (
                        "hazard ratio",
                        "survival",
                        "mortality",
                        "association",
                        "predict",
                        "prognos",
                        "risk",
                        "regression",
                    )
                )
            )
        )
    if standard == StandardId.MIAME_MINSEQE:
        return bool(
            bundle.resource_identifiers
            or "rna-seq" in corpus
            or "microarray" in corpus
            or (
                ModalityOverlay.OMICS_TRANSCRIPTOMICS in overlays
                and has_structured_evidence
                and any(
                    token in corpus
                    for token in (
                        "transcript",
                        "rna",
                        "gene expression",
                        "sequencing",
                        "expression profile",
                    )
                )
            )
        )
    if standard == StandardId.MIXS_MIMARKS:
        return bool(
            "metagenom" in corpus
            or "16s" in corpus
            or (
                ModalityOverlay.SEQUENCE_METAGENOMICS in overlays
                and has_structured_evidence
                and any(
                    token in corpus
                    for token in (
                        "microbiome",
                        "microbiota",
                        "virome",
                        "viral",
                        "sequencing",
                        "metagenom",
                    )
                )
            )
        )
    if standard == StandardId.MIAPE_PROTEOMEXCHANGE:
        return bool(
            "proteom" in corpus
            or bool(bundle.resource_identifiers)
            or (
                ModalityOverlay.PROTEOMICS_MASSSPEC in overlays
                and has_structured_evidence
                and any(
                    token in corpus
                    for token in (
                        "protein complex",
                        "mass spec",
                        "mass spectrometry",
                        "peptide",
                        "spectra",
                        "atlas",
                        "database",
                        "retrieval",
                    )
                )
            )
        )
    if standard == StandardId.WWPDB_TRACEABILITY:
        return "pdb" in corpus or bool(bundle.resource_identifiers)
    if standard == StandardId.EML_DARWIN_CORE:
        return "ecology" in corpus or "biodiversity" in corpus
    if standard == StandardId.MIQE_2_0:
        return "qpcr" in corpus or "pcr" in corpus
    if standard == StandardId.STRENDA:
        return _has_enzymology_signal(corpus)
    if standard == StandardId.REUSE_TRACEABILITY:
        return bool(bundle.resource_identifiers or bundle.methods_text)
    return bool(bundle.methods_text or bundle.results_text or bundle.resource_identifiers)


def _overlay_has_direct_evidence(
    overlay: ModalityOverlay,
    bundle: AutoReviewSourceBundle,
) -> bool:
    corpus = _join_non_empty(
        (
            bundle.abstract_text,
            bundle.methods_text,
            bundle.results_text,
            " ".join(bundle.figure_captions),
            " ".join(bundle.table_snippets),
        )
    ).lower()
    if overlay == ModalityOverlay.ENZYMOLOGY:
        return _has_enzymology_signal(corpus)
    if overlay == ModalityOverlay.BIOMARKER_PROGNOSTIC:
        return any(token in corpus for token in ("biomarker", "hazard ratio", "roc curve", "predictive", "prognostic"))
    if overlay == ModalityOverlay.OMICS_TRANSCRIPTOMICS:
        return any(token in corpus for token in ("rna seq", "rna-seq", "transcriptome", "microarray", "scrna"))
    if overlay == ModalityOverlay.SEQUENCE_METAGENOMICS:
        return any(token in corpus for token in ("metagenom", "microbiome", "16s", "amplicon", "sequencing"))
    if overlay == ModalityOverlay.PROTEOMICS_MASSSPEC:
        return any(token in corpus for token in ("proteom", "mass spectrometry", "mass spec", "peptide", "spectra"))
    if overlay == ModalityOverlay.STRUCTURAL_BIOPHYSICS:
        return any(token in corpus for token in ("pdb", "structure", "cryo em", "x ray"))
    if overlay == ModalityOverlay.ECOLOGY_BIODIVERSITY:
        return any(token in corpus for token in ("ecology", "biodiversity", "species", "habitat", "gbif"))
    if overlay == ModalityOverlay.QPCR:
        return any(token in corpus for token in ("qpcr", "rt qpcr", "rt-qpcr", "quantitative pcr"))
    return False


def _effective_auto_review_paper(
    paper: SourcePaper,
    bundle: AutoReviewSourceBundle,
) -> SourcePaper:
    if not paper.modality_overlays:
        return paper
    supported_overlays = tuple(
        overlay for overlay in paper.modality_overlays if _overlay_has_direct_evidence(overlay, bundle)
    )
    if supported_overlays == paper.modality_overlays:
        return paper
    return replace(paper, modality_overlays=supported_overlays)


def _domain_has_direct_evidence(domain: str, bundle: AutoReviewSourceBundle) -> bool:
    if domain in {
        ScientificCriticalDomain.DESIGN_ANALYSIS_CREDIBILITY.value,
        WritingCriticalDomain.ABSTRACT_RESULT_ALIGNMENT.value,
    }:
        return bool(bundle.methods_text and (bundle.results_text or _bundle_has_resource_release_signal(bundle)))
    if domain == ScientificCriticalDomain.MINIMAL_INTERPRETABLE_CORE.value:
        return bool(bundle.methods_text or bundle.results_text or bundle.figure_captions or bundle.table_snippets)
    if domain == ScientificCriticalDomain.REQUIRED_TRACEABILITY.value:
        if bundle.resource_identifiers or bundle.trial_registry_ids:
            return True
        if bundle.methods_text and bundle.results_text and _bundle_has_resource_release_signal(bundle):
            return True
        if bundle.methods_text and bundle.results_text and _has_quantitative_result_signal(bundle):
            return True
        return bool(
            bundle.methods_text
            and bundle.results_text
            and (bundle.figure_captions or bundle.table_snippets or _has_figure_table_signal(bundle))
        )
    if domain == ScientificCriticalDomain.CLAIM_MODE_ALIGNMENT.value:
        return bool(bundle.abstract_text and (bundle.results_text or bundle.methods_text))
    if domain == ScientificSupportingDomain.REPRODUCIBILITY_SUPPORT.value:
        return bool(
            bundle.resource_identifiers
            or bundle.trial_registry_ids
            or bundle.methods_text
            or (bundle.methods_text and _bundle_has_resource_release_signal(bundle))
        )
    if domain == ScientificSupportingDomain.RESOURCE_SPECIFICITY.value:
        return bool(
            bundle.resource_identifiers
            or (bundle.methods_text and _bundle_has_resource_release_signal(bundle))
        )
    if domain == WritingCriticalDomain.NARRATIVE_COHERENCE.value:
        return bool(bundle.abstract_text and (bundle.methods_text or bundle.results_text))
    if domain == WritingCriticalDomain.METHODS_CLARITY.value:
        return bool(bundle.methods_text)
    if domain == WritingCriticalDomain.FIGURE_TABLE_GROUNDING.value:
        return bool(
            _has_grounded_figure_table_support(bundle)
            or (bundle.methods_text and _bundle_has_resource_release_signal(bundle))
        )
    if domain == WritingCriticalDomain.LIMITATION_UNCERTAINTY_DISCLOSURE.value:
        return _has_limitation_signal(bundle)
    if domain == WritingSupportingDomain.TITLE_SCOPE_ALIGNMENT.value:
        return bool(bundle.abstract_text)
    if domain == WritingSupportingDomain.CITATION_CONTEXTUALIZATION.value:
        return bool(bundle.open_review_snippets or bundle.resource_identifiers)
    if domain == ScientificCriticalDomain.INTEGRITY_STATUS.value:
        return True
    return False


def _deterministic_precheck(
    paper: SourcePaper,
    bundle: AutoReviewSourceBundle,
    packaging_review: Optional[PackagingReview] = None,
) -> Dict[str, object]:
    effective_paper = _effective_auto_review_paper(paper, bundle)
    excluded_reasons: List[str] = []
    cap_reasons: List[str] = []
    skip_writing = False
    if paper.publication_status in {
        PublicationStatus.RETRACTED,
        PublicationStatus.WITHDRAWN,
        PublicationStatus.REMOVED,
    }:
        excluded_reasons.append(f"publication_status={paper.publication_status.value}")
    if paper.partial_retraction_invalidates_core_claims:
        excluded_reasons.append("partial_retraction_invalidates_core_claims")
    if bundle.bundle_completeness == AutoReviewBundleCompleteness.METADATA_ONLY:
        cap_reasons.append("bundle_completeness_metadata_only")
    elif bundle.bundle_completeness == AutoReviewBundleCompleteness.PARTIAL:
        cap_reasons.append("bundle_completeness_partial")
    if not (
        bundle.methods_text
        or bundle.results_text
        or bundle.figure_captions
        or bundle.table_snippets
        or bundle.resource_identifiers
        or bundle.trial_registry_ids
    ):
        skip_writing = True
        cap_reasons.append("writing_skipped_insufficient_evidence")
    if paper.publication_status == PublicationStatus.PREPRINT:
        cap_reasons.append("preprint_shadow_only")
    if packaging_review and paper.controlled_access_human_data and not packaging_review.controlled_access_rule_satisfied:
        cap_reasons.append("controlled_access_no_safe_artifact_path")
    missing_standard_evidence = tuple(
        standard
        for standard in required_standards_for_paper(effective_paper)
        if not _standard_evidence_available(effective_paper, bundle, standard)
    )
    return {
        "excluded_reasons": tuple(excluded_reasons),
        "cap_reasons": tuple(cap_reasons),
        "skip_writing": skip_writing,
        "missing_standard_evidence": missing_standard_evidence,
    }


def _fingerprint(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest().upper()


def _render_prompt(role: AutoReviewRole, paper: SourcePaper, bundle: AutoReviewSourceBundle) -> str:
    return "\n".join(
        [
            f"role={role.value}",
            f"paper_id={paper.paper_id}",
            f"title={paper.title}",
            f"study_class={paper.study_class.value}",
            f"claim_mode={paper.claim_mode.value}",
            f"bundle_completeness={bundle.bundle_completeness.value}",
            f"abstract={bundle.abstract_text}",
            f"methods={bundle.methods_text}",
            f"results={bundle.results_text}",
            f"figure_captions={' | '.join(bundle.figure_captions)}",
            f"table_snippets={' | '.join(bundle.table_snippets)}",
            f"figure_reference_snippets={' | '.join(bundle.figure_reference_snippets)}",
            f"table_reference_snippets={' | '.join(bundle.table_reference_snippets)}",
            f"resource_identifiers={' | '.join(bundle.resource_identifiers)}",
            f"trial_registry_ids={' | '.join(bundle.trial_registry_ids)}",
            f"open_review_snippets={' | '.join(bundle.open_review_snippets)}",
        ]
    )


def _downgrade(value: DomainOutcome) -> DomainOutcome:
    if value == DomainOutcome.PASS:
        return DomainOutcome.BORDERLINE
    if value == DomainOutcome.BORDERLINE:
        return DomainOutcome.FAIL
    return value


def _base_scientific_votes(
    paper: SourcePaper,
    bundle: AutoReviewSourceBundle,
    missing_standard_evidence: Sequence[StandardId],
) -> Tuple[Dict[ScientificCriticalDomain, DomainOutcome], Dict[ScientificSupportingDomain, DomainOutcome], Tuple[str, ...]]:
    resource_release = _bundle_has_resource_release_signal(bundle)
    critical: Dict[ScientificCriticalDomain, DomainOutcome] = {
        ScientificCriticalDomain.INTEGRITY_STATUS: DomainOutcome.PASS,
        ScientificCriticalDomain.DESIGN_ANALYSIS_CREDIBILITY: DomainOutcome.PASS
        if (
            (bundle.methods_text and bundle.results_text)
            or (paper.study_class == StudyClass.METHODS_RESOURCE and bundle.methods_text and resource_release)
        )
        else (DomainOutcome.BORDERLINE if _has_methods_results_signal(bundle) or (bundle.methods_text and resource_release) else DomainOutcome.FAIL),
        ScientificCriticalDomain.MINIMAL_INTERPRETABLE_CORE: DomainOutcome.PASS
        if (
            bundle.bundle_completeness == AutoReviewBundleCompleteness.REVIEW_READY
            or (paper.study_class == StudyClass.METHODS_RESOURCE and bundle.methods_text and resource_release)
        )
        else (DomainOutcome.BORDERLINE if bundle.bundle_completeness == AutoReviewBundleCompleteness.PARTIAL else DomainOutcome.FAIL),
        ScientificCriticalDomain.REQUIRED_TRACEABILITY: _traceability_outcome(paper, bundle),
        ScientificCriticalDomain.CLAIM_MODE_ALIGNMENT: DomainOutcome.PASS
        if bundle.abstract_text and (bundle.results_text or bundle.methods_text or resource_release)
        else DomainOutcome.BORDERLINE,
    }
    supporting: Dict[ScientificSupportingDomain, DomainOutcome] = {
        ScientificSupportingDomain.REPRODUCIBILITY_SUPPORT: DomainOutcome.PASS
        if bundle.resource_identifiers or bundle.trial_registry_ids or (paper.study_class == StudyClass.METHODS_RESOURCE and bundle.methods_text and resource_release)
        else (DomainOutcome.BORDERLINE if bundle.methods_text else DomainOutcome.FAIL),
        ScientificSupportingDomain.RESOURCE_SPECIFICITY: DomainOutcome.PASS
        if bundle.resource_identifiers or (paper.study_class == StudyClass.METHODS_RESOURCE and bundle.methods_text and resource_release)
        else (DomainOutcome.BORDERLINE if bundle.methods_text else DomainOutcome.FAIL),
    }
    insufficient: List[str] = []
    if missing_standard_evidence:
        insufficient.extend(standard.value for standard in missing_standard_evidence)
        critical[ScientificCriticalDomain.REQUIRED_TRACEABILITY] = _downgrade(
            critical[ScientificCriticalDomain.REQUIRED_TRACEABILITY]
        )
    return critical, supporting, tuple(insufficient)


def _base_writing_votes(
    paper: SourcePaper,
    bundle: AutoReviewSourceBundle,
) -> Tuple[Dict[WritingCriticalDomain, DomainOutcome], Tuple[str, ...]]:
    resource_release = _bundle_has_resource_release_signal(bundle)
    votes: Dict[WritingCriticalDomain, DomainOutcome] = {
        WritingCriticalDomain.ABSTRACT_RESULT_ALIGNMENT: DomainOutcome.PASS
        if bundle.abstract_text and (bundle.results_text or (paper.study_class == StudyClass.METHODS_RESOURCE and bundle.methods_text and resource_release))
        else DomainOutcome.BORDERLINE,
        WritingCriticalDomain.NARRATIVE_COHERENCE: DomainOutcome.PASS
        if bundle.abstract_text and (bundle.methods_text or bundle.results_text)
        else DomainOutcome.BORDERLINE,
        WritingCriticalDomain.METHODS_CLARITY: DomainOutcome.PASS
        if bundle.methods_text
        else (DomainOutcome.BORDERLINE if bundle.bundle_completeness != AutoReviewBundleCompleteness.METADATA_ONLY else DomainOutcome.FAIL),
        WritingCriticalDomain.FIGURE_TABLE_GROUNDING: DomainOutcome.PASS
        if _has_grounded_figure_table_support(bundle)
        else (
            DomainOutcome.BORDERLINE
            if _has_figure_table_signal(bundle) or (paper.study_class == StudyClass.METHODS_RESOURCE and bundle.methods_text and resource_release)
            else DomainOutcome.FAIL
        ),
        WritingCriticalDomain.LIMITATION_UNCERTAINTY_DISCLOSURE: DomainOutcome.PASS
        if _has_limitation_signal(bundle)
        else DomainOutcome.BORDERLINE,
    }
    insufficient: List[str] = []
    if not bundle.methods_text:
        insufficient.append(WritingCriticalDomain.METHODS_CLARITY.value)
    if not _has_grounded_figure_table_support(bundle):
        insufficient.append(WritingCriticalDomain.FIGURE_TABLE_GROUNDING.value)
    return votes, tuple(insufficient)


def _build_auto_panel_vote(
    paper: SourcePaper,
    bundle: AutoReviewSourceBundle,
    role: AutoReviewRole,
    model_id: str,
    profile: ExecutionProfile,
    temperature: float,
    top_p: float,
    seed: int,
    packaging_review: Optional[PackagingReview] = None,
) -> AutoPanelVote:
    precheck = _deterministic_precheck(paper, bundle, packaging_review=packaging_review)
    critical, supporting, insufficient_scientific = _base_scientific_votes(
        paper,
        bundle,
        precheck["missing_standard_evidence"],
    )
    writing_votes, insufficient_writing = _base_writing_votes(paper, bundle)
    insufficient = list(insufficient_scientific) + list(insufficient_writing)

    if role == AutoReviewRole.EVIDENCE_SKEPTIC:
        for domain in list(critical):
            if critical[domain] != DomainOutcome.FAIL and not _domain_has_direct_evidence(domain.value, bundle):
                critical[domain] = _downgrade(critical[domain])
                insufficient.append(domain.value)
        for domain in list(supporting):
            if supporting[domain] == DomainOutcome.PASS and not _domain_has_direct_evidence(domain.value, bundle):
                supporting[domain] = DomainOutcome.BORDERLINE
                insufficient.append(domain.value)
        for domain in list(writing_votes):
            if writing_votes[domain] != DomainOutcome.FAIL and not _domain_has_direct_evidence(domain.value, bundle):
                writing_votes[domain] = _downgrade(writing_votes[domain])
                insufficient.append(domain.value)
    elif role == AutoReviewRole.WRITING_REVIEWER:
        if bundle.bundle_completeness == AutoReviewBundleCompleteness.METADATA_ONLY:
            critical[ScientificCriticalDomain.DESIGN_ANALYSIS_CREDIBILITY] = _downgrade(
                critical[ScientificCriticalDomain.DESIGN_ANALYSIS_CREDIBILITY]
            )
        if not bundle.results_text:
            writing_votes[WritingCriticalDomain.ABSTRACT_RESULT_ALIGNMENT] = _downgrade(
                writing_votes[WritingCriticalDomain.ABSTRACT_RESULT_ALIGNMENT]
            )
    else:
        if bundle.bundle_completeness == AutoReviewBundleCompleteness.PARTIAL:
            supporting[ScientificSupportingDomain.REPRODUCIBILITY_SUPPORT] = DomainOutcome.BORDERLINE

    if precheck["skip_writing"]:
        writing_votes = {}

    prompt = _render_prompt(role, paper, bundle)
    prompt_fingerprint = _fingerprint(role.value, prompt)
    model_fingerprint = _fingerprint(
        profile.profile_id,
        model_id,
        f"temperature={temperature}",
        f"top_p={top_p}",
        f"seed={seed}",
    )
    rationale = (
        f"{role.value} reviewed a {bundle.bundle_completeness.value} bundle with "
        f"{len(precheck['missing_standard_evidence'])} missing-standard-evidence flags."
    )
    notes: List[str] = []
    if precheck["cap_reasons"]:
        notes.append("cap_reasons=" + ",".join(precheck["cap_reasons"]))
    if precheck["excluded_reasons"]:
        notes.append("excluded_reasons=" + ",".join(precheck["excluded_reasons"]))
    return AutoPanelVote(
        paper_id=paper.paper_id,
        role=role,
        critical_domain_votes=critical,
        supporting_domain_votes=supporting,
        writing_domain_votes=writing_votes,
        insufficient_evidence_flags=tuple(sorted(set(insufficient))),
        rationale=rationale,
        prompt_fingerprint=prompt_fingerprint,
        model_fingerprint=model_fingerprint,
        notes=tuple(notes),
    )


def run_auto_paper_reviews(
    papers: Sequence[SourcePaper],
    bundles: Sequence[AutoReviewSourceBundle],
    execution_profile: ExecutionProfile,
    model_id: str,
    packaging_reviews: Sequence[PaperPackagingReviewRecord] = (),
    *,
    temperature: float = 0.0,
    top_p: float = 1.0,
    seed: int = 0,
) -> Tuple[AutoPanelVote, ...]:
    papers_by_id = {paper.paper_id: paper for paper in papers}
    packaging_by_paper = {record.paper_id: record.packaging_review for record in packaging_reviews}
    votes: List[AutoPanelVote] = []
    for bundle in bundles:
        paper = papers_by_id.get(bundle.paper_id)
        if paper is None:
            continue
        packaging_review = packaging_by_paper.get(bundle.paper_id)
        for role in (
            AutoReviewRole.SCIENTIFIC_REVIEWER,
            AutoReviewRole.WRITING_REVIEWER,
            AutoReviewRole.EVIDENCE_SKEPTIC,
        ):
            votes.append(
                _build_auto_panel_vote(
                    paper,
                    bundle,
                    role,
                    model_id=model_id,
                    profile=execution_profile,
                    temperature=temperature,
                    top_p=top_p,
                    seed=seed,
                    packaging_review=packaging_review,
                )
            )
    return tuple(votes)


def _majority_vote(values: Sequence[DomainOutcome]) -> DomainOutcome:
    if not values:
        return DomainOutcome.BORDERLINE
    counts = Counter(values)
    ordered = sorted(
        counts.items(),
        key=lambda item: (-item[1], {DomainOutcome.PASS: 0, DomainOutcome.BORDERLINE: 1, DomainOutcome.FAIL: 2}[item[0]]),
    )
    if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
        return DomainOutcome.BORDERLINE
    return ordered[0][0]


def _aggregate_domain_votes(
    bundle: AutoReviewSourceBundle,
    votes: Sequence[AutoPanelVote],
    domain_names: Sequence,
    accessor,
) -> Dict:
    aggregated = {}
    for domain in domain_names:
        values = [accessor(vote).get(domain) for vote in votes if accessor(vote).get(domain) is not None]
        values = [value for value in values if value is not None]
        if not values:
            continue
        outcome = _majority_vote(values)
        if (
            outcome == DomainOutcome.PASS
            and any(domain.value in vote.insufficient_evidence_flags for vote in votes)
            and not _domain_has_direct_evidence(domain.value, bundle)
        ):
            outcome = DomainOutcome.BORDERLINE
        aggregated[domain] = outcome
    return aggregated


def aggregate_auto_paper_reviews(
    papers: Sequence[SourcePaper],
    bundles: Sequence[AutoReviewSourceBundle],
    panel_votes: Sequence[AutoPanelVote],
) -> Tuple[AutoAggregatedPaperReviewRecord, ...]:
    papers_by_id = {paper.paper_id: paper for paper in papers}
    bundles_by_id = {bundle.paper_id: bundle for bundle in bundles}
    votes_by_paper: Dict[str, List[AutoPanelVote]] = {}
    for vote in panel_votes:
        votes_by_paper.setdefault(vote.paper_id, []).append(vote)

    records: List[AutoAggregatedPaperReviewRecord] = []
    for paper_id, votes in votes_by_paper.items():
        paper = papers_by_id.get(paper_id)
        bundle = bundles_by_id.get(paper_id)
        if paper is None or bundle is None:
            continue
        effective_paper = _effective_auto_review_paper(paper, bundle)
        scientific_review = ScientificReview(
            critical_domains=_aggregate_domain_votes(
                bundle,
                votes,
                tuple(ScientificCriticalDomain),
                lambda vote: vote.critical_domain_votes,
            ),
            supporting_domains=_aggregate_domain_votes(
                bundle,
                votes,
                tuple(ScientificSupportingDomain),
                lambda vote: vote.supporting_domain_votes,
            ),
            applied_standards=required_standards_for_paper(effective_paper),
            standard_outcomes={
                standard: (
                    DomainOutcome.PASS
                    if _standard_evidence_available(effective_paper, bundle, standard)
                    else DomainOutcome.BORDERLINE
                )
                for standard in required_standards_for_paper(effective_paper)
            },
            standard_notes={
                standard: (
                    "auto-review bundle contains direct evidence for this standard"
                    if _standard_evidence_available(effective_paper, bundle, standard)
                    else "auto-review bundle is missing direct evidence for this standard"
                )
                for standard in required_standards_for_paper(effective_paper)
            },
            notes=("review_origin=auto_panel",),
        )
        skip_writing = bundle.bundle_completeness == AutoReviewBundleCompleteness.METADATA_ONLY or not any(
            vote.writing_domain_votes for vote in votes
        )
        writing_review = WritingReview(
            critical_domains=(
                {}
                if skip_writing
                else _aggregate_domain_votes(
                    bundle,
                    votes,
                    tuple(WritingCriticalDomain),
                    lambda vote: vote.writing_domain_votes,
                )
            ),
            supporting_domains=(
                {}
                if skip_writing
                else {
                    WritingSupportingDomain.TITLE_SCOPE_ALIGNMENT: (
                        DomainOutcome.PASS if bundle.abstract_text else DomainOutcome.BORDERLINE
                    ),
                    WritingSupportingDomain.CITATION_CONTEXTUALIZATION: (
                        DomainOutcome.PASS
                        if bundle.open_review_snippets or bundle.resource_identifiers
                        else DomainOutcome.BORDERLINE
                    ),
                }
            ),
            notes=("review_origin=auto_panel",),
        )
        confidence = (
            AutoReviewConfidence.MEDIUM
            if bundle.bundle_completeness == AutoReviewBundleCompleteness.REVIEW_READY
            and not skip_writing
            and not any(vote.insufficient_evidence_flags for vote in votes)
            else AutoReviewConfidence.LOW
        )
        cap_reason = None
        if bundle.bundle_completeness == AutoReviewBundleCompleteness.METADATA_ONLY:
            cap_reason = "bundle_completeness_metadata_only"
        elif bundle.bundle_completeness == AutoReviewBundleCompleteness.PARTIAL:
            cap_reason = "bundle_completeness_partial"
        records.append(
            AutoAggregatedPaperReviewRecord(
                paper_id=paper_id,
                scientific_review=scientific_review,
                writing_review=writing_review,
                review_origin="auto_panel",
                confidence=confidence,
                skipped_writing_review=skip_writing,
                auto_release_cap_reason=cap_reason,
                notes=tuple(sorted({note for vote in votes for note in vote.notes})),
            )
        )
    return tuple(records)


def build_auto_paper_qualification_records(
    papers: Sequence[SourcePaper],
    bundles: Sequence[AutoReviewSourceBundle],
    aggregated_reviews: Sequence[AutoAggregatedPaperReviewRecord],
    packaging_reviews: Sequence[PaperPackagingReviewRecord],
    policy: Optional[PackagingPolicy] = None,
) -> Tuple[AutoQualificationRecord, ...]:
    papers_by_id = {paper.paper_id: paper for paper in papers}
    bundles_by_id = {bundle.paper_id: bundle for bundle in bundles}
    packaging_by_paper = {record.paper_id: record.packaging_review for record in packaging_reviews}
    records: List[AutoQualificationRecord] = []
    for aggregated in aggregated_reviews:
        paper = papers_by_id.get(aggregated.paper_id)
        bundle = bundles_by_id.get(aggregated.paper_id)
        packaging_review = packaging_by_paper.get(aggregated.paper_id)
        if paper is None or bundle is None or packaging_review is None:
            continue
        effective_paper = _effective_auto_review_paper(paper, bundle)

        scientific, integrity_disposition, required_standards, missing_standards, scientific_reasons = qualify_scientific(
            effective_paper,
            aggregated.scientific_review,
        )
        writing, writing_reasons = qualify_writing(aggregated.writing_review)
        packaging, packaging_reasons = qualify_packaging(paper, packaging_review, policy=policy)

        cap_reason = aggregated.auto_release_cap_reason
        candidate_tier = CandidateTier.EXCLUDED
        eligible_for_unit_extraction = False
        auto_reasons: List[str] = []

        if integrity_disposition != IntegrityDisposition.CLEAR:
            auto_reasons.append("non-clear integrity disposition blocks auto release")
        elif scientific in {PaperScientificQualification.C, PaperScientificQualification.Q}:
            auto_reasons.append("scientific qualification excludes paper from auto shadow release")
        elif packaging == PaperPackagingQualification.P3:
            auto_reasons.append("packaging qualification excludes paper from auto shadow release")
        elif paper.publication_status == PublicationStatus.PREPRINT:
            candidate_tier = CandidateTier.STRESS_CANDIDATE
            cap_reason = cap_reason or "preprint_shadow_only"
            auto_reasons.append("preprints are capped to stress_candidate in auto-only mode")
        elif bundle.bundle_completeness == AutoReviewBundleCompleteness.METADATA_ONLY:
            candidate_tier = CandidateTier.STRESS_CANDIDATE
            cap_reason = cap_reason or "bundle_completeness_metadata_only"
            auto_reasons.append("metadata-only bundles cannot become shadow candidates")
        elif bundle.bundle_completeness == AutoReviewBundleCompleteness.PARTIAL:
            candidate_tier = CandidateTier.STRESS_CANDIDATE
            cap_reason = cap_reason or "bundle_completeness_partial"
            auto_reasons.append("partial bundles are capped to stress_candidate")
        elif packaging == PaperPackagingQualification.P2:
            candidate_tier = CandidateTier.STRESS_CANDIDATE
            cap_reason = cap_reason or "packaging_p2"
            auto_reasons.append("P2 packaging is stress-only in auto mode")
        elif scientific == PaperScientificQualification.B:
            candidate_tier = CandidateTier.STRESS_CANDIDATE
            cap_reason = cap_reason or "scientific_b"
            auto_reasons.append("B-level scientific qualification is stress-only in auto mode")
        elif scientific == PaperScientificQualification.A and packaging == PaperPackagingQualification.P1:
            candidate_tier = CandidateTier.SHADOW_CANDIDATE
            eligible_for_unit_extraction = True
            auto_reasons.append("paper is shadow-ready under auto-only rules")
        else:
            auto_reasons.append("paper does not satisfy auto shadow eligibility")

        decision = PaperQualificationDecision(
            scientific=scientific,
            packaging=packaging,
            candidate_tier=candidate_tier,
            eligible_for_unit_extraction=eligible_for_unit_extraction,
            required_standards=required_standards,
            writing=writing,
            public_writing_eligible=False,
            missing_standards=missing_standards,
            integrity_disposition=integrity_disposition,
            reasons=tuple(
                list(scientific_reasons)
                + list(writing_reasons)
                + list(packaging_reasons)
                + auto_reasons
                + ["auto-only mode disables public gold and public writing eligibility"]
            ),
        )
        records.append(
            AutoQualificationRecord(
                paper_id=paper.paper_id,
                decision=decision,
                review_origin=aggregated.review_origin,
                confidence=aggregated.confidence,
                auto_release_cap_reason=cap_reason,
                judge_validation_ready=False,
                notes=tuple(note for note in aggregated.notes if note),
            )
        )
    return tuple(records)


def summarize_auto_review_batch(
    papers: Sequence[SourcePaper],
    bundles: Sequence[AutoReviewSourceBundle] = (),
    panel_votes: Sequence[AutoPanelVote] = (),
    aggregated_reviews: Sequence[AutoAggregatedPaperReviewRecord] = (),
    qualification_records: Sequence[AutoQualificationRecord] = (),
) -> AutoReviewBatchReport:
    completeness_counts = Counter(bundle.bundle_completeness.value for bundle in bundles)
    scientific_counts = Counter(record.decision.scientific.value for record in qualification_records)
    writing_counts = Counter(record.decision.writing.value for record in qualification_records)
    packaging_counts = Counter(record.decision.packaging.value for record in qualification_records)
    candidate_tier_counts = Counter(record.decision.candidate_tier.value for record in qualification_records)
    confidence_counts = Counter(record.confidence.value for record in qualification_records)
    return AutoReviewBatchReport(
        generated_at=_utc_timestamp(),
        total_papers=len(papers),
        source_bundle_count=len(bundles),
        panel_vote_count=len(panel_votes),
        aggregated_review_count=len(aggregated_reviews),
        qualification_count=len(qualification_records),
        completeness_counts=dict(completeness_counts),
        scientific_counts=dict(scientific_counts),
        writing_counts=dict(writing_counts),
        packaging_counts=dict(packaging_counts),
        candidate_tier_counts=dict(candidate_tier_counts),
        confidence_counts=dict(confidence_counts),
        eligible_for_unit_extraction_count=sum(
            1 for record in qualification_records if record.decision.eligible_for_unit_extraction
        ),
        skipped_writing_review_count=sum(1 for record in aggregated_reviews if record.skipped_writing_review),
        notes=("auto-only mode caps all decisions below public_gold_candidate",),
    )
