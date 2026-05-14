"""Tests for the Terraform state file parser."""

import json
import pytest
from pathlib import Path

from drift_check.parsers.terraform_state import parse_state_file, TerraformResource


SAMPLE_STATE = {
    "version": 4,
    "terraform_version": "1.5.0",
    "resources": [
        {
            "mode": "managed",
            "type": "aws_instance",
            "name": "web",
            "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
            "instances": [
                {
                    "attributes": {
                        "id": "i-0abc123",
                        "instance_type": "t3.micro",
                        "ami": "ami-0abcdef1234567890",
                    }
                }
            ],
        },
        {
            "mode": "data",
            "type": "aws_ami",
            "name": "latest",
            "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
            "instances": [{"attributes": {"id": "ami-999"}}],
        },
    ],
}


@pytest.fixture()
def state_file(tmp_path: Path) -> Path:
    p = tmp_path / "terraform.tfstate"
    p.write_text(json.dumps(SAMPLE_STATE))
    return p


def test_parse_returns_only_managed_resources(state_file: Path):
    resources = parse_state_file(state_file)
    assert len(resources) == 1
    assert resources[0].resource_type == "aws_instance"


def test_parsed_resource_attributes(state_file: Path):
    resource = parse_state_file(state_file)[0]
    assert resource.name == "web"
    assert resource.attributes["instance_type"] == "t3.micro"
    assert resource.resource_id == "aws_instance.web"


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        parse_state_file(tmp_path / "missing.tfstate")


def test_invalid_json_raises(tmp_path: Path):
    bad = tmp_path / "bad.tfstate"
    bad.write_text("not json")
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_state_file(bad)


def test_unsupported_version_raises(tmp_path: Path):
    state = {**SAMPLE_STATE, "version": 3}
    p = tmp_path / "old.tfstate"
    p.write_text(json.dumps(state))
    with pytest.raises(ValueError, match="Unsupported Terraform state version"):
        parse_state_file(p)
