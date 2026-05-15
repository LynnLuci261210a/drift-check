"""Prometheus / OpenMetrics text-format reporter for drift results."""
from __future__ import annotations

from typing import Sequence

from drift_check.drift_detector import DriftItem, DriftKind

# Metric names
_METRIC_DRIFT_TOTAL = "drift_check_drift_total"
_METRIC_DRIFT_ITEMS = "drift_check_drift_items"

_KIND_LABEL: dict[DriftKind, str] = {
    DriftKind.CHANGED: "changed",
    DriftKind.MISSING_LIVE: "missing_live",
    DriftKind.EXTRA_LIVE: "extra_live",
}


def _escape_label_value(value: str) -> str:
    """Escape backslash, double-quote, and newline in Prometheus label values."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render_prometheus(items: Sequence[DriftItem]) -> str:
    """Return a Prometheus text-format string describing the drift results.

    Emits two metric families:
    - ``drift_check_drift_total``  – gauge with label ``kind`` (one series per kind)
    - ``drift_check_drift_items``  – gauge with labels ``resource_id`` and ``kind``
      (one series per drifted resource)
    """
    lines: list[str] = []

    # --- drift_check_drift_total ---
    counts: dict[str, int] = {label: 0 for label in _KIND_LABEL.values()}
    for item in items:
        counts[_KIND_LABEL[item.kind]] += 1

    lines.append(f"# HELP {_METRIC_DRIFT_TOTAL} Total number of drifted resources by kind.")
    lines.append(f"# TYPE {_METRIC_DRIFT_TOTAL} gauge")
    for kind_label, count in counts.items():
        lines.append(f'{_METRIC_DRIFT_TOTAL}{{kind="{kind_label}"}} {count}')

    lines.append("")

    # --- drift_check_drift_items ---
    lines.append(f"# HELP {_METRIC_DRIFT_ITEMS} Per-resource drift indicator (1 = drifted).")
    lines.append(f"# TYPE {_METRIC_DRIFT_ITEMS} gauge")
    for item in items:
        rid = _escape_label_value(item.resource_id)
        kind_label = _KIND_LABEL[item.kind]
        lines.append(f'{_METRIC_DRIFT_ITEMS}{{resource_id="{rid}",kind="{kind_label}"}} 1')

    if not items:
        lines.append(f"# no drift detected")

    lines.append("")  # trailing newline
    return "\n".join(lines)
