"""Tests for the TeamCity service-message formatter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.teamcity_reporter import render_teamcity, _escape


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
    return [l for l in output.splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# _escape helper
# ---------------------------------------------------------------------------

def test_escape_pipe():
    assert _escape("a|b") == "a||b"


def test_escape_newline():
    assert _escape("a\nb") == "a|nb"


def test_escape_brackets():
    assert _escape("[x]") == "|[x|]"


# ---------------------------------------------------------------------------
# No-drift output
# ---------------------------------------------------------------------------

def test_no_drift_has_suite_start_and_finish():
    out = render_teamcity([])
    assert "testSuiteStarted" in out
    assert "testSuiteFinished" in out


def test_no_drift_emits_passing_test():
    out = render_teamcity([])
    assert "testStarted name='drift.no_drift'" in out
    assert "testFinished name='drift.no_drift'" in out
    assert "testFailed" not in out


# ---------------------------------------------------------------------------
# Drift output
# ---------------------------------------------------------------------------

def test_changed_item_emits_test_failed(changed_item):
    out = render_teamcity([changed_item])
    assert "testFailed" in out
    assert "drift.changed.aws_instance.web" in out


def test_changed_item_includes_diff_details(changed_item):
    out = render_teamcity([changed_item])
    assert "instance_type" in out
    assert "t2.micro" in out
    assert "t3.small" in out


def test_missing_item_emits_test_failed(missing_item):
    out = render_teamcity([missing_item])
    assert "testFailed" in out
    assert "drift.missing_live.aws_s3_bucket.logs" in out


def test_extra_item_emits_test_failed(extra_item):
    out = render_teamcity([extra_item])
    assert "testFailed" in out
    assert "drift.extra_live.aws_instance.rogue" in out


def test_multiple_items_each_get_start_and_finish(changed_item, missing_item):
    out = render_teamcity([changed_item, missing_item])
    assert out.count("testStarted") == 2
    assert out.count("testFinished") == 2
    assert out.count("testFailed") == 2


def test_suite_name_is_drift_check():
    out = render_teamcity([])
    assert "name='drift-check'" in out


def test_output_ends_with_newline(changed_item):
    out = render_teamcity([changed_item])
    assert out.endswith("\n")
