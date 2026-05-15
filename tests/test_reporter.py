"""Tests for drift_check.reporter."""

from __future__ import annotations

import io
import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.reporter import OutputFormat, render_json, render_text, report


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        attribute="instance_type",
        expected="t3.micro",
        actual="t3.small",
    )


@pytest.fixture()
def missing_live_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.assets",
        kind=DriftKind.MISSING_LIVE,
    )


def test_render_text_no_drift():
    out = io.StringIO()
    render_text([], out)
    assert "No drift detected" in out.getvalue()


def test_render_text_shows_resource_id(changed_item):
    out = io.StringIO()
    render_text([changed_item], out)
    text = out.getvalue()
    assert "aws_instance.web" in text
    assert "CHANGED" in text


def test_render_text_shows_attribute_diff(changed_item):
    out = io.StringIO()
    render_text([changed_item], out)
    text = out.getvalue()
    assert "t3.micro" in text
    assert "t3.small" in text


def test_render_text_missing_live_label(missing_live_item):
    out = io.StringIO()
    render_text([missing_live_item], out)
    assert "MISSING (live)" in out.getvalue()


def test_render_json_structure(changed_item, missing_live_item):
    out = io.StringIO()
    render_json([changed_item, missing_live_item], out)
    data = json.loads(out.getvalue())
    assert data["drift_count"] == 2
    assert len(data["items"]) == 2
    first = data["items"][0]
    assert first["resource_id"] == "aws_instance.web"
    assert first["kind"] == DriftKind.CHANGED.value
    assert first["attribute"] == "instance_type"


def test_report_returns_zero_when_clean():
    out = io.StringIO()
    code = report([], fmt=OutputFormat.TEXT, out=out)
    assert code == 0


def test_report_returns_one_when_drift(changed_item):
    out = io.StringIO()
    code = report([changed_item], fmt=OutputFormat.TEXT, out=out)
    assert code == 1


def test_report_json_format(changed_item):
    out = io.StringIO()
    report([changed_item], fmt=OutputFormat.JSON, out=out)
    data = json.loads(out.getvalue())
    assert "drift_count" in data
