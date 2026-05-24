"""Tests for the HTML timeline reporter."""
import pytest
from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.timeline_reporter import render_timeline


@pytest.fixture()
def changed_item():
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={
            "instance_type": {"terraform": "t2.micro", "live": "t3.small"},
        },
    )


@pytest.fixture()
def missing_item():
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        diff={},
    )


@pytest.fixture()
def extra_item():
    return DriftItem(
        resource_id="aws_instance.orphan",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


def test_no_drift_produces_valid_html():
    out = render_timeline([])
    assert "<!DOCTYPE html>" in out
    assert "<html" in out
    assert "</html>" in out


def test_no_drift_shows_success_message():
    out = render_timeline([])
    assert "No drift detected" in out


def test_no_drift_omits_event_divs():
    out = render_timeline([])
    assert "class='event" not in out


def test_changed_item_shows_resource_id(changed_item):
    out = render_timeline([changed_item])
    assert "aws_instance.web" in out


def test_changed_item_shows_badge(changed_item):
    out = render_timeline([changed_item])
    assert "changed" in out


def test_changed_item_shows_diff_attributes(changed_item):
    out = render_timeline([changed_item])
    assert "instance_type" in out
    assert "t2.micro" in out
    assert "t3.small" in out


def test_missing_item_shows_badge(missing_item):
    out = render_timeline([missing_item])
    assert "missing" in out


def test_extra_item_shows_badge(extra_item):
    out = render_timeline([extra_item])
    assert "extra" in out


def test_alternating_sides_for_multiple_items(changed_item, missing_item, extra_item):
    out = render_timeline([changed_item, missing_item, extra_item])
    assert "left" in out
    assert "right" in out


def test_item_count_in_header(changed_item, missing_item):
    out = render_timeline([changed_item, missing_item])
    assert "2 item(s)" in out


def test_html_escaping_in_resource_id():
    item = DriftItem(
        resource_id="aws_instance.<dangerous>&",
        kind=DriftKind.CHANGED,
        diff={},
    )
    out = render_timeline([item])
    assert "<dangerous>" not in out
    assert "&lt;dangerous&gt;" in out


def test_generated_timestamp_present():
    out = render_timeline([])
    assert "Generated:" in out
