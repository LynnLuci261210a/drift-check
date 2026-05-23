"""Tests for drift_check.parsers.aws_state."""

from unittest.mock import MagicMock, patch

import pytest

from drift_check.parsers.aws_state import fetch_live_resources, LiveResource


def _make_session(ec2_instances=None, s3_buckets=None):
    """Build a mock boto3 session.

    Args:
        ec2_instances: List of EC2 instance dicts to return from the paginator.
        s3_buckets: List of S3 bucket dicts to return from list_buckets.

    Returns:
        A MagicMock session whose ``client()`` factory returns pre-configured
        EC2 and S3 client mocks.
    """
    session = MagicMock()

    ec2_client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": ec2_instances or []
                }
            ]
        }
    ]
    ec2_client.get_paginator.return_value = paginator

    s3_client = MagicMock()
    s3_client.list_buckets.return_value = {"Buckets": s3_buckets or []}

    def client_factory(service):
        return ec2_client if service == "ec2" else s3_client

    session.client.side_effect = client_factory
    return session


def test_fetch_ec2_instances():
    session = _make_session(
        ec2_instances=[
            {
                "InstanceId": "i-abc",
                "InstanceType": "t3.micro",
                "ImageId": "ami-123",
                "State": {"Name": "running"},
                "Tags": [{"Key": "Name", "Value": "web"}],
            }
        ]
    )
    resources = fetch_live_resources(session, resource_types=["aws_instance"])
    assert len(resources) == 1
    r = resources[0]
    assert r.resource_type == "aws_instance"
    assert r.resource_id == "i-abc"
    assert r.attributes["instance_type"] == "t3.micro"
    assert r.attributes["tags"] == {"Name": "web"}


def test_fetch_s3_buckets():
    from datetime import datetime
    session = _make_session(
        s3_buckets=[{"Name": "my-bucket", "CreationDate": datetime(2023, 1, 1)}]
    )
    resources = fetch_live_resources(session, resource_types=["aws_s3_bucket"])
    assert len(resources) == 1
    assert resources[0].resource_type == "aws_s3_bucket"
    assert resources[0].resource_id == "my-bucket"


def test_fetch_all_resource_types():
    session = _make_session(
        ec2_instances=[{"InstanceId": "i-1", "InstanceType": "t2.nano", "ImageId": "ami-0", "State": {"Name": "stopped"}, "Tags": []}],
        s3_buckets=[{"Name": "bucket-a", "CreationDate": ""}],
    )
    resources = fetch_live_resources(session)
    types = {r.resource_type for r in resources}
    assert "aws_instance" in types
    assert "aws_s3_bucket" in types


def test_unsupported_type_is_skipped():
    session = _make_session()
    resources = fetch_live_resources(session, resource_types=["aws_lambda_function"])
    assert resources == []


def test_live_resource_equality():
    a = LiveResource(resource_type="aws_instance", resource_id="i-1")
    b = LiveResource(resource_type="aws_instance", resource_id="i-1", attributes={"x": 1})
    assert a == b


def test_fetch_ec2_instances_empty():
    """Fetching EC2 instances when none exist should return an empty list."""
    session = _make_session(ec2_instances=[])
    resources = fetch_live_resources(session, resource_types=["aws_instance"])
    assert resources == []


def test_fetch_s3_buckets_empty():
    """Fetching S3 buckets when none exist should return an empty list."""
    session = _make_session(s3_buckets=[])
    resources = fetch_live_resources(session, resource_types=["aws_s3_bucket"])
    assert resources == []
