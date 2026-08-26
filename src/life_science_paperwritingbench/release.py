from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .models import (
    BenchmarkUnit,
    BenchmarkUnitDecisionRecord,
    BundleVerificationReport,
    ReleaseArtifactChecksum,
    ReleaseProvenanceManifest,
    SplitSafetyViolation,
)
from .policy import (
    DEFAULT_CANARY_PREFIX,
    DEFAULT_PRIVATE_HOLDOUT_RATIO,
    DEFAULT_PUBLIC_HOLDOUT_RATIO,
    ReleaseTier,
    SplitSafetyPolicy,
)
from .split_safety import validate_split_safety


PUBLIC_HOLDOUT_BUCKET = "public"
PRIVATE_HOLDOUT_BUCKET = "private"
RELEASE_INDEX_FILENAME = "release_index.jsonl"
SPLIT_SAFETY_VIOLATIONS_FILENAME = "split_safety_violations.jsonl"
RELEASE_SUMMARY_FILENAME = "release_summary.json"
PROVENANCE_MANIFEST_FILENAME = "provenance_manifest.json"
CHECKSUMS_FILENAME = "checksums.json"
BUNDLE_VERIFY_REPORT_FILENAME = "bundle_verify_report.json"


def _stable_score(key: str, salt: str) -> float:
    digest = hashlib.sha256(f"{salt}:{key}".encode("utf-8")).hexdigest()
    numerator = int(digest[:16], 16)
    denominator = float(16 ** 16 - 1)
    return numerator / denominator


def assign_holdout_bucket(
    key: str,
    public_ratio: float = DEFAULT_PUBLIC_HOLDOUT_RATIO,
    private_ratio: float = DEFAULT_PRIVATE_HOLDOUT_RATIO,
    salt: str = "ls-pwb-holdout-v1",
) -> str:
    total_ratio = public_ratio + private_ratio
    if public_ratio <= 0 or private_ratio <= 0:
        raise ValueError("public_ratio and private_ratio must both be positive")
    if abs(total_ratio - 1.0) > 1e-9:
        raise ValueError("public_ratio and private_ratio must sum to 1.0")
    score = _stable_score(key, salt)
    return PUBLIC_HOLDOUT_BUCKET if score < public_ratio else PRIVATE_HOLDOUT_BUCKET


def generate_canary_string(
    label: str,
    prefix: str = DEFAULT_CANARY_PREFIX,
    salt: str = "ls-pwb-canary-v1",
) -> str:
    normalized_label = re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_").upper() or "UNIT"
    digest = hashlib.sha256(f"{salt}:{label}".encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}-{normalized_label}-{digest}"


@dataclass(frozen=True)
class ReleaseIndexEntry:
    benchmark_unit_id: str
    paper_id: str
    release_tier: ReleaseTier
    holdout_bucket: str
    canary_string: str
    benchmark_split: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        return {
            "benchmark_unit_id": self.benchmark_unit_id,
            "paper_id": self.paper_id,
            "release_tier": self.release_tier.value,
            "holdout_bucket": self.holdout_bucket,
            "canary_string": self.canary_string,
            "benchmark_split": self.benchmark_split or "",
        }


@dataclass(frozen=True)
class ReleaseManifestBundle:
    release_index: Tuple[ReleaseIndexEntry, ...]
    split_safety_violations: Tuple[SplitSafetyViolation, ...] = ()
    provenance_manifest: Optional[ReleaseProvenanceManifest] = None
    artifact_checksums: Tuple[ReleaseArtifactChecksum, ...] = ()

    def summary(self) -> Dict[str, object]:
        holdout_counts = {
            PUBLIC_HOLDOUT_BUCKET: 0,
            PRIVATE_HOLDOUT_BUCKET: 0,
        }
        tier_counts = {tier.value: 0 for tier in ReleaseTier if tier != ReleaseTier.EXCLUDED}
        benchmark_split_counts: Dict[str, int] = {}
        for entry in self.release_index:
            holdout_counts[entry.holdout_bucket] += 1
            tier_counts[entry.release_tier.value] += 1
            benchmark_split = entry.benchmark_split or "unspecified"
            benchmark_split_counts[benchmark_split] = benchmark_split_counts.get(benchmark_split, 0) + 1
        return {
            "entries": len(self.release_index),
            "holdout_counts": holdout_counts,
            "tier_counts": tier_counts,
            "benchmark_split_counts": benchmark_split_counts,
            "split_safety_violations": len(self.split_safety_violations),
            "release_bundle_id": self.provenance_manifest.release_bundle_id
            if self.provenance_manifest
            else None,
        }


def _record_dict(record: Any) -> Dict[str, Any]:
    if hasattr(record, "to_dict"):
        return record.to_dict()
    if isinstance(record, Mapping):
        return dict(record)
    raise TypeError("record must provide to_dict() or be a mapping")


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_jsonl_bytes(records: Sequence[Any]) -> bytes:
    lines = [json.dumps(_record_dict(record), sort_keys=True) for record in records]
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _salt_digest(salt: str) -> str:
    return hashlib.sha256(salt.encode("utf-8")).hexdigest()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _artifact_checksums_from_payloads(payloads: Mapping[str, bytes]) -> Tuple[ReleaseArtifactChecksum, ...]:
    checksums = []
    for artifact_name, payload in sorted(payloads.items()):
        checksums.append(
            ReleaseArtifactChecksum(
                artifact_name=artifact_name,
                sha256=_sha256_hex(payload),
                size_bytes=len(payload),
                line_count=payload.count(b"\n") if artifact_name.endswith(".jsonl") else None,
            )
        )
    return tuple(checksums)


def _holdout_split_units(
    units: Sequence[BenchmarkUnit],
    public_ratio: float,
    private_ratio: float,
    holdout_salt: str,
) -> Tuple[BenchmarkUnit, ...]:
    def _holdout_group_key(unit: BenchmarkUnit) -> str:
        if unit.lineage.source_family:
            return f"source_family:{unit.lineage.source_family}"
        if unit.paper_id:
            return f"paper_id:{unit.paper_id}"
        return f"benchmark_unit_id:{unit.benchmark_unit_id}"

    reassigned = []
    for unit in units:
        reassigned.append(
            BenchmarkUnit(
                benchmark_unit_id=unit.benchmark_unit_id,
                paper_id=unit.paper_id,
                evidence_unit_ids=unit.evidence_unit_ids,
                split=assign_holdout_bucket(
                    _holdout_group_key(unit),
                    public_ratio=public_ratio,
                    private_ratio=private_ratio,
                    salt=holdout_salt,
                ),
                lineage=unit.lineage,
            )
        )
    return tuple(reassigned)


def build_release_index(
    units: Sequence[BenchmarkUnit],
    unit_decisions: Mapping[str, BenchmarkUnitDecisionRecord],
    public_ratio: float = DEFAULT_PUBLIC_HOLDOUT_RATIO,
    private_ratio: float = DEFAULT_PRIVATE_HOLDOUT_RATIO,
    holdout_salt: str = "ls-pwb-holdout-v1",
    canary_prefix: str = DEFAULT_CANARY_PREFIX,
    canary_salt: str = "ls-pwb-canary-v1",
    split_policy: Optional[SplitSafetyPolicy] = None,
    enforce_split_safety: bool = True,
) -> Tuple[ReleaseIndexEntry, ...]:
    for unit in units:
        if unit.benchmark_unit_id not in unit_decisions:
            raise KeyError(f"missing unit decision for {unit.benchmark_unit_id}")

    included_units = tuple(
        unit
        for unit in units
        if unit_decisions[unit.benchmark_unit_id].release_tier != ReleaseTier.EXCLUDED
    )
    holdout_units = _holdout_split_units(
        included_units,
        public_ratio=public_ratio,
        private_ratio=private_ratio,
        holdout_salt=holdout_salt,
    )
    holdout_by_unit_id = {
        unit.benchmark_unit_id: unit.split or PRIVATE_HOLDOUT_BUCKET
        for unit in holdout_units
    }
    violations = validate_split_safety(holdout_units, policy=split_policy)
    if enforce_split_safety and violations:
        summary = "; ".join(
            f"{item.violation_type.value}:{item.lineage_type}={item.lineage_value}"
            for item in violations
        )
        raise ValueError("release-index split safety failed: " + summary)

    entries = []
    for unit in included_units:
        decision = unit_decisions[unit.benchmark_unit_id]
        entries.append(
            ReleaseIndexEntry(
                benchmark_unit_id=unit.benchmark_unit_id,
                paper_id=unit.paper_id,
                release_tier=decision.release_tier,
                holdout_bucket=holdout_by_unit_id[unit.benchmark_unit_id],
                canary_string=generate_canary_string(
                    unit.benchmark_unit_id,
                    prefix=canary_prefix,
                    salt=canary_salt,
                ),
                benchmark_split=unit.split,
            )
        )
    return tuple(sorted(entries, key=lambda item: item.benchmark_unit_id))


def _build_release_provenance_manifest(
    units: Sequence[BenchmarkUnit],
    unit_decisions: Mapping[str, BenchmarkUnitDecisionRecord],
    release_index: Sequence[ReleaseIndexEntry],
    split_safety_violations: Sequence[SplitSafetyViolation],
    public_ratio: float,
    private_ratio: float,
    holdout_salt: str,
    canary_prefix: str,
    canary_salt: str,
    split_policy: Optional[SplitSafetyPolicy],
    generated_at: Optional[str],
    bundle_version: str,
) -> ReleaseProvenanceManifest:
    ordered_units = tuple(sorted(units, key=lambda item: item.benchmark_unit_id))
    ordered_decisions = tuple(
        unit_decisions[unit_id]
        for unit_id in sorted(unit_decisions)
    )
    units_fingerprint_sha256 = _sha256_hex(_canonical_jsonl_bytes(ordered_units))
    decisions_fingerprint_sha256 = _sha256_hex(_canonical_jsonl_bytes(ordered_decisions))
    included_unit_ids = tuple(entry.benchmark_unit_id for entry in release_index)
    excluded_unit_ids = tuple(
        sorted(
            unit_id
            for unit_id, decision in unit_decisions.items()
            if decision.release_tier == ReleaseTier.EXCLUDED
        )
    )
    summary_bundle = ReleaseManifestBundle(
        release_index=tuple(release_index),
        split_safety_violations=tuple(split_safety_violations),
    )
    summary = summary_bundle.summary()
    split_policy_summary = {
        "max_units_per_lineage": split_policy.max_units_per_lineage
        if split_policy is not None
        else SplitSafetyPolicy().max_units_per_lineage,
    }
    policy_fingerprint = _sha256_hex(
        _canonical_json_bytes(
            {
                "public_ratio": public_ratio,
                "private_ratio": private_ratio,
                "holdout_salt_sha256": _salt_digest(holdout_salt),
                "canary_prefix": canary_prefix,
                "canary_salt_sha256": _salt_digest(canary_salt),
                "split_safety_policy": split_policy_summary,
                "units_fingerprint_sha256": units_fingerprint_sha256,
                "decisions_fingerprint_sha256": decisions_fingerprint_sha256,
            }
        )
    )[:12].upper()
    return ReleaseProvenanceManifest(
        release_bundle_id=f"LS-PWB-BUNDLE-{policy_fingerprint}",
        generated_at=generated_at or _utc_timestamp(),
        bundle_version=bundle_version,
        units_fingerprint_sha256=units_fingerprint_sha256,
        decisions_fingerprint_sha256=decisions_fingerprint_sha256,
        input_record_counts={
            "benchmark_units": len(ordered_units),
            "unit_decisions": len(ordered_decisions),
        },
        included_benchmark_unit_ids=included_unit_ids,
        excluded_benchmark_unit_ids=excluded_unit_ids,
        holdout_policy={
            "public_ratio": public_ratio,
            "private_ratio": private_ratio,
            "salt_sha256": _salt_digest(holdout_salt),
        },
        canary_policy={
            "prefix": canary_prefix,
            "salt_sha256": _salt_digest(canary_salt),
        },
        split_safety_policy=split_policy_summary,
        holdout_counts=dict(summary["holdout_counts"]),
        tier_counts=dict(summary["tier_counts"]),
        benchmark_split_counts=dict(summary["benchmark_split_counts"]),
        split_safety_violation_count=len(split_safety_violations),
    )


def render_release_bundle_artifacts(
    bundle: ReleaseManifestBundle,
    include_checksums: bool = True,
) -> Dict[str, bytes]:
    payloads = {
        RELEASE_INDEX_FILENAME: _canonical_jsonl_bytes(bundle.release_index),
        SPLIT_SAFETY_VIOLATIONS_FILENAME: _canonical_jsonl_bytes(bundle.split_safety_violations),
        RELEASE_SUMMARY_FILENAME: _canonical_json_bytes(bundle.summary()),
    }
    if bundle.provenance_manifest is not None:
        payloads[PROVENANCE_MANIFEST_FILENAME] = _canonical_json_bytes(
            bundle.provenance_manifest.to_dict()
        )
    if include_checksums and bundle.artifact_checksums:
        payloads[CHECKSUMS_FILENAME] = _canonical_json_bytes(
            {
                "release_bundle_id": bundle.provenance_manifest.release_bundle_id
                if bundle.provenance_manifest
                else None,
                "artifacts": [item.to_dict() for item in bundle.artifact_checksums],
            }
        )
    return payloads


def verify_release_bundle_directory(bundle_dir: str) -> BundleVerificationReport:
    bundle_path = Path(bundle_dir)
    required_artifacts = (
        RELEASE_INDEX_FILENAME,
        SPLIT_SAFETY_VIOLATIONS_FILENAME,
        RELEASE_SUMMARY_FILENAME,
        PROVENANCE_MANIFEST_FILENAME,
        CHECKSUMS_FILENAME,
    )
    missing_artifacts = tuple(
        artifact_name
        for artifact_name in required_artifacts
        if not (bundle_path / artifact_name).exists()
    )
    if missing_artifacts:
        return BundleVerificationReport(
            bundle_dir=str(bundle_path),
            release_bundle_id=None,
            ok=False,
            missing_artifacts=missing_artifacts,
            notes=("bundle is missing one or more required release artifacts",),
        )

    with (bundle_path / RELEASE_SUMMARY_FILENAME).open("r", encoding="utf-8") as handle:
        summary_payload = json.load(handle)
    with (bundle_path / PROVENANCE_MANIFEST_FILENAME).open("r", encoding="utf-8") as handle:
        provenance_payload = json.load(handle)
    with (bundle_path / CHECKSUMS_FILENAME).open("r", encoding="utf-8") as handle:
        checksums_payload = json.load(handle)
    release_bundle_id = provenance_payload.get("release_bundle_id")

    checksum_mismatches = []
    verified_artifacts = []
    for artifact in checksums_payload.get("artifacts", []):
        artifact_name = str(artifact["artifact_name"])
        artifact_path = bundle_path / artifact_name
        if not artifact_path.exists():
            checksum_mismatches.append(f"{artifact_name}:missing")
            continue
        payload = artifact_path.read_bytes()
        if _sha256_hex(payload) != str(artifact["sha256"]):
            checksum_mismatches.append(f"{artifact_name}:sha256")
            continue
        if len(payload) != int(artifact["size_bytes"]):
            checksum_mismatches.append(f"{artifact_name}:size_bytes")
            continue
        if artifact.get("line_count") is not None and payload.count(b"\n") != int(artifact["line_count"]):
            checksum_mismatches.append(f"{artifact_name}:line_count")
            continue
        verified_artifacts.append(artifact_name)

    with (bundle_path / RELEASE_INDEX_FILENAME).open("r", encoding="utf-8") as handle:
        release_index = [json.loads(line) for line in handle if line.strip()]
    with (bundle_path / SPLIT_SAFETY_VIOLATIONS_FILENAME).open("r", encoding="utf-8") as handle:
        split_violations = [json.loads(line) for line in handle if line.strip()]

    holdout_counts = {PUBLIC_HOLDOUT_BUCKET: 0, PRIVATE_HOLDOUT_BUCKET: 0}
    tier_counts: Dict[str, int] = {
        tier.value: 0
        for tier in ReleaseTier
        if tier != ReleaseTier.EXCLUDED
    }
    benchmark_split_counts: Dict[str, int] = {}
    release_index_ids = []
    for item in release_index:
        holdout_bucket = str(item["holdout_bucket"])
        holdout_counts[holdout_bucket] = holdout_counts.get(holdout_bucket, 0) + 1
        tier_key = str(item["release_tier"])
        tier_counts[tier_key] = tier_counts.get(tier_key, 0) + 1
        split_key = str(item.get("benchmark_split") or "unspecified")
        benchmark_split_counts[split_key] = benchmark_split_counts.get(split_key, 0) + 1
        release_index_ids.append(str(item["benchmark_unit_id"]))

    summary_consistent = (
        int(summary_payload.get("entries", -1)) == len(release_index)
        and dict(summary_payload.get("holdout_counts", {})) == holdout_counts
        and dict(summary_payload.get("tier_counts", {})) == tier_counts
        and dict(summary_payload.get("benchmark_split_counts", {})) == benchmark_split_counts
        and int(summary_payload.get("split_safety_violations", -1)) == len(split_violations)
    )

    provenance_consistent = (
        str(summary_payload.get("release_bundle_id")) == str(release_bundle_id)
        and str(checksums_payload.get("release_bundle_id")) == str(release_bundle_id)
        and tuple(provenance_payload.get("included_benchmark_unit_ids", [])) == tuple(release_index_ids)
        and int(provenance_payload.get("split_safety_violation_count", -1)) == len(split_violations)
        and dict(provenance_payload.get("holdout_counts", {})) == holdout_counts
        and dict(provenance_payload.get("tier_counts", {})) == tier_counts
        and dict(provenance_payload.get("benchmark_split_counts", {})) == benchmark_split_counts
    )

    ok = (
        not missing_artifacts
        and not checksum_mismatches
        and summary_consistent
        and provenance_consistent
    )
    notes = []
    if not summary_consistent:
        notes.append("release summary does not match the indexed artifacts")
    if not provenance_consistent:
        notes.append("provenance manifest does not match bundle contents")
    return BundleVerificationReport(
        bundle_dir=str(bundle_path),
        release_bundle_id=release_bundle_id,
        ok=ok,
        verified_artifacts=tuple(sorted(verified_artifacts)),
        missing_artifacts=missing_artifacts,
        checksum_mismatches=tuple(sorted(checksum_mismatches)),
        summary_consistent=summary_consistent,
        provenance_consistent=provenance_consistent,
        notes=tuple(notes),
    )


def build_release_manifest_bundle(
    units: Sequence[BenchmarkUnit],
    unit_decisions: Mapping[str, BenchmarkUnitDecisionRecord],
    public_ratio: float = DEFAULT_PUBLIC_HOLDOUT_RATIO,
    private_ratio: float = DEFAULT_PRIVATE_HOLDOUT_RATIO,
    holdout_salt: str = "ls-pwb-holdout-v1",
    canary_prefix: str = DEFAULT_CANARY_PREFIX,
    canary_salt: str = "ls-pwb-canary-v1",
    split_policy: Optional[SplitSafetyPolicy] = None,
    enforce_split_safety: bool = True,
    generated_at: Optional[str] = None,
    bundle_version: str = "release-bundle-v1",
) -> ReleaseManifestBundle:
    for unit in units:
        if unit.benchmark_unit_id not in unit_decisions:
            raise KeyError(f"missing unit decision for {unit.benchmark_unit_id}")

    included_units = tuple(
        unit
        for unit in units
        if unit_decisions[unit.benchmark_unit_id].release_tier != ReleaseTier.EXCLUDED
    )
    holdout_units = _holdout_split_units(
        included_units,
        public_ratio=public_ratio,
        private_ratio=private_ratio,
        holdout_salt=holdout_salt,
    )
    violations = tuple(validate_split_safety(holdout_units, policy=split_policy))
    if enforce_split_safety and violations:
        summary = "; ".join(
            f"{item.violation_type.value}:{item.lineage_type}={item.lineage_value}"
            for item in violations
        )
        raise ValueError("release manifest split safety failed: " + summary)
    release_index = build_release_index(
        units,
        unit_decisions,
        public_ratio=public_ratio,
        private_ratio=private_ratio,
        holdout_salt=holdout_salt,
        canary_prefix=canary_prefix,
        canary_salt=canary_salt,
        split_policy=split_policy,
        enforce_split_safety=False,
    )
    provenance_manifest = _build_release_provenance_manifest(
        units,
        unit_decisions,
        release_index=release_index,
        split_safety_violations=violations,
        public_ratio=public_ratio,
        private_ratio=private_ratio,
        holdout_salt=holdout_salt,
        canary_prefix=canary_prefix,
        canary_salt=canary_salt,
        split_policy=split_policy,
        generated_at=generated_at,
        bundle_version=bundle_version,
    )
    provisional_bundle = ReleaseManifestBundle(
        release_index=release_index,
        split_safety_violations=violations,
        provenance_manifest=provenance_manifest,
    )
    artifact_checksums = _artifact_checksums_from_payloads(
        render_release_bundle_artifacts(provisional_bundle, include_checksums=False)
    )
    return ReleaseManifestBundle(
        release_index=release_index,
        split_safety_violations=violations,
        provenance_manifest=provenance_manifest,
        artifact_checksums=artifact_checksums,
    )
