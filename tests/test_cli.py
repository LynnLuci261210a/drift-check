"""Tests for the drift_check CLI entry-point."""

import json
import pytest
from unittest.mock import patch, MagicMock

from drift_check.cli import main, build_parser
from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.parsers.terraform_state import TerraformResource
from drift_check.parsers.aws_state import LiveResource, AWSStateError


STATE_FILE = "terraform.tfstate"


@pytest.fixture()
def tf_resource():
    return TerraformResource(
        resource_type="aws_instance",
        name="web",
        provider="aws",
        attributes={"instance_type": "t3.micro", "id": "i-abc123"},
    )


@pytest.fixture()
def live_resource():
    return LiveResource(
        resource_type="aws_instance",
        resource_id="i-abc123",
        attributes={"instance_type": "t3.micro"},
    )


def _patch_deps(tf_resources, live_resources, drift_items):
    """Return a context-manager stack that patches all I/O."""
    return (
        patch("drift_check.cli.parse_state_file", return_value=tf_resources),
        patch("drift_check.cli.fetch_live_resources", return_value=live_resources),
        patch("drift_check.cli.detect_drift", return_value=drift_items),
        patch("drift_check.cli.boto3.Session", return_value=MagicMock()),
    )


def test_no_drift_exits_zero(tf_resource, live_resource, capsys):
    with patch("drift_check.cli.parse_state_file", return_value=[tf_resource]), \
         patch("drift_check.cli.fetch_live_resources", return_value=[live_resource]), \
         patch("drift_check.cli.detect_drift", return_value=[]), \
         patch("drift_check.cli.boto3.Session", return_value=MagicMock()):
        rc = main([STATE_FILE])
    assert rc == 0


def test_drift_with_exit_code_flag_exits_one(tf_resource, live_resource):
    drift = [DriftItem(DriftKind.CHANGED, "aws_instance.web", "instance_type", "t3.micro", "t3.small")]
    with patch("drift_check.cli.parse_state_file", return_value=[tf_resource]), \
         patch("drift_check.cli.fetch_live_resources", return_value=[live_resource]), \
         patch("drift_check.cli.detect_drift", return_value=drift), \
         patch("drift_check.cli.boto3.Session", return_value=MagicMock()):
        rc = main([STATE_FILE, "--exit-code"])
    assert rc == 1


def test_drift_without_exit_code_flag_exits_zero(tf_resource, live_resource):
    drift = [DriftItem(DriftKind.CHANGED, "aws_instance.web", "instance_type", "t3.micro", "t3.small")]
    with patch("drift_check.cli.parse_state_file", return_value=[tf_resource]), \
         patch("drift_check.cli.fetch_live_resources", return_value=[live_resource]), \
         patch("drift_check.cli.detect_drift", return_value=drift), \
         patch("drift_check.cli.boto3.Session", return_value=MagicMock()):
        rc = main([STATE_FILE])
    assert rc == 0


def test_missing_state_file_exits_two():
    with patch("drift_check.cli.parse_state_file", side_effect=FileNotFoundError("not found")):
        rc = main([STATE_FILE])
    assert rc == 2


def test_aws_error_exits_two(tf_resource):
    with patch("drift_check.cli.parse_state_file", return_value=[tf_resource]), \
         patch("drift_check.cli.fetch_live_resources", side_effect=AWSStateError("denied")), \
         patch("drift_check.cli.boto3.Session", return_value=MagicMock()):
        rc = main([STATE_FILE])
    assert rc == 2


def test_json_format_output(tf_resource, live_resource, capsys):
    with patch("drift_check.cli.parse_state_file", return_value=[tf_resource]), \
         patch("drift_check.cli.fetch_live_resources", return_value=[live_resource]), \
         patch("drift_check.cli.detect_drift", return_value=[]), \
         patch("drift_check.cli.boto3.Session", return_value=MagicMock()):
        main([STATE_FILE, "--format", "json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "drift" in parsed


def test_region_and_profile_forwarded_to_session(tf_resource, live_resource):
    mock_session_cls = MagicMock()
    with patch("drift_check.cli.parse_state_file", return_value=[tf_resource]), \
         patch("drift_check.cli.fetch_live_resources", return_value=[live_resource]), \
         patch("drift_check.cli.detect_drift", return_value=[]), \
         patch("drift_check.cli.boto3.Session", mock_session_cls):
        main([STATE_FILE, "--region", "us-west-2", "--profile", "dev"])
    mock_session_cls.assert_called_once_with(region_name="us-west-2", profile_name="dev")
