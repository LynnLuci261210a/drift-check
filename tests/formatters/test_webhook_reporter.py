"""Tests for drift_check.formatters.webhook_reporter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.webhook_reporter import render_webhook


@pytest.fixture()
def changed_item():
    return DriftItem(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        kind=DriftKind.CHANGED,
        attribute_diffs=[("instance_type", "t2.micro", "t3.small")],
    )


@pytest.fixture()
def missing_item():
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs=[],
    )


@pytest.fixture()
def extra_item():
    return DriftItem(
        resource_id="aws_instance.rogue",
        resource_type="aws_instance",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diffs=[],
    )


def _parse(text: str) -> dict:
    return json.loads(text)


def test_no_drift_has_zero_totals():
    data = _parse(render_webhook([]))
    assert data["summary"]["total"] == 0
    assert data["summary"]["changed"] == 0
    assert data["summary"]["missing_live"] == 0
    assert data["summary"]["extra_live"] == 0


def test_no_drift_has_drift_false():
    data = _parse(render_webhook([]))
    assert data["summary"]["has_drift"] is False


def test_no_drift_produces_empty_items_list():
    data = _parse(render_webhook([]))
    assert data["drift_items"] == []


def test_envelope_contains_source(changed_item):
    data = _parse(render_webhook([changed_item], source="my-pipeline"))
    assert data["source"] == "my-pipeline"


def test_envelope_contains_timestamp(changed_item):
    data = _parse(render_webhook([changed_item]))
    ts = data["timestamp"]
    assert ts.endswith("Z")
    assert "T" in ts


def test_changed_item_kind_label(changed_item):
    data = _parse(render_webhook([changed_item]))
    assert data["drift_items"][0]["kind"] == "changed"


def test_changed_item_attribute_diffs(changed_item):
    data = _parse(render_webhook([changed_item]))
    diffs = data["drift_items"][0]["attribute_diffs"]
    assert len(diffs) == 1
    assert diffs[0]["attribute"] == "instance_type"
    assert diffs[0]["terraform"] == "t2.micro"
    assert diffs[0]["live"] == "t3.small"


def test_missing_item_has_no_attribute_diffs_key(missing_item):
    data = _parse(render_webhook([missing_item]))
    assert "attribute_diffs" not in data["drift_items"][0]


def test_summary_counts_multiple_kinds(changed_item, missing_item, extra_item):
    data = _parse(render_webhook([changed_item, missing_item, extra_item]))
    s = data["summary"]
    assert s["total"] == 3
    assert s["changed"] == 1
    assert s["missing_live"] == 1
    assert s["extra_live"] == 1
    assert s["has_drift"] is True


def test_default_source_is_drift_check():
    data = _parse(render_webhook([]))
    assert data["source"] == "drift-check"


def test_compact_output_with_no_indent():
    text = render_webhook([])
    assert "\n" not in text.strip()


def test_changed_item_includes_resource_id_and_type(changed_item):
    data = _parse(render_webhook([changed_item]))
    item = data["drift_items"][0]
    assert item["resource_id"] == "aws_instance.web"
    assert item["resource_type"] == "aws_instance"
