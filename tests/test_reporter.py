"""Tests for the core reporter module."""
import json
from io import StringIO

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.reporter import OutputFormat, render_json, render_text, report


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.app",
        resource_type="aws_instance",
        kind=DriftKind.CHANGED,
        attribute_diffs={"ami": ("ami-old", "ami-new")},
    )


@pytest.fixture
def missing_live_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.data",
        resource_type="aws_s3_bucket",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs={},
    )


def test_render_text_no_drift():
    assert "No drift" in render_text([])


def test_render_text_shows_resource_id(changed_item):
    assert "aws_instance.app" in render_text([changed_item])


def test_render_text_shows_attribute_diff(changed_item):
    result = render_text([changed_item])
    assert "ami-old" in result
    assert "ami-new" in result


def test_render_text_shows_item_count(changed_item, missing_live_item):
    result = render_text([changed_item, missing_live_item])
    assert "2 drift item(s)" in result


def test_render_json_no_drift():
    result = render_json([])
    assert json.loads(result) == []


def test_render_json_structure(changed_item):
    data = json.loads(render_json([changed_item]))
    assert len(data) == 1
    assert data[0]["resource_id"] == "aws_instance.app"
    assert data[0]["kind"] == DriftKind.CHANGED.value
    assert "ami" in data[0]["attribute_diffs"]


def test_report_text_writes_to_stream(changed_item):
    buf = StringIO()
    report([changed_item], fmt=OutputFormat.TEXT, out=buf)
    assert "aws_instance.app" in buf.getvalue()


def test_report_json_writes_valid_json(changed_item):
    buf = StringIO()
    report([changed_item], fmt=OutputFormat.JSON, out=buf)
    data = json.loads(buf.getvalue())
    assert isinstance(data, list)


def test_report_markdown_format(changed_item):
    buf = StringIO()
    report([changed_item], fmt=OutputFormat.MARKDOWN, out=buf)
    assert "# Drift Report" in buf.getvalue()


def test_report_csv_format_has_header(changed_item):
    buf = StringIO()
    report([changed_item], fmt=OutputFormat.CSV, out=buf)
    assert "resource_id" in buf.getvalue()
