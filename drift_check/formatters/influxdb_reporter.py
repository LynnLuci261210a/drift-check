"""InfluxDB line protocol reporter for drift-check results."""
from __future__ import annotations

import time
from typing import List, Optional

from drift_check.drift_detector import DriftItem, DriftKind


def _sanitize(value: str) -> str:
    """Escape special characters for InfluxDB line protocol tag/field values."""
    return value.replace(",", "\\,").replace(" ", "\ ").replace("=", "\\=")


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def render_influxdb(
    items: List[DriftItem],
    measurement: str = "drift_check",
    timestamp: Optional[int] = None,
) -> str:
    """Render drift items as InfluxDB line protocol.

    Each DriftItem becomes one line in the measurement.  A summary line
    with aggregate counters is always emitted first.

    Args:
        items: Detected drift items.
        measurement: InfluxDB measurement name (default: ``drift_check``).
        timestamp: Unix nanoseconds; defaults to the current time.

    Returns:
        Newline-terminated string in InfluxDB line protocol format.
    """
    ts = timestamp if timestamp is not None else time.time_ns()
    m = _sanitize(measurement)

    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)
    total = len(items)

    lines: List[str] = []

    # Summary line
    lines.append(
        f"{m},type=summary "
        f"total={total}i,changed={changed}i,missing_live={missing}i,extra_live={extra}i "
        f"{ts}"
    )

    for item in items:
        kind_tag = _sanitize(_kind_label(item.kind))
        resource_tag = _sanitize(item.resource_id)
        tags = f"type=item,kind={kind_tag},resource_id={resource_tag}"

        attribute = _sanitize(item.attribute or "")
        tf_val = _sanitize(str(item.tf_value) if item.tf_value is not None else "")
        live_val = _sanitize(str(item.live_value) if item.live_value is not None else "")

        fields = (
            f'attribute="{attribute}",'
            f'tf_value="{tf_val}",'
            f'live_value="{live_val}"'
        )
        lines.append(f"{m},{tags} {fields} {ts}")

    return "\n".join(lines) + "\n"
