"""Tests for the Splunk HEC reporter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.splunk_reporter import render_splunk

FIXED_TS = 1_700_000_000.0


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        kind=DriftKind.CHANGED,
        attribute_diffs={"instance_type": ("t2.micro", "t3.micro")},
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
    return [json.loads(line) for line in output.strip().splitlines()]


def test_no_drift_produces_single_event():
    out = render_splunk([], timestamp=FIXED_TS)
    events = _parse(out)
    assert len(events) == 1


def test_no_drift_event_indicates_no_drift():
    out = render_splunk([], timestamp=FIXED_TS)
    events = _parse(out)
    assert events[0]["event"]["summary"] == "no_drift"
    assert events[0]["event"]["total"] == 0


def test_no_drift_uses_fixed_timestamp():
    out = render_splunk([], timestamp=FIXED_TS)
    events = _parse(out)
    assert events[0]["time"] == FIXED_TS


def test_drift_produces_item_events_plus_summary(changed_item, missing_item):
    out = render_splunk([changed_item, missing_item], timestamp=FIXED_TS)
    events = _parse(out)
    # 2 item events + 1 summary
    assert len(events) == 3


def test_summary_event_counts_are_correct(changed_item, missing_item, extra_item):
    out = render_splunk([changed_item, missing_item, extra_item], timestamp=FIXED_TS)
    events = _parse(out)
    summary = events[-1]["event"]
    assert summary["total"] == 3
    assert summary["changed"] == 1
    assert summary["missing_live"] == 1
    assert summary["extra_live"] == 1


def test_item_event_contains_resource_id(changed_item):
    out = render_splunk([changed_item], timestamp=FIXED_TS)
    events = _parse(out)
    assert events[0]["event"]["resource_id"] == "aws_instance.web"


def test_item_event_contains_drift_kind(changed_item):
    out = render_splunk([changed_item], timestamp=FIXED_TS)
    events = _parse(out)
    assert events[0]["event"]["drift_kind"] == "changed"


def test_changed_item_includes_attribute_diffs(changed_item):
    out = render_splunk([changed_item], timestamp=FIXED_TS)
    events = _parse(out)
    diffs = events[0]["event"]["attribute_diffs"]
    assert len(diffs) == 1
    assert diffs[0]["attribute"] == "instance_type"
    assert diffs[0]["terraform"] == "t2.micro"
    assert diffs[0]["live"] == "t3.micro"


def test_default_sourcetype_is_drift_check(changed_item):
    out = render_splunk([changed_item], timestamp=FIXED_TS)
    events = _parse(out)
    assert all(e["sourcetype"] == "drift_check" for e in events)


def test_custom_source_and_index(changed_item):
    out = render_splunk([changed_item], timestamp=FIXED_TS, source="ci", index="ops")
    events = _parse(out)
    assert all(e["source"] == "ci" for e in events)
    assert all(e["index"] == "ops" for e in events)
