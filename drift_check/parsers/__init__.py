"""Parsers package for drift-check.

Exposes the primary parsing utilities for both Terraform state files
and live AWS infrastructure state.
"""

from drift_check.parsers.terraform_state import (
    TerraformResource,
    parse_state_file,
    resource_id,
)
from drift_check.parsers.aws_state import (
    LiveResource,
    fetch_live_resources,
    AWSStateError,
)

__all__ = [
    "TerraformResource",
    "parse_state_file",
    "resource_id",
    "LiveResource",
    "fetch_live_resources",
    "AWSStateError",
]
