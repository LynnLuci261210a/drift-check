"""Tests for drift_check.drift_detector."""

import pytest

from drift_check.parsers.terraform_state import TerraformResource
from drift_check.parsers.aws_state import LiveResource
from drift_check.drift_detector import detect_drift, DriftKind, DriftItem


@pytest.fixture
def tf_instance() -> TerraformResource:
    return TerraformResource(
        resource_type="aws_instance",
        resource_id="i-abc123",
        attributes={"instance_type": "t3.micro", "ami": "ami-0abcdef"},
    )


@pytest.fixture
def live_instance_matching() -> LiveResource:
    return LiveResource(
        resource_type="aws_instance",
        resource_id="i-abc123",
        attributes={"instance_type": "t3.micro", "ami": "ami-0abcdef", "state": "running"},
    )


@pytest.fixture
def live_instance_changed() -> LiveResource:
    return LiveResource(
        resource_type="aws_instance",
        resource_id="i-abc123",
        attributes={"instance_type": "t3.large", "ami": "ami-0abcdef", "state": "running"},
    )


def test_no_drift_when_attributes_match(tf_instance, live_instance_matching):
    result = detect_drift([tf_instance], [live_instance_matching], ignore_keys=["state"])
    assert result == []


def test_detects_changed_attribute(tf_instance, live_instance_changed):
    result = detect_drift([tf_instance], [live_instance_changed], ignore_keys=["state"])
    assert len(result) == 1
    item = result[0]
    assert item.kind == DriftKind.CHANGED
    assert item.resource_id == "i-abc123"
    assert "instance_type" in item.details
    assert item.details["instance_type"]["terraform"] == "t3.micro"
    assert item.details["instance_type"]["live"] == "t3.large"


def test_detects_missing_resource(tf_instance):
    result = detect_drift([tf_instance], [])
    assert len(result) == 1
    assert result[0].kind == DriftKind.MISSING
    assert result[0].resource_id == "i-abc123"


def test_detects_unexpected_resource(live_instance_matching):
    result = detect_drift([], [live_instance_matching])
    assert len(result) == 1
    assert result[0].kind == DriftKind.UNEXPECTED
    assert result[0].resource_id == "i-abc123"


def test_ignore_keys_excludes_attribute(tf_instance):
    live = LiveResource(
        resource_type="aws_instance",
        resource_id="i-abc123",
        attributes={"instance_type": "t3.micro", "ami": "ami-NEW"},
    )
    result = detect_drift([tf_instance], [live], ignore_keys=["ami"])
    assert result == []


def test_summary_format():
    item = DriftItem(kind=DriftKind.CHANGED, resource_type="aws_instance", resource_id="i-xyz")
    assert item.summary() == "[CHANGED] aws_instance.i-xyz"


def test_multiple_resources_mixed_drift(tf_instance):
    extra_live = LiveResource(
        resource_type="aws_s3_bucket",
        resource_id="my-bucket",
        attributes={"bucket": "my-bucket"},
    )
    result = detect_drift([tf_instance], [extra_live])
    kinds = {item.kind for item in result}
    assert DriftKind.MISSING in kinds
    assert DriftKind.UNEXPECTED in kinds
