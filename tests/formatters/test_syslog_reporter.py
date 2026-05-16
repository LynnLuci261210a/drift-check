"""Tests for drift_check.formatters.syslog_reporter."""
from __future__ import annotations

import re
from typing import List

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.syslog_reporter import render_syslog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="i-abc123",
        resource_type="aws_instance",
        kind=DriftKind.CHANGED,
        diff={"instance_type": {"terraform": "t2.micro", "live": "t3.small"}},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="i-dead",
        resource_type="aws_instance",
        kind=DriftKind.MISSING_LIVE,
        diff=None,
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="bucket-xyz",
        resource_type="aws_s3_bucket",
        kind=DriftKind.EXTRA_LIVE,
        diff=None,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RFC5424_RE = re.compile(
    r"^<\d+>1 \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z - drift-check - - [\w]+ - "
)


def _lines(items) -> List[str]:
    return render_syslog(items).splitlines()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_drift_produces_single_summary_line():
    lines = _lines([])
    assert len(lines) == 1
    assert "SUMMARY" in lines[0]


def test_no_drift_summary_counts_zero():
    line = _lines([])[0]
    assert "total=0" in line
    assert "changed=0" in line
    assert "missing=0" in line
    assert "extra=0" in line


def test_all_lines_match_rfc5424_prefix(changed_item, missing_item, extra_item):
    for line in _lines([changed_item, missing_item, extra_item]):
        assert RFC5424_RE.match(line), f"Line did not match RFC-5424 pattern: {line!r}"


def test_changed_item_uses_warning_severity(changed_item):
    # WARNING -> severity code 4, facility 1 -> PRI = 1*8+4 = 12
    line = _lines([changed_item])[0]
    assert line.startswith("<12>")


def test_missing_item_uses_error_severity(missing_item):
    # ERROR -> severity code 3, facility 1 -> PRI = 11
    line = _lines([missing_item])[0]
    assert line.startswith("<11>")


def test_extra_item_uses_notice_severity(extra_item):
    # NOTICE -> severity code 5, facility 1 -> PRI = 13
    line = _lines([extra_item])[0]
    assert line.startswith("<13>")


def test_changed_item_includes_resource_id(changed_item):
    line = _lines([changed_item])[0]
    assert "i-abc123" in line


def test_changed_item_includes_diff(changed_item):
    line = _lines([changed_item])[0]
    assert "t2.micro" in line
    assert "t3.small" in line


def test_summary_line_is_last(changed_item, missing_item):
    lines = _lines([changed_item, missing_item])
    assert "SUMMARY" in lines[-1]


def test_summary_counts_match_items(changed_item, missing_item, extra_item):
    line = _lines([changed_item, missing_item, extra_item])[-1]
    assert "total=3" in line
    assert "changed=1" in line
    assert "missing=1" in line
    assert "extra=1" in line
