"""Azure DevOps logging commands reporter.

Emits Azure DevOps Pipeline logging commands so that drift items
appear as warnings/errors in the build summary when drift-check is
run inside an Azure Pipelines job.

See: https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands
"""
from __future__ import annotations

from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _escape(value: str) -> str:
    """Escape special characters for Azure DevOps logging command data."""
    return (
        value
        .replace("%", "%AZP25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace("]", "%5D")
    )


def _issue_line(item: DriftItem) -> str:
    """Format a single DriftItem as an ##[issue] logging command."""
    severity = "error" if item.kind == DriftKind.MISSING_LIVE else "warning"
    kind = _kind_label(item.kind)
    if item.diff:
        details = "; ".join(
            f"{attr}: {old!r} -> {new!r}" for attr, old, new in item.diff
        )
        message = f"[{kind}] {item.resource_id}: {details}"
    else:
        message = f"[{kind}] {item.resource_id}"
    return f"##vso[task.logissue type={severity}]{_escape(message)}"


def render_azure_devops(items: List[DriftItem]) -> str:
    """Return Azure DevOps logging-command lines for *items*.

    A summary ``##vso[task.complete]`` command is appended last so the
    pipeline step is marked as succeeded-with-issues when drift is found.
    """
    lines: list[str] = []
    for item in items:
        lines.append(_issue_line(item))

    total = len(items)
    if total == 0:
        result = "Succeeded"
        detail = "No drift detected."
    else:
        result = "SucceededWithIssues"
        detail = f"{total} drift item(s) detected."

    lines.append(f"##vso[task.complete result={result}]{_escape(detail)}")
    return "\n".join(lines)
