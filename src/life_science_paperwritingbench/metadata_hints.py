from __future__ import annotations

import json
import re
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .models import MetadataGovernanceHint, SourcePaper
from .policy import ClaimMode, ModalityOverlay, StandardId, StudyClass
from .qualification import required_standards_for_configuration


def _normalize_text(value: str) -> str:
    return value.lower().replace("_", " ").replace("-", " ")


def _metadata_text(paper: SourcePaper) -> str:
    chunks = [paper.title]
    for key, value in sorted(paper.metadata.items()):
        if isinstance(value, (dict, list, tuple)):
            serialized = json.dumps(value, sort_keys=True)
        else:
            serialized = str(value)
        chunks.append(f"{key}: {serialized}")
    return _normalize_text(" ".join(chunks))


def _matched_terms(text: str, phrases: Sequence[str]) -> Tuple[str, ...]:
    return tuple(
        sorted(
            {
                phrase
                for phrase in phrases
                if _normalize_text(phrase) in text
            }
        )
    )


_ENZYMOLOGY_PATTERNS = (
    re.compile(r"\benzyme kinetics\b"),
    re.compile(r"\bmichaelis menten\b"),
    re.compile(r"\bmichaelis-menten\b"),
    re.compile(r"\bsubstrate turnover\b"),
    re.compile(r"\bkcat\b"),
    re.compile(r"\bkm\b.{0,24}\b(?:enzyme|enzymatic|substrate|kinetic|activity)\b"),
    re.compile(r"\b(?:enzyme|enzymatic)\b.{0,24}\bkm\b"),
)


def _matched_overlay_terms(text: str, overlay: ModalityOverlay, phrases: Sequence[str]) -> Tuple[str, ...]:
    if overlay != ModalityOverlay.ENZYMOLOGY:
        return _matched_terms(text, phrases)

    matches = set(_matched_terms(text, tuple(phrase for phrase in phrases if phrase != "km ")))
    for pattern in _ENZYMOLOGY_PATTERNS:
        found = pattern.search(text)
        if found:
            matches.add(found.group(0).strip())
    return tuple(sorted(matches))


STUDY_CLASS_RULES = {
    StudyClass.HUMAN_INTERVENTIONAL: (
        "randomized",
        "randomised",
        "clinical trial",
        "phase ii",
        "phase iii",
        "phase 2",
        "phase 3",
        "intervention",
        "placebo",
        "trial registration",
        "nct0",
    ),
    StudyClass.HUMAN_OBSERVATIONAL: (
        "cohort",
        "case control",
        "cross sectional",
        "observational",
        "retrospective",
        "prospective",
        "registry",
        "biobank",
        "survival analysis",
    ),
    StudyClass.SYSTEMATIC_REVIEW_META_ANALYSIS: (
        "systematic review",
        "meta analysis",
        "meta-analysis",
        "prisma",
        "pooled analysis",
    ),
    StudyClass.ANIMAL_PRECLINICAL: (
        "mouse",
        "mice",
        "murine",
        "rat",
        "zebrafish",
        "xenograft",
        "animal model",
        "in vivo",
        "preclinical",
    ),
    StudyClass.MECHANISTIC_EXPERIMENTAL: (
        "cell line",
        "organoid",
        "crispr",
        "knockout",
        "knockdown",
        "western blot",
        "immunoblot",
        "perturbation",
        "mechanism",
    ),
    StudyClass.METHODS_RESOURCE: (
        "resource",
        "database",
        "atlas",
        "benchmark",
        "pipeline",
        "workflow",
        "tool",
        "software",
        "protocol",
        "reference map",
    ),
}

OVERLAY_RULES = {
    ModalityOverlay.BIOMARKER_PROGNOSTIC: (
        "biomarker",
        "prognostic",
        "predictive",
        "hazard ratio",
        "roc curve",
        "survival model",
    ),
    ModalityOverlay.OMICS_TRANSCRIPTOMICS: (
        "rna seq",
        "rna-seq",
        "scrna",
        "transcriptome",
        "microarray",
        "geo accession",
        "arrayexpress",
    ),
    ModalityOverlay.SEQUENCE_METAGENOMICS: (
        "metagenom",
        "microbiome",
        "16s",
        "amplicon",
        "sra accession",
        "metatranscriptom",
    ),
    ModalityOverlay.PROTEOMICS_MASSSPEC: (
        "proteomics",
        "mass spectrometry",
        "lc ms",
        "lc-ms",
        "ms/ms",
        "pride",
        "proteomexchange",
    ),
    ModalityOverlay.STRUCTURAL_BIOPHYSICS: (
        "cryo em",
        "cryo-em",
        "x ray crystallography",
        "x-ray crystallography",
        "nmr structure",
        "pdb accession",
        "emdb",
        "bmrb",
    ),
    ModalityOverlay.ECOLOGY_BIODIVERSITY: (
        "biodiversity",
        "ecology",
        "field survey",
        "species distribution",
        "darwin core",
        "gbif",
        "eml metadata",
    ),
    ModalityOverlay.QPCR: (
        "qpcr",
        "rt qpcr",
        "rt-qpcr",
        "quantitative pcr",
    ),
    ModalityOverlay.ENZYMOLOGY: (
        "enzyme kinetics",
        "kcat",
        "michaelis menten",
        "michaelis-menten",
        "substrate turnover",
    ),
}

CLAIM_MODE_RULES = {
    ClaimMode.RESOURCE_RELEASE: (
        "resource",
        "resource paper",
        "atlas resource",
        "reference atlas",
        "benchmark dataset",
        "software",
        "software tool",
        "toolkit",
        "web server",
    ),
    ClaimMode.NEGATIVE_RESULT: (
        "negative result",
        "null result",
        "no significant",
        "did not improve",
        "failed to replicate",
        "no difference",
    ),
    ClaimMode.CONFIRMATORY: (
        "primary endpoint",
        "hypothesis tested",
        "confirmatory",
        "validation cohort",
        "randomized",
    ),
    ClaimMode.DESCRIPTIVE: (
        "descriptive",
        "characterization",
        "survey",
        "profiling",
        "landscape",
        "mapping",
        "systematic review",
        "meta analysis",
    ),
}


def _score_rule_matches(text: str, rules: Mapping) -> Dict:
    scores = {}
    for item, phrases in rules.items():
        if isinstance(item, ModalityOverlay):
            matches = _matched_overlay_terms(text, item, phrases)
        else:
            matches = _matched_terms(text, phrases)
        if matches:
            scores[item] = matches
    return scores


def _best_study_class(matches: Mapping[StudyClass, Tuple[str, ...]]) -> Optional[StudyClass]:
    if not matches:
        return None
    ranked = sorted(
        matches.items(),
        key=lambda item: (len(item[1]), item[0].value),
        reverse=True,
    )
    return ranked[0][0]


def _best_claim_mode(
    text: str,
    study_class: Optional[StudyClass],
    matches: Mapping[ClaimMode, Tuple[str, ...]],
) -> Optional[ClaimMode]:
    resource_matches = set(matches.get(ClaimMode.RESOURCE_RELEASE, ()))
    strong_resource_signal = bool(
        resource_matches.intersection(
            {
                "resource",
                "resource paper",
                "atlas resource",
                "reference atlas",
                "benchmark dataset",
                "software",
                "software tool",
                "toolkit",
                "web server",
            }
        )
    )
    if study_class == StudyClass.METHODS_RESOURCE and resource_matches:
        return ClaimMode.RESOURCE_RELEASE
    if resource_matches and (strong_resource_signal or len(resource_matches) >= 2):
        return ClaimMode.RESOURCE_RELEASE
    if ClaimMode.NEGATIVE_RESULT in matches:
        return ClaimMode.NEGATIVE_RESULT
    if study_class == StudyClass.SYSTEMATIC_REVIEW_META_ANALYSIS:
        return ClaimMode.DESCRIPTIVE
    if ClaimMode.CONFIRMATORY in matches:
        return ClaimMode.CONFIRMATORY
    if ClaimMode.DESCRIPTIVE in matches:
        return ClaimMode.DESCRIPTIVE
    if "exploratory" in text:
        return ClaimMode.EXPLORATORY
    return None


def suggest_governance_metadata_hints(paper: SourcePaper) -> MetadataGovernanceHint:
    text = _metadata_text(paper)
    study_class_matches = _score_rule_matches(text, STUDY_CLASS_RULES)
    overlay_matches = _score_rule_matches(text, OVERLAY_RULES)
    claim_mode_matches = _score_rule_matches(text, CLAIM_MODE_RULES)

    suggested_study_class = _best_study_class(study_class_matches)
    suggested_overlays = tuple(sorted(overlay_matches.keys(), key=lambda item: item.value))
    suggested_claim_mode = _best_claim_mode(text, suggested_study_class, claim_mode_matches)

    warnings: List[str] = []
    if suggested_study_class and suggested_study_class != paper.study_class:
        warnings.append(
            "metadata suggests study_class "
            + suggested_study_class.value
            + " but paper is configured as "
            + paper.study_class.value
        )

    missing_overlays = tuple(
        overlay for overlay in suggested_overlays if overlay not in paper.modality_overlays
    )
    if missing_overlays:
        warnings.append(
            "metadata suggests missing modality overlays: "
            + ", ".join(overlay.value for overlay in missing_overlays)
        )

    if suggested_claim_mode and suggested_claim_mode != paper.claim_mode:
        warnings.append(
            "metadata suggests claim_mode "
            + suggested_claim_mode.value
            + " but paper is configured as "
            + paper.claim_mode.value
        )

    configured_required = set(required_standards_for_configuration(paper.study_class, paper.modality_overlays))
    suggestion_study_class = suggested_study_class or paper.study_class
    suggestion_overlays = tuple(
        sorted(
            set(paper.modality_overlays).union(suggested_overlays),
            key=lambda item: item.value,
        )
    )
    suggested_required_standards = required_standards_for_configuration(
        suggestion_study_class,
        suggestion_overlays,
    )
    extra_suggested = [
        standard
        for standard in suggested_required_standards
        if standard not in configured_required
    ]
    if extra_suggested:
        warnings.append(
            "metadata suggests additional required standards: "
            + ", ".join(standard.value for standard in extra_suggested)
        )

    matched_terms = {
        "study_class": tuple(
            sorted(term for matches in study_class_matches.values() for term in matches)
        ),
        "claim_mode": tuple(
            sorted(term for matches in claim_mode_matches.values() for term in matches)
        ),
        "modality_overlays": tuple(
            sorted(term for matches in overlay_matches.values() for term in matches)
        ),
    }

    return MetadataGovernanceHint(
        paper_id=paper.paper_id,
        suggested_study_class=suggested_study_class,
        suggested_claim_mode=suggested_claim_mode,
        suggested_modality_overlays=suggested_overlays,
        suggested_required_standards=suggested_required_standards,
        matched_terms=matched_terms,
        warnings=tuple(warnings),
    )
