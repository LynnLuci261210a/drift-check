"""TeamCity service-message formatter for drift-check results.

Produces TeamCity service messages that can be consumed directly by a
TeamCity build agent to surface drift items as test failures.

See https://www.jetbrains.com/help/teamcity/service-messages.html
"""
from __future__ import annotations

from typing import Sequence

from drift_check.drift_detector import DriftItem, DriftKind


def _escape(value: str) -> str:
    """Escape special characters for TeamCity service messages."""
    replacements = [
        ("|", "||"),
        ("'", "|'"),
        ("\n", "|n"),
        ("\r", "|r"),
        ("[", "|["),
        ("]", "|]"),
    ]
    for char, escaped in replacements:
        value = value.replace(char, escaped)
    return value


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _test_name(item: DriftItem) -> str:
    return f"drift.{_kind_label(item.kind)}.{item.resource_id}"


def _failure_details(item: DriftItem) -> str:
    if item.kind == DriftKind.CHANGED and item.diff:
        lines = []
        for attr, (expected, actual) in item.diff.items():
            lines.append(f"  {attr}: expected={expected!r} actual={actual!r}")
        return "\n".join(lines)
    if item.kind == DriftKind.MISSING_LIVE:
        return f"Resource '{item.resource_id}' is defined in Terraform but not found in live infrastructure."
    return f"Resource '{item.resource_id}' exists in live infrastructure but is not tracked by Terraform."


def render_teamcity(items: Sequence[DriftItem]) -> str:
    """Render drift items as TeamCity service messages."""
    lines: list[str] = []

    suite_name = "drift-check"
    lines.append(f"##teamcity[testSuiteStarted name='{_escape(suite_name)}']")  

    if not items:
        lines.append(
            f"##teamcity[testStarted name='{_escape('drift.no_drift')}']"
        )
        lines.append(
            f"##teamcity[testFinished name='{_escape('drift.no_drift')}']"
        )
    else:
        for item in items:
            name = _escape(_test_name(item))
            lines.append(f"##teamcity[testStarted name='{name}']")
            details = _escape(_failure_details(item))
            message = _escape(f"Drift detected: {_kind_label(item.kind)} on {item.resource_id}")
            lines.append(
                f"##teamcity[testFailed name='{name}' message='{message}' details='{details}']"
            )
            lines.append(f"##teamcity[testFinished name='{name}']")

    lines.append(f"##teamcity[testSuiteFinished name='{_escape(suite_name)}']")  
    return "\n".join(lines) + "\n"
