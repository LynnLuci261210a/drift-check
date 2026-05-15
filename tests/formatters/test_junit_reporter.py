"""Tests for the JUnit XML reporter."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.junit_reporter import render_junit


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        diff={},
    )


@pytest.fixture
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.ghost",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


def _parse(xml_str: str) -> ET.Element:
    return ET.fromstring(xml_str)


def test_no_drift_produces_valid_xml():
    xml_str = render_junit([])
    root = _parse(xml_str)
    assert root.tag == "testsuite"


def test_no_drift_has_zero_failures():
    root = _parse(render_junit([]))
    assert root.attrib["failures"] == "0"


def test_no_drift_contains_passing_testcase():
    root = _parse(render_junit([]))
    cases = root.findall("testcase")
    assert len(cases) == 1
    assert cases[0].attrib["name"] == "no_drift"
    assert cases[0].find("failure") is None


def test_changed_item_produces_failure(changed_item):
    root = _parse(render_junit([changed_item]))
    cases = root.findall("testcase")
    assert len(cases) == 1
    failure = cases[0].find("failure")
    assert failure is not None
    assert failure.attrib["message"] == "changed"


def test_failure_text_contains_attribute_diff(changed_item):
    root = _parse(render_junit([changed_item]))
    failure = root.find(".//failure")
    assert "instance_type" in failure.text
    assert "t2.micro" in failure.text
    assert "t3.small" in failure.text


def test_missing_live_item_classname(missing_item):
    root = _parse(render_junit([missing_item]))
    tc = root.find("testcase")
    assert "missing_live" in tc.attrib["classname"]


def test_multiple_items_all_present(changed_item, missing_item, extra_item):
    root = _parse(render_junit([changed_item, missing_item, extra_item]))
    cases = root.findall("testcase")
    assert len(cases) == 3
    ids = {tc.attrib["name"] for tc in cases}
    assert ids == {"aws_instance.web", "aws_s3_bucket.logs", "aws_instance.ghost"}


def test_failures_count_matches_items(changed_item, missing_item):
    root = _parse(render_junit([changed_item, missing_item]))
    assert root.attrib["failures"] == "2"


def test_custom_suite_name():
    root = _parse(render_junit([], suite_name="my-suite"))
    assert root.attrib["name"] == "my-suite"
