from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from .models import (
    AnswerRecord,
    AssertionRecord,
    EvaluationExtractionAuditReport,
    ExtractionAuditReport,
    EvidenceExtractionRecord,
    EvidenceRecord,
    EvidenceUnit,
    ObservationRecord,
    ParserAssistedExtractionReport,
    QuestionRecord,
    SourcePaper,
    SourceQualityRecord,
    TruthManifest,
    TruthManifestVerificationReport,
)
from .policy import (
    AnswerFormat,
    ClaimMode,
    EvidenceUnitType,
    ObservationType,
    SourceQualityConcernType,
    SourceQualitySeverity,
    StudyClass,
    TaskFamily,
)
from .qualification import required_standards_for_paper


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_payload(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_payload(payload).encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}:{digest}"


def _parse_claim_mode(value: Any) -> Optional[ClaimMode]:
    if value in (None, ""):
        return None
    if isinstance(value, ClaimMode):
        return value
    return ClaimMode(str(value))


def _dedupe_preserve_order(values: Iterable[str]) -> Tuple[str, ...]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


def _metadata_value(paper: SourcePaper, keys: Sequence[str]) -> Optional[str]:
    for key in keys:
        value = paper.metadata.get(key)
        if value is not None:
            if isinstance(value, (dict, list, tuple)):
                normalized = json.dumps(value, sort_keys=True)
            else:
                normalized = str(value).strip()
            if normalized:
                return normalized
    return None


def _metadata_object_value(paper: SourcePaper, keys: Sequence[str]) -> Optional[Any]:
    for key in keys:
        if key not in paper.metadata:
            continue
        value = paper.metadata[key]
        if value in (None, "", [], {}, ()):
            continue
        if isinstance(value, (dict, list, tuple)):
            return value
        normalized = str(value).strip()
        if not normalized:
            continue
        if normalized[0] in "[{":
            try:
                return json.loads(normalized)
            except json.JSONDecodeError:
                pass
        return normalized
    return None


def _split_pointer_values(value: Optional[str]) -> Tuple[str, ...]:
    if not value:
        return ()
    pieces = []
    for item in re.split(r"[;\n|]+", value):
        normalized = item.strip()
        if normalized:
            pieces.append(normalized)
    return _dedupe_preserve_order(pieces)


def _clean_statement(value: str) -> str:
    normalized = value.replace("\r", "\n").strip()
    normalized = re.sub(r"^\s*(?:[-*•]+|\d+[.)])\s*", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _extract_statements(text: str, limit: int) -> Tuple[str, ...]:
    statements: List[str] = []
    for line in text.replace("\r", "\n").split("\n"):
        cleaned_line = _clean_statement(line)
        if not cleaned_line:
            continue
        pieces = re.split(r"(?<=[.!?])\s+", cleaned_line)
        for piece in pieces:
            cleaned_piece = _clean_statement(piece)
            if not cleaned_piece:
                continue
            statements.append(cleaned_piece)
            if len(statements) >= limit:
                return _dedupe_preserve_order(statements)
    return _dedupe_preserve_order(statements[:limit])


def _truncate(value: str, limit: int = 160) -> str:
    normalized = _clean_statement(value)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _section_claim_mode(paper: SourcePaper, unit_type: EvidenceUnitType) -> Optional[ClaimMode]:
    if unit_type == EvidenceUnitType.METHODS_PROTOCOL_BLOCK:
        return ClaimMode.DESCRIPTIVE
    if unit_type == EvidenceUnitType.RESOURCE_DESCRIPTION_BLOCK:
        if paper.claim_mode == ClaimMode.RESOURCE_RELEASE:
            return ClaimMode.RESOURCE_RELEASE
        return ClaimMode.DESCRIPTIVE
    return paper.claim_mode


def _is_figure_pointer(pointer: Optional[str]) -> bool:
    if not pointer:
        return False
    normalized = pointer.strip().lower()
    return normalized.startswith("fig") or normalized.startswith("figure")


def _is_table_pointer(pointer: Optional[str]) -> bool:
    if not pointer:
        return False
    normalized = pointer.strip().lower()
    return normalized.startswith("tbl") or normalized.startswith("table")


def _observation_type_for_pointer(pointer: Optional[str], unit_type: EvidenceUnitType) -> ObservationType:
    if _is_figure_pointer(pointer):
        return ObservationType.FIGURE_OBSERVATION
    if _is_table_pointer(pointer):
        return ObservationType.TABLE_OBSERVATION
    if unit_type == EvidenceUnitType.METHODS_PROTOCOL_BLOCK:
        return ObservationType.METHODS_OBSERVATION
    if unit_type == EvidenceUnitType.REVIEW_REVISION_BLOCK:
        return ObservationType.REVIEW_OBSERVATION
    if unit_type == EvidenceUnitType.RESOURCE_DESCRIPTION_BLOCK:
        return ObservationType.RESOURCE_OBSERVATION
    return ObservationType.LITERATURE_STATEMENT


def _structured_items(value: Any) -> Tuple[Dict[str, Optional[str]], ...]:
    if value in (None, "", [], {}, ()):
        return ()
    if isinstance(value, str):
        return tuple({"pointer": None, "text": item} for item in _split_pointer_values(value))
    if isinstance(value, Mapping):
        items: List[Dict[str, Optional[str]]] = []
        for key, item_value in value.items():
            if isinstance(item_value, Mapping):
                text = item_value.get("text") or item_value.get("caption") or item_value.get("value")
                pointer = item_value.get("pointer") or item_value.get("id") or str(key)
            else:
                text = item_value
                pointer = str(key)
            normalized_text = _clean_statement(str(text)) if text is not None else ""
            if normalized_text:
                items.append({"pointer": str(pointer) if pointer else None, "text": normalized_text})
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, Mapping):
                text = item.get("text") or item.get("caption") or item.get("value") or item.get("description")
                pointer = item.get("pointer") or item.get("id") or item.get("label")
            else:
                text = item
                pointer = None
            normalized_text = _clean_statement(str(text)) if text is not None else ""
            if normalized_text:
                items.append({"pointer": str(pointer) if pointer else None, "text": normalized_text})
            elif item not in (None, "", [], {}, ()):
                items.append({"pointer": f"item_{index}", "text": _clean_statement(json.dumps(item, sort_keys=True))})
        return tuple(items)
    return ({"pointer": None, "text": _clean_statement(str(value))},)


def _primary_task_family_for_unit(paper: SourcePaper, unit_type: EvidenceUnitType) -> TaskFamily:
    if unit_type == EvidenceUnitType.FIGURE_TABLE_RESULT:
        return TaskFamily.FIGURE_QA
    if unit_type == EvidenceUnitType.METHODS_PROTOCOL_BLOCK:
        if paper.study_class == StudyClass.HUMAN_INTERVENTIONAL:
            return TaskFamily.TRIAL_QA
        return TaskFamily.LITERATURE_QA
    if unit_type == EvidenceUnitType.REVIEW_REVISION_BLOCK:
        return TaskFamily.SOURCE_QUALITY_QA
    return TaskFamily.LITERATURE_QA


def _task_family_for_observation_type(
    paper: SourcePaper,
    unit_type: EvidenceUnitType,
    observation_type: ObservationType,
) -> TaskFamily:
    if observation_type == ObservationType.FIGURE_OBSERVATION:
        return TaskFamily.FIGURE_QA
    if observation_type == ObservationType.TABLE_OBSERVATION:
        return TaskFamily.TABLE_QA
    if observation_type == ObservationType.TRIAL_OBSERVATION:
        return TaskFamily.TRIAL_QA
    if observation_type == ObservationType.SOURCE_QUALITY_SIGNAL:
        return TaskFamily.SOURCE_QUALITY_QA
    return _primary_task_family_for_unit(paper, unit_type)


def _default_prompt(task_family: TaskFamily, paper: SourcePaper, unit_type: EvidenceUnitType) -> str:
    if task_family == TaskFamily.FIGURE_QA:
        return f"What result is directly supported by the cited figure evidence in {paper.paper_id}?"
    if task_family == TaskFamily.TABLE_QA:
        return f"What result is directly supported by the cited table evidence in {paper.paper_id}?"
    if task_family == TaskFamily.TRIAL_QA:
        return f"What trial design, arm, endpoint, or outcome detail is supported by {paper.paper_id}?"
    if task_family == TaskFamily.SOURCE_QUALITY_QA:
        return f"What review or source-quality concern is evidenced for {paper.paper_id}?"
    if unit_type == EvidenceUnitType.METHODS_PROTOCOL_BLOCK:
        return f"What protocol or methods detail is supported by {paper.paper_id}?"
    return f"What supported literature claim can be answered from {paper.paper_id}?"


def _classify_source_quality(text: str) -> SourceQualityConcernType:
    lowered = text.lower()
    if any(term in lowered for term in ("control", "bias", "confound", "study design", "design flaw")):
        return SourceQualityConcernType.DESIGN_FLAW
    if any(term in lowered for term in ("statistic", "p-value", "multiple testing", "power", "variance")):
        return SourceQualityConcernType.STATISTICAL_METHODOLOGY
    if any(term in lowered for term in ("missing experiment", "additional experiment", "validation", "replicate")):
        return SourceQualityConcernType.MISSING_EXPERIMENT
    if any(term in lowered for term in ("novelty", "prior art", "related work", "precedent")):
        return SourceQualityConcernType.PRIOR_ART_NOVELTY
    if any(term in lowered for term in ("unclear", "clarify", "writing", "grammar", "presentation")):
        return SourceQualityConcernType.WRITING_CLARITY
    if any(term in lowered for term in ("antibody", "cell line", "reagent", "protocol", "method specificity")):
        return SourceQualityConcernType.REAGENT_METHOD_SPECIFICITY
    if any(term in lowered for term in ("overstate", "causal", "interpretation", "conclusion")):
        return SourceQualityConcernType.INTERPRETATION
    return SourceQualityConcernType.OTHER


def _source_quality_severity(text: str) -> SourceQualitySeverity:
    lowered = text.lower()
    if any(term in lowered for term in ("major", "critical", "essential", "must", "required")):
        return SourceQualitySeverity.MAJOR
    if any(term in lowered for term in ("optional", "could", "nice to have", "if possible")):
        return SourceQualitySeverity.OPTIONAL
    return SourceQualitySeverity.MINOR


def _build_parser_assisted_unit(
    paper: SourcePaper,
    *,
    section_name: str,
    unit_type: EvidenceUnitType,
    source_text: str,
    pointer_values: Sequence[str],
    excluded_text: Optional[str],
    max_assertions_per_unit: int,
) -> Tuple[EvidenceUnit, Dict[str, Any]]:
    statement_limit = max(max_assertions_per_unit, 1)
    assertions = _extract_statements(source_text, limit=statement_limit)
    if not assertions:
        raise ValueError(f"parser-assisted extraction yielded no assertions for {paper.paper_id}:{section_name}")

    default_pointer = f"{section_name}_section"
    evidence_items = [
        {
            "pointer": default_pointer,
            "evidence_type": "section_text",
            "description": _truncate(source_text),
        }
    ]
    if unit_type == EvidenceUnitType.FIGURE_TABLE_RESULT:
        for pointer in pointer_values:
            evidence_items.append(
                {
                    "pointer": pointer,
                    "evidence_type": "figure_table_pointer",
                    "description": f"published figure/table pointer for {section_name}",
                }
            )
    else:
        for pointer in pointer_values:
            evidence_items.append(
                {
                    "pointer": pointer,
                    "evidence_type": "section_pointer",
                    "description": f"metadata pointer for {section_name}",
                }
            )

    unit_id = _stable_id(
        "EUAUTO",
        {
            "paper_id": paper.paper_id,
            "section_name": section_name,
            "unit_type": unit_type.value,
            "assertions": assertions,
            "pointers": tuple(item["pointer"] for item in evidence_items),
        },
    )
    evidence_unit = EvidenceUnit(
        unit_id=unit_id,
        paper_id=paper.paper_id,
        unit_type=unit_type,
        evidence_pointers=tuple(item["pointer"] for item in evidence_items),
        locally_supported=True,
        internally_coherent=True,
        depends_on_excluded_narrative=False,
        releasable=True,
        description=f"parser-assisted draft for {section_name}",
        modality_overlays=paper.modality_overlays,
    )

    excluded_assertions = ()
    if excluded_text:
        excluded_assertions = tuple(
            {"text": statement, "claim_mode": _section_claim_mode(paper, unit_type).value}
            for statement in _extract_statements(excluded_text, limit=statement_limit)
        )

    extraction_spec: Dict[str, Any] = {
        "paper_id": paper.paper_id,
        "evidence_unit_id": unit_id,
        "notes": (
            f"parser-assisted draft generated from metadata:{section_name}",
        ),
        "evidence_items": tuple(evidence_items),
        "assertions": tuple(
            {
                "text": statement,
                "claim_mode": _section_claim_mode(paper, unit_type).value
                if _section_claim_mode(paper, unit_type) is not None
                else None,
            }
            for statement in assertions
        ),
        "excluded_assertions": excluded_assertions,
    }
    return evidence_unit, extraction_spec


def build_parser_assisted_extraction_drafts(
    source_papers: Sequence[SourcePaper],
    max_assertions_per_unit: int = 3,
) -> Tuple[Tuple[EvidenceUnit, ...], Tuple[Dict[str, Any], ...], ParserAssistedExtractionReport]:
    section_definitions = (
        {
            "section_name": "abstract",
            "unit_type": EvidenceUnitType.CLAIM_CLUSTER,
            "text_keys": ("abstract", "abstract_text", "summary", "summary_text"),
            "pointer_keys": ("abstract_pointer", "abstract_pointers"),
            "excluded_keys": ("abstract_excluded_assertions",),
        },
        {
            "section_name": "results",
            "unit_type": EvidenceUnitType.FIGURE_TABLE_RESULT,
            "text_keys": ("results_text", "results_summary", "figure_table_summary"),
            "pointer_keys": ("figure_pointers", "table_pointers", "results_pointers"),
            "excluded_keys": ("results_excluded_assertions",),
        },
        {
            "section_name": "methods",
            "unit_type": EvidenceUnitType.METHODS_PROTOCOL_BLOCK,
            "text_keys": ("methods_text", "methods_summary", "protocol_text", "protocol_summary"),
            "pointer_keys": ("methods_pointers", "protocol_pointers"),
            "excluded_keys": ("methods_excluded_assertions",),
        },
        {
            "section_name": "review_revision",
            "unit_type": EvidenceUnitType.REVIEW_REVISION_BLOCK,
            "text_keys": ("review_response_text", "review_response", "revision_response_text"),
            "pointer_keys": ("review_response_pointers",),
            "excluded_keys": ("review_excluded_assertions",),
        },
        {
            "section_name": "resource",
            "unit_type": EvidenceUnitType.RESOURCE_DESCRIPTION_BLOCK,
            "text_keys": ("resource_text", "resource_description", "resource_summary"),
            "pointer_keys": ("resource_pointers",),
            "excluded_keys": ("resource_excluded_assertions",),
        },
    )

    evidence_units: List[EvidenceUnit] = []
    extraction_specs: List[Dict[str, Any]] = []
    unit_type_counts: MutableMapping[str, int] = {}
    skipped_paper_ids: List[str] = []
    papers_with_suggestions = 0

    for paper in source_papers:
        paper_generated = 0
        for definition in section_definitions:
            source_text = _metadata_value(paper, definition["text_keys"])
            if not source_text:
                continue
            pointer_values = ()
            for pointer_key in definition["pointer_keys"]:
                pointer_values += _split_pointer_values(paper.metadata.get(pointer_key))
            excluded_text = _metadata_value(paper, definition["excluded_keys"])
            evidence_unit, extraction_spec = _build_parser_assisted_unit(
                paper,
                section_name=definition["section_name"],
                unit_type=definition["unit_type"],
                source_text=source_text,
                pointer_values=_dedupe_preserve_order(pointer_values),
                excluded_text=excluded_text,
                max_assertions_per_unit=max_assertions_per_unit,
            )
            evidence_units.append(evidence_unit)
            extraction_specs.append(extraction_spec)
            unit_type_key = definition["unit_type"].value
            unit_type_counts[unit_type_key] = unit_type_counts.get(unit_type_key, 0) + 1
            paper_generated += 1
        if paper_generated:
            papers_with_suggestions += 1
        else:
            skipped_paper_ids.append(paper.paper_id)

    report = ParserAssistedExtractionReport(
        generated_at=_utc_timestamp(),
        paper_count=len(source_papers),
        papers_with_suggestions=papers_with_suggestions,
        evidence_unit_count=len(evidence_units),
        extraction_spec_count=len(extraction_specs),
        unit_type_counts=dict(sorted(unit_type_counts.items())),
        skipped_paper_ids=tuple(skipped_paper_ids),
        notes=(
            "parser-assisted drafts are metadata-driven and must be reviewed before truth-manifest freeze",
        ),
    )
    return tuple(evidence_units), tuple(extraction_specs), report


def build_evaluation_extraction_artifacts(
    source_papers: Sequence[SourcePaper],
    evidence_units: Sequence[EvidenceUnit],
    extraction_specs: Sequence[Mapping[str, Any]],
    max_questions_per_unit: int = 2,
) -> Tuple[
    Tuple[ObservationRecord, ...],
    Tuple[QuestionRecord, ...],
    Tuple[AnswerRecord, ...],
    Tuple[SourceQualityRecord, ...],
    EvaluationExtractionAuditReport,
]:
    paper_map = {paper.paper_id: paper for paper in source_papers}
    unit_map = {unit.unit_id: unit for unit in evidence_units}
    observations: List[ObservationRecord] = []
    questions: List[QuestionRecord] = []
    answers: List[AnswerRecord] = []
    quality_records: List[SourceQualityRecord] = []
    task_family_counts: MutableMapping[str, int] = {}

    metadata_templates = (
        (
            ("figure_captions", "figure_caption_text", "figure_observations"),
            ObservationType.FIGURE_OBSERVATION,
            TaskFamily.FIGURE_QA,
        ),
        (
            ("table_captions", "table_rows", "table_cells", "table_observations"),
            ObservationType.TABLE_OBSERVATION,
            TaskFamily.TABLE_QA,
        ),
        (
            ("trial_registry_summary", "trial_arms", "trial_endpoints", "trial_outcomes"),
            ObservationType.TRIAL_OBSERVATION,
            TaskFamily.TRIAL_QA,
        ),
        (
            ("review_comments", "review_concerns", "decision_letters"),
            ObservationType.SOURCE_QUALITY_SIGNAL,
            TaskFamily.SOURCE_QUALITY_QA,
        ),
        (
            ("resource_identifiers", "resource_inventory"),
            ObservationType.RESOURCE_OBSERVATION,
            TaskFamily.LITERATURE_QA,
        ),
    )

    for spec in extraction_specs:
        paper_id = str(spec["paper_id"])
        evidence_unit_id = str(spec["evidence_unit_id"])
        if paper_id not in paper_map:
            raise KeyError(f"missing source paper for evaluation extraction: {paper_id}")
        if evidence_unit_id not in unit_map:
            raise KeyError(f"missing evidence unit for evaluation extraction: {evidence_unit_id}")
        paper = paper_map[paper_id]
        evidence_unit = unit_map[evidence_unit_id]
        evidence_specs = tuple(spec.get("evidence_items", ()))
        assertion_specs = tuple(spec.get("assertions", ()))

        unit_observation_ids: Dict[TaskFamily, List[str]] = {}
        unit_observation_texts: Dict[TaskFamily, List[str]] = {}
        unit_observation_pointers: Dict[TaskFamily, List[str]] = {}
        unit_quality_observations: List[ObservationRecord] = []

        for index, assertion_spec in enumerate(assertion_specs):
            if not isinstance(assertion_spec, Mapping):
                continue
            text = _clean_statement(str(assertion_spec.get("text", "")))
            if not text:
                continue
            candidate_pointers = [
                str(item.get("pointer"))
                for item in evidence_specs
                if isinstance(item, Mapping) and item.get("pointer")
            ]
            selected_pointer = next((pointer for pointer in candidate_pointers if _is_figure_pointer(pointer)), None)
            if selected_pointer is None:
                selected_pointer = next((pointer for pointer in candidate_pointers if _is_table_pointer(pointer)), None)
            observation_type = _observation_type_for_pointer(selected_pointer, evidence_unit.unit_type)
            task_family = _task_family_for_observation_type(paper, evidence_unit.unit_type, observation_type)
            observation_id = _stable_id(
                "OBS",
                {
                    "paper_id": paper_id,
                    "evidence_unit_id": evidence_unit_id,
                    "index": index,
                    "task_family": task_family.value,
                    "pointer": selected_pointer,
                    "text": text,
                },
            )
            observation = ObservationRecord(
                observation_id=observation_id,
                paper_id=paper_id,
                task_family=task_family,
                observation_type=observation_type,
                text=text,
                evidence_unit_id=evidence_unit_id,
                pointer=selected_pointer,
                provenance_note=f"derived from extraction spec assertions for {evidence_unit.unit_type.value}",
            )
            observations.append(observation)
            unit_observation_ids.setdefault(task_family, []).append(observation_id)
            unit_observation_texts.setdefault(task_family, []).append(text)
            if selected_pointer:
                unit_observation_pointers.setdefault(task_family, []).append(selected_pointer)
            if task_family == TaskFamily.SOURCE_QUALITY_QA:
                unit_quality_observations.append(observation)

        for keys, observation_type, task_family in metadata_templates:
            metadata_value = _metadata_object_value(paper, keys)
            if metadata_value is None:
                continue
            for index, item in enumerate(_structured_items(metadata_value), start=1):
                text = _clean_statement(str(item.get("text", "")))
                if not text:
                    continue
                pointer = item.get("pointer")
                observation_id = _stable_id(
                    "OBS",
                    {
                        "paper_id": paper_id,
                        "evidence_unit_id": evidence_unit_id,
                        "metadata_keys": tuple(keys),
                        "index": index,
                        "pointer": pointer,
                        "text": text,
                    },
                )
                observation = ObservationRecord(
                    observation_id=observation_id,
                    paper_id=paper_id,
                    task_family=task_family,
                    observation_type=observation_type,
                    text=text,
                    evidence_unit_id=evidence_unit_id,
                    pointer=pointer,
                    provenance_note=f"derived from metadata keys: {', '.join(keys)}",
                )
                observations.append(observation)
                unit_observation_ids.setdefault(task_family, []).append(observation_id)
                unit_observation_texts.setdefault(task_family, []).append(text)
                if pointer:
                    unit_observation_pointers.setdefault(task_family, []).append(pointer)
                if task_family == TaskFamily.SOURCE_QUALITY_QA:
                    unit_quality_observations.append(observation)

        for observation in unit_quality_observations:
            quality_record = SourceQualityRecord(
                quality_record_id=_stable_id(
                    "QUAL",
                    {
                        "paper_id": observation.paper_id,
                        "observation_id": observation.observation_id,
                        "text": observation.text,
                    },
                ),
                paper_id=observation.paper_id,
                concern_type=_classify_source_quality(observation.text),
                severity=_source_quality_severity(observation.text),
                text=observation.text,
                pointer=observation.pointer,
                evidence_unit_id=observation.evidence_unit_id,
                supporting_observation_ids=(observation.observation_id,),
            )
            quality_records.append(quality_record)

        ranked_task_families = sorted(
            (
                family
                for family, observation_ids in unit_observation_ids.items()
                if observation_ids
            ),
            key=lambda family: (-len(unit_observation_ids[family]), family.value),
        )[: max(max_questions_per_unit, 1)]
        for question_index, task_family in enumerate(ranked_task_families, start=1):
            observation_ids = tuple(_dedupe_preserve_order(unit_observation_ids[task_family]))
            evidence_pointers = tuple(
                _dedupe_preserve_order(unit_observation_pointers.get(task_family, ()))
            )
            answer_text = " ".join(_dedupe_preserve_order(unit_observation_texts[task_family][:2]))
            question_id = _stable_id(
                "Q",
                {
                    "paper_id": paper_id,
                    "evidence_unit_id": evidence_unit_id,
                    "task_family": task_family.value,
                    "question_index": question_index,
                    "observations": observation_ids,
                },
            )
            answer_id = _stable_id(
                "ANS",
                {
                    "question_id": question_id,
                    "answer_text": answer_text,
                },
            )
            questions.append(
                QuestionRecord(
                    question_id=question_id,
                    paper_id=paper_id,
                    task_family=task_family,
                    prompt=_default_prompt(task_family, paper, evidence_unit.unit_type),
                    answer_format=AnswerFormat.FREE_TEXT,
                    evidence_unit_id=evidence_unit_id,
                    supporting_observation_ids=observation_ids,
                    supporting_evidence_pointers=evidence_pointers,
                    expected_answer_ids=(answer_id,),
                )
            )
            answers.append(
                AnswerRecord(
                    answer_id=answer_id,
                    paper_id=paper_id,
                    question_id=question_id,
                    answer_text=answer_text,
                    rationale=f"compiled from {len(observation_ids)} supporting observations",
                    supporting_observation_ids=observation_ids,
                    supporting_evidence_pointers=evidence_pointers,
                )
            )
            task_family_counts[task_family.value] = task_family_counts.get(task_family.value, 0) + 1

    report = EvaluationExtractionAuditReport(
        generated_at=_utc_timestamp(),
        paper_count=len({record.paper_id for record in observations}),
        observation_count=len(observations),
        question_count=len(questions),
        answer_count=len(answers),
        source_quality_count=len(quality_records),
        task_family_counts=dict(sorted(task_family_counts.items())),
        notes=(
            "evaluation extraction is a QA-oriented companion layer and does not replace truth-manifest review",
        ),
    )
    return (
        tuple(observations),
        tuple(questions),
        tuple(answers),
        tuple(quality_records),
        report,
    )


def build_extraction_records(
    source_papers: Mapping[str, SourcePaper],
    evidence_units: Mapping[str, EvidenceUnit],
    extraction_specs: Sequence[Mapping[str, Any]],
    default_evidence_type: str = "text_span",
) -> Tuple[Tuple[AssertionRecord, ...], Tuple[EvidenceRecord, ...], Tuple[EvidenceExtractionRecord, ...], ExtractionAuditReport]:
    assertion_records: List[AssertionRecord] = []
    evidence_records: List[EvidenceRecord] = []
    extraction_records: List[EvidenceExtractionRecord] = []
    paper_ids = set()
    evidence_unit_ids = set()
    unit_type_counts: MutableMapping[str, int] = {}

    for spec in extraction_specs:
        paper_id = str(spec["paper_id"])
        evidence_unit_id = str(spec["evidence_unit_id"])
        if paper_id not in source_papers:
            raise KeyError(f"missing source paper for extraction spec: {paper_id}")
        if evidence_unit_id not in evidence_units:
            raise KeyError(f"missing evidence unit for extraction spec: {evidence_unit_id}")
        evidence_unit = evidence_units[evidence_unit_id]
        if evidence_unit.paper_id != paper_id:
            raise ValueError("extraction spec paper_id does not match evidence unit paper_id")

        evidence_specs = tuple(spec.get("evidence_items", ()))
        assertion_specs = tuple(spec.get("assertions", ()))
        excluded_specs = tuple(spec.get("excluded_assertions", ()))
        extraction_id = str(
            spec.get("extraction_id")
            or _stable_id(
                "EXTRACT",
                {
                    "paper_id": paper_id,
                    "evidence_unit_id": evidence_unit_id,
                    "assertions": assertion_specs,
                    "evidence_items": evidence_specs,
                    "excluded_assertions": excluded_specs,
                    "notes": tuple(spec.get("notes", ())),
                },
            )
        )

        local_evidence_ids = []
        for index, item in enumerate(evidence_specs):
            if not isinstance(item, Mapping):
                raise ValueError("evidence_items entries must be mappings")
            evidence_id = str(
                item.get("evidence_id")
                or _stable_id(
                    "EVID",
                    {
                        "extraction_id": extraction_id,
                        "index": index,
                        "pointer": item.get("pointer"),
                        "evidence_type": item.get("evidence_type", default_evidence_type),
                        "description": item.get("description", ""),
                    },
                )
            )
            local_evidence_ids.append(evidence_id)
            evidence_records.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    paper_id=paper_id,
                    evidence_type=str(item.get("evidence_type", default_evidence_type)),
                    pointer=str(item["pointer"]),
                    description=str(item.get("description", "")),
                )
            )

        local_assertion_ids = []
        for index, item in enumerate(assertion_specs):
            if not isinstance(item, Mapping):
                raise ValueError("assertions entries must be mappings")
            assertion_id = str(
                item.get("assertion_id")
                or _stable_id(
                    "ASSERT",
                    {
                        "extraction_id": extraction_id,
                        "index": index,
                        "text": item.get("text", ""),
                        "claim_mode": item.get("claim_mode"),
                    },
                )
            )
            evidence_record_ids = tuple(item.get("evidence_record_ids", ())) or tuple(local_evidence_ids)
            local_assertion_ids.append(assertion_id)
            assertion_records.append(
                AssertionRecord(
                    assertion_id=assertion_id,
                    paper_id=paper_id,
                    text=str(item["text"]),
                    claim_mode=_parse_claim_mode(item.get("claim_mode")),
                    supported=bool(item.get("supported", True)),
                    excluded=bool(item.get("excluded", False)),
                    evidence_record_ids=evidence_record_ids,
                )
            )

        local_excluded_ids = []
        for index, item in enumerate(excluded_specs):
            if isinstance(item, Mapping):
                text = str(item["text"])
                claim_mode = _parse_claim_mode(item.get("claim_mode"))
                evidence_record_ids = tuple(item.get("evidence_record_ids", ()))
                custom_id = item.get("assertion_id")
            else:
                text = str(item)
                claim_mode = None
                evidence_record_ids = ()
                custom_id = None
            assertion_id = str(
                custom_id
                or _stable_id(
                    "ASSERT",
                    {
                        "extraction_id": extraction_id,
                        "excluded_index": index,
                        "text": text,
                    },
                )
            )
            local_excluded_ids.append(assertion_id)
            assertion_records.append(
                AssertionRecord(
                    assertion_id=assertion_id,
                    paper_id=paper_id,
                    text=text,
                    claim_mode=claim_mode,
                    supported=False,
                    excluded=True,
                    evidence_record_ids=evidence_record_ids,
                )
            )

        extraction_records.append(
            EvidenceExtractionRecord(
                extraction_id=extraction_id,
                paper_id=paper_id,
                evidence_unit_id=evidence_unit_id,
                assertion_ids=tuple(local_assertion_ids),
                evidence_ids=tuple(local_evidence_ids),
                excluded_assertion_ids=tuple(local_excluded_ids),
                notes=tuple(str(item) for item in spec.get("notes", ())),
            )
        )
        paper_ids.add(paper_id)
        evidence_unit_ids.add(evidence_unit_id)
        unit_type_key = evidence_unit.unit_type.value
        unit_type_counts[unit_type_key] = unit_type_counts.get(unit_type_key, 0) + 1

    report = ExtractionAuditReport(
        generated_at=_utc_timestamp(),
        paper_count=len(paper_ids),
        evidence_unit_count=len(evidence_unit_ids),
        extraction_count=len(extraction_records),
        assertion_count=sum(1 for record in assertion_records if not record.excluded),
        excluded_assertion_count=sum(1 for record in assertion_records if record.excluded),
        evidence_record_count=len(evidence_records),
        unit_type_counts=dict(sorted(unit_type_counts.items())),
    )
    return (
        tuple(assertion_records),
        tuple(evidence_records),
        tuple(extraction_records),
        report,
    )


def build_truth_manifest_from_extractions(
    paper: SourcePaper,
    evidence_units: Sequence[EvidenceUnit],
    assertion_records: Sequence[AssertionRecord],
    evidence_records: Sequence[EvidenceRecord],
    extraction_records: Sequence[EvidenceExtractionRecord],
    manifest_id: Optional[str] = None,
    caveats: Sequence[str] = (),
    provenance_agents: Sequence[str] = ("curation_pipeline:semi_structured_extraction",),
) -> TruthManifest:
    evidence_unit_map = {unit.unit_id: unit for unit in evidence_units}
    assertion_map = {record.assertion_id: record for record in assertion_records}
    evidence_map = {record.evidence_id: record for record in evidence_records}

    ordered_extractions = sorted(
        (
            record
            for record in extraction_records
            if record.paper_id == paper.paper_id
        ),
        key=lambda item: item.extraction_id,
    )
    if not ordered_extractions:
        raise ValueError(f"no extraction records found for paper {paper.paper_id}")

    included_assertion_ids: List[str] = []
    included_assertion_texts: List[str] = []
    excluded_assertion_texts: List[str] = []
    evidence_ids: List[str] = []
    evidence_items: List[str] = []
    evidence_types: List[str] = []
    provenance_entities: List[str] = []
    provenance_activities: List[str] = []
    inconsistent_unit_ids = []

    for extraction in ordered_extractions:
        provenance_activities.append(extraction.extraction_id)
        provenance_entities.append(extraction.evidence_unit_id)
        unit = evidence_unit_map.get(extraction.evidence_unit_id)
        if unit is None or unit.paper_id != paper.paper_id:
            inconsistent_unit_ids.append(extraction.evidence_unit_id)
            continue
        for assertion_id in extraction.assertion_ids:
            record = assertion_map.get(assertion_id)
            if record is None or record.paper_id != paper.paper_id or record.excluded or not record.supported:
                continue
            included_assertion_ids.append(assertion_id)
            included_assertion_texts.append(record.text)
        for assertion_id in extraction.excluded_assertion_ids:
            record = assertion_map.get(assertion_id)
            if record is None:
                continue
            excluded_assertion_texts.append(record.text)
        for evidence_id in extraction.evidence_ids:
            record = evidence_map.get(evidence_id)
            if record is None or record.paper_id != paper.paper_id:
                continue
            evidence_ids.append(evidence_id)
            evidence_items.append(record.pointer)
            evidence_types.append(record.evidence_type)
            provenance_entities.append(evidence_id)

    if inconsistent_unit_ids:
        raise ValueError("extraction references evidence units outside the target paper")

    normalized_assertion_ids = _dedupe_preserve_order(included_assertion_ids)
    normalized_assertion_texts = tuple(
        assertion_map[assertion_id].text for assertion_id in normalized_assertion_ids
    )
    normalized_evidence_ids = _dedupe_preserve_order(evidence_ids)
    normalized_evidence_items = tuple(
        evidence_map[evidence_id].pointer for evidence_id in normalized_evidence_ids
    )
    normalized_evidence_types = tuple(
        evidence_map[evidence_id].evidence_type for evidence_id in normalized_evidence_ids
    )
    normalized_excluded_assertions = _dedupe_preserve_order(excluded_assertion_texts)
    normalized_provenance_entities = _dedupe_preserve_order(provenance_entities)
    normalized_provenance_activities = _dedupe_preserve_order(provenance_activities)
    normalized_provenance_agents = _dedupe_preserve_order(provenance_agents)

    manifest_id = manifest_id or _stable_id(
        "TM",
        {
            "paper_id": paper.paper_id,
            "extraction_ids": normalized_provenance_activities,
            "assertion_ids": normalized_assertion_ids,
            "evidence_ids": normalized_evidence_ids,
        },
    )

    return TruthManifest(
        manifest_id=manifest_id,
        paper_id=paper.paper_id,
        assertion_ids=normalized_assertion_ids,
        assertion_texts=normalized_assertion_texts,
        evidence_items=normalized_evidence_items,
        evidence_types=normalized_evidence_types,
        excluded_assertions=normalized_excluded_assertions,
        caveats=tuple(str(item) for item in caveats),
        provenance_entities=normalized_provenance_entities,
        provenance_activities=normalized_provenance_activities,
        provenance_agents=normalized_provenance_agents,
        applied_standards=required_standards_for_paper(paper),
        study_class=paper.study_class,
        modality_overlays=paper.modality_overlays,
        frozen=False,
        frozen_at=None,
    )


def freeze_truth_manifest(
    truth_manifest: TruthManifest,
    frozen_at: Optional[str] = None,
) -> TruthManifest:
    return replace(
        truth_manifest,
        frozen=True,
        frozen_at=frozen_at or _utc_timestamp(),
    )


def verify_truth_manifest(
    truth_manifest: TruthManifest,
    paper: SourcePaper,
    evidence_units: Sequence[EvidenceUnit],
    assertion_records: Sequence[AssertionRecord],
    evidence_records: Sequence[EvidenceRecord],
    extraction_records: Sequence[EvidenceExtractionRecord],
) -> TruthManifestVerificationReport:
    assertion_map = {record.assertion_id: record for record in assertion_records}
    evidence_map = {record.evidence_id: record for record in evidence_records}
    evidence_unit_map = {unit.unit_id: unit for unit in evidence_units}
    paper_extractions = [
        record for record in extraction_records if record.paper_id == paper.paper_id
    ]

    missing_assertion_ids = sorted(
        assertion_id for assertion_id in truth_manifest.assertion_ids if assertion_id not in assertion_map
    )
    referenced_evidence_ids = _dedupe_preserve_order(
        evidence_id
        for extraction in paper_extractions
        for evidence_id in extraction.evidence_ids
    )
    missing_evidence_ids = sorted(
        evidence_id for evidence_id in referenced_evidence_ids if evidence_id not in evidence_map
    )
    missing_extraction_ids = sorted(
        extraction.extraction_id
        for extraction in paper_extractions
        if extraction.evidence_unit_id not in evidence_unit_map
    )

    inconsistent_paper_ids = []
    if truth_manifest.paper_id != paper.paper_id:
        inconsistent_paper_ids.append(truth_manifest.paper_id)
    for assertion_id in truth_manifest.assertion_ids:
        record = assertion_map.get(assertion_id)
        if record is not None and record.paper_id != paper.paper_id:
            inconsistent_paper_ids.append(assertion_id)
    for evidence_id in referenced_evidence_ids:
        record = evidence_map.get(evidence_id)
        if record is not None and record.paper_id != paper.paper_id:
            inconsistent_paper_ids.append(evidence_id)

    notes = []
    if not truth_manifest.frozen:
        notes.append("truth manifest is not frozen")
    if not paper_extractions:
        notes.append("no extraction records were found for this paper")

    ok = not any((missing_assertion_ids, missing_evidence_ids, missing_extraction_ids, inconsistent_paper_ids)) and truth_manifest.frozen
    return TruthManifestVerificationReport(
        manifest_id=truth_manifest.manifest_id,
        paper_id=truth_manifest.paper_id,
        ok=ok,
        frozen=truth_manifest.frozen,
        missing_assertion_ids=tuple(missing_assertion_ids),
        missing_evidence_ids=tuple(missing_evidence_ids),
        missing_extraction_ids=tuple(missing_extraction_ids),
        inconsistent_paper_ids=tuple(_dedupe_preserve_order(inconsistent_paper_ids)),
        notes=tuple(notes),
    )
