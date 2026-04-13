from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .policy import CandidateTier, ClaimMode, ModalityOverlay, StudyClass


@dataclass(frozen=True)
class PilotCalibrationSpec:
    calibration_id: str
    study_class: StudyClass
    claim_mode: ClaimMode
    modality_overlays: Tuple[ModalityOverlay, ...] = ()
    target_candidate_tier: CandidateTier = CandidateTier.PUBLIC_GOLD_CANDIDATE
    expects_quarantine_case: bool = False
    controlled_access_example: bool = False
    preprint_shadow_only: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return {
            "calibration_id": self.calibration_id,
            "study_class": self.study_class.value,
            "claim_mode": self.claim_mode.value,
            "modality_overlays": [overlay.value for overlay in self.modality_overlays],
            "target_candidate_tier": self.target_candidate_tier.value,
            "expects_quarantine_case": self.expects_quarantine_case,
            "controlled_access_example": self.controlled_access_example,
            "preprint_shadow_only": self.preprint_shadow_only,
            "notes": list(self.notes),
        }


def pilot_calibration_spec_from_dict(data: Dict[str, object]) -> PilotCalibrationSpec:
    return PilotCalibrationSpec(
        calibration_id=str(data["calibration_id"]),
        study_class=StudyClass(str(data["study_class"])),
        claim_mode=ClaimMode(str(data["claim_mode"])),
        modality_overlays=tuple(
            ModalityOverlay(str(item)) for item in data.get("modality_overlays", [])
        ),
        target_candidate_tier=CandidateTier(
            str(data.get("target_candidate_tier", CandidateTier.PUBLIC_GOLD_CANDIDATE.value))
        ),
        expects_quarantine_case=bool(data.get("expects_quarantine_case", False)),
        controlled_access_example=bool(data.get("controlled_access_example", False)),
        preprint_shadow_only=bool(data.get("preprint_shadow_only", False)),
        notes=tuple(str(item) for item in data.get("notes", [])),
    )


@dataclass(frozen=True)
class CalibrationDriftReport:
    baseline_total_specs: int
    updated_total_specs: int
    added_calibration_ids: Tuple[str, ...] = ()
    removed_calibration_ids: Tuple[str, ...] = ()
    study_class_count_delta: Dict[str, int] = None
    candidate_tier_count_delta: Dict[str, int] = None
    hybrid_overlay_delta: int = 0
    quarantine_delta: int = 0
    controlled_access_delta: int = 0
    preprint_delta: int = 0
    negative_or_descriptive_delta: int = 0
    changed_target_labels: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return {
            "baseline_total_specs": self.baseline_total_specs,
            "updated_total_specs": self.updated_total_specs,
            "added_calibration_ids": list(self.added_calibration_ids),
            "removed_calibration_ids": list(self.removed_calibration_ids),
            "study_class_count_delta": dict(self.study_class_count_delta or {}),
            "candidate_tier_count_delta": dict(self.candidate_tier_count_delta or {}),
            "hybrid_overlay_delta": self.hybrid_overlay_delta,
            "quarantine_delta": self.quarantine_delta,
            "controlled_access_delta": self.controlled_access_delta,
            "preprint_delta": self.preprint_delta,
            "negative_or_descriptive_delta": self.negative_or_descriptive_delta,
            "changed_target_labels": list(self.changed_target_labels),
        }


def pilot_coverage_summary(specs: Sequence[PilotCalibrationSpec]) -> Dict[str, object]:
    study_class_counts = {
        study_class.value: 0 for study_class in StudyClass
    }
    candidate_tier_counts = {
        candidate_tier.value: 0 for candidate_tier in CandidateTier
    }

    hybrid_count = 0
    quarantine_count = 0
    controlled_access_count = 0
    preprint_count = 0
    negative_or_descriptive_count = 0

    for spec in specs:
        study_class_counts[spec.study_class.value] += 1
        candidate_tier_counts[spec.target_candidate_tier.value] += 1
        if len(spec.modality_overlays) >= 2:
            hybrid_count += 1
        if spec.expects_quarantine_case:
            quarantine_count += 1
        if spec.controlled_access_example:
            controlled_access_count += 1
        if spec.preprint_shadow_only:
            preprint_count += 1
        if spec.claim_mode in {
            ClaimMode.NEGATIVE_RESULT,
            ClaimMode.DESCRIPTIVE,
            ClaimMode.RESOURCE_RELEASE,
        }:
            negative_or_descriptive_count += 1

    return {
        "total_specs": len(specs),
        "study_class_counts": study_class_counts,
        "candidate_tier_counts": candidate_tier_counts,
        "hybrid_overlay_specs": hybrid_count,
        "quarantine_specs": quarantine_count,
        "controlled_access_specs": controlled_access_count,
        "preprint_specs": preprint_count,
        "negative_or_descriptive_specs": negative_or_descriptive_count,
    }


def validate_calibration_set(
    specs: Sequence[PilotCalibrationSpec],
    *,
    minimum_total: int,
    minimum_per_study_class: int,
    minimum_hybrid: int,
    minimum_quarantine: int,
    minimum_controlled_access: int,
    minimum_negative_or_descriptive: int,
) -> Tuple[str, ...]:
    issues: List[str] = []
    summary = pilot_coverage_summary(specs)

    if summary["total_specs"] < minimum_total:
        issues.append(f"calibration set must contain at least {minimum_total} papers")

    study_class_counts = summary["study_class_counts"]
    for study_class in StudyClass:
        if study_class_counts[study_class.value] < minimum_per_study_class:
            issues.append(
                f"calibration set must contain at least {minimum_per_study_class} papers for "
                + study_class.value
            )

    if summary["hybrid_overlay_specs"] < minimum_hybrid:
        issues.append(
            f"calibration set must contain at least {minimum_hybrid} hybrid multi-overlay papers"
        )

    if summary["quarantine_specs"] < minimum_quarantine:
        issues.append(
            f"calibration set must contain at least {minimum_quarantine} quarantine examples"
        )

    if summary["controlled_access_specs"] < minimum_controlled_access:
        issues.append(
            f"calibration set must contain at least {minimum_controlled_access} controlled-access examples"
        )

    if summary["negative_or_descriptive_specs"] < minimum_negative_or_descriptive:
        issues.append(
            "calibration set must contain at least "
            f"{minimum_negative_or_descriptive} negative-result or descriptive/resource examples"
        )

    return tuple(issues)


def validate_pilot_calibration_set(
    specs: Sequence[PilotCalibrationSpec],
) -> Tuple[str, ...]:
    issues = list(
        validate_calibration_set(
            specs,
            minimum_total=12,
            minimum_per_study_class=2,
            minimum_hybrid=3,
            minimum_quarantine=1,
            minimum_controlled_access=1,
            minimum_negative_or_descriptive=1,
        )
    )
    return tuple(
        issue.replace("calibration set", "pilot calibration set", 1)
        for issue in issues
    )


def validate_full_calibration_set(
    specs: Sequence[PilotCalibrationSpec],
) -> Tuple[str, ...]:
    return validate_calibration_set(
        specs,
        minimum_total=60,
        minimum_per_study_class=10,
        minimum_hybrid=15,
        minimum_quarantine=6,
        minimum_controlled_access=8,
        minimum_negative_or_descriptive=8,
    )


def build_full_calibration_scaffold(prefix: str = "full") -> Tuple[PilotCalibrationSpec, ...]:
    claim_modes = (
        ClaimMode.CONFIRMATORY,
        ClaimMode.EXPLORATORY,
        ClaimMode.DESCRIPTIVE,
        ClaimMode.NEGATIVE_RESULT,
        ClaimMode.RESOURCE_RELEASE,
        ClaimMode.CONFIRMATORY,
        ClaimMode.EXPLORATORY,
        ClaimMode.NEGATIVE_RESULT,
        ClaimMode.DESCRIPTIVE,
        ClaimMode.RESOURCE_RELEASE,
    )
    target_tiers = (
        CandidateTier.PUBLIC_GOLD_CANDIDATE,
        CandidateTier.PUBLIC_GOLD_CANDIDATE,
        CandidateTier.PUBLIC_GOLD_CANDIDATE,
        CandidateTier.SHADOW_CANDIDATE,
        CandidateTier.SHADOW_CANDIDATE,
        CandidateTier.PUBLIC_GOLD_CANDIDATE,
        CandidateTier.SHADOW_CANDIDATE,
        CandidateTier.STRESS_CANDIDATE,
        CandidateTier.PUBLIC_GOLD_CANDIDATE,
        CandidateTier.SHADOW_CANDIDATE,
    )
    overlay_cycle = (
        (),
        (ModalityOverlay.OMICS_TRANSCRIPTOMICS, ModalityOverlay.QPCR),
        (ModalityOverlay.STRUCTURAL_BIOPHYSICS,),
        (ModalityOverlay.SEQUENCE_METAGENOMICS, ModalityOverlay.ECOLOGY_BIODIVERSITY),
        (ModalityOverlay.PROTEOMICS_MASSSPEC,),
        (),
        (ModalityOverlay.BIOMARKER_PROGNOSTIC, ModalityOverlay.OMICS_TRANSCRIPTOMICS),
        (ModalityOverlay.QPCR, ModalityOverlay.ENZYMOLOGY),
        (ModalityOverlay.STRUCTURAL_BIOPHYSICS,),
        (),
    )

    specs: List[PilotCalibrationSpec] = []
    counter = 1
    for study_class in StudyClass:
        for index in range(10):
            specs.append(
                PilotCalibrationSpec(
                    calibration_id=f"{prefix}-{counter:02d}",
                    study_class=study_class,
                    claim_mode=claim_modes[index],
                    modality_overlays=overlay_cycle[index],
                    target_candidate_tier=target_tiers[index],
                    expects_quarantine_case=index == 0,
                    controlled_access_example=index in {0, 1},
                    preprint_shadow_only=index == 9,
                    notes=(
                        f"{study_class.value} calibration scaffold item {index + 1}",
                    ),
                )
            )
            counter += 1
    return tuple(specs)


def audit_calibration_drift(
    baseline_specs: Sequence[PilotCalibrationSpec],
    updated_specs: Sequence[PilotCalibrationSpec],
) -> CalibrationDriftReport:
    baseline_summary = pilot_coverage_summary(baseline_specs)
    updated_summary = pilot_coverage_summary(updated_specs)
    baseline_map = {spec.calibration_id: spec for spec in baseline_specs}
    updated_map = {spec.calibration_id: spec for spec in updated_specs}

    added = tuple(sorted(set(updated_map) - set(baseline_map)))
    removed = tuple(sorted(set(baseline_map) - set(updated_map)))
    changed = []
    for calibration_id in sorted(set(baseline_map) & set(updated_map)):
        old = baseline_map[calibration_id]
        new = updated_map[calibration_id]
        if (
            old.study_class != new.study_class
            or old.claim_mode != new.claim_mode
            or old.target_candidate_tier != new.target_candidate_tier
            or old.modality_overlays != new.modality_overlays
        ):
            changed.append(calibration_id)

    study_class_delta = {
        study_class.value: updated_summary["study_class_counts"][study_class.value]
        - baseline_summary["study_class_counts"][study_class.value]
        for study_class in StudyClass
    }
    candidate_tier_delta = {
        tier.value: updated_summary["candidate_tier_counts"][tier.value]
        - baseline_summary["candidate_tier_counts"][tier.value]
        for tier in CandidateTier
    }
    return CalibrationDriftReport(
        baseline_total_specs=baseline_summary["total_specs"],
        updated_total_specs=updated_summary["total_specs"],
        added_calibration_ids=added,
        removed_calibration_ids=removed,
        study_class_count_delta=study_class_delta,
        candidate_tier_count_delta=candidate_tier_delta,
        hybrid_overlay_delta=updated_summary["hybrid_overlay_specs"] - baseline_summary["hybrid_overlay_specs"],
        quarantine_delta=updated_summary["quarantine_specs"] - baseline_summary["quarantine_specs"],
        controlled_access_delta=updated_summary["controlled_access_specs"] - baseline_summary["controlled_access_specs"],
        preprint_delta=updated_summary["preprint_specs"] - baseline_summary["preprint_specs"],
        negative_or_descriptive_delta=updated_summary["negative_or_descriptive_specs"]
        - baseline_summary["negative_or_descriptive_specs"],
        changed_target_labels=tuple(changed),
    )
