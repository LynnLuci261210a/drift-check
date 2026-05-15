"""Command-line interface for drift-check."""

import sys
import argparse
import boto3

from drift_check.parsers.terraform_state import parse_state_file
from drift_check.parsers.aws_state import fetch_live_resources, AWSStateError
from drift_check.drift_detector import detect_drift
from drift_check.reporter import report, OutputFormat


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drift-check",
        description="Diff live AWS infrastructure against Terraform state.",
    )
    parser.add_argument(
        "state_file",
        metavar="STATE_FILE",
        help="Path to terraform.tfstate (or a remote state JSON export).",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="output_format",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="AWS region to query (overrides environment / profile default).",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="AWS CLI profile to use.",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        dest="exit_code",
        help="Exit with code 1 when drift is detected.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # --- parse Terraform state ---
    try:
        tf_resources = parse_state_file(args.state_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # --- fetch live AWS state ---
    session_kwargs: dict = {}
    if args.region:
        session_kwargs["region_name"] = args.region
    if args.profile:
        session_kwargs["profile_name"] = args.profile

    session = boto3.Session(**session_kwargs)

    try:
        live_resources = fetch_live_resources(session)
    except AWSStateError as exc:
        print(f"error fetching live state: {exc}", file=sys.stderr)
        return 2

    # --- detect drift and report ---
    drift_items = detect_drift(tf_resources, live_resources)
    output_format = OutputFormat(args.output_format)
    print(report(drift_items, fmt=output_format))

    if args.exit_code and drift_items:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
