"""OpsGenie-compatible alert payload reporter for drift results."""
from __future__ import annotations

from typing import Sequence

from drift_check.drift_detector import DriftItem, DriftKind

_KIND_PRIORITY: dict[DriftKind, str] = {
    DriftKind.MISSING_LIVE: "P1",
    DriftKind.CHANGED: "P2",
    DriftKind.EXTRA_LIVE: "P3",
}

_KIND_LABEL: dict[DriftKind, str] = {
    DriftKind.CHANGED: "changed",
    DriftKind.MISSING_LIVE: "missing_live",
    DriftKind.EXTRA_LIVE: "extra_live",
}


def _alert_message(items: Sequence[DriftItem]) -> str:
    counts = {k: 0 for k in DriftKind}
    for item in items:
        counts[item.kind] += 1
    parts = [
        f"{counts[DriftKind.CHANGED]} changed",
        f"{counts[DriftKind.MISSING_LIVE]} missing",
        f"{counts[DriftKind.EXTRA_LIVE]} extra",
    ]
    return "Terraform drift detected: " + ", ".join(parts)


def _highest_priority(items: Sequence[DriftItem]) -> str:
    priorities = [_KIND_PRIORITY[item.kind] for item in items]
    for p in ("P1", "P2", "P3", "P4", "P5"):
        if p in priorities:
            return p
    return "P5"


def render_opsgenie(items: Sequence[DriftItem], *, alias: str = "drift-check") -> dict:
    """Return an OpsGenie Create Alert request body.

    Returns an empty dict when there is no drift (no alert needed).
    """
    if not items:
        return {}

    details = {
        f"{_KIND_LABEL[item.kind]}:{item.resource_id}": item.attribute or "resource"
        for item in items
    }

    tags = sorted(
        {f"kind:{_KIND_LABEL[item.kind]}" for item in items}
        | {f"type:{item.resource_type}" for item in items}
    )

    return {
        "message": _alert_message(items),
        "alias": alias,
        "priority": _highest_priority(items),
        "tags": tags,
        "details": details,
    }
