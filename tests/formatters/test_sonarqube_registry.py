"""Verify that the sonarqube formatter is reachable via the formatter registry."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters import get_available_formatters, get_formatter


def test_sonarqube_is_listed():
    assert "sonarqube" in get_available_formatters()


def test_get_formatter_returns_callable():
    fn = get_formatter("sonarqube")
    assert callable(fn)


def test_get_formatter_produces_valid_json():
    fn = get_formatter("sonarqube")
    item = DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.test",
        diff={"ami": ("ami-old", "ami-new")},
    )
    output = fn([item])
    parsed = json.loads(output)
    assert "issues" in parsed
    assert len(parsed["issues"]) == 1


def test_unknown_formatter_raises_key_error():
    with pytest.raises(KeyError, match="Unknown formatter"):
        get_formatter("nonexistent_format")


def test_all_registered_formatters_are_importable():
    """Smoke-test: every entry in the registry must resolve without ImportError."""
    for name in get_available_formatters():
        # Skip formatters with heavy optional deps that may not be installed
        if name in ("excel", "pdf"):
            continue
        fn = get_formatter(name)
        assert callable(fn), f"Formatter {name!r} did not return a callable"
