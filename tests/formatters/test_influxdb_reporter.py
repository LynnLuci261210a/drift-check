"""Tests for drift_check.formatters.influxdb_reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.influxdb_reporter import render_influxdb

FIXED_TS = 1_700_000_000_000_000_000  # fixed nanosecond timestamp for tests


@pytest.fixture
def changed_item():
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        attribute="instance_type",
        tf_value="t3.micro",
        live_value="t3.small",
    )


@pytest.fixture
def missing_item():
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        attribute=None,
        tf_value=None,
        live_value=None,
    )


@pytest.fixture
def extra_item():
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_instance.ghost",
        attribute=None,
        tf_value=None,
        live_value=None,
    )


def _parse(output: str) -> list[dict]:
    """Parse line-protocol lines into a list of dicts with keys: measurement, tags, fields, ts."""
    rows = []
    for line in output.strip().splitlines():
        meas_and_tags, rest = line.split(" ", 1)
        fields_str, ts = rest.rsplit(" ", 1)
        meas_parts = meas_and_tags.split(",", 1)
        meas = meas_parts[0]
        tags = dict(kv.split("=", 1) for kv in meas_parts[1].split(",")) if len(meas_parts) > 1 else {}
        fields = dict(kv.split("=", 1) for kv in fields_str.split(","))
        rows.append({"measurement": meas, "tags": tags, "fields": fields, "ts": int(ts)})
    return rows


def test_no_drift_produces_summary_only():
    output = render_influxdb([], timestamp=FIXED_TS)
    rows = _parse(output)
    assert len(rows) == 1
    assert rows[0]["tags"]["type"] == "summary"


def test_no_drift_summary_totals_are_zero():
    output = render_influxdb([], timestamp=FIXED_TS)
    rows = _parse(output)
    summary = rows[0]["fields"]
    assert summary["total"] == "0i"
    assert summary["changed"] == "0i"
    assert summary["missing_live"] == "0i"
    assert summary["extra_live"] == "0i"


def test_changed_item_increments_changed_counter(changed_item):
    output = render_influxdb([changed_item], timestamp=FIXED_TS)
    rows = _parse(output)
    assert rows[0]["fields"]["changed"] == "1i"
    assert rows[0]["fields"]["total"] == "1i"


def test_item_line_has_correct_kind_tag(changed_item):
    output = render_influxdb([changed_item], timestamp=FIXED_TS)
    rows = _parse(output)
    item_row = rows[1]
    assert item_row["tags"]["kind"] == "changed"


def test_item_line_contains_resource_id(changed_item):
    output = render_influxdb([changed_item], timestamp=FIXED_TS)
    rows = _parse(output)
    assert "aws_instance.web" in rows[1]["tags"]["resource_id"]


def test_item_line_contains_attribute_and_values(changed_item):
    output = render_influxdb([changed_item], timestamp=FIXED_TS)
    rows = _parse(output)
    fields = rows[1]["fields"]
    assert "instance_type" in fields["attribute"]
    assert "t3.micro" in fields["tf_value"]
    assert "t3.small" in fields["live_value"]


def test_missing_live_item_tag(missing_item):
    output = render_influxdb([missing_item], timestamp=FIXED_TS)
    rows = _parse(output)
    assert rows[1]["tags"]["kind"] == "missing_live"


def test_extra_live_item_tag(extra_item):
    output = render_influxdb([extra_item], timestamp=FIXED_TS)
    rows = _parse(output)
    assert rows[1]["tags"]["kind"] == "extra_live"


def test_custom_measurement_name(changed_item):
    output = render_influxdb([changed_item], measurement="infra_drift", timestamp=FIXED_TS)
    assert output.startswith("infra_drift,")


def test_timestamp_is_propagated(changed_item):
    output = render_influxdb([changed_item], timestamp=FIXED_TS)
    for line in output.strip().splitlines():
        assert line.endswith(str(FIXED_TS))


def test_output_ends_with_newline(changed_item, missing_item, extra_item):
    output = render_influxdb([changed_item, missing_item, extra_item], timestamp=FIXED_TS)
    assert output.endswith("\n")
