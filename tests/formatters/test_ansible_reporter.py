"""Tests for the Ansible-format drift reporter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.ansible_reporter import render_ansible


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        diff={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.orphan",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


def _parse(output: str) -> dict:
    return json.loads(output)


def test_no_drift_produces_valid_json():
    output = render_ansible([])
    data = _parse(output)
    assert "plays" in data
    assert "stats" in data


def test_no_drift_stats_all_zero_except_ok():
    data = _parse(render_ansible([]))
    stats = data["stats"]["drift-check"]
    assert stats["changed"] == 0
    assert stats["failures"] == 0
    assert stats["ok"] == 1


def test_no_drift_produces_empty_tasks():
    data = _parse(render_ansible([]))
    assert data["plays"][0]["tasks"] == []


def test_changed_item_appears_in_tasks(changed_item):
    data = _parse(render_ansible([changed_item]))
    tasks = data["plays"][0]["tasks"]
    assert len(tasks) == 1
    host_result = tasks[0]["hosts"]["aws_instance.web"]
    assert host_result["drift_kind"] == "changed"
    assert host_result["failed"] is True


def test_changed_item_includes_diff(changed_item):
    data = _parse(render_ansible([changed_item]))
    host_result = data["plays"][0]["tasks"][0]["hosts"]["aws_instance.web"]
    assert "diff" in host_result
    assert host_result["diff"]["before"]["instance_type"] == "t2.micro"
    assert host_result["diff"]["after"]["instance_type"] == "t3.small"


def test_missing_item_counted_as_failure(missing_item):
    data = _parse(render_ansible([missing_item]))
    assert data["stats"]["drift-check"]["failures"] == 1
    assert data["stats"]["drift-check"]["changed"] == 0


def test_extra_item_counted_as_failure(extra_item):
    data = _parse(render_ansible([extra_item]))
    assert data["stats"]["drift-check"]["failures"] == 1


def test_mixed_items_stats(changed_item, missing_item, extra_item):
    data = _parse(render_ansible([changed_item, missing_item, extra_item]))
    stats = data["stats"]["drift-check"]
    assert stats["changed"] == 1
    assert stats["failures"] == 2
    assert stats["ok"] == 0


def test_task_message_contains_resource_id(changed_item):
    data = _parse(render_ansible([changed_item]))
    host_result = data["plays"][0]["tasks"][0]["hosts"]["aws_instance.web"]
    assert "aws_instance.web" in host_result["msg"]


def test_play_name_is_drift_check():
    data = _parse(render_ansible([]))
    assert data["plays"][0]["play"]["name"] == "drift-check"
