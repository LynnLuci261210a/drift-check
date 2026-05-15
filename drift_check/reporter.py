"""Formats and outputs drift detection results."""

from __future__ import annotations

import json
import sys
from enum import Enum
from typing import IO, List

from drift_check.drift_detector import DriftItem, DriftKind


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


def _kind_label(kind: DriftKind) -> str:
    labels = {
        DriftKind.CHANGED: "CHANGED",
        DriftKind.MISSING_LIVE: "MISSING (live)",
        DriftKind.MISSING_TERRAFORM: "MISSING (terraform)",
    }
    return labels.get(kind, kind.value)


def render_text(items: List[DriftItem], out: IO[str] = sys.stdout) -> None:
    """Write a human-readable drift report to *out*."""
    if not items:
        out.write("No drift detected.\n")
        return

    out.write(f"Drift detected — {len(items)} issue(s):\n")
    for item in items:
        out.write(f"\n  [{_kind_label(item.kind)}] {item.resource_id}\n")
        if item.attribute:
            out.write(f"    attribute : {item.attribute}\n")
        if item.expected is not None:
            out.write(f"    expected  : {item.expected}\n")
        if item.actual is not None:
            out.write(f"    actual    : {item.actual}\n")


def render_json(items: List[DriftItem], out: IO[str] = sys.stdout) -> None:
    """Write a JSON drift report to *out*."""
    payload = [
        {
            "resource_id": item.resource_id,
            "kind": item.kind.value,
            "attribute": item.attribute,
            "expected": item.expected,
            "actual": item.actual,
        }
        for item in items
    ]
    json.dump({"drift_count": len(items), "items": payload}, out, indent=2)
    out.write("\n")


def report(
    items: List[DriftItem],
    fmt: OutputFormat = OutputFormat.TEXT,
    out: IO[str] = sys.stdout,
) -> int:
    """Render *items* in the requested format and return an exit code.

    Returns 1 when drift is present, 0 otherwise.
    """
    if fmt == OutputFormat.JSON:
        render_json(items, out)
    else:
        render_text(items, out)
    return 1 if items else 0
