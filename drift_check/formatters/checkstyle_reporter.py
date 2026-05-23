"""Checkstyle XML reporter for drift-check.

Emits a Checkstyle-compatible XML document so that CI tools (Jenkins,
GitHub Actions, etc.) can parse drift results as code-quality violations.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing_live",
        DriftKind.EXTRA_LIVE: "extra_live",
    }[kind]


def _severity(kind: DriftKind) -> str:
    """Map drift kind to a Checkstyle severity string."""
    if kind == DriftKind.CHANGED:
        return "warning"
    return "error"


def _error_message(item: DriftItem) -> str:
    """Build a human-readable message for a Checkstyle <error> element."""
    label = _kind_label(item.kind)
    if item.kind == DriftKind.CHANGED and item.diff:
        pairs = "; ".join(
            f"{attr}: expected={expected!r} got={live!r}"
            for attr, (expected, live) in item.diff.items()
        )
        return f"[{label}] {item.resource_id}: {pairs}"
    return f"[{label}] {item.resource_id}"


def render_checkstyle(items: List[DriftItem]) -> str:
    """Render *items* as a Checkstyle XML string.

    Each drifted resource becomes a ``<file>`` element (keyed by
    resource_id) containing one ``<error>`` per drift item.  When there
    is no drift the document contains a single empty ``<checkstyle>``
    root so downstream tooling still receives a valid document.
    """
    root = ET.Element("checkstyle", version="8.0")

    # Group items by resource_id so each resource maps to one <file>.
    grouped: dict[str, List[DriftItem]] = {}
    for item in items:
        grouped.setdefault(item.resource_id, []).append(item)

    for resource_id, resource_items in grouped.items():
        file_el = ET.SubElement(root, "file", name=resource_id)
        for item in resource_items:
            ET.SubElement(
                file_el,
                "error",
                line="1",
                column="0",
                severity=_severity(item.kind),
                message=_error_message(item),
                source=f"drift-check.{_kind_label(item.kind)}",
            )

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
