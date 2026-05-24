"""Tests for the StAX XML streaming reporter."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.stax_reporter import render_stax


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        diff={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        diff={},
    )


@pytest.fixture
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_instance.orphan",
        resource_type="aws_instance",
        diff={},
    )


def _parse(xml_str: str) -> ET.Element:
    return ET.fromstring(xml_str)


def test_no_drift_produces_valid_xml():
    output = render_stax([])
    root = _parse(output)
    assert root.tag == "driftReport"


def test_no_drift_summary_all_zeros():
    root = _parse(render_stax([]))
    summary = root.find("summary")
    assert summary is not None
    assert summary.attrib["total"] == "0"
    assert summary.attrib["changed"] == "0"
    assert summary.attrib["missing"] == "0"
    assert summary.attrib["extra"] == "0"


def test_no_drift_items_element_is_empty():
    root = _parse(render_stax([]))
    items = root.find("items")
    assert items is not None
    assert list(items) == []


def test_changed_item_appears_in_output(changed_item):
    root = _parse(render_stax([changed_item]))
    items = root.find("items")
    assert len(list(items)) == 1
    item_el = items[0]
    assert item_el.attrib["kind"] == "changed"
    assert item_el.attrib["resourceId"] == "aws_instance.web"


def test_changed_item_has_attribute_diff(changed_item):
    root = _parse(render_stax([changed_item]))
    attr_el = root.find(".//attribute[@name='instance_type']")
    assert attr_el is not None
    assert attr_el.attrib["expected"] == "t2.micro"
    assert attr_el.attrib["actual"] == "t3.small"


def test_missing_item_kind_label(missing_item):
    root = _parse(render_stax([missing_item]))
    item_el = root.find(".//item")
    assert item_el.attrib["kind"] == "missing_live"


def test_extra_item_kind_label(extra_item):
    root = _parse(render_stax([extra_item]))
    item_el = root.find(".//item")
    assert item_el.attrib["kind"] == "extra_live"


def test_summary_counts_multiple_items(changed_item, missing_item, extra_item):
    root = _parse(render_stax([changed_item, missing_item, extra_item]))
    summary = root.find("summary")
    assert summary.attrib["total"] == "3"
    assert summary.attrib["changed"] == "1"
    assert summary.attrib["missing"] == "1"
    assert summary.attrib["extra"] == "1"


def test_output_starts_with_xml_declaration():
    output = render_stax([])
    assert output.startswith("<?xml version=\"1.0\"")


def test_resource_type_attribute_present(changed_item):
    root = _parse(render_stax([changed_item]))
    item_el = root.find(".//item")
    assert item_el.attrib["resourceType"] == "aws_instance"
