"""Tests for the SARIF reporter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.sarif_reporter import render_sarif


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        attribute_diff={"instance_type": {"terraform": "t2.micro", "live": "t3.small"}},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        attribute_diff=None,
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.orphan",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diff=None,
    )


def _parse(text: str) -> dict:
    return json.loads(text)


def test_no_drift_produces_valid_sarif():
    doc = _parse(render_sarif([]))
    assert doc["version"] == "2.1.0"
    assert len(doc["runs"]) == 1


def test_no_drift_has_empty_results():
    doc = _parse(render_sarif([]))
    assert doc["runs"][0]["results"] == []


def test_tool_name_is_drift_check():
    doc = _parse(render_sarif([]))
    assert doc["runs"][0]["tool"]["driver"]["name"] == "drift-check"


def test_changed_item_level_is_warning(changed_item):
    doc = _parse(render_sarif([changed_item]))
    result = doc["runs"][0]["results"][0]
    assert result["level"] == "warning"


def test_missing_item_level_is_error(missing_item):
    doc = _parse(render_sarif([missing_item]))
    result = doc["runs"][0]["results"][0]
    assert result["level"] == "error"


def test_extra_item_level_is_note(extra_item):
    doc = _parse(render_sarif([extra_item]))
    result = doc["runs"][0]["results"][0]
    assert result["level"] == "note"


def test_changed_message_contains_attribute_diff(changed_item):
    doc = _parse(render_sarif([changed_item]))
    msg = doc["runs"][0]["results"][0]["message"]["text"]
    assert "instance_type" in msg
    assert "t2.micro" in msg
    assert "t3.small" in msg


def test_resource_id_in_logical_location(changed_item):
    doc = _parse(render_sarif([changed_item]))
    loc = doc["runs"][0]["results"][0]["locations"][0]["logicalLocations"][0]
    assert loc["name"] == "aws_instance.web"


def test_rules_deduplicated_by_kind(changed_item, missing_item):
    doc = _parse(render_sarif([changed_item, missing_item]))
    rules = doc["runs"][0]["tool"]["driver"]["rules"]
    rule_ids = [r["id"] for r in rules]
    assert len(rule_ids) == len(set(rule_ids))


def test_multiple_items_produce_multiple_results(changed_item, missing_item, extra_item):
    doc = _parse(render_sarif([changed_item, missing_item, extra_item]))
    assert len(doc["runs"][0]["results"]) == 3
