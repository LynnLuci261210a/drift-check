"""Markdown report formatter for drift-check output."""
from __future__ import annotations

from typing import Sequence

from drift_check.drift_detector import DriftItem, DriftKind


_KIND_EMOJI = {
    DriftKind.CHANGED: "🔄",
    DriftKind.MISSING_LIVE: "❌",
    DriftKind.EXTRA_LIVE: "➕",
}


def _kind_label(kind: DriftKind) -> str:
    emoji = _KIND_EMOJI.get(kind, "")
    return f"{emoji} {kind.value.replace('_', ' ').title()}"


def _diff_table(item: DriftItem) -> str:
    if not item.attribute_diffs:
        return ""
    rows = ["| Attribute | Expected | Actual |",
            "| --- | --- | --- |"]
    for attr, (expected, actual) in item.attribute_diffs.items():
        rows.append(f"| `{attr}` | `{expected}` | `{actual}` |")
    return "\n".join(rows)


def render_markdown(items: Sequence[DriftItem]) -> str:
    """Render drift items as a Markdown document."""
    lines: list[str] = ["# Drift Report", ""]

    if not items:
        lines.append("✅ **No drift detected.** Infrastructure matches Terraform state.")
        return "\n".join(lines)

    lines.append(f"**{len(items)} drift item(s) detected.**")
    lines.append("")

    for item in items:
        lines.append(f"## {_kind_label(item.kind)}: `{item.resource_id}`")
        lines.append("")
        lines.append(f"- **Resource type:** `{item.resource_type}`")
        lines.append(f"- **Kind:** `{item.kind.value}`")
        lines.append("")
        table = _diff_table(item)
        if table:
            lines.append(table)
            lines.append("")

    return "\n".join(lines)
