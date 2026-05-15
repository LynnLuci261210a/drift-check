"""HTML report formatter for drift-check output."""
from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_KIND_BADGE: dict[DriftKind, tuple[str, str]] = {
    DriftKind.CHANGED: ("#d97706", "CHANGED"),
    DriftKind.MISSING_LIVE: ("#dc2626", "MISSING"),
    DriftKind.EXTRA_LIVE: ("#2563eb", "EXTRA"),
}


def _badge(kind: DriftKind) -> str:
    color, label = _KIND_BADGE[kind]
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:0.8em;font-weight:bold;">{label}</span>'
    )


def _diff_rows(item: DriftItem) -> str:
    if not item.attribute_diffs:
        return ""
    rows = []
    for attr, (expected, actual) in item.attribute_diffs.items():
        rows.append(
            "<tr>"
            f"<td style='padding:4px 8px;color:#6b7280;'>{html.escape(attr)}</td>"
            f"<td style='padding:4px 8px;color:#16a34a;'>{html.escape(str(expected))}</td>"
            f"<td style='padding:4px 8px;color:#dc2626;'>{html.escape(str(actual))}</td>"
            "</tr>"
        )
    header = (
        "<table style='margin-top:6px;border-collapse:collapse;width:100%;font-size:0.85em;'>"
        "<tr style='background:#f3f4f6;'>"
        "<th style='padding:4px 8px;text-align:left;'>Attribute</th>"
        "<th style='padding:4px 8px;text-align:left;'>Expected</th>"
        "<th style='padding:4px 8px;text-align:left;'>Actual</th>"
        "</tr>"
    )
    return header + "".join(rows) + "</table>"


def render_html(items: List[DriftItem]) -> str:
    """Render drift items as a self-contained HTML report string."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if not items:
        body = "<p style='color:#16a34a;font-weight:bold;'>&#10003; No drift detected.</p>"
    else:
        cards = []
        for item in items:
            cards.append(
                "<div style='border:1px solid #e5e7eb;border-radius:6px;"
                "padding:12px 16px;margin-bottom:12px;'>"
                f"<div>{_badge(item.kind)}&nbsp;"
                f"<strong>{html.escape(item.resource_id)}</strong></div>"
                + _diff_rows(item)
                + "</div>"
            )
        body = "".join(cards)

    summary_line = (
        f"<p style='color:#374151;'>{len(items)} drift item(s) found &mdash; {timestamp}</p>"
    )
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<title>Drift Check Report</title></head>"
        "<body style='font-family:sans-serif;max-width:860px;margin:40px auto;padding:0 16px;'>"
        "<h1 style='font-size:1.5rem;'>&#128270; Drift Check Report</h1>"
        + summary_line
        + body
        + "</body></html>"
    )
