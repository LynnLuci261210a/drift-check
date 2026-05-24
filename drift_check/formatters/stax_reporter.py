"""StAX-style XML streaming reporter for drift results."""
from __future__ import annotations

from typing import List
from xml.sax.saxutils import escape

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _diff_elements(item: DriftItem) -> str:
    if not item.diff:
        return ""
    lines: List[str] = ["      <attributes>"]
    for attr, (expected, actual) in item.diff.items():
        lines.append(
            f"        <attribute name={escape(attr)!r}"
            f" expected={escape(str(expected))!r}"
            f" actual={escape(str(actual))!r} />"
        )
    lines.append("      </attributes>")
    return "\n".join(lines)


def render_stax(items: List[DriftItem]) -> str:
    """Render drift items as a streaming-friendly XML document."""
    changed = [i for i in items if i.kind == DriftKind.CHANGED]
    missing = [i for i in items if i.kind == DriftKind.MISSING_LIVE]
    extra = [i for i in items if i.kind == DriftKind.EXTRA_LIVE]

    lines: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<driftReport>",
        "  <summary",
        f'    total="{len(items)}"',
        f'    changed="{len(changed)}"',
        f'    missing="{len(missing)}"',
        f'    extra="{len(extra)}"',
        "  />",
        "  <items>",
    ]

    for item in items:
        kind = _kind_label(item.kind)
        lines.append(
            f"    <item kind={escape(kind)!r}"
            f" resourceId={escape(item.resource_id)!r}"
            f" resourceType={escape(item.resource_type)!r}>"
        )
        diff_block = _diff_elements(item)
        if diff_block:
            lines.append(diff_block)
        lines.append("    </item>")

    lines += ["  </items>", "</driftReport>"]
    return "\n".join(lines)
