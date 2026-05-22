"""Tests for the Terraform HCL-style drift reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.terraform_reporter import render_terraform


@pytest.fixture
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        diff={"instance_type": ("t2.micro", "t3.medium"), "tags": ("prod", "staging")},
    )


@pytest.fixture
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        diff={},
    )


@pytest.fixture
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_instance.rogue",
        diff={},
    )


def test_no_drift_produces_no_drift_message() -> None:
    result = render_terraform([])
    assert "No drift detected" in result


def test_no_drift_does_not_contain_block() -> None:
    result = render_terraform([])
    assert "drift {" not in result


def test_changed_item_uses_tilde_symbol(changed_item: DriftItem) -> None:
    result = render_terraform([changed_item])
    assert "~ resource" in result


def test_changed_item_shows_resource_id(changed_item: DriftItem) -> None:
    result = render_terraform([changed_item])
    assert "aws_instance.web" in result


def test_changed_item_shows_old_and_new_values(changed_item: DriftItem) -> None:
    result = render_terraform([changed_item])
    assert "t2.micro" in result
    assert "t3.medium" in result


def test_missing_item_uses_minus_symbol(missing_item: DriftItem) -> None:
    result = render_terraform([missing_item])
    assert "- resource" in result


def test_missing_item_shows_resource_id(missing_item: DriftItem) -> None:
    result = render_terraform([missing_item])
    assert "aws_s3_bucket.logs" in result


def test_extra_item_uses_plus_symbol(extra_item: DriftItem) -> None:
    result = render_terraform([extra_item])
    assert "+ resource" in result


def test_summary_line_includes_counts(changed_item, missing_item, extra_item) -> None:
    result = render_terraform([changed_item, missing_item, extra_item])
    assert "1 changed" in result
    assert "1 missing" in result
    assert "1 extra" in result


def test_output_wrapped_in_drift_block(changed_item: DriftItem) -> None:
    result = render_terraform([changed_item])
    assert result.strip().count("drift {") == 1
    assert "}" in result


def test_multiple_diffs_all_present(changed_item: DriftItem) -> None:
    result = render_terraform([changed_item])
    assert "instance_type" in result
    assert "tags" in result
