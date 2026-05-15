"""Tests for the OpsGenie reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.opsgenie_reporter import render_opsgenie


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        attribute="instance_type",
        expected="t3.micro",
        actual="t3.small",
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        attribute=None,
        expected=None,
        actual=None,
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_instance.rogue",
        resource_type="aws_instance",
        attribute=None,
        expected=None,
        actual=None,
    )


def test_no_drift_returns_empty_dict():
    assert render_opsgenie([]) == {}


def test_drift_produces_message_key(changed_item):
    payload = render_opsgenie([changed_item])
    assert "message" in payload
    assert "drift" in payload["message"].lower()


def test_missing_live_sets_p1_priority(missing_item):
    payload = render_opsgenie([missing_item])
    assert payload["priority"] == "P1"


def test_changed_only_sets_p2_priority(changed_item):
    payload = render_opsgenie([changed_item])
    assert payload["priority"] == "P2"


def test_extra_only_sets_p3_priority(extra_item):
    payload = render_opsgenie([extra_item])
    assert payload["priority"] == "P3"


def test_missing_overrides_extra_priority(missing_item, extra_item):
    payload = render_opsgenie([extra_item, missing_item])
    assert payload["priority"] == "P1"


def test_tags_include_kind(changed_item):
    payload = render_opsgenie([changed_item])
    assert any("kind:changed" in t for t in payload["tags"])


def test_tags_include_resource_type(changed_item):
    payload = render_opsgenie([changed_item])
    assert any("type:aws_instance" in t for t in payload["tags"])


def test_details_contains_resource_id(changed_item):
    payload = render_opsgenie([changed_item])
    assert any("aws_instance.web" in k for k in payload["details"])


def test_alias_default(changed_item):
    payload = render_opsgenie([changed_item])
    assert payload["alias"] == "drift-check"


def test_alias_custom(changed_item):
    payload = render_opsgenie([changed_item], alias="my-alias")
    assert payload["alias"] == "my-alias"
