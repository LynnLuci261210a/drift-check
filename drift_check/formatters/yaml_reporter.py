"""YAML formatter for drift-check reports."""
from __future__ import annotations

from typing import List

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyYAML is required for YAML output: pip install pyyaml") from exc

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _item_to_dict(item: DriftItem) -> dict:
    """Serialise a single DriftItem to a plain dict suitable for YAML."""
    record: dict = {
        "resource_id": item.resource_id,
        "kind": _kind_label(item.kind),
    }
    if item.attribute_diffs:
        record["attribute_diffs"] = [
            {
                "attribute": attr,
                "terraform": tf_val,
                "live": live_val,
            }
            for attr, tf_val, live_val in item.attribute_diffs
        ]
    return record


def render_yaml(items: List[DriftItem]) -> str:
    """Return a YAML string representing the drift report.

    The top-level document contains:
    - ``drift_detected`` (bool)
    - ``total`` (int)
    - ``items`` (list)
    """
    document = {
        "drift_detected": len(items) > 0,
        "total": len(items),
        "items": [_item_to_dict(i) for i in items],
    }
    return yaml.dump(document, default_flow_style=False, sort_keys=False)
