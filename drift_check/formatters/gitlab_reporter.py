"""GitLab Code Quality / CI report formatter.

Produces a JSON array compatible with GitLab's Code Quality artifact format
(https://docs.gitlab.com/ee/ci/testing/code_quality.html) so drift items
appear as inline annotations in Merge Requests.
"""
from __future__ import annotations

import hashlib
import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


# GitLab severity levels accepted by the Code Quality spec
_SEVERITY_MAP: dict[DriftKind, str] = {
    DriftKind.CHANGED: "major",
    DriftKind.MISSING_LIVE: "critical",
    DriftKind.EXTRA_LIVE: "minor",
}


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing",
        DriftKind.EXTRA_LIVE: "extra",
    }[kind]


def _fingerprint(item: DriftItem) -> str:
    """Stable, unique fingerprint for deduplication in GitLab UI."""
    raw = f"{item.resource_id}:{item.kind.value}:{sorted(item.attribute_diff.keys())}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _description(item: DriftItem) -> str:
    label = _kind_label(item.kind)
    if item.kind == DriftKind.CHANGED and item.attribute_diff:
        attrs = ", ".join(
            f"{k}: {v['terraform']!r} -> {v['live']!r}"
            for k, v in item.attribute_diff.items()
        )
        return f"Drift [{label}] {item.resource_id}: {attrs}"
    return f"Drift [{label}] {item.resource_id}"


def render_gitlab(items: List[DriftItem]) -> str:
    """Render drift items as a GitLab Code Quality JSON artifact.

    Returns an empty JSON array when there is no drift.
    """
    issues = [
        {
            "description": _description(item),
            "severity": _SEVERITY_MAP[item.kind],
            "fingerprint": _fingerprint(item),
            "location": {
                "path": "terraform",
                "lines": {"begin": 1},
            },
        }
        for item in items
    ]
    return json.dumps(issues, indent=2)
