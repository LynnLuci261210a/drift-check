"""Tests for the Excel (XLSX) reporter."""
from __future__ import annotations

import io
import pytest

openpyxl = pytest.importorskip("openpyxl")

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.excel_reporter import render_excel


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        attributes={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING,
        attributes={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.extra",
        kind=DriftKind.EXTRA,
        attributes={},
    )


def _load_wb(raw: bytes):
    return openpyxl.load_workbook(io.BytesIO(raw))


def test_no_drift_produces_valid_xlsx():
    raw = render_excel([])
    wb = _load_wb(raw)
    assert "Drift Report" in wb.sheetnames


def test_no_drift_shows_no_drift_message():
    raw = render_excel([])
    ws = _load_wb(raw).active
    values = [ws.cell(row=2, column=c).value for c in range(1, 6)]
    assert any("No drift" in str(v) for v in values if v)


def test_header_row_contains_expected_columns():
    raw = render_excel([])
    ws = _load_wb(raw).active
    headers = [ws.cell(row=1, column=c).value for c in range(1, 6)]
    assert headers == ["Resource ID", "Kind", "Attribute", "Expected", "Actual"]


def test_changed_item_appears_in_sheet(changed_item):
    raw = render_excel([changed_item])
    ws = _load_wb(raw).active
    cell_values = [[ws.cell(row=r, column=c).value for c in range(1, 6)] for r in range(2, 10)]
    flat = [v for row in cell_values for v in row if v]
    assert "aws_instance.web" in flat
    assert "changed" in flat
    assert "instance_type" in flat
    assert "t2.micro" in flat
    assert "t3.small" in flat


def test_missing_item_kind_label(missing_item):
    raw = render_excel([missing_item])
    ws = _load_wb(raw).active
    row2 = [ws.cell(row=2, column=c).value for c in range(1, 6)]
    assert "missing" in row2


def test_extra_item_kind_label(extra_item):
    raw = render_excel([extra_item])
    ws = _load_wb(raw).active
    row2 = [ws.cell(row=2, column=c).value for c in range(1, 6)]
    assert "extra" in row2


def test_multiple_items_each_on_own_row(changed_item, missing_item, extra_item):
    raw = render_excel([changed_item, missing_item, extra_item])
    ws = _load_wb(raw).active
    resource_ids = [ws.cell(row=r, column=1).value for r in range(2, ws.max_row + 1)]
    resource_ids = [v for v in resource_ids if v]
    assert "aws_instance.web" in resource_ids
    assert "aws_s3_bucket.logs" in resource_ids
    assert "aws_instance.extra" in resource_ids


def test_returns_bytes(changed_item):
    raw = render_excel([changed_item])
    assert isinstance(raw, bytes)
    assert len(raw) > 0
