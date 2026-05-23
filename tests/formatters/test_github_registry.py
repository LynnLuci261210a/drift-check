"""Registry integration tests for the GitHub Actions reporter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters import get_available_formatters, get_formatter


def test_github_is_listed():
    assert "github" in get_available_formatters()


def test_get_formatter_returns_callable():
    fn = get_formatter("github")
    assert callable(fn)


def test_get_formatter_no_drift_produces_string():
    fn = get_formatter("github")
    result = fn([])
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_formatter_with_drift_produces_warning():
    fn = get_formatter("github")
    item = DriftItem(
        resource_id="aws_instance.test",
        kind=DriftKind.CHANGED,
        diff={"ami": {"terraform": "ami-old", "live": "ami-new"}},
    )
    result = fn([item])
    assert "::warning" in result
    assert "aws_instance.test" in result


def test_unknown_formatter_raises_key_error():
    with pytest.raises(KeyError):
        get_formatter("nonexistent_formatter_xyz")


def test_all_registered_formatters_are_importable():
    for name in get_available_formatters():
        fn = get_formatter(name)
        assert callable(fn), f"Formatter '{name}' is not callable"
