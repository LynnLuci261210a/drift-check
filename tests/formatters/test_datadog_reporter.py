"""Tests for the Datadog reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.datadog_reporter import render_datadog

FIXED_TS = 1_700_000_000


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        attribute="instance_type",
        expected="t3.micro",
        actual="t3.small",
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        attribute=None,
        expected=None,
        actual=None,
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_instance.rogue",
        resource_type="aws_instance",
        attribute=None,
        expected=None,
        actual=None,
    )


def test_no_drift_produces_summary_only():
    payload = render_datadog([], timestamp=FIXED_TS)
    assert "series" in payload
    # Only the three summary gauges, no item series
    assert len(payload["series"]) == 3


def test_no_drift_all_counts_zero():
    payload = render_datadog([], timestamp=FIXED_TS)
    for series in payload["series"]:
        assert series["points"][0]["value"] == 0.0


def test_changed_item_increments_changed_count(changed_item):
    payload = render_datadog([changed_item], timestamp=FIXED_TS)
    changed_series = next(
        s for s in payload["series"] if s["metric"] == "drift_check.changed"
    )
    assert changed_series["points"][0]["value"] == 1.0


def test_item_series_contains_resource_id(changed_item):
    payload = render_datadog([changed_item], timestamp=FIXED_TS)
    item_series = [s for s in payload["series"] if s["metric"] == "drift_check.resource_drift"]
    assert len(item_series) == 1
    assert "resource_id:aws_instance.web" in item_series[0]["tags"]


def test_item_series_contains_kind_tag(missing_item):
    payload = render_datadog([missing_item], timestamp=FIXED_TS)
    item_series = [s for s in payload["series"] if s["metric"] == "drift_check.resource_drift"]
    assert "kind:missing_live" in item_series[0]["tags"]


def test_timestamp_is_applied(changed_item):
    payload = render_datadog([changed_item], timestamp=FIXED_TS)
    for series in payload["series"]:
        assert series["points"][0]["timestamp"] == FIXED_TS


def test_multiple_items_produce_multiple_item_series(changed_item, missing_item, extra_item):
    payload = render_datadog([changed_item, missing_item, extra_item], timestamp=FIXED_TS)
    item_series = [s for s in payload["series"] if s["metric"] == "drift_check.resource_drift"]
    assert len(item_series) == 3


def test_series_type_is_gauge(changed_item):
    payload = render_datadog([changed_item], timestamp=FIXED_TS)
    for series in payload["series"]:
        assert series["type"] == 0
