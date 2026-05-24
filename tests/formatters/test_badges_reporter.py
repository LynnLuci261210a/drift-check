"""Tests for the Shields.io badge reporter."""
import json
import pytest
from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.badges_reporter import render_badges, _choose_colour, _label_text


@pytest.fixture()
def changed_item():
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={"instance_type": {"terraform": "t2.micro", "live": "t3.small"}},
    )


@pytest.fixture()
def missing_item():
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        diff={},
    )


@pytest.fixture()
def extra_item():
    return DriftItem(
        resource_id="aws_instance.orphan",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


def _parse(output: str) -> dict:
    return json.loads(output)


def test_no_drift_produces_valid_json():
    out = render_badges([])
    data = _parse(out)
    assert isinstance(data, dict)


def test_no_drift_schema_version():
    data = _parse(render_badges([]))
    assert data["schemaVersion"] == 1


def test_no_drift_label_is_drift():
    data = _parse(render_badges([]))
    assert data["label"] == "drift"


def test_no_drift_message_is_in_sync():
    data = _parse(render_badges([]))
    assert data["message"] == "in sync"


def test_no_drift_colour_is_brightgreen():
    data = _parse(render_badges([]))
    assert data["color"] == "brightgreen"


def test_changed_only_colour_is_orange(changed_item):
    assert _choose_colour([changed_item]) == "orange"


def test_missing_colour_is_red(missing_item):
    assert _choose_colour([missing_item]) == "red"


def test_extra_only_colour_is_yellow(extra_item):
    assert _choose_colour([extra_item]) == "yellow"


def test_changed_label_text(changed_item):
    assert "changed" in _label_text([changed_item])


def test_missing_label_text(missing_item):
    assert "missing" in _label_text([missing_item])


def test_extra_label_text(extra_item):
    assert "extra" in _label_text([extra_item])


def test_multiple_kinds_label_text(changed_item, missing_item):
    text = _label_text([changed_item, missing_item])
    assert "changed" in text
    assert "missing" in text


def test_render_output_contains_message_key(changed_item):
    data = _parse(render_badges([changed_item]))
    assert "message" in data
    assert "color" in data
