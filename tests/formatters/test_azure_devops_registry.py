"""Verify that the azure_devops formatter is registered in the formatter registry."""
from __future__ import annotations

from drift_check.formatters import get_available_formatters, get_formatter
from drift_check.drift_detector import DriftItem, DriftKind


def test_azure_devops_is_listed():
    assert "azure_devops" in get_available_formatters()


def test_get_formatter_returns_callable():
    fn = get_formatter("azure_devops")
    assert callable(fn)


def test_get_formatter_produces_string():
    fn = get_formatter("azure_devops")
    result = fn([])
    assert isinstance(result, str)


def test_get_formatter_no_drift_succeeded():
    fn = get_formatter("azure_devops")
    result = fn([])
    assert "Succeeded" in result


def test_get_formatter_with_drift_succeeded_with_issues():
    fn = get_formatter("azure_devops")
    item = DriftItem(
        resource_id="aws_instance.test",
        kind=DriftKind.CHANGED,
        diff=[("ami", "ami-old", "ami-new")],
    )
    result = fn([item])
    assert "SucceededWithIssues" in result


def test_unknown_formatter_raises_key_error():
    import pytest
    with pytest.raises(KeyError):
        get_formatter("nonexistent_formatter_xyz")
