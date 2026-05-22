"""Tests for the NDJSON formatter."""
from __future__ import annotations

import json
from typing import List

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.ndjson_reporter import render_ndjson


def _parse(output: str) -> List[dict]:
    """Parse NDJSON output into a list of dicts."""
    return [json.loads(line) for line in output.strip().splitlines()]


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        kind=DriftKind.CHANGED,
        attribute_diffs={"instance_type": ("t2.micro", "t3.micro")},
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


def test_no_drift_produces_single_summary_line():
    output = render_ndjson([])
    records = _parse(output)
    assert len(records) == 1
    assert records[0]["record_type"] == "summary"


def test_no_drift_all_counts_zero():
    records = _parse(render_ndjson([]))
    s = records[0]
    assert s["total"] == 0
    assert s["changed"] == 0
    assert s["missing_live"] == 0
    assert s["extra_live"] == 0


def test_each_item_produces_one_line(changed_item, missing_item, extra_item):
    items = [changed_item, missing_item, extra_item]
    records = _parse(render_ndjson(items))
    # 1 summary + 3 drift records
    assert len(records) == 4


def test_summary_counts_correct(changed_item, missing_item, extra_item):
    records = _parse(render_ndjson([changed_item, missing_item, extra_item]))
    s = records[0]
    assert s["total"] == 3
    assert s["changed"] == 1
    assert s["missing_live"] == 1
    assert s["extra_live"] == 1


def test_drift_record_type_field(changed_item):
    records = _parse(render_ndjson([changed_item]))
    drift = records[1]
    assert drift["record_type"] == "drift"


def test_changed_item_kind_label(changed_item):
    records = _parse(render_ndjson([changed_item]))
    assert records[1]["kind"] == "changed"


def test_missing_item_kind_label(missing_item):
    records = _parse(render_ndjson([missing_item]))
    assert records[1]["kind"] == "missing_live"


def test_extra_item_kind_label(extra_item):
    records = _parse(render_ndjson([extra_item]))
    assert records[1]["kind"] == "extra_live"


def test_attribute_diffs_present(changed_item):
    records = _parse(render_ndjson([changed_item]))
    diffs = records[1]["attribute_diffs"]
    assert len(diffs) == 1
    assert diffs[0]["attribute"] == "instance_type"
    assert diffs[0]["terraform"] == "t2.micro"
    assert diffs[0]["live"] == "t3.micro"


def test_no_attribute_diffs_key_when_empty(missing_item):
    records = _parse(render_ndjson([missing_item]))
    assert "attribute_diffs" not in records[1]


def test_every_line_is_valid_json(changed_item, missing_item):
    output = render_ndjson([changed_item, missing_item])
    for line in output.strip().splitlines():
        # Should not raise
        json.loads(line)


def test_output_ends_with_newline(changed_item):
    assert render_ndjson([changed_item]).endswith("\n")
