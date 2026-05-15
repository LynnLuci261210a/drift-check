"""JUnit XML reporter for drift-check results.

Produces a JUnit-compatible XML report so CI systems (Jenkins, GitHub
Actions, CircleCI, …) can display drift findings as test failures.
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


def _failure_message(item: DriftItem) -> str:
    """Build a human-readable failure message for a single drift item."""
    lines = [f"Drift kind : {_kind_label(item.kind)}"]
    if item.diff:
        for attr, (expected, actual) in item.diff.items():
            lines.append(f"  {attr}: expected={expected!r}  actual={actual!r}")
    return "\n".join(lines)


def render_junit(items: List[DriftItem], suite_name: str = "drift-check") -> str:
    """Return a JUnit XML string representing *items*.

    Every drift item becomes a <testcase> element.  Items with drift are
    marked as <failure>; a run with no drift produces a suite of zero
    failures.
    """
    suite = ET.Element("testsuite", name=suite_name)
    suite.set("tests", str(max(len(items), 1)))
    failures = sum(1 for i in items if i.kind != DriftKind.CHANGED or i.diff)
    suite.set("failures", str(len(items)))

    if not items:
        tc = ET.SubElement(suite, "testcase", name="no_drift", classname=suite_name)
        # empty testcase == pass
    else:
        for item in items:
            tc = ET.SubElement(
                suite,
                "testcase",
                name=item.resource_id,
                classname=f"{suite_name}.{_kind_label(item.kind)}",
            )
            failure = ET.SubElement(tc, "failure", message=_kind_label(item.kind))
            failure.text = _failure_message(item)

    suite.set("failures", str(len(items)))  # recalculate after loop
    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    return ET.tostring(suite, encoding="unicode", xml_declaration=True)
