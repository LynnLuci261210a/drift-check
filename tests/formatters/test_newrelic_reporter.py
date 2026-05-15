"""Tests for the New Relic Events API reporter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.newrelic_reporter import render_newrelic

FIXED_TS = 1_700_000_000


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        kind=DriftKind.CHANGED,
        attribute_diffs={"instance_type": ("t2.micro", "t3.micro"), "ami": ("ami-aaa", "ami-bbb")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.ghost",
        resource_type="aws_instance",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diffs={},
    )


def _parse(output: str) -> list[dict]:
    return json.loads(output)


def test_no_drift_produces_only_summary():
    events = _parse(render_newrelic([], timestamp=FIXED_TS))
    assert len(events) == 1
    assert events[0]["eventType"] == "DriftCheckSummary"


def test_no_drift_summary_has_zero_counts():
    events = _parse(render_newrelic([], timestamp=FIXED_TS))
    summary = events[0]
    assert summary["total"] == 0
    assert summary["changed"] == 0
    assert summary["missingLive"] == 0
    assert summary["extraLive"] == 0
    assert summary["hasDrift"] is False


def test_no_drift_summary_timestamp(  ):
    events = _parse(render_newrelic([], timestamp=FIXED_TS))
    assert events[0]["timestamp"] == FIXED_TS


def test_drift_produces_finding_events_plus_summary(changed_item, missing_item):
    events = _parse(render_newrelic([changed_item, missing_item], timestamp=FIXED_TS))
    types = [e["eventType"] for e in events]
    assert types.count("DriftCheckFinding") == 2
    assert types.count("DriftCheckSummary") == 1


def test_summary_counts_are_correct(changed_item, missing_item, extra_item):
    events = _parse(render_newrelic([changed_item, missing_item, extra_item], timestamp=FIXED_TS))
    summary = next(e for e in events if e["eventType"] == "DriftCheckSummary")
    assert summary["total"] == 3
    assert summary["changed"] == 1
    assert summary["missingLive"] == 1
    assert summary["extraLive"] == 1
    assert summary["hasDrift"] is True


def test_finding_event_resource_fields(changed_item):
    events = _parse(render_newrelic([changed_item], timestamp=FIXED_TS))
    finding = next(e for e in events if e["eventType"] == "DriftCheckFinding")
    assert finding["resourceId"] == "aws_instance.web"
    assert finding["resourceType"] == "aws_instance"
    assert finding["driftKind"] == "changed"


def test_finding_event_attribute_drift_count(changed_item):
    events = _parse(render_newrelic([changed_item], timestamp=FIXED_TS))
    finding = next(e for e in events if e["eventType"] == "DriftCheckFinding")
    assert finding["attributeDriftCount"] == 2


def test_finding_event_flattened_attrs(changed_item):
    events = _parse(render_newrelic([changed_item], timestamp=FIXED_TS))
    finding = next(e for e in events if e["eventType"] == "DriftCheckFinding")
    assert "attr0_name" in finding
    assert finding["attr0_terraform"] in ("t2.micro", "ami-aaa")


def test_output_is_valid_json(changed_item, missing_item):
    out = render_newrelic([changed_item, missing_item], timestamp=FIXED_TS)
    parsed = json.loads(out)
    assert isinstance(parsed, list)
