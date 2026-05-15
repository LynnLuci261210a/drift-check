"""New Relic Events API JSON reporter for drift results."""
from __future__ import annotations

import json
import time
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_KIND_LABEL = {
    DriftKind.CHANGED: "changed",
    DriftKind.MISSING_LIVE: "missing_live",
    DriftKind.EXTRA_LIVE: "extra_live",
}


def _item_event(item: DriftItem, timestamp: int) -> dict:
    """Convert a single DriftItem to a New Relic custom event dict."""
    event: dict = {
        "eventType": "DriftCheckFinding",
        "timestamp": timestamp,
        "resourceId": item.resource_id,
        "resourceType": item.resource_type,
        "driftKind": _KIND_LABEL[item.kind],
        "attributeDriftCount": len(item.attribute_diffs),
    }
    # Flatten up to 5 attribute diffs as top-level fields for NRQL queries.
    for i, (attr, (tf_val, live_val)) in enumerate(list(item.attribute_diffs.items())[:5]):
        event[f"attr{i}_name"] = attr
        event[f"attr{i}_terraform"] = str(tf_val)
        event[f"attr{i}_live"] = str(live_val)
    return event


def render_newrelic(
    items: List[DriftItem],
    *,
    timestamp: int | None = None,
) -> str:
    """Return a JSON array of New Relic custom events.

    A summary event is always included.  Individual finding events are
    appended for each DriftItem so that NRQL queries can filter by
    resource or drift kind.
    """
    ts = timestamp if timestamp is not None else int(time.time())

    events: list[dict] = []

    for item in items:
        events.append(_item_event(item, ts))

    summary: dict = {
        "eventType": "DriftCheckSummary",
        "timestamp": ts,
        "total": len(items),
        "changed": sum(1 for i in items if i.kind == DriftKind.CHANGED),
        "missingLive": sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE),
        "extraLive": sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE),
        "hasDrift": len(items) > 0,
    }
    events.append(summary)

    return json.dumps(events, indent=2)
