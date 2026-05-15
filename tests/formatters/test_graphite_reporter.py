"""Tests for the Graphite plaintext reporter."""
from __future__ import annotations

import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters.graphite_reporter import render_graphite, _sanitize

FIXED_TS = 1_700_000_000


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.CHANGED,
        resource_id="aws_instance.web",
        diff={"instance_type": ("t2.micro", "t3.micro")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.MISSING_LIVE,
        resource_id="aws_s3_bucket.logs",
        diff={},
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        kind=DriftKind.EXTRA_LIVE,
        resource_id="aws_instance.orphan",
        diff={},
    )


def _parse(output: str) -> dict[str, tuple[str, str]]:
    """Return {metric: (value, timestamp)} from Graphite plaintext output."""
    result: dict[str, tuple[str, str]] = {}
    for line in output.strip().splitlines():
        parts = line.split()
        assert len(parts) == 3, f"Unexpected line format: {line!r}"
        result[parts[0]] = (parts[1], parts[2])
    return result


def test_no_drift_summary_totals_are_zero() -> None:
    out = render_graphite([], timestamp=FIXED_TS)
    metrics = _parse(out)
    assert metrics["drift_check.summary.total"] == ("0", str(FIXED_TS))
    assert metrics["drift_check.summary.changed"] == ("0", str(FIXED_TS))
    assert metrics["drift_check.summary.missing"] == ("0", str(FIXED_TS))
    assert metrics["drift_check.summary.extra"] == ("0", str(FIXED_TS))


def test_no_drift_emits_no_resource_metrics() -> None:
    out = render_graphite([], timestamp=FIXED_TS)
    assert ".resources." not in out


def test_summary_counts_are_correct(changed_item, missing_item, extra_item) -> None:
    out = render_graphite([changed_item, missing_item, extra_item], timestamp=FIXED_TS)
    metrics = _parse(out)
    assert metrics["drift_check.summary.total"][0] == "3"
    assert metrics["drift_check.summary.changed"][0] == "1"
    assert metrics["drift_check.summary.missing"][0] == "1"
    assert metrics["drift_check.summary.extra"][0] == "1"


def test_changed_item_emits_drift_kind_1(changed_item) -> None:
    out = render_graphite([changed_item], timestamp=FIXED_TS)
    metrics = _parse(out)
    key = "drift_check.resources.aws_instance.web.drift_kind"
    assert metrics[key][0] == "1"


def test_missing_item_emits_drift_kind_2(missing_item) -> None:
    out = render_graphite([missing_item], timestamp=FIXED_TS)
    metrics = _parse(out)
    key = "drift_check.resources.aws_s3_bucket.logs.drift_kind"
    assert metrics[key][0] == "2"


def test_extra_item_emits_drift_kind_3(extra_item) -> None:
    out = render_graphite([extra_item], timestamp=FIXED_TS)
    metrics = _parse(out)
    key = "drift_check.resources.aws_instance.orphan.drift_kind"
    assert metrics[key][0] == "3"


def test_changed_attributes_count_emitted(changed_item) -> None:
    out = render_graphite([changed_item], timestamp=FIXED_TS)
    metrics = _parse(out)
    key = "drift_check.resources.aws_instance.web.changed_attributes"
    assert metrics[key][0] == "1"


def test_custom_prefix_is_used(changed_item) -> None:
    out = render_graphite([changed_item], prefix="myapp.infra", timestamp=FIXED_TS)
    assert out.startswith("myapp.infra.summary.total")


def test_output_ends_with_newline(changed_item) -> None:
    out = render_graphite([changed_item], timestamp=FIXED_TS)
    assert out.endswith("\n")


def test_sanitize_replaces_slashes() -> None:
    assert "/" not in _sanitize("a/b/c")


def test_sanitize_replaces_spaces() -> None:
    assert " " not in _sanitize("hello world")


def test_timestamp_defaults_to_int(changed_item) -> None:
    out = render_graphite([changed_item])
    metrics = _parse(out)
    ts_str = metrics["drift_check.summary.total"][1]
    assert ts_str.isdigit()
