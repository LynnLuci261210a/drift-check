"""Tests for the core reporter dispatcher."""
from __future__ import annotations

import json

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.reporter import OutputFormat, render_text, render_json, report


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture
def missing_live_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        diff={},
    )


def test_render_text_no_drift():
    assert render_text([]) == "No drift detected.\n"


def test_render_text_shows_resource_id(changed_item):
    out = render_text([changed_item])
    assert "aws_instance.web" in out


def test_render_text_shows_attribute_diff(changed_item):
    out = render_text([changed_item])
    assert "instance_type" in out
    assert "t2.micro" in out
    assert "t3.small" in out


def test_render_text_shows_kind_label(missing_live_item):
    out = render_text([missing_live_item])
    assert "MISSING_LIVE" in out


def test_render_json_no_drift():
    payload = json.loads(render_json([]))
    assert payload == []


def test_render_json_structure(changed_item):
    payload = json.loads(render_json([changed_item]))
    assert len(payload) == 1
    entry = payload[0]
    assert entry["resource_id"] == "aws_instance.web"
    assert entry["kind"] == "CHANGED"
    assert "instance_type" in entry["diff"]


def test_report_dispatches_text(changed_item):
    out = report([changed_item], fmt=OutputFormat.TEXT)
    assert "CHANGED" in out


def test_report_dispatches_json(changed_item):
    out = report([changed_item], fmt=OutputFormat.JSON)
    payload = json.loads(out)
    assert payload[0]["resource_id"] == "aws_instance.web"


def test_report_dispatches_html(changed_item):
    out = report([changed_item], fmt=OutputFormat.HTML)
    assert "<html" in out.lower() or "<!doctype" in out.lower() or "<table" in out.lower()


def test_report_dispatches_csv(changed_item):
    out = report([changed_item], fmt=OutputFormat.CSV)
    assert "resource_id" in out


def test_report_dispatches_markdown(changed_item):
    out = report([changed_item], fmt=OutputFormat.MARKDOWN)
    assert "#" in out


def test_report_dispatches_junit(changed_item):
    out = report([changed_item], fmt=OutputFormat.JUNIT)
    assert "<testsuite" in out
