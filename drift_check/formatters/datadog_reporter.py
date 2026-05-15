"""Datadog-compatible JSON reporter for drift results."""
from __future__ import annotations

import time
from typing import Sequence

from drift_check.drift_detector import DriftItem, DriftKind

_KIND_TO_ALERT: dict[DriftKind, str] = {
    DriftKind.CHANGED: "warning",
    DriftKind.MISSING_LIVE: "error",
    DriftKind.EXTRA_LIVE: "info",
}


def _series_tags(item: DriftItem) -> list[str]:
    tags = [
        f"resource_id:{item.resource_id}",
        f"resource_type:{item.resource_type}",
        f"kind:{item.kind.value}",
    ]
    return tags


def render_datadog(items: Sequence[DriftItem], *, timestamp: int | None = None) -> dict:
    """Return a Datadog-compatible metrics payload dict.

    The payload can be serialised to JSON and submitted to the
    ``/api/v2/series`` endpoint.
    """
    ts = timestamp if timestamp is not None else int(time.time())

    counts: dict[DriftKind, int] = {
        DriftKind.CHANGED: 0,
        DriftKind.MISSING_LIVE: 0,
        DriftKind.EXTRA_LIVE: 0,
    }
    for item in items:
        counts[item.kind] += 1

    summary_series = [
        {
            "metric": f"drift_check.{kind.value}",
            "type": 0,  # GAUGE
            "points": [{"timestamp": ts, "value": float(count)}],
            "tags": [f"kind:{kind.value}"],
        }
        for kind, count in counts.items()
    ]

    item_series = [
        {
            "metric": "drift_check.resource_drift",
            "type": 0,
            "points": [{"timestamp": ts, "value": 1.0}],
            "tags": _series_tags(item),
        }
        for item in items
    ]

    return {"series": summary_series + item_series}
