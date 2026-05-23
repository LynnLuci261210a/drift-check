"""Tests for drift_check.formatters.checkstyle_reporter."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.checkstyle_reporter import render_checkstyle


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        diff={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        diff={},
    )


@pytest.fixture()
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
    xml_str = render_checkstyle([])
    root = _parse(xml_str)
    assert root.tag == "checkstyle"


def test_no_drift_has_no_file_elements():
    root = _parse(render_checkstyle([]))
    assert root.findall("file") == []


def test_no_drift_includes_xml_declaration():
    xml_str = render_checkstyle([])
    assert xml_str.startswith("<?xml")


def test_changed_item_creates_file_element(changed_item):
    root = _parse(render_checkstyle([changed_item]))
    files = root.findall("file")
    assert len(files) == 1
    assert files[0].attrib["name"] == "aws_instance.web"


def test_changed_item_severity_is_warning(changed_item):
    root = _parse(render_checkstyle([changed_item]))
    error = root.find("file/error")
    assert error is not None
    assert error.attrib["severity"] == "warning"


def test_changed_item_message_contains_diff(changed_item):
    root = _parse(render_checkstyle([changed_item]))
    error = root.find("file/error")
    assert "instance_type" in error.attrib["message"]
    assert "t2.micro" in error.attrib["message"]
    assert "t3.small" in error.attrib["message"]


def test_missing_item_severity_is_error(missing_item):
    root = _parse(render_checkstyle([missing_item]))
    error = root.find("file/error")
    assert error.attrib["severity"] == "error"


def test_extra_item_severity_is_error(extra_item):
    root = _parse(render_checkstyle([extra_item]))
    error = root.find("file/error")
    assert error.attrib["severity"] == "error"


def test_source_attribute_reflects_kind(changed_item):
    root = _parse(render_checkstyle([changed_item]))
    error = root.find("file/error")
    assert error.attrib["source"] == "drift-check.changed"


def test_multiple_items_same_resource_grouped():
    items = [
        DriftItem(
            kind=DriftKind.CHANGED,
            resource_id="aws_instance.web",
            resource_type="aws_instance",
            diff={"instance_type": ("t2.micro", "t3.small")},
        ),
        DriftItem(
            kind=DriftKind.CHANGED,
            resource_id="aws_instance.web",
            resource_type="aws_instance",
            diff={"ami": ("ami-aaa", "ami-bbb")},
        ),
    ]
    root = _parse(render_checkstyle(items))
    files = root.findall("file")
    assert len(files) == 1
    errors = files[0].findall("error")
    assert len(errors) == 2


def test_multiple_resources_create_separate_file_elements(changed_item, missing_item):
    root = _parse(render_checkstyle([changed_item, missing_item]))
    names = {f.attrib["name"] for f in root.findall("file")}
    assert names == {"aws_instance.web", "aws_s3_bucket.logs"}
