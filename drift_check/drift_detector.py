"""Core drift detection logic: compares Terraform state against live AWS state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from drift_check.parsers.terraform_state import TerraformResource
from drift_check.parsers.aws_state import LiveResource


class DriftKind(str, Enum):
    MISSING = "missing"          # resource in Terraform but not in AWS
    UNEXPECTED = "unexpected"    # resource in AWS but not in Terraform
    CHANGED = "changed"          # resource exists in both but attributes differ


@dataclass
class DriftItem:
    """Represents a single drift finding."""

    kind: DriftKind
    resource_type: str
    resource_id: str
    details: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        return f"[{self.kind.value.upper()}] {self.resource_type}.{self.resource_id}"


def _attribute_diff(
    tf_attrs: dict[str, Any], live_attrs: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Return a dict of attribute keys that differ between terraform and live state."""
    diffs: dict[str, dict[str, Any]] = {}
    all_keys = set(tf_attrs) | set(live_attrs)
    for key in all_keys:
        tf_val = tf_attrs.get(key)
        live_val = live_attrs.get(key)
        if tf_val != live_val:
            diffs[key] = {"terraform": tf_val, "live": live_val}
    return diffs


def detect_drift(
    tf_resources: list[TerraformResource],
    live_resources: list[LiveResource],
    ignore_keys: list[str] | None = None,
) -> list[DriftItem]:
    """Compare Terraform resources against live resources and return drift items.

    Args:
        tf_resources: Resources parsed from Terraform state file.
        live_resources: Resources fetched from live AWS.
        ignore_keys: Attribute keys to exclude from comparison.

    Returns:
        List of DriftItem describing each drift finding.
    """
    ignore: set[str] = set(ignore_keys or [])
    drift: list[DriftItem] = []

    live_index: dict[tuple[str, str], LiveResource] = {
        (r.resource_type, r.resource_id): r for r in live_resources
    }
    tf_index: dict[tuple[str, str], TerraformResource] = {
        (r.resource_type, r.resource_id): r for r in tf_resources
    }

    for key, tf_res in tf_index.items():
        if key not in live_index:
            drift.append(DriftItem(kind=DriftKind.MISSING, resource_type=key[0], resource_id=key[1]))
            continue
        live_res = live_index[key]
        tf_attrs = {k: v for k, v in tf_res.attributes.items() if k not in ignore}
        live_attrs = {k: v for k, v in live_res.attributes.items() if k not in ignore}
        diffs = _attribute_diff(tf_attrs, live_attrs)
        if diffs:
            drift.append(
                DriftItem(
                    kind=DriftKind.CHANGED,
                    resource_type=key[0],
                    resource_id=key[1],
                    details=diffs,
                )
            )

    for key in live_index:
        if key not in tf_index:
            drift.append(
                DriftItem(kind=DriftKind.UNEXPECTED, resource_type=key[0], resource_id=key[1])
            )

    return drift
