"""Shields.io-compatible JSON badge reporter for drift status."""
from __future__ import annotations

import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _choose_colour(items: List[DriftItem]) -> str:
    if not items:
        return "brightgreen"
    kinds = {it.kind for it in items}
    if DriftKind.MISSING_LIVE in kinds:
        return "red"
    if DriftKind.CHANGED in kinds:
        return "orange"
    return "yellow"


def _label_text(items: List[DriftItem]) -> str:
    if not items:
        return "in sync"
    changed = sum(1 for it in items if it.kind == DriftKind.CHANGED)
    missing = sum(1 for it in items if it.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for it in items if it.kind == DriftKind.EXTRA_LIVE)
    parts: list[str] = []
    if changed:
        parts.append(f"{changed} changed")
    if missing:
        parts.append(f"{missing} missing")
    if extra:
        parts.append(f"{extra} extra")
    return ", ".join(parts) if parts else "drift detected"


def render_badges(items: List[DriftItem]) -> str:
    """Return a Shields.io endpoint-compatible JSON string."""
    payload = {
        "schemaVersion": 1,
        "label": "drift",
        "message": _label_text(items),
        "color": _choose_colour(items),
    }
    return json.dumps(payload, indent=2)
