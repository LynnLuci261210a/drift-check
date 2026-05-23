"""GitHub Actions workflow commands and step-summary reporter."""
from __future__ import annotations

from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _annotation_level(kind: DriftKind) -> str:
    """Map drift kind to GitHub annotation level."""
    if kind == DriftKind.CHANGED:
        return "warning"
    return "error"


def _workflow_command(item: DriftItem) -> str:
    """Emit a ::warning:: or ::error:: workflow command line."""
    level = _annotation_level(item.kind)
    title = f"Drift detected [{_kind_label(item.kind)}]: {item.resource_id}"
    if item.diff:
        attrs = ", ".join(
            f"{k}: {v.get('terraform')!r} -> {v.get('live')!r}"
            for k, v in item.diff.items()
        )
        msg = f"{title} | {attrs}"
    else:
        msg = title
    return f"::{level} title={title}::{msg}"


def _summary_table(items: List[DriftItem]) -> str:
    """Render a Markdown summary table for GitHub step summary."""
    lines = [
        "## Drift Check Results",
        "",
        "| Resource ID | Kind | Details |",
        "| --- | --- | --- |",
    ]
    for item in items:
        if item.diff:
            details = "<br>".join(
                f"`{k}`: `{v.get('terraform')}` → `{v.get('live')}`"
                for k, v in item.diff.items()
            )
        else:
            details = _kind_label(item.kind)
        lines.append(f"| `{item.resource_id}` | {_kind_label(item.kind)} | {details} |")
    return "\n".join(lines)


def render_github(items: List[DriftItem]) -> str:
    """Render GitHub Actions output: workflow commands + step summary block.

    The returned string contains workflow command lines followed by a
    fenced Markdown block suitable for writing to $GITHUB_STEP_SUMMARY.
    """
    sections: List[str] = []

    if not items:
        sections.append("::notice title=Drift Check::No configuration drift detected.")
        sections.append("")
        sections.append("## Drift Check Results")
        sections.append("")
        sections.append("✅ No drift detected.")
        return "\n".join(sections)

    for item in items:
        sections.append(_workflow_command(item))

    sections.append("")
    sections.append(_summary_table(items))
    return "\n".join(sections)
