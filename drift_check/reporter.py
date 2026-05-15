"""Core reporter that dispatches to the appropriate formatter."""
from __future__ import annotations

import json
from enum import Enum
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters import render_html, render_csv, render_markdown, render_junit


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    CSV = "csv"
    MARKDOWN = "markdown"
    JUNIT = "junit"


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "CHANGED",
        DriftKind.MISSING_LIVE: "MISSING_LIVE",
        DriftKind.EXTRA_LIVE: "EXTRA_LIVE",
    }[kind]


def render_text(items: List[DriftItem]) -> str:
    if not items:
        return "No drift detected.\n"
    lines: list[str] = []
    for item in items:
        lines.append(f"[{_kind_label(item.kind)}] {item.resource_id}")
        for attr, (expected, actual) in (item.diff or {}).items():
            lines.append(f"  {attr}: {expected!r} -> {actual!r}")
    return "\n".join(lines) + "\n"


def render_json(items: List[DriftItem]) -> str:
    payload = [
        {
            "resource_id": item.resource_id,
            "kind": _kind_label(item.kind),
            "diff": {
                k: {"expected": exp, "actual": act}
                for k, (exp, act) in (item.diff or {}).items()
            },
        }
        for item in items
    ]
    return json.dumps(payload, indent=2)


def report(
    items: List[DriftItem],
    fmt: OutputFormat = OutputFormat.TEXT,
) -> str:
    """Render *items* using the requested *fmt* and return the string."""
    dispatch = {
        OutputFormat.TEXT: render_text,
        OutputFormat.JSON: render_json,
        OutputFormat.HTML: render_html,
        OutputFormat.CSV: render_csv,
        OutputFormat.MARKDOWN: render_markdown,
        OutputFormat.JUNIT: render_junit,
    }
    renderer = dispatch[fmt]
    return renderer(items)
