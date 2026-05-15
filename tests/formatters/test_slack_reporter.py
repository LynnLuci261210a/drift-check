"""Tests for the Slack payload renderer."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.slack_reporter import render_slack


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        attribute_diff={"instance_type": ("t2.micro", "t3.micro")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING,
        resource_id="aws_s3_bucket.logs",
        attribute_diff=None,
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA,
        resource_id="aws_instance.rogue",
        attribute_diff=None,
    )


def _parse(output: str) -> dict:
    return json.loads(output)


def test_no_drift_produces_success_message():
    result = _parse(render_slack([]))
    assert "No infrastructure drift" in result["text"]
    assert "attachments" not in result


def test_no_drift_returns_valid_json():
    raw = render_slack([])
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


def test_drift_count_in_header(changed_item, missing_item):
    result = _parse(render_slack([changed_item, missing_item]))
    assert "2" in result["text"]


def test_changed_item_has_warning_emoji(changed_item):
    result = _parse(render_slack([changed_item]))
    attachment = result["attachments"][0]
    assert ":warning:" in attachment["title"]


def test_missing_item_has_x_emoji(missing_item):
    result = _parse(render_slack([missing_item]))
    attachment = result["attachments"][0]
    assert ":x:" in attachment["title"]


def test_extra_item_has_plus_emoji(extra_item):
    result = _parse(render_slack([extra_item]))
    attachment = result["attachments"][0]
    assert ":heavy_plus_sign:" in attachment["title"]


def test_resource_id_in_attachment_title(changed_item):
    result = _parse(render_slack([changed_item]))
    assert "aws_instance.web" in result["attachments"][0]["title"]


def test_attribute_diff_appears_as_fields(changed_item):
    result = _parse(render_slack([changed_item]))
    fields = result["attachments"][0]["fields"]
    assert len(fields) == 1
    assert fields[0]["title"] == "instance_type"
    assert "t2.micro" in fields[0]["value"]
    assert "t3.micro" in fields[0]["value"]


def test_missing_item_has_no_fields(missing_item):
    result = _parse(render_slack([missing_item]))
    fields = result["attachments"][0]["fields"]
    assert fields == []


def test_changed_attachment_color_is_orange(changed_item):
    result = _parse(render_slack([changed_item]))
    assert result["attachments"][0]["color"] == "#FFA500"


def test_multiple_items_produce_multiple_attachments(changed_item, missing_item, extra_item):
    result = _parse(render_slack([changed_item, missing_item, extra_item]))
    assert len(result["attachments"]) == 3
