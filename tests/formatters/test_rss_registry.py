"""Registry integration tests for the RSS reporter."""
from __future__ import annotations

import pytest
from xml.etree import ElementTree as ET

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters import get_available_formatters, get_formatter


def test_rss_is_listed():
    assert "rss" in get_available_formatters()


def test_get_formatter_returns_callable():
    fn = get_formatter("rss")
    assert callable(fn)


def test_get_formatter_no_drift_produces_string():
    fn = get_formatter("rss")
    result = fn([])
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_formatter_no_drift_valid_xml():
    fn = get_formatter("rss")
    result = fn([])
    root = ET.fromstring(result)
    assert root.tag == "rss"


def test_get_formatter_with_drift_contains_resource_id():
    fn = get_formatter("rss")
    item = DriftItem(
        resource_id="aws_instance.prod",
        kind=DriftKind.CHANGED,
        attribute_diffs={"ami": ("ami-old", "ami-new")},
    )
    result = fn([item])
    assert "aws_instance.prod" in result


def test_unknown_formatter_raises_key_error():
    with pytest.raises(KeyError):
        get_formatter("nonexistent_format_xyz")


def test_all_registered_formatters_are_importable():
    for name in get_available_formatters():
        fn = get_formatter(name)
        assert callable(fn), f"Formatter '{name}' is not callable"
