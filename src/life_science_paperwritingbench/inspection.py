from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .models import (
    ShadowInspectionDeltaReport,
    AutoQualificationRecord,
    AutoReviewSourceBundle,
    ShadowInspectionBatchReport,
    ShadowInspectionEntry,
    ShadowInspectionTaxonomyCategory,
    ShadowInspectionTaxonomyReport,
    SourcePaper,
    TaskBundle,
)
from .policy import AutoReviewConfidence, PaperWritingQualification, ReleaseTier


_FETCH_ERROR_NOTE_MARKER = "fetch_error"
_ABSTRACT_INFERRED_NOTE_MARKER = "inferred from abstract"
_UPSTREAM_BLOCKED_HTTP_MARKERS: Tuple[str, ...] = (
    "HTTP Error 400",
    "HTTP Error 401",
    "HTTP Error 403",
    "HTTP Error 404",
    "HTTP Error 410",
    "HTTP Error 451",
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _has_note_marker(notes: Sequence[str], marker: str) -> bool:
    return any(marker in (note or "") for note in notes)


def _has_abstract_inferred_only_signal(bundle: AutoReviewSourceBundle) -> bool:
    if not _has_note_marker(bundle.notes, _FETCH_ERROR_NOTE_MARKER):
        return False
    if not _has_note_marker(bundle.notes, _ABSTRACT_INFERRED_NOTE_MARKER):
        return False
    has_grounded_figures = bool(bundle.figure_captions) and bool(bundle.figure_reference_snippets)
    has_grounded_tables = bool(bundle.table_snippets) and bool(bundle.table_reference_snippets)
    if has_grounded_figures or has_grounded_tables:
        return False
    if bundle.resource_identifiers or bundle.trial_registry_ids:
        return False
    return True


def _has_upstream_blocked_signal(bundle: AutoReviewSourceBundle) -> bool:
    if not _has_abstract_inferred_only_signal(bundle):
        return False
    return any(
        _has_note_marker(bundle.notes, marker)
        for marker in _UPSTREAM_BLOCKED_HTTP_MARKERS
    )


def _focus_tags(
    *,
    paper: SourcePaper,
    record: AutoQualificationRecord,
    bundle: AutoReviewSourceBundle,
) -> Tuple[str, ...]:
    tags: List[str] = []
    if record.confidence == AutoReviewConfidence.LOW:
        tags.append("low_confidence")
    else:
        tags.append("medium_confidence")
    tags.append(f"writing_{record.decision.writing.value.lower()}")
    if bundle.bundle_completeness.value != "review_ready":
        tags.append(bundle.bundle_completeness.value)
    if len(paper.modality_overlays) > 1:
        tags.append("hybrid_overlay")
    if bundle.figure_captions:
        tags.append("figure_rich")
    if bundle.table_snippets:
        tags.append("table_rich")
    if bundle.figure_captions and bundle.figure_reference_snippets:
        tags.append("figure_grounded")
    if bundle.table_snippets and bundle.table_reference_snippets:
        tags.append("table_grounded")
    if bundle.resource_identifiers:
        tags.append("resource_ids")
    if bundle.trial_registry_ids:
        tags.append("trial_registry")
    if bundle.trial_registry_ids and bundle.trial_registry_reference_snippets:
        tags.append("trial_registry_grounded")
    if paper.claim_mode.value == "resource_release":
        tags.append("resource_release_claim")
        if _has_resource_release_grounding(bundle):
            tags.append("resource_release_grounded")
    if _has_abstract_inferred_only_signal(bundle):
        tags.append("abstract_inferred_only")
        if _has_upstream_blocked_signal(bundle):
            tags.append("fulltext_acquisition_blocked_upstream")
    return tuple(tags)


def _has_resource_release_grounding(bundle: AutoReviewSourceBundle) -> bool:
    if bundle.resource_identifiers:
        return True
    has_methods_results = bool(bundle.methods_text.strip()) and bool(bundle.results_text.strip())
    has_grounded_visual_evidence = (
        bool(bundle.figure_captions)
        and bool(bundle.figure_reference_snippets)
    ) or (
        bool(bundle.table_snippets)
        and bool(bundle.table_reference_snippets)
    )
    return has_methods_results and has_grounded_visual_evidence


def _evidence_snapshot(bundle: AutoReviewSourceBundle) -> Dict[str, int]:
    return {
        "abstract_text": int(bool(bundle.abstract_text.strip())),
        "methods_text": int(bool(bundle.methods_text.strip())),
        "results_text": int(bool(bundle.results_text.strip())),
        "figure_captions": len(bundle.figure_captions),
        "table_snippets": len(bundle.table_snippets),
        "figure_reference_snippets": len(bundle.figure_reference_snippets),
        "table_reference_snippets": len(bundle.table_reference_snippets),
        "resource_identifiers": len(bundle.resource_identifiers),
        "trial_registry_ids": len(bundle.trial_registry_ids),
        "trial_registry_reference_snippets": len(bundle.trial_registry_reference_snippets),
        "open_review_snippets": len(bundle.open_review_snippets),
    }


def _priority_tuple(
    *,
    paper: SourcePaper,
    record: AutoQualificationRecord,
    bundle: AutoReviewSourceBundle,
    task_bundle: TaskBundle,
) -> Tuple[int, int, int, int, str]:
    confidence_rank = 0 if record.confidence == AutoReviewConfidence.LOW else 1
    writing_rank = {
        PaperWritingQualification.W3: 0,
        PaperWritingQualification.W2: 1,
        PaperWritingQualification.W1: 2,
    }[record.decision.writing]
    hybrid_rank = 0 if len(paper.modality_overlays) > 1 else 1
    evidence_rank = -(
        len(bundle.figure_captions)
        + len(bundle.table_snippets)
        + len(bundle.resource_identifiers)
        + len(bundle.trial_registry_ids)
    )
    return (
        confidence_rank,
        writing_rank,
        hybrid_rank,
        evidence_rank,
        task_bundle.task_bundle_id,
    )


def build_shadow_inspection_batch(
    *,
    task_bundles: Sequence[TaskBundle],
    papers: Mapping[str, SourcePaper],
    auto_qualification_records: Mapping[str, AutoQualificationRecord],
    source_bundles: Mapping[str, AutoReviewSourceBundle],
    target_total: int = 30,
    include_holdout_buckets: Optional[Sequence[str]] = None,
) -> Tuple[ShadowInspectionEntry, ...]:
    if target_total <= 0:
        raise ValueError("target_total must be positive")

    eligible = [
        bundle
        for bundle in task_bundles
        if bundle.release_tier == ReleaseTier.SHADOW_GOLD
        and (not include_holdout_buckets or (bundle.holdout_bucket or "unassigned") in set(include_holdout_buckets))
    ]
    if not eligible:
        return ()

    grouped: Dict[Tuple[str, str], List[TaskBundle]] = {}
    for bundle in eligible:
        if bundle.paper_id not in papers:
            raise KeyError(f"missing source paper for task bundle {bundle.task_bundle_id}")
        if bundle.paper_id not in auto_qualification_records:
            raise KeyError(f"missing auto qualification record for task bundle {bundle.task_bundle_id}")
        if bundle.paper_id not in source_bundles:
            raise KeyError(f"missing source bundle for task bundle {bundle.task_bundle_id}")
        key = (bundle.task_family.value, bundle.study_class.value)
        grouped.setdefault(key, []).append(bundle)

    for key, items in grouped.items():
        grouped[key] = sorted(
            items,
            key=lambda bundle: _priority_tuple(
                paper=papers[bundle.paper_id],
                record=auto_qualification_records[bundle.paper_id],
                bundle=source_bundles[bundle.paper_id],
                task_bundle=bundle,
            ),
        )

    selected: List[TaskBundle] = []
    selected_papers = set()
    group_keys = sorted(grouped)
    while len(selected) < target_total:
        made_progress = False
        for key in group_keys:
            candidates = grouped[key]
            while candidates and candidates[0].paper_id in selected_papers:
                candidates.pop(0)
            if not candidates:
                continue
            candidate = candidates.pop(0)
            selected.append(candidate)
            selected_papers.add(candidate.paper_id)
            made_progress = True
            if len(selected) >= target_total:
                break
        if not made_progress:
            break

    if len(selected) < target_total:
        remaining = sorted(
            [
                bundle
                for bundles in grouped.values()
                for bundle in bundles
                if bundle.paper_id not in selected_papers
            ],
            key=lambda bundle: _priority_tuple(
                paper=papers[bundle.paper_id],
                record=auto_qualification_records[bundle.paper_id],
                bundle=source_bundles[bundle.paper_id],
                task_bundle=bundle,
            ),
        )
        for candidate in remaining:
            selected.append(candidate)
            selected_papers.add(candidate.paper_id)
            if len(selected) >= target_total:
                break

    entries = []
    for index, bundle in enumerate(selected, start=1):
        paper = papers[bundle.paper_id]
        record = auto_qualification_records[bundle.paper_id]
        source_bundle = source_bundles[bundle.paper_id]
        entries.append(
            ShadowInspectionEntry(
                inspection_id=f"INSPECT:{index:03d}:{bundle.task_bundle_id}",
                task_bundle_id=bundle.task_bundle_id,
                benchmark_unit_id=bundle.benchmark_unit_id,
                paper_id=bundle.paper_id or "",
                title=paper.title,
                publication_year=paper.publication_year,
                task_family=bundle.task_family,
                study_class=bundle.study_class,
                claim_mode=bundle.claim_mode,
                release_tier=bundle.release_tier,
                holdout_bucket=bundle.holdout_bucket or "unassigned",
                writing=record.decision.writing,
                confidence=record.confidence,
                bundle_completeness=source_bundle.bundle_completeness,
                modality_overlays=paper.modality_overlays,
                focus_tags=_focus_tags(paper=paper, record=record, bundle=source_bundle),
                evidence_snapshot=_evidence_snapshot(source_bundle),
                qualification_reasons=record.decision.reasons,
                source_bundle_notes=source_bundle.notes,
            )
        )
    return tuple(entries)


def summarize_shadow_inspection_batch(
    entries: Iterable[ShadowInspectionEntry],
    *,
    target_total: int,
    generated_at: Optional[str] = None,
) -> ShadowInspectionBatchReport:
    entries = tuple(entries)
    focus_tag_counts = Counter(
        tag
        for entry in entries
        for tag in entry.focus_tags
    )
    return ShadowInspectionBatchReport(
        generated_at=generated_at or _utc_timestamp(),
        target_total=target_total,
        selected_total=len(entries),
        task_family_counts=dict(Counter(entry.task_family.value for entry in entries)),
        study_class_counts=dict(Counter(entry.study_class.value for entry in entries)),
        claim_mode_counts=dict(Counter(entry.claim_mode.value for entry in entries)),
        writing_counts=dict(Counter(entry.writing.value for entry in entries)),
        confidence_counts=dict(Counter(entry.confidence.value for entry in entries)),
        completeness_counts=dict(Counter(entry.bundle_completeness.value for entry in entries)),
        holdout_bucket_counts=dict(Counter(entry.holdout_bucket for entry in entries)),
        focus_tag_counts=dict(focus_tag_counts),
        notes=(),
    )


def render_shadow_inspection_markdown(
    entries: Sequence[ShadowInspectionEntry],
    report: ShadowInspectionBatchReport,
) -> str:
    lines = [
        "# Shadow Inspection Batch",
        "",
        f"- Selected entries: {report.selected_total}",
        f"- Target total: {report.target_total}",
        f"- Holdout buckets: {dict(report.holdout_bucket_counts)}",
        f"- Task families: {dict(report.task_family_counts)}",
        f"- Study classes: {dict(report.study_class_counts)}",
        f"- Writing labels: {dict(report.writing_counts)}",
        f"- Confidence labels: {dict(report.confidence_counts)}",
        "",
    ]
    for index, entry in enumerate(entries, start=1):
        lines.extend(
            [
                f"## {index}. {entry.task_bundle_id}",
                "",
                f"- Title: {entry.title}",
                f"- Paper: {entry.paper_id}",
                f"- Year: {entry.publication_year}",
                f"- Task family: {entry.task_family.value}",
                f"- Study class: {entry.study_class.value}",
                f"- Claim mode: {entry.claim_mode.value}",
                f"- Writing: {entry.writing.value}",
                f"- Confidence: {entry.confidence.value}",
                f"- Bundle completeness: {entry.bundle_completeness.value}",
                f"- Holdout: {entry.holdout_bucket}",
                f"- Focus tags: {', '.join(entry.focus_tags) if entry.focus_tags else 'none'}",
                f"- Evidence snapshot: {dict(entry.evidence_snapshot)}",
                f"- Qualification reasons: {', '.join(entry.qualification_reasons) if entry.qualification_reasons else 'none'}",
                f"- Source bundle notes: {', '.join(entry.source_bundle_notes) if entry.source_bundle_notes else 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


_TAXONOMY_SPECS = {
    "low_confidence_shadow": {
        "label": "Low-confidence shadow decisions",
        "priority": "high",
        "recommended_actions": (
            "Inspect the underlying evidence snapshot before relaxing any pass thresholds.",
            "Compare low-confidence entries against nearby shadow papers to tighten borderline-to-pass rules.",
        ),
    },
    "writing_quality_risk": {
        "label": "Writing-quality risk",
        "priority": "high",
        "recommended_actions": (
            "Sample these entries first when refining writing-oriented prompts or heuristics.",
            "Track whether failures come from structure, hedging, or evidence narration before changing rules globally.",
        ),
    },
    "resource_release_specificity": {
        "label": "Resource-release specificity risk",
        "priority": "high",
        "recommended_actions": (
            "Strengthen resource-specificity checks for resource-release claims before promoting similar papers.",
            "Prefer explicit identifiers and reproducibility cues over broad release-language matches.",
        ),
    },
    "fulltext_acquisition_gap": {
        "label": "Full-text acquisition gap",
        "priority": "high",
        "recommended_actions": (
            "Retry full-text acquisition (publisher-native or Europe PMC) before re-running the shadow lane on these papers.",
            "Do not treat these cases as parser-labeling mistakes; the extraction substrate itself is missing.",
        ),
    },
    "fulltext_acquisition_blocked_upstream": {
        "label": "Full-text acquisition blocked upstream",
        "priority": "high",
        "recommended_actions": (
            "Do not retry via Europe PMC; the fetch returned a 4xx and the paper is likely non-OA or not indexed.",
            "Escalate to an alternate backend (NCBI PMC efetch) or a publisher-native / manual acquisition path; otherwise flag these papers for exclusion from the shadow lane.",
        ),
    },
    "identifier_sparse_low_confidence": {
        "label": "Identifier-sparse low-confidence cases",
        "priority": "high",
        "recommended_actions": (
            "Prioritize richer parser or accession extraction for entries without resource or registry identifiers.",
            "Avoid prompt-only fixes until identifier support is improved.",
        ),
    },
    "hybrid_overlay_complexity": {
        "label": "Hybrid-overlay complexity",
        "priority": "medium",
        "recommended_actions": (
            "Spot-check overlay-specific standards and grounding for mixed-modality papers.",
            "Confirm that modality-specific evidence is actually present before applying stricter overlay policies.",
        ),
    },
    "trial_registry_traceability": {
        "label": "Trial-registry traceability",
        "priority": "medium",
        "recommended_actions": (
            "Verify that registry identifiers and stated outcomes line up with the extracted evidence.",
            "Use this category when tuning interventional-paper traceability prompts.",
        ),
    },
    "figure_table_grounding": {
        "label": "Figure/table grounding",
        "priority": "medium",
        "recommended_actions": (
            "Inspect whether figure and table references are grounded in the extracted captions and snippets.",
            "Use these entries to improve parser-assisted evidence grounding before changing review thresholds.",
        ),
    },
    "stable_shadow_controls": {
        "label": "Stable shadow controls",
        "priority": "low",
        "recommended_actions": (
            "Keep a small control set around when auditing future prompt or parser changes.",
        ),
    },
}


def _taxonomy_categories_for_entry(entry: ShadowInspectionEntry) -> Tuple[str, ...]:
    categories: List[str] = []
    focus_tags = set(entry.focus_tags)
    reason_text = " ".join(reason.lower() for reason in entry.qualification_reasons)
    fulltext_gap = "abstract_inferred_only" in focus_tags

    if entry.confidence == AutoReviewConfidence.LOW:
        categories.append("low_confidence_shadow")
    if entry.writing == PaperWritingQualification.W3 or "writing domain" in reason_text:
        categories.append("writing_quality_risk")
    if (
        "resource_release_claim" in focus_tags
        and "resource_release_grounded" not in focus_tags
        and not fulltext_gap
    ):
        categories.append("resource_release_specificity")
    if fulltext_gap:
        categories.append("fulltext_acquisition_gap")
        if "fulltext_acquisition_blocked_upstream" in focus_tags:
            categories.append("fulltext_acquisition_blocked_upstream")
    if "hybrid_overlay" in focus_tags:
        categories.append("hybrid_overlay_complexity")
    if "trial_registry" in focus_tags and "trial_registry_grounded" not in focus_tags:
        categories.append("trial_registry_traceability")
    if ("figure_rich" in focus_tags and "figure_grounded" not in focus_tags) or (
        "table_rich" in focus_tags and "table_grounded" not in focus_tags
    ):
        categories.append("figure_table_grounding")
    if (
        entry.confidence == AutoReviewConfidence.LOW
        and entry.evidence_snapshot.get("resource_identifiers", 0) == 0
        and entry.evidence_snapshot.get("trial_registry_ids", 0) == 0
        and not fulltext_gap
    ):
        categories.append("identifier_sparse_low_confidence")

    if not categories:
        return ("stable_shadow_controls",)
    return tuple(dict.fromkeys(categories))


def build_shadow_inspection_taxonomy(
    entries: Sequence[ShadowInspectionEntry],
) -> Tuple[ShadowInspectionTaxonomyCategory, ...]:
    grouped: Dict[str, List[ShadowInspectionEntry]] = {}
    for entry in entries:
        for category_id in _taxonomy_categories_for_entry(entry):
            grouped.setdefault(category_id, []).append(entry)

    if not grouped:
        return ()

    categories: List[ShadowInspectionTaxonomyCategory] = []
    for category_id, category_entries in grouped.items():
        spec = _TAXONOMY_SPECS[category_id]
        categories.append(
            ShadowInspectionTaxonomyCategory(
                category_id=category_id,
                label=str(spec["label"]),
                priority=str(spec["priority"]),
                entry_count=len(category_entries),
                task_family_counts=dict(Counter(entry.task_family.value for entry in category_entries)),
                study_class_counts=dict(Counter(entry.study_class.value for entry in category_entries)),
                claim_mode_counts=dict(Counter(entry.claim_mode.value for entry in category_entries)),
                writing_counts=dict(Counter(entry.writing.value for entry in category_entries)),
                confidence_counts=dict(Counter(entry.confidence.value for entry in category_entries)),
                focus_tag_counts=dict(
                    Counter(tag for entry in category_entries for tag in entry.focus_tags)
                ),
                representative_inspection_ids=tuple(
                    entry.inspection_id for entry in category_entries[:5]
                ),
                representative_task_bundle_ids=tuple(
                    entry.task_bundle_id for entry in category_entries[:5]
                ),
                recommended_actions=tuple(str(item) for item in spec["recommended_actions"]),
            )
        )

    priority_rank = {"high": 0, "medium": 1, "low": 2}
    return tuple(
        sorted(
            categories,
            key=lambda category: (
                priority_rank.get(category.priority, 9),
                -category.entry_count,
                category.category_id,
            ),
        )
    )


def summarize_shadow_inspection_taxonomy(
    entries: Sequence[ShadowInspectionEntry],
    categories: Sequence[ShadowInspectionTaxonomyCategory],
    *,
    generated_at: Optional[str] = None,
) -> ShadowInspectionTaxonomyReport:
    return ShadowInspectionTaxonomyReport(
        generated_at=generated_at or _utc_timestamp(),
        total_entries=len(entries),
        category_count=len(categories),
        priority_counts=dict(Counter(category.priority for category in categories)),
        categories=tuple(categories),
        notes=(
            "taxonomy categories are overlapping and do not partition the inspection slice",
        ),
    )


def render_shadow_inspection_taxonomy_markdown(
    report: ShadowInspectionTaxonomyReport,
) -> str:
    lines = [
        "# Shadow Inspection Taxonomy",
        "",
        f"- Total inspection entries: {report.total_entries}",
        f"- Categories: {report.category_count}",
        f"- Priority counts: {dict(report.priority_counts)}",
        "",
    ]
    for note in report.notes:
        lines.append(f"- Note: {note}")
    if report.notes:
        lines.append("")

    for index, category in enumerate(report.categories, start=1):
        lines.extend(
            [
                f"## {index}. {category.label}",
                "",
                f"- Category id: {category.category_id}",
                f"- Priority: {category.priority}",
                f"- Entry count: {category.entry_count}",
                f"- Task families: {dict(category.task_family_counts)}",
                f"- Study classes: {dict(category.study_class_counts)}",
                f"- Claim modes: {dict(category.claim_mode_counts)}",
                f"- Writing labels: {dict(category.writing_counts)}",
                f"- Confidence labels: {dict(category.confidence_counts)}",
                f"- Focus tags: {dict(category.focus_tag_counts)}",
                f"- Representative inspections: {list(category.representative_inspection_ids)}",
                f"- Representative task bundles: {list(category.representative_task_bundle_ids)}",
                "- Recommended actions:",
            ]
        )
        for action in category.recommended_actions:
            lines.append(f"  - {action}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _delta_mapping(previous: Mapping[str, int], current: Mapping[str, int]) -> Dict[str, int]:
    keys = set(previous) | set(current)
    return {
        key: int(current.get(key, 0)) - int(previous.get(key, 0))
        for key in sorted(keys)
        if int(current.get(key, 0)) - int(previous.get(key, 0)) != 0
    }


def compare_shadow_inspection_reports(
    previous_report: ShadowInspectionBatchReport,
    current_report: ShadowInspectionBatchReport,
    previous_taxonomy: ShadowInspectionTaxonomyReport,
    current_taxonomy: ShadowInspectionTaxonomyReport,
    *,
    previous_label: str = "previous",
    current_label: str = "current",
    generated_at: Optional[str] = None,
) -> ShadowInspectionDeltaReport:
    previous_categories = {
        category.category_id: category.entry_count
        for category in previous_taxonomy.categories
    }
    current_categories = {
        category.category_id: category.entry_count
        for category in current_taxonomy.categories
    }
    notes: List[str] = []
    identifier_sparse_delta = current_categories.get("identifier_sparse_low_confidence", 0) - previous_categories.get(
        "identifier_sparse_low_confidence", 0
    )
    if identifier_sparse_delta < 0:
        notes.append(
            f"identifier_sparse_low_confidence decreased by {abs(identifier_sparse_delta)}"
        )
    low_confidence_delta = current_report.confidence_counts.get("low", 0) - previous_report.confidence_counts.get("low", 0)
    if low_confidence_delta < 0:
        notes.append(f"low-confidence inspection entries decreased by {abs(low_confidence_delta)}")
    resource_id_delta = current_report.focus_tag_counts.get("resource_ids", 0) - previous_report.focus_tag_counts.get("resource_ids", 0)
    if resource_id_delta > 0:
        notes.append(f"inspection slice gained {resource_id_delta} entries with resource identifiers")
    trial_registry_grounded_delta = current_report.focus_tag_counts.get("trial_registry_grounded", 0) - previous_report.focus_tag_counts.get("trial_registry_grounded", 0)
    if trial_registry_grounded_delta > 0:
        notes.append(
            f"inspection slice gained {trial_registry_grounded_delta} entries with grounded trial-registry support"
        )
    trial_registry_delta = current_categories.get("trial_registry_traceability", 0) - previous_categories.get(
        "trial_registry_traceability", 0
    )
    if trial_registry_delta < 0:
        notes.append(f"trial_registry_traceability decreased by {abs(trial_registry_delta)}")
    resource_release_grounded_delta = current_report.focus_tag_counts.get(
        "resource_release_grounded", 0
    ) - previous_report.focus_tag_counts.get("resource_release_grounded", 0)
    if resource_release_grounded_delta > 0:
        notes.append(
            f"inspection slice gained {resource_release_grounded_delta} entries with grounded resource-release support"
        )
    resource_release_delta = current_categories.get("resource_release_specificity", 0) - previous_categories.get(
        "resource_release_specificity", 0
    )
    if resource_release_delta < 0:
        notes.append(f"resource_release_specificity decreased by {abs(resource_release_delta)}")
    fulltext_gap_delta = current_categories.get("fulltext_acquisition_gap", 0) - previous_categories.get(
        "fulltext_acquisition_gap", 0
    )
    if fulltext_gap_delta > 0:
        notes.append(
            f"fulltext_acquisition_gap gained {fulltext_gap_delta} entries — prioritize full-text acquisition before re-running the shadow lane"
        )
    elif fulltext_gap_delta < 0:
        notes.append(f"fulltext_acquisition_gap decreased by {abs(fulltext_gap_delta)}")
    abstract_inferred_delta = current_report.focus_tag_counts.get(
        "abstract_inferred_only", 0
    ) - previous_report.focus_tag_counts.get("abstract_inferred_only", 0)
    if abstract_inferred_delta > 0:
        notes.append(
            f"inspection slice gained {abstract_inferred_delta} entries whose bundles are abstract-inferred only"
        )
    blocked_upstream_category_delta = current_categories.get(
        "fulltext_acquisition_blocked_upstream", 0
    ) - previous_categories.get("fulltext_acquisition_blocked_upstream", 0)
    if blocked_upstream_category_delta > 0:
        notes.append(
            f"fulltext_acquisition_blocked_upstream gained {blocked_upstream_category_delta} entries — retrying Europe PMC will not help, escalate to an alternate backend"
        )
    elif blocked_upstream_category_delta < 0:
        notes.append(
            f"fulltext_acquisition_blocked_upstream decreased by {abs(blocked_upstream_category_delta)}"
        )

    return ShadowInspectionDeltaReport(
        generated_at=generated_at or _utc_timestamp(),
        previous_label=previous_label,
        current_label=current_label,
        previous_selected_total=previous_report.selected_total,
        current_selected_total=current_report.selected_total,
        confidence_count_delta=_delta_mapping(previous_report.confidence_counts, current_report.confidence_counts),
        writing_count_delta=_delta_mapping(previous_report.writing_counts, current_report.writing_counts),
        focus_tag_delta=_delta_mapping(previous_report.focus_tag_counts, current_report.focus_tag_counts),
        taxonomy_category_entry_delta=_delta_mapping(previous_categories, current_categories),
        notes=tuple(notes),
    )
