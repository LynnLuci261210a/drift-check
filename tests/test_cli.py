"""Tests for the CLI, including the SARIF output path."""
from __future__ import annotations

import json
from contextlib import contextmanager
from typing import List
from unittest.mock import patch, MagicMock

import pytest

from drift_check.cli import build_parser, main
from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.parsers.terraform_state import TerraformResource
from drift_check.parsers.aws_state import LiveResource


@pytest.fixture()
def tf_resource() -> TerraformResource:
    return TerraformResource(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        attributes={"instance_type": "t2.micro", "ami": "ami-123"},
    )


@pytest.fixture()
def live_resource() -> LiveResource:
    return LiveResource(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        attributes={"instance_type": "t2.micro", "ami": "ami-123"},
    )


@contextmanager
def _patch_deps(tf_resources, live_resources):
    with patch("drift_check.cli.parse_state_file", return_value=tf_resources), \
         patch("drift_check.cli.fetch_live_resources", return_value=live_resources):
        yield


def test_no_drift_exits_zero(tf_resource, live_resource, capsys):
    with _patch_deps([tf_resource], [live_resource]):
        code = main(["fake.tfstate", "--exit-code"])
    assert code == 0


def test_drift_with_exit_code_flag_exits_one(tf_resource, capsys):
    changed = LiveResource(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        attributes={"instance_type": "t3.large", "ami": "ami-123"},
    )
    with _patch_deps([tf_resource], [changed]):
        code = main(["fake.tfstate", "--exit-code"])
    assert code == 1


def test_drift_without_exit_code_flag_exits_zero(tf_resource, capsys):
    changed = LiveResource(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        attributes={"instance_type": "t3.large", "ami": "ami-123"},
    )
    with _patch_deps([tf_resource], [changed]):
        code = main(["fake.tfstate"])
    assert code == 0


def test_sarif_format_outputs_valid_json(tf_resource, capsys):
    changed = LiveResource(
        resource_id="aws_instance.web",
        resource_type="aws_instance",
        attributes={"instance_type": "t3.large", "ami": "ami-123"},
    )
    with _patch_deps([tf_resource], [changed]):
        main(["fake.tfstate", "--format", "sarif"])
    captured = capsys.readouterr()
    doc = json.loads(captured.out)
    assert doc["version"] == "2.1.0"


def test_sarif_format_no_drift_empty_results(tf_resource, live_resource, capsys):
    with _patch_deps([tf_resource], [live_resource]):
        main(["fake.tfstate", "--format", "sarif"])
    captured = capsys.readouterr()
    doc = json.loads(captured.out)
    assert doc["runs"][0]["results"] == []


def test_build_parser_includes_sarif_format():
    parser = build_parser()
    args = parser.parse_args(["state.tfstate", "--format", "sarif"])
    assert args.format == "sarif"


def test_resource_type_filter_passed_through(tf_resource, live_resource, capsys):
    with _patch_deps([tf_resource], [live_resource]):
        code = main(["fake.tfstate", "--resource-type", "aws_instance"])
    assert code == 0
