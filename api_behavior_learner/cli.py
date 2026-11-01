#!/usr/bin/env python3
"""CLI for API Behavior Learner."""

import argparse
import json
import sys
from pathlib import Path

from api_behavior_learner.grouper import EndpointGrouper
from api_behavior_learner.har_parser import HARParser
from api_behavior_learner.llm_analyzer import LLMAnalyzer
from api_behavior_learner.spec_generator import SpecGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Reverse engineer API behavior from HTTP traffic logs"
    )

    parser.add_argument("har_file", help="Path to HAR file")

    parser.add_argument(
        "-o",
        "--output",
        default="api-docs",
        help="Output directory (default: api-docs)",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "openapi", "both"],
        default="both",
        help="Output format (default: both)",
    )

    parser.add_argument("--title", default="API", help="API title for OpenAPI spec")

    parser.add_argument(
        "--version", default="1.0.0", help="API version for OpenAPI spec"
    )

    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM analysis (use basic patterns only)",
    )

    args = parser.parse_args()

    # Validate input file
    har_path = Path(args.har_file)
    if not har_path.exists():
        print(f"Error: HAR file not found: {args.har_file}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    print(f"Loading HAR file: {args.har_file}")
    har_parser = HARParser(str(har_path))
    transactions = har_parser.load()
    print(f"Found {len(transactions)} HTTP transactions")

    print("Grouping endpoints...")
    grouper = EndpointGrouper(transactions)
    endpoints = grouper.group()
    print(f"Found {len(endpoints)} unique endpoint patterns")

    print("Analyzing patterns...")
    analyzer = LLMAnalyzer() if not args.no_llm else LLMAnalyzer(api_key="")
    spec_gen = SpecGenerator(analyzer)

    # Generate specs
    if args.format in ["markdown", "both"]:
        print("Generating markdown documentation...")
        md_content = spec_gen.generate_markdown(endpoints)
        md_path = output_dir / "api-docs.md"
        with open(md_path, "w") as f:
            f.write(md_content)
        print(f"Written: {md_path}")

    if args.format in ["openapi", "both"]:
        print("Generating OpenAPI specification...")
        openapi_spec = spec_gen.generate_openapi(
            endpoints, title=args.title, version=args.version
        )
        openapi_path = output_dir / "openapi.json"
        with open(openapi_path, "w") as f:
            json.dump(openapi_spec, f, indent=2)
        print(f"Written: {openapi_path}")

    print("Done!")


if __name__ == "__main__":
    main()
