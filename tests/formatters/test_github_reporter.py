"""Tests for the GitHub Actions reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.github_reporter import render_github


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={
            "instance_type": {"terraform": "t3.micro", "live": "t3.small"},
        },
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
        resource_id="aws_instance.ghost",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


class TestNoDrift:
    def test_no_drift_contains_notice_command(self):
        out = render_github([])
        assert "::notice" in out

    def test_no_drift_contains_no_drift_message(self):
        out = render_github([])
        assert "No drift" in out or "no drift" in out.lower()

    def test_no_drift_contains_success_emoji(self):
        out = render_github([])
        assert "✅" in out

    def test_no_drift_has_no_warning_or_error_command(self):
        out = render_github([])
        assert "::warning" not in out
        assert "::error" not in out


class TestWorkflowCommands:
    def test_changed_item_emits_warning_command(self, changed_item):
        out = render_github([changed_item])
        assert "::warning" in out

    def test_missing_item_emits_error_command(self, missing_item):
        out = render_github([missing_item])
        assert "::error" in out

    def test_extra_item_emits_error_command(self, extra_item):
        out = render_github([extra_item])
        assert "::error" in out

    def test_command_contains_resource_id(self, changed_item):
        out = render_github([changed_item])
        assert "aws_instance.web" in out

    def test_command_contains_diff_values(self, changed_item):
        out = render_github([changed_item])
        assert "t3.micro" in out
        assert "t3.small" in out


class TestSummaryTable:
    def test_summary_heading_present(self, changed_item):
        out = render_github([changed_item])
        assert "## Drift Check Results" in out

    def test_table_header_present(self, changed_item):
        out = render_github([changed_item])
        assert "Resource ID" in out
        assert "Kind" in out

    def test_resource_id_in_table(self, changed_item):
        out = render_github([changed_item])
        lines = out.splitlines()
        table_lines = [l for l in lines if "|" in l]
        combined = " ".join(table_lines)
        assert "aws_instance.web" in combined

    def test_multiple_items_all_appear(self, changed_item, missing_item, extra_item):
        out = render_github([changed_item, missing_item, extra_item])
        assert "aws_instance.web" in out
        assert "aws_s3_bucket.logs" in out
        assert "aws_instance.ghost" in out
