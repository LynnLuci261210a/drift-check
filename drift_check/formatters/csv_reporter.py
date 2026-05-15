"""CSV formatter for drift-check reports."""
from __future__ import annotations

import csv
import io
from typing import Sequence

from drift_check.drift_detector import DriftItem, DriftKind

_KIND_LABEL: dict[DriftKind, str] = {
    DriftKind.CHANGED: "changed",
    DriftKind.MISSING_LIVE: "missing_live",
    DriftKind.EXTRA_LIVE: "extra_live",
}

_HEADERS = [
    "resource_id",
    "resource_type",
    "drift_kind",
    "attribute",
    "expected",
    "actual",
]


def render_csv(items: Sequence[DriftItem]) -> str:
    """Return a CSV string representing *items*.

    Each changed attribute produces its own row.  Resources that are
    missing from live state or extra in live state produce a single row
    with empty attribute/expected/actual columns.
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_HEADERS, lineterminator="\n")
    writer.writeheader()

    for item in items:
        base = {
            "resource_id": item.resource_id,
            "resource_type": item.resource_type,
            "drift_kind": _KIND_LABEL[item.kind],
        }
        if item.kind == DriftKind.CHANGED and item.attribute_diffs:
            for attr, (expected, actual) in item.attribute_diffs.items():
                writer.writerow(
                    {
                        **base,
                        "attribute": attr,
                        "expected": expected if expected is not None else "",
                        "actual": actual if actual is not None else "",
                    }
                )
        else:
            writer.writerow(
                {**base, "attribute": "", "expected": "", "actual": ""}
            )

    return output.getvalue()
