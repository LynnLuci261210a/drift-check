"""Tests for the RSS 2.0 reporter."""
from __future__ import annotations

import pytest
from xml.etree import ElementTree as ET

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.rss_reporter import render_rss


@pytest.fixture
def changed_item():
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        attribute_diffs={"instance_type": ("t2.micro", "t3.medium")},
    )


@pytest.fixture
def missing_item():
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs={},
    )


@pytest.fixture
def extra_item():
    return DriftItem(
        resource_id="aws_instance.old",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diffs={},
    )


def _parse(output: str) -> ET.Element:
    return ET.fromstring(output)


def test_no_drift_produces_valid_xml():
    out = render_rss([])
    root = _parse(out)
    assert root.tag == "rss"
    assert root.attrib["version"] == "2.0"


def test_no_drift_contains_no_drift_item():
    out = render_rss([])
    root = _parse(out)
    titles = [el.text for el in root.findall(".//item/title")]
    assert any("No drift" in t for t in titles)


def test_no_drift_description_all_match():
    out = render_rss([])
    root = _parse(out)
    descs = [el.text for el in root.findall(".//item/description")]
    assert any("match" in (d or "") for d in descs)


def test_drift_item_count_matches(changed_item, missing_item, extra_item):
    out = render_rss([changed_item, missing_item, extra_item])
    root = _parse(out)
    items = root.findall(".//item")
    assert len(items) == 3


def test_changed_item_title(changed_item):
    out = render_rss([changed_item])
    root = _parse(out)
    title = root.findtext(".//item/title")
    assert "Changed" in title
    assert "aws_instance.web" in title


def test_changed_item_description_contains_attribute(changed_item):
    out = render_rss([changed_item])
    root = _parse(out)
    desc = root.findtext(".//item/description")
    assert "instance_type" in desc
    assert "t2.micro" in desc
    assert "t3.medium" in desc


def test_missing_item_category(missing_item):
    out = render_rss([missing_item])
    root = _parse(out)
    category = root.findtext(".//item/category")
    assert category == "Missing (live)"


def test_extra_item_guid(extra_item):
    out = render_rss([extra_item])
    root = _parse(out)
    guid = root.findtext(".//item/guid")
    assert "aws_instance.old" in guid
    assert "extra_live" in guid


def test_custom_feed_metadata():
    out = render_rss(
        [],
        feed_title="My Feed",
        feed_link="https://example.com",
        feed_description="Custom desc",
    )
    root = _parse(out)
    assert root.findtext("channel/title") == "My Feed"
    assert root.findtext("channel/link") == "https://example.com"
    assert root.findtext("channel/description") == "Custom desc"


def test_output_starts_with_xml_declaration():
    out = render_rss([])
    assert out.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_generator_tag_present():
    out = render_rss([])
    root = _parse(out)
    generator = root.findtext("channel/generator")
    assert generator == "drift-check"
