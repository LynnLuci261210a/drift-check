"""Tests for drift_check.formatters.table_reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.table_reporter import render_table


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
        resource_id="aws_instance.orphan",
        kind=DriftKind.EXTRA_LIVE,
        diff={},
    )


def test_no_drift_contains_header()	:
    output = render_table([])
    assert "Resource ID" in output
    assert "Kind" in output
    assert "Attribute" in output


def test_no_drift_shows_no_drift_message():
    output = render_table([])
    assert "No drift detected." in output


def test_no_drift_summary_shows_zeros():
    output = render_table([])
    assert "Total: 0" in output
    assert "Changed: 0" in output
    assert "Missing: 0" in output
    assert "Extra: 0" in output


def test_changed_item_shows_resource_id(changed_item):
    output = render_table([changed_item])
    assert "aws_instance.web" in output


def test_changed_item_shows_kind_label(changed_item):
    output = render_table([changed_item])
    assert "CHANGED" in output


def test_changed_item_shows_attribute(changed_item):
    output = render_table([changed_item])
    assert "instance_type" in output


def test_changed_item_shows_expected_and_actual(changed_item):
    output = render_table([changed_item])
    assert "t2.micro" in output
    assert "t3.small" in output


def test_missing_item_shows_missing_label(missing_item):
    output = render_table([missing_item])
    assert "MISSING" in output
    assert "aws_s3_bucket.logs" in output


def test_extra_item_shows_extra_label(extra_item):
    output = render_table([extra_item])
    assert "EXTRA" in output
    assert "aws_instance.orphan" in output


def test_summary_counts_all_kinds(changed_item, missing_item, extra_item):
    output = render_table([changed_item, missing_item, extra_item])
    assert "Total: 3" in output
    assert "Changed: 1" in output
    assert "Missing: 1" in output
    assert "Extra: 1" in output


def test_output_ends_with_newline(changed_item):
    output = render_table([changed_item])
    assert output.endswith("\n")


def test_multiple_diff_attributes_produce_multiple_rows():
    item = DriftItem(
        resource_id="aws_instance.multi",
        kind=DriftKind.CHANGED,
        diff={
            "instance_type": ("t2.micro", "t3.medium"),
            "ami": ("ami-old", "ami-new"),
        },
    )
    output = render_table([item])
    assert output.count("aws_instance.multi") == 2
    assert "instance_type" in output
    assert "ami" in output
