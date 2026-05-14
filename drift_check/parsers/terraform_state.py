"""Parser for Terraform state files (.tfstate)."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TerraformResource:
    """Represents a single resource extracted from Terraform state."""

    resource_type: str
    name: str
    provider: str
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def resource_id(self) -> str:
        return f"{self.resource_type}.{self.name}"


def parse_state_file(path: str | Path) -> list[TerraformResource]:
    """Parse a Terraform state file and return a list of TerraformResource objects.

    Args:
        path: Path to the .tfstate file.

    Returns:
        List of parsed TerraformResource instances.

    Raises:
        FileNotFoundError: If the state file does not exist.
        ValueError: If the file is not valid JSON or unsupported state version.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"State file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        try:
            state = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in state file: {exc}") from exc

    version = state.get("version")
    if version != 4:
        raise ValueError(f"Unsupported Terraform state version: {version}. Only version 4 is supported.")

    resources: list[TerraformResource] = []
    for resource in state.get("resources", []):
        if resource.get("mode") != "managed":
            continue
        for instance in resource.get("instances", []):
            resources.append(
                TerraformResource(
                    resource_type=resource["type"],
                    name=resource["name"],
                    provider=resource.get("provider", ""),
                    attributes=instance.get("attributes", {}),
                )
            )
    return resources
