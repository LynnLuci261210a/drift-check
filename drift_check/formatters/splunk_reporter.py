"""Splunk HTTP Event Collector (HEC) JSON reporter for drift results."""
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


def _event(item: DriftItem, timestamp: float) -> dict:
    """Build a single Splunk HEC event dict for *item*."""
    event_body: dict = {
        "resource_id": item.resource_id,
        "resource_type": item.resource_type,
        "drift_kind": _KIND_LABEL[item.kind],
    }
    if item.attribute_diffs:
        event_body["attribute_diffs"] = [
            {
                "attribute": attr,
                "terraform": tf_val,
                "live": live_val,
            }
            for attr, (tf_val, live_val) in item.attribute_diffs.items()
        ]
    return {
        "time": timestamp,
        "sourcetype": "drift_check",
        "event": event_body,
    }


def render_splunk(
    items: List[DriftItem],
    *,
    timestamp: float | None = None,
    source: str = "drift-check",
    index: str = "main",
) -> str:
    """Return a newline-delimited sequence of Splunk HEC JSON events.

    When *items* is empty a single summary event is emitted so that the
    absence of drift is still recorded in Splunk.
    """
    ts = timestamp if timestamp is not None else time.time()
    common: dict = {"source": source, "index": index}

    if not items:
        summary_event = {
            **common,
            "time": ts,
            "sourcetype": "drift_check",
            "event": {"summary": "no_drift", "total": 0},
        }
        return json.dumps(summary_event)

    lines = [json.dumps({**common, **_event(item, ts)}) for item in items]

    summary_event = {
        **common,
        "time": ts,
        "sourcetype": "drift_check",
        "event": {
            "summary": "drift_detected",
            "total": len(items),
            "changed": sum(1 for i in items if i.kind == DriftKind.CHANGED),
            "missing_live": sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE),
            "extra_live": sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE),
        },
    }
    lines.append(json.dumps(summary_event))
    return "\n".join(lines)
