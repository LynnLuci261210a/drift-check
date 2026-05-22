"""SonarQube Generic Issue Import format reporter.

Produces JSON consumable by SonarQube's Generic Issue Import feature:
https://docs.sonarqube.org/latest/analysis/generic-issue/
"""
from __future__ import annotations

import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_SEVERITY_MAP = {
    DriftKind.CHANGED: "MAJOR",
    DriftKind.MISSING: "CRITICAL",
    DriftKind.EXTRA: "MINOR",
}

_ENGINE_ID = "drift-check"
_RULE_ID_MAP = {
    DriftKind.CHANGED: "DRIFT001",
    DriftKind.MISSING: "DRIFT002",
    DriftKind.EXTRA: "DRIFT003",
}


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING: "missing",
        DriftKind.EXTRA: "extra",
    }[kind]


def _issue_message(item: DriftItem) -> str:
    label = _kind_label(item.kind)
    if item.kind == DriftKind.CHANGED and item.diff:
        attrs = ", ".join(item.diff.keys())
        return f"Resource {item.resource_id} has drifted ({label}): attributes [{attrs}] differ"
    return f"Resource {item.resource_id} is {label} in live infrastructure"


def _to_issue(item: DriftItem) -> dict:
    return {
        "engineId": _ENGINE_ID,
        "ruleId": _RULE_ID_MAP[item.kind],
        "severity": _SEVERITY_MAP[item.kind],
        "type": "BUG",
        "primaryLocation": {
            "message": _issue_message(item),
            "filePath": "terraform.tfstate",
        },
    }


def render_sonarqube(items: List[DriftItem]) -> str:
    """Render *items* as a SonarQube Generic Issue Import JSON string."""
    payload = {"issues": [_to_issue(item) for item in items]}
    return json.dumps(payload, indent=2)
