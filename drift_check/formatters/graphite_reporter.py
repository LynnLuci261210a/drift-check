"""Graphite plaintext protocol reporter for drift metrics."""
from __future__ import annotations

import time
from typing import Sequence

from drift_check.drift_detector import DriftItem, DriftKind


def _sanitize(value: str) -> str:
    """Replace characters that are invalid in Graphite metric paths."""
    return value.replace(" ", "_").replace("/", ".").replace("-", "_")


def render_graphite(
    items: Sequence[DriftItem],
    *,
    prefix: str = "drift_check",
    timestamp: int | None = None,
) -> str:
    """Return Graphite plaintext protocol lines for the given drift items.

    Each line has the form::

        <prefix>.<resource_id>.<metric> <value> <timestamp>

    A summary block is always emitted under ``<prefix>.summary.*``.
    """
    ts = timestamp if timestamp is not None else int(time.time())
    lines: list[str] = []

    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)
    total = len(items)

    pfx = _sanitize(prefix)
    lines.append(f"{pfx}.summary.total {total} {ts}")
    lines.append(f"{pfx}.summary.changed {changed} {ts}")
    lines.append(f"{pfx}.summary.missing {missing} {ts}")
    lines.append(f"{pfx}.summary.extra {extra} {ts}")

    for item in items:
        rid = _sanitize(item.resource_id)
        kind_val = {
            DriftKind.CHANGED: 1,
            DriftKind.MISSING_LIVE: 2,
            DriftKind.EXTRA_LIVE: 3,
        }[item.kind]
        lines.append(f"{pfx}.resources.{rid}.drift_kind {kind_val} {ts}")
        if item.diff:
            lines.append(
                f"{pfx}.resources.{rid}.changed_attributes {len(item.diff)} {ts}"
            )

    return "\n".join(lines) + "\n"
