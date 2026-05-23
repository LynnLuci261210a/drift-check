"""Tests for the TAP formatter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.tap_reporter import render_tap


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={"instance_type": ("t2.micro", "t3.small")},
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
        resource_id="aws_instance.rogue",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


def _lines(output: str) -> list[str]:
    return output.splitlines()


def test_no_drift_starts_with_tap_version() -> None:
    out = render_tap([])
    assert out.startswith("TAP version 13")


def test_no_drift_plan_is_one() -> None:
    lines = _lines(render_tap([]))
    assert "1..1" in lines


def test_no_drift_single_ok_line() -> None:
    out = render_tap([])
    assert "ok 1 - no configuration drift detected" in out


def test_no_drift_no_not_ok() -> None:
    out = render_tap([])
    assert "not ok" not in out


def test_drift_starts_with_tap_version(changed_item: DriftItem) -> None:
    out = render_tap([changed_item])
    assert out.startswith("TAP version 13")


def test_drift_plan_matches_item_count(changed_item: DriftItem, missing_item: DriftItem) -> None:
    out = render_tap([changed_item, missing_item])
    assert "1..2" in out


def test_changed_item_is_not_ok(changed_item: DriftItem) -> None:
    out = render_tap([changed_item])
    assert "not ok 1 - changed: aws_instance.web" in out


def test_missing_item_kind_label(missing_item: DriftItem) -> None:
    out = render_tap([missing_item])
    assert "missing_live" in out


def test_extra_item_kind_label(extra_item: DriftItem) -> None:
    out = render_tap([extra_item])
    assert "extra_live" in out


def test_changed_item_includes_diff(changed_item: DriftItem) -> None:
    out = render_tap([changed_item])
    assert "instance_type" in out
    assert "t2.micro" in out
    assert "t3.small" in out


def test_diagnostic_block_has_yaml_markers(changed_item: DriftItem) -> None:
    out = render_tap([changed_item])
    assert "  ---" in out
    assert "  ..." in out


def test_output_ends_with_newline(changed_item: DriftItem) -> None:
    assert render_tap([changed_item]).endswith("\n")
    assert render_tap([]).endswith("\n")
