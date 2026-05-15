"""Tests for the Markdown report formatter."""
import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.markdown_reporter import render_markdown


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        kind=DriftKind.CHANGED,
        attribute_diffs={"instance_type": ("t2.micro", "t3.medium")},
    )


@pytest.fixture
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs={},
    )


@pytest.fixture
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.orphan",
        resource_type="aws_instance",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diffs={},
    )


def test_no_drift_produces_heading()
    result = render_markdown([])
    assert "# Drift Report" in result


def test_no_drift_shows_success_message():
    result = render_markdown([])
    assert "No drift detected" in result


def test_no_drift_omits_table():
    result = render_markdown([])
    assert "|" not in result


def test_changed_item_shows_resource_id(changed_item):
    result = render_markdown([changed_item])
    assert "aws_instance.web" in result


def test_changed_item_shows_diff_table(changed_item):
    result = render_markdown([changed_item])
    assert "instance_type" in result
    assert "t2.micro" in result
    assert "t3.medium" in result


def test_changed_item_includes_emoji(changed_item):
    result = render_markdown([changed_item])
    assert "🔄" in result


def test_missing_item_shows_emoji(missing_item):
    result = render_markdown([missing_item])
    assert "❌" in result


def test_extra_item_shows_emoji(extra_item):
    result = render_markdown([extra_item])
    assert "➕" in result


def test_item_count_in_summary(changed_item, missing_item):
    result = render_markdown([changed_item, missing_item])
    assert "2 drift item(s)" in result


def test_multiple_items_all_present(changed_item, missing_item, extra_item):
    result = render_markdown([changed_item, missing_item, extra_item])
    assert "aws_instance.web" in result
    assert "aws_s3_bucket.logs" in result
    assert "aws_instance.orphan" in result
