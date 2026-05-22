"""Webhook (generic HTTP JSON POST) reporter for drift results."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _item_to_dict(item: DriftItem) -> dict:
    payload: dict = {
        "resource_id": item.resource_id,
        "resource_type": item.resource_type,
        "kind": _kind_label(item.kind),
    }
    if item.attribute_diffs:
        payload["attribute_diffs"] = [
            {
                "attribute": attr,
                "terraform": tf_val,
                "live": live_val,
            }
            for attr, tf_val, live_val in item.attribute_diffs
        ]
    return payload


def render_webhook(
    items: List[DriftItem],
    *,
    source: str = "drift-check",
    indent: int | None = 2,
) -> str:
    """Return a JSON string suitable for POSTing to a generic webhook endpoint.

    The envelope contains:
    - ``source``      – configurable sender identifier
    - ``timestamp``   – ISO-8601 UTC timestamp
    - ``summary``     – counts by drift kind
    - ``drift_items`` – list of individual drift records
    """
    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)

    envelope = {
        "source": source,
        "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total": len(items),
            "changed": changed,
            "missing_live": missing,
            "extra_live": extra,
            "has_drift": bool(items),
        },
        "drift_items": [_item_to_dict(i) for i in items],
    }
    return json.dumps(envelope, indent=indent)
