"""Core reporter: dispatches to the appropriate formatter and writes output."""
from __future__ import annotations

import json
import sys
from enum import Enum
from typing import Sequence, TextIO

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.html_reporter import render_html
from drift_check.formatters.csv_reporter import render_csv
from drift_check.formatters.markdown_reporter import render_markdown


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    CSV = "csv"
    MARKDOWN = "markdown"


def _kind_label(kind: DriftKind) -> str:
    return kind.value.replace("_", " ").upper()


def render_text(items: Sequence[DriftItem]) -> str:
    if not items:
        return "No drift detected.\n"
    lines: list[str] = [f"{len(items)} drift item(s) found:\n"]
    for item in items:
        lines.append(f"  [{_kind_label(item.kind)}] {item.resource_id} ({item.resource_type})")
        for attr, (expected, actual) in item.attribute_diffs.items():
            lines.append(f"    {attr}: expected={expected!r} actual={actual!r}")
    return "\n".join(lines) + "\n"


def render_json(items: Sequence[DriftItem]) -> str:
    payload = [
        {
            "resource_id": item.resource_id,
            "resource_type": item.resource_type,
            "kind": item.kind.value,
            "attribute_diffs": {
                k: {"expected": exp, "actual": act}
                for k, (exp, act) in item.attribute_diffs.items()
            },
        }
        for item in items
    ]
    return json.dumps(payload, indent=2)


def report(
    items: Sequence[DriftItem],
    fmt: OutputFormat = OutputFormat.TEXT,
    out: TextIO = sys.stdout,
) -> None:
    """Render *items* in the requested format and write to *out*."""
    renderers = {
        OutputFormat.TEXT: render_text,
        OutputFormat.JSON: render_json,
        OutputFormat.HTML: render_html,
        OutputFormat.CSV: render_csv,
        OutputFormat.MARKDOWN: render_markdown,
    }
    renderer = renderers[fmt]
    out.write(renderer(items))
