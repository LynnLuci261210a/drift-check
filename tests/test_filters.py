"""Tests for drift_check.filters."""
import pytest

from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.filters import FilterOptions, apply_filters


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def changed_ec2() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={"instance_type": ("t2.micro", "t3.micro")},
    )


@pytest.fixture()
def missing_s3() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.assets",
        kind=DriftKind.MISSING_LIVE,
        diff={},
    )


@pytest.fixture()
def extra_ec2() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.bastion",
        kind=DriftKind.MISSING_TF,
        diff={},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_filters_returns_all(changed_ec2, missing_s3, extra_ec2):
    items = [changed_ec2, missing_s3, extra_ec2]
    result = apply_filters(items, FilterOptions())
    assert result == items


def test_filter_by_resource_type_prefix(changed_ec2, missing_s3, extra_ec2):
    result = apply_filters(
        [changed_ec2, missing_s3, extra_ec2],
        FilterOptions(resource_types=["aws_instance"]),
    )
    assert changed_ec2 in result
    assert extra_ec2 in result
    assert missing_s3 not in result


def test_filter_by_kind(changed_ec2, missing_s3, extra_ec2):
    result = apply_filters(
        [changed_ec2, missing_s3, extra_ec2],
        FilterOptions(kinds=[DriftKind.CHANGED]),
    )
    assert result == [changed_ec2]


def test_filter_by_attribute_name_excludes_unrelated_change(changed_ec2, missing_s3):
    result = apply_filters(
        [changed_ec2, missing_s3],
        FilterOptions(attribute_names=["ami"]),
    )
    # changed_ec2 diff touches 'instance_type', not 'ami' — should be excluded.
    assert changed_ec2 not in result
    # missing_s3 is not CHANGED, so attribute filter is a no-op for it.
    assert missing_s3 in result


def test_filter_by_attribute_name_includes_matching_change(changed_ec2):
    result = apply_filters(
        [changed_ec2],
        FilterOptions(attribute_names=["instance_type"]),
    )
    assert result == [changed_ec2]


def test_combined_filters(changed_ec2, missing_s3, extra_ec2):
    result = apply_filters(
        [changed_ec2, missing_s3, extra_ec2],
        FilterOptions(
            resource_types=["aws_instance"],
            kinds=[DriftKind.CHANGED],
            attribute_names=["instance_type"],
        ),
    )
    assert result == [changed_ec2]


def test_empty_input_returns_empty():
    result = apply_filters([], FilterOptions(kinds=[DriftKind.CHANGED]))
    assert result == []
