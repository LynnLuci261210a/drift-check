"""Tests for the CycloneDX formatter."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.cyclonedx_reporter import render_cyclonedx

NS = {"cdx": "http://cyclonedx.org/schema/bom/1.4"}


def _parse(text: str) -> ET.Element:
    return ET.fromstring(text)


@pytest.fixture
def changed_item():
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture
def missing_item():
    return DriftItem(
        resource_id="aws_instance.db",
        kind=DriftKind.MISSING_LIVE,
        diff={},
    )


@pytest.fixture
def extra_item():
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


def test_no_drift_produces_valid_xml():
    output = render_cyclonedx([])
    root = _parse(output)
    assert root.tag.endswith("bom")


def test_no_drift_omits_vulnerabilities_element():
    output = render_cyclonedx([])
    root = _parse(output)
    assert root.find("cdx:vulnerabilities", NS) is None


def test_no_drift_includes_tool_metadata():
    output = render_cyclonedx([])
    root = _parse(output)
    tool = root.find(".//cdx:tool/cdx:name", NS)
    assert tool is not None
    assert tool.text == "drift-check"


def test_changed_item_produces_vulnerability(changed_item):
    output = render_cyclonedx([changed_item])
    root = _parse(output)
    vulns = root.findall("cdx:vulnerabilities/cdx:vulnerability", NS)
    assert len(vulns) == 1


def test_changed_item_id_matches_resource(changed_item):
    output = render_cyclonedx([changed_item])
    root = _parse(output)
    vuln_id = root.find(".//cdx:vulnerability/cdx:id", NS)
    assert vuln_id is not None
    assert vuln_id.text == "aws_instance.web"


def test_changed_item_severity_is_low(changed_item):
    output = render_cyclonedx([changed_item])
    root = _parse(output)
    severity = root.find(".//cdx:rating/cdx:severity", NS)
    assert severity is not None
    assert severity.text == "low"


def test_missing_item_severity_is_high(missing_item):
    output = render_cyclonedx([missing_item])
    root = _parse(output)
    severity = root.find(".//cdx:rating/cdx:severity", NS)
    assert severity is not None
    assert severity.text == "high"


def test_extra_item_severity_is_medium(extra_item):
    output = render_cyclonedx([extra_item])
    root = _parse(output)
    severity = root.find(".//cdx:rating/cdx:severity", NS)
    assert severity is not None
    assert severity.text == "medium"


def test_description_contains_diff_details(changed_item):
    output = render_cyclonedx([changed_item])
    root = _parse(output)
    desc = root.find(".//cdx:vulnerability/cdx:description", NS)
    assert desc is not None
    assert "instance_type" in desc.text
    assert "t2.micro" in desc.text
    assert "t3.small" in desc.text


def test_multiple_items_produce_multiple_vulnerabilities(changed_item, missing_item, extra_item):
    output = render_cyclonedx([changed_item, missing_item, extra_item])
    root = _parse(output)
    vulns = root.findall("cdx:vulnerabilities/cdx:vulnerability", NS)
    assert len(vulns) == 3


def test_drift_kind_property_present(changed_item):
    output = render_cyclonedx([changed_item])
    root = _parse(output)
    props = root.findall(".//cdx:property", NS)
    drift_props = [p for p in props if p.get("name") == "drift-kind"]
    assert len(drift_props) == 1
    assert drift_props[0].text == "changed"


def test_serial_number_is_urn_uuid():
    output = render_cyclonedx([])
    root = _parse(output)
    serial = root.get("serialNumber", "")
    assert serial.startswith("urn:uuid:")
