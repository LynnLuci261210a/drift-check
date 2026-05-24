"""Shields.io-compatible JSON badge reporter for drift-check.

Produces a single JSON object that can be served as a dynamic badge endpoint
understood by https://shields.io/endpoint.

Schema reference:
  https://shields.io/endpoint
"""
from __future__ import annotations

import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

# Colour thresholds
_COLOUR_OK = "brightgreen"
_COLOUR_WARN = "yellow"
_COLOUR_ERROR = "red"


def _choose_colour(items: List[DriftItem]) -> str:
    """Return a Shields.io colour string based on drift severity."""
    if not items:
        return _COLOUR_OK
    kinds = {item.kind for item in items}
    if DriftKind.MISSING_LIVE in kinds or DriftKind.EXTRA_LIVE in kinds:
        return _COLOUR_ERROR
    return _COLOUR_WARN


def _label_text(items: List[DriftItem]) -> str:
    """Return a short human-readable message for the badge value."""
    if not items:
        return "in sync"
    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)
    parts: List[str] = []
    if changed:
        parts.append(f"{changed} changed")
    if missing:
        parts.append(f"{missing} missing")
    if extra:
        parts.append(f"{extra} extra")
    return ", ".join(parts)


def render_badges(items: List[DriftItem], **_kwargs: object) -> str:
    """Render *items* as a Shields.io endpoint JSON badge.

    Parameters
    ----------
    items:
        Drift items produced by :func:`drift_check.drift_detector.detect_drift`.

    Returns
    -------
    str
        A JSON string conforming to the Shields.io endpoint schema.
    """
    badge = {
        "schemaVersion": 1,
        "label": "drift",
        "message": _label_text(items),
        "color": _choose_colour(items),
        "isError": bool(items),
    }
    return json.dumps(badge, indent=2)
