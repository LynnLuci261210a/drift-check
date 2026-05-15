"""PDF report formatter for drift-check results."""
from __future__ import annotations

from io import BytesIO
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    _REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _REPORTLAB_AVAILABLE = False


_KIND_LABEL: dict[DriftKind, str] = {
    DriftKind.CHANGED: "CHANGED",
    DriftKind.MISSING_LIVE: "MISSING (live)",
    DriftKind.EXTRA_LIVE: "EXTRA (live)",
}

_KIND_COLOR: dict[DriftKind, tuple] = {
    DriftKind.CHANGED: colors.orange,
    DriftKind.MISSING_LIVE: colors.red,
    DriftKind.EXTRA_LIVE: colors.blue,
}


def render_pdf(items: List[DriftItem]) -> bytes:
    """Render *items* as a PDF document and return raw bytes."""
    if not _REPORTLAB_AVAILABLE:  # pragma: no cover
        raise RuntimeError(
            "reportlab is required for PDF output. "
            "Install it with: pip install reportlab"
        )

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Drift-Check Report", styles["Title"]))
    story.append(Spacer(1, 12))

    if not items:
        story.append(Paragraph("\u2705 No drift detected.", styles["Normal"]))
        doc.build(story)
        return buf.getvalue()

    summary_text = f"Detected <b>{len(items)}</b> drift item(s)."
    story.append(Paragraph(summary_text, styles["Normal"]))
    story.append(Spacer(1, 12))

    header = ["Resource ID", "Kind", "Attribute", "Expected", "Live"]
    table_data = [header]

    row_colors: list[tuple] = []
    for idx, item in enumerate(items, start=1):
        row_bg = _KIND_COLOR.get(item.kind, colors.white)
        if item.kind == DriftKind.CHANGED:
            for attr, (expected, live) in (item.diff or {}).items():
                table_data.append(
                    [item.resource_id, _KIND_LABEL[item.kind], attr, str(expected), str(live)]
                )
                row_colors.append((len(table_data) - 1, row_bg))
        else:
            table_data.append([item.resource_id, _KIND_LABEL[item.kind], "", "", ""])
            row_colors.append((len(table_data) - 1, row_bg))

    col_widths = [160, 80, 90, 90, 90]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    base_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]
    for row_idx, bg in row_colors:
        base_style.append(("BACKGROUND", (1, row_idx), (1, row_idx), bg))

    tbl.setStyle(TableStyle(base_style))
    story.append(tbl)

    doc.build(story)
    return buf.getvalue()
