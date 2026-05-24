"""Tests for drift_check.formatters.console_reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.console_reporter import render_console


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        attribute="instance_type",
        expected="t3.micro",
        actual="t3.small",
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        attribute=None,
        expected=None,
        actual=None,
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_instance.ghost",
        attribute=None,
        expected=None,
        actual=None,
    )


# ---------------------------------------------------------------------------
# No-drift cases
# ---------------------------------------------------------------------------

def test_no_drift_contains_success_message() -> None:
    result = render_console([], colour=False)
    assert "No drift detected" in result


def test_no_drift_with_colour_contains_success_message() -> None:
    result = render_console([], colour=True)
    assert "No drift detected" in result


def test_no_drift_does_not_contain_summary_line() -> None:
    result = render_console([], colour=False)
    assert "Summary:" not in result


# ---------------------------------------------------------------------------
# Drift present – plain text (colour=False)
# ---------------------------------------------------------------------------

def test_changed_item_label_present(changed_item: DriftItem) -> None:
    result = render_console([changed_item], colour=False)
    assert "[CHANGED]" in result


def test_changed_item_resource_id_present(changed_item: DriftItem) -> None:
    result = render_console([changed_item], colour=False)
    assert "aws_instance.web" in result


def test_changed_item_attribute_present(changed_item: DriftItem) -> None:
    result = render_console([changed_item], colour=False)
    assert "instance_type" in result


def test_changed_item_expected_and_actual(changed_item: DriftItem) -> None:
    result = render_console([changed_item], colour=False)
    assert "t3.micro" in result
    assert "t3.small" in result


def test_missing_item_label(missing_item: DriftItem) -> None:
    result = render_console([missing_item], colour=False)
    assert "[MISSING]" in result


def test_extra_item_label(extra_item: DriftItem) -> None:
    result = render_console([extra_item], colour=False)
    assert "[EXTRA]" in result


# ---------------------------------------------------------------------------
# Summary line
# ---------------------------------------------------------------------------

def test_summary_counts(
    changed_item: DriftItem,
    missing_item: DriftItem,
    extra_item: DriftItem,
) -> None:
    result = render_console(
        [changed_item, missing_item, extra_item], colour=False
    )
    assert "1 changed" in result
    assert "1 missing" in result
    assert "1 extra" in result


def test_summary_zero_counts(changed_item: DriftItem) -> None:
    result = render_console([changed_item], colour=False)
    assert "0 missing" in result
    assert "0 extra" in result


# ---------------------------------------------------------------------------
# Colour mode does not break output
# ---------------------------------------------------------------------------

def test_colour_output_still_contains_resource_id(changed_item: DriftItem) -> None:
    result = render_console([changed_item], colour=True)
    assert "aws_instance.web" in result


def test_output_ends_with_newline(changed_item: DriftItem) -> None:
    result = render_console([changed_item], colour=False)
    assert result.endswith("\n")
