"""Verify CycloneDX formatter is registered in the formatters registry."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters import get_available_formatters, get_formatter


def test_cyclonedx_is_listed():
    assert "cyclonedx" in get_available_formatters()


def test_get_formatter_returns_callable():
    fn = get_formatter("cyclonedx")
    assert callable(fn)


def test_get_formatter_no_drift_produces_string():
    fn = get_formatter("cyclonedx")
    result = fn([])
    assert isinstance(result, str)
    assert "bom" in result


def test_get_formatter_with_drift_contains_vulnerability():
    fn = get_formatter("cyclonedx")
    items = [
        DriftItem(
            resource_id="aws_instance.x",
            kind=DriftKind.CHANGED,
            diff={"ami": ("ami-old", "ami-new")},
        )
    ]
    result = fn(items)
    assert "vulnerability" in result
    assert "aws_instance.x" in result


def test_unknown_formatter_raises_key_error():
    with pytest.raises(KeyError):
        get_formatter("no_such_format")


def test_all_registered_formatters_are_importable():
    for name in get_available_formatters():
        fn = get_formatter(name)
        assert callable(fn), f"{name} formatter is not callable"
