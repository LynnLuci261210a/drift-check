"""Tests for the YAML reporter formatter."""
from __future__ import annotations

import pytest

try:
    import yaml
except ImportError:  # pragma: no cover
    pytest.skip("PyYAML not installed", allow_module_level=True)

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.yaml_reporter import render_yaml


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        attribute_diffs=[("instance_type", "t2.micro", "t3.micro")],
    )


@pytest.fixture
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs=[],
    )


@pytest.fixture
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.ghost",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diffs=[],
    )


def _parse(text: str) -> dict:
    return yaml.safe_load(text)


def test_no_drift_produces_valid_yaml():
    result = _parse(render_yaml([]))
    assert isinstance(result, dict)


def test_no_drift_flag_is_false():
    result = _parse(render_yaml([]))
    assert result["drift_detected"] is False


def test_no_drift_total_is_zero():
    result = _parse(render_yaml([]))
    assert result["total"] == 0


def test_no_drift_items_is_empty_list():
    result = _parse(render_yaml([]))
    assert result["items"] == []


def test_drift_detected_flag_is_true(changed_item):
    result = _parse(render_yaml([changed_item]))
    assert result["drift_detected"] is True


def test_total_reflects_item_count(changed_item, missing_item, extra_item):
    result = _parse(render_yaml([changed_item, missing_item, extra_item]))
    assert result["total"] == 3


def test_changed_item_kind_label(changed_item):
    result = _parse(render_yaml([changed_item]))
    assert result["items"][0]["kind"] == "changed"


def test_missing_item_kind_label(missing_item):
    result = _parse(render_yaml([missing_item]))
    assert result["items"][0]["kind"] == "missing_live"


def test_extra_item_kind_label(extra_item):
    result = _parse(render_yaml([extra_item]))
    assert result["items"][0]["kind"] == "extra_live"


def test_attribute_diffs_present(changed_item):
    result = _parse(render_yaml([changed_item]))
    diffs = result["items"][0]["attribute_diffs"]
    assert len(diffs) == 1
    assert diffs[0]["attribute"] == "instance_type"
    assert diffs[0]["terraform"] == "t2.micro"
    assert diffs[0]["live"] == "t3.micro"


def test_no_attribute_diffs_key_when_empty(missing_item):
    result = _parse(render_yaml([missing_item]))
    assert "attribute_diffs" not in result["items"][0]


def test_resource_id_preserved(changed_item):
    result = _parse(render_yaml([changed_item]))
    assert result["items"][0]["resource_id"] == "aws_instance.web"
