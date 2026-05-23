"""TAP (Test Anything Protocol) formatter for drift results."""
from __future__ import annotations

from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _diagnostic(item: DriftItem) -> str:
    """Return a YAML-block diagnostic for a drift item."""
    lines = [
        "  ---",
        f"  resource_id: {item.resource_id}",
        f"  kind: {_kind_label(item.kind)}",
    ]
    if item.diff:
        lines.append("  diff:")
        for attr, (expected, actual) in item.diff.items():
            lines.append(f"    {attr}:")
            lines.append(f"      expected: {expected!r}")
            lines.append(f"      actual:   {actual!r}")
    lines.append("  ...")
    return "\n".join(lines)


def render_tap(items: List[DriftItem]) -> str:
    """Render drift items as a TAP version 13 document.

    Each drift item becomes a failing test point; a clean run produces
    a single passing point confirming no drift was detected.
    """
    output_lines: List[str] = ["TAP version 13"]

    if not items:
        output_lines.append("1..1")
        output_lines.append("ok 1 - no configuration drift detected")
        return "\n".join(output_lines) + "\n"

    total = len(items)
    output_lines.append(f"1..{total}")

    for idx, item in enumerate(items, start=1):
        description = f"{_kind_label(item.kind)}: {item.resource_id}"
        output_lines.append(f"not ok {idx} - {description}")
        output_lines.append(_diagnostic(item))

    return "\n".join(output_lines) + "\n"
