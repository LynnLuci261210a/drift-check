"""Tests for drift_check.formatters.dotenv_reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.dotenv_reporter import render_dotenv, _sanitize_key


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
        resource_id="aws_instance.orphan",
        attribute=None,
        expected=None,
        actual=None,
    )


def _parse(output: str) -> dict[str, str]:
    """Parse KEY=value lines into a dict, ignoring comment lines."""
    result: dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        result[key] = value
    return result


class TestNoDrift:
    def test_no_drift_total_is_zero(self):
        out = render_dotenv([])
        data = _parse(out)
        assert data["DRIFT_TOTAL"] == "0"

    def test_no_drift_all_counts_zero(self):
        data = _parse(render_dotenv([]))
        assert data["DRIFT_CHANGED"] == "0"
        assert data["DRIFT_MISSING_LIVE"] == "0"
        assert data["DRIFT_EXTRA_LIVE"] == "0"

    def test_no_drift_produces_no_item_lines(self):
        out = render_dotenv([])
        assert "_INDEX=" not in out

    def test_output_ends_with_newline(self):
        assert render_dotenv([]).endswith("\n")


class TestWithItems:
    def test_total_reflects_item_count(self, changed_item, missing_item):
        data = _parse(render_dotenv([changed_item, missing_item]))
        assert data["DRIFT_TOTAL"] == "2"

    def test_changed_count_incremented(self, changed_item):
        data = _parse(render_dotenv([changed_item]))
        assert data["DRIFT_CHANGED"] == "1"
        assert data["DRIFT_MISSING_LIVE"] == "0"

    def test_missing_live_count_incremented(self, missing_item):
        data = _parse(render_dotenv([missing_item]))
        assert data["DRIFT_MISSING_LIVE"] == "1"

    def test_extra_live_count_incremented(self, extra_item):
        data = _parse(render_dotenv([extra_item]))
        assert data["DRIFT_EXTRA_LIVE"] == "1"

    def test_changed_item_attribute_present(self, changed_item):
        data = _parse(render_dotenv([changed_item]))
        key_prefix = "DRIFT_CHANGED_AWS_INSTANCE_WEB"
        assert data[f"{key_prefix}_ATTRIBUTE"] == "instance_type"
        assert data[f"{key_prefix}_EXPECTED"] == "t3.micro"
        assert data[f"{key_prefix}_ACTUAL"] == "t3.small"

    def test_missing_item_omits_attribute_line(self, missing_item):
        out = render_dotenv([missing_item])
        assert "_ATTRIBUTE=" not in out

    def test_item_index_is_sequential(self, changed_item, extra_item):
        data = _parse(render_dotenv([changed_item, extra_item]))
        safe_changed = "DRIFT_CHANGED_AWS_INSTANCE_WEB_INDEX"
        safe_extra = "DRIFT_EXTRA_LIVE_AWS_INSTANCE_ORPHAN_INDEX"
        assert data[safe_changed] == "0"
        assert data[safe_extra] == "1"

    def test_kind_value_written(self, missing_item):
        data = _parse(render_dotenv([missing_item]))
        assert data["DRIFT_MISSING_LIVE_AWS_S3_BUCKET_LOGS_KIND"] == "missing_live"


class TestSanitizeKey:
    def test_dots_replaced(self):
        assert "." not in _sanitize_key("aws_instance.web")

    def test_result_is_uppercase(self):
        result = _sanitize_key("aws_instance.web")
        assert result == result.upper()

    def test_alphanumeric_preserved(self):
        assert _sanitize_key("abc123") == "ABC123"
