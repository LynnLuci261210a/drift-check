"""SARIF (Static Analysis Results Interchange Format) reporter for drift-check."""
from __future__ import annotations

import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_TOOL_NAME = "drift-check"
_TOOL_VERSION = "0.1.0"
_TOOL_URI = "https://github.com/example/drift-check"

_KIND_LEVEL = {
    DriftKind.CHANGED: "warning",
    DriftKind.MISSING_LIVE: "error",
    DriftKind.EXTRA_LIVE: "note",
}


def _rule_id(item: DriftItem) -> str:
    return f"DC{item.kind.value:03d}"


def _message_text(item: DriftItem) -> str:
    if item.kind == DriftKind.CHANGED:
        pairs = "; ".join(
            f"{k}: {v['terraform']!r} -> {v['live']!r}"
            for k, v in (item.attribute_diff or {}).items()
        )
        return f"Configuration drift on {item.resource_id}: {pairs}"
    if item.kind == DriftKind.MISSING_LIVE:
        return f"Resource {item.resource_id} defined in Terraform but not found in live state."
    return f"Resource {item.resource_id} exists in live state but not in Terraform."


def render_sarif(items: List[DriftItem]) -> str:
    """Return a SARIF 2.1.0 JSON string for *items*."""
    rules = {
        _rule_id(i): {
            "id": _rule_id(i),
            "name": i.kind.name.title().replace("_", ""),
            "shortDescription": {"text": i.kind.name.replace("_", " ").title()},
            "defaultConfiguration": {"level": _KIND_LEVEL[i.kind]},
        }
        for i in items
    }

    results = [
        {
            "ruleId": _rule_id(item),
            "level": _KIND_LEVEL[item.kind],
            "message": {"text": _message_text(item)},
            "locations": [
                {
                    "logicalLocations": [
                        {"name": item.resource_id, "kind": "resource"}
                    ]
                }
            ],
        }
        for item in items
    ]

    sarif = {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": _TOOL_NAME,
                        "version": _TOOL_VERSION,
                        "informationUri": _TOOL_URI,
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(sarif, indent=2)
