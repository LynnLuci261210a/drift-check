"""Tests for the SonarQube reporter."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.sonarqube_reporter import render_sonarqube


@pytest.fixture
def changed_item():
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        diff={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture
def missing_item():
    return DriftItem(
        kind=DriftKind.MISSING,
        resource_id="aws_s3_bucket.logs",
        diff={},
    )


@pytest.fixture
def extra_item():
    return DriftItem(
        kind=DriftKind.EXTRA,
        resource_id="aws_instance.orphan",
        diff={},
    )


def _parse(output: str) -> dict:
    return json.loads(output)


def test_no_drift_produces_empty_issues_list():
    result = _parse(render_sonarqube([]))
    assert result["issues"] == []


def test_output_is_valid_json():
    item = DriftItem(kind=DriftKind.CHANGED, resource_id="aws_instance.x", diff={})
    json.loads(render_sonarqube([item]))  # must not raise


def test_changed_item_has_major_severity(changed_item):
    result = _parse(render_sonarqube([changed_item]))
    assert result["issues"][0]["severity"] == "MAJOR"


def test_missing_item_has_critical_severity(missing_item):
    result = _parse(render_sonarqube([missing_item]))
    assert result["issues"][0]["severity"] == "CRITICAL"


def test_extra_item_has_minor_severity(extra_item):
    result = _parse(render_sonarqube([extra_item]))
    assert result["issues"][0]["severity"] == "MINOR"


def test_engine_id_is_drift_check(changed_item):
    result = _parse(render_sonarqube([changed_item]))
    assert result["issues"][0]["engineId"] == "drift-check"


def test_rule_ids_are_distinct(changed_item, missing_item, extra_item):
    result = _parse(render_sonarqube([changed_item, missing_item, extra_item]))
    rule_ids = {issue["ruleId"] for issue in result["issues"]}
    assert len(rule_ids) == 3


def test_changed_message_includes_attribute_name(changed_item):
    result = _parse(render_sonarqube([changed_item]))
    msg = result["issues"][0]["primaryLocation"]["message"]
    assert "instance_type" in msg


def test_missing_message_includes_resource_id(missing_item):
    result = _parse(render_sonarqube([missing_item]))
    msg = result["issues"][0]["primaryLocation"]["message"]
    assert "aws_s3_bucket.logs" in msg


def test_file_path_is_tfstate(changed_item):
    result = _parse(render_sonarqube([changed_item]))
    assert result["issues"][0]["primaryLocation"]["filePath"] == "terraform.tfstate"


def test_type_is_bug(extra_item):
    result = _parse(render_sonarqube([extra_item]))
    assert result["issues"][0]["type"] == "BUG"


def test_multiple_items_produce_multiple_issues(changed_item, missing_item, extra_item):
    result = _parse(render_sonarqube([changed_item, missing_item, extra_item]))
    assert len(result["issues"]) == 3
