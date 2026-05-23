"""Tests for the GitLab Code Quality formatter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.gitlab_reporter import render_gitlab, _fingerprint


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
        attribute_diff={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.orphan",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diff={},
    )


def _parse(output: str) -> list:
    return json.loads(output)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_drift_produces_empty_array():
    result = _parse(render_gitlab([]))
    assert result == []


def test_no_drift_is_valid_json():
    raw = render_gitlab([])
    assert isinstance(json.loads(raw), list)


def test_changed_item_severity_is_major(changed_item):
    issues = _parse(render_gitlab([changed_item]))
    assert issues[0]["severity"] == "major"


def test_missing_item_severity_is_critical(missing_item):
    issues = _parse(render_gitlab([missing_item]))
    assert issues[0]["severity"] == "critical"


def test_extra_item_severity_is_minor(extra_item):
    issues = _parse(render_gitlab([extra_item]))
    assert issues[0]["severity"] == "minor"


def test_description_contains_resource_id(changed_item):
    issues = _parse(render_gitlab([changed_item]))
    assert "aws_instance.web" in issues[0]["description"]


def test_changed_description_includes_attribute_diff(changed_item):
    issues = _parse(render_gitlab([changed_item]))
    desc = issues[0]["description"]
    assert "instance_type" in desc
    assert "t2.micro" in desc
    assert "t3.small" in desc


def test_each_issue_has_fingerprint(changed_item, missing_item, extra_item):
    issues = _parse(render_gitlab([changed_item, missing_item, extra_item]))
    for issue in issues:
        assert "fingerprint" in issue
        assert len(issue["fingerprint"]) == 64  # SHA-256 hex


def test_fingerprints_are_unique(changed_item, missing_item, extra_item):
    issues = _parse(render_gitlab([changed_item, missing_item, extra_item]))
    fingerprints = [i["fingerprint"] for i in issues]
    assert len(fingerprints) == len(set(fingerprints))


def test_fingerprint_is_stable(changed_item):
    fp1 = _fingerprint(changed_item)
    fp2 = _fingerprint(changed_item)
    assert fp1 == fp2


def test_location_path_is_terraform(changed_item):
    issues = _parse(render_gitlab([changed_item]))
    assert issues[0]["location"]["path"] == "terraform"


def test_multiple_items_produce_multiple_issues(changed_item, missing_item, extra_item):
    issues = _parse(render_gitlab([changed_item, missing_item, extra_item]))
    assert len(issues) == 3
