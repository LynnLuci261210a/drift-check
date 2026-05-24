"""Plain-text table formatter for drift results.

Produces a human-readable, fixed-width table suitable for terminal
output or saving to a plain text file.
"""
from __future__ import annotations

from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_KIND_LABEL: dict[DriftKind, str] = {
    DriftKind.CHANGED: "CHANGED",
    DriftKind.MISSING_LIVE: "MISSING",
    DriftKind.EXTRA_LIVE: "EXTRA",
}

_COL_WIDTHS = {
    "resource_id": 40,
    "kind": 9,
    "attribute": 28,
    "expected": 22,
    "actual": 22,
}


def _header_row() -> str:
    return (
        f"{'Resource ID':<{_COL_WIDTHS['resource_id']}} "
        f"{'Kind':<{_COL_WIDTHS['kind']}} "
        f"{'Attribute':<{_COL_WIDTHS['attribute']}} "
        f"{'Expected':<{_COL_WIDTHS['expected']}} "
        f"{'Actual':<{_COL_WIDTHS['actual']}}"
    )


def _separator() -> str:
    return " ".join("-" * w for w in _COL_WIDTHS.values())


def _item_rows(item: DriftItem) -> List[str]:
    kind_label = _KIND_LABEL[item.kind]
    if item.kind == DriftKind.CHANGED and item.diff:
        rows = []
        for attr, (expected, actual) in item.diff.items():
            rows.append(
                f"{item.resource_id:<{_COL_WIDTHS['resource_id']}} "
                f"{kind_label:<{_COL_WIDTHS['kind']}} "
                f"{attr:<{_COL_WIDTHS['attribute']}} "
                f"{str(expected):<{_COL_WIDTHS['expected']}} "
                f"{str(actual):<{_COL_WIDTHS['actual']}}"
            )
        return rows
    return [
        f"{item.resource_id:<{_COL_WIDTHS['resource_id']}} "
        f"{kind_label:<{_COL_WIDTHS['kind']}} "
        f"{'—':<{_COL_WIDTHS['attribute']}} "
        f"{'—':<{_COL_WIDTHS['expected']}} "
        f"{'—':<{_COL_WIDTHS['actual']}}"
    ]


def render_table(items: List[DriftItem]) -> str:
    """Return a fixed-width table string representing *items*."""
    lines: List[str] = [_header_row(), _separator()]
    if not items:
        lines.append("No drift detected.")
    else:
        for item in items:
            lines.extend(_item_rows(item))
    lines.append(_separator())
    total = len(items)
    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)
    lines.append(
        f"Total: {total}  Changed: {changed}  Missing: {missing}  Extra: {extra}"
    )
    return "\n".join(lines) + "\n"
