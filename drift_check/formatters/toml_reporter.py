"""TOML formatter for drift-check output."""
from __future__ import annotations

from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _item_to_dict(item: DriftItem) -> dict:
    d: dict = {
        "resource_id": item.resource_id,
        "kind": _kind_label(item.kind),
    }
    if item.attribute_diffs:
        d["attribute_diffs"] = [
            {
                "attribute": attr,
                "terraform_value": str(tf_val),
                "live_value": str(live_val),
            }
            for attr, (tf_val, live_val) in item.attribute_diffs.items()
        ]
    return d


def render_toml(items: List[DriftItem]) -> str:
    """Render drift items as a TOML document."""
    lines: List[str] = []

    # Summary table
    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)
    total = len(items)

    lines.append("[summary]")
    lines.append(f"total = {total}")
    lines.append(f"changed = {changed}")
    lines.append(f"missing_live = {missing}")
    lines.append(f"extra_live = {extra}")

    if not items:
        lines.append("")
        lines.append("# No drift detected.")
        return "\n".join(lines) + "\n"

    for idx, item in enumerate(items):
        d = _item_to_dict(item)
        lines.append("")
        lines.append(f"[[drift]]")
        lines.append(f'resource_id = "{d["resource_id"]}"')
        lines.append(f'kind = "{d["kind"]}"')
        for diff in d.get("attribute_diffs", []):
            lines.append("")
            lines.append(f"  [[drift.attribute_diffs]]")
            lines.append(f'  attribute = "{diff["attribute"]}"')
            lines.append(f'  terraform_value = "{diff["terraform_value"]}"')
            lines.append(f'  live_value = "{diff["live_value"]}"')

    return "\n".join(lines) + "\n"
