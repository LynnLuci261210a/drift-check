"""Tests for the Code Climate reporter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.codeclimate_reporter import (
    _fingerprint,
    render_codeclimate,
)


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        attribute_diffs={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_instance.db",
        attribute_diffs={},
    )


@pytest.fixture
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_s3_bucket.logs",
        attribute_diffs={},
    )


def _parse(output: str) -> list:
    return json.loads(output)


def test_no_drift_produces_empty_array():
    result = _parse(render_codeclimate([]))
    assert result == []


def test_no_drift_produces_valid_json():
    output = render_codeclimate([])
    assert json.loads(output) == []


def test_changed_item_has_major_severity(changed_item):
    issues = _parse(render_codeclimate([changed_item]))
    assert issues[0]["severity"] == "major"


def test_missing_item_has_critical_severity(missing_item):
    issues = _parse(render_codeclimate([missing_item]))
    assert issues[0]["severity"] == "critical"


def test_extra_item_has_minor_severity(extra_item):
    issues = _parse(render_codeclimate([extra_item]))
    assert issues[0]["severity"] == "minor"


def test_issue_type_is_issue(changed_item):
    issues = _parse(render_codeclimate([changed_item]))
    assert issues[0]["type"] == "issue"


def test_check_name_contains_kind(changed_item):
    issues = _parse(render_codeclimate([changed_item]))
    assert "changed" in issues[0]["check_name"]


def test_description_contains_resource_id(changed_item):
    issues = _parse(render_codeclimate([changed_item]))
    assert "aws_instance.web" in issues[0]["description"]


def test_changed_description_contains_attribute(changed_item):
    issues = _parse(render_codeclimate([changed_item]))
    assert "instance_type" in issues[0]["description"]


def test_fingerprint_is_stable(changed_item):
    fp1 = _fingerprint(changed_item)
    fp2 = _fingerprint(changed_item)
    assert fp1 == fp2
    assert len(fp1) == 64  # sha256 hex digest


def test_fingerprints_differ_for_different_resources(changed_item, missing_item):
    assert _fingerprint(changed_item) != _fingerprint(missing_item)


def test_location_path_is_terraform(changed_item):
    issues = _parse(render_codeclimate([changed_item]))
    assert issues[0]["location"]["path"] == "terraform"


def test_multiple_items_produce_correct_count(changed_item, missing_item, extra_item):
    issues = _parse(render_codeclimate([changed_item, missing_item, extra_item]))
    assert len(issues) == 3


def test_categories_contains_bug_risk(changed_item):
    issues = _parse(render_codeclimate([changed_item]))
    assert "Bug Risk" in issues[0]["categories"]
