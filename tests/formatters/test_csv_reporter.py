"""Tests for drift_check.formatters.csv_reporter."""
from __future__ import annotations

import csv
import io

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.csv_reporter import render_csv


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        kind=DriftKind.CHANGED,
        attribute_diffs={
            "instance_type": ("t2.micro", "t3.small"),
            "ami": ("ami-abc", "ami-xyz"),
        },
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        kind=DriftKind.MISSING_LIVE,
        attribute_diffs={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.ghost",
        resource_type="aws_instance",
        kind=DriftKind.EXTRA_LIVE,
        attribute_diffs={},
    )


def _parse_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def test_no_items_produces_header_only():
    result = render_csv([])
    rows = _parse_csv(result)
    assert rows == []
    assert result.startswith("resource_id,")


def test_changed_item_expands_to_one_row_per_attribute(changed_item):
    rows = _parse_csv(render_csv([changed_item]))
    assert len(rows) == 2
    attrs = {r["attribute"] for r in rows}
    assert attrs == {"instance_type", "ami"}


def test_changed_item_row_values(changed_item):
    rows = _parse_csv(render_csv([changed_item]))
    by_attr = {r["attribute"]: r for r in rows}
    assert by_attr["instance_type"]["expected"] == "t2.micro"
    assert by_attr["instance_type"]["actual"] == "t3.small"
    assert by_attr["instance_type"]["drift_kind"] == "changed"


def test_missing_item_produces_single_row(missing_item):
    rows = _parse_csv(render_csv([missing_item]))
    assert len(rows) == 1
    assert rows[0]["drift_kind"] == "missing_live"
    assert rows[0]["attribute"] == ""


def test_extra_item_produces_single_row(extra_item):
    rows = _parse_csv(render_csv([extra_item]))
    assert len(rows) == 1
    assert rows[0]["drift_kind"] == "extra_live"


def test_multiple_items_all_present(changed_item, missing_item, extra_item):
    rows = _parse_csv(render_csv([changed_item, missing_item, extra_item]))
    # 2 attribute rows + 1 missing + 1 extra
    assert len(rows) == 4
    resource_ids = {r["resource_id"] for r in rows}
    assert "aws_instance.web" in resource_ids
    assert "aws_s3_bucket.logs" in resource_ids
    assert "aws_instance.ghost" in resource_ids
