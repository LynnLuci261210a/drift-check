"""Tests for the HTML report formatter."""
import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.html_reporter import render_html


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        attribute_diffs={"instance_type": ("t2.micro", "t3.medium")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        attribute_diffs={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_instance.orphan",
        attribute_diffs={},
    )


def test_no_drift_produces_valid_html():
    output = render_html([])
    assert "<!DOCTYPE html>" in output
    assert "No drift detected" in output


def test_no_drift_omits_table():
    output = render_html([])
    assert "<table" not in output


def test_changed_item_shows_badge(changed_item):
    output = render_html([changed_item])
    assert "CHANGED" in output


def test_changed_item_shows_resource_id(changed_item):
    output = render_html([changed_item])
    assert "aws_instance.web" in output


def test_changed_item_renders_diff_table(changed_item):
    output = render_html([changed_item])
    assert "instance_type" in output
    assert "t2.micro" in output
    assert "t3.medium" in output
    assert "<table" in output


def test_missing_item_shows_badge(missing_item):
    output = render_html([missing_item])
    assert "MISSING" in output


def test_extra_item_shows_badge(extra_item):
    output = render_html([extra_item])
    assert "EXTRA" in output


def test_summary_shows_item_count(changed_item, missing_item):
    output = render_html([changed_item, missing_item])
    assert "2 drift item(s)" in output


def test_html_escaping_in_resource_id():
    item = DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.<special>&",
        attribute_diffs={},
    )
    output = render_html([item])
    assert "<special>" not in output
    assert "&lt;special&gt;" in output
