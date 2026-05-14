"""Parser for live AWS infrastructure state using boto3."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LiveResource:
    """Represents a live resource fetched from AWS."""

    resource_type: str
    resource_id: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LiveResource):
            return NotImplemented
        return self.resource_type == other.resource_type and self.resource_id == other.resource_id


class AWSStateError(Exception):
    """Raised when live AWS state cannot be retrieved."""


def _fetch_ec2_instances(client: Any) -> list[LiveResource]:
    resources: list[LiveResource] = []
    try:
        paginator = client.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance.get("InstanceId", "")
                    resources.append(
                        LiveResource(
                            resource_type="aws_instance",
                            resource_id=instance_id,
                            attributes={
                                "instance_type": instance.get("InstanceType"),
                                "ami": instance.get("ImageId"),
                                "state": instance.get("State", {}).get("Name"),
                                "tags": {
                                    t["Key"]: t["Value"]
                                    for t in instance.get("Tags", [])
                                },
                            },
                        )
                    )
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to fetch EC2 instances: %s", exc)
    return resources


def _fetch_s3_buckets(client: Any) -> list[LiveResource]:
    resources: list[LiveResource] = []
    try:
        response = client.list_buckets()
        for bucket in response.get("Buckets", []):
            name = bucket.get("Name", "")
            resources.append(
                LiveResource(
                    resource_type="aws_s3_bucket",
                    resource_id=name,
                    attributes={"bucket": name, "creation_date": str(bucket.get("CreationDate", ""))},
                )
            )
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to fetch S3 buckets: %s", exc)
    return resources


def fetch_live_resources(session: Any, resource_types: list[str] | None = None) -> list[LiveResource]:
    """Fetch live AWS resources for the given resource types.

    Args:
        session: A boto3 Session object.
        resource_types: Optional list of resource types to fetch. Defaults to all supported types.

    Returns:
        List of LiveResource instances.
    """
    supported = {
        "aws_instance": lambda: _fetch_ec2_instances(session.client("ec2")),
        "aws_s3_bucket": lambda: _fetch_s3_buckets(session.client("s3")),
    }
    types_to_fetch = resource_types if resource_types is not None else list(supported.keys())
    results: list[LiveResource] = []
    for rtype in types_to_fetch:
        if rtype not in supported:
            logger.warning("Unsupported resource type: %s — skipping", rtype)
            continue
        results.extend(supported[rtype]())
    return results
