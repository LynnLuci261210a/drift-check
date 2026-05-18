"""Tests for drift_check.formatters.pagerduty_reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.pagerduty_reporter import render_pagerduty


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={
            "instance_type": {"terraform": "t3.micro", "live": "t3.small"},
        },
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.db",
        kind=DriftKind.MISSING_LIVE,
        diff={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


def test_no_drift_returns_empty_events():
    result = render_pagerduty([])
    assert result["events"] == []
    assert result["total_drift"] == 0


def test_no_drift_includes_source():
    result = render_pagerduty([], source="my-pipeline")
    assert result["source"] == "my-pipeline"


def test_changed_item_severity_is_warning(changed_item):
    result = render_pagerduty([changed_item])
    event = result["events"][0]
    assert event["payload"]["severity"] == "warning"


def test_missing_item_severity_is_critical(missing_item):
    result = render_pagerduty([missing_item])
    event = result["events"][0]
    assert event["payload"]["severity"] == "critical"


def test_extra_item_severity_is_info(extra_item):
    result = render_pagerduty([extra_item])
    event = result["events"][0]
    assert event["payload"]["severity"] == "info"


def test_event_action_is_trigger(changed_item):
    result = render_pagerduty([changed_item])
    assert result["events"][0]["event_action"] == "trigger"


def test_changed_item_summary_contains_resource_id(changed_item):
    result = render_pagerduty([changed_item])
    summary = result["events"][0]["payload"]["summary"]
    assert "aws_instance.web" in summary


def test_changed_item_summary_lists_attribute(changed_item):
    result = render_pagerduty([changed_item])
    summary = result["events"][0]["payload"]["summary"]
    assert "instance_type" in summary


def test_diff_values_included_in_custom_details(changed_item):
    result = render_pagerduty([changed_item])
    details = result["events"][0]["payload"]["custom_details"]
    assert details["diff"]["instance_type"]["terraform"] == "t3.micro"
    assert details["diff"]["instance_type"]["live"] == "t3.small"


def test_missing_item_has_no_diff_key_when_empty(missing_item):
    result = render_pagerduty([missing_item])
    details = result["events"][0]["payload"]["custom_details"]
    assert "diff" not in details


def test_total_drift_reflects_item_count(changed_item, missing_item, extra_item):
    result = render_pagerduty([changed_item, missing_item, extra_item])
    assert result["total_drift"] == 3
    assert len(result["events"]) == 3
