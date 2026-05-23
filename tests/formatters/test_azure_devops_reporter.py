"""Tests for the Azure DevOps logging-commands reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.azure_devops_reporter import (
    _escape,
    _kind_label,
    render_azure_devops,
)


@pytest.fixture
def changed_item():
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff=[("instance_type", "t2.micro", "t3.small")],
    )


@pytest.fixture
def missing_item():
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        diff=[],
    )


@pytest.fixture
def extra_item():
    return DriftItem(
        resource_id="aws_instance.rogue",
        kind=DriftKind.EXTRA_LIVE,
        diff=[],
    )


def _lines(output: str) -> list[str]:
    return output.strip().splitlines()


def test_no_drift_produces_single_complete_line():
    out = render_azure_devops([])
    lines = _lines(out)
    assert len(lines) == 1
    assert lines[0].startswith("##vso[task.complete result=Succeeded]")


def test_no_drift_success_message(  ):
    out = render_azure_devops([])
    assert "No drift detected" in out


def test_changed_item_emits_warning(changed_item):
    out = render_azure_devops([changed_item])
    lines = _lines(out)
    warning_lines = [l for l in lines if "type=warning" in l]
    assert len(warning_lines) == 1
    assert "aws_instance.web" in warning_lines[0]


def test_missing_item_emits_error(missing_item):
    out = render_azure_devops([missing_item])
    lines = _lines(out)
    error_lines = [l for l in lines if "type=error" in l]
    assert len(error_lines) == 1
    assert "aws_s3_bucket.logs" in error_lines[0]


def test_extra_item_emits_warning(extra_item):
    out = render_azure_devops([extra_item])
    lines = _lines(out)
    warning_lines = [l for l in lines if "type=warning" in l]
    assert any("aws_instance.rogue" in l for l in warning_lines)


def test_diff_details_included_in_output(changed_item):
    out = render_azure_devops([changed_item])
    assert "instance_type" in out
    assert "t2.micro" in out
    assert "t3.small" in out


def test_drift_complete_result_is_succeeded_with_issues(changed_item, missing_item):
    out = render_azure_devops([changed_item, missing_item])
    assert "result=SucceededWithIssues" in out


def test_complete_line_is_last(changed_item):
    out = render_azure_devops([changed_item])
    lines = _lines(out)
    assert lines[-1].startswith("##vso[task.complete")


def test_escape_percent():
    assert "%AZP25" in _escape("100% done")


def test_escape_newline():
    assert "%0A" in _escape("line1\nline2")


def test_escape_closing_bracket():
    assert "%5D" in _escape("value]extra")


def test_kind_label_values():
    assert _kind_label(DriftKind.CHANGED) == "changed"
    assert _kind_label(DriftKind.MISSING_LIVE) == "missing_live"
    assert _kind_label(DriftKind.EXTRA_LIVE) == "extra_live"


def test_multiple_items_each_get_a_line(changed_item, missing_item, extra_item):
    out = render_azure_devops([changed_item, missing_item, extra_item])
    issue_lines = [l for l in _lines(out) if "task.logissue" in l]
    assert len(issue_lines) == 3
