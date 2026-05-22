"""NDJSON (Newline-Delimited JSON) formatter for drift reports.

Each drift item is emitted as a single JSON object per line, preceded by
a summary line, making the output easy to stream and process with tools
like ``jq``.
"""
from __future__ import annotations

import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind, summary


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _item_to_dict(item: DriftItem) -> dict:
    record: dict = {
        "resource_id": item.resource_id,
        "resource_type": item.resource_type,
        "kind": _kind_label(item.kind),
    }
    if item.attribute_diffs:
        record["attribute_diffs"] = [
            {
                "attribute": attr,
                "terraform": tf_val,
                "live": live_val,
            }
            for attr, (tf_val, live_val) in item.attribute_diffs.items()
        ]
    return record


def render_ndjson(items: List[DriftItem]) -> str:
    """Render *items* as NDJSON.

    The first line is always a summary record.  Each subsequent line
    represents one :class:`~drift_check.drift_detector.DriftItem`.

    Args:
        items: Drift items produced by :func:`~drift_check.drift_detector.detect_drift`.

    Returns:
        A string where every line is a valid JSON object.
    """
    totals = summary(items)
    summary_record = {
        "record_type": "summary",
        "total": totals["total"],
        "changed": totals["changed"],
        "missing_live": totals["missing_live"],
        "extra_live": totals["extra_live"],
    }
    lines = [json.dumps(summary_record, separators=(",", ":"))]
    for item in items:
        record = _item_to_dict(item)
        record["record_type"] = "drift"
        lines.append(json.dumps(record, separators=(",", ":")))
    return "\n".join(lines) + "\n"
