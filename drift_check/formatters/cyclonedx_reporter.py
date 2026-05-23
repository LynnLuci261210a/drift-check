"""CycloneDX-inspired drift report formatter.

Produces a minimal CycloneDX-style XML document where each DriftItem
becomes a <vulnerability> element so the output can be ingested by
tools that understand the CycloneDX BOM standard.
"""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_SCHEMA_VERSION = "1.4"
_XMLNS = "http://cyclonedx.org/schema/bom/1.4"


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing-live",
        DriftKind.EXTRA_LIVE: "extra-live",
    }.get(kind, "unknown")


def _severity(kind: DriftKind) -> str:
    """Map drift kind to a CycloneDX severity string."""
    if kind == DriftKind.MISSING_LIVE:
        return "high"
    if kind == DriftKind.EXTRA_LIVE:
        return "medium"
    return "low"


def _description(item: DriftItem) -> str:
    if item.kind == DriftKind.CHANGED and item.diff:
        parts = [
            f"{attr}: expected={exp!r} actual={act!r}"
            for attr, (exp, act) in item.diff.items()
        ]
        return "; ".join(parts)
    return _kind_label(item.kind)


def render_cyclonedx(items: List[DriftItem]) -> str:
    """Return a CycloneDX BOM XML string representing *items*."""
    bom = ET.Element("bom", xmlns=_XMLNS, version="1")
    bom.set("serialNumber", f"urn:uuid:{uuid.uuid4()}")

    metadata = ET.SubElement(bom, "metadata")
    tool_el = ET.SubElement(ET.SubElement(metadata, "tools"), "tool")
    ET.SubElement(tool_el, "name").text = "drift-check"

    if not items:
        ET.indent(bom, space="  ")
        return ET.tostring(bom, encoding="unicode", xml_declaration=True)

    vulns = ET.SubElement(bom, "vulnerabilities")
    for item in items:
        vuln = ET.SubElement(vulns, "vulnerability")
        vuln.set("bom-ref", str(uuid.uuid4()))
        ET.SubElement(vuln, "id").text = item.resource_id
        ET.SubElement(vuln, "description").text = _description(item)
        ratings = ET.SubElement(vuln, "ratings")
        rating = ET.SubElement(ratings, "rating")
        ET.SubElement(rating, "severity").text = _severity(item.kind)
        props = ET.SubElement(vuln, "properties")
        p = ET.SubElement(props, "property")
        p.set("name", "drift-kind")
        p.text = _kind_label(item.kind)

    ET.indent(bom, space="  ")
    return ET.tostring(bom, encoding="unicode", xml_declaration=True)
