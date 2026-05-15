"""Command-line interface for drift-check."""
from __future__ import annotations

import argparse
import sys
from typing import List

from drift_check.parsers.terraform_state import parse_state_file
from drift_check.parsers.aws_state import fetch_live_resources
from drift_check.drift_detector import detect_drift, DriftItem
from drift_check.filters import FilterOptions, apply_filters
from drift_check.reporter import report, OutputFormat
from drift_check.formatters.sarif_reporter import render_sarif


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drift-check",
        description="Diff live AWS infrastructure against Terraform state.",
    )
    parser.add_argument("state_file", help="Path to terraform.tfstate")
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat] + ["sarif"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when drift is detected",
    )
    parser.add_argument(
        "--resource-type",
        dest="resource_type",
        default=None,
        help="Filter by resource type prefix (e.g. aws_instance)",
    )
    parser.add_argument(
        "--attribute",
        dest="attribute",
        default=None,
        help="Only report drift on this attribute name",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="AWS profile name",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="AWS region",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    tf_resources = parse_state_file(args.state_file)
    live_resources = fetch_live_resources(
        profile=args.profile,
        region=args.region,
    )

    items: List[DriftItem] = detect_drift(tf_resources, live_resources)

    filter_opts = FilterOptions(
        resource_type=args.resource_type,
        attribute=args.attribute,
    )
    items = apply_filters(items, filter_opts)

    if args.format == "sarif":
        print(render_sarif(items))
    else:
        fmt = OutputFormat(args.format)
        report(items, fmt)

    if args.exit_code and items:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
