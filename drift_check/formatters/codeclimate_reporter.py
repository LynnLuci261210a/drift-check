"""Code Climate JSON reporter for drift-check.

Produces a Code Climate-compatible JSON array suitable for use with
GitLab CI code-quality artifacts or the Code Climate CLI.
"""
from __future__ import annotations

import hashlib
import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


_SEVERITY_MAP = {
    DriftKind.CHANGED: "major",
    DriftKind.MISSING_LIVE: "critical",
    DriftKind.EXTRA_LIVE: "minor",
}


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _fingerprint(item: DriftItem) -> str:
    """Stable fingerprint derived from resource id and drift kind."""
    raw = f"{item.resource_id}:{_kind_label(item.kind)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _description(item: DriftItem) -> str:
    label = _kind_label(item.kind)
    if item.kind == DriftKind.CHANGED and item.attribute_diffs:
        attrs = ", ".join(item.attribute_diffs.keys())
        return f"Drift detected ({label}) on {item.resource_id}: attributes differ: {attrs}"
    return f"Drift detected ({label}) on {item.resource_id}"


def _to_issue(item: DriftItem) -> dict:
    return {
        "type": "issue",
        "check_name": f"drift-check/{_kind_label(item.kind)}",
        "description": _description(item),
        "severity": _SEVERITY_MAP[item.kind],
        "fingerprint": _fingerprint(item),
        "location": {
            "path": "terraform",
            "lines": {"begin": 1},
        },
        "categories": ["Bug Risk"],
    }


def render_codeclimate(items: List[DriftItem]) -> str:
    """Return a Code Climate JSON string for *items*."""
    issues = [_to_issue(item) for item in items]
    return json.dumps(issues, indent=2)
