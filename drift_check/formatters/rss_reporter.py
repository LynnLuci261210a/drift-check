"""RSS 2.0 feed reporter for drift-check results."""
from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import List
from xml.etree import ElementTree as ET

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "Changed",
        DriftKind.MISSING_LIVE: "Missing (live)",
        DriftKind.EXTRA_LIVE: "Extra (live)",
    }[kind]


def _item_title(item: DriftItem) -> str:
    return f"[{_kind_label(item.kind)}] {item.resource_id}"


def _item_description(item: DriftItem) -> str:
    if item.kind == DriftKind.CHANGED and item.attribute_diffs:
        lines = []
        for attr, (expected, actual) in item.attribute_diffs.items():
            lines.append(
                f"<li><b>{html.escape(attr)}</b>: "
                f"expected {html.escape(repr(expected))}, "
                f"got {html.escape(repr(actual))}</li>"
            )
        return "<ul>" + "".join(lines) + "</ul>"
    return html.escape(_kind_label(item.kind))


def render_rss(
    items: List[DriftItem],
    *,
    feed_title: str = "drift-check report",
    feed_link: str = "https://github.com/your-org/drift-check",
    feed_description: str = "Infrastructure drift detected by drift-check",
) -> str:
    """Render drift items as an RSS 2.0 feed string."""
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = feed_title
    ET.SubElement(channel, "link").text = feed_link
    ET.SubElement(channel, "description").text = feed_description
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    ET.SubElement(channel, "pubDate").text = pub_date
    ET.SubElement(channel, "generator").text = "drift-check"

    if not items:
        item_el = ET.SubElement(channel, "item")
        ET.SubElement(item_el, "title").text = "No drift detected"
        ET.SubElement(item_el, "description").text = "All resources match Terraform state."
        ET.SubElement(item_el, "guid").text = "no-drift"
    else:
        for drift_item in items:
            item_el = ET.SubElement(channel, "item")
            ET.SubElement(item_el, "title").text = _item_title(drift_item)
            desc_el = ET.SubElement(item_el, "description")
            desc_el.text = _item_description(drift_item)
            ET.SubElement(item_el, "guid").text = (
                f"{drift_item.resource_id}:{drift_item.kind.value}"
            )
            ET.SubElement(item_el, "category").text = _kind_label(drift_item.kind)

    ET.indent(rss, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        rss, encoding="unicode"
    )
