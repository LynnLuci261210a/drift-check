"""Tests for the TOML drift reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.toml_reporter import render_toml, _kind_label


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        attribute_diffs={"instance_type": ("t2.micro", "t3.medium")},
    )


@pytest.fixture
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs={},
    )


@pytest.fixture
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.orphan",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diffs={},
    )


def _parse(toml_str: str) -> dict:
    """Minimal TOML parser for test assertions (handles our specific output)."""
    import tomllib  # Python 3.11+
    return tomllib.loads(toml_str)


def test_kind_label_changed():
    assert _kind_label(DriftKind.CHANGED) == "changed"


def test_kind_label_missing_live():
    assert _kind_label(DriftKind.MISSING_LIVE) == "missing_live"


def test_kind_label_extra_live():
    assert _kind_label(DriftKind.EXTRA_LIVE) == "extra_live"


def test_no_drift_contains_summary():
    result = render_toml([])
    assert "[summary]" in result


def test_no_drift_totals_are_zero():
    result = render_toml([])
    assert "total = 0" in result
    assert "changed = 0" in result
    assert "missing_live = 0" in result
    assert "extra_live = 0" in result


def test_no_drift_shows_no_drift_comment():
    result = render_toml([])
    assert "No drift detected" in result


def test_no_drift_omits_drift_block():
    result = render_toml([])
    assert "[[drift]]" not in result


def test_changed_item_appears_in_output(changed_item):
    result = render_toml([changed_item])
    assert "aws_instance.web" in result
    assert "changed" in result


def test_changed_item_summary_counts(changed_item):
    result = render_toml([changed_item])
    assert "total = 1" in result
    assert "changed = 1" in result
    assert "missing_live = 0" in result


def test_attribute_diff_values_present(changed_item):
    result = render_toml([changed_item])
    assert "instance_type" in result
    assert "t2.micro" in result
    assert "t3.medium" in result


def test_missing_item_kind_label(missing_item):
    result = render_toml([missing_item])
    assert 'kind = "missing_live"' in result


def test_multiple_items_summary(changed_item, missing_item, extra_item):
    result = render_toml([changed_item, missing_item, extra_item])
    assert "total = 3" in result
    assert "changed = 1" in result
    assert "missing_live = 1" in result
    assert "extra_live = 1" in result


def test_output_ends_with_newline(changed_item):
    result = render_toml([changed_item])
    assert result.endswith("\n")


def test_no_drift_ends_with_newline():
    result = render_toml([])
    assert result.endswith("\n")


try:
    import tomllib

    def test_valid_toml_no_drift():
        result = render_toml([])
        parsed = tomllib.loads(result)
        assert parsed["summary"]["total"] == 0

    def test_valid_toml_with_items(changed_item, missing_item):
        result = render_toml([changed_item, missing_item])
        parsed = tomllib.loads(result)
        assert parsed["summary"]["total"] == 2
        assert len(parsed["drift"]) == 2

except ImportError:
    pass
