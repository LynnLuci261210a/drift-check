"""Tests for the Prometheus text-format reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.prometheus_reporter import render_prometheus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        attribute_diffs={"instance_type": ("t2.micro", "t3.micro")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id='aws_instance.ghost"server',  # contains a quote for escaping test
        kind=DriftKind.EXTRA_LIVE,
        attribute_diffs={},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_drift_contains_zero_totals() -> None:
    output = render_prometheus([])
    assert 'drift_check_drift_total{kind="changed"} 0' in output
    assert 'drift_check_drift_total{kind="missing_live"} 0' in output
    assert 'drift_check_drift_total{kind="extra_live"} 0' in output


def test_no_drift_emits_no_item_series() -> None:
    output = render_prometheus([])
    assert "drift_check_drift_items" in output
    # No actual series lines for items
    item_lines = [l for l in output.splitlines() if l.startswith("drift_check_drift_items{")]
    assert item_lines == []


def test_no_drift_contains_comment() -> None:
    output = render_prometheus([])
    assert "no drift detected" in output


def test_changed_item_increments_changed_total(changed_item: DriftItem) -> None:
    output = render_prometheus([changed_item])
    assert 'drift_check_drift_total{kind="changed"} 1' in output
    assert 'drift_check_drift_total{kind="missing_live"} 0' in output


def test_changed_item_produces_item_series(changed_item: DriftItem) -> None:
    output = render_prometheus([changed_item])
    assert 'drift_check_drift_items{resource_id="aws_instance.web",kind="changed"} 1' in output


def test_missing_item_series(missing_item: DriftItem) -> None:
    output = render_prometheus([missing_item])
    assert 'drift_check_drift_items{resource_id="aws_s3_bucket.logs",kind="missing_live"} 1' in output


def test_label_value_escaping(extra_item: DriftItem) -> None:
    output = render_prometheus([extra_item])
    # The double-quote in the resource_id must be escaped
    assert '\\"' in output
    assert 'kind="extra_live"' in output


def test_multiple_items_counts(changed_item: DriftItem, missing_item: DriftItem, extra_item: DriftItem) -> None:
    output = render_prometheus([changed_item, missing_item, extra_item])
    assert 'drift_check_drift_total{kind="changed"} 1' in output
    assert 'drift_check_drift_total{kind="missing_live"} 1' in output
    assert 'drift_check_drift_total{kind="extra_live"} 1' in output


def test_output_ends_with_newline(changed_item: DriftItem) -> None:
    output = render_prometheus([changed_item])
    assert output.endswith("\n")


def test_help_and_type_lines_present() -> None:
    output = render_prometheus([])
    assert "# HELP drift_check_drift_total" in output
    assert "# TYPE drift_check_drift_total gauge" in output
    assert "# HELP drift_check_drift_items" in output
    assert "# TYPE drift_check_drift_items gauge" in output
