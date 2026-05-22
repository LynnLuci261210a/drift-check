"""Formatter that emits drift results as Terraform-style HCL-like output."""
from __future__ import annotations

from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "~",
        DriftKind.MISSING_LIVE: "-",
        DriftKind.EXTRA_LIVE: "+",
    }[kind]


def _format_item(item: DriftItem) -> str:
    lines: List[str] = []
    symbol = _kind_label(item.kind)
    lines.append(f"  {symbol} resource \"drift\" \"{item.resource_id}\" {{")
    if item.kind == DriftKind.CHANGED and item.diff:
        for attr, (expected, actual) in item.diff.items():
            lines.append(f"      # attribute: {attr}")
            lines.append(f"      - {attr} = {expected!r}")
            lines.append(f"      + {attr} = {actual!r}")
    elif item.kind == DriftKind.MISSING_LIVE:
        lines.append(f"      # resource exists in Terraform state but not in live infrastructure")
    elif item.kind == DriftKind.EXTRA_LIVE:
        lines.append(f"      # resource exists in live infrastructure but not in Terraform state")
    lines.append("  }")
    return "\n".join(lines)


def render_terraform(items: List[DriftItem]) -> str:
    """Render drift items as a Terraform plan-style diff string."""
    if not items:
        return "# No drift detected. Infrastructure matches Terraform state.\n"

    changed = [i for i in items if i.kind == DriftKind.CHANGED]
    missing = [i for i in items if i.kind == DriftKind.MISSING_LIVE]
    extra = [i for i in items if i.kind == DriftKind.EXTRA_LIVE]

    sections: List[str] = []
    sections.append("# Drift Check Report")
    sections.append(
        f"# Summary: {len(changed)} changed, {len(missing)} missing, {len(extra)} extra"
    )
    sections.append("")
    sections.append("drift {")
    for item in items:
        sections.append(_format_item(item))
    sections.append("}")
    sections.append("")
    return "\n".join(sections)
