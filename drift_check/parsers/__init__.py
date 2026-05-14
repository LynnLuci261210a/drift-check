"""Parsers package for drift-check.

Provides readers for Terraform state files and (in future) HCL config files.

Example usage::

    from drift_check.parsers.terraform_state import parse_state_file

    resources = parse_state_file("terraform.tfstate")
    for r in resources:
        print(r.resource_id, r.attributes)
"""

from drift_check.parsers.terraform_state import TerraformResource, parse_state_file

__all__ = ["TerraformResource", "parse_state_file"]
